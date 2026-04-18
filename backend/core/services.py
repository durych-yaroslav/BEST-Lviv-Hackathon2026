"""
services.py — Data processing algorithm for land & property registry comparison.

Reads two Excel files (Land registry and Property registry), merges them on
common identifiers (Cadastral Number ↔ Cadastral Number, and EDRPOU/Tax Number),
validates corresponding fields, and returns a list[dict] of Record objects ready
for Django's bulk_create via the JSON schema defined in README.md.
"""

import logging
import math
import re
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Tolerance for comparing numeric area values (relative %)
AREA_RELATIVE_TOLERANCE = 0.05  # 5 %

# All valid problem enum strings
VALID_PROBLEMS = frozenset(
    {
        "edrpou_of_land_user",
        "land_user",
        "location",
        "area",
        "date_of_state_registration_of_ownership",
        "share_of_ownership",
        "purpose",
    }
)

# ---------------------------------------------------------------------------
# Column-name normalisation maps
# ---------------------------------------------------------------------------
# The Excel files from Ukrainian registries may have headers in Ukrainian or
# English, or mixed.  We define a liberal mapping from *likely* column headers
# to our canonical internal key names.  Mapping is attempted case-insensitively,
# after stripping whitespace and collapsing multiple spaces / underscores.

LAND_COLUMN_MAP: Dict[str, str] = {
    # Ukrainian variants
    "кадастровий номер": "cadastral_number",
    "коатуу": "koatuu",
    "форма власності": "form_of_ownership",
    "цільове призначення": "purpose",
    "місцезнаходження": "location",
    "вид сільськогосподарських угідь": "type_of_agricultural_land",
    "площа": "area",
    "нормативна грошова оцінка": "average_monetary_valuation",
    "середня грошова оцінка": "average_monetary_valuation",
    "код єдрпоу землекористувача": "edrpou_of_land_user",
    "єдрпоу землекористувача": "edrpou_of_land_user",
    "землекористувач": "land_user",
    "назва землекористувача": "land_user",
    "частка власності": "share_of_ownership",
    "дата державної реєстрації права власності": "date_of_state_registration_of_ownership",
    "номер запису про право власності": "record_number_of_ownership",
    "орган що здійснив державну реєстрацію права власності": "authority_that_performed_state_registration_of_ownership",
    "тип": "type",
    "підтип": "subtype",
    # English / snake_case variants (in case headers are already in English)
    "cadastral_number": "cadastral_number",
    "cadastral number": "cadastral_number",
    "koatuu": "koatuu",
    "form_of_ownership": "form_of_ownership",
    "form of ownership": "form_of_ownership",
    "purpose": "purpose",
    "location": "location",
    "type_of_agricultural_land": "type_of_agricultural_land",
    "type of agricultural land": "type_of_agricultural_land",
    "area": "area",
    "average_monetary_valuation": "average_monetary_valuation",
    "average monetary valuation": "average_monetary_valuation",
    "edrpou_of_land_user": "edrpou_of_land_user",
    "edrpou of land user": "edrpou_of_land_user",
    "edrpou": "edrpou_of_land_user",
    "land_user": "land_user",
    "land user": "land_user",
    "share_of_ownership": "share_of_ownership",
    "share of ownership": "share_of_ownership",
    "date_of_state_registration_of_ownership": "date_of_state_registration_of_ownership",
    "date of state registration of ownership": "date_of_state_registration_of_ownership",
    "record_number_of_ownership": "record_number_of_ownership",
    "record number of ownership": "record_number_of_ownership",
    "authority_that_performed_state_registration_of_ownership": "authority_that_performed_state_registration_of_ownership",
    "authority that performed state registration of ownership": "authority_that_performed_state_registration_of_ownership",
    "type": "type",
    "subtype": "subtype",
}

