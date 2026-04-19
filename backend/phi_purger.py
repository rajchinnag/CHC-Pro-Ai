"""Rule-based PHI purger. Runs entirely in-process (no external AI).

Redacts HIPAA Safe-Harbor identifiers from free-text medical records so
downstream coding logic only ever sees de-identified text.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Dict, List

# Common clinical terms that look like capitalized words but must not be
# treated as patient names.
CLINICAL_WHITELIST = {
    "Patient", "Diagnosis", "Procedure", "History", "Physical", "Exam",
    "Chief", "Complaint", "Impression", "Plan", "Assessment", "Review",
    "Systems", "Vitals", "Medication", "Medications", "Allergies",
    "Hospital", "Clinic", "Department", "Emergency", "Room", "Discharge",
    "Admission", "Admit", "Date", "Time", "DOB", "Age", "Sex", "Gender",
    "Male", "Female", "Dr", "MD", "DO", "RN", "PA", "NP", "FACP", "FACS",
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
    "Sunday", "CT", "MRI", "EKG", "ECG", "CBC", "BMP", "CMP", "X-Ray",
    "Chest", "Abdomen", "Pelvis", "Head", "Neck", "Spine", "Left", "Right",
    "Bilateral", "Anterior", "Posterior", "Superior", "Inferior",
    "Normal", "Abnormal", "Positive", "Negative", "Signed", "Attending",
    "Resident", "Intern", "Nurse", "Physician", "Provider", "Facility",
    "Medicare", "Medicaid", "Insurance", "Payer", "Policy", "Group",
    "Blue", "Cross", "Shield", "United", "Aetna", "Cigna", "Humana",
    "Street", "Avenue", "Road", "Drive", "Lane", "Boulevard", "Suite",
    "Apartment", "Floor", "Unit", "Building", "Center", "Centre",
    "United", "States", "America", "USA",
}


@dataclass
class PHIReport:
    redactions: Dict[str, int] = field(default_factory=dict)
    categories_found: List[str] = field(default_factory=list)

    def bump(self, category: str, n: int = 1) -> None:
        if n <= 0:
            return
        self.redactions[category] = self.redactions.get(category, 0) + n
        if category not in self.categories_found:
            self.categories_found.append(category)


PATTERNS: List[tuple[str, re.Pattern, str]] = [
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED-SSN]"),
    ("SSN", re.compile(r"\bSSN[:#\s]*\d{9}\b", re.IGNORECASE), "[REDACTED-SSN]"),
    ("Phone", re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[REDACTED-PHONE]"),
    ("Fax", re.compile(r"\bfax[:\s]*\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", re.IGNORECASE), "[REDACTED-FAX]"),
    ("Email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED-EMAIL]"),
    ("URL", re.compile(r"\bhttps?://[^\s<>]+"), "[REDACTED-URL]"),
    ("IP", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[REDACTED-IP]"),
    ("MRN", re.compile(r"\b(?:MRN|Medical Record (?:No|Number)|Chart (?:No|#))[:#\s]*[A-Z0-9-]{4,}\b", re.IGNORECASE), "[REDACTED-MRN]"),
    ("AccountNumber", re.compile(r"\b(?:Acct|Account)[:#\s]*[A-Z0-9-]{4,}\b", re.IGNORECASE), "[REDACTED-ACCT]"),
    ("InsuranceID", re.compile(r"\b(?:Policy|Member|Subscriber|Insurance)[:\s#]*(?:ID|No|Number)?[:#\s]*[A-Z0-9-]{5,}\b", re.IGNORECASE), "[REDACTED-INSURANCE-ID]"),
    ("LicenseNumber", re.compile(r"\b(?:License|Certificate)[:#\s]*[A-Z0-9-]{4,}\b", re.IGNORECASE), "[REDACTED-LICENSE]"),
    ("Vehicle", re.compile(r"\b(?:VIN|Plate|License Plate)[:#\s]*[A-Z0-9-]{4,}\b", re.IGNORECASE), "[REDACTED-VEHICLE]"),
    ("Device", re.compile(r"\b(?:Serial|SN|Device ID)[:#\s]*[A-Z0-9-]{4,}\b", re.IGNORECASE), "[REDACTED-DEVICE]"),
    # Full dates → keep year only
    ("Date", re.compile(r"\b(0?[1-9]|1[0-2])[/\-](0?[1-9]|[12]\d|3[01])[/\-](\d{2,4})\b"), r"[REDACTED-DATE, YEAR-\3]"),
    ("Date", re.compile(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(\d{4})\b", re.IGNORECASE), r"[REDACTED-DATE, YEAR-\2]"),
    ("Date", re.compile(r"\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b", re.IGNORECASE), r"[REDACTED-DATE, YEAR-\2]"),
    # ZIP codes
    ("ZIP", re.compile(r"\b\d{5}(?:-\d{4})?\b"), "[REDACTED-ZIP]"),
    # Address lines
    ("Address", re.compile(r"\b\d{1,6}\s+[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*\s+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Court|Ct|Way|Place|Pl)\b\.?", re.IGNORECASE), "[REDACTED-ADDRESS]"),
]


def _redact_names(text: str, report: PHIReport) -> str:
    """Redact lines of the form 'Patient: John Smith' and DOB lines."""
    def _sub_patient(m: re.Match) -> str:
        report.bump("Name", 1)
        return f"{m.group(1)}: [REDACTED-NAME]"

    text = re.sub(
        r"\b(Patient(?:\s+Name)?|Name|Pt|Subject)\s*[:\-]\s*([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){0,3})",
        _sub_patient,
        text,
    )
    # DOB lines → redact (age >89 flagged)
    def _sub_dob(m: re.Match) -> str:
        report.bump("DOB", 1)
        return "DOB: [REDACTED-DOB]"
    text = re.sub(r"\b(DOB|Date of Birth)\s*[:\-]\s*[^\n]+", _sub_dob, text, flags=re.IGNORECASE)

    def _sub_age(m: re.Match) -> str:
        age = int(m.group(1))
        if age > 89:
            report.bump("Age>89", 1)
            return "Age: [REDACTED-AGE>89]"
        return m.group(0)
    text = re.sub(r"\bAge\s*[:\-]?\s*(\d{1,3})\b", _sub_age, text, flags=re.IGNORECASE)

    # Doctor signature names
    def _sub_dr(m: re.Match) -> str:
        report.bump("ProviderName", 1)
        return "Dr. [REDACTED-NAME]"
    text = re.sub(r"\b(?:Dr\.|Doctor)\s+([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)?)", _sub_dr, text)
    return text


def purge_phi(text: str) -> tuple[str, PHIReport]:
    """Return (de-identified text, report).

    The returned text is safe to pass to the internal coding engine.
    """
    report = PHIReport()
    if not text:
        return "", report

    cleaned = _redact_names(text, report)

    for cat, pattern, replacement in PATTERNS:
        def _sub(m: re.Match, _cat=cat, _rep=replacement) -> str:
            report.bump(_cat, 1)
            if callable(_rep):
                return _rep(m)
            # Support backrefs for date patterns
            try:
                return m.expand(_rep)
            except re.error:
                return _rep
        cleaned = pattern.sub(_sub, cleaned)

    return cleaned, report
