"""Read official template 4 and create template 5, without writing data to disk."""
import io
import posixpath
import re
import zipfile
from xml.etree import ElementTree as ET

from xlsxwriter import Workbook

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
HEADERS_IN = ("问题", "预期答案")
HEADERS_OUT = ("问题", "预期答案", "智能体实际回复", "耗时(秒)", "状态")
MAX_ROWS = 500


class TemplateError(ValueError):
    pass


def parse_excel(data: bytes) -> list[dict]:
    if not data or len(data) > 3 * 1024 * 1024:
        raise TemplateError("上传文件为空或大于3MB")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as book:
            files = book.infolist()
            if len(files) > 150 or sum(f.file_size for f in files) > 20 * 1024 * 1024:
                raise TemplateError("Excel解压内容过大")
            workbook = ET.fromstring(book.read("xl/workbook.xml"))
            sheet = workbook.find("m:sheets/m:sheet", NS)
            if sheet is None:
                raise TemplateError("没有工作表")
            rel = ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
            target = next((n.get("Target") for n in rel
                           if n.get("Id") == sheet.attrib.get(RID)), None)
            if not target:
                raise TemplateError("无法读取工作表")
            path = posixpath.normpath(target.lstrip("/") if target.startswith("/")
                                      else "xl/" + target)
            if not path.startswith("xl/worksheets/"):
                raise TemplateError("工作表路径无效")
            root = ET.fromstring(book.read(path))
            shared = []
            if "xl/sharedStrings.xml" in book.namelist():
                strings = ET.fromstring(book.read("xl/sharedStrings.xml"))
                shared = ["".join(t.text or "" for t in cell.findall(".//m:t", NS))
                          for cell in strings.findall("m:si", NS)]
    except (zipfile.BadZipFile, KeyError, ET.ParseError, IndexError, StopIteration) as e:
        raise TemplateError("不是有效的xlsx文件") from e

    rows = []
    for node in root.findall("m:sheetData/m:row", NS):
        values = {}
        for cell in node.findall("m:c", NS):
            match = re.fullmatch(r"([A-Z]+)[0-9]+", cell.get("r", ""))
            if not match or match.group(1) not in ("A", "B"):
                continue
            if cell.find("m:f", NS) is not None:
                raise TemplateError("问题和预期答案不能是公式")
            raw = cell.findtext("m:v", "", NS)
            if cell.get("t") == "s":
                try:
                    raw = shared[int(raw)]
                except (ValueError, IndexError) as e:
                    raise TemplateError("字符串索引损坏") from e
            elif cell.get("t") == "inlineStr":
                raw = "".join(n.text or "" for n in cell.findall(".//m:is/m:t", NS))
            if len(raw) > 32000:
                raise TemplateError("单元格内容过长")
            values[match.group(1)] = raw.strip()
        if values:
            rows.append(values)
        if len(rows) > MAX_ROWS + 1:
            raise TemplateError("最多支持500道题")
    if not rows or (rows[0].get("A"), rows[0].get("B")) != HEADERS_IN:
        raise TemplateError("首行应依次为「问题」「预期答案」")
    result = []
    for row in rows[1:]:
        question, expected = row.get("A", ""), row.get("B", "")
        if not question:
            if expected:
                raise TemplateError("存在预期答案但问题为空的行")
            continue
        if len(question) > 4000:
            raise TemplateError("单题问题长度不能超过4000字")
        result.append({"question": question, "expected": expected,
                       "answer": "", "duration": None, "status": "待运行"})
    if not result:
        raise TemplateError("没有有效问题")
    return result


def export_excel(rows: list[dict]) -> bytes:
    output = io.BytesIO()
    workbook = Workbook(output, {"in_memory": True, "strings_to_formulas": False,
                                  "strings_to_urls": False})
    try:
        sheet = workbook.add_worksheet("Sheet1")
        title = workbook.add_format({"bold": True, "bg_color": "#EBF2FB"})
        wrap = workbook.add_format({"text_wrap": True, "valign": "top"})
        for col, heading in enumerate(HEADERS_OUT):
            sheet.write_string(0, col, heading, title)
        for col, width in enumerate((44, 54, 80, 15, 14)):
            sheet.set_column(col, col, width)
        sheet.freeze_panes(1, 0)
        for num, row in enumerate(rows, 1):
            for col, key in enumerate(("question", "expected", "answer")):
                sheet.write_string(num, col, str(row.get(key, ""))[:32000], wrap)
            seconds = row.get("duration")
            if type(seconds) in (float, int):
                sheet.write_number(num, 3, round(seconds, 1))
            sheet.write_string(num, 4, row.get("status", ""), wrap)
        sheet.autofilter(0, 0, len(rows), 4)
    finally:
        workbook.close()
    return output.getvalue()