PROPERTY_COLUMN_MAP: Dict[str, str] = {
    # Ukrainian variants
    "податковий номер": "tax_number_of_pp",
    "іпн": "tax_number_of_pp",
    "рнокпп": "tax_number_of_pp",
    "назва платника податків": "name_of_the_taxpayer",
    "платник податків": "name_of_the_taxpayer",
    "тип об'єкта": "type_of_object",
    "тип обєкта": "type_of_object",
    "адреса об'єкта": "address_of_the_object",
    "адреса обєкта": "address_of_the_object",
    "місцезнаходження": "address_of_the_object",
    "дата державної реєстрації права власності": "date_of_state_registration_of_ownership",
    "дата державної реєстрації обтяження права власності": "date_of_state_registration_of_pledge_of_ownership",
    "загальна площа": "total_area",
    "площа": "total_area",
    "вид спільної власності": "type_of_joint_ownership",
    "частка власності": "share_of_ownership",
    "кадастровий номер": "cadastral_number",
    "код єдрпоу": "tax_number_of_pp",
    "єдрпоу": "tax_number_of_pp",
    # English / snake_case variants
    "tax_number_of_pp": "tax_number_of_pp",
    "tax number of pp": "tax_number_of_pp",
    "tax number": "tax_number_of_pp",
    "name_of_the_taxpayer": "name_of_the_taxpayer",
    "name of the taxpayer": "name_of_the_taxpayer",
    "type_of_object": "type_of_object",
    "type of object": "type_of_object",
    "address_of_the_object": "address_of_the_object",
    "address of the object": "address_of_the_object",
    "date_of_state_registration_of_ownership": "date_of_state_registration_of_ownership",
    "date of state registration of ownership": "date_of_state_registration_of_ownership",
    "date_of_state_registration_of_pledge_of_ownership": "date_of_state_registration_of_pledge_of_ownership",
    "date of state registration of pledge of ownership": "date_of_state_registration_of_pledge_of_ownership",
    "total_area": "total_area",
    "total area": "total_area",
    "type_of_joint_ownership": "type_of_joint_ownership",
    "type of joint ownership": "type_of_joint_ownership",
    "share_of_ownership": "share_of_ownership",
    "share of ownership": "share_of_ownership",
    "cadastral_number": "cadastral_number",
    "cadastral number": "cadastral_number",
    "edrpou": "tax_number_of_pp",
    "edrpou_of_land_user": "tax_number_of_pp",
}

# Keys that MUST appear in the output dicts (with None as fallback)
LAND_DATA_KEYS = [
    "cadastral_number",
    "koatuu",
    "form_of_ownership",
    "purpose",
    "location",
    "type_of_agricultural_land",
    "area",
    "average_monetary_valuation",
    "edrpou_of_land_user",
    "land_user",
    "share_of_ownership",
    "date_of_state_registration_of_ownership",
    "record_number_of_ownership",
    "authority_that_performed_state_registration_of_ownership",
    "type",
    "subtype",
]

PROPERTY_DATA_KEYS = [
    "tax_number_of_pp",
    "name_of_the_taxpayer",
    "type_of_object",
    "address_of_the_object",
    "date_of_state_registration_of_ownership",
    "date_of_state_registration_of_pledge_of_ownership",
    "total_area",
    "type_of_joint_ownership",
    "share_of_ownership",
]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _normalise_header(header: str) -> str:
    """Lowercase, strip, collapse whitespace / underscores to single space."""
    h = str(header).strip().lower()
    h = re.sub(r"[_\s]+", " ", h)
    return h


def _rename_columns(df: pd.DataFrame, col_map: Dict[str, str]) -> pd.DataFrame:
    """Rename DataFrame columns using a case-insensitive mapping."""
    rename_dict: Dict[str, str] = {}
    for col in df.columns:
        normalised = _normalise_header(col)
        if normalised in col_map:
            rename_dict[col] = col_map[normalised]
    return df.rename(columns=rename_dict)


def _safe_value(val: Any) -> Any:
    """Convert pandas NaN / NaT to None for JSON serialisation;
    convert numpy types to native Python types."""
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    # numpy int / float → Python int / float
    try:
        import numpy as np

        if isinstance(val, (np.integer,)):
            return int(val)
        if isinstance(val, (np.floating,)):
            return float(val)
        if isinstance(val, (np.bool_,)):
            return bool(val)
    except ImportError:
        pass
    # Timestamp → ISO-8601 string
    if isinstance(val, pd.Timestamp):
        return val.isoformat()
    return val


