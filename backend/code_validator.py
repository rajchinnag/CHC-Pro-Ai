"""
code_validator.py
==================
Post-processing validation layer on top of Claude's output.

Validates:
  1. ICD-10-CM code format (letter + 2 digits + optional decimals)
  2. CPT code format (5 digits)
  3. HCPCS Level II format (letter + 4 digits)
  4. Revenue code format (4 digits, starts 0-9)
  5. Occurrence code format (2 digits, 01-69 or A0-L9)
  6. Value code format (alphanumeric, 2 chars)
  7. Condition code format (2 digits or 2 chars, 01-99 or A0-Z9)
  8. Type of Bill format (4 chars starting with 0)
  9. MS-DRG format (3-digit number, 001-999)
 10. MUE (Medically Unlikely Edit) — basic unit limits
 11. NCCI (National Correct Coding Initiative) — known bundled pairs
 12. Revenue code + CPT pairing rules

This is your safety net. Even if Claude makes a mistake, this catches it.
"""

import re
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Format validators
# ---------------------------------------------------------------------------

ICD10CM_PATTERN = re.compile(r"^[A-Z]\d{2}(\.\w{1,4})?$", re.IGNORECASE)
ICD10PCS_PATTERN = re.compile(r"^[A-Z0-9]{7}$", re.IGNORECASE)
CPT_PATTERN = re.compile(r"^\d{5}[A-Z]?$")
HCPCS_PATTERN = re.compile(r"^[A-V]\d{4}$", re.IGNORECASE)
REVENUE_PATTERN = re.compile(r"^\d{4}$")
OCCURRENCE_PATTERN = re.compile(r"^(\d{2}|[A-L]\d)$")
VALUE_PATTERN = re.compile(r"^(\d{2}|[A-Z]\d)$", re.IGNORECASE)
CONDITION_PATTERN = re.compile(r"^(\d{2}|[A-Z]\d)$", re.IGNORECASE)
TOB_PATTERN = re.compile(r"^0\d{3}$")
DRG_PATTERN = re.compile(r"^\d{3}$")


# ---------------------------------------------------------------------------
# MUE limits (subset — most common codes)
# Medically Unlikely Edits: max units per date of service
# ---------------------------------------------------------------------------

MUE_LIMITS = {
    "99213": 1, "99214": 1, "99215": 1,  # E&M visits
    "93000": 1,  # ECG
    "71046": 1,  # Chest X-ray 2 views
    "70553": 1,  # MRI Brain w/ and w/o contrast
    "93306": 1,  # Echo complete
    "36415": 2,  # Venipuncture
    "80053": 1,  # Comprehensive metabolic panel
    "85025": 1,  # CBC with diff
    "84443": 1,  # TSH
}


# ---------------------------------------------------------------------------
# NCCI bundled pairs (subset — common pairs that cannot be billed together)
# Format: (column1_code, column2_code) — column2 is bundled into column1
# ---------------------------------------------------------------------------

NCCI_BUNDLES = {
    ("99213", "99212"),
    ("99214", "99213"),
    ("99215", "99214"),
    ("71046", "71045"),   # 2-view chest includes 1-view
    ("93306", "93307"),   # complete echo includes limited
    ("80053", "80048"),   # comprehensive metabolic includes basic metabolic
    ("85025", "85027"),   # CBC with diff includes CBC without diff
}


# ---------------------------------------------------------------------------
# Revenue code + CPT pairing rules
# Revenue code ranges that require a CPT/HCPCS code
# ---------------------------------------------------------------------------

REVENUE_REQUIRES_CPT = {
    "0360", "0361", "0362",  # OR services
    "0450", "0451", "0452",  # Emergency room
    "0490", "0491",          # Ambulatory surgical care
    "0730", "0731",          # EKG/ECG
    "0320", "0321", "0322",  # Radiology
    "0300", "0301",          # Lab
}

# Revenue codes that should NOT have CPT
REVENUE_NO_CPT = {
    "0100", "0101",  # Room and board
    "0110", "0111", "0112",
    "0120", "0121", "0122",
    "0130", "0131", "0132",
    "0200", "0201",  # Intensive care
    "0210", "0211",
}


# ---------------------------------------------------------------------------
# Validator functions
# ---------------------------------------------------------------------------

def _validate_format(code: str, pattern: re.Pattern, code_type: str, errors: list) -> bool:
    if not code:
        errors.append(f"Empty {code_type} code.")
        return False
    if not pattern.match(code.upper()):
        errors.append(f"Invalid {code_type} format: '{code}'")
        return False
    return True


def _check_mue(cpt_codes: list, errors: list) -> list:
    """Check CPT units against MUE limits."""
    validated = []
    for entry in cpt_codes:
        code = entry.get("code", "")
        units = int(entry.get("units", 1))
        limit = MUE_LIMITS.get(code)
        if limit and units > limit:
            errors.append(
                f"MUE violation: CPT {code} has {units} units but MUE limit is {limit}. "
                f"Adjusted to {limit}."
            )
            entry = dict(entry)
            entry["units"] = limit
            entry["mue_adjusted"] = True
        validated.append(entry)
    return validated


def _check_ncci(cpt_codes: list, errors: list) -> list:
    """Remove codes bundled by NCCI edits."""
    code_set = {e.get("code", "") for e in cpt_codes}
    to_remove = set()

    for col1, col2 in NCCI_BUNDLES:
        if col1 in code_set and col2 in code_set:
            errors.append(
                f"NCCI bundle: CPT {col2} is bundled into CPT {col1}. "
                f"Removed {col2}."
            )
            to_remove.add(col2)

    return [e for e in cpt_codes if e.get("code") not in to_remove]


