"""
response_parser.py
===================
Parses Claude's raw JSON response into structured CodingResult objects.

Handles:
  - Malformed JSON (strips markdown fences, fixes common issues)
  - Missing sections (returns empty arrays, not crashes)
  - Low confidence flagging
  - Evidence and coding note extraction
  - UB-04 field position mapping
"""

import json
import re
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CodingResult:
    session_id: str
    clinical_summary: str = ""
    principal_diagnosis: dict = field(default_factory=dict)
    secondary_diagnoses: list = field(default_factory=list)
    icd10_pcs: list = field(default_factory=list)
    cpt_codes: list = field(default_factory=list)
    hcpcs_codes: list = field(default_factory=list)
    ms_drg: dict = field(default_factory=dict)
    revenue_codes: list = field(default_factory=list)
    occurrence_codes: list = field(default_factory=list)
    value_codes: list = field(default_factory=list)
    condition_codes: list = field(default_factory=list)
    type_of_bill: dict = field(default_factory=dict)
    coding_flags: list = field(default_factory=list)
    validation_errors: list = field(default_factory=list)
    overall_confidence: float = 0.0
    codes_requiring_review: list = field(default_factory=list)
    raw_response: str = ""


# ---------------------------------------------------------------------------
# UB-04 field mappings
# ---------------------------------------------------------------------------

UB04_FIELD_MAP = {
    "type_of_bill":        "FL 4",
    "principal_diagnosis": "FL 67",
    "secondary_diagnoses": "FL 67A-Q",
    "icd10_pcs":           "FL 74",
    "cpt_codes":           "FL 44",
    "revenue_codes":       "FL 42",
    "occurrence_codes":    "FL 31-34",
    "value_codes":         "FL 39-41",
    "condition_codes":     "FL 18-28",
    "ms_drg":              "FL 71",
}


# ---------------------------------------------------------------------------
# JSON cleaning
# ---------------------------------------------------------------------------

