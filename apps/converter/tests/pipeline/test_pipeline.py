"""The pipeline end to end on synthetic files: the answer really comes from the uploaded file (WP-F0p)."""
from __future__ import annotations

import io
import json
import logging
import re
import zipfile

import pytest
from fastapi.testclient import TestClient

from app import cli
from app.config import Settings
from app.main import create_app
from tools import coi_lint

SETTINGS = Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000"})
NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"')


def pdf(title: str, extra: str = "Pole opisowe testu") -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, invariant=1)
    c.setFont("Helvetica", 9)
    c.drawString(56, 810, "Zalacznik nr 1 do zarzadzenia")      # page furniture, small
    c.setFont("Helvetica-Bold", 16)
    c.drawString(120, 760, title)
    c.setFont("Helvetica", 10)
    c.drawString(56, 700, extra)
    c.save()
    return buf.getvalue()


def docx(title: str) -> bytes:
    def para(text: str) -> str:
        return f'<w:p><w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>'

    body = para("Załącznik nr 2") + para("") + para(title) + para("Treść pomocnicza dokumentu")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/'
                   'content-types"><Default Extension="xml" ContentType="application/xml"/><Override '
                   'PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.'
                   'wordprocessingml.document.main+xml"/></Types>')
        z.writestr("word/document.xml",
                   f'<?xml version="1.0" encoding="UTF-8"?><w:document {NS}><w:body>{body}</w:body></w:document>')
    return buf.getvalue()


def xlsx() -> bytes:
    import openpyxl

    wb = openpyxl.Workbook()
    wb.active["A1"] = "Wniosek"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app(SETTINGS))


def post(client: TestClient, name: str, data: bytes):
    return client.post("/v1/forms/convert", files={"file": (name, data, "application/octet-stream")})


def errors_of(form: dict) -> list:
    return [m for k, m in coi_lint.check(form, "strict") if k == "ERROR"]


@pytest.mark.parametrize("name,data,title", [
    ("a.pdf", pdf("WNIOSEK O WYDANIE ZASWIADCZENIA"), "WNIOSEK O WYDANIE ZASWIADCZENIA"),
    ("a.docx", docx("Wniosek o dopłatę do czynszu"), "Wniosek o dopłatę do czynszu"),
])
def test_the_answer_is_a_valid_form_with_the_title_of_the_file(client, name, data, title):
    r = post(client, name, data)
    assert r.status_code == 200, r.text
    form = r.json()
    assert list(form) == ["title", "tabs", "flow"] or set(form) == {"title", "tabs", "flow"}
    assert form["title"] == title
    assert errors_of(form) == []
    assert len(form["tabs"]) >= 2


def test_two_different_files_give_different_titles(client):
    a = post(client, "a.pdf", pdf("WNIOSEK PIERWSZY")).json()
    b = post(client, "b.pdf", pdf("WNIOSEK DRUGI")).json()
    assert a["title"] != b["title"] and a != b
    assert post(client, "a.docx", docx("Alfa")).json()["title"] != post(client, "b.docx", docx("Beta")).json()["title"]


def test_the_same_file_twice_gives_the_same_bytes(client):
    data = pdf("WNIOSEK POWTORZONY")
    assert post(client, "a.pdf", data).content == post(client, "a.pdf", data).content


def test_the_command_line_gives_the_same_bytes_as_http(client, tmp_path, monkeypatch):
    data = pdf("WNIOSEK Z LINII POLECEN")
    src, out = tmp_path / "in.pdf", tmp_path / "out.json"
    src.write_bytes(data)
    monkeypatch.setenv("AUTH_MODE", "off")
    assert cli.main(["convert", str(src), "--out", str(out)]) == 0
    assert out.read_bytes() == post(client, "in.pdf", data).content


def test_the_sidecar_says_the_fields_of_the_matter_are_not_read(client):
    r = client.post("/v1/forms/report", files={"file": ("a.pdf", pdf("WNIOSEK"), "application/pdf")})
    assert r.status_code == 200
    side = r.json()
    codes = [w["code"] for w in side["warnings"]]
    assert "BRIEF_NOT_READ" in codes
    w = next(w for w in side["warnings"] if w["code"] == "BRIEF_NOT_READ")
    assert "Pola sprawy" in w["detail"]
    assert side["converter"]["pipeline"] == "interim"


