import fitz  # PyMuPDF
import pdfplumber
import re
from typing import Dict, Optional, List
from groq import Groq
from app.config import get_settings

import logging

logger = logging.getLogger("cancercare.parser")
settings = get_settings()
groq_client = None
if settings.groq_api_key:
    groq_client = Groq(api_key=settings.groq_api_key.strip())

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


def extract_key_fields(text: str) -> Dict:
    """Use regex patterns to extract structured data from report text."""
    text_lower = text.lower()
    results = {}
    for field, pattern in EXTRACTION_PATTERNS.items():
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            results[field] = match.group(1).strip()[:100]
    return results


def analyze_with_llm(text: str) -> Dict:
    """Use LLM to summarize key findings and determine recovery status."""
    logger.info(f"Analyzing report text with LLM (length: {len(text)})")
    if not groq_client:
        logger.warning("Groq client not initialized - skipping AI analysis")
        return {
            "summary": "AI analysis unavailable",
            "recovery_status": "Unknown",
            "overall_signal": "Unknown",
            "signal_evidence": ["AI analysis unavailable"],
            "table_highlights": []
        }

    prompt = f"""
    Analyze the following medical report text and provide:
    1. A concise summary of key findings (2-3 sentences).
    2. A recovery status indicator (e.g., 'Positive signs', 'Stable', 'Concerning', or 'Requires discussion').
    3. A clear overall signal label: one of ["Good signs", "Mixed", "Concerning", "Unknown"].
    4. Evidence from the report that supports the signal (3-6 short bullet items).
    5. Table highlights if present (2-5 items). Include key marker/value pairs.

    Report Text:
    {text[:4000]}

    Return the result in JSON format:
    {{
        "summary": "...",
        "recovery_status": "...",
        "overall_signal": "...",
        "signal_evidence": ["..."],
        "table_highlights": ["..."],
        "key_metrics": "..."
    }}
    """
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        import json
        result = json.loads(response.choices[0].message.content)
        logger.info(f"AI Analysis successful: {result.get('recovery_status')}")
        return result
    except Exception as e:
        logger.error(f"AI Analysis failed: {str(e)}")
        return {
            "summary": "Failed to analyze with AI",
            "recovery_status": "Unknown",
            "overall_signal": "Unknown",
            "signal_evidence": ["AI analysis failed"],
            "table_highlights": []
        }


def _clean_cell(value: Optional[str]) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _tables_to_text(tables: List[List[List[Optional[str]]]], max_rows: int = 8) -> str:
    lines = []
    for table in tables:
        if not table:
            continue
        header = [_clean_cell(cell) for cell in table[0]]
        header = [h for h in header if h]
        if header:
            lines.append("Table columns: " + " | ".join(header))
        for row in table[1:max_rows + 1]:
            cells = [_clean_cell(cell) for cell in row]
            if any(cells):
                lines.append("Row: " + " | ".join([c for c in cells if c]))
        lines.append("")
    return "\n".join(lines).strip()


def build_report_text(file_bytes: bytes, table_max_pages: int = 4) -> Dict:
    """Extract report text and a compact table excerpt from a PDF."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    page_count = len(doc)

    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    text = "\n".join(text_parts)

    table_text = ""
    if table_max_pages > 0:
        try:
            with pdfplumber.open(stream=file_bytes) as pdf:
                tables = []
                for page in pdf.pages[:table_max_pages]:
                    try:
                        tables.extend(page.extract_tables() or [])
                    except Exception:
                        continue
                table_text = _tables_to_text(tables)
        except Exception:
            table_text = ""

    combined_text = text
    if table_text:
        combined_text = f"{text}\n\nTABLES:\n{table_text}"

    return {
        "combined_text": combined_text,
        "page_count": page_count,
        "table_text": table_text,
    }


def parse_report(file_bytes: bytes, include_ai: bool = True, include_tables: bool = True) -> Dict:
    """Parse a PDF medical report: extract text, structured fields, and AI summary."""
    report_text = build_report_text(file_bytes, table_max_pages=4 if include_tables else 0)
    combined_text = report_text["combined_text"]
    page_count = report_text["page_count"]
    table_text = report_text["table_text"]

    extracted = extract_key_fields(combined_text)
    if include_ai:
        ai_analysis = analyze_with_llm(combined_text)
        extracted.update(ai_analysis)
    if table_text:
        extracted["table_excerpt"] = table_text[:1500]

    return {
        "raw_text": combined_text[:5000],  # first 5000 chars stored in DB
        "full_text": combined_text,
        "extracted_fields": extracted,
        "page_count": page_count
    }
