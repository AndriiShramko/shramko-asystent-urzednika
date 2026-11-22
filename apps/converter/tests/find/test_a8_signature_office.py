"""AUDIT-8 VA-1 (22-F1, 22-F2): a signature blank that shares its line with a date, and the places of a part the
office fills, are no fields of the applicant. Synthetic papers; each rule has a negative case."""
from __future__ import annotations

from app.find import find
from app.mean import understand
from tests.find.find_builders import DOTS, Native, model


def _run(n: Native):
    m = model(n.page())
    f = find(m)
    return f, understand(m, f)


def _labels(b) -> list[str]:
    return [f.label for s in b.matter for f in s.fields]


def _paper(*extra: tuple[float, str, float, bool]) -> Native:
    """Extra lines (y, text, width, bold); a text of dots stands right of the label on its row."""
    n = Native()
    n.text(70, 60, "WNIOSEK O WYDANIE ZASWIADCZENIA", 300, bold=True)
    n.text(50, 100, "Nazwa ogrodu", 80)
    n.text(140, 100, DOTS, 200)
    for y, text, w, bold in extra:
        n.text(140 if text == DOTS else 50, y, text, w, bold=bold)
    return n


def test_date_and_signature_on_one_line_are_left_out() -> None:
    f, b = _run(_paper((600, "Data .......... Podpis ..........", 300, False)))
    assert _labels(b) == ["Nazwa ogrodu"]
    assert sorted(c.kind for c in f.candidates if c.label and c.label.text in ("Data", "Podpis")) == ["signature", "signature"]


def test_a_dotted_line_with_its_bracketed_signature_caption_is_left_out() -> None:
    _f, b = _run(_paper((600, ".......... (podpis)", 300, False)))
    assert _labels(b) == ["Nazwa ogrodu"]


def test_a_long_sentence_that_names_a_signature_keeps_its_blank() -> None:
    # negative case: a blank in a sentence with many words is no signature even when the sentence says "podpis"
    _f, b = _run(_paper((300, "Upowazniam do odbioru dokumentu za podpisem osobe .......... w terminie ..........", 400, False)))
    assert len(_labels(b)) >= 2


def test_ja_nizej_podpisany_names_the_person_and_stays_a_field() -> None:
    _f, b = _run(_paper((300, "Ja nizej podpisany .......... zamieszkaly ..........", 300, False)))
    assert len(_labels(b)) >= 2


def test_a_date_on_a_line_without_a_signature_stays_a_field() -> None:
    _f, b = _run(_paper((300, "Data zdarzenia .......... Miejsce zdarzenia ..........", 300, False)))
    assert "Data zdarzenia" in _labels(b)


def test_places_under_an_office_heading_are_office_use() -> None:
    f, b = _run(_paper((500, "WYPEŁNIA URZĄD", 200, True), (520, "Uwagi", 40, False), (520, DOTS, 200, False)))
    assert _labels(b) == ["Nazwa ogrodu"]
    assert any(c.kind == "office_use" for c in f.candidates)


def test_a_part_filled_by_the_office_in_other_words_is_office_use() -> None:
    _f, b = _run(_paper((500, "CZĘŚĆ WYPEŁNIANA PRZEZ URZĄD", 250, True), (520, "Decyzja", 40, False),
                        (520, DOTS, 200, False)))
    assert _labels(b) == ["Nazwa ogrodu"]


def test_a_part_the_organizer_fills_stays_with_the_applicant() -> None:
    # negative case (review 43): "wypełnia organizator" names the applicant of an event, not the office
    _f, b = _run(_paper((500, "WYPEŁNIA ORGANIZATOR", 200, True), (520, "Nazwa imprezy", 80, False),
                        (520, DOTS, 200, False)))
    assert "Nazwa imprezy" in _labels(b)


def test_a_part_the_employee_fills_stays_with_the_applicant() -> None:
    # negative case (review 43): on a staff form "wypełnia pracownik" is the person who files it
    _f, b = _run(_paper((500, "Część I – wypełnia pracownik", 200, True), (520, "Stanowisko", 80, False),
                        (520, DOTS, 200, False)))
    assert "Stanowisko" in _labels(b)


def test_an_office_box_above_the_title_does_not_take_the_applicant_fields() -> None:
    # review 43: the office box stands above the title and no heading follows the title before the first field
    n = Native()
    n.text(50, 20, "WYPEŁNIA URZĄD", 150, bold=True)
    n.text(50, 35, "Data wpływu", 60)
    n.text(140, 35, DOTS, 200)
    n.text(70, 60, "WNIOSEK O WYDANIE ZASWIADCZENIA", 300, bold=True)
    n.text(50, 100, "Nazwa ogrodu", 80)
    n.text(140, 100, DOTS, 200)
    _f, b = _run(n)
    assert "Nazwa ogrodu" in _labels(b)


def test_the_next_heading_ends_the_office_part() -> None:
    _f, b = _run(_paper((500, "WYPEŁNIA URZĄD", 200, True), (520, "Uwagi", 40, False), (520, DOTS, 200, False),
                        (600, "DANE DZIALKI", 200, True), (620, "Numer dzialki", 80, False), (620, DOTS, 200, False)))
    assert "Numer dzialki" in _labels(b)
