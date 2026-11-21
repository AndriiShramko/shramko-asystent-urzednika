"""WP-F3b, finder second pass: symbol-font option marks (sets 3 and 9) and numbered headings that are not bold
(set 9 PDF), on synthetic pages built from code."""
from __future__ import annotations

from app.find import find
from app.mean import understand
from tests.find.find_builders import DOTS, Native, model

PUA = ""   # the glyph set 3 prints before each option of a list


def _options_page() -> Native:
    n = Native()
    n.text(70, 100, "WNIOSEK O WYDANIE ZAŚWIADCZENIA", 300, bold=True)
    n.text(90, 130, "Proszę o wydanie zaświadczenia o:", 250, bold=True)
    n.text(90, 160, f"{PUA} ilości posiadanych użytków rolnych", 250)
    n.text(90, 182, f"{PUA} okresie posiadania gospodarstwa rolnego", 250)
    n.text(90, 204, f"{PUA} nieposiadaniu gospodarstwa rolnego", 250)
    n.text(90, 226, f"{PUA} inne", 30)
    n.text(125, 226, DOTS, 250)
    return n


def test_symbol_font_marks_make_one_group_with_the_blank_of_inne() -> None:
    fo = find(model(_options_page().page()))
    groups = [c for c in fo.candidates if c.kind == "choice_group"]
    assert len(groups) == 1
    g = groups[0]
    assert [o.text for o in g.options][-1] == "inne"
    assert len(g.options) == 4
    assert g.options[-1].blank is not None
    assert g.label is not None and g.label.text.startswith("Proszę o wydanie")


def test_a_symbol_bullet_and_a_glyph_inside_a_sentence_are_not_marks() -> None:
    n = Native()
    n.text(70, 100, "INFORMACJE", 300, bold=True)
    n.text(90, 130, " Opłata wynosi 17 zł od każdego egzemplarza", 300)      # Symbol bullet
    n.text(90, 152, f"Wpisz znak {PUA} w polu obok", 300)                           # not at the start
    fo = find(model(n.page()))
    assert not [c for c in fo.candidates if c.kind in ("box", "choice_group")]


def _numbered_variant(number: int, roman: str, what: str) -> Native:
    n = Native(number)
    n.text(80, 74, f"{roman}. Wniosek o przyznanie {what} sportowego Rady Miasta", 360)
    n.text(107, 90, "Przykładowa", 80)                       # the title wraps onto a short line
    n.text(71, 118, "1. Dane kandydata", 150)
    n.text(71, 150, "Imię", 30)
    n.text(100, 150, DOTS, 200)
    n.text(71, 180, "Nazwisko", 50)
    n.text(125, 180, DOTS, 200)
    return n


def test_numbered_headings_at_the_top_of_a_page_open_sections_without_bold() -> None:
    fo = find(model(_numbered_variant(1, "I", "stypendium").page()))
    titles = [s.title for s in fo.sections]
    assert titles[0] == "Wniosek o przyznanie stypendium sportowego Rady Miasta Przykładowa"
    assert "Dane kandydata" in titles


def test_numbered_labels_lower_on_a_page_stay_labels() -> None:
    n = Native()
    n.text(70, 60, "DEKLARACJA O WYSOKOŚCI OPŁATY", 300, bold=True)
    n.text(70, 80, "Część pierwsza formularza", 200)
    n.text(70, 100, "Druga linia wstępu", 200)
    n.text(70, 300, "4. Nazwisko i imię", 150)
    n.text(70, 320, DOTS, 200)
    fo = find(model(n.page()))
    assert "Nazwisko i imię" not in [s.title for s in fo.sections]


def test_three_numbered_variants_give_one_selector() -> None:
    pm = model(_numbered_variant(1, "I", "stypendium").page(), _numbered_variant(2, "II", "nagrody").page(),
               _numbered_variant(3, "III", "wyróżnienia").page())
    brief = understand(pm, find(pm), {"strict": True})
    assert brief.title.value == "Wniosek o przyznanie stypendium sportowego Rady Miasta Przykładowa"
    selectors = [f for m in brief.matter for f in m.fields if f.key == "rodzaj_wniosku"]
    assert len(selectors) == 1 and len(selectors[0].options) == 3


def test_numbered_single_boxes_in_two_columns_with_places_between_are_one_group() -> None:
    n = Native()
    n.text(70, 100, "C. OKOLICZNOŚCI", 300, bold=True)
    n.text(70, 120, "25. Okoliczności", 150)
    n.text(80, 150, "☐ 1. pierwsza deklaracja", 200)
    n.text(80, 172, "data zdarzenia", 80)
    n.text(170, 172, DOTS, 120)
    n.text(80, 200, "☐ 3. ustanie obowiązku", 200)
    n.text(330, 150, "☐ 2. nowa deklaracja", 200)
    n.text(330, 200, "☐ 4. korekta deklaracji", 200)
    fo = find(model(n.page()))
    groups = [c for c in fo.candidates if c.kind == "choice_group"]
    assert len(groups) == 1 and len(groups[0].options) == 4
    assert [o.text.split()[0] for o in groups[0].options] == ["1.", "2.", "3.", "4."]


def test_numbered_single_boxes_with_a_gap_in_the_numbers_stay_single() -> None:
    n = Native()
    n.text(70, 100, "C. OKOLICZNOŚCI", 300, bold=True)
    n.text(80, 150, "☐ 1. pierwsza deklaracja", 200)
    n.text(80, 200, "☐ 3. ustanie obowiązku", 200)
    fo = find(model(n.page()))
    assert not [c for c in fo.candidates if c.kind == "choice_group"]
