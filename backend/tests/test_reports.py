from fastapi.testclient import TestClient

from app.main import app
from app.auth.router import get_current_user
import app.routes.reports as reports_routes


client = TestClient(app)


def _mock_user():
    return {"sub": "user-123", "role": "patient"}


class _MockCollection:
    def insert_one(self, _doc):
        return None

    def find(self, *_args, **_kwargs):
        return []


class _MockMongo:
    def __getitem__(self, _name):
        return _MockCollection()


def test_upload_report_rejects_non_pdf():
    app.dependency_overrides[get_current_user] = _mock_user
    try:
        response = client.post(
            "/api/reports/upload",
            files={"file": ("note.txt", b"hello", "text/plain")},
        )
        assert response.status_code == 400
        assert "Only PDF files" in response.json().get("detail", "")
    finally:
        app.dependency_overrides.clear()


def test_upload_report_pdf_success(monkeypatch):
    monkeypatch.setattr(
        reports_routes,
        "parse_report",
        lambda _bytes: {
            "raw_text": "raw",
            "full_text": "full",
            "extracted_fields": {"cancer_type": "breast"},
            "page_count": 1,
        },
    )
    monkeypatch.setattr(reports_routes, "add_patient_report", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(reports_routes, "get_mongo", lambda: _MockMongo())

    app.dependency_overrides[get_current_user] = _mock_user
    try:
        response = client.post(
            "/api/reports/upload",
            files={"file": ("report.pdf", b"%PDF-1.4 test", "application/pdf")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body.get("status") == "Report uploaded and indexed"
        assert "extracted" in body
    finally:
        app.dependency_overrides.clear()
