"""Temporary Office export checks; to be removed after source-only cleanup."""
from io import BytesIO
from zipfile import ZipFile

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.export_routes import excel_export, router, word_export

DATA = {
    "answer": "一、产业发展部署\n推进先进制造业。",
    "claims": [{"text": "产业规模发展", "dimension": "工业",
                "quotes": ["强化先进制造业"], "chunk_ids": ["c1"]}],
    "evidence_refs": [{"planid": "1831", "title": "地区规划",
                       "area": "临朐县", "fyp": "十一五",
                       "section_path": "工业", "chunk_id": "c1"}],
    "status": "completed", "task_type": "qa", "evidence_status": "verified",
}


def test_word_file_contains_research_text():
    with ZipFile(BytesIO(word_export("产业如何发展？", DATA))) as z:
        xml = z.read("word/document.xml").decode()
        assert "产业如何发展" in xml
        assert "推进先进制造业" in xml


def test_excel_file_contains_sheets_and_readable_text():
    with ZipFile(BytesIO(excel_export("产业如何发展？", DATA))) as z:
        assert "xl/workbook.xml" in z.namelist()
        assert "地区规划" in z.read("xl/sharedStrings.xml").decode()


def test_endpoint_and_unfinished_guard():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    ok = client.post("/api/exports/docx", json={"question": "研究", "result": DATA})
    assert ok.status_code == 200 and ok.content.startswith(b"PK")
    failed = client.post("/api/exports/xlsx", json={
        "question": "研究", "result": {**DATA, "status": "failed"},
    })
    assert failed.status_code == 422
