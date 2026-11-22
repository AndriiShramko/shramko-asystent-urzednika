"""BL13 DATE-D: our form against the partner's own export of the same paper, and the paper-only places named.

The partner's exports of its two reference papers have no date of filing and no signature (decision D10: the
e-service signs after the preview), so those places are left out of the form and named in the sidecar as an
INPUT_NOTE with an `applied` fix (rule `paper_only.*`). A content date the partner has (DATEPICKER, or a text field
that means a date) must never be missing; the recall of the partner's fields must not drop below the value measured
on 2026-11-22 (commit of this test): reference 01 47/49 (PDF, DOC, DOCX, ODS, XLSX), reference 05 46/51 (PDF, DOC,
DOCX, ODS). The images are slower and lower (01: 43/49, 05: 43/51) and are held at those values.
"""
from __future__ import annotations

import io
import json

import pytest

from app import pipeline
from app.config import Settings
from refcheck import compare, leaves, norm

SETTINGS = Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false"})

# reference set -> {suffix: minimum number of the partner's fields found}; measured, see the module text
FLOOR = {
    "reference-01-numer-porzadkowy": ({".pdf": 47, ".docx": 47, ".doc": 47, ".ods": 47, ".xlsx": 47, ".jpg": 43}, 49),
    "reference-05-nadplata-podatku": ({".pdf": 46, ".docx": 46, ".doc": 46, ".ods": 46}, 51),
}


def _form(*fields: tuple[str, str, str]) -> dict:
    """A partner-shaped form: one tab per distinct section, one section each."""
    tabs: dict[str, list] = {}
    for sec, typ, title in fields:
        tabs.setdefault(sec, []).append({"field": {"type": typ, "title": title}})
    return {"tabs": [{"title": s, "questions": [{"field": {"type": "SECTION", "title": s, "repeatingSectionGrid": qs}}]}
                     for s, qs in tabs.items()]}


def _notes(sidecar: dict) -> list[dict]:
    return [w for w in sidecar["warnings"] if (w.get("fix") or {}).get("rule", "").startswith("paper_only.")]


# -- synthetic: run everywhere ------------------------------------------------------------------------------------


def test_labels_fold_case_letters_and_synonyms() -> None:
    assert norm("Nazwa organu") == norm("nazwa URZĘDU") == "nazwa urzedu"
    assert norm("Informacje o budynku") == "szczegoly sprawy"
    assert norm("<b>Numer  telefonu:</b>") == "numer telefonu"


def test_recall_is_tolerant_to_order_and_section_and_reports_type_and_extra() -> None:
    partner = _form(("Adresat", "TEXT_FIELD", "Nazwa urzędu"), ("Sprawa", "DATEPICKER", "Data zdarzenia"),
                    ("Sprawa", "TEXT_FIELD", "Obręb"), ("Opłata", "FILE_UPLOADER", "Potwierdzenie przelewu"))
    ours = _form(("Szczegóły sprawy", "TEXT_FIELD", "Obręb"), ("Szczegóły sprawy", "TEXT_FIELD", "Data zdarzenia"),
                 ("Adresat", "TEXT_FIELD", "Nazwa organu"), ("Opłata", "FILE_UPLOADER", "Plik z przelewem"),
                 ("Szczegóły sprawy", "TEXT_FIELD", "Uwagi"))
    m = compare(partner, ours)
    assert (len(m.found), m.partner, m.ours) == (4, 4, 5)
    assert m.recall == 1.0 and m.type_agree == 3            # the date is found but typed TEXT_FIELD: reported
    assert [x.label for x in m.extra] == ["uwagi"]
    assert not m.missing_dates


def test_a_missing_partner_date_is_caught() -> None:
    partner = _form(("Sprawa", "DATEPICKER", "Data urodzenia psa"), ("Sprawa", "TEXT_FIELD", "Termin realizacji"),
                    ("Sprawa", "TEXT_FIELD", "Rasa"))
    m = compare(partner, _form(("Sprawa", "TEXT_FIELD", "Rasa")))
    assert m.recall == pytest.approx(1 / 3)
    assert sorted(x.label for x in m.missing_dates) == ["data urodzenia psa", "termin realizacji"]