def _safe_str(val: Any) -> Optional[str]:
    """Return a stripped string or None."""
    v = _safe_value(val)
    if v is None:
        return None
    return str(v).strip()


def _safe_float(val: Any) -> Optional[float]:
    """Return a float or None."""
    v = _safe_value(val)
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _build_dict(row: pd.Series, keys: List[str]) -> Dict[str, Any]:
    """Build an output dict from a row, ensuring all required keys are present
    and NaN values are replaced with None."""
    result: Dict[str, Any] = {}
    for key in keys:
        result[key] = _safe_value(row.get(key))
    return result


def _normalise_str_for_comparison(val: Any) -> Optional[str]:
    """Normalise a value to a comparable lowercase stripped string."""
    s = _safe_str(val)
    if s is None:
        return None
    return re.sub(r"\s+", " ", s).strip().lower()


def _normalise_edrpou(val: Any) -> Optional[str]:
    """Strip leading zeros, whitespace, and special chars from an EDRPOU / tax number."""
    s = _safe_str(val)
    if s is None:
        return None
    # Keep only digits
    digits = re.sub(r"\D", "", s)
    return digits if digits else None


def _dates_differ(val_a: Any, val_b: Any) -> bool:
    """Compare two date values; return True if they meaningfully differ."""
    a = _safe_value(val_a)
    b = _safe_value(val_b)
    if a is None and b is None:
        return False
    if a is None or b is None:
        return True
    # Try to parse both as timestamps for date-level comparison
    try:
        ts_a = pd.Timestamp(a)
        ts_b = pd.Timestamp(b)
        return ts_a.date() != ts_b.date()
    except Exception:
        # Fallback to string comparison
        return _normalise_str_for_comparison(a) != _normalise_str_for_comparison(b)


def _areas_differ(land_area: Any, prop_area: Any) -> bool:
    """Return True if the two area values differ beyond the tolerance threshold."""
    a = _safe_float(land_area)
    b = _safe_float(prop_area)
    if a is None and b is None:
        return False
    if a is None or b is None:
        return True
    if a == 0 and b == 0:
        return False
    denominator = max(abs(a), abs(b))
    if denominator == 0:
        return a != b
    return abs(a - b) / denominator > AREA_RELATIVE_TOLERANCE


# ---------------------------------------------------------------------------
# Main processing function
# ---------------------------------------------------------------------------


