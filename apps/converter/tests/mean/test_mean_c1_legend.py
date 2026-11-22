"""WP-C1 step h: a star alone is no cue; a legend under the star ("pola oznaczone gwiazdką są obowiązkowe") makes
the starred labels, and only them, required by the paper. The legend is the footnote of the star, so the footnote
path of the understanding step carries it; these tests pin that, and the negated legend (new with the guard)."""
from __future__ import annotations

import pytest

from tests.mean.test_mean_core import Paper


def _starred_and_plain(note: str):
    p = Paper()
    s = p.heading("Dane ogrodu")
    p.blank("Nazwa ogrodu*", section=s, footnotes=("*",))
    p.blank("Kolor furtki", section=s)
    p.text(note, role="note")
    got = {f.label: (f.required, f.required_basis) for sec in p.brief().matter for f in sec.fields}
    return got["Nazwa ogrodu"], got["Kolor furtki"]


@pytest.mark.parametrize("legend", [
    "* pola oznaczone gwiazdką są obowiązkowe",
    "* pola oznaczone * są wymagane",
    "*) pole obowiązkowe",
])
def test_a_legend_makes_the_starred_label_required_by_the_paper_and_no_other(legend: str) -> None:
    starred, plain = _starred_and_plain(legend)
    assert starred == (True, "paper")
    assert plain == (True, "inferred")


def test_a_star_of_the_strike_out_note_is_no_cue() -> None:
    starred, plain = _starred_and_plain("* niepotrzebne skreślić")
    assert starred == (True, "inferred") and plain == (True, "inferred")


def test_a_negated_legend_makes_the_starred_label_optional() -> None:   # was "required, paper" before the guard
    starred, plain = _starred_and_plain("* pola oznaczone gwiazdką nie są obowiązkowe")
    assert starred == (False, None) and plain == (True, "inferred")