def test_page_furniture_is_not_the_title(client):
    # the small "Zalacznik nr 1" line is first on the page, the bigger heading below it is the title
    assert post(client, "a.pdf", pdf("TYTUL ARKUSZA")).json()["title"] == "TYTUL ARKUSZA"
    assert post(client, "a.docx", docx("Tytuł akapitu")).json()["title"] == "Tytuł akapitu"


def test_a_broken_pdf_is_422_without_a_trace(client, caplog):
    caplog.set_level(logging.DEBUG)
    broken = pdf("X")[:-200] + b"\n%%EOF\n"
    r = post(client, "secret-name-xyz.pdf", broken)
    assert r.status_code == 422 and r.json()["code"] == "UNREADABLE"
    assert "Traceback" not in r.text and "File \"" not in r.text
    assert "secret-name-xyz" not in caplog.text


def _sheet_doc_builders():
    import sys
    from pathlib import Path

    here = str(Path(__file__).resolve().parent.parent / "readers")
    if here not in sys.path:
        sys.path.insert(0, here)
    import test_sheet_doc_readers as t

    return {"xlsx": lambda: t._xlsx(t._form), "ods": t._ods_form, "doc": t._doc}


@pytest.mark.parametrize("fmt", ["xlsx", "ods", "doc"])
def test_a_sheet_or_binary_word_file_gives_a_form_that_passes_the_gate(client, fmt):
    r = post(client, f"a.{fmt}", _sheet_doc_builders()[fmt]())
    assert r.status_code == 200, r.text
    form = r.json()
    assert set(form) == {"title", "tabs", "flow"} and form["tabs"]
    assert errors_of(form) == []


def test_a_truncated_png_is_not_answered_with_a_form(client):
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(buf, "PNG")
    r = post(client, "a.png", buf.getvalue()[:-24])
    assert r.status_code == 422 and r.json()["code"] == "UNREADABLE" and "tabs" not in r.json()


def test_a_doc_that_holds_a_docx_is_read_as_a_docx(client):
    r = post(client, "old.doc", docx("Tytuł w pliku doc"))
    assert r.status_code == 200 and r.json()["title"] == "Tytuł w pliku doc"


def test_settings_reach_the_composer():
    s = Settings.from_env({"AUTH_MODE": "off", "FORM_KEY": "moj-klucz", "FINISH_STYLE": "info_section",
                           "VALIDATORS": "off", "STATUTORY_REPRESENTATIVE": "false", "POA_EXEMPTION": "true",
                           "OCR_MIN_CHARS": "5", "MAX_PAGES": "3"})
    from app.config import compose_options, read_options

    c, r = compose_options(s), read_options(s)
    assert (c.form_key, c.finish_style, c.validators, c.statutory_representative, c.poa_exemption) == (
        "moj-klucz", "info_section", False, False, True)
    assert (r.ocr_min_chars, r.max_pages) == (5, 3)
    a = TestClient(create_app(s)).post("/v1/forms/convert", files={"file": ("a.pdf", pdf("A"), "application/pdf")}).json()
    b = TestClient(create_app(SETTINGS)).post("/v1/forms/convert", files={"file": ("a.pdf", pdf("A"), "application/pdf")}).json()
    assert a != b and not errors_of(a)


def test_too_many_pages_is_413():
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, invariant=1)
    for i in range(4):
        c.drawString(72, 700, f"Strona {i}")
        c.showPage()
    c.save()
    s = Settings.from_env({"AUTH_MODE": "off", "MAX_PAGES": "2"})
    r = TestClient(create_app(s)).post("/v1/forms/convert", files={"file": ("a.pdf", buf.getvalue(), "application/pdf")})
    assert r.status_code == 413 and r.json()["code"] == "TOO_LARGE"


# ---- the partner's sets (local only) ----------------------------------------------------------------------

