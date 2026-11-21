"""WP-F4 integration: finder + understanding in the service pipeline (sidecar pipeline 'brief', closed ledger)."""
from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from app import pipeline
from app.config import Settings
from app.main import create_app
from tools import coi_lint

SETTINGS = Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000"})


def matter_pdf() -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, invariant=1)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(120, 780, "WNIOSEK O WYNAJEM SWIETLICY")
    c.setFont("Helvetica", 11)
    y = 720
    for label in ("Termin wynajmu", "Cel wynajmu", "Liczba osob"):
        c.drawString(56, y, label + " ")
        c.drawString(56 + c.stringWidth(label + " ", "Helvetica", 11), y, "." * 60)
        y -= 28
    c.save()
    return buf.getvalue()


def test_a_paper_with_blanks_goes_through_finder_and_understanding():
    r = pipeline.run(matter_pdf(), "a.pdf", SETTINGS)
    side = r.sidecar
    assert side["converter"]["pipeline"] == "brief"
    codes = {w["code"] for w in side["warnings"]}
    assert "BRIEF_NOT_READ" not in codes
    ledger = side["meta"]["ledger"]
    assert ledger["blanks_found"] == len(ledger["rows"]) >= 3
    assert ledger["became_field"] >= 3
    assert [m for k, m in coi_lint.check(r.form, "strict") if k == "ERROR"] == []


def test_a_paper_without_blanks_falls_back_to_the_interim_brief_with_a_warning():
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, invariant=1)
    c.drawString(100, 700, "Tylko tekst bez pol")
    c.save()
    r = pipeline.run(buf.getvalue(), "a.pdf", SETTINGS)
    assert r.sidecar["converter"]["pipeline"] == "interim"
    assert "BRIEF_NOT_READ" in {w["code"] for w in r.sidecar["warnings"]}


def test_the_http_answer_is_the_partner_object_only():
    client = TestClient(create_app(SETTINGS))
    r = client.post("/v1/forms/convert", files={"file": ("a.pdf", matter_pdf(), "application/pdf")})
    assert r.status_code == 200 and "ledger" not in r.text


@pytest.mark.sets
def test_every_judged_set_converts_with_fields_of_the_matter_and_no_linter_error():
    from tools.coi_paths import sets

    done = 0
    for folder in sets("judged"):
        for f in sorted(folder.iterdir()):
            if f.suffix.lower() not in (".pdf", ".docx"):
                continue
            res = pipeline.run(f.read_bytes(), f.name, SETTINGS)
            assert res.sidecar["converter"]["pipeline"] == "brief", folder.name
            assert [m for k, m in coi_lint.check(res.form, "strict") if k == "ERROR"] == [], folder.name
            assert res.sidecar["meta"]["ledger"]["blanks_found"] > 0, folder.name
            done += 1
    assert done >= 7
