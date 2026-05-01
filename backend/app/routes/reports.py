from pathlib import Path
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.auth.router import get_current_user
from app.ml.report_parser import parse_report, analyze_with_llm
from app.ml.rag_pipeline import add_patient_report, BACKEND_DIR
from app.ml.risk_model import predict_risk
from app.database import get_db, SessionLocal
from app.models.db import Report

router = APIRouter()
USER_REPORTS_DIR = BACKEND_DIR / "data/user_reports"

def _summary_needs_regen(summary: str | None) -> bool:
    if not summary:
        return True
    summary_lower = summary.lower()
    fallback_markers = [
        "diagnosis:",
        "stage ",
        "planned treatment:",
        "medications:",
    ]
    return any(marker in summary_lower for marker in fallback_markers)


def _run_ai_analysis(report_id: uuid.UUID, combined_text: str) -> None:
    """Background task: run LLM analysis and update report record."""
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return

        ai_analysis = analyze_with_llm(combined_text)
        extracted = report.extracted_fields or {}
        for key, value in ai_analysis.items():
            if value in {None, "", "Unknown", "AI analysis unavailable", "Failed to analyze with AI"}:
                continue
            extracted[key] = value
        report.extracted_fields = extracted
        db.commit()
    finally:
        db.close()


@router.post("/upload")
async def upload_report(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    """Upload a medical report PDF. Parses it, extracts key fields, and indexes for RAG."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    file_bytes = await file.read()
    user_id_str = current_user["sub"]
    user_id = uuid.UUID(user_id_str)

    # Store the original report
    user_dir = USER_REPORTS_DIR / f"user_{user_id_str}"
    user_dir.mkdir(parents=True, exist_ok=True)
    safe_filename = Path(file.filename or "report.pdf").name
    stamped_filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{safe_filename}"
    stored_path = (user_dir / stamped_filename).resolve()
    stored_path.write_bytes(file_bytes)

    # Parse the report
    parsed = parse_report(file_bytes, include_ai=True, include_tables=False)
    summary = parsed["extracted_fields"].get("summary")
    if not summary or summary in {"AI analysis unavailable", "Failed to analyze with AI"}:
        raise HTTPException(status_code=502, detail="Groq analysis failed. Check GROQ_API_KEY and try again.")

    # Add to user's vector store for RAG (background)
    if background_tasks is not None:
        background_tasks.add_task(add_patient_report, user_id_str, parsed["full_text"])

    # Attempt to get a risk score
    risk_assessment = None
    try:
        risk_assessment = predict_risk(parsed["extracted_fields"])
    except Exception:
        pass

    # Save to SQL database
    try:
        new_report = Report(
            user_id=user_id,
            filename=file.filename,
            stored_file=str(stored_path),
            size_bytes=len(file_bytes),
            extracted_fields=parsed["extracted_fields"],
            raw_text=parsed["raw_text"],
            page_count=parsed["page_count"]
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save report to database: {str(e)}")

    if background_tasks is not None:
        background_tasks.add_task(_run_ai_analysis, new_report.id, parsed["full_text"])

    return {
        "status": "Report uploaded and indexed",
        "id": str(new_report.id),
        "extracted": parsed["extracted_fields"],
        "risk_assessment": risk_assessment,
        "page_count": parsed["page_count"]
    }


@router.get("/my-reports")
async def get_my_reports(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all reports uploaded by the current user."""
    user_id = uuid.UUID(current_user["sub"])
    reports = db.query(Report).filter(Report.user_id == user_id).order_by(desc(Report.uploaded_at)).all()

    updated = False
    for report in reports:
        extracted = report.extracted_fields or {}
        if _summary_needs_regen(extracted.get("summary")) and report.raw_text:
            ai_analysis = analyze_with_llm(report.raw_text)
            summary = ai_analysis.get("summary")
            if summary and summary not in {"AI analysis unavailable", "Failed to analyze with AI"}:
                extracted.update(ai_analysis)
                report.extracted_fields = extracted
                updated = True

    if updated:
        db.commit()

    return {
        "reports": [
            {
                "id": str(r.id),
                "filename": r.filename,
                "size_bytes": r.size_bytes,
                "extracted_fields": r.extracted_fields,
                "page_count": r.page_count,
                "uploaded_at": r.uploaded_at
            } for r in reports
        ]
    }


@router.get("/files")
async def get_my_report_files(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """List downloadable uploaded report PDFs for the current user."""
    user_id = uuid.UUID(current_user["sub"])
    records = db.query(Report).filter(Report.user_id == user_id).order_by(desc(Report.uploaded_at)).all()

    return {
        "files": [
            {
                "id": str(r.id),
                "filename": r.filename,
                "size_bytes": r.size_bytes,
                "uploaded_at": r.uploaded_at,
                "download_url": f"/api/reports/download/{str(r.id)}"
            } for r in records
        ]
    }


@router.get("/download/{report_id}")
async def download_my_report_file(report_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Download an uploaded PDF report that belongs to the authenticated user."""
    user_id = uuid.UUID(current_user["sub"])
    report_uuid = uuid.UUID(report_id)
    
    record = db.query(Report).filter(and_(Report.id == report_uuid, Report.user_id == user_id)).first()

    if not record:
        raise HTTPException(status_code=404, detail="Report file not found")

    target = Path(record.stored_file)
    if not target.exists() or target.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="Stored report file is unavailable")

    return FileResponse(path=target, media_type="application/pdf", filename=record.filename)
