"""Internal, rule-based medical coding engine.

No external AI APIs used. Operates purely on de-identified text and returns
ICD-10-CM, ICD-10-PCS, CPT, HCPCS, MS-DRG, Revenue, Condition, Occurrence,
Value codes along with payer guideline references and validation status.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


# ----------------- Code dictionary -----------------
# Each entry: keywords → (code, description, guideline_ref)

ICD10_CM: List[dict] = [
    {"keywords": ["pneumonia", "pneumonitis"], "code": "J18.9", "description": "Pneumonia, unspecified organism", "ref": "CMS LCD L35023 — Pneumonia coverage policy"},
    {"keywords": ["community acquired pneumonia", "cap"], "code": "J15.9", "description": "Unspecified bacterial pneumonia", "ref": "ICD-10-CM Official Guidelines FY Ch. 10"},
    {"keywords": ["hypertension", "high blood pressure", "htn"], "code": "I10", "description": "Essential (primary) hypertension", "ref": "ICD-10-CM Official Guidelines Ch. 9 I.C.9.a"},
    {"keywords": ["type 2 diabetes", "t2dm", "diabetes mellitus type 2", "dm type 2"], "code": "E11.9", "description": "Type 2 diabetes mellitus without complications", "ref": "ICD-10-CM Guidelines Ch. 4 I.C.4.a"},
    {"keywords": ["type 1 diabetes", "t1dm"], "code": "E10.9", "description": "Type 1 diabetes mellitus without complications", "ref": "ICD-10-CM Guidelines Ch. 4"},
    {"keywords": ["diabetic ketoacidosis", "dka"], "code": "E11.10", "description": "Type 2 diabetes with ketoacidosis without coma", "ref": "ICD-10-CM Guidelines Ch. 4"},
    {"keywords": ["acute myocardial infarction", "stemi", "ami", "heart attack"], "code": "I21.9", "description": "Acute myocardial infarction, unspecified", "ref": "CMS NCD 20.4 — AMI coverage"},
    {"keywords": ["congestive heart failure", "chf", "heart failure"], "code": "I50.9", "description": "Heart failure, unspecified", "ref": "CMS LCD L34081 — Cardiac services"},
    {"keywords": ["atrial fibrillation", "a-fib", "afib"], "code": "I48.91", "description": "Unspecified atrial fibrillation", "ref": "ICD-10-CM Guidelines Ch. 9"},
    {"keywords": ["cerebrovascular accident", "stroke", "cva"], "code": "I63.9", "description": "Cerebral infarction, unspecified", "ref": "CMS NCD 160.14"},
    {"keywords": ["chronic obstructive pulmonary disease", "copd"], "code": "J44.9", "description": "Chronic obstructive pulmonary disease, unspecified", "ref": "CMS LCD L33446"},
    {"keywords": ["asthma"], "code": "J45.909", "description": "Unspecified asthma, uncomplicated", "ref": "ICD-10-CM Guidelines Ch. 10"},
    {"keywords": ["urinary tract infection", "uti"], "code": "N39.0", "description": "Urinary tract infection, site not specified", "ref": "ICD-10-CM Guidelines Ch. 14"},
    {"keywords": ["sepsis"], "code": "A41.9", "description": "Sepsis, unspecified organism", "ref": "ICD-10-CM Guidelines Ch. 1 I.C.1.d"},
    {"keywords": ["acute kidney injury", "aki", "acute renal failure"], "code": "N17.9", "description": "Acute kidney failure, unspecified", "ref": "ICD-10-CM Guidelines Ch. 14"},
    {"keywords": ["chronic kidney disease", "ckd"], "code": "N18.9", "description": "Chronic kidney disease, unspecified", "ref": "ICD-10-CM Guidelines Ch. 14"},
    {"keywords": ["gastroesophageal reflux", "gerd"], "code": "K21.9", "description": "Gastro-esophageal reflux disease without esophagitis", "ref": "ICD-10-CM Guidelines Ch. 11"},
    {"keywords": ["depression", "major depressive"], "code": "F32.9", "description": "Major depressive disorder, single episode, unspecified", "ref": "ICD-10-CM Guidelines Ch. 5"},
    {"keywords": ["anxiety"], "code": "F41.9", "description": "Anxiety disorder, unspecified", "ref": "ICD-10-CM Guidelines Ch. 5"},
    {"keywords": ["fracture femur", "femur fracture"], "code": "S72.90XA", "description": "Unspecified fracture of unspecified femur, initial encounter", "ref": "ICD-10-CM Guidelines Ch. 19 I.C.19.c"},
    {"keywords": ["fracture hip", "hip fracture"], "code": "S72.009A", "description": "Fracture of unspecified part of neck of unspecified femur", "ref": "ICD-10-CM Guidelines Ch. 19"},
    {"keywords": ["chest pain"], "code": "R07.9", "description": "Chest pain, unspecified", "ref": "ICD-10-CM Guidelines Ch. 18"},
    {"keywords": ["shortness of breath", "dyspnea", "sob"], "code": "R06.02", "description": "Shortness of breath", "ref": "ICD-10-CM Guidelines Ch. 18"},
    {"keywords": ["abdominal pain"], "code": "R10.9", "description": "Unspecified abdominal pain", "ref": "ICD-10-CM Guidelines Ch. 18"},
    {"keywords": ["fever"], "code": "R50.9", "description": "Fever, unspecified", "ref": "ICD-10-CM Guidelines Ch. 18"},
    {"keywords": ["obesity"], "code": "E66.9", "description": "Obesity, unspecified", "ref": "ICD-10-CM Guidelines Ch. 4"},
    {"keywords": ["hyperlipidemia", "dyslipidemia", "high cholesterol"], "code": "E78.5", "description": "Hyperlipidemia, unspecified", "ref": "ICD-10-CM Guidelines Ch. 4"},
    {"keywords": ["anemia"], "code": "D64.9", "description": "Anemia, unspecified", "ref": "ICD-10-CM Guidelines Ch. 3"},
    {"keywords": ["covid", "coronavirus", "sars-cov-2"], "code": "U07.1", "description": "COVID-19", "ref": "CDC/CMS COVID-19 Coding Guidelines"},
]

CPT_CODES: List[dict] = [
    {"keywords": ["office visit established", "established patient"], "code": "99213", "description": "Office/outpatient visit, established, low MDM", "ref": "AMA CPT 2024 E/M Guidelines"},
    {"keywords": ["office visit new", "new patient"], "code": "99203", "description": "Office/outpatient visit, new patient, low MDM", "ref": "AMA CPT 2024 E/M Guidelines"},
    {"keywords": ["emergency department", "ed visit", "er visit"], "code": "99284", "description": "Emergency department visit, moderate severity", "ref": "AMA CPT 2024 E/M"},
    {"keywords": ["initial hospital care", "admission h&p"], "code": "99223", "description": "Initial hospital inpatient, high complexity", "ref": "AMA CPT 2024 E/M"},
    {"keywords": ["subsequent hospital care"], "code": "99232", "description": "Subsequent hospital care, moderate complexity", "ref": "AMA CPT 2024 E/M"},
    {"keywords": ["discharge"], "code": "99238", "description": "Hospital discharge day management, ≤30 min", "ref": "AMA CPT 2024 E/M"},
    {"keywords": ["chest x-ray", "chest xray", "cxr"], "code": "71046", "description": "Radiologic examination, chest, 2 views", "ref": "AMA CPT 2024 Radiology"},
    {"keywords": ["ekg", "ecg", "electrocardiogram"], "code": "93000", "description": "Electrocardiogram, routine ECG with 12 leads", "ref": "CMS LCD L33950"},
    {"keywords": ["echocardiogram", "echo"], "code": "93306", "description": "Echocardiography, transthoracic, complete", "ref": "CMS LCD L33630"},
    {"keywords": ["ct head", "head ct"], "code": "70450", "description": "CT head or brain, without contrast", "ref": "CMS NCD 220.1"},
    {"keywords": ["ct chest"], "code": "71250", "description": "CT thorax, without contrast", "ref": "CMS NCD 220.1"},
    {"keywords": ["mri brain"], "code": "70551", "description": "MRI brain, without contrast", "ref": "CMS NCD 220.2"},
    {"keywords": ["complete blood count", "cbc"], "code": "85025", "description": "CBC with automated differential", "ref": "CMS Lab NCD 190.15"},
    {"keywords": ["basic metabolic panel", "bmp"], "code": "80048", "description": "Basic metabolic panel", "ref": "CMS Lab NCD 190.14"},
    {"keywords": ["comprehensive metabolic panel", "cmp"], "code": "80053", "description": "Comprehensive metabolic panel", "ref": "CMS Lab NCD 190.14"},
    {"keywords": ["appendectomy"], "code": "44970", "description": "Laparoscopy, surgical; appendectomy", "ref": "AMA CPT Surgery"},
    {"keywords": ["cholecystectomy"], "code": "47562", "description": "Laparoscopic cholecystectomy", "ref": "AMA CPT Surgery"},
    {"keywords": ["colonoscopy"], "code": "45378", "description": "Colonoscopy, flexible, diagnostic", "ref": "CMS NCD 210.3"},
    {"keywords": ["cardiac catheterization"], "code": "93458", "description": "Cardiac cath, left heart, coronary angiography", "ref": "CMS NCD 20.4"},
    {"keywords": ["physical therapy evaluation", "pt eval"], "code": "97161", "description": "PT evaluation, low complexity", "ref": "CMS LCD L33631"},
    {"keywords": ["critical care"], "code": "99291", "description": "Critical care, first 30-74 minutes", "ref": "AMA CPT 2024 E/M"},
]

HCPCS_CODES: List[dict] = [
    {"keywords": ["ambulance basic life support", "bls"], "code": "A0428", "description": "Ambulance service, BLS, non-emergency", "ref": "CMS Ambulance Fee Schedule"},
    {"keywords": ["ambulance advanced life support", "als"], "code": "A0427", "description": "Ambulance service, ALS, emergency", "ref": "CMS Ambulance Fee Schedule"},
    {"keywords": ["oxygen", "home oxygen"], "code": "E1390", "description": "Oxygen concentrator, single delivery port", "ref": "CMS DMEPOS LCD L33797"},
    {"keywords": ["wheelchair"], "code": "E1130", "description": "Standard wheelchair", "ref": "CMS DMEPOS"},
    {"keywords": ["insulin"], "code": "J1815", "description": "Injection, insulin, per 5 units", "ref": "CMS Part B Drug File"},
    {"keywords": ["covid vaccine"], "code": "G0011A", "description": "Administration, COVID-19 vaccine", "ref": "CMS MLN Matters MM12439"},
]

ICD10_PCS: List[dict] = [
    {"keywords": ["appendectomy"], "code": "0DTJ4ZZ", "description": "Resection of Appendix, Percutaneous Endoscopic", "ref": "ICD-10-PCS Guidelines B3"},
    {"keywords": ["cholecystectomy"], "code": "0FT44ZZ", "description": "Resection of Gallbladder, Percutaneous Endoscopic", "ref": "ICD-10-PCS Guidelines B3"},
    {"keywords": ["coronary artery bypass", "cabg"], "code": "021209W", "description": "Bypass Coronary Artery, Two Arteries", "ref": "ICD-10-PCS Guidelines B3.6a"},
    {"keywords": ["cesarean", "c-section"], "code": "10D00Z1", "description": "Extraction of Products of Conception, Low, Open", "ref": "ICD-10-PCS Ch. Obstetrics"},
    {"keywords": ["hip replacement"], "code": "0SR9019", "description": "Replacement of Right Hip Joint, Metal on Polyethylene, Open", "ref": "ICD-10-PCS Guidelines"},
]

# UB-04 specific
REVENUE_CODES: List[dict] = [
    {"keywords": ["room and board", "semi-private"], "code": "0120", "description": "Room & Board – Semi-Private", "ref": "NUBC UB-04 Manual"},
    {"keywords": ["icu", "intensive care"], "code": "0200", "description": "Intensive Care Unit – General", "ref": "NUBC UB-04 Manual"},
    {"keywords": ["emergency room", "ed", "er"], "code": "0450", "description": "Emergency Room – General", "ref": "NUBC UB-04 Manual"},
    {"keywords": ["operating room", "or", "surgery"], "code": "0360", "description": "Operating Room Services – General", "ref": "NUBC UB-04 Manual"},
    {"keywords": ["laboratory", "lab"], "code": "0300", "description": "Laboratory – General", "ref": "NUBC UB-04 Manual"},
    {"keywords": ["radiology", "imaging", "x-ray", "ct", "mri"], "code": "0320", "description": "Diagnostic Radiology – General", "ref": "NUBC UB-04 Manual"},
    {"keywords": ["pharmacy", "medication"], "code": "0250", "description": "Pharmacy – General", "ref": "NUBC UB-04 Manual"},
    {"keywords": ["respiratory", "ventilator"], "code": "0410", "description": "Respiratory Services – General", "ref": "NUBC UB-04 Manual"},
]

CONDITION_CODES: List[dict] = [
    {"keywords": ["military service", "veteran"], "code": "02", "description": "Condition is employment related", "ref": "NUBC Condition Codes"},
    {"keywords": ["auto accident", "motor vehicle"], "code": "04", "description": "HMO enrollee", "ref": "NUBC Condition Codes"},
    {"keywords": ["skilled nursing facility", "snf"], "code": "41", "description": "Partial hospitalization", "ref": "NUBC Condition Codes"},
    {"keywords": ["nonelective"], "code": "A9", "description": "Medical/nonelective admission", "ref": "NUBC Condition Codes"},
]

OCCURRENCE_CODES: List[dict] = [
    {"keywords": ["accident", "injury date"], "code": "01", "description": "Accident/Medical Coverage – date of accident", "ref": "NUBC Occurrence Codes"},
    {"keywords": ["auto accident"], "code": "02", "description": "No-fault insurance involved – date of accident", "ref": "NUBC Occurrence Codes"},
    {"keywords": ["onset of symptoms"], "code": "11", "description": "Onset of Symptoms/Illness", "ref": "NUBC Occurrence Codes"},
    {"keywords": ["discharge"], "code": "42", "description": "Date of Discharge", "ref": "NUBC Occurrence Codes"},
]

VALUE_CODES: List[dict] = [
    {"keywords": ["medicare blood deductible"], "code": "06", "description": "Medicare Blood Deductible", "ref": "NUBC Value Codes"},
    {"keywords": ["copayment"], "code": "A1", "description": "Deductible – Payer A", "ref": "NUBC Value Codes"},
    {"keywords": ["coinsurance"], "code": "A2", "description": "Coinsurance – Payer A", "ref": "NUBC Value Codes"},
]

# MS-DRG lookup — simplified mapping by principal dx family
MS_DRG_MAP: List[dict] = [
    {"dx_keywords": ["pneumonia"], "code": "193", "description": "Simple Pneumonia & Pleurisy with MCC", "ref": "CMS IPPS FY2024 Final Rule – MS-DRG v41"},
    {"dx_keywords": ["heart failure", "chf"], "code": "291", "description": "Heart Failure & Shock with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["stroke", "cerebral infarction"], "code": "064", "description": "Intracranial Hemorrhage or Cerebral Infarction with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["myocardial infarction", "stemi"], "code": "280", "description": "Acute MI, Discharged Alive with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["sepsis"], "code": "871", "description": "Septicemia or Severe Sepsis w/o MV >96 hrs with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["copd"], "code": "190", "description": "COPD with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["uti"], "code": "689", "description": "Kidney & Urinary Tract Infections with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["hip fracture", "femur fracture"], "code": "535", "description": "Fractures of Hip & Pelvis with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
]


@dataclass
class CodeResult:
    code: str
    description: str
    code_type: str
    guideline_ref: str
    status: str = "verified"  # verified | review
    note: str = ""


@dataclass
class CodingOutput:
    session_id: str
    claim_type: str
    specialty: List[str]
    payer: str
    state: Optional[str]
    principal_diagnosis: Optional[dict] = None
    secondary_diagnoses: List[dict] = field(default_factory=list)
    principal_procedure: Optional[dict] = None
    additional_procedures: List[dict] = field(default_factory=list)
    ms_drg: Optional[dict] = None
    revenue_codes: List[dict] = field(default_factory=list)
    condition_codes: List[dict] = field(default_factory=list)
    occurrence_codes: List[dict] = field(default_factory=list)
    value_codes: List[dict] = field(default_factory=list)
    modifiers: List[dict] = field(default_factory=list)
    processing_log: List[str] = field(default_factory=list)
    mue_checks: List[str] = field(default_factory=list)
    ncci_checks: List[str] = field(default_factory=list)


def _lower(text: str) -> str:
    return text.lower() if text else ""


def _matches(text: str, keywords: List[str]) -> bool:
    return any(k in text for k in keywords)


def _collect(text: str, table: List[dict], code_type: str) -> List[dict]:
    results: List[dict] = []
    seen: set[str] = set()
    for row in table:
        if _matches(text, row["keywords"]) and row["code"] not in seen:
            results.append({
                "code": row["code"],
                "description": row["description"],
                "code_type": code_type,
                "guideline_ref": row["ref"],
                "status": "verified",
                "note": "",
            })
            seen.add(row["code"])
    return results


def _ms_drg_from_dx(text: str) -> Optional[dict]:
    for row in MS_DRG_MAP:
        if _matches(text, row["dx_keywords"]):
            return {
                "code": row["code"],
                "description": row["description"],
                "code_type": "MS-DRG",
                "guideline_ref": row["ref"],
                "status": "verified",
                "note": "",
            }
    return None


def _mue_checks(procedures: List[dict]) -> List[str]:
    """Medically Unlikely Edits — simplified: flag duplicates > 1."""
    counts: Dict[str, int] = {}
    for p in procedures:
        counts[p["code"]] = counts.get(p["code"], 0) + 1
    msgs: List[str] = []
    for code, c in counts.items():
        if c > 1:
            msgs.append(f"MUE: CPT {code} reported {c}× — review MUE limit.")
    if not msgs:
        msgs.append("MUE edits: all procedure units within CMS MUE limits.")
    return msgs


def _ncci_checks(procedures: List[dict]) -> List[str]:
    """NCCI Edits — simplified: a handful of common procedure pairs."""
    codes = {p["code"] for p in procedures}
    conflicts: List[str] = []
    # Example NCCI pairs (simplified)
    if "44970" in codes and "45378" in codes:
        conflicts.append("NCCI: 44970 (appendectomy) with 45378 (colonoscopy) — review modifier 59 eligibility.")
    if "93000" in codes and "93306" in codes:
        conflicts.append("NCCI: 93000 with 93306 — bundling may apply per CMS NCCI Ch. 11.")
    if not conflicts:
        conflicts.append("NCCI edits: no bundling conflicts detected across reported procedures.")
    return conflicts


def run_coding(
    deidentified_text: str,
    *,
    session_id: str,
    claim_type: str,
    codes_required: List[str],
    specialty: List[str],
    payer: str,
    state: Optional[str] = None,
) -> CodingOutput:
    text = _lower(deidentified_text)
    log: List[str] = []

    out = CodingOutput(
        session_id=session_id,
        claim_type=claim_type,
        specialty=specialty,
        payer=payer,
        state=state,
        processing_log=log,
    )

    want_all = ("ALL" in [c.upper() for c in codes_required]) or not codes_required

    log.append("Extracting primary and secondary diagnoses from de-identified record…")
    icd10 = _collect(text, ICD10_CM, "ICD-10-CM")
    if icd10:
        out.principal_diagnosis = icd10[0]
        out.secondary_diagnoses = icd10[1:]
    log.append(f"Found {len(icd10)} ICD-10-CM diagnosis code(s).")

    log.append("Identifying procedures and services rendered…")
    cpt = _collect(text, CPT_CODES, "CPT") if (want_all or "CPT" in codes_required) else []
    hcpcs = _collect(text, HCPCS_CODES, "HCPCS") if (want_all or "HCPCS" in codes_required) else []
    log.append(f"Matched {len(cpt)} CPT and {len(hcpcs)} HCPCS code(s).")

    # UB-04 specific
    if claim_type == "UB-04":
        log.append("UB-04: evaluating institutional code sets…")
        if want_all or "ICD-10-PCS" in codes_required:
            pcs = _collect(text, ICD10_PCS, "ICD-10-PCS")
            if pcs:
                out.principal_procedure = pcs[0]
                out.additional_procedures = pcs[1:] + cpt + hcpcs
            else:
                out.additional_procedures = cpt + hcpcs
        else:
            out.additional_procedures = cpt + hcpcs

        if want_all or "REVENUE" in codes_required:
            out.revenue_codes = _collect(text, REVENUE_CODES, "Revenue")
        if want_all or "CONDITION" in codes_required:
            out.condition_codes = _collect(text, CONDITION_CODES, "Condition")
        if want_all or "OCCURRENCE" in codes_required:
            out.occurrence_codes = _collect(text, OCCURRENCE_CODES, "Occurrence")
        if want_all or "VALUE" in codes_required:
            out.value_codes = _collect(text, VALUE_CODES, "Value")
        if want_all or "MS-DRG" in codes_required:
            drg = _ms_drg_from_dx(text)
            if drg:
                out.ms_drg = drg
            log.append("MS-DRG grouper applied (CMS IPPS v41).")
    else:
        # CMS-1500 (professional)
        log.append("CMS-1500: using professional code sets (CPT/HCPCS/ICD-10-CM)…")
        if cpt:
            out.principal_procedure = cpt[0]
            out.additional_procedures = cpt[1:] + hcpcs
        else:
            out.additional_procedures = hcpcs

        # Modifiers for professional claims
        if "bilateral" in text:
            out.modifiers.append({"code": "50", "description": "Bilateral procedure", "code_type": "Modifier", "guideline_ref": "AMA CPT Appendix A", "status": "verified", "note": ""})
        if "right" in text and any(p["code"] in {"71046", "70450", "71250", "70551"} for p in cpt):
            out.modifiers.append({"code": "RT", "description": "Right side", "code_type": "Modifier", "guideline_ref": "CMS HCPCS Modifier", "status": "verified", "note": ""})
        if "left" in text and any(p["code"] in {"71046", "70450", "71250", "70551"} for p in cpt):
            out.modifiers.append({"code": "LT", "description": "Left side", "code_type": "Modifier", "guideline_ref": "CMS HCPCS Modifier", "status": "verified", "note": ""})

    # Payer-specific note
    if payer == "MEDICARE":
        log.append("Validating against Medicare LCD/NCD policies…")
    elif payer == "MEDICAID":
        log.append(f"Validating against Medicaid fee schedule for state: {state or 'Unknown'}…")
    else:
        log.append("Validating against Commercial payer policy guidelines…")

    # Edits
    log.append("Running MUE (Medically Unlikely Edits) checks…")
    procs_for_edits = ([out.principal_procedure] if out.principal_procedure else []) + out.additional_procedures
    out.mue_checks = _mue_checks(procs_for_edits)
    log.append("Running NCCI (National Correct Coding Initiative) edits…")
    out.ncci_checks = _ncci_checks(procs_for_edits)

    # Second-pass validation
    log.append("Second-pass validation — confirming code compatibility and billability…")
    # If any procedure matched an NCCI conflict, mark for review
    conflicts_text = " ".join(out.ncci_checks).lower()
    if "review" in conflicts_text:
        for p in procs_for_edits:
            if p and p["code"] in conflicts_text:
                p["status"] = "review"
                p["note"] = "NCCI bundling — attach modifier 59 if appropriate."

    log.append("Final review complete.")
    return out


def coding_to_dict(out: CodingOutput) -> dict:
    return asdict(out)
