"""
services.py — Service layer for merging land and property registry records.

Algorithm:
  1. Parse both Excel files (land & property) with Ukrainian→English column mapping.
  2. Compute a similarity score between every (land, property) pair using
     multiple signals: EDRPOU↔tax_number, location↔address, area↔total_area.
  3. Use greedy best-match assignment (score >= threshold) to pair rows 1-to-1.
  4. For matched pairs, compare corresponding fields and populate `problems`.
  5. Unmatched land rows → record with property_data = null fields.
     Unmatched property rows → record with land_data = null fields.
"""

from __future__ import annotations

import math
import re
import uuid
from datetime import datetime, date
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Problem enum values (from README)
# ---------------------------------------------------------------------------

PROBLEM_EDRPOU = "edrpou_of_land_user"
PROBLEM_LAND_USER = "land_user"
PROBLEM_LOCATION = "location"
PROBLEM_AREA = "area"
PROBLEM_DATE = "date_of_state_registration_of_ownership"
PROBLEM_SHARE = "share_of_ownership"
PROBLEM_PURPOSE = "purpose"

FLOAT_TOLERANCE = 0.01
MATCH_THRESHOLD = 0.40  # minimum combined score to consider a pair "related"


# ---------------------------------------------------------------------------
# Schema templates — every record will have exactly these keys
# ---------------------------------------------------------------------------

LAND_DATA_TEMPLATE: Dict[str, Any] = {
    "cadastral_number": None,
    "koatuu": None,
    "form_of_ownership": None,
    "purpose": None,
    "location": None,
    "type_of_agricultural_land": None,
    "area": None,
    "average_monetary_valuation": None,
    "edrpou_of_land_user": None,
    "land_user": None,
    "share_of_ownership": None,
    "date_of_state_registration_of_ownership": None,
    "record_number_of_ownership": None,
    "authority_that_performed_state_registration_of_ownership": None,
    "type": None,
    "subtype": None,
}

PROPERTY_DATA_TEMPLATE: Dict[str, Any] = {
    "tax_number_of_pp": None,
    "name_of_the_taxpayer": None,
    "type_of_object": None,
    "address_of_the_object": None,
    "date_of_state_registration_of_ownership": None,
    "date_of_state_registration_of_pledge_of_ownership": None,
    "total_area": None,
    "type_of_joint_ownership": None,
    "share_of_ownership": None,
}


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------


def _norm_str(value: Any) -> Optional[str]:
    """Return a lowercased, stripped string or None."""
    if value is None:
        return None
    s = str(value).strip()
    return s.lower() if s else None


def _norm_float(value: Any) -> Optional[float]:
    """Return a float or None."""
    if value is None:
        return None
    try:
        f = float(value)
        return f if not math.isnan(f) else None
    except (ValueError, TypeError):
        return None


