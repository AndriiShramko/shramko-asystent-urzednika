"""AUDIT-8 VC-2: a DOCX or XLSX with an embedded Office object (word/embeddings/*.xlsx, as Word writes a pasted
Excel table) is a normal file, not "an archive inside an archive". Any other ZIP member stays refused."""
from __future__ import annotations

import io
import zipfile

import factory as fx
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def make() -> TestClient:
    env = {"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000"}
    return TestClient(create_app(Settings.from_env(env)))


def with_member(base: bytes, name: str, data: bytes) -> bytes:
    src = zipfile.ZipFile(io.BytesIO(base))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for i in src.infolist():
            z.writestr(i, src.read(i))
        z.writestr(name, data)
    return buf.getvalue()


def convert(client: TestClient, name: str, data: bytes):
    return client.post("/v1/forms/convert", files={"file": (name, data, "application/octet-stream")})


def test_docx_with_an_embedded_excel_object_converts():
    data = with_member(fx.docx(), "word/embeddings/Microsoft_Excel_Worksheet.xlsx", fx.xlsx())
    r = convert(make(), "a.docx", data)
    assert r.status_code == 200, r.text


def test_xlsx_with_an_embedded_word_object_converts():
    data = with_member(fx.xlsx(), "xl/embeddings/Microsoft_Word_Document.docx", fx.docx())
    r = convert(make(), "a.xlsx", data)
    assert r.status_code == 200, r.text


def test_any_embedded_package_type_converts():
    # a Visio drawing, a binary workbook, a slide: Word keeps each as a ZIP under word/embeddings/ (review 45, VC-2)
    for member in ("Microsoft_Visio_Drawing.vsdx", "Microsoft_Excel_Binary_Worksheet.xlsb", "Presentation.sldx"):
        data = with_member(fx.docx(), f"word/embeddings/{member}", fx.xlsx())
        r = convert(make(), "a.docx", data)
        assert r.status_code == 200, (member, r.text)


def test_an_embedded_macro_workbook_counts_as_macros_under_strict():
    data = with_member(fx.docx(), "word/embeddings/Microsoft_Excel_Macro-Enabled_Worksheet.xlsm", fx.xlsx())
    env = {"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000", "ACTIVE_CONTENT": "strict"}
    r = TestClient(create_app(Settings.from_env(env))).post(
        "/v1/forms/convert", files={"file": ("a.docx", data, "application/octet-stream")})
    assert r.json().get("code") == "ACTIVE_CONTENT", r.text


def test_a_zip_elsewhere_in_a_docx_is_still_refused():
    data = with_member(fx.docx(), "word/media/x.zip", fx.zip_of({"x.pdf": fx.pdf()}))
    r = convert(make(), "a.docx", data)
    assert r.status_code == 413 and r.json()["code"] == "ARCHIVE_LIMIT"
