from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from groq import Groq
from app.config import get_settings
from app.auth.router import get_current_user
from app.database import get_db
from app.ml.rag_pipeline import load_vectorstore, get_embeddings, VECTOR_STORE_PATH
from app.models.db import Report
from langchain_community.vectorstores import FAISS
from sqlalchemy.orm import Session
from sqlalchemy import desc
import uuid

router = APIRouter()
settings = get_settings()

# Initialize Groq client for fast LLM inference
groq_client = None
if settings.groq_api_key:
    groq_client = Groq(api_key=settings.groq_api_key.strip())

SYSTEM_PROMPT = """You are CancerCare AI, a compassionate and knowledgeable health assistant
specifically designed for cancer patients. You answer questions based on the provided medical
context. Always:
1. Be empathetic and supportive in tone
2. Cite information from the context when available
3. Remind users that you are not a substitute for professional medical advice
4. If the context does not contain enough information, say so clearly
Do NOT make up medical information."""

LOW_CONFIDENCE_THRESHOLD = 0.20
MEDIUM_CONFIDENCE_THRESHOLD = 0.35


def _fallback_reply(message: str, context: str) -> str:
    """Return a safe local fallback response when external LLM is unavailable."""
    if context and context != "No specific context available.":
        snippet = context[:500].strip()
        return (
            "I can still help, but advanced AI generation is currently unavailable. "
            "Based on your available medical context, here is a relevant excerpt:\n\n"
            f"{snippet}\n\n"
            "Please confirm any treatment decisions with your oncologist."
        )

    return (
        "I can still help with general guidance, but advanced AI generation is currently unavailable. "
        "For your question, please share more details (symptoms, treatment stage, or report findings), "
        "and I will provide a structured support-oriented response. "
        "Always consult your oncologist for medical decisions."
    )


def _score_to_confidence(score: float) -> float:
    """Convert FAISS distance-like score into a bounded confidence value."""
    try:
        return round(1.0 / (1.0 + float(score)), 4)
    except Exception:
        return 0.0


def _compute_retrieval_confidence(user_scores: List[float], global_scores: List[float]) -> float:
    """Estimate evidence confidence from top retrieval scores and personalization boost."""
    confidences = [_score_to_confidence(s) for s in (user_scores + global_scores)]
    if not confidences:
        return 0.0

    top = sorted(confidences, reverse=True)[:3]
    base = sum(top) / len(top)
    if user_scores:
        base += 0.05
    return round(min(1.0, base), 4)


def _report_context_confidence(report_rows_used: int) -> float:
    """Treat direct report fallback context as evidence for gating purposes."""
    if report_rows_used <= 0:
        return 0.0
    return min(0.35, 0.2 + (0.05 * min(report_rows_used, 3)))


def _uncertainty_response(confidence: float) -> str:
    """Safe low-confidence response that avoids speculative medical guidance."""
    return (
        "I do not have enough high-confidence evidence to answer this safely right now. "
        "Please upload a recent clinical report or ask a more specific question "
        "(for example: cancer type, current treatment, and symptom details). "
        "For urgent or treatment-changing decisions, contact your oncology team directly. "
        f"(retrieval_confidence={confidence})"
    )


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class ExperimentConfig(BaseModel):
    use_global_retrieval: bool = True
    use_patient_retrieval: bool = True
    use_reranker: bool = False
    use_uncertainty_gating: bool = True


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    use_report: Optional[bool] = True
    experiment_config: Optional[ExperimentConfig] = None
    include_retrieval_debug: Optional[bool] = False


def _build_report_fallback_context(db: Session, user_id: str) -> tuple[list[str], int]:
    """Build a compact patient-report context from the latest uploaded reports."""
    try:
        report_rows = (
            db.query(Report)
            .filter(Report.user_id == uuid.UUID(user_id))
            .order_by(desc(Report.uploaded_at))
            .limit(2)
            .all()
        )
    except Exception:
        return [], 0

    context_parts = []
    for report in report_rows:
        extracted = report.extracted_fields or {}
        summary = extracted.get("summary")
        recovery_status = extracted.get("recovery_status")
        overall_signal = extracted.get("overall_signal")
        signal_evidence = extracted.get("signal_evidence")
        table_excerpt = extracted.get("table_excerpt")

        block = [f"Report filename: {report.filename}"]
        if recovery_status:
            block.append(f"Recovery status: {recovery_status}")
        if overall_signal:
            block.append(f"Overall signal: {overall_signal}")
        if summary:
            block.append(f"Clinical summary: {summary}")
        if signal_evidence:
            if isinstance(signal_evidence, list):
                block.append("Signal evidence:")
                block.extend([f"- {item}" for item in signal_evidence[:6] if item])
            else:
                block.append(f"Signal evidence: {signal_evidence}")

        structured_fields = [
            f"{key.replace('_', ' ')}: {value}"
            for key, value in extracted.items()
            if key not in {"summary", "recovery_status", "key_metrics"} and value
        ]
        if structured_fields:
            block.append("Extracted findings:")
            block.extend(structured_fields[:12])

        if report.raw_text:
            block.append("Report text excerpt:")
            block.append(report.raw_text[:2000])
        if table_excerpt:
            block.append("Table excerpt:")
            block.append(str(table_excerpt)[:1500])

        context_parts.append("\n".join(block))

    return context_parts, len(report_rows)