def _norm_date(value: Any) -> Optional[date]:
    """Parse a date; return None on failure."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value).strip()).date()
    except (ValueError, TypeError):
        return None


def _norm_digits(value: Any) -> Optional[str]:
    """Extract digits only from a value (for EDRPOU / tax number comparison)."""
    if value is None:
        return None
    digits = "".join(c for c in str(value) if c.isdigit())
    return digits or None


# ---------------------------------------------------------------------------
# Field comparison helpers (for problem detection)
# ---------------------------------------------------------------------------


def _str_mismatch(a: Any, b: Any) -> bool:
    """True when two string-like values meaningfully differ."""
    na, nb = _norm_str(a), _norm_str(b)
    if na is None and nb is None:
        return False
    if na is None or nb is None:
        return True
    return na != nb


def _float_mismatch(a: Any, b: Any) -> bool:
    """True when two numeric values differ beyond FLOAT_TOLERANCE."""
    fa, fb = _norm_float(a), _norm_float(b)
    if fa is None and fb is None:
        return False
    if fa is None or fb is None:
        return True
    return abs(fa - fb) > FLOAT_TOLERANCE


def _date_mismatch(a: Any, b: Any) -> bool:
    """True when two date values differ."""
    da, db = _norm_date(a), _norm_date(b)
    if da is None and db is None:
        return False
    if da is None or db is None:
        return True
    return da != db


def _digits_mismatch(a: Any, b: Any) -> bool:
    """True when digit-only representations differ."""
    da, db = _norm_digits(a), _norm_digits(b)
    if da is None and db is None:
        return False
    if da is None or db is None:
        return True
    return da != db


# ---------------------------------------------------------------------------
# Similarity helpers (for matching)
# ---------------------------------------------------------------------------


def _str_similarity(a: Any, b: Any) -> float:
    """Return 0.0–1.0 similarity between two strings (SequenceMatcher)."""
    na, nb = _norm_str(a), _norm_str(b)
    if na is None or nb is None:
        return 0.0
    if na == nb:
        return 1.0
    return SequenceMatcher(None, na, nb).ratio()


def _digits_similarity(a: Any, b: Any) -> float:
    """Return 1.0 if digit representations match, else 0.0."""
    da, db = _norm_digits(a), _norm_digits(b)
    if da is None or db is None:
        return 0.0
    return 1.0 if da == db else 0.0


def _float_similarity(a: Any, b: Any) -> float:
    """Return 1.0 if both within tolerance, 0.0 otherwise."""
    fa, fb = _norm_float(a), _norm_float(b)
    if fa is None or fb is None:
        return 0.0
    if abs(fa - fb) <= FLOAT_TOLERANCE:
        return 1.0
    # Partial credit for close values
    if fa == 0 and fb == 0:
        return 1.0
    denominator = max(abs(fa), abs(fb))
    if denominator == 0:
        return 1.0
    ratio = 1.0 - abs(fa - fb) / denominator
    return max(0.0, ratio)


# ---------------------------------------------------------------------------
# Matching score computation
# ---------------------------------------------------------------------------

# Weights for different matching signals
WEIGHT_EDRPOU = 0.50   # EDRPOU/tax number match is the strongest signal
WEIGHT_LOCATION = 0.25  # Location/address similarity
WEIGHT_AREA = 0.15      # Area similarity
WEIGHT_NAME = 0.10      # Name similarity


def _compute_match_score(land: Dict[str, Any], prop: Dict[str, Any]) -> float:
    """
    Compute a weighted similarity score between a land row and a property row.
    Returns a float 0.0–1.0.
    """
    score = 0.0

    # 1. EDRPOU ↔ tax_number_of_pp (strongest signal)
    score += WEIGHT_EDRPOU * _digits_similarity(
        land.get("edrpou_of_land_user"),
        prop.get("tax_number_of_pp"),
    )

    # 2. Location ↔ address
    score += WEIGHT_LOCATION * _str_similarity(
        land.get("location"),
        prop.get("address_of_the_object"),
    )

    # 3. Area ↔ total_area
    score += WEIGHT_AREA * _float_similarity(
        land.get("area"),
        prop.get("total_area"),
    )

    # 4. Land user name ↔ taxpayer name
    score += WEIGHT_NAME * _str_similarity(
        land.get("land_user"),
        prop.get("name_of_the_taxpayer"),
    )

    return score


# ---------------------------------------------------------------------------
# Problem detection
# ---------------------------------------------------------------------------

# Each check: (problem_key, comparator, land_field, property_field)
PROBLEM_CHECKS = [
    (PROBLEM_EDRPOU,    _digits_mismatch, "edrpou_of_land_user",                    "tax_number_of_pp"),
    (PROBLEM_LAND_USER, _str_mismatch,    "land_user",                               "name_of_the_taxpayer"),
    (PROBLEM_LOCATION,  _str_mismatch,    "location",                                "address_of_the_object"),
    (PROBLEM_AREA,      _float_mismatch,  "area",                                    "total_area"),
    (PROBLEM_DATE,      _date_mismatch,   "date_of_state_registration_of_ownership", "date_of_state_registration_of_ownership"),
    (PROBLEM_SHARE,     _float_mismatch,  "share_of_ownership",                      "share_of_ownership"),
    (PROBLEM_PURPOSE,   _str_mismatch,    "purpose",                                 "type_of_object"),
]


def _detect_problems(land: Dict[str, Any], prop: Dict[str, Any]) -> List[str]:
    """
    Compare corresponding fields between land_data and property_data.
    Return a list of problem enum strings for fields that have discrepancies.
    """
    problems: List[str] = []

    for problem_key, comparator, land_field, prop_field in PROBLEM_CHECKS:
        land_val = land.get(land_field)
        prop_val = prop.get(prop_field)
        try:
            if comparator(land_val, prop_val):
                problems.append(problem_key)
        except Exception:
            problems.append(problem_key)

    return problems


# ---------------------------------------------------------------------------
# Schema enforcement — fill missing keys with None
# ---------------------------------------------------------------------------


def _enforce_land_schema(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Return a dict with exactly the keys from LAND_DATA_TEMPLATE."""
    result = dict(LAND_DATA_TEMPLATE)
    for key in LAND_DATA_TEMPLATE:
        if key in raw and raw[key] is not None:
            result[key] = raw[key]
    return result


