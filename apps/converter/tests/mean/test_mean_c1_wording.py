"""WP-C1 step e2 (item 4 of the order): "należy wypełnić" and "musi zawierać" are the paper's words for required;
an asterisk alone is not. Synthetic labels; the "paper" cases were "required, inferred" before."""
from __future__ import annotations

import pytest

from tests.mean.test_mean_c1_negation import field_of


@pytest.mark.parametrize("label", [
    "Nazwa ogrodu - należy wypełnić",
    "Nazwa ogrodu (należy wypełnić)",
    "Opis ogrodu musi zawierać liczbę grządek",
])
def test_the_papers_wording_makes_a_field_required_by_the_paper(label: str) -> None:
    f = field_of(label)
    assert (f.required, f.required_basis) == (True, "paper")


@pytest.mark.parametrize("label", [
    "Nazwa ogrodu (należy wypełnić drukowanymi literami)",     # how to fill in, not whether
    "Nazwa ogrodu (należy wypełnić w przypadku ogrodu z ogrodzeniem)",
    "Rubryki o kolorze furtki nie należy wypełnić",
    "Nazwa ogrodu*",                                           # on these papers a star is a footnote mark
])
def test_similar_wording_is_not_required_by_the_paper(label: str) -> None:
    assert field_of(label).required_basis != "paper"


def test_the_wording_in_a_footnote_is_required_by_the_paper() -> None:
    f = field_of("Kolor furtki", footnote="Należy wypełnić.")
    assert (f.required, f.required_basis) == (True, "paper")
