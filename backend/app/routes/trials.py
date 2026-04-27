from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.auth.router import get_current_user

router = APIRouter()
KNOWLEDGE_BASE_DIR = Path("data/knowledge_base").resolve()


@router.get("/references")
async def list_reference_documents(current_user: dict = Depends(get_current_user)):
    """List cancer knowledge-base PDFs used by the assistant for grounded answers."""
    if not KNOWLEDGE_BASE_DIR.exists():
        return {"documents": []}

    docs = []
    for file_path in sorted(KNOWLEDGE_BASE_DIR.rglob("*.pdf")):
        rel = file_path.relative_to(KNOWLEDGE_BASE_DIR).as_posix()
        docs.append({
            "name": file_path.name,
            "relative_path": rel,
            "size_bytes": file_path.stat().st_size,
            "download_url": f"/api/trials/references/file/{quote(rel, safe='')}"
        })

    return {"documents": docs}


@router.get("/references/file/{doc_path:path}")
async def download_reference_document(doc_path: str, current_user: dict = Depends(get_current_user)):
    """Download a knowledge-base PDF by relative path."""
    target = (KNOWLEDGE_BASE_DIR / doc_path).resolve()

    # Prevent path traversal outside knowledge base directory.
    if not str(target).startswith(str(KNOWLEDGE_BASE_DIR)):
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not target.exists() or target.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="Reference document not found")

    return FileResponse(path=target, media_type="application/pdf", filename=target.name)