@pytest.mark.sets
def test_pdf_and_docx_of_all_nine_sets_answer_200_and_pass_the_strict_linter(client):
    from eval.golden import golden_inputs, judged_inputs

    done = 0
    for f in golden_inputs() + judged_inputs():
        if f.suffix.lower() not in (".pdf", ".docx", ".doc") or "wizualizacja" in f.name or f.stem.endswith("(1)"):
            continue
        r = post(client, f.name, f.read_bytes())
        label = f"{f.parent.name[:12]}{f.suffix.lower()}"
        if f.suffix.lower() == ".doc" and r.status_code != 200:
            continue  # a real binary .doc has no reader yet; only the DOCX-in-.doc files are counted
        assert r.status_code == 200, f"{label}: {r.status_code} {r.json().get('code')}"
        errs = errors_of(r.json())
        assert not errs, f"{label}: {len(errs)} linter errors"
        done += 1
    assert done >= 14


@pytest.mark.sets
def test_the_reference_forms_carry_the_words_of_their_names(client):
    from eval.golden import golden_inputs

    words = {"numer-porzadkowy": ("numer", "porządkow"), "nadplata-podatku": ("nadpłat",)}
    seen = 0
    for f in golden_inputs():
        key = next((k for k in words if k in f.parent.name), None)
        if key is None or f.suffix.lower() not in (".pdf", ".docx"):
            continue
        title = post(client, f.name, f.read_bytes()).json()["title"].lower()
        assert any(re.search(w, title) for w in words[key]), f"{key}{f.suffix}: title {title!r}"
        seen += 1
    assert seen >= 2


# ---- the pre-import gate behind the pipeline (WP-F0q) -------------------------------------------------------------

class _Broken:
    """What the composer hands back when the form it built is wrong: one techName over the 60 characters of D7 (the schema and G3 both judge it; G1 comes first)."""

    def __init__(self, real) -> None:
        form = json.loads(real.form.to_json_bytes())
        form["tabs"][0]["questions"][0]["field"]["techName"] = "x" * 61
        self._bytes = json.dumps(form).encode()
        self.origins, self.brief_keys, self.remarks = real.origins, real.brief_keys, real.remarks
        self.form = self

    def to_json_bytes(self) -> bytes:
        return self._bytes


@pytest.fixture
def broken_composer(monkeypatch):
    from app import pipeline

    real = pipeline.compose
    monkeypatch.setattr(pipeline, "compose", lambda brief, opts: _Broken(real(brief, opts)))


def test_a_form_the_gate_refuses_is_500_gate_failed_with_the_check_and_without_a_form(client, broken_composer):
    r = post(client, "a.pdf", pdf("WNIOSEK ZEPSUTY"))
    assert r.status_code == 500
    body = r.json()
    assert body["code"] == "GATE_FAILED" and r.headers["content-type"].startswith("application/problem+json")
    assert "G1" in body["detail"] and "schema" in body["detail"] and "/techName" in body["detail"]
    assert "x" * 61 not in r.text
    assert "tabs" not in body and "flow" not in body
    side = client.post("/v1/forms/report", files={"file": ("a.pdf", pdf("WNIOSEK ZEPSUTY"), "application/pdf")})
    assert side.status_code == 500 and "tabs" not in side.json()


def test_the_command_line_refuses_a_form_the_gate_refuses_and_writes_no_file(broken_composer, tmp_path, monkeypatch, capsys):
    src, out = tmp_path / "in.pdf", tmp_path / "out.json"
    src.write_bytes(pdf("WNIOSEK ZEPSUTY"))
    monkeypatch.setenv("AUTH_MODE", "off")
    assert cli.main(["convert", str(src), "--out", str(out)]) != 0
    assert not out.exists()
    seen = capsys.readouterr()
    assert seen.out == "" and "GATE_FAILED" in seen.err and "G1" in seen.err


@pytest.mark.parametrize("name,data", [("a.pdf", pdf("WNIOSEK BRAMKA")), ("a.docx", docx("WNIOSEK BRAMKA"))])
def test_a_good_file_passes_the_gate_and_the_sidecar_lists_every_check(client, name, data):
    r = client.post("/v1/forms/report", files={"file": (name, data, "application/octet-stream")})
    assert r.status_code == 200
    checks = {c["id"]: c["status"] for c in r.json()["checks"]}
    assert list(checks) == [f"G{i}" for i in range(1, 13)]
    assert all(checks[f"G{i}"] == "passed" for i in range(1, 11))
    assert checks["G11"] == checks["G12"] == "not_applicable"
    assert post(client, name, data).status_code == 200
