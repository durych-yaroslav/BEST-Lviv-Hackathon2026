"""
merge_service.py — Service layer for merging land and property registry records.

Algorithm (fast, O(n+m)):
  1. Parse both Excel files (land & property) with Ukrainian→English column mapping.
  2. Build a hash-map index of property rows keyed by tax_number_of_pp.
  3. For each land row, look up matching property row via edrpou_of_land_user.
  4. For matched pairs, compare corresponding fields and populate `problems`.
  5. Unmatched land rows → record with property_data = {}.
     Unmatched property rows → record with land_data = {}.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional

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
        return float(value)
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
# Field comparison helpers
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
# Matching — fast O(n+m) index-based
# ---------------------------------------------------------------------------


def _build_property_index(
    property_rows: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Build a lookup index from property rows keyed by normalised
    tax_number_of_pp (digits only).
    """
    index: Dict[str, List[Dict[str, Any]]] = {}

    for row in property_rows:
        tax = _norm_digits(row.get("tax_number_of_pp"))
        if tax:
            index.setdefault(tax, []).append(row)

    return index


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
    if land and prop:
        problems = _detect_problems(land, prop)
    else:
        problems = []

    return {
        "report_id": report_id,
        "record_id": str(uuid.uuid4()),
        "problems": problems,
        "land_data": dict(land) if land else {},
        "property_data": dict(prop) if prop else {},
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def merge_records(
    land_rows: List[Dict[str, Any]],
    property_rows: List[Dict[str, Any]],
    report_id: str,
) -> List[Dict[str, Any]]:
    """
    Merge land and property rows into unified report records.

    Matching key: edrpou_of_land_user (land) ↔ tax_number_of_pp (property).
    Comparison is done on normalised digits only.

    For matched pairs, corresponding fields are compared and discrepancies
    are listed in the `problems` array.

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
    by_tax = _build_property_index(property_rows)
    matched_prop_ids: set[int] = set()
    records: List[Dict[str, Any]] = []

    for land in land_rows:
        edrpou = _norm_digits(land.get("edrpou_of_land_user"))
        matches = by_tax.get(edrpou, []) if edrpou else []

        if matches:
            for prop in matches:
                matched_prop_ids.add(id(prop))
                records.append(_make_record(report_id, land, prop))
        else:
            # Land row with no matching property row
            records.append(_make_record(report_id, land, {}))

    # Property rows that had no matching land row
    for prop in property_rows:
        if id(prop) not in matched_prop_ids:
            records.append(_make_record(report_id, {}, prop))

    return records


# ---------------------------------------------------------------------------
# Excel column mappings — Ukrainian header → English API key
# ---------------------------------------------------------------------------

LAND_COLUMN_MAP: Dict[str, str] = {
    "Кадастровий номер": "cadastral_number",
    "koatuu": "koatuu",
    "Форма власності": "form_of_ownership",
    "Цільове призначення": "purpose",
    "Місцерозташування": "location",
    "Вид с/г угідь": "type_of_agricultural_land",
    "Площа, га": "area",
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