def _clean_json(raw: str) -> str:
    """Strip markdown fences and leading/trailing whitespace."""
    text = raw.strip()
    # Remove ```json ... ``` fences
    text = re.sub(r"^```json\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^```\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)
    text = text.strip()

    # Find the first { and last } to extract JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]

    return text


# ---------------------------------------------------------------------------
# Section parsers
# ---------------------------------------------------------------------------

def _safe_list(data: dict, key: str) -> list:
    val = data.get(key, [])
    return val if isinstance(val, list) else []


def _safe_dict(data: dict, key: str) -> dict:
    val = data.get(key, {})
    return val if isinstance(val, dict) else {}


def _parse_diagnosis(raw: dict) -> dict:
    """Normalize a single diagnosis code entry."""
    if not raw or not isinstance(raw, dict):
        return {}
    return {
        "code": str(raw.get("code", "")).upper().strip(),
        "description": raw.get("description", ""),
        "confidence": float(raw.get("confidence", 0.0)),
        "evidence": raw.get("evidence", ""),
        "coding_note": raw.get("coding_note", ""),
        "ub04_field": UB04_FIELD_MAP["principal_diagnosis"],
    }


def _parse_code_list(raw_list: list, code_type: str) -> list:
    """Normalize a list of code entries."""
    result = []
    ub04 = UB04_FIELD_MAP.get(code_type, "")
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code", "")).strip()
        if not code:
            continue
        parsed = {
            "code": code,
            "description": item.get("description", ""),
            "confidence": float(item.get("confidence", 0.0)),
            "evidence": item.get("evidence", ""),
            "ub04_field": ub04,
        }
        # Type-specific fields
        if code_type == "cpt_codes":
            parsed["modifier"] = item.get("modifier")
            parsed["units"] = int(item.get("units", 1))
        elif code_type == "hcpcs_codes":
            parsed["units"] = int(item.get("units", 1))
        elif code_type == "revenue_codes":
            parsed["related_cpt_hcpcs"] = item.get("related_cpt_hcpcs")
            parsed["units"] = int(item.get("units", 1))
        elif code_type == "occurrence_codes":
            parsed["date"] = item.get("date")
        elif code_type == "value_codes":
            parsed["amount"] = float(item.get("amount", 0.0))
        elif code_type == "condition_codes":
            pass  # no extra fields

        result.append(parsed)
    return result


def _parse_ms_drg(raw: dict) -> dict:
    if not raw or not isinstance(raw, dict):
        return {}
    return {
        "drg_number": str(raw.get("drg_number", "")).strip(),
        "description": raw.get("description", ""),
        "mdc": raw.get("mdc", ""),
        "drg_type": raw.get("drg_type", ""),
        "geometric_mean_los": float(raw.get("geometric_mean_los", 0.0)),
        "confidence": float(raw.get("confidence", 0.0)),
        "note": raw.get("note", ""),
        "ub04_field": UB04_FIELD_MAP["ms_drg"],
    }


def _parse_tob(raw: dict) -> dict:
    if not raw or not isinstance(raw, dict):
        return {}
    return {
        "code": str(raw.get("code", "")).strip(),
        "description": raw.get("description", ""),
        "facility_type_digit": raw.get("facility_type_digit", ""),
        "care_type_digit": raw.get("care_type_digit", ""),
        "sequence_digit": raw.get("sequence_digit", raw.get("frequency_digit", "")),
        "confidence": float(raw.get("confidence", 0.0)),
        "ub04_field": UB04_FIELD_MAP["type_of_bill"],
    }


def _parse_flags(raw_list: list) -> list:
    result = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        result.append({
            "flag_type": item.get("flag_type", "INFO"),
            "message": item.get("message", ""),
        })
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_coding_response(raw_response: str, session_id: str) -> CodingResult:
    """
    Parse Claude's raw text response into a CodingResult.

    Args:
        raw_response : Raw text from Claude API response.
        session_id   : For error logging.

    Returns:
        CodingResult dataclass with all sections populated.
    """
    result = CodingResult(session_id=session_id, raw_response=raw_response)

    try:
        cleaned = _clean_json(raw_response)
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"[{session_id}] JSON parse failed: {e}. Raw: {raw_response[:500]}")
        result.validation_errors.append(f"Response parse error: {str(e)}")
        result.coding_flags.append({
            "flag_type": "WARNING",
            "message": "Claude response could not be parsed. Manual coding required."
        })
        return result

    # --- Parse all sections ---
    result.clinical_summary = data.get("clinical_summary", "")
    result.principal_diagnosis = _parse_diagnosis(data.get("principal_diagnosis", {}))
    result.secondary_diagnoses = [
        _parse_diagnosis(d) for d in _safe_list(data, "secondary_diagnoses")
    ]

    procedures = _safe_dict(data, "procedures")
    result.icd10_pcs = _parse_code_list(_safe_list(procedures, "icd10_pcs"), "icd10_pcs")
    result.cpt_codes = _parse_code_list(_safe_list(procedures, "cpt"), "cpt_codes")
    result.hcpcs_codes = _parse_code_list(_safe_list(procedures, "hcpcs"), "hcpcs_codes")

    result.ms_drg = _parse_ms_drg(data.get("ms_drg", {}))
    result.revenue_codes = _parse_code_list(_safe_list(data, "revenue_codes"), "revenue_codes")
    result.occurrence_codes = _parse_code_list(_safe_list(data, "occurrence_codes"), "occurrence_codes")
    result.value_codes = _parse_code_list(_safe_list(data, "value_codes"), "value_codes")
    result.condition_codes = _parse_code_list(_safe_list(data, "condition_codes"), "condition_codes")
    result.type_of_bill = _parse_tob(data.get("type_of_bill", {}))
    result.coding_flags = _parse_flags(_safe_list(data, "coding_flags"))
    result.overall_confidence = float(data.get("overall_confidence", 0.0))
    result.codes_requiring_review = data.get("codes_requiring_review", [])

    logger.info(
        f"[{session_id}] Parsed: principal={result.principal_diagnosis.get('code','?')}, "
        f"secondary={len(result.secondary_diagnoses)}, CPT={len(result.cpt_codes)}, "
        f"revenue={len(result.revenue_codes)}, TOB={result.type_of_bill.get('code','?')}, "
        f"confidence={result.overall_confidence}"
    )

    return result
