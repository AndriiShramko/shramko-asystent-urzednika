"""BL13 FIX-TYPE: the card's minimum (line 65) - only supported formats, the content (MIME) must match the extension.

Under STRICT_EXTENSIONS=true (the default) a file whose content proves another kind than its extension is 415
TYPE_MISMATCH with a Polish reason naming both; a file with no extension is 415 EXTENSION. Exceptions: a .doc that
holds DOCX or RTF (the partner's own s07.doc and ref05.doc) and jpg/jpeg/jpe as one kind. STRICT_EXTENSIONS=false
keeps reading by content. Every file is built in code."""
from __future__ import annotations

import factory as fx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.guard import ProblemError, inspect_upload
from app.main import create_app

RTF = b"{\\rtf1\\ansi\\ansicpg1250 \\pard Wniosek o wydanie zezwolenia\\par \\pard Imi\\'ea i nazwisko: ..........\\par}"
S = Settings(auth_mode="off")
LOOSE = Settings(auth_mode="off", strict_extensions=False)


def refused(name, data, code, settings=S):
    with pytest.raises(ProblemError) as ei:
        inspect_upload(name, data, settings)
    assert ei.value.code == code, ei.value.detail
    assert ei.value.status == 415
    return ei.value


def post(c: TestClient, name: str, data: bytes):
    body, ctype = fx.multipart([("file", name, data, "application/octet-stream")])
    return c.post("/v1/forms/convert", content=body, headers={"Content-Type": ctype})


@pytest.mark.parametrize("name,data,label,fix", [
    ("a.pdf", fx.png(), "obraz PNG", ".png"), ("a.xlsx", fx.docx(), "dokument DOCX", ".docx"),
    ("a.xlsx", fx.ods(), "arkusz ODS", ".ods"), ("a.docx", fx.xlsx(), "arkusz XLSX", ".xlsx"),
    ("a.png", fx.jpeg(), "obraz JPEG", ".jpg"), ("a.doc", fx.pdf(), "dokument PDF", ".pdf"),
])
def test_content_of_another_kind_is_415_naming_both_and_the_remedy(name, data, label, fix):
    e = refused(name, data, "TYPE_MISMATCH")
    ext = "." + name.rsplit(".", 1)[1]
    assert e.detail.startswith(f"Rozszerzenie {ext}, a zawartość to {label}.")
    assert f"Zmień rozszerzenie na {fix} albo wybierz właściwy plik." in e.detail


def test_rtf_named_pdf_is_415_and_says_the_format_is_not_supported():
    e = refused("a.pdf", RTF, "TYPE_MISMATCH")
    assert "dokument RTF" in e.detail and "nie jest obsługiwany" in e.detail


def test_no_extension_is_415_with_the_accepted_list():
    e = refused("wniosek", fx.pdf(), "EXTENSION")
    assert "nie ma rozszerzenia" in e.detail and "pdf, doc, docx, ods, xlsx, jpg, jpeg, png" in e.detail


def test_text_named_pdf_keeps_its_old_refusal():
    e = refused("a.pdf", b"just text, not a pdf", "TYPE_MISMATCH")
    assert e.detail == "Rozszerzenie .pdf, a zawartość to plik tekstowy."


@pytest.mark.parametrize("data,kind", [(fx.docx(), "docx"), (RTF, "rtf")])
def test_doc_holding_docx_or_rtf_is_read_by_content_with_the_warning(data, kind):
    info = inspect_upload("formularz.doc", data, S)
    assert info.kind == kind and "nie zgadza się z zawartością" in info.warnings[0]


@pytest.mark.parametrize("name", ["a.jpg", "a.jpeg", "a.jpe", "A.JPG"])
def test_jpg_jpeg_jpe_are_one_kind(name):
    assert inspect_upload(name, fx.jpeg(), S).kind == "jpeg"


@pytest.mark.parametrize("name,data,kind", [
    ("a.pdf", fx.png(), "png"), ("a.xlsx", fx.docx(), "docx"), ("a.pdf", RTF, "rtf"), ("wniosek", fx.pdf(), "pdf"),
])
def test_strict_off_keeps_reading_by_content(name, data, kind):
    info = inspect_upload(name, data, LOOSE)
    assert info.kind == kind and info.warnings


def test_http_answers_415_problem_in_polish_and_docx_as_doc_200():
    c = TestClient(create_app(Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false"})))
    for name, data in (("a.pdf", fx.png()), ("a.xlsx", fx.docx()), ("a.pdf", RTF), ("bez", fx.pdf())):
        r = post(c, name, data)
        assert r.status_code == 415, (name, r.status_code, r.text[:200])
        assert r.headers["content-type"].startswith("application/problem+json")
    for name, data in (("a.doc", fx.docx()), ("a.doc", RTF)):
        r = post(c, name, data)
        assert r.status_code == 200, (name, r.status_code, r.text[:300])
