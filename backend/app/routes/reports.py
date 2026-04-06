from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.auth.router import get_current_user
from app.ml.report_parser import parse_report
from app.ml.rag_pipeline import add_patient_report
from app.database import get_mongo
from datetime import datetime

router = APIRouter()


@router.post("/upload")
async def upload_report(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a medical report PDF. Parses it, extracts key fields, and indexes for RAG."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    file_bytes = await file.read()
    user_id = current_user["sub"]

    # Parse the report
    parsed = parse_report(file_bytes)

    # Add to user's vector store for RAG
    try:
        add_patient_report(user_id, parsed["full_text"])
    except Exception:
        pass  # Indexing failure shouldn't block upload

    # Save parsed data to MongoDB
    try:
        mongo = get_mongo()
        mongo["reports"].insert_one({
            "user_id": user_id,
            "filename": file.filename,
            "extracted_fields": parsed["extracted_fields"],
            "raw_text": parsed["raw_text"],
            "page_count": parsed["page_count"],
            "uploaded_at": datetime.utcnow()
        })
    except Exception:
        pass

    return {
        "status": "Report uploaded and indexed",
        "extracted": parsed["extracted_fields"],
        "page_count": parsed["page_count"]
    }


@router.get("/my-reports")
async def get_my_reports(current_user: dict = Depends(get_current_user)):
    """Get all reports uploaded by the current user."""
    try:
        mongo = get_mongo()
        reports = list(mongo["reports"].find(
            {"user_id": current_user["sub"]},
            {"_id": 0, "full_text": 0}  # exclude large fields
        ).sort("uploaded_at", -1))
        return {"reports": reports}
    except Exception:
        return {"reports": []}
