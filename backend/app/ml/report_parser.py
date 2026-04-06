import fitz  # PyMuPDF
import re
from typing import Dict

# Key cancer report fields to extract via regex
EXTRACTION_PATTERNS = {
    "cancer_type": r"(?:diagnosis|cancer type|malignancy)[:\s]+([A-Za-z\s]+)",
    "stage": r"(?:stage|staging)[:\s]+(I{1,3}V?|[1-4][a-c]?)",
    "tumor_markers": r"(?:CA-\d+|PSA|CEA|AFP|HER2)[:\s]+([\d.]+)",
    "hemoglobin": r"(?:hemoglobin|hgb|hb)[:\s]+([\d.]+)",
    "wbc": r"(?:white blood cell|wbc)[:\s]+([\d.]+)",
    "treatment": r"(?:treatment|chemotherapy|radiation|surgery)[:\s]+([A-Za-z\s,]+)",
    "medications": r"(?:medication|drug|prescribed)[:\s]+([A-Za-z\s,]+)",
}


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF file using PyMuPDF."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    return "\n".join(text_parts)


def extract_key_fields(text: str) -> Dict:
    """Use regex patterns to extract structured data from report text."""
    text_lower = text.lower()
    results = {}
    for field, pattern in EXTRACTION_PATTERNS.items():
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            results[field] = match.group(1).strip()[:100]
    return results


def parse_report(file_bytes: bytes) -> Dict:
    """Parse a PDF medical report: extract text and structured fields."""
    text = extract_text_from_pdf(file_bytes)
    extracted = extract_key_fields(text)
    return {
        "raw_text": text[:5000],  # first 5000 chars stored in DB
        "full_text": text,
        "extracted_fields": extracted,
        "page_count": len(fitz.open(stream=file_bytes, filetype="pdf"))
    }
