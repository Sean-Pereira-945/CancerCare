from pathlib import Path
from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from app.auth.router import get_current_user
from app.ml.report_parser import parse_report
from app.ml.rag_pipeline import add_patient_report
from app.database import get_mongo

router = APIRouter()
USER_REPORTS_DIR = Path("data/user_reports")


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

    # Store the original report so patients can reference exactly what AI used.
    user_dir = USER_REPORTS_DIR / f"user_{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    safe_filename = Path(file.filename or "report.pdf").name
    stamped_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{safe_filename}"
    stored_path = (user_dir / stamped_filename).resolve()
    stored_path.write_bytes(file_bytes)

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
            "stored_file": str(stored_path),
            "size_bytes": len(file_bytes),
            "extracted_fields": parsed["extracted_fields"],
            "raw_text": parsed["raw_text"],
            "page_count": parsed["page_count"],
            "uploaded_at": datetime.utcnow()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save report to database: {str(e)}")

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


@router.get("/files")
async def get_my_report_files(current_user: dict = Depends(get_current_user)):
    """List downloadable uploaded report PDFs for the current user."""
    try:
        mongo = get_mongo()
        records = list(mongo["reports"].find(
            {"user_id": current_user["sub"]},
            {"filename": 1, "stored_file": 1, "size_bytes": 1, "uploaded_at": 1}
        ).sort("uploaded_at", -1))

        files = []
        for r in records:
            files.append({
                "id": str(r.get("_id")),
                "filename": r.get("filename", "report.pdf"),
                "size_bytes": r.get("size_bytes", 0),
                "uploaded_at": r.get("uploaded_at"),
                "download_url": f"/api/reports/download/{str(r.get('_id'))}"
            })

        return {"files": files}
    except Exception:
        return {"files": []}


@router.get("/download/{report_id}")
async def download_my_report_file(report_id: str, current_user: dict = Depends(get_current_user)):
    """Download an uploaded PDF report that belongs to the authenticated user."""
    mongo = get_mongo()

    record = None
    if ObjectId.is_valid(report_id):
        record = mongo["reports"].find_one({"_id": ObjectId(report_id), "user_id": current_user["sub"]})
    if record is None:
        record = mongo["reports"].find_one({"_id": report_id, "user_id": current_user["sub"]})

    if not record:
        raise HTTPException(status_code=404, detail="Report file not found")

    stored_file = record.get("stored_file")
    if not stored_file:
        raise HTTPException(status_code=404, detail="Stored report file is unavailable")

    target = Path(stored_file)
    if not target.exists() or target.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="Stored report file is unavailable")

    return FileResponse(path=target, media_type="application/pdf", filename=record.get("filename", target.name))
