"""AUDIT-8 VA-8 (03-review-typing-lexicon F3, F8): "nie jest wymagane" / "niewymagane" make a place optional (it was
required, because "wymagan" matched the required row); a date and a place in one label in other word orders is text,
not a date picker. Negative neighbours keep their old meaning. Synthetic labels only."""
from __future__ import annotations

import pytest

from tests.mean.test_a8_lexicon_rows import _one


@pytest.mark.parametrize("label, required", [
    ("Adres poczty elektronicznej (nie jest wymagane)", False),
    ("Adres poczty elektronicznej (niewymagane)", False),
    ("Adres poczty elektronicznej (nieobowiązkowe)", False),   # unchanged
    ("Adres poczty elektronicznej (wymagane)", True),          # negative neighbour
    ("Adres poczty elektronicznej", True),                     # negative neighbour: our default
])
def test_explicitly_optional_wording(label: str, required: bool) -> None:
    f, _b = _one(label)
    assert f.required is required


@pytest.mark.parametrize("label, typ", [
    ("Data urodzenia i miejsce urodzenia", "TEXT_FIELD"),
    ("Miejsce i data urodzenia", "TEXT_FIELD"),
    ("Data i miejsce urodzenia", "TEXT_FIELD"),                # VA-5, unchanged
    ("Data urodzenia", "DATEPICKER"),                          # negative neighbour
    ("Data wydania decyzji", "DATEPICKER"),                    # negative neighbour: "data" + word, no place
])
def test_date_and_place_in_any_order_is_text(label: str, typ: str) -> None:
    f, _b = _one(label)
    assert f.type == typ
