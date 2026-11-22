"""A10 STRICT: by default the service accepts exactly the eight formats of the task card ("wyłącznie obsługiwane
formaty": PDF, DOC, DOCX, ODS, XLSX, JPG, JPEG, PNG); the other formats this build reads stay behind one switch,
STRICT_EXTENSIONS=false, and then work as before. Every file is built here from code."""
from __future__ import annotations

from pathlib import Path

import factory as fx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.guard import ProblemError, inspect_upload
from app.guard.checks import CARD_EXTENSIONS, EXTENSIONS, accepted_extensions
from app.main import create_app

CARD = ("pdf", "doc", "docx", "ods", "xlsx", "jpg", "jpeg", "png")
EXTRA = ("odt", "xls", "rtf", "txt", "tif", "tiff", "bmp", "gif", "webp", "heic", "heif")
RTF = b"{\\rtf1\\ansi\\ansicpg1250 \\pard Wniosek o wydanie zezwolenia\\par \\pard Imi\\'ea i nazwisko: ..........\\par}"
TXT = "Wniosek o wydanie zezwolenia\nImię i nazwisko: ..........\n".encode("utf-8")


def client(**env) -> TestClient:
    return TestClient(create_app(Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false", **env})))


def post(c: TestClient, name: str, data: bytes):
    body, ctype = fx.multipart([("file", name, data, "application/octet-stream")])
    return c.post("/v1/forms/convert", content=body, headers={"Content-Type": ctype})


def test_the_default_is_exactly_the_eight_formats_of_the_card(tmp_path: Path):
    s = Settings.from_env({"AUTH_MODE": "off"})
    assert s.strict_extensions is True and Settings().strict_extensions is True
    assert accepted_extensions(s.strict_extensions) == CARD == CARD_EXTENSIONS
    assert set(EXTENSIONS) - set(CARD) == set(EXTRA)   # nothing the build reads is lost, it only waits for the switch


@pytest.mark.parametrize("name,data,kind", [
    ("a.pdf", fx.pdf(), "pdf"), ("A.PDF", fx.pdf(), "pdf"), ("a.docx", fx.docx(), "docx"), ("A.DOCX", fx.docx(), "docx"),
    ("a.xlsx", fx.xlsx(), "xlsx"), ("a.XlSx", fx.xlsx(), "xlsx"), ("a.ods", fx.ods(), "ods"), ("A.ODS", fx.ods(), "ods"),
    ("a.png", fx.png(), "png"), ("A.PNG", fx.png(), "png"), ("a.jpg", fx.jpeg(), "jpeg"), ("A.JPG", fx.jpeg(), "jpeg"),
    ("a.jpeg", fx.jpeg(), "jpeg"), ("A.JPEG", fx.jpeg(), "jpeg"), ("a.doc", fx.doc(), "doc"), ("A.DOC", fx.doc(), "doc"),
    ("A.JPE", fx.jpeg(), "jpeg"),   # the partner's judged set 7 ships a .JPE: a JPEG by its content, kept
])
def test_the_eight_are_accepted_in_any_case(name, data, kind):
    assert inspect_upload(name, data, Settings(auth_mode="off")).kind == kind


@pytest.mark.parametrize("ext", EXTRA + ("RTF", "Odt", "TIFF"))
def test_an_extra_format_is_refused_by_default_with_the_accepted_list(ext):
    with pytest.raises(ProblemError) as e:
        inspect_upload(f"wniosek.{ext}", RTF, Settings(auth_mode="off"))
    assert e.value.code == "EXTENSION"
    assert str(e.value).endswith("Obsługiwane rozszerzenia: pdf, doc, docx, ods, xlsx, jpg, jpeg, png.")


@pytest.mark.parametrize("name,data", [("wniosek.rtf", RTF), ("wniosek.txt", TXT), ("skan.tif", fx.png()),
                                       ("skan.gif", fx.png())])
def test_http_answers_the_services_own_clean_415_in_polish(name, data):
    r = post(client(), name, data)
    assert r.status_code == 415 and r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    assert body["code"] == "EXTENSION" and body["status"] == 415
    assert "Obsługiwane rozszerzenia: pdf, doc, docx, ods, xlsx, jpg, jpeg, png." in body["detail"]
    assert "Traceback" not in r.text


def test_status_lists_exactly_what_is_accepted():
    assert client().get("/status").json()["formats"] == list(CARD)
    assert client(STRICT_EXTENSIONS="false").get("/status").json()["formats"] == list(EXTENSIONS)


def test_with_the_switch_off_the_extra_formats_work_as_before():
    loose = Settings.from_env({"AUTH_MODE": "off", "STRICT_EXTENSIONS": "false"})
    assert loose.strict_extensions is False and accepted_extensions(False) == EXTENSIONS
    assert inspect_upload("wniosek.rtf", RTF, loose).kind == "rtf"
    assert inspect_upload("WNIOSEK.TXT", TXT, loose).kind == "txt"
    assert inspect_upload("skan.tiff", fx.png(), loose).kind == "png"   # read as the kind its content is, as before
    c = client(STRICT_EXTENSIONS="false")
    for name, data in (("wniosek.rtf", RTF), ("wniosek.txt", TXT)):
        r = post(c, name, data)
        assert r.status_code == 200, (name, r.status_code, r.text[:300])
        assert r.json()["tabs"]
    assert post(c, "a.exe", fx.pdf()).status_code == 415   # the switch opens the readable formats, not anything


def test_a_doc_holding_rtf_is_still_read_by_default():
    # the partner's sets hold .doc files whose content is RTF or DOCX: the extension is one of the eight, so it stays
    assert inspect_upload("stary.doc", RTF, Settings(auth_mode="off")).kind == "rtf"
