import fitz  # PyMuPDF
import re
from typing import Dict, Optional
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
        return {"summary": "AI analysis unavailable", "recovery_status": "Unknown"}

    prompt = f"""
    Analyze the following medical report text and provide:
    1. A concise summary of key findings (2-3 sentences).
    2. A recovery status indicator (e.g., 'Positive signs', 'Stable', 'Concerning', or 'Requires discussion').
    3. Any critical tumor markers or values found.

    Report Text:
    {text[:4000]}

    Return the result in JSON format:
    {{
        "summary": "...",
        "recovery_status": "...",
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
        return {"summary": "Failed to analyze with AI", "recovery_status": "Unknown"}


def parse_report(file_bytes: bytes) -> Dict:
    """Parse a PDF medical report: extract text, structured fields, and AI summary."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    page_count = len(doc)
    
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    text = "\n".join(text_parts)
    
    extracted = extract_key_fields(text)
    ai_analysis = analyze_with_llm(text)
    
    # Merge AI analysis into extracted fields for display
    extracted.update(ai_analysis)
    
    return {
        "raw_text": text[:5000],  # first 5000 chars stored in DB
        "full_text": text,
        "extracted_fields": extracted,
        "page_count": page_count
    }
