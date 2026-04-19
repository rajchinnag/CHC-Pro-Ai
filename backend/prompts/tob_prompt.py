"""
prompts/tob_prompt.py
======================
Dedicated Type of Bill (TOB) determination prompt.

TOB is a 4-character code on UB-04 Form Locator 4.
Structure: 0 + Facility Type + Care Type + Claim Frequency

Common TOB codes:
  0111 = Hospital Inpatient (admit through discharge)
  0114 = Hospital Inpatient (Interim - last claim)
  0121 = Hospital Inpatient Part B
  0131 = Hospital Outpatient
  0141 = Hospital - Other
  0711 = Clinic - Rural Health
  0721 = Clinic - Hospital Based or Independent Renal Dialysis
  0731 = Clinic - Freestanding
  0851 = Critical Access Hospital (CAH)

Used as a secondary verification pass when the main coding prompt
TOB confidence is below 0.90.
"""


def build_tob_prompt(
    deidentified_text: str,
    facility_type: str,
    patient_status: str,
    payer: str,
) -> list:
    """
    Build a focused TOB determination prompt.

    Returns messages list for Claude API.
    """

    user_prompt = f"""Determine the correct Type of Bill (TOB) code for a UB-04 claim.

FACILITY TYPE  : {facility_type}
PATIENT STATUS : {patient_status}
PAYER          : {payer}

CLINICAL CONTEXT (de-identified):
----------------------------------
{deidentified_text[:2000]}
----------------------------------

The Type of Bill is a 4-character code: 0 + [Facility Digit] + [Care Type Digit] + [Frequency Digit]

Facility Type digits:
  1 = Hospital
  2 = Skilled Nursing Facility
  3 = Home Health
  4 = Religious Non-Medical Health Care
  5 = (reserved)
  6 = Intermediate Care
  7 = Clinic / Hospital-Based Renal Dialysis
  8 = Special Facility

Care Type digits:
  1 = Inpatient (Part A)
  2 = Inpatient (Part B)
  3 = Outpatient
  4 = Other (Part B)
  5 = Intermediate Care Level I
  6 = Intermediate Care Level II
  7 = Subacute Inpatient
  8 = Swing Beds

Frequency (Sequence) digits:
  1 = Admit through Discharge (non-interim)
  2 = First Interim
  3 = Continuing Interim
  4 = Last Interim
  7 = Replacement of Prior Claim
  8 = Void/Cancel Prior Claim

Return ONLY this JSON with no other text:
{{
  "type_of_bill": {{
    "code": "4-character code starting with 0",
    "description": "plain English description",
    "facility_type_digit": "digit and meaning",
    "care_type_digit": "digit and meaning", 
    "frequency_digit": "digit and meaning",
    "reasoning": "1-2 sentence explanation",
    "confidence": 0.00
  }}
}}"""

    return [{"role": "user", "content": user_prompt}]
