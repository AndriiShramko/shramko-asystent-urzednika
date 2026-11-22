"""AUDIT-8 VA-5 (22-F4, F6, F7, F8): rows of the lexicon for wordings common on Polish forms. Each row has a
negative neighbour that must keep its old meaning. Synthetic labels only."""
from __future__ import annotations

import pytest

from tests.mean.test_mean_core import Paper


def _one(label: str, kind: str = "leader", how: str = "left", before: tuple[str, ...] = ()):
    p = Paper()
    p.text("WNIOSEK O WPIS", bold=True)
    s = p.heading("Dane sprawy", number="3")
    for b in before:
        p.blank(b, section=s, kind=kind, how=how)
    p.blank(label, section=s, kind=kind, how=how)
    b = p.brief()
    got = [f for sec in b.matter for f in sec.fields]
    return got[-1] if got else None, b


@pytest.mark.parametrize("label, want", [
    ("a) nazwa podmiotu", "Nazwa podmiotu"),          # 22-F4: lower-case lettering is numbering
    ("b) uzasadnienie", "Uzasadnienie"),
])
def test_lower_case_lettering_is_stripped(label: str, want: str) -> None:
    f, _b = _one(label)
    assert f.label == want


def test_a_word_that_starts_with_a_letter_and_bracket_stays() -> None:
    f, _b = _one("Nazwa (skrot)")
    assert f.label.startswith("Nazwa")


@pytest.mark.parametrize("label, typ, concept", [
    ("PESEL lub numer paszportu", "TEXT_FIELD", None),   # 22-F6: either of two identifiers, no PESEL check
    ("NIP/PESEL", "TEXT_FIELD", None),
    ("Kwota słownie", "TEXT_FIELD", None),              # an amount in words is text
    ("Data i miejsce urodzenia", "TEXT_FIELD", None),   # a date and a place: not a date picker
    ("Rachunek bankowy", "TEXT_FIELD", "nrb"),          # 22-F7: "rachunek" itself, not only "rachunku"
    ("Numer konta", "TEXT_FIELD", "nrb"),
    ("nr tel.", "TEXT_FIELD", "phone"),
    ("tel. kontaktowy", "TEXT_FIELD", "phone"),
    # negative neighbours: the old meaning stays
    ("PESEL", "TEXT_FIELD", "pesel"),
    ("Kwota", "NUMBER", "amount_pln"),
    ("Data urodzenia", "DATEPICKER", "date"),
    ("Hotel", "TEXT_FIELD", None),
    ("Kontakt", "TEXT_FIELD", None),
])
def test_concept_rows(label: str, typ: str, concept: str | None) -> None:
    f, _b = _one(label)
    assert (f.type, f.concept) == (typ, concept)


def test_an_amount_inside_a_sentence_is_a_number() -> None:
    f, _b = _one("w kwocie", kind="blank_in_sentence", how="sentence")
    assert (f.label, f.type) == ("Kwota", "NUMBER")


def test_a_day_inside_a_sentence_is_a_date() -> None:
    f, _b = _one("w dniu", kind="blank_in_sentence", how="sentence")
    assert f.type == "DATEPICKER"


def test_a_period_from_to_inside_a_sentence_is_two_dates() -> None:
    p = Paper()
    p.text("WNIOSEK O WPIS", bold=True)
    s = p.heading("Okres", number="3")
    p.blank("w okresie od", section=s, kind="blank_in_sentence", how="sentence")
    p.blank("do", section=s, kind="blank_in_sentence", how="sentence")
    got = [(f.type) for sec in p.brief().matter for f in sec.fields]
    assert got == ["DATEPICKER", "DATEPICKER"]


def test_place_and_date_at_the_foot_of_the_paper_is_the_signature_date() -> None:   # 22-F8
    f, b = _one("Miejscowość, data", before=("Nazwa sali",))
    assert f.label == "Nazwa sali"
    assert any(d.reason == "SIGNATURE_AND_DATE" for d in b.dropped)


def test_a_plain_place_at_the_foot_stays_a_field() -> None:
    f, _b = _one("Miejscowość", before=("Nazwa sali",))
    assert f is not None