@router.post("/message")
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a message to the RAG-powered chatbot. Uses Groq (Llama 3.1 70B) for fast inference."""
    user_id = current_user["sub"]

    exp_config = request.experiment_config or ExperimentConfig(
        use_patient_retrieval=request.use_report
    )

    # Load global knowledge base
    global_scores = []
    global_docs = []
    global_pairs = []
    if exp_config.use_global_retrieval:
        try:
            global_vs = load_vectorstore()
            global_pairs = global_vs.similarity_search_with_score(request.message, k=3)
            global_docs = [doc for doc, _ in global_pairs]
            global_scores = [score for _, score in global_pairs]
        except Exception:
            pass

    # Also search user-specific report if it exists
    user_docs = []
    user_store_path = VECTOR_STORE_PATH / f"user_{user_id}"
    user_scores = []
    user_pairs = []
    report_fallback_contexts = []
    report_rows_used = 0
    if exp_config.use_patient_retrieval and user_store_path.exists():
        try:
            embeddings = get_embeddings()
            user_vs = FAISS.load_local(str(user_store_path), embeddings, allow_dangerous_deserialization=True)
            user_pairs = user_vs.similarity_search_with_score(request.message, k=4)
            user_docs = [doc for doc, _ in user_pairs]
            user_scores = [score for _, score in user_pairs]
        except Exception:
            pass

    if exp_config.use_patient_retrieval and not user_docs:
        report_fallback_contexts, report_rows_used = _build_report_fallback_context(db, user_id)

    # Build context from retrieved documents
    context_parts = []
    if user_docs:
        context_parts.append("=== YOUR MEDICAL REPORT ===")
        context_parts.extend([d.page_content for d in user_docs])
    elif report_fallback_contexts:
        context_parts.append("=== YOUR LATEST UPLOADED REPORTS ===")
        context_parts.extend(report_fallback_contexts)
    if global_docs:
        context_parts.append("=== MEDICAL KNOWLEDGE BASE ===")
        context_parts.extend([d.page_content for d in global_docs])

    context = "\n\n".join(context_parts) if context_parts else "No specific context available."
    retrieval_confidence = max(
        _compute_retrieval_confidence(user_scores, global_scores),
        _report_context_confidence(report_rows_used),
    )

    if exp_config.use_uncertainty_gating:
        if retrieval_confidence < LOW_CONFIDENCE_THRESHOLD:
            out = {
                "reply": _uncertainty_response(retrieval_confidence),
                "sources_used": len(user_docs) + len(global_docs) + len(report_fallback_contexts),
                "confidence": retrieval_confidence,
                "response_mode": "abstain",
                "medical_disclaimer": "CancerCare AI does not replace professional medical advice."
            }
            if request.include_retrieval_debug:
                out["retrieval_debug"] = {
                    "global_scores": global_scores,
                    "user_scores": user_scores,
                    "global_docs": len(global_docs),
                    "user_docs": len(user_docs),
                    "report_rows_used": report_rows_used,
                }
            return out

    # Build messages for LLM
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in (request.history or [])[-6:]:  # last 3 exchanges
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({
        "role": "user",
        "content": f"Context:\n{context}\n\nQuestion: {request.message}"
    })

    # Call Groq (Llama 3.1 70B — fast and free)
    if not groq_client:
        out = {
            "reply": _fallback_reply(request.message, context),
            "sources_used": len(user_docs) + len(global_docs) + len(report_fallback_contexts),
            "confidence": retrieval_confidence,
            "response_mode": "fallback",
            "medical_disclaimer": "CancerCare AI does not replace professional medical advice."
        }
        if request.include_retrieval_debug:
            out["retrieval_debug"] = {
                "global_scores": global_scores,
                "user_scores": user_scores,
                "global_docs": len(global_docs),
                "user_docs": len(user_docs),
                "report_rows_used": report_rows_used,
            }
        return out

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=1024,
            temperature=0.3,
        )
        answer = response.choices[0].message.content
    except Exception as e:
        answer = f"I'm sorry, I encountered an error: {str(e)}"

    if exp_config.use_uncertainty_gating:
        response_mode = "cautious" if retrieval_confidence < MEDIUM_CONFIDENCE_THRESHOLD else "normal"
    else:
        response_mode = "normal"
        
    out = {
        "reply": answer,
        "sources_used": len(user_docs) + len(global_docs) + len(report_fallback_contexts),
        "confidence": retrieval_confidence,
        "response_mode": response_mode,
        "context": context,
        "medical_disclaimer": "CancerCare AI does not replace professional medical advice."
    }
    if request.include_retrieval_debug:
        out["retrieval_debug"] = {
            "global_scores": global_scores,
            "user_scores": user_scores,
            "global_docs": len(global_docs),
            "user_docs": len(user_docs),
            "report_rows_used": report_rows_used,
            "top_global_confidence": _score_to_confidence(global_scores[0]) if global_scores else 0.0,
            "top_user_confidence": _score_to_confidence(user_scores[0]) if user_scores else 0.0,
        }
    return out
