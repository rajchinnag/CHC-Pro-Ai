"""Internal OCR + document text extraction. No external OCR APIs."""
from __future__ import annotations
import io
from typing import List, Tuple

import pytesseract
from PIL import Image

try:
    import pdfplumber
except Exception:  # pragma: no cover
    pdfplumber = None

try:
    import docx  # python-docx
except Exception:  # pragma: no cover
    docx = None


def extract_from_image(data: bytes) -> str:
    img = Image.open(io.BytesIO(data))
    return pytesseract.image_to_string(img)


def extract_from_pdf(data: bytes) -> str:
    if not pdfplumber:
        return ""
    out: List[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            if not txt.strip():
                # Fall back to OCR on page image
                try:
                    pil = page.to_image(resolution=200).original
                    txt = pytesseract.image_to_string(pil)
                except Exception:
                    txt = ""
            out.append(txt)
    return "\n".join(out)


def extract_from_docx(data: bytes) -> str:
    if not docx:
        return ""
    d = docx.Document(io.BytesIO(data))
    return "\n".join(p.text for p in d.paragraphs)


def extract_text(filename: str, data: bytes) -> Tuple[str, int]:
    """Return (text, page_count_estimate)."""
    name = (filename or "").lower()
    if name.endswith((".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp")):
        return extract_from_image(data), 1
    if name.endswith(".pdf"):
        text = extract_from_pdf(data)
        # rough page count
        try:
            if pdfplumber:
                with pdfplumber.open(io.BytesIO(data)) as pdf:
                    return text, len(pdf.pages)
        except Exception:
            pass
        return text, max(1, text.count("\f") + 1)
    if name.endswith(".docx"):
        return extract_from_docx(data), 1
    if name.endswith(".txt"):
        try:
            return data.decode("utf-8", errors="ignore"), 1
        except Exception:
            return "", 1
    # Fallback: assume image
    try:
        return extract_from_image(data), 1
    except Exception:
        return "", 0
