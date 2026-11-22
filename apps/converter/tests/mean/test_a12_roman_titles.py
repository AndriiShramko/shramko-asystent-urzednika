"""BL12: Roman section numbers keep their capitals when a shouted title goes to sentence case ("II. RODZAJ KARTY"
gave "Ii. rodzaj karty", found by the strict jury review on a new synthetic form)."""
from __future__ import annotations

import pytest

from app.mean._doc import is_roman, sentence_case


@pytest.mark.parametrize("raw, want", [
    ("II. RODZAJ KARTY", "II. rodzaj karty"),
    ("IV) DANE WNIOSKODAWCY", "IV) dane wnioskodawcy"),
    ("XII OŚWIADCZENIA", "XII oświadczenia"),
    ("I. DANE OSOBOWE", "I. dane osobowe"),
    ("WNIOSEK O WYDANIE I ZMIANĘ", "Wniosek o wydanie i zmianę"),
    ("DAJ MI ZNAĆ", "Daj mi znać"),
    ("Dane PESEL i NIP", "Dane PESEL i NIP"),
])
def test_roman_numbers_stay_in_capitals(raw, want):
    assert sentence_case(raw) == want


@pytest.mark.parametrize("word, roman", [
    ("II.", True), ("IV)", True), ("XII", True), ("I.", True), ("I", False), ("MI", False), ("CI", False),
    ("DC.", True), ("IIII", False), ("", False), ("VX", False),
])
def test_is_roman(word, roman):
    assert is_roman(word) is roman