def _enforce_property_schema(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Return a dict with exactly the keys from PROPERTY_DATA_TEMPLATE."""
    result = dict(PROPERTY_DATA_TEMPLATE)
    for key in PROPERTY_DATA_TEMPLATE:
        if key in raw and raw[key] is not None:
            result[key] = raw[key]
    return result


# ---------------------------------------------------------------------------
# Record builder
# ---------------------------------------------------------------------------


def _make_record(
    report_id: str,
    land: Dict[str, Any],
    prop: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Construct a single output record.
    - If both land and prop are present → detect problems between them.
    - Otherwise → problems is empty.
    """
    has_land = bool(land)
    has_prop = bool(prop)

    if has_land and has_prop:
        problems = _detect_problems(land, prop)
    else:
        problems = []

    return {
        "report_id": report_id,
        "record_id": str(uuid.uuid4()),
        "problems": problems,
        "land_data": _enforce_land_schema(land) if has_land else _enforce_land_schema({}),
        "property_data": _enforce_property_schema(prop) if has_prop else _enforce_property_schema({}),
    }


# ---------------------------------------------------------------------------
# Greedy best-match assignment
# ---------------------------------------------------------------------------


def _greedy_match(
    land_rows: List[Dict[str, Any]],
    property_rows: List[Dict[str, Any]],
) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
    """
    Greedy 1-to-1 matching of land rows to property rows.

    1. Compute all (land_idx, prop_idx, score) where score >= MATCH_THRESHOLD.
    2. Sort by descending score.
    3. Greedily assign pairs, ensuring each row is used at most once.

    Returns:
        matched_pairs: list of (land_idx, prop_idx)
        unmatched_land: list of land_idx
        unmatched_prop: list of prop_idx
    """
    candidates: List[Tuple[float, int, int]] = []

    for li, land in enumerate(land_rows):
        for pi, prop in enumerate(property_rows):
            score = _compute_match_score(land, prop)
            if score >= MATCH_THRESHOLD:
                candidates.append((score, li, pi))

    # Sort descending by score
    candidates.sort(key=lambda x: x[0], reverse=True)

    used_land: set = set()
    used_prop: set = set()
    matched_pairs: List[Tuple[int, int]] = []

    for score, li, pi in candidates:
        if li not in used_land and pi not in used_prop:
            matched_pairs.append((li, pi))
            used_land.add(li)
            used_prop.add(pi)

    unmatched_land = [i for i in range(len(land_rows)) if i not in used_land]
    unmatched_prop = [i for i in range(len(property_rows)) if i not in used_prop]

    return matched_pairs, unmatched_land, unmatched_prop


# ---------------------------------------------------------------------------
# Public API — merge_records
# ---------------------------------------------------------------------------


def merge_records(
    land_rows: List[Dict[str, Any]],
    property_rows: List[Dict[str, Any]],
    report_id: str,
) -> List[Dict[str, Any]]:
    """
    Merge land and property rows into unified report records.

    Matching uses a multi-signal weighted scoring system:
      - EDRPOU ↔ tax_number_of_pp (50%)
      - Location ↔ address (25%)
      - Area ↔ total_area (15%)
      - Land user ↔ taxpayer name (10%)

    Pairs scoring >= MATCH_THRESHOLD are greedily matched 1-to-1.
    For matched pairs the corresponding fields are compared and
    discrepancies are listed in the `problems` array.

    Parameters
    ----------
    land_rows : list[dict]
        Rows parsed from the land registry XLSX.
    property_rows : list[dict]
        Rows parsed from the property registry XLSX.
    report_id : str
        UUID string of the parent report.

    Returns
    -------
    list[dict]
        Records matching the API schema.
    """
    matched_pairs, unmatched_land, unmatched_prop = _greedy_match(
        land_rows, property_rows,
    )

    records: List[Dict[str, Any]] = []

    # 1. Matched pairs
    for li, pi in matched_pairs:
        records.append(_make_record(report_id, land_rows[li], property_rows[pi]))

    # 2. Unmatched land rows
    for li in unmatched_land:
        records.append(_make_record(report_id, land_rows[li], {}))

    # 3. Unmatched property rows
    for pi in unmatched_prop:
        records.append(_make_record(report_id, {}, property_rows[pi]))

    return records


# ---------------------------------------------------------------------------
# Excel column mappings — Ukrainian header → English API key
# ---------------------------------------------------------------------------

LAND_COLUMN_MAP: Dict[str, str] = {
    "Кадастровий номер": "cadastral_number",
    "koatuu": "koatuu",
    "КОАТУУ": "koatuu",
    "Форма власності": "form_of_ownership",
    "Цільове призначення": "purpose",
    "Місцерозташування": "location",
    "Вид с/г угідь": "type_of_agricultural_land",
    "Площа, га": "area",
    "Площа": "area",
    "Усереднена нормативно грошова оцінка": "average_monetary_valuation",
    "ЄДРПОУ землекористувача": "edrpou_of_land_user",
    "Землекористувач": "land_user",
    "Частка володіння": "share_of_ownership",
    "Дата державної реєстрації права власності": "date_of_state_registration_of_ownership",
    "Номер запису про право власності": "record_number_of_ownership",
    "Орган, що здійснив державну реєстрацію права власності": "authority_that_performed_state_registration_of_ownership",
    "Тип": "type",
    "Підтип": "subtype",
}

PROPERTY_COLUMN_MAP: Dict[str, str] = {
    "ІПН платника податку": "tax_number_of_pp",
    "Найменування платника податку": "name_of_the_taxpayer",
    "Тип об'єкта": "type_of_object",
    "Адреса об'єкта": "address_of_the_object",
    "Дата державної реєстрації права власності": "date_of_state_registration_of_ownership",
    "Дата державної реєстрації обтяження права власності": "date_of_state_registration_of_pledge_of_ownership",
    "Загальна площа": "total_area",
    "Тип спільної власності": "type_of_joint_ownership",
    "Частка володіння": "share_of_ownership",
}


# ---------------------------------------------------------------------------
# Excel parsing
# ---------------------------------------------------------------------------


def _clean_for_json(row: dict) -> dict:
    """Replace NaN / NaT / numpy types with JSON-safe Python types."""
    import datetime as _dt
    cleaned = {}
    for k, v in row.items():
        if pd.isna(v):
            cleaned[k] = None
        elif isinstance(v, (_dt.datetime, _dt.date)):
            cleaned[k] = v.isoformat()
        elif isinstance(v, pd.Timestamp):
            cleaned[k] = v.isoformat()
        elif isinstance(v, (np.integer,)):
            cleaned[k] = int(v)
        elif isinstance(v, (np.floating,)):
            cleaned[k] = float(v)
        else:
            cleaned[k] = v
    return cleaned


def process_excel_files(land_file, property_file) -> list:
    """
    Parse two .xlsx uploads and return a list of merged record dicts.

    Each dict contains keys: report_id, record_id, problems, land_data, property_data.
    The land_data and property_data sub-dicts always contain every field from
    the API schema (missing values → None).
    """
    land_df = pd.read_excel(land_file, engine="openpyxl")
    property_df = pd.read_excel(property_file, engine="openpyxl")

    # Rename Ukrainian headers → English API keys
    land_df.rename(columns=LAND_COLUMN_MAP, inplace=True)
    property_df.rename(columns=PROPERTY_COLUMN_MAP, inplace=True)

    land_rows = [_clean_for_json(r) for r in land_df.to_dict(orient="records")]
    property_rows = [_clean_for_json(r) for r in property_df.to_dict(orient="records")]

    # report_id placeholder — the view assigns the real DB id
    return merge_records(land_rows, property_rows, report_id="")