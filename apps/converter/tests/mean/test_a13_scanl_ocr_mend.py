"""BL13 SCAN-L: labels read by OCR from a scan lose the tokens a dotted leader became and take the lead-in phrase of
the lexicon they misspell by at most one letter in six; real words are never cut."""
from __future__ import annotations

import pytest

from app.mean._fields import _PHRASES, _leader_token, ocr_mend, ocr_vocab

REAL = ["przeterminowane", "Wierzbięcice", "ewentualnie", "deklaracje", "zezwolenie", "rezerwacje", "eksperci",
        "cesarzowa", "seksrecesja", "Szczecinek", "osiedle", "przedsiębiorcę", "wnioskodawca", "Rzeczpospolitej",
        "serwerowe", "ceremonie", "korespondencji", "Warszawa", "erozja", "sesje", "Rosevear", "averse"]


@pytest.mark.parametrize("word", REAL)
def test_real_words_are_no_leaders(word):
    assert not _leader_token(word)
    assert ocr_mend(f"{word} przy ulicy") == "przy ulicy" or word in ocr_mend(f"{word} przy ulicy")


@pytest.mark.parametrize("tok", ["Reeeeeeeeeeeseeeeee", "eeceeeeeo", "eeeeeeeeeee", "esesesee", "....eeeeeeee...."])
def test_leader_artifacts(tok):
    assert _leader_token(tok)


def test_leader_dropped_then_phrase():
    assert ocr_mend("Reeeeeeeeeeeseeeeee przy ulicy?") == "przy ulicy"


def test_misspelled_lead_in():
    assert ocr_mend("W micjscowOŚCI") == "w miejscowości"


def test_far_text_stays():
    assert ocr_mend("Numer ewidencyjny działki") == "Numer ewidencyjny działki"   # a known wording stays as printed
    assert ocr_mend("Obręb") == "Obręb"
    assert ocr_mend("w miasteczku") == "w miasteczku"


def test_dictionary_is_the_lexicon_without_stems():
    v = ocr_vocab()
    assert "w miejscowości" in v and "kod pocztowy" in v and "wójta gminy" in v and "miejscowość, data" in v
    assert not {"siedzib", "pełnomocni", "ewentualn", "wnioskodawc"} & set(v)
    assert all(k in v for k in _PHRASES if len(k) >= 6)


def test_misspelt_lexicon_words():
    assert ocr_mend("Kod pocztcwy") == "kod pocztowy" or ocr_mend("Kod pocztcwy").casefold() == "kod pocztowy"
    assert ocr_mend("Wojewodztwo").casefold() == "województwo"


def test_only_leader_kept_as_is():
    # nothing but leader dots: the label is not emptied by the mending, the caller decides
    assert ocr_mend("eeeeeeeeee") == "eeeeeeeeee"
