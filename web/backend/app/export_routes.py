"""In-memory DOCX/XLSX export of user-visible policy research output."""
from __future__ import annotations

import io
import re
from datetime import datetime, timezone
from typing import Any

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from xlsxwriter import Workbook

router = APIRouter(prefix="/api/exports", tags=["exports"])
MAX_PAYLOAD = 2_000_000
MAX_CELL = 32_000
MAX_ITEMS = 2_000


class ExportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(default="", max_length=10_000)
    result: dict[str, Any]


def value(item: Any, limit: int = MAX_CELL) -> str:
    if isinstance(item, (str, int, float, bool)):
        return str(item)[:limit]
    return ""


def records(data: Any) -> list[dict[str, Any]]:
    return [r for r in data[:MAX_ITEMS] if isinstance(r, dict)] if isinstance(data, list) else []


def excel_text(item: Any) -> str:
    raw = value(item)
    # Spreadsheet formula/URL injection must not be possible from policy text.
    return "'" + raw if raw.lstrip().startswith(("=", "+", "-", "@")) else raw


def word_export(question: str, result: dict[str, Any]) -> bytes:
    doc = Document()
    norm = doc.styles["Normal"]
    norm.font.name, norm.font.size = "Microsoft YaHei", Pt(10.5)
    norm.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    doc.sections[0].top_margin = Cm(2.2)
    doc.sections[0].bottom_margin = Cm(2)
    doc.add_heading("政策研究结果", 0)
    if question:
        doc.add_heading("研究问题", level=1)
        doc.add_paragraph(question)
    doc.add_heading("研究正文", level=1)
    answer = value(result.get("answer"), 150_000)
    for line in (answer or "本轮无研究正文").replace("\r\n", "\n").split("\n"):
        text = line.strip()
        if not text:
            continue
        heading = re.match(r"^(#{1,4})\s+(.+)", text)
        if heading:
            doc.add_heading(heading.group(2), level=min(heading.group(1).__len__() + 1, 4))
        elif re.match(r"^[一二三四五六七八九十]+、", text):
            doc.add_heading(text, level=2)
        else:
            doc.add_paragraph(text)
    facts = records(result.get("claims"))
    if facts:
        doc.add_heading("事实依据", level=1)
        for n, claim in enumerate(facts, 1):
            doc.add_paragraph(f"{n}. {value(claim.get('text'))}")
            for quote in (claim.get("quotes") or [])[:12]:
                if isinstance(quote, str) and quote.strip():
                    doc.add_paragraph("原文：" + value(quote))
            ids = claim.get("chunk_ids")
            if isinstance(ids, list) and ids:
                doc.add_paragraph("证据区块：" + "、".join(map(str, ids[:30])))
    sources = records(result.get("evidence_refs"))
    if sources:
        doc.add_heading("参考文献", level=1)
        for n, source in enumerate(sources, 1):
            components = [f"《{value(source.get('title'))}》",
                          value(source.get("area")), value(source.get("fyp")),
                          "planid=" + value(source.get("planid")),
                          value(source.get("section_path"))]
            doc.add_paragraph(f"[{n}] " + " · ".join(filter(None, components)))
    if result.get("evidence_status") != "verified":
        doc.add_paragraph("提示：本轮证据未全部核验，请核对来源原文。")
    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()


def tab(wb: Workbook, title: str, columns: list[str], rows: list[list[Any]], widths: list[int]):
    sheet = wb.add_worksheet(title)
    header = wb.add_format({"bold": True, "bg_color": "#E4EAF5", "font_color": "#263653"})
    body = wb.add_format({"valign": "top", "text_wrap": True})
    sheet.freeze_panes(1, 0)
    for i, col in enumerate(columns):
        sheet.write_string(0, i, col, header)
        sheet.set_column(i, i, widths[i])
    for n, row in enumerate(rows[:MAX_ITEMS], 1):
        for i, cell in enumerate(row):
            if type(cell) is int:
                sheet.write_number(n, i, cell, body)
            else:
                sheet.write_string(n, i, excel_text(cell), body)
    if rows:
        sheet.autofilter(0, 0, min(len(rows), MAX_ITEMS), len(columns) - 1)


def flatten(obj: Any, path: str = "", depth: int = 0):
    if depth >= 8:
        yield path, "[超出层级限制]"
    elif isinstance(obj, dict):
        for key, v in list(obj.items())[:MAX_ITEMS]:
            yield from flatten(v, (path + "." if path else "") + str(key), depth + 1)
    elif isinstance(obj, list):
        for n, v in enumerate(obj[:MAX_ITEMS]):
            yield from flatten(v, path + f"[{n}]", depth + 1)
    else:
        yield path, value(obj)


def excel_export(question: str, result: dict[str, Any]) -> bytes:
    out = io.BytesIO()
    wb = Workbook(out, {"in_memory": True, "strings_to_formulas": False,
                        "strings_to_urls": False})
    try:
        first = [["研究问题", question], ["任务类型", result.get("task_type")],
                 ["执行状态", result.get("status")],
                 ["证据状态", result.get("evidence_status")]]
        first += [["研究正文", line] for line in value(result.get("answer"), 150_000).split("\n")
                  if line.strip()]
        tab(wb, "研究结果", ["项目", "内容"], first, [24, 96])
        tab(wb, "核验事实", ["序号", "维度", "事实", "原文引句", "证据区块"],
            [[n, c.get("dimension"), c.get("text"),
              "；".join(value(v) for v in (c.get("quotes") or [])[:12]),
              "、".join(str(v) for v in (c.get("chunk_ids") or [])[:50])]
             for n, c in enumerate(records(result.get("claims")), 1)],
            [9, 22, 72, 75, 42])
        tab(wb, "参考文献",
            ["序号", "planid", "标题", "地区", "时期", "章节路径", "chunk_id", "起点", "终点"],
            [[n, ref.get("planid"), ref.get("title"), ref.get("area"),
              ref.get("fyp"), ref.get("section_path"), ref.get("chunk_id"),
              ref.get("char_start"), ref.get("char_end")]
             for n, ref in enumerate(records(result.get("evidence_refs")), 1)],
            [9, 15, 65, 24, 25, 48, 35, 13, 13])
        structured = result.get("structured")
        if isinstance(structured, (dict, list)):
            tab(wb, "结构化研究", ["字段路径", "内容"],
                [[path, content] for path, content in list(flatten(structured))[:MAX_ITEMS]],
                [70, 96])
    finally:
        wb.close()
    return out.getvalue()


@router.post("/{format_name}")
async def export_result(format_name: str, payload: ExportRequest):
    if format_name not in {"docx", "xlsx"}:
        raise HTTPException(404, "不支持的导出格式")
    if len(payload.model_dump_json()) > MAX_PAYLOAD:
        raise HTTPException(413, "导出内容过大")
    result = payload.result
    if result.get("status") != "completed":
        raise HTTPException(422, "未完成的研究不允许导出为正式报告")
    output = (word_export(payload.question, result) if format_name == "docx"
              else excel_export(payload.question, result))
    name = "guance-research-" + datetime.now(timezone.utc).strftime("%Y%m%d")
    mime = ("application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if format_name == "docx" else
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    return StreamingResponse(io.BytesIO(output), media_type=mime, headers={
        "Content-Disposition": f'attachment; filename="{name}.{format_name}"',
        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
    })
