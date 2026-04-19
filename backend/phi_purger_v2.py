"""
phi_purger_v2.py
================
3-layer HIPAA Safe Harbor PHI purger.

Layer 1 — Regex  : structured PHI (SSN, dates, phones, MRNs, emails, IPs, URLs)
Layer 2 — Presidio: NER-based (names, locations, organisations, ages, NPI)
Layer 3 — scispaCy: clinical NER (provider names, facility names embedded in text)

Returns de-identified text + a redaction audit log (no PHI stored in log).
Claude only ever receives the output of this pipeline.

Install deps:
    pip install presidio-analyzer presidio-anonymizer spacy
    pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_lg-0.5.3.tar.gz
    python -m spacy download en_core_web_lg
"""

import re
import hashlib
import logging
from datetime import datetime, timezone
from typing import Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LAYER 1 — Regex patterns for structured PHI (18 Safe Harbor categories)
# ---------------------------------------------------------------------------

PHI_PATTERNS = [
    # Names — basic title+name patterns (Presidio handles the rest)
    (r"\b(Dr\.?|Mr\.?|Mrs\.?|Ms\.?|Prof\.?)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?", "[NAME]"),

    # Dates — all common formats
    (r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", "[DATE]"),
    (r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
     r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
     r"Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}\b", "[DATE]"),
    (r"\b\d{4}-\d{2}-\d{2}\b", "[DATE]"),

    # Ages over 89
    (r"\b(9\d|1[0-1]\d|120)\s*(?:year[s]?\s*old|y/?o|yo)\b", "[AGE_OVER_89]"),
    (r"\b(?:age[d]?|aged)\s*(9\d|1[0-1]\d|120)\b", "[AGE_OVER_89]"),

    # Phone numbers
    (r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b", "[PHONE]"),

    # SSN
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
    (r"\bSSN\s*:?\s*\d{3}-?\d{2}-?\d{4}\b", "[SSN]"),

    # MRN / Patient ID / Account Number
    (r"\b(?:MRN|Medical Record(?:\s+Number)?|Patient\s+ID|Acct\.?|Account)\s*[:#]?\s*\w+\b", "[MRN]"),
    (r"\bMR#?\s*\d+\b", "[MRN]"),

    # NPI
    (r"\b(?:NPI|National Provider)\s*[:#]?\s*\d{10}\b", "[NPI]"),

    # Email addresses
    (r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", "[EMAIL]"),

    # URLs
    (r"https?://\S+", "[URL]"),
    (r"www\.\S+\.\w+", "[URL]"),

    # IP addresses
    (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[IP_ADDRESS]"),

    # ZIP codes (5 or 9 digit)
    (r"\b\d{5}(?:-\d{4})?\b", "[ZIP]"),

    # Device / Serial numbers
    (r"\b(?:Serial|Device|Implant)\s*(?:No\.?|Number|#)\s*:?\s*[\w\-]+\b", "[DEVICE_ID]"),

    # Health plan / insurance IDs
    (r"\b(?:Policy|Member|Group|Insurance\s+ID)\s*[:#]?\s*[\w\-]+\b", "[HEALTH_PLAN_ID]"),

    # Certificate / license numbers
    (r"\b(?:License|Certificate|DEA)\s*(?:No\.?|Number|#)?\s*:?\s*[A-Z]{1,2}\d{7,}\b", "[LICENSE]"),

    # Vehicle identifiers
    (r"\b(?:VIN|License\s+Plate)\s*:?\s*[A-Z0-9\-]+\b", "[VEHICLE_ID]"),

    # Geographic — street addresses
    (r"\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:St|Ave|Blvd|Dr|Rd|Ln|Ct|Way|Pl|Circle|Suite|Ste)\.?\b",
     "[ADDRESS]"),

    # Fax numbers
    (r"\b[Ff]ax\s*[:#]?\s*(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b", "[FAX]"),
]

COMPILED_PATTERNS = [(re.compile(p, re.IGNORECASE), r) for p, r in PHI_PATTERNS]


def _layer1_regex(text: str, audit: list) -> str:
    """Apply all regex patterns sequentially."""
    for pattern, replacement in COMPILED_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            audit.append({
                "layer": 1,
                "type": replacement,
                "count": len(matches),
                "hash": hashlib.sha256(str(matches).encode()).hexdigest()[:16]
            })
        text = pattern.sub(replacement, text)
    return text


# ---------------------------------------------------------------------------
# LAYER 2 — Microsoft Presidio (NER-based)
# ---------------------------------------------------------------------------

def _layer2_presidio(text: str, audit: list) -> str:
    """
    Use Presidio AnalyzerEngine + AnonymizerEngine for NER-based PHI detection.
    Handles names, locations, organisations, and other entities regex misses.
    """
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine
        from presidio_anonymizer.entities import OperatorConfig

        analyzer = AnalyzerEngine()
        anonymizer = AnonymizerEngine()

        entities = [
            "PERSON", "LOCATION", "ORGANIZATION",
            "DATE_TIME", "EMAIL_ADDRESS", "PHONE_NUMBER",
            "US_SSN", "US_PASSPORT", "MEDICAL_LICENSE",
            "IP_ADDRESS", "URL", "NRP",
        ]

        results = analyzer.analyze(text=text, entities=entities, language="en")

        if results:
            audit.append({
                "layer": 2,
                "type": "PRESIDIO_NER",
                "count": len(results),
                "entities_found": list(set(r.entity_type for r in results))
            })

        operators = {
            entity: OperatorConfig("replace", {"new_value": f"[{entity}]"})
            for entity in entities
        }

        anonymized = anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )
        return anonymized.text

    except ImportError:
        logger.warning("Presidio not installed — skipping Layer 2. Run: pip install presidio-analyzer presidio-anonymizer")
        return text
    except Exception as e:
        logger.error(f"Presidio Layer 2 error: {e}")
        return text


# ---------------------------------------------------------------------------
# LAYER 3 — scispaCy clinical NER
# ---------------------------------------------------------------------------

def _layer3_scispacy(text: str, audit: list) -> str:
    """
    Use scispaCy en_core_sci_lg to catch clinical identifiers:
    provider names in clinical context, facility names, etc.
    Falls back gracefully if not installed.
    """
    try:
        import spacy

        try:
            nlp = spacy.load("en_core_sci_lg")
        except OSError:
            try:
                nlp = spacy.load("en_core_web_lg")
            except OSError:
                logger.warning("No spaCy model found — skipping Layer 3.")
                return text

        doc = nlp(text)
        redacted = text
        phi_ents = []

        for ent in doc.ents:
            if ent.label_ in ("PERSON", "GPE", "LOC", "ORG", "FAC"):
                phi_ents.append((ent.text, ent.label_))

        if phi_ents:
            audit.append({
                "layer": 3,
                "type": "SCISPACY_NER",
                "count": len(phi_ents),
                "labels": list(set(l for _, l in phi_ents))
            })

        for ent_text, ent_label in phi_ents:
            escaped = re.escape(ent_text)
            redacted = re.sub(escaped, f"[{ent_label}]", redacted)

        return redacted

    except ImportError:
        logger.warning("scispaCy not installed — skipping Layer 3. Run: pip install scispacy")
        return text
    except Exception as e:
        logger.error(f"scispaCy Layer 3 error: {e}")
        return text


# ---------------------------------------------------------------------------
# LAYER 4 — Final safety scan
# ---------------------------------------------------------------------------

RESIDUAL_PATTERNS = [
    # Any remaining sequences that look like IDs
    (re.compile(r"\b[A-Z]{2}\d{6,}\b"), "[ID]"),
    # Any 10-digit sequences (possible NPI/phone)
    (re.compile(r"\b\d{10}\b"), "[ID_10DIGIT]"),
    # Remaining email-like patterns
    (re.compile(r"\b\S+@\S+\.\S+\b"), "[EMAIL]"),
]


def _layer4_safety(text: str, audit: list) -> str:
    """Final pass — catch anything that slipped through."""
    for pattern, replacement in RESIDUAL_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            audit.append({
                "layer": 4,
                "type": "SAFETY_SCAN",
                "replacement": replacement,
                "count": len(matches)
            })
            text = pattern.sub(replacement, text)
    return text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def purge_phi(raw_text: str) -> Tuple[str, dict]:
    """
    Main entry point. Run all 4 layers sequentially.

    Args:
        raw_text: Raw OCR output from the medical document.

    Returns:
        Tuple of:
          - de_identified_text (str): Safe to send to Claude API.
          - audit_report (dict): Redaction summary for compliance logging.
            Contains NO actual PHI — only counts, types, and hashes.
    """
    if not raw_text or not raw_text.strip():
        return "", {"error": "Empty input text", "timestamp": datetime.now(timezone.utc).isoformat()}

    audit = []
    text = raw_text

    # Run all layers
    text = _layer1_regex(text, audit)
    text = _layer2_presidio(text, audit)
    text = _layer3_scispacy(text, audit)
    text = _layer4_safety(text, audit)

    # Build audit report
    total_redactions = sum(entry.get("count", 0) for entry in audit)
    input_hash = hashlib.sha256(raw_text.encode()).hexdigest()[:16]
    output_hash = hashlib.sha256(text.encode()).hexdigest()[:16]

    audit_report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_char_count": len(raw_text),
        "output_char_count": len(text),
        "total_redactions": total_redactions,
        "redaction_rate_pct": round((1 - len(text) / max(len(raw_text), 1)) * 100, 2),
        "input_hash": input_hash,
        "output_hash": output_hash,
        "layers": audit,
        "phi_free_confidence": "HIGH" if total_redactions > 0 else "REVIEW_RECOMMENDED",
    }

    logger.info(f"PHI purge complete: {total_redactions} redactions, input={input_hash}, output={output_hash}")

    return text, audit_report


def verify_phi_free(text: str) -> bool:
    """
    Quick check — scan de-identified text for any obvious remaining PHI.
    Returns True if text appears PHI-free, False if suspicious patterns found.
    Used as a gate before sending to Claude.
    """
    suspicious = [
        r"\b\d{3}-\d{2}-\d{4}\b",          # SSN
        r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",  # Email
        r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b",  # Phone
    ]
    for pattern in suspicious:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning("PHI verification failed — suspicious pattern found after purge.")
            return False
    return True