def _paper() -> bytes:
    """A request with a filing date at the top right and a signature at the bottom, like reference 01."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, invariant=1)
    c.setFont("Helvetica", 10)
    c.drawString(400, 800, "................................")
    c.drawString(430, 788, "(data)")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(140, 740, "WNIOSEK O WYDANIE ZASWIADCZENIA TESTOWEGO")
    c.setFont("Helvetica", 10)
    c.drawString(56, 690, "Numer ewidencyjny dzialki ..........................................")
    c.drawString(56, 670, "Cel wydania zaswiadczenia ..........................................")
    c.drawString(360, 560, "......................................................")
    c.drawString(380, 548, "(podpis wnioskodawcy)")
    c.save()
    return buf.getvalue()


def test_paper_only_places_are_named_in_the_sidecar_and_not_in_the_form() -> None:
    r = pipeline.run(_paper(), "x.pdf", SETTINGS)
    labels = [leaf.label for leaf in leaves(r.form)]
    assert not any(lab in ("data", "podpis wnioskodawcy", "podpis") for lab in labels)
    notes = _notes(r.sidecar)
    rules = sorted(n["fix"]["rule"] for n in notes)
    assert rules == ["paper_only.signature_and_date", "paper_only.signature_and_date"], json.dumps(notes)[:400]
    for n in notes:
        assert n["code"] == "INPUT_NOTE" and n["fix"]["kind"] == "applied"
        assert n["fix"]["text"] == "Podpis i datę złożenia dodaje e-usługa przy wysyłce."
        src = n["fix"]["source"]
        assert src["type"] == "paper" and src["page"] == 1 and len(src["box"]) == 4 and src["quote"]
    assert {n["fix"]["source"]["quote"].strip("()").casefold() for n in notes} >= {"data"}


# -- the partner's sets: local only ---------------------------------------------------------------------------------


def _refs():
    from tools.coi_paths import sets

    for folder in sets("reference"):
        floors, total = FLOOR.get(folder.name, ({}, 0))
        partner = next(folder.glob("*.json"), None)
        for p in sorted(folder.iterdir()):
            if p.suffix.lower() in floors and "wizualizacja" not in p.name and "(1)" not in p.name:
                yield pytest.param(p, partner, floors[p.suffix.lower()], total, id=f"{folder.name[:12]}{p.suffix.lower()}")


@pytest.mark.sets
@pytest.mark.parametrize("paper,partner,floor,total", list(_refs()) or [pytest.param(None, None, 0, 0, id="absent")])
def test_reference_recall_does_not_drop_and_no_partner_date_is_missing(paper, partner, floor, total) -> None:
    if paper is None:
        pytest.skip("the reference sets are not on this machine")
    theirs = json.loads(partner.read_text(encoding="utf-8"))
    r = pipeline.run(paper.read_bytes(), "x" + paper.suffix.lower(), SETTINGS)
    m = compare(theirs, r.form)
    report = "\n".join(m.lines())
    assert m.partner == total, report
    assert len(m.found) >= floor, report
    assert not m.missing_dates, report


@pytest.mark.sets
def test_reference_01_names_its_filing_date_and_signature() -> None:
    from tools.coi_paths import sets

    folder = next((f for f in sets("reference") if f.name.startswith("reference-01")), None)
    if folder is None:
        pytest.skip("the reference sets are not on this machine")
    paper = next(p for p in folder.iterdir() if p.suffix.lower() == ".pdf")
    notes = _notes(pipeline.run(paper.read_bytes(), "x.pdf", SETTINGS).sidecar)
    quotes = " | ".join(n["fix"]["source"]["quote"].casefold() for n in notes)
    assert "data" in quotes and "podpis wnioskodawcy" in quotes, quotes


@pytest.mark.sets
def test_judged_dates_and_declarant_fields_stay() -> None:
    """jud08 PDF: the first circumstance's date (a DD-MM | RRRR comb pair whose words a choice option holds);
    jud09 sheets: "Ja niżej podpisany" is the declarant's name, not a signature."""
    from tools.coi_paths import sets

    by = {f.name[:9]: f for f in sets("judged")}
    if "judged-08" not in by or "judged-09" not in by:
        pytest.skip("the judged sets are not on this machine")
    p8 = next(p for p in by["judged-08"].iterdir() if p.suffix.lower() == ".pdf")
    f8 = leaves(pipeline.run(p8.read_bytes(), "x.pdf", SETTINGS).form)
    assert any(x.type == "DATEPICKER" and x.label.startswith("data zdarzenia powodujacego powstanie") for x in f8)
    p9 = next(p for p in by["judged-09"].iterdir() if p.suffix.lower() == ".xlsx")
    f9 = leaves(pipeline.run(p9.read_bytes(), "x.xlsx", SETTINGS).form)
    assert sum(1 for x in f9 if "nizej podpisany" in x.label) >= 3
