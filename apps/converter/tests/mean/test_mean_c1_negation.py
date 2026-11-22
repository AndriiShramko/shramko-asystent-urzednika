"""WP-C1 step c: a negation before a required cue blocks it. Synthetic labels; every "not paper" case failed on the
code before the guard (the habit `required` fired on "wymagan" after "nie jest")."""
from __future__ import annotations

import pytest

from tests.mean.test_mean_core import Paper


def field_of(label: str, title: str = "Dane ogrodu", footnote: str | None = None):
    """The one field of the matter that a paper with this section title and this label gives."""
    p = Paper()
    s = p.heading(title)
    p.blank(label, section=s, footnotes=("1",) if footnote else ())
    if footnote:
        p.text(f"1) {footnote}", role="note")
    got = [f for sec in p.brief().matter for f in sec.fields]
    assert len(got) == 1, [f.label for f in got]
    return got[0]


@pytest.mark.parametrize("label", [
    "Kolor furtki nie jest wymagany",
    "Gatunki drzew nie są wymagane",
    "Opis grządek niewymagany",
    "Podanie koloru furtki nie jest obowiązkowe",
    "Kolor furtki, nie dotyczy ogrodów bez wymaganego ogrodzenia",
])
def test_a_negated_cue_is_not_required_by_the_paper(label: str) -> None:
    assert field_of(label).required_basis != "paper"


@pytest.mark.parametrize("label", [
    "Nazwa ogrodu - pole wymagane",
    "Nazwa ogrodu - pole obowiązkowe",
    "Nie wiadomo jeszcze, ile grządek powstanie w tym ogrodzie, liczba grządek wymagana",   # the "nie" is out of reach
])
def test_a_plain_cue_is_required_by_the_paper(label: str) -> None:
    f = field_of(label)
    assert (f.required, f.required_basis) == (True, "paper")


def test_a_negated_cue_in_a_footnote_is_not_required_by_the_paper() -> None:
    assert field_of("Kolor furtki", footnote="Podanie tej informacji nie jest wymagane.").required_basis != "paper"
    assert field_of("Kolor furtki", footnote="Pole wymagane.").required_basis == "paper"
