"""A8 CX, ORDER C5: headings.

1. A heading followed by an instruction in brackets is cut at " (" before the heading tests: "4. Uzasadnienie wniosku
   (opisz ...)" and "B.4 ADRES DO KORESPONDENCJI (wypełnić tylko ...)" are headings; the words in brackets do not
   make the line an instruction.
2. A numbered line that is not bold and not at the top of its page is a heading when the numbers before it at its
   level are all headings already (1, 2, 3 -> 4); a form that numbers its labels (no numbered headings) keeps them.
3. A row of two or more numbered captions ("17. Kraj   20. Miejscowość") is never a heading.

Synthetic words only.
"""
from __future__ import annotations

from app.find import find
from find_builders import DOTS, STRICT, Native, flow, model


def _sections(out) -> list[tuple[str | None, str]]:  # noqa: ANN001
    return [(s.number, s.title) for s in out.sections]


def test_numbered_heading_with_a_bracket_continues_the_numbered_headings():
    page = flow("Urzad Gminy Przykladowo", "Wniosek o zwrot oplaty",
                "1. Dane wnioskodawcy", "Imie i nazwisko: " + DOTS,
                "2. Informacje o oplacie", "Data uiszczenia: " + DOTS, "Wysokosc oplaty: " + DOTS,
                "3. Uzasadnienie wniosku (opisz w polu ponizej, dlaczego oplata zostala uiszczona blednie i podaj szczegoly)",
                DOTS,
                "4. Sposob zwrotu oplaty (postaw x w wybranym polu)",
                "□ Gotowka w kasie", "□ Przelewem na rachunek",
                bold=(2, 4))
    out = find(model(page), STRICT)
    secs = _sections(out)
    assert ("3", "Uzasadnienie wniosku") in secs, secs
    assert ("4", "Sposob zwrotu oplaty") in secs, secs


def test_capital_heading_with_a_lowercase_bracket_is_a_heading_not_an_instruction():
    page = flow("B.3 ADRES ZAMIESZKANIA", "Miejscowosc: " + DOTS,
                "B.4 ADRES DO KORESPONDENCJI (wypelnic tylko w przypadku, kiedy jest inny niz w poz. B.3)",
                "Miejscowosc: " + DOTS, bold=(0,))
    out = find(model(page), STRICT)
    titles = [t for _n, t in _sections(out)]
    assert any(t.startswith("B.4 ADRES DO KORESPONDENCJI") for t in titles), titles


def test_a_row_of_numbered_captions_is_not_a_heading():
    n = Native()
    n.text(60, 60, "17. Kraj", w=40)
    n.text(300, 60, "20. Miejscowosc", w=70)
    n.text(60, 80, DOTS, w=200)
    n.text(300, 80, DOTS, w=200)
    out = find(model(n.page()), STRICT)
    titles = [t for _n, t in _sections(out)]
    assert not any("Kraj" in t or "Miejscowosc" in t for t in titles), titles


def test_two_numbered_captions_in_one_line_are_not_a_heading():
    page = flow("1. Skladajacy", "Wlasciciel: " + DOTS, "2. Dane", "Nazwisko: " + DOTS, "Imie: " + DOTS,
                "3. PESEL 4. NIP/REGON (dot. tylko osob prawnych)", DOTS, bold=(0, 2))
    out = find(model(page), STRICT)
    titles = [t for _n, t in _sections(out)]
    assert not any("PESEL" in t for t in titles), titles


def test_numbered_labels_of_a_form_without_numbered_headings_stay_labels():
    """Negative control: a declaration that numbers its labels (no numbered heading before them)."""
    page = flow("A. DANE SKLADAJACEGO", "Prosze wypelnic pola ponizej", "Pola sa wymagane", "Uwaga",
                "11. Numer domu", DOTS, "12. Numer lokalu", DOTS, bold=(0,))
    out = find(model(page), STRICT)
    titles = [t for _n, t in _sections(out)]
    assert not any("Numer" in t for t in titles), titles
