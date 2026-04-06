from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from groq import Groq
from app.config import get_settings
from app.auth.router import get_current_user
from app.ml.rag_pipeline import load_vectorstore, get_embeddings
from pathlib import Path
from langchain_community.vectorstores import FAISS

router = APIRouter()
settings = get_settings()

# Initialize Groq client for fast LLM inference
groq_client = None
if settings.groq_api_key:
    groq_client = Groq(api_key=settings.groq_api_key)

SYSTEM_PROMPT = """You are CancerCare AI, a compassionate and knowledgeable health assistant
specifically designed for cancer patients. You answer questions based on the provided medical
context. Always:
1. Be empathetic and supportive in tone
2. Cite information from the context when available
3. Remind users that you are not a substitute for professional medical advice
4. If the context does not contain enough information, say so clearly
Do NOT make up medical information."""


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    use_report: Optional[bool] = True


@router.post("/message")
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Send a message to the RAG-powered chatbot. Uses Groq (Llama 3.1 70B) for fast inference."""
    user_id = current_user["sub"]

    # Load global knowledge base
    try:
        global_vs = load_vectorstore()
        global_docs = global_vs.similarity_search(request.message, k=3)
    except Exception:
        global_docs = []

    # Also search user-specific report if it exists
    user_docs = []
    user_store_path = Path(f"data/vector_store/user_{user_id}")
    if request.use_report and user_store_path.exists():
        try:
            embeddings = get_embeddings()
            user_vs = FAISS.load_local(str(user_store_path), embeddings, allow_dangerous_deserialization=True)
            user_docs = user_vs.similarity_search(request.message, k=4)
        except Exception:
            pass

    # Build context from retrieved documents
    context_parts = []
    if user_docs:
        context_parts.append("=== YOUR MEDICAL REPORT ===")
        context_parts.extend([d.page_content for d in user_docs])
    if global_docs:
        context_parts.append("=== MEDICAL KNOWLEDGE BASE ===")
        context_parts.extend([d.page_content for d in global_docs])

    context = "\n\n".join(context_parts) if context_parts else "No specific context available."

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
        return {"reply": "Chatbot not configured. Please set GROQ_API_KEY in .env", "sources_used": 0}

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=messages,
            max_tokens=1024,
            temperature=0.3,
        )
        answer = response.choices[0].message.content
    except Exception as e:
        answer = f"I'm sorry, I encountered an error: {str(e)}"

    return {"reply": answer, "sources_used": len(user_docs) + len(global_docs)}
