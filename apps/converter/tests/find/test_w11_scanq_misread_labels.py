"""Wave 11 SCANQ: the guard of label cleanup for a dotted leader that the OCR read as letters and the image reader
could not turn back into dots. The garbage strings are the labels the verified image gave for the set scans
(sets 06, 07 and 09, SCAN_PREP off); the real labels are labels of the same forms that must come through unchanged."""
from __future__ import annotations

import pytest

from app.find._core import clean, drop_misread, misread

GARBAGE = ["eeeeeeeeee«", "eeeeeeeeev.", "eeeeeeeev.", "e-ezeeeeee", "e-eeeeeeee", "eeeeeeeseee", "eseeeeee",
           "eeseeeev.", "eeeeeeeeeeee", "e..e.eees", "eeer", "eee", "eeeeeerseesraeeeeaeee", "eeeeeeeseeseaeeeeeeee",
           "eeeeeeeaeesraeeeeaeee", "sirzzcyznsrszozssswszesieszi", "Eeveeeeseeeseeeeee"]

REAL = ["szerokość", "razem", "działka", "nr", "ewid", "korespondencyjny:", "www.bydgoszcz.pl", "III", "XXX", "VIII.",
        "nieruchomości", "współwłaścicieli", "zaświadczenia", "skarbowej", "oświadczenie", "PESEL", "REGON",
        "Wnioskodawca/Pełnomocnik", "zezwolenia", "długość", "powierzchnia", "(imię", "nazwisko)", "m²", "ee"]


@pytest.mark.parametrize("chunk", GARBAGE)
def test_a_leader_read_as_letters_is_told(chunk):
    assert misread(chunk)


@pytest.mark.parametrize("chunk", REAL)
def test_a_real_word_is_not(chunk):
    assert not misread(chunk)


@pytest.mark.parametrize("raw, label", [
    ("eeeeeeeeee« szerokość", "szerokość"),
    ("eeeeeeeev. razem", "razem"),
    ("e-ezeeeeee szerokość", "szerokość"),
    ("eseeeeee razem", "razem"),
    ("e..e.eees eeer eee eee eee ke eee działka nr ewid", "działka nr ewid"),
    ("Eeveeeeseeeseeeeee przy ulicy", "przy ulicy"),
    ("Inny adres korespondencyjny: sirzzcyznsrszozssswszesieszi", "Inny adres korespondencyjny"),
    ("eeeeeerseesraeeeeaeee", ""),
])
def test_on_an_ocr_page_the_label_loses_the_misread_leader(raw, label):
    assert clean(raw, True)[0] == label


@pytest.mark.parametrize("raw", [
    "Imię i nazwisko", "Adres zamieszkania (ulica, nr domu, nr lokalu)", "Strona www.bydgoszcz.pl", "Część III",
    "Powierzchnia zajętego pasa drogowego w m²", "eeeeee nr", "nr eeeeee ewid",
])
def test_words_around_are_kept(raw):
    kept = drop_misread(raw).split()
    assert [w for w in raw.split() if not misread(w)] == kept


def test_a_text_without_one_is_the_same_string():
    raw = "Imię  i nazwisko:\xa0"
    assert drop_misread(raw) is raw


def test_off_an_ocr_page_nothing_changes():
    assert clean("eeeeeeeeee« szerokość")[0] == "eeeeeeeeee« szerokość"
    assert clean("eeeeeeeeee« szerokość", False)[0] == "eeeeeeeeee« szerokość"