def process_excel_files(land_file, property_file) -> List[Dict[str, Any]]:
    """
    Read two Excel files (land registry & property registry), merge them on
    common identifiers, validate for data inconsistencies, and return a list
    of Record dicts matching the API schema.

    Parameters
    ----------
    land_file : InMemoryUploadedFile
        The uploaded Excel file with land registry data.
    property_file : InMemoryUploadedFile
        The uploaded Excel file with property registry data.

    Returns
    -------
    list[dict]
        Each dict has keys: ``problems``, ``land_data``, ``property_data``.
    """

    # ------------------------------------------------------------------
    # 1. Read Excel files into DataFrames
    # ------------------------------------------------------------------
    try:
        land_df = pd.read_excel(land_file, engine="openpyxl")
    except Exception as exc:
        logger.error("Failed to parse land Excel file: %s", exc)
        raise ValueError(f"Unable to read the land Excel file: {exc}") from exc

    try:
        prop_df = pd.read_excel(property_file, engine="openpyxl")
    except Exception as exc:
        logger.error("Failed to parse property Excel file: %s", exc)
        raise ValueError(f"Unable to read the property Excel file: {exc}") from exc

    # ------------------------------------------------------------------
    # 2. Normalise column headers
    # ------------------------------------------------------------------
    land_df = _rename_columns(land_df, LAND_COLUMN_MAP)
    prop_df = _rename_columns(prop_df, PROPERTY_COLUMN_MAP)

    # Drop completely empty rows
    land_df = land_df.dropna(how="all").reset_index(drop=True)
    prop_df = prop_df.dropna(how="all").reset_index(drop=True)

    logger.info(
        "Loaded %d land rows and %d property rows",
        len(land_df),
        len(prop_df),
    )

    # ------------------------------------------------------------------
    # 3. Determine merge strategy & merge
    # ------------------------------------------------------------------
    # Strategy A: merge on cadastral_number (present in both)
    # Strategy B: merge on EDRPOU/tax_number (land.edrpou_of_land_user ↔ prop.tax_number_of_pp)
    # We attempt A first; if either DF lacks the column we fall back to B,
    # and finally to a cross-join if no common key exists.

    land_has_cadastral = "cadastral_number" in land_df.columns
    prop_has_cadastral = "cadastral_number" in prop_df.columns
    land_has_edrpou = "edrpou_of_land_user" in land_df.columns
    prop_has_tax = "tax_number_of_pp" in prop_df.columns

    merged_df: pd.DataFrame

    if land_has_cadastral and prop_has_cadastral:
        # Normalise cadastral numbers for matching
        land_df["_merge_cadastral"] = (
            land_df["cadastral_number"].astype(str).str.strip().str.lower()
        )
        prop_df["_merge_cadastral"] = (
            prop_df["cadastral_number"].astype(str).str.strip().str.lower()
        )

        merged_df = pd.merge(
            land_df,
            prop_df,
            on="_merge_cadastral",
            how="outer",
            suffixes=("_land", "_prop"),
            indicator=True,
        )
        merged_df.drop(columns=["_merge_cadastral"], inplace=True, errors="ignore")

    elif land_has_edrpou and prop_has_tax:
        land_df["_merge_edrpou"] = land_df["edrpou_of_land_user"].apply(
            _normalise_edrpou
        )
        prop_df["_merge_edrpou"] = prop_df["tax_number_of_pp"].apply(
            _normalise_edrpou
        )

        merged_df = pd.merge(
            land_df,
            prop_df,
            on="_merge_edrpou",
            how="outer",
            suffixes=("_land", "_prop"),
            indicator=True,
        )
        merged_df.drop(columns=["_merge_edrpou"], inplace=True, errors="ignore")

    else:
        # Fallback: treat every land row + every property row independently
        logger.warning(
            "No common merge key found between the two files. "
            "Processing each file independently."
        )
        land_df["_merge_key"] = range(len(land_df))
        prop_df["_merge_key"] = range(len(prop_df))
        # Pad the shorter DF so they align 1-to-1 as much as possible
        max_len = max(len(land_df), len(prop_df))
        if len(land_df) < max_len:
            extra = pd.DataFrame(
                {"_merge_key": range(len(land_df), max_len)}
            )
            land_df = pd.concat([land_df, extra], ignore_index=True)
        if len(prop_df) < max_len:
            extra = pd.DataFrame(
                {"_merge_key": range(len(prop_df), max_len)}
            )
            prop_df = pd.concat([prop_df, extra], ignore_index=True)

        merged_df = pd.merge(
            land_df,
            prop_df,
            on="_merge_key",
            how="outer",
            suffixes=("_land", "_prop"),
            indicator=True,
        )
        merged_df.drop(columns=["_merge_key"], inplace=True, errors="ignore")

    # ------------------------------------------------------------------
    # 4. Resolve suffixed columns back to canonical names
    # ------------------------------------------------------------------
    # After an outer merge, columns that existed in both DFs get _land / _prop
    # suffixes.  We need to resolve them so that land_data and property_data
    # each get the correct value.

    def _resolve_col(df: pd.DataFrame, key: str, suffix: str) -> pd.Series:
        """Return the column for *key* with the given *suffix*, falling back
        to the un-suffixed column if the suffixed one doesn't exist."""
        suffixed = f"{key}_{suffix}"
        if suffixed in df.columns:
            return df[suffixed]
        if key in df.columns:
            return df[key]
        return pd.Series([None] * len(df), dtype=object)

    # ------------------------------------------------------------------
    # 5. Build output records with validation
    # ------------------------------------------------------------------
    records: List[Dict[str, Any]] = []

    for idx in range(len(merged_df)):
        row = merged_df.iloc[idx]
        merge_indicator = row.get("_merge", "both")

        problems: List[str] = []

        # --- Build land_data dict ---
        land_row: Dict[str, Any] = {}
        for key in LAND_DATA_KEYS:
            col_val = _resolve_col(merged_df, key, "land").iloc[idx]
            land_row[key] = col_val
        land_data = {k: _safe_value(v) for k, v in land_row.items()}

        # --- Build property_data dict ---
        prop_row: Dict[str, Any] = {}
        for key in PROPERTY_DATA_KEYS:
            col_val = _resolve_col(merged_df, key, "prop").iloc[idx]
            prop_row[key] = col_val
        property_data = {k: _safe_value(v) for k, v in prop_row.items()}

        # ---------------------------------------------------------------
        # Validation checks (only when both sides have data)
        # ---------------------------------------------------------------

        has_land = merge_indicator in ("left_only", "both")
        has_prop = merge_indicator in ("right_only", "both")

        if has_land and has_prop:
            # 1) EDRPOU / Tax number mismatch
            edrpou_land = _normalise_edrpou(land_data.get("edrpou_of_land_user"))
            edrpou_prop = _normalise_edrpou(property_data.get("tax_number_of_pp"))
            if edrpou_land and edrpou_prop and edrpou_land != edrpou_prop:
                problems.append("edrpou_of_land_user")
            elif (edrpou_land is None) != (edrpou_prop is None):
                # One side missing
                problems.append("edrpou_of_land_user")

            # 2) Land user / taxpayer name mismatch
            name_land = _normalise_str_for_comparison(land_data.get("land_user"))
            name_prop = _normalise_str_for_comparison(
                property_data.get("name_of_the_taxpayer")
            )
            if name_land and name_prop and name_land != name_prop:
                problems.append("land_user")
            elif (name_land is None) != (name_prop is None):
                problems.append("land_user")

            # 3) Location mismatch
            loc_land = _normalise_str_for_comparison(land_data.get("location"))
            loc_prop = _normalise_str_for_comparison(
                property_data.get("address_of_the_object")
            )
            if loc_land and loc_prop and loc_land != loc_prop:
                problems.append("location")
            elif (loc_land is None) != (loc_prop is None):
                problems.append("location")

            # 4) Area deviation
            if _areas_differ(land_data.get("area"), property_data.get("total_area")):
                problems.append("area")

            # 5) Date of state registration of ownership mismatch
            if _dates_differ(
                land_data.get("date_of_state_registration_of_ownership"),
                property_data.get("date_of_state_registration_of_ownership"),
            ):
                problems.append("date_of_state_registration_of_ownership")

            # 6) Share of ownership mismatch
            share_land = _safe_float(land_data.get("share_of_ownership"))
            share_prop = _safe_float(property_data.get("share_of_ownership"))
            if share_land is not None and share_prop is not None:
                if abs(share_land - share_prop) > 1e-6:
                    problems.append("share_of_ownership")
            elif (share_land is None) != (share_prop is None):
                problems.append("share_of_ownership")

            # 7) Purpose mismatch (land purpose vs property type_of_object)
            purpose_land = _normalise_str_for_comparison(land_data.get("purpose"))
            purpose_prop = _normalise_str_for_comparison(
                property_data.get("type_of_object")
            )
            if purpose_land and purpose_prop and purpose_land != purpose_prop:
                problems.append("purpose")
            elif (purpose_land is None) != (purpose_prop is None):
                problems.append("purpose")

        elif has_land and not has_prop:
            # Land row without matching property — flag all property-relevant fields
            problems.extend(
                [
                    "edrpou_of_land_user",
                    "land_user",
                    "location",
                    "area",
                    "date_of_state_registration_of_ownership",
                    "share_of_ownership",
                    "purpose",
                ]
            )

        elif has_prop and not has_land:
            # Property row without matching land — flag all land-relevant fields
            problems.extend(
                [
                    "edrpou_of_land_user",
                    "land_user",
                    "location",
                    "area",
                    "date_of_state_registration_of_ownership",
                    "share_of_ownership",
                    "purpose",
                ]
            )

        # Ensure only valid enums
        problems = [p for p in problems if p in VALID_PROBLEMS]

        records.append(
            {
                "problems": problems,
                "land_data": land_data,
                "property_data": property_data,
            }
        )

    logger.info("Processed %d total records (%d with problems)",
                len(records),
                sum(1 for r in records if r["problems"]))

    return records
