"""
merge_service.py — Service layer for merging land and property registry records.

Algorithm:
  1. Parse both Excel files (land & property) with Ukrainian→English column mapping.
  2. For every land row, score it against every (unmatched) property row using
     approximate comparison on overlapping fields.
  3. Greedily pair up the best-scoring matches above a threshold.
  4. Each pair becomes one report record with both land_data and property_data filled.
  5. Unmatched land rows get property_data = {}, unmatched property rows get land_data = {}.
  6. Problems are left empty for now.
"""

from __future__ import annotations

import uuid
from datetime import datetime, date
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Minimum total similarity score (0..1) for two rows to be considered a match.
MATCH_THRESHOLD = 0.35

# Individual field weights for the similarity score.
WEIGHTS = {
    "cadastral": 5.0,       # cadastral_number — strongest signal
    "edrpou_tax": 4.0,      # edrpou_of_land_user ↔ tax_number_of_pp
    "owner_name": 3.0,      # land_user ↔ name_of_the_taxpayer
    "location": 2.5,        # location ↔ address_of_the_object
    "area": 2.0,            # area ↔ total_area
    "share": 1.0,           # share_of_ownership
    "date_reg": 1.0,        # date_of_state_registration_of_ownership
}

TOTAL_WEIGHT = sum(WEIGHTS.values())


# ---------------------------------------------------------------------------
# Low-level helpers
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
    """Extract digits only from a value."""
    if value is None:
        return None
    digits = "".join(c for c in str(value) if c.isdigit())
    return digits or None


def _norm_cadastral(value: Any) -> Optional[str]:
    """Normalise cadastral number: lowercase, strip, collapse inner spaces."""
    s = _norm_str(value)
    if s is None:
        return None
    return " ".join(s.split())


# ---------------------------------------------------------------------------
# Field-level similarity functions (each returns 0.0 .. 1.0)
# ---------------------------------------------------------------------------


def _sim_exact_str(a: Any, b: Any) -> float:
    """1.0 if normalised strings are identical, 0.0 otherwise."""
    na, nb = _norm_str(a), _norm_str(b)
    if na is None or nb is None:
        return 0.0
    return 1.0 if na == nb else 0.0


def _sim_fuzzy_str(a: Any, b: Any) -> float:
    """Fuzzy string similarity via SequenceMatcher (0..1)."""
    na, nb = _norm_str(a), _norm_str(b)
    if na is None or nb is None:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def _sim_digits(a: Any, b: Any) -> float:
    """1.0 if digit-only representations match, 0.0 otherwise."""
    da, db = _norm_digits(a), _norm_digits(b)
    if da is None or db is None:
        return 0.0
    return 1.0 if da == db else 0.0


def _sim_float(a: Any, b: Any, tolerance: float = 0.05) -> float:
    """
    Return 1.0 for identical floats, linearly declining to 0.0
    as relative difference exceeds `tolerance`.
    """
    fa, fb = _norm_float(a), _norm_float(b)
    if fa is None or fb is None:
        return 0.0
    denom = max(abs(fa), abs(fb), 1e-9)
    rel_diff = abs(fa - fb) / denom
    if rel_diff <= tolerance:
        return 1.0
    # linear decay — fully 0.0 at 10× tolerance
    return max(0.0, 1.0 - (rel_diff - tolerance) / (tolerance * 9))


def _sim_date(a: Any, b: Any) -> float:
    """1.0 if same date, 0.0 otherwise (or if either is missing)."""
    da, db = _norm_date(a), _norm_date(b)
    if da is None or db is None:
        return 0.0
    return 1.0 if da == db else 0.0


# ---------------------------------------------------------------------------
# Composite scoring
# ---------------------------------------------------------------------------


