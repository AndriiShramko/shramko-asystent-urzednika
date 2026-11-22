"""W11 CLERK-S: when the paper has no addressee block the whole paper is searched for the office (one found: stated;
several: ambiguous with the most likely first); a page read by OCR gives single words, which are joined into lines
first; the clause printed on the paper is kept as paragraphs for the consent. Invented offices and places only."""
from __future__ import annotations

from app.mean import understand
from app.model.candidate import Candidate, Confidence, FinderOutput, Label
from app.model.common import InputRef
from app.model.page import Page, PageModel, Run, Source
from tests.mean.test_mean_core import STRICT, Paper


def _paper() -> Paper:
    p = Paper()
    p.text("WNIOSEK O WPIS", bold=True)
    s = p.heading("Dane sprawy", number="1")
    p.blank("Cel wpisu", section=s)
    return p


def test_block_on_the_paper_is_read_as_before_and_names_no_candidates() -> None:
    p = Paper()
    p.text("Urząd Gminy Wzorcowo")
    p.text("WNIOSEK O WPIS", bold=True)
    p.blank("Cel wpisu", section=p.heading("Dane sprawy", number="1"))
    a = p.brief().addressee
    assert (a.status, a.name, a.candidates) == ("stated", "Urząd Gminy Wzorcowo", [])


def test_one_office_named_only_in_the_clause_is_the_addressee() -> None:
    p = _paper()
    p.text("Klauzula informacyjna", role="clause")
    p.text("1. Administratorem Pani/Pana danych osobowych jest Burmistrz Miasta Przykładowa z siedzibą przy ul. Lipowej 1.", role="clause")
    p.text("2. Skargę wnosi się do Prezesa Urzędu Ochrony Danych Osobowych.", role="clause")
    b = p.brief()
    a = b.addressee
    assert (a.status, a.kind, a.name) == ("stated", "body", "Burmistrz Miasta Przykładowa")
    assert len(a.candidates) == 1 and "Administratorem" in (a.candidates[0].evidence.quote or "")


def test_two_different_offices_are_ambiguous_and_the_controller_of_the_data_comes_first() -> None:
    p = _paper()
    p.text("Kopię otrzymuje Starosta Dalekowski.")
    p.text("Administratorem danych jest Urząd Miejski w Przykładowie.", role="clause")
    a = p.brief().addressee
    assert a.status == "ambiguous" and [c.name for c in a.candidates] == ["Urząd Miejski w Przykładowie", "Starosta Dalekowski"]
    assert a.name == "Urząd Miejski w Przykładowie" and len(a.evidence) == 2


def test_no_office_anywhere_stays_not_found() -> None:
    a = _paper().brief().addressee
    assert a.status == "not_found" and a.name is None and a.candidates == []


def test_the_clause_is_kept_as_paragraphs_without_repeats() -> None:
    p = _paper()
    for _ in range(2):   # a paper of two applications prints its clause twice
        p.text("Klauzula informacyjna:", role="clause")
        p.text("1. Dane przetwarza Wójt Gminy Wzorcowo w celu", role="clause")
        p.text("rozpatrzenia wniosku.", role="clause")
        p.text("2. Dane przechowuje się 5 lat.", role="clause")
    ct = p.brief().declarations.clause_text
    assert ct is not None and (ct.origin, ct.conf) == ("flow", 1.0)
    assert ct.paragraphs == ["Klauzula informacyjna:", "1. Dane przetwarza Wójt Gminy Wzorcowo w celu rozpatrzenia wniosku.",
                             "2. Dane przechowuje się 5 lat."]
    assert _paper().brief().declarations.clause_text is None


def _ocr_words(lines: list[tuple[float, float, str]]) -> tuple[PageModel, FinderOutput]:
    """A page as the OCR reader gives it: one run per word, each with its box and the word confidence."""
    runs, n = [], 0
    for x, y, text in lines:
        for word in text.split():
            n += 1
            w = 5.0 * len(word)
            runs.append(Run(id=f"r{n}", text=word, box=(x, y, x + w, y + 9.0), conf=0.92))
            x += w + 3.0
    n += 1
    runs.append(Run(id=f"r{n}", text="." * 30, box=(120.0, 400.0, 400.0, 409.0), conf=0.9))
    label = next(r.id for r in runs if r.text == "Cel")
    cand = Candidate(id="c1", kind="leader", page=1, box=(120.0, 400.0, 400.0, 409.0), runs=[runs[-1].id],
                     label=Label(text="Cel wpisu", runs=[label], how="left", margin=0.8), conf=Confidence(geometry=0.9, label=0.8, text=0.92))
    pm = PageModel(source=Source(sha256="0" * 64, format="png", reader="test.ocr", pages=1),
                   pages=[Page(number=1, origin="ocr", width=595.0, height=842.0, runs=runs)])
    fo = FinderOutput(input=InputRef(sha256="0" * 64, format="png"), order=[r.id for r in runs], sections=[], candidates=[cand], roles={})
    return pm, fo


def test_words_of_a_scan_are_joined_into_the_line_that_names_the_office() -> None:
    pm, fo = _ocr_words([(350.0, 100.0, "Urząd Miasta i Gminy Wzorcowo"), (350.0, 114.0, "ul. Lipowa 1"),
                         (200.0, 200.0, "WNIOSEK O WPIS"), (60.0, 400.0, "Cel wpisu")])
    a = understand(pm, fo, STRICT).addressee
    assert (a.status, a.name) == ("stated", "Urząd Miasta i Gminy Wzorcowo")
    ev = a.candidates[0].evidence
    assert ev.page == 1 and ev.box is not None and ev.box[1] == 100.0 and ev.quote == "Urząd Miasta i Gminy Wzorcowo"


def test_a_name_in_capitals_on_a_scan_is_written_in_title_case_with_its_place_name() -> None:
    pm, fo = _ocr_words([(300.0, 220.0, "WÓJT GMINY WZORCOWO"), (300.0, 235.0, "Wzorcowo 8"), (60.0, 400.0, "Cel wpisu")])
    a = understand(pm, fo, STRICT).addressee
    assert (a.status, a.kind, a.name) == ("stated", "body", "Wójt Gminy Wzorcowo")
