"""
claude_coding_engine.py
========================
Replaces coding_engine.py entirely.

Sends de-identified clinical text to Claude API and returns
structured medical codes across all code types:
  ICD-10-CM, ICD-10-PCS, CPT, HCPCS, MS-DRG,
  Revenue Codes, Occurrence Codes, Value Codes,
  Condition Codes, Type of Bill.

Flow:
  1. Verify text is PHI-free
  2. Build prompt
  3. Call Claude API (claude-sonnet-4-5 model)
  4. Parse and validate response
  5. Run edit checks (MUE/NCCI) via code_validator.py
  6. Return structured coding result

Set ANTHROPIC_API_KEY in environment variables.
BAA must be signed with Anthropic before production use.
"""

import os
import json
import logging
import time
from typing import Optional
from datetime import datetime, timezone

from prompts.medical_coding_prompt import build_coding_prompt, get_system_prompt
from prompts.tob_prompt import build_tob_prompt
from response_parser import parse_coding_response, CodingResult
from code_validator import validate_coding_result
from baa_compliance_logger import log_api_call
from phi_purger_v2 import verify_phi_free

logger = logging.getLogger(__name__)

CLAUDE_MODEL = "claude-sonnet-4-5-20251022"
MAX_TOKENS = 4096
MIN_CONFIDENCE_THRESHOLD = 0.80


class CodingEngineError(Exception):
    pass


class PHILeakError(CodingEngineError):
    """Raised when PHI is detected in text before Claude API call."""
    pass


def run_coding_session(
    deidentified_text: str,
    phi_audit_report: dict,
    session_id: str,
    payer: str = "Medicare",
    facility_type: str = "Hospital",
    claim_type: str = "UB-04",
    patient_status: str = "Inpatient",
    specialty: Optional[str] = None,
) -> dict:
    """
    Main entry point for AI-powered medical coding.

    Args:
        deidentified_text : Output of phi_purger_v2.purge_phi()
        phi_audit_report  : Audit dict from phi_purger_v2 (logged, not sent to Claude)
        session_id        : Coding session ID for audit trail
        payer             : Medicare | Medicaid | Commercial
        facility_type     : Hospital | Clinic | SNF | ASC
        claim_type        : UB-04 | CMS-1500
        patient_status    : Inpatient | Outpatient | Emergency | Observation
        specialty         : Optional specialty hint

    Returns:
        Full coding result dict with all code types, confidence scores, and flags.

    Raises:
        PHILeakError      : If PHI detected in text — API call blocked.
        CodingEngineError : On API failure or invalid response.
    """

    # --- Gate 1: PHI verification before ANY external call ---
    if not verify_phi_free(deidentified_text):
        logger.critical(f"PHI leak detected for session {session_id} — API call BLOCKED")
        raise PHILeakError(
            "PHI detected in text after purge. API call blocked. "
            "Review phi_purger_v2 output before retrying."
        )

    if len(deidentified_text.strip()) < 50:
        raise CodingEngineError("Text too short for meaningful coding. Minimum 50 characters required.")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise CodingEngineError("ANTHROPIC_API_KEY not set in environment variables.")

    # --- Build prompt ---
    messages = build_coding_prompt(
        deidentified_text=deidentified_text,
        payer=payer,
        facility_type=facility_type,
        claim_type=claim_type,
        patient_status=patient_status,
        specialty=specialty,
    )
    system_prompt = get_system_prompt()

    # --- Call Claude API ---
    start_time = time.time()
    raw_response = _call_claude_api(
        api_key=api_key,
        system=system_prompt,
        messages=messages,
    )
    elapsed_ms = int((time.time() - start_time) * 1000)

    # --- Log the API call for BAA compliance ---
    log_api_call(
        session_id=session_id,
        input_char_count=len(deidentified_text),
        output_char_count=len(raw_response),
        response_time_ms=elapsed_ms,
        phi_audit=phi_audit_report,
        payer=payer,
        patient_status=patient_status,
    )

    # --- Parse response ---
    coding_result: CodingResult = parse_coding_response(raw_response, session_id)

    # --- Run TOB verification if low confidence ---
    if coding_result.type_of_bill and coding_result.type_of_bill.get("confidence", 0) < 0.90:
        tob_result = _verify_tob(
            deidentified_text=deidentified_text,
            api_key=api_key,
            facility_type=facility_type,
            patient_status=patient_status,
            payer=payer,
        )
        if tob_result:
            coding_result.type_of_bill = tob_result

    # --- Validate codes (MUE/NCCI/Revenue-CPT pairing) ---
    validated_result = validate_coding_result(coding_result)

    # --- Build final output ---
    return _build_output(
        validated_result=validated_result,
        session_id=session_id,
        elapsed_ms=elapsed_ms,
        payer=payer,
        claim_type=claim_type,
    )


