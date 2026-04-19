"""
prompts/medical_coding_prompt.py
=================================
Master prompt template for Claude medical coding.

This is the most critical file in the system.
The quality of every code Claude returns depends on this prompt.

Covers:
  - ICD-10-CM (diagnosis)
  - ICD-10-PCS (inpatient procedures)
  - CPT (outpatient procedures)
  - HCPCS Level II (supplies, drugs, DME)
  - Revenue Codes (UB-04 FL 42)
  - Occurrence Codes + Dates (UB-04 FL 31-34)
  - Value Codes + Amounts (UB-04 FL 39-41)
  - Condition Codes (UB-04 FL 18-28)
  - Type of Bill (UB-04 FL 4)
  - MS-DRG (Medicare inpatient)
"""

from typing import Optional


SYSTEM_PROMPT = """You are a dual-credentialed medical coder with CPC (Certified Professional Coder) 
and CCS (Certified Coding Specialist) certifications, with 15 years of experience in both 
facility (UB-04) and professional (CMS-1500) claim coding across all specialties.

You follow Official ICD-10-CM/PCS Guidelines, AHA Coding Clinic guidance, CPT Assistant 
guidelines, and CMS Claims Processing Manual instructions precisely.

CRITICAL RULES YOU MUST FOLLOW:
1. NEVER code a condition that is documented as "suspected", "rule out", "possible", 
   "probable", or "?". For outpatient — code the sign/symptom instead.
2. NEVER code a condition documented as "no evidence of", "denied", "negative for", 
   or "resolved" as an active diagnosis.
3. "History of" means the condition is no longer active — use personal history codes (Z87.x).
4. Code to the HIGHEST level of specificity available in the documentation.
5. Sequence principal diagnosis first (the condition chiefly responsible for admission/visit).
6. Code all conditions that affect patient care, treatment, or management.
7. For Revenue Codes — every revenue code line must have a corresponding CPT/HCPCS code 
   where applicable per UB-04 billing guidelines.
8. Type of Bill is ALWAYS a 4-character code starting with 0 (e.g., 0111, 0131, 0721).
9. Occurrence codes require dates. Value codes require amounts. Always include them.
10. Return ONLY valid, currently active codes — do not invent or approximate codes.

You think step by step through the clinical documentation before assigning any code."""


def build_coding_prompt(
    deidentified_text: str,
    payer: str = "Medicare",
    facility_type: str = "Hospital",
    claim_type: str = "UB-04",
    patient_status: str = "Inpatient",
    specialty: Optional[str] = None,
) -> list:
    """
    Build the messages list for the Claude API call.

    Args:
        deidentified_text : PHI-purged clinical note text.
        payer             : Medicare | Medicaid | Commercial | Managed Care
        facility_type     : Hospital | Clinic | SNF | Home Health | Hospice | ASC
        claim_type        : UB-04 | CMS-1500
        patient_status    : Inpatient | Outpatient | Emergency | Observation
        specialty         : Optional clinical specialty hint (e.g. Cardiology, Orthopedics)

    Returns:
        List of message dicts for the Claude messages API.
    """

    specialty_context = f"\nClinical Specialty Context: {specialty}" if specialty else ""

    user_prompt = f"""MEDICAL CODING TASK
===================
Payer            : {payer}
Facility Type    : {facility_type}
Claim Form       : {claim_type}
Patient Status   : {patient_status}{specialty_context}

DE-IDENTIFIED CLINICAL DOCUMENTATION:
--------------------------------------
{deidentified_text}
--------------------------------------

INSTRUCTIONS:
Carefully read the full clinical documentation above. Think through the case step by step.
Then return a single valid JSON object with EXACTLY this structure — no markdown, no 
explanation text, just the raw JSON:

{{
  "clinical_summary": "2-3 sentence summary of the encounter in coding terms",
  
  "principal_diagnosis": {{
    "code": "ICD-10-CM code",
    "description": "full official code description",
    "confidence": 0.00,
    "evidence": "exact phrase from the note that supports this code",
    "coding_note": "brief rationale per official guidelines"
  }},
  
  "secondary_diagnoses": [
    {{
      "code": "ICD-10-CM code",
      "description": "full official code description",
      "confidence": 0.00,
      "evidence": "exact phrase from the note",
      "coding_note": "why this affects care or management"
    }}
  ],
  
  "procedures": {{
    "icd10_pcs": [
      {{
        "code": "7-character ICD-10-PCS code",
        "description": "full description",
        "confidence": 0.00,
        "evidence": "procedure documented in note"
      }}
    ],
    "cpt": [
      {{
        "code": "CPT code",
        "description": "full description",
        "modifier": "modifier if applicable or null",
        "units": 1,
        "confidence": 0.00,
        "evidence": "procedure documented in note"
      }}
    ],
    "hcpcs": [
      {{
        "code": "HCPCS Level II code",
        "description": "full description",
        "units": 1,
        "confidence": 0.00,
        "evidence": "item or service documented"
      }}
    ]
  }},
  
  "ms_drg": {{
    "drg_number": "3-digit DRG",
    "description": "full DRG description",
    "mdc": "Major Diagnostic Category number and name",
    "drg_type": "Medical or Surgical",
    "geometric_mean_los": 0.0,
    "confidence": 0.00,
    "note": "MCC/CC present or absent"
  }},
  
  "revenue_codes": [
    {{
      "revenue_code": "4-digit revenue code",
      "description": "revenue code description",
      "related_cpt_hcpcs": "associated CPT or HCPCS code or null",
      "units": 1,
      "confidence": 0.00,
      "evidence": "service documented"
    }}
  ],
  
  "occurrence_codes": [
    {{
      "code": "2-digit occurrence code",
      "description": "occurrence code description",
      "date": "MM/DD/YYYY or null if not documented",
      "confidence": 0.00,
      "evidence": "event documented in note"
    }}
  ],
  
  "value_codes": [
    {{
      "code": "2-character value code",
      "description": "value code description",
      "amount": 0.00,
      "confidence": 0.00,
      "evidence": "value documented in note"
    }}
  ],
  
  "condition_codes": [
    {{
      "code": "2-digit condition code",
      "description": "condition code description",
      "confidence": 0.00,
      "evidence": "condition documented"
    }}
  ],
  
  "type_of_bill": {{
    "code": "4-character TOB starting with 0",
    "description": "full TOB description",
    "facility_type_digit": "first digit meaning",
    "care_type_digit": "second digit meaning",
    "sequence_digit": "third digit meaning",
    "confidence": 0.00
  }},
  
  "coding_flags": [
    {{
      "flag_type": "QUERY | WARNING | INFO",
      "message": "Any coding questions, conflicting documentation, or items needing physician clarification"
    }}
  ],
  
  "overall_confidence": 0.00,
  "codes_requiring_review": ["list any codes below 0.80 confidence by code value"]
}}

If a section is NOT applicable for this encounter (e.g., no ICD-10-PCS for outpatient, 
no value codes if none documented), return an empty array [] for that section.
Do NOT fabricate codes for sections with no supporting documentation.
Return ONLY the JSON. No preamble. No explanation."""

    return [
        {"role": "user", "content": user_prompt}
    ]


def get_system_prompt() -> str:
    return SYSTEM_PROMPT

