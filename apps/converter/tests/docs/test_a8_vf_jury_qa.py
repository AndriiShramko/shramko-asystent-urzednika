"""The answers of docs/05-hackathon/jury-qa-formularze.md say only what the code does today (audit 8, VF).

Each test pairs one promise of the Polish answers with the code or a run of the pipeline: when the promise is in
the document, the code must keep it. A juror can check each of these in two minutes, so a promise without code
is a defect of the document, not of the code.
"""
from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path

import pytest

from app import pipeline
from app.config import Settings
from app.gate.journeys import load_journeys

ROOT = Path(__file__).resolve().parents[4]
DOC = ROOT / "docs" / "05-hackathon" / "jury-qa-formularze.md"
APP = ROOT / "apps" / "converter" / "app"
SETTINGS = Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false"})
NUMBERS = {"dwie": 2, "trzy": 3, "cztery": 4, "pięć": 5, "sześć": 6, "siedem": 7, "osiem": 8, "dziewięć": 9}


def text() -> str:
    return DOC.read_text(encoding="utf-8")


def answer(q: str) -> str:
    """The section of one question ("1" .. "15", "R1" ..), from its heading to the next heading."""
    m = re.search(rf"^### {re.escape(q)}\.(.*?)(?=^### |^## |\Z)", text(), re.S | re.M)
    assert m, f"question {q} not found"
    return m.group(1)


def app_sources(skip: tuple[str, ...] = ()) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in APP.rglob("*.py") if p.name not in skip)


def docx(title: str) -> bytes:
    ns = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'

    def para(t: str) -> str:
        return f'<w:p><w:r><w:t xml:space="preserve">{t}</w:t></w:r></w:p>'

    body = para("Załącznik nr 2") + para("") + para(title) + para("Imię i nazwisko") + para("Adres zamieszkania")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/'
                   'content-types"><Default Extension="xml" ContentType="application/xml"/><Override '
                   'PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.'
                   'wordprocessingml.document.main+xml"/></Types>')
        z.writestr("word/document.xml",
                   f'<?xml version="1.0" encoding="UTF-8"?><w:document {ns}><w:body>{body}</w:body></w:document>')
    return buf.getvalue()


def ids(form: dict) -> set[str]:
    out: set[str] = set()

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("id"), str) and o.get("type"):
                out.add(o["id"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(form["tabs"])
    return out


def test_q1_says_only_the_first_four_checks_block():
    """pipeline.py: only G1 to G4 refuse a result; G5 to G10 become warnings of a 200, G11 and G12 do not run."""
    if "Każdy plik przechodzi naszą kontrolę" in answer("1"):
        assert pipeline.BLOCKING_CHECKS == {f"G{i}" for i in range(1, 13)}, \
            "Q1 says every file passes our gate, but only G1-G4 block a result"


def test_q3_names_the_number_of_journeys_the_gate_has():
    m = re.search(r"(\w+) odtwarzanych ścieżek", answer("3"))
    if m and m.group(1).lower() in NUMBERS:
        assert NUMBERS[m.group(1).lower()] == len(load_journeys()), \
            f"Q3 says {m.group(1)} journeys, the gate has {len(load_journeys())}"


def test_q9_promises_no_worker_process_the_code_does_not_have():
    if re.search(r"osobny,? krótko żyjący proces", answer("9")):
        src = (APP / "pipeline.py").read_text(encoding="utf-8")
        assert "threading.Thread" not in src, "Q9 promises a separate process; run_limited uses a daemon thread"


def test_q10_gives_measurements_only_when_the_file_exists():
    if "Mierzymy osobno" in answer("10"):
        assert (ROOT / "eval" / "metrics.json").is_file(), "Q10 says we measure; eval/metrics.json does not exist"


def test_q13_promises_no_libreoffice_the_images_do_not_install():
    a = answer("13")
    if re.search(r"LibreOffice.{0,40}(jest|będzie) .{0,40}obrazie", a):
        docker = (ROOT / "apps" / "converter" / "Dockerfile").read_text(encoding="utf-8").lower()
        assert "libreoffice" in docker or "soffice" in docker, "Q13 promises LibreOffice in an image; no stage installs it"


def test_q14_promises_no_second_ocr_engine_and_no_scan_crop():
    a = answer("14")
    if "drugi, niezależny silnik OCR" in a:
        assert re.search(r"\.ocr_second_engine\b", app_sources(skip=("config.py",))), \
            "Q14 promises a second OCR engine; OCR_SECOND_ENGINE is read by nothing"
    if "wycinkiem skanu" in a:
        ui = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "apps" / "review-web" / "src").rglob("*.ts"))
        assert re.search(r"crop|drawImage", ui), "Q14 promises a crop of the scan; the review screen draws none"


def test_q15_ids_follow_the_title_so_the_answer_must_say_so():
    """The form key is the slug of the title (compose/__init__.py), so a new title gives new ids everywhere."""
    a = pipeline.run(docx("Wniosek o dopłatę do czynszu"), "a.docx", SETTINGS).form
    b = pipeline.run(docx("Wniosek o dopłatę do czynszu za lokal"), "a.docx", SETTINGS).form
    shared = ids(a) & ids(b)
    if not shared and "zmiana jednego zdania nie zmienia" in answer("15"):
        assert "tytuł" in answer("15").split("True only if")[0], \
            "Q15 says one changed sentence keeps the ids; a changed title changes every id"


def test_q15_promises_no_comparison_of_versions_that_does_not_exist():
    if "dają listę zmian" in answer("15").split("True only if")[0]:
        main = (APP / "main.py").read_text(encoding="utf-8") + (APP / "cli.py").read_text(encoding="utf-8")
        assert "diff" in main, "Q15 promises a list of changes; there is no diff route and no diff command"


def test_r1_promises_no_filled_form_alarm_and_no_memory_only_file():
    a = answer("R1")
    if "Rozpoznajemy wypełnienie" in a:
        assert "FILLED_FORM" in app_sources(skip=("common.py",)), "R1 promises an alarm; FILLED_FORM is never emitted"
    if "Plik żyje tylko w pamięci" in a:
        docker = (ROOT / "apps" / "converter" / "Dockerfile").read_text(encoding="utf-8")
        assert "OCR writes temporary files to /tmp" not in docker, "R1 says memory only; OCR writes files to /tmp"


@pytest.mark.sets
def test_q7_tables_become_repeating_sections_only_if_set_8_has_one():
    from tools.coi_paths import sets
    if not re.search(r"(?<!nie )zamieniamy na sekcje powtarzalne", answer("7")):
        return
    folder = next(p for p in sets("judged") if p.name.startswith("judged-08"))
    pdf = next(folder.glob("*.pdf"))
    form = pipeline.run(pdf.read_bytes(), "a.pdf", SETTINGS).form
    assert '"REPEATING_SECTION"' in json.dumps(form), "Q7 says tables become repeating sections; set 8 has none"
