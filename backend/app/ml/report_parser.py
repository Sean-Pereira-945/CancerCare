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


def _build_fallback_summary(extracted: Dict) -> str:
    parts = []
    cancer_type = extracted.get("cancer_type")
    stage = extracted.get("stage")
    tumor_markers = extracted.get("tumor_markers")
    treatment = extracted.get("treatment")
    medications = extracted.get("medications")
    hemoglobin = extracted.get("hemoglobin")
    wbc = extracted.get("wbc")

    if cancer_type:
        parts.append(f"Diagnosis: {cancer_type.title()}.")
    if stage:
        parts.append(f"Stage {str(stage).upper()}.")
    if tumor_markers:
        parts.append(f"Tumor marker: {tumor_markers}.")
    if treatment:
        parts.append(f"Planned treatment: {treatment}.")
    if medications:
        parts.append(f"Medications: {medications}.")
    if hemoglobin or wbc:
        labs = []
        if hemoglobin:
            labs.append(f"Hgb {hemoglobin}")
        if wbc:
            labs.append(f"WBC {wbc}")
        parts.append(f"Labs: {', '.join(labs)}.")

    return " ".join(parts) if parts else "Clinical report uploaded. Key findings pending review."


def _ensure_indicators(extracted: Dict) -> None:
    recovery_status = extracted.get("recovery_status")
    overall_signal = extracted.get("overall_signal")
    placeholder_values = {"Unknown", "Processing", "AI analysis unavailable", "Failed to analyze with AI", ""}

    if not recovery_status or recovery_status in placeholder_values:
        extracted["recovery_status"] = "Pending review"
    if not overall_signal or overall_signal in placeholder_values:
        extracted["overall_signal"] = "Needs review"


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
    1. A concise, readable summary of key findings (1-2 full sentences, no fragments).
    2. A recovery status indicator (e.g., 'Positive signs', 'Stable', 'Concerning', or 'Requires discussion').
    3. A clear overall signal label: one of ["Good signs", "Mixed", "Concerning", "Unknown"].
    4. A strict classification label based on the report text: one of ["positive", "negative"].
    5. Evidence from the report that supports the signal (3-6 short bullet items).
    6. Table highlights if present (2-5 items). Include key marker/value pairs.

    Rules for the summary:
    - Use plain language and complete sentences.
    - Keep it under 60 words.
    - Avoid abbreviations unless explicitly in the report.
    - Only include facts stated in the report text; do not invent details.
    - Mention at least one concrete clinical detail (diagnosis, stage, marker, tumor size, treatment, or procedure).
    - End with a sentence that states whether the overall signal is positive or concerning and why (1 short clause).

    Report Text:
    {text[:4000]}

    Return the result in JSON format:
    {{
        "summary": "...",
        "recovery_status": "...",
        "overall_signal": "...",
        "signal_classification": "positive | negative",
        "signal_evidence": ["..."],
        "table_highlights": ["..."],
        "key_metrics": "..."
    }}
    """
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a clinical summarization assistant. Follow the rules exactly and return JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        import json
        result = json.loads(response.choices[0].message.content)
        if isinstance(result, dict):
            summary = result.get("summary")
            if summary:
                normalized = _normalize_summary(summary)
                if not _summary_has_report_overlap(normalized, text):
                    raise ValueError("AI summary failed overlap check")
                refined = _rephrase_summary_with_groq(normalized, text)
                if refined and _summary_has_report_overlap(refined, text):
                    result["summary"] = _normalize_summary(refined)
                else:
                    result["summary"] = normalized
            if result.get("summary"):
                result["summary"] = _ensure_summary_signal(
                    result["summary"],
                    result.get("recovery_status"),
                    result.get("overall_signal")
                )
            result["signal_classification"] = _normalize_signal_classification(
                result.get("signal_classification")
            )
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


def _normalize_summary(summary: str) -> str:
    cleaned = re.sub(r"\s+", " ", summary).strip()
    cleaned = cleaned.replace("..", ".").replace(" ,", ",")
    if cleaned and not cleaned.endswith("."):
        cleaned = f"{cleaned}."
    return cleaned[:420]


def _ensure_summary_signal(summary: str, recovery_status: str | None, overall_signal: str | None) -> str:
    summary_lower = summary.lower()
    signal_terms = ["positive", "concerning", "stable", "mixed", "favorable", "unfavorable"]
    if any(term in summary_lower for term in signal_terms):
        return summary

    signal = (recovery_status or overall_signal or "Unknown").strip()
    if signal.lower() in {"unknown", "processing", "pending review", "needs review"}:
        return summary

    suffix = f" Overall, this suggests {signal.lower()}."
    return _normalize_summary(f"{summary} {suffix}")


def _normalize_signal_classification(value: str | None) -> str:
    if not value:
        return "negative"
    normalized = value.strip().lower()
    if normalized in {"positive", "negative"}:
        return normalized
    if "positive" in normalized or "good" in normalized:
        return "positive"
    if "negative" in normalized or "concern" in normalized:
        return "negative"
    return "negative"


def _summary_has_report_overlap(summary: str, text: str) -> bool:
    summary_lower = summary.lower()
    tokens = re.findall(r"[a-zA-Z]{4,}", text.lower())
    if not tokens:
        return False
    stopwords = {
        "with", "from", "that", "this", "were", "have", "patient", "patients", "report",
        "which", "will", "been", "into", "your", "also", "more", "than", "they", "them",
        "clinical", "medical", "summary", "findings", "results", "treatment", "therapy"
    }
    freq = {}
    for token in tokens:
        if token in stopwords:
            continue
        freq[token] = freq.get(token, 0) + 1
    if not freq:
        return False
    top_terms = sorted(freq, key=freq.get, reverse=True)[:6]
    return any(term in summary_lower for term in top_terms)


def _rephrase_summary_with_groq(summary: str, report_text: str) -> str:
    if not groq_client:
        return summary

    prompt = f"""
    Rewrite the summary below to sound natural and polished, without changing meaning.
    Rules:
    - Keep it 1-2 sentences under 60 words.
    - Fix spelling/grammar.
    - Do not add new facts.
    - Keep clinical details mentioned in the report text.

    Report Text (for grounding):
    {report_text[:2000]}

    Original Summary:
    {summary}

    Return only the revised summary text.
    """

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You rewrite clinical summaries. Return only the revised summary text."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        revised = response.choices[0].message.content.strip()
        return revised
    except Exception:
        return summary


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
