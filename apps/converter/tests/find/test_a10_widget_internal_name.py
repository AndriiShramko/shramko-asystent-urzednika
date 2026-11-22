"""WAVE-10 VJF-2: a fillable widget named like a program identifier ("Nazwisko_Osoba", "AdresPocztyElektronicznej",
"Text7") gave a field labelled with that identifier although the paper prints the question beside the box.

A text widget with such a name takes the words printed left of it or above it; when the paper shows none, the name
made readable. A widget named in plain words keeps its name; a box to tick keeps its readable name. Synthetic pages.
"""
from __future__ import annotations

from app.find import find
from app.mean import understand
from app.model.page import Widget
from tests.find.find_builders import Native, model


def _fields(n: Native, *widgets: Widget) -> list[str]:
    pg = n.page().model_copy(update={"widgets": list(widgets)})
    m = model(pg)
    b = understand(m, find(m))
    return [f.label for s in b.matter for f in s.fields]


def _paper() -> Native:
    n = Native()
    n.text(70, 60, "WNIOSEK O WYDANIE ZASWIADCZENIA", 300, bold=True)
    return n


def test_identifier_name_gives_way_to_the_printed_label() -> None:
    n = _paper()
    n.text(50, 100, "Nazwisko wnioskodawcy", 120)
    n.text(50, 130, "Adres poczty elektronicznej", 130)
    labels = _fields(n, Widget(id="p1w1", kind="text", name="Nazwisko_Osoba", box=(200, 98, 500, 112)),
                     Widget(id="p1w2", kind="text", name="AdresPocztyElektronicznej", box=(200, 128, 500, 142)))
    assert labels == ["Nazwisko wnioskodawcy", "Adres poczty elektronicznej"]


def test_identifier_name_without_printed_words_is_made_readable() -> None:
    n = _paper()
    labels = _fields(n, Widget(id="p1w1", kind="text", name="Miejsce_Urodzenia", box=(200, 300, 500, 314)))
    assert labels == ["Miejsce urodzenia"]


def test_plain_word_name_stays() -> None:
    n = _paper()
    n.text(50, 100, "Imie", 30)
    labels = _fields(n, Widget(id="p1w1", kind="text", name="Nazwa ogrodu", box=(200, 300, 500, 314)))
    assert "Nazwa ogrodu" in labels


def test_alias_rules() -> None:
    from app.find._core import widget_alias
    assert widget_alias("form1[0].Page1[0].Imię_Osoba[0]") == "Imię osoba"
    assert widget_alias("AdresPocztyElektronicznej") == "Adres poczty elektronicznej"
    assert widget_alias("Data_dzień") == "Data dzień"
    assert widget_alias("PESEL_Osoba") == "PESEL osoba"