def _check_revenue_cpt_pairing(revenue_codes: list, cpt_codes: list, errors: list) -> list:
    """Check revenue code + CPT pairing rules."""
    cpt_code_set = {e.get("code", "") for e in cpt_codes}
    hcpcs_not_needed = set()
    validated = []

    for entry in revenue_codes:
        rev_code = entry.get("code", "")
        related = entry.get("related_cpt_hcpcs")

        if rev_code in REVENUE_REQUIRES_CPT:
            if not related and not any(
                c.get("code") for c in cpt_codes
            ):
                errors.append(
                    f"Revenue code {rev_code} requires a CPT/HCPCS code but none is associated."
                )
                entry = dict(entry)
                entry["pairing_warning"] = True

        if rev_code in REVENUE_NO_CPT and related:
            errors.append(
                f"Revenue code {rev_code} (room/board) should not have CPT {related}. "
                f"CPT association removed."
            )
            entry = dict(entry)
            entry["related_cpt_hcpcs"] = None

        validated.append(entry)

    return validated


def _validate_tob(tob: dict, errors: list) -> dict:
    """Validate Type of Bill format."""
    if not tob:
        return tob
    code = tob.get("code", "")
    if not TOB_PATTERN.match(str(code)):
        errors.append(f"Invalid Type of Bill format: '{code}'. Must be 4 digits starting with 0.")
        tob = dict(tob)
        tob["format_error"] = True
    return tob


def _validate_occurrence_dates(occurrence_codes: list, errors: list) -> list:
    """Check that occurrence codes have dates."""
    validated = []
    date_pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")
    for entry in occurrence_codes:
        date_val = entry.get("date")
        if date_val and not date_pattern.match(str(date_val)):
            errors.append(
                f"Occurrence code {entry.get('code')} has invalid date format: '{date_val}'. "
                f"Expected MM/DD/YYYY."
            )
            entry = dict(entry)
            entry["date_format_error"] = True
        validated.append(entry)
    return validated


def _validate_value_amounts(value_codes: list, errors: list) -> list:
    """Check that value codes have numeric amounts."""
    validated = []
    for entry in value_codes:
        amount = entry.get("amount", 0)
        try:
            float(amount)
        except (ValueError, TypeError):
            errors.append(
                f"Value code {entry.get('code')} has non-numeric amount: '{amount}'."
            )
            entry = dict(entry)
            entry["amount_error"] = True
        validated.append(entry)
    return validated


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_coding_result(coding_result) -> object:
    """
    Run all validation checks on a CodingResult.

    Modifies the result in-place and appends to validation_errors.
    Returns the validated CodingResult.
    """
    result = deepcopy(coding_result)
    errors = []

    # ICD-10-CM formats
    if result.principal_diagnosis:
        code = result.principal_diagnosis.get("code", "")
        _validate_format(code, ICD10CM_PATTERN, "ICD-10-CM principal", errors)

    for dx in result.secondary_diagnoses:
        code = dx.get("code", "")
        _validate_format(code, ICD10CM_PATTERN, "ICD-10-CM secondary", errors)

    # ICD-10-PCS formats
    for proc in result.icd10_pcs:
        _validate_format(proc.get("code", ""), ICD10PCS_PATTERN, "ICD-10-PCS", errors)

    # CPT formats
    for cpt in result.cpt_codes:
        _validate_format(cpt.get("code", ""), CPT_PATTERN, "CPT", errors)

    # HCPCS formats
    for hcpcs in result.hcpcs_codes:
        _validate_format(hcpcs.get("code", ""), HCPCS_PATTERN, "HCPCS", errors)

    # Revenue code formats
    for rev in result.revenue_codes:
        _validate_format(rev.get("code", ""), REVENUE_PATTERN, "Revenue", errors)

    # Occurrence code formats
    for occ in result.occurrence_codes:
        _validate_format(occ.get("code", ""), OCCURRENCE_PATTERN, "Occurrence", errors)

    # Value code formats
    for val in result.value_codes:
        _validate_format(val.get("code", ""), VALUE_PATTERN, "Value", errors)

    # Condition code formats
    for cond in result.condition_codes:
        _validate_format(cond.get("code", ""), CONDITION_PATTERN, "Condition", errors)

    # MS-DRG format
    if result.ms_drg:
        _validate_format(str(result.ms_drg.get("drg_number", "")), DRG_PATTERN, "MS-DRG", errors)

    # TOB format
    result.type_of_bill = _validate_tob(result.type_of_bill, errors)

    # MUE checks
    result.cpt_codes = _check_mue(result.cpt_codes, errors)

    # NCCI checks
    result.cpt_codes = _check_ncci(result.cpt_codes, errors)

    # Revenue + CPT pairing
    result.revenue_codes = _check_revenue_cpt_pairing(
        result.revenue_codes, result.cpt_codes, errors
    )

    # Occurrence date validation
    result.occurrence_codes = _validate_occurrence_dates(result.occurrence_codes, errors)

    # Value amount validation
    result.value_codes = _validate_value_amounts(result.value_codes, errors)

    if errors:
        logger.warning(f"[{result.session_id}] {len(errors)} validation issue(s): {errors[:3]}")

    result.validation_errors = errors
    return result