def _call_claude_api(api_key: str, system: str, messages: list) -> str:
    """
    Call Anthropic Claude API.
    Returns raw text response from Claude.
    """
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=messages,
        )

        if not response.content:
            raise CodingEngineError("Empty response from Claude API.")

        return response.content[0].text

    except ImportError:
        raise CodingEngineError(
            "anthropic package not installed. Run: pip install anthropic"
        )
    except Exception as e:
        logger.error(f"Claude API call failed: {e}")
        raise CodingEngineError(f"Claude API error: {str(e)}")


def _verify_tob(
    deidentified_text: str,
    api_key: str,
    facility_type: str,
    patient_status: str,
    payer: str,
) -> Optional[dict]:
    """
    Secondary Claude call focused solely on Type of Bill determination.
    Called when main prompt TOB confidence < 0.90.
    """
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        messages = build_tob_prompt(deidentified_text, facility_type, patient_status, payer)

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=512,
            messages=messages,
        )

        raw = response.content[0].text.strip()
        clean = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean)
        return parsed.get("type_of_bill")

    except Exception as e:
        logger.warning(f"TOB verification call failed: {e}")
        return None


def _build_output(
    validated_result,
    session_id: str,
    elapsed_ms: int,
    payer: str,
    claim_type: str,
) -> dict:
    """Assemble final structured output dict."""
    vr = validated_result

    low_confidence = [
        c for c in (
            [vr.principal_diagnosis] +
            vr.secondary_diagnoses +
            vr.cpt_codes +
            vr.hcpcs_codes +
            vr.revenue_codes
        )
        if isinstance(c, dict) and c.get("confidence", 1.0) < MIN_CONFIDENCE_THRESHOLD
    ]

    return {
        "session_id": session_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "payer": payer,
        "claim_type": claim_type,
        "response_time_ms": elapsed_ms,
        "clinical_summary": vr.clinical_summary,

        # Diagnosis codes
        "principal_diagnosis": vr.principal_diagnosis,
        "secondary_diagnoses": vr.secondary_diagnoses,

        # Procedure codes
        "icd10_pcs": vr.icd10_pcs,
        "cpt_codes": vr.cpt_codes,
        "hcpcs_codes": vr.hcpcs_codes,

        # Grouper
        "ms_drg": vr.ms_drg,

        # UB-04 specific
        "revenue_codes": vr.revenue_codes,
        "occurrence_codes": vr.occurrence_codes,
        "value_codes": vr.value_codes,
        "condition_codes": vr.condition_codes,
        "type_of_bill": vr.type_of_bill,

        # Quality
        "coding_flags": vr.coding_flags,
        "validation_errors": vr.validation_errors,
        "overall_confidence": vr.overall_confidence,
        "codes_requiring_review": [
            c.get("code") for c in low_confidence if isinstance(c, dict)
        ],
        "requires_human_review": len(low_confidence) > 0 or len(vr.validation_errors) > 0,
    }
