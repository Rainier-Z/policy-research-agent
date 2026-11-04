"""On-demand batch evaluation using the existing /api/runs entrypoint.

Uploads and generated answers live in process memory only. Nothing is
committed to the repository or persisted as a validation-results file.
"""
from __future__ import annotations

import asyncio
import io
import time
from uuid import uuid4

import httpx
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from .validation_excel import MAX_ROWS, TemplateError, export_excel, parse_excel

router = APIRouter(prefix="/api/validation-batches", tags=["validation-batches"])
UPLOAD_TTL_SECONDS = 1800
RESULT_TTL_SECONDS = 3600
PER_QUESTION_TIMEOUT_SECONDS = 210
MAX_ACTIVE_JOBS = 2


class ValidationBatchService:
    def __init__(self):
        self.uploads: dict[str, dict] = {}
        self.jobs: dict[str, dict] = {}
        self.worker_gate = asyncio.Semaphore(1)
        self.tasks: set[asyncio.Task] = set()

    def prune(self):
        now = time.monotonic()
        self.uploads = {key: item for key, item in self.uploads.items()
                        if now - item["created"] < UPLOAD_TTL_SECONDS}
        self.jobs = {key: item for key, item in self.jobs.items()
                     if item["state"] in ("queued", "running", "cancelling")
                     or now - item["updated"] < RESULT_TTL_SECONDS}

    def preview(self, rows: list[dict]) -> dict:
        self.prune()
        if len(self.uploads) >= 8:
            raise HTTPException(status_code=429, detail="待执行的上传文件过多")
        key = uuid4().hex
        self.uploads[key] = {"created": time.monotonic(), "rows": rows}
        return {
            "upload_id": key, "total": len(rows),
            "columns": ["问题", "预期答案"],
            "preview": [{"question": r["question"], "expected": r["expected"]}
                        for r in rows[:10]],
        }

    def start(self, upload_id: str, app) -> dict:
        self.prune()
        if not getattr(app.state, "ready", False):
            raise HTTPException(status_code=503, detail="研究服务尚未就绪")
        active = sum(j["state"] in ("queued", "running", "cancelling")
                     for j in self.jobs.values())
        if active >= MAX_ACTIVE_JOBS:
            raise HTTPException(status_code=429, detail="当前批量任务过多")
        upload = self.uploads.pop(upload_id, None)
        if not upload:
            raise HTTPException(status_code=404, detail="上传已过期或已开始执行")
        job_id = uuid4().hex
        now = time.monotonic()
        job = {
            "id": job_id, "rows": upload["rows"], "total": len(upload["rows"]),
            "done": 0, "state": "queued", "cancel": False,
            "created": now, "updated": now,
        }
        self.jobs[job_id] = job
        task = asyncio.create_task(self.run(job, app))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return {"job_id": job_id, "state": "queued", "total": job["total"]}

    async def run(self, job: dict, app):
        try:
            async with self.worker_gate:
                if job["cancel"]:
                    job["state"] = "cancelled"
                    return
                job["state"] = "running"
                # In-process ASGI request calls exactly the same research route
                # as the interactive page (including catalog discovery).
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app),
                    base_url="http://validation-batch.local", timeout=None,
                ) as client:
                    for row in job["rows"]:
                        if job["cancel"]:
                            job["state"] = "cancelled"
                            break
                        started = time.monotonic()
                        try:
                            response = await asyncio.wait_for(
                                client.post("/api/runs", json={
                                    "question": row["question"], "task_type": "qa",
                                    # Each question starts an independent session:
                                    # no accidental cross-question evidence leakage.
                                    "session_id": "v_" + uuid4().hex,
                                }),
                                timeout=PER_QUESTION_TIMEOUT_SECONDS,
                            )
                            if response.status_code != 200:
                                row["status"] = ("超时" if response.status_code == 504
                                                 else "失败")
                            else:
                                payload = response.json()
                                answer = payload.get("answer", "")
                                row["answer"] = answer[:32000] if isinstance(answer, str) else ""
                                code = (payload.get("error") or {}).get("code", "")
                                if code in ("MODEL_TIMEOUT", "TIMEOUT"):
                                    row["status"] = "超时"
                                elif payload.get("status") == "completed":
                                    row["status"] = "正常"
                                else:
                                    row["status"] = "失败"
                        except (asyncio.TimeoutError, TimeoutError):
                            row["status"] = "超时"
                        except Exception:  # noqa: BLE001
                            # Do not leak API keys, server errors or tool traces.
                            row["status"] = "失败"
                        finally:
                            row["duration"] = round(time.monotonic() - started, 1)
                            job["done"] += 1
                            job["updated"] = time.monotonic()
                    if job["state"] != "cancelled":
                        job["state"] = "finished"
        except asyncio.CancelledError:
            job["state"] = "cancelled"
            raise
        except Exception:  # noqa: BLE001
            job["state"] = "failed"
        finally:
            job["updated"] = time.monotonic()

    def get(self, job_id: str) -> dict:
        self.prune()
        job = self.jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="任务不存在或已过期")
        return job

    async def close(self):
        for task in list(self.tasks):
            task.cancel()
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        self.jobs.clear()
        self.uploads.clear()


def service(request: Request) -> ValidationBatchService:
    return request.app.state.validation_batches


@router.post("/preview")
async def preview(request: Request, file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=422, detail="请上传模板4格式的.xlsx文件")
    try:
        content = await file.read(3 * 1024 * 1024 + 1)
        rows = parse_excel(content)
    except TemplateError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        await file.close()
    return service(request).preview(rows)


@router.post("/{upload_id}/start")
async def start(request: Request, upload_id: str):
    return service(request).start(upload_id, request.app)


@router.get("/jobs/{job_id}")
async def status(request: Request, job_id: str):
    job = service(request).get(job_id)
    return {
        "job_id": job["id"], "state": job["state"],
        "total": job["total"], "completed": job["done"],
        "rows": [{"index": idx + 1, "question": row["question"],
                  "status": row["status"], "duration": row["duration"]}
                 for idx, row in enumerate(job["rows"])],
    }


@router.post("/jobs/{job_id}/cancel")
async def cancel(request: Request, job_id: str):
    job = service(request).get(job_id)
    if job["state"] in ("queued", "running"):
        job["cancel"] = True
        job["state"] = "cancelling"
    return {"state": job["state"]}


@router.get("/jobs/{job_id}/export")
async def export(request: Request, job_id: str):
    job = service(request).get(job_id)
    if job["state"] not in ("finished", "failed", "cancelled"):
        raise HTTPException(status_code=409, detail="任务尚未结束")
    content = export_excel(job["rows"])
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="guance-validation-results.xlsx"',
            "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
        },
    )
