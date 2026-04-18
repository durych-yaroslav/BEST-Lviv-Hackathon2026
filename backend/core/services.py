"""
merge_service.py — Service layer for merging land and property registry records.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FLOAT_TOLERANCE = 0.01

PROBLEM_EDRPOU = "edrpou_of_land_user"
PROBLEM_LAND_USER = "land_user"
PROBLEM_LOCATION = "location"
PROBLEM_AREA = "area"
PROBLEM_DATE = "date_of_state_registration_of_ownership"
PROBLEM_SHARE = "share_of_ownership"
PROBLEM_PURPOSE = "purpose"

ALL_PROBLEMS = (
    PROBLEM_EDRPOU,
    PROBLEM_LAND_USER,
    PROBLEM_LOCATION,
    PROBLEM_AREA,
    PROBLEM_DATE,
    PROBLEM_SHARE,
    PROBLEM_PURPOSE,
)

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


def _norm_date(value: Any) -> Optional[datetime]:
    """Parse an ISO-format date string / datetime; return None on failure."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).strip())
    except (ValueError, TypeError):
        return None


def _norm_cadastral(value: Any) -> Optional[str]:
    """Normalise cadastral number: lowercase, strip, collapse inner spaces."""
    s = _norm_str(value)
    if s is None:
        return None
    return " ".join(s.split())


def _norm_tax(value: Any) -> Optional[str]:
    """Normalise tax / EDRPOU number: digits only."""
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
    """True when two date values differ (or either fails to parse)."""
    da, db = _norm_date(a), _norm_date(b)
    if da is None and db is None:
        return False
    if da is None or db is None:
        # One side present, other missing or unparseable → mismatch
        return True
    return da.date() != db.date()


# ---------------------------------------------------------------------------
# Problem detection
# ---------------------------------------------------------------------------


def _detect_problems(land: Dict[str, Any], prop: Dict[str, Any]) -> List[str]:
    """Compare corresponding fields and return a list of problem enum strings."""
    problems: List[str] = []

    checks = [
        (PROBLEM_EDRPOU,   _str_mismatch,   land.get("edrpou_of_land_user"),                    prop.get("tax_number_of_pp")),
        (PROBLEM_LAND_USER,_str_mismatch,   land.get("land_user"),                               prop.get("name_of_the_taxpayer")),
        (PROBLEM_LOCATION, _str_mismatch,   land.get("location"),                                prop.get("address_of_the_object")),
        (PROBLEM_AREA,     _float_mismatch, land.get("area"),                                    prop.get("total_area")),
        (PROBLEM_DATE,     _date_mismatch,  land.get("date_of_state_registration_of_ownership"), prop.get("date_of_state_registration_of_ownership")),
        (PROBLEM_SHARE,    _float_mismatch, land.get("share_of_ownership"),                      prop.get("share_of_ownership")),
        (PROBLEM_PURPOSE,  _str_mismatch,   land.get("purpose"),                                 prop.get("type_of_object")),
    ]

    for problem_key, comparator, land_val, prop_val in checks:
        try:
            if comparator(land_val, prop_val):
                problems.append(problem_key)
        except Exception:
            problems.append(problem_key)

    return problems


# ---------------------------------------------------------------------------
# Matching logic
# ---------------------------------------------------------------------------


def _build_property_index(
    property_rows: List[Dict[str, Any]],
) -> tuple[Dict[str, List[Dict]], Dict[str, List[Dict]]]:
    """
    Build two lookup indexes from property rows:
      - by normalised cadastral_number
      - by normalised tax_number_of_pp (fallback)
    """
    by_cadastral: Dict[str, List[Dict]] = {}
    by_tax: Dict[str, List[Dict]] = {}

    for row in property_rows:
        cad = _norm_cadastral(row.get("cadastral_number"))
        if cad:
            by_cadastral.setdefault(cad, []).append(row)

        tax = _norm_tax(row.get("tax_number_of_pp"))
        if tax:
            by_tax.setdefault(tax, []).append(row)

    return by_cadastral, by_tax


def _find_matches(
    land: Dict[str, Any],
    by_cadastral: Dict[str, List[Dict]],
    by_tax: Dict[str, List[Dict]],
) -> List[Dict[str, Any]]:
    """Return all property rows matching this land row."""
    cad = _norm_cadastral(land.get("cadastral_number"))
    if cad and cad in by_cadastral:
        return by_cadastral[cad]

    tax = _norm_tax(land.get("edrpou_of_land_user"))
    if tax and tax in by_tax:
        return by_tax[tax]

    return []


# ---------------------------------------------------------------------------
# Record builder
# ---------------------------------------------------------------------------


def _make_record(
    report_id: str,
    land: Dict[str, Any],
    prop: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Construct a single output record."""
    problems: List[str] = (
        _detect_problems(land, prop) if prop is not None else list(ALL_PROBLEMS)
    )

    return {
        "report_id": report_id,
        "record_id": str(uuid.uuid4()),
        "problems": problems,
        "land_data": dict(land),
        "property_data": dict(prop) if prop is not None else {},
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def merge_records(
    land_rows: list,
    property_rows: list,
    report_id: str,
) -> list:
    """
    Merge land and property rows into unified report records.

    Matching priority:
      1. cadastral_number (exact, normalised)
      2. edrpou_of_land_user ↔ tax_number_of_pp (digits-only normalised)

    One land row may produce multiple records if multiple property rows match.
    Unmatched land rows produce a record with property_data = None.

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
    by_cadastral, by_tax = _build_property_index(property_rows)
    matched_prop_ids: set[int] = set()
    records: List[Dict[str, Any]] = []

    for land in land_rows:
        try:
            matches = _find_matches(land, by_cadastral, by_tax)
        except Exception:
            matches = []

        if matches:
            for prop in matches:
                matched_prop_ids.add(id(prop))
                try:
                    records.append(_make_record(report_id, land, prop))
                except Exception:
                    records.append(_make_record(report_id, land, None))
        else:
            records.append(_make_record(report_id, land, None))

    # Property rows that had no matching land row
    for prop in property_rows:
        if id(prop) not in matched_prop_ids:
            empty_land: Dict[str, Any] = {}
            records.append(_make_record(report_id, empty_land, prop))

    return records


# ---------------------------------------------------------------------------
# Excel parsing
# ---------------------------------------------------------------------------


def _clean_for_json(row: dict) -> dict:
    """Replace NaN / NaT / numpy types with JSON-safe Python types."""
    cleaned = {}
    for k, v in row.items():
        if isinstance(v, float) and math.isnan(v):
            cleaned[k] = None
        elif isinstance(v, pd.Timestamp):
            cleaned[k] = v.isoformat()
        elif isinstance(v, (np.integer,)):
            cleaned[k] = int(v)
        elif isinstance(v, (np.floating,)):
            cleaned[k] = None if np.isnan(v) else float(v)
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

    land_rows = [_clean_for_json(r) for r in land_df.to_dict(orient="records")]
    property_rows = [_clean_for_json(r) for r in property_df.to_dict(orient="records")]

    # report_id placeholder — the view assigns the real DB id
    return merge_records(land_rows, property_rows, report_id="")