def _score_pair(land: Dict[str, Any], prop: Dict[str, Any]) -> float:
    """
    Return a weighted similarity score (0..1) between a land row and a
    property row by comparing overlapping fields.
    """
    scores: List[Tuple[float, float]] = []  # (weight, similarity)

    # cadastral_number — both tables may have it
    cad_land = land.get("cadastral_number")
    cad_prop = prop.get("cadastral_number")
    if cad_land or cad_prop:
        scores.append((WEIGHTS["cadastral"], _sim_exact_str(cad_land, cad_prop)))

    # EDRPOU ↔ tax number
    edrpou = land.get("edrpou_of_land_user")
    tax = prop.get("tax_number_of_pp")
    if edrpou or tax:
        scores.append((WEIGHTS["edrpou_tax"], _sim_digits(edrpou, tax)))

    # Owner / taxpayer name
    lu = land.get("land_user")
    tn = prop.get("name_of_the_taxpayer")
    if lu or tn:
        scores.append((WEIGHTS["owner_name"], _sim_fuzzy_str(lu, tn)))

    # Location / address
    loc = land.get("location")
    addr = prop.get("address_of_the_object")
    if loc or addr:
        scores.append((WEIGHTS["location"], _sim_fuzzy_str(loc, addr)))

    # Area
    area_l = land.get("area")
    area_p = prop.get("total_area")
    if area_l is not None or area_p is not None:
        scores.append((WEIGHTS["area"], _sim_float(area_l, area_p)))

    # Share of ownership
    share_l = land.get("share_of_ownership")
    share_p = prop.get("share_of_ownership")
    if share_l is not None or share_p is not None:
        scores.append((WEIGHTS["share"], _sim_float(share_l, share_p)))

    # Date of state registration of ownership
    date_l = land.get("date_of_state_registration_of_ownership")
    date_p = prop.get("date_of_state_registration_of_ownership")
    if date_l or date_p:
        scores.append((WEIGHTS["date_reg"], _sim_date(date_l, date_p)))

    if not scores:
        return 0.0

    total_w = sum(w for w, _ in scores)
    if total_w == 0:
        return 0.0

    return sum(w * s for w, s in scores) / total_w


# ---------------------------------------------------------------------------
# Greedy matching
# ---------------------------------------------------------------------------


def _greedy_match(
    land_rows: List[Dict[str, Any]],
    property_rows: List[Dict[str, Any]],
) -> Tuple[
    List[Tuple[Dict[str, Any], Dict[str, Any]]],   # matched pairs
    List[Dict[str, Any]],                            # unmatched land
    List[Dict[str, Any]],                            # unmatched property
]:
    """
    Score every (land, property) pair, then greedily pick the highest-score
    pairs above MATCH_THRESHOLD.  Each row is used at most once.
    """
    # Build all candidate pairs with scores
    candidates: List[Tuple[float, int, int]] = []
    for li, land in enumerate(land_rows):
        for pi, prop in enumerate(property_rows):
            score = _score_pair(land, prop)
            if score >= MATCH_THRESHOLD:
                candidates.append((score, li, pi))

    # Sort descending by score
    candidates.sort(key=lambda x: x[0], reverse=True)

    used_land: set[int] = set()
    used_prop: set[int] = set()
    pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []

    for score, li, pi in candidates:
        if li in used_land or pi in used_prop:
            continue
        pairs.append((land_rows[li], property_rows[pi]))
        used_land.add(li)
        used_prop.add(pi)

    unmatched_land = [r for i, r in enumerate(land_rows) if i not in used_land]
    unmatched_prop = [r for i, r in enumerate(property_rows) if i not in used_prop]

    return pairs, unmatched_land, unmatched_prop


# ---------------------------------------------------------------------------
# Record builder
# ---------------------------------------------------------------------------


def _make_record(
    report_id: str,
    land: Dict[str, Any],
    prop: Dict[str, Any],
) -> Dict[str, Any]:
    """Construct a single output record.  Problems are left empty."""
    return {
        "report_id": report_id,
        "record_id": str(uuid.uuid4()),
        "problems": [],           # ← empty for now
        "land_data": dict(land),
        "property_data": dict(prop),
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

    Algorithm:
      1. Score every (land, property) pair on overlapping fields.
      2. Greedily pair up the best matches above MATCH_THRESHOLD.
      3. Paired rows → one record with both land_data & property_data.
      4. Unpaired land rows → record with property_data = {}.
      5. Unpaired property rows → record with land_data = {}.
      6. Problems are always empty for now.

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
    pairs, unmatched_land, unmatched_prop = _greedy_match(land_rows, property_rows)

    records: List[Dict[str, Any]] = []

    # Matched pairs
    for land, prop in pairs:
        records.append(_make_record(report_id, land, prop))

    # Unmatched land rows
    for land in unmatched_land:
        records.append(_make_record(report_id, land, {}))

    # Unmatched property rows
    for prop in unmatched_prop:
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

    Each dict contains keys: problems, land_data, property_data.
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