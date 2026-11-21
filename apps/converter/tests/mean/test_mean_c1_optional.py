"""WP-C1 step d: the paper's own words for "optional" beyond the three of the habit `optional`. Synthetic labels;
every "optional" case was "required, inferred" before."""
from __future__ import annotations

import pytest

from tests.mean.test_mean_c1_negation import field_of


@pytest.mark.parametrize("label", [
    "Ewentualne uwagi o ogrodzie",
    "Adres składzika, jeśli różni się od adresu ogrodu",
    "Adresy składzików, jeżeli są różne od adresu ogrodu",
    "Opis dodatkowy w razie potrzeby",
    "Kolor furtki nie jest wymagany",
    "Opis grządek niewymagany",
    "Podanie koloru furtki nie jest obowiązkowe",
])
def test_the_papers_wording_makes_a_field_optional(label: str) -> None:
    f = field_of(label)
    assert (f.required, f.required_basis) == (False, None)


@pytest.mark.parametrize("label", [
    "Kolor furtki, jeśli jest znany",          # a condition alone is not "optional" in the understanding step
    "Potrzeby ogrodu",                         # "potrzeby" without "w razie"
    "Różnica wysokości grządek",
])
def test_similar_words_do_not_make_a_field_optional(label: str) -> None:
    f = field_of(label)
    assert (f.required, f.required_basis) == (True, "inferred")


def test_an_optional_wording_in_a_footnote_makes_the_field_optional() -> None:
    assert field_of("Kolor furtki", footnote="Ewentualnie podać odcień.").required is False
    assert field_of("Kolor furtki", footnote="Wypełnić w razie potrzeby.").required is False
