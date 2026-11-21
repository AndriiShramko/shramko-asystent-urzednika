"""The finder on synthetic papers (WP-F3, design 6.3): each rule has a paper that would break it.

Drills of the verification plan, section 2: 3 (two columns), 4 (text boxes in another order), 7 (a box with
"inne (jakie?)" next to a bullet), 8 (eleven boxes are one value), 10 (a table that continues on the next page).
"""
from __future__ import annotations

import random

from app.find import find
from app.model import count_coverage
from app.model.page import Page, Run
from find_builders import DOTS, STRICT, Native, flow, flow_table, model, pdf, tops


def _kinds(out) -> list[str]:  # noqa: ANN001
    return [c.kind for c in tops(out)]


def _labels(out) -> list[str | None]:  # noqa: ANN001
    return [c.label.text if c.label else None for c in tops(out)]


def _covered(out, pm) -> None:  # noqa: ANN001
    cov = count_coverage(out, pm)
    assert cov.unassigned == [], cov.unassigned
    assert sorted(out.order) == sorted(pm.run_index())


# ---------------------------------------------------------------- leaders, blanks, line blocks


def test_blanks_inside_a_sentence_keep_the_words_before_them_pdf():
    def draw(c):  # noqa: ANN001
        c.setFont("Helvetica", 11)
        c.drawString(70, 700, "Wnosze o ustalenie numeru budynkowi polozonemu")
        c.drawString(70, 680, "w miejscowosci " + "." * 30 + " przy ulicy " + "." * 30)
        c.drawString(70, 660, "nr dzialki " + "." * 15 + " w obrebie " + "." * 40)

    pm = pdf(draw)
    out = find(pm, STRICT)
    assert _kinds(out) == ["blank_in_sentence"] * 4
    assert _labels(out) == ["w miejscowosci", "przy ulicy", "nr dzialki", "w obrebie"]
    assert {c.label.how for c in out.candidates} == {"sentence"}
    _covered(out, pm)


def test_blanks_inside_one_flow_run_are_spans_and_the_footnote_mark_is_not_label_text():
    pm = model(flow("w\xa0miejscowości……………….……………… przy ulicy1)……………….…………………"), fmt="docx")
    out = find(pm, STRICT)
    assert _labels(out) == ["w miejscowości", "przy ulicy"]
    assert out.candidates[1].footnotes == ["1"]
    assert all(c.spans and not c.runs and c.anchor == "p[0]" for c in out.candidates)
    out.check_spans(pm)
    _covered(out, pm)


def test_caption_under_a_leader_and_three_dotted_lines_as_one_block_pdf():
    def draw(c):  # noqa: ANN001
        c.setFont("Helvetica", 11)
        c.drawString(70, 760, "." * 40)
        c.setFont("Helvetica", 8)
        c.drawString(90, 748, "(imie i nazwisko)")
        c.setFont("Helvetica", 11)
        c.drawString(70, 700, "Uzasadnienie:")
        for k in range(3):
            c.drawString(70, 680 - 16 * k, "." * 110)

    out = find(pdf(draw), STRICT)
    assert _kinds(out) == ["leader", "line_block"]
    assert _labels(out) == ["imie i nazwisko", "Uzasadnienie"]
    assert out.candidates[1].lines == 3 and out.candidates[1].label.how == "above"


def test_signature_and_office_use_come_from_the_label():
    pm = model(flow("Nr sprawy: " + DOTS, DOTS, "(podpis wnioskodawcy)"), fmt="docx")
    out = find(pm, STRICT)
    assert _kinds(out) == ["office_use", "signature"]


def test_a_place_without_any_text_is_a_warning_not_a_guess():
    n = Native()
    n.text(60, 400, DOTS, w=200)
    out = find(model(n.page()), STRICT)
    assert _labels(out) == [None]
    assert [(w.code, w.candidate, w.page) for w in out.warnings] == [("LABEL_NOT_FOUND", "c1", 1)]
    assert out.candidates[0].conf.label == 0.0


# ---------------------------------------------------------------- combs (drill 8)


def test_eleven_boxes_are_one_value_and_a_printed_hyphen_is_the_mask_pdf():
    def draw(c):  # noqa: ANN001
        c.setFont("Helvetica", 10)
        c.drawString(70, 705, "PESEL")
        for k in range(11):
            c.rect(120 + 16 * k, 700, 16, 18)
        c.drawString(70, 665, "Kod pocztowy")
        for k in (0, 1):
            c.rect(160 + 16 * k, 660, 16, 18)
        c.drawString(197, 665, "-")
        for k in (0, 1, 2):
            c.rect(208 + 16 * k, 660, 16, 18)

    pm = pdf(draw)
    out = find(pm, STRICT)
    assert _kinds(out) == ["comb", "comb"]                      # never one field per box
    assert [c.cells for c in out.candidates] == [11, 5]
    assert _labels(out) == ["PESEL", "Kod pocztowy"]
    assert [c.mask for c in out.candidates] == [None, "__-___"]
    _covered(out, pm)


def test_a_date_comb_takes_the_pattern_printed_under_it():
    n = Native()
    n.text(60, 104, "Data", w=22)
    for k in (0, 1, 3, 4, 6, 7, 8, 9):
        n.rect(100 + 16 * k, 100, 16, 18)
    n.text(136, 104, "-", w=4)
    n.text(184, 104, "-", w=4)
    n.text(110, 122, "DD-MM-RRRR", w=60, size=8.0)
    pm = model(n.page())
    out = find(pm, STRICT)
    assert [(c.kind, c.cells, c.mask) for c in out.candidates] == [("comb", 8, "DD-MM-RRRR")]
    assert len(out.candidates[0].runs) == 3                     # two hyphens and the pattern belong to the place
    _covered(out, pm)


def test_two_boxes_with_a_label_between_them_are_two_cells_not_a_comb():
    n = Native()
    n.text(60, 105, "Nr domu", w=36)
    n.rect(100, 100, 30, 20)
    n.text(140, 105, "Nr lokalu", w=40)
    n.rect(185, 100, 30, 20)
    out = find(model(n.page()), STRICT)
    assert _kinds(out) == ["cell", "cell"] and _labels(out) == ["Nr domu", "Nr lokalu"]


# ---------------------------------------------------------------- boxes and groups


def test_boxes_and_words_in_one_run_are_one_group_of_two_with_spans():
    n = Native()
    n.text(60, 100, "Plec:", w=30)
    rid = n.text(250, 100, "❑ pies ❑ suka", w=120)
    pm = model(n.page())
    out = find(pm, STRICT)
    assert _kinds(out) == ["choice_group"]
    g = tops(out)[0]
    assert g.label.text == "Plec" and g.label.how == "question"
    assert [o.text for o in g.options] == ["pies", "suka"]
    marks = [c for c in out.candidates if c.kind == "box"]
    assert [(s.run, s.start, s.end) for m in marks for s in m.spans] == [(rid, 0, 1), (rid, 7, 8)]
    assert [(s.start, s.end) for o in g.options for s in o.spans] == [(2, 6), (9, 13)]
    assert [o.mark for o in g.options] == [m.id for m in marks] and all(m.group == g.id for m in marks)
    _covered(out, pm)


def test_a_ruled_line_separates_two_groups_and_two_options_of_three_carry_a_blank():
    n = Native()
    n.text(60, 100, "Plec:", w=30)
    n.text(250, 100, "❑ pies", w=40)
    n.text(400, 100, "❑ suka", w=40)
    n.hline(240, 540, 116)
    n.text(60, 146, "Sposob oznakowania:", w=100)
    n.text(250, 123, "❑ mikroprocesor", w=80)
    n.text(333, 123, DOTS, w=150)
    n.text(250, 146, "❑ tatuaz", w=45)
    n.text(298, 146, DOTS, w=180)
    n.text(250, 169, "❑ brak", w=35)
    pm = model(n.page())
    out = find(pm, STRICT)
    groups = [c for c in out.candidates if c.kind == "choice_group"]
    assert [[o.text for o in g.options] for g in groups] == [["pies", "suka"], ["mikroprocesor", "tatuaz", "brak"]]
    assert [g.label.text for g in groups] == ["Plec", "Sposob oznakowania"]
    assert [o.blank is not None for o in groups[1].options] == [True, True, False]
    kinds = {c.id: c.kind for c in out.candidates}
    assert {kinds[o.blank] for o in groups[1].options if o.blank} == {"leader"}
    _covered(out, pm)


def test_the_square_character_in_a_flow_paragraph_is_a_box():
    pm = model(flow("Poczta tradycyjna - na ktory adres kierowac korespondencje\n□ adres siedziby klubu\n□ inny adres",
                    "Dane kontaktowe klubu", "□ Dane pelnomocnika klubu sportowego"), fmt="docx")
    out = find(pm, STRICT)
    assert _kinds(out) == ["choice_group", "box"]
    g, lone = tops(out)
    assert [o.text for o in g.options] == ["adres siedziby klubu", "inny adres"]
    assert g.label.text.startswith("Poczta tradycyjna") and g.label.spans and not g.label.runs
    assert lone.label.text == "Dane pelnomocnika klubu sportowego"
    assert sum(c.kind == "box" for c in out.candidates) == 3
    _covered(out, pm)


def test_empty_box_bullet_crossed_box_and_eleven_cells_are_one_group_and_one_field():
    """The cheapest test of the package: one choice group (not four fields) and one PESEL field."""
    n = Native()
    n.text(60, 100, "Czy wnioskodawca jest wlascicielem psa?", w=220)
    n.text(60, 120, "☐ tak", w=30)
    n.text(60, 136, "• dotyczy tylko osob fizycznych", w=170)
    n.text(60, 152, "☒ nie", w=30)
    n.text(60, 200, "PESEL", w=32)
    for k in range(11):
        n.rect(100 + 15 * k, 196, 15, 18)
    pm = model(n.page())
    out = find(pm, STRICT)
    assert _kinds(out) == ["choice_group", "comb"]
    g, comb = tops(out)
    assert [o.text for o in g.options] == ["tak", "nie"] and g.label.text.startswith("Czy wnioskodawca")
    assert comb.cells == 11 and comb.label.text == "PESEL"
    _covered(out, pm)


def test_drill_7_inne_jakie_next_to_a_bullet_is_one_option_with_a_text_blank():
    pm = model(flow("Rodzaj zwierzecia:", "□ pies", "□ kot", "• □ inne (jakie?) " + DOTS,
                    "• pouczenie: wniosek sklada sie w urzedzie"), fmt="docx")
    out = find(pm, STRICT)
    groups = [c for c in out.candidates if c.kind == "choice_group"]
    assert len(groups) == 1 and groups[0].label.text == "Rodzaj zwierzecia"
    assert [o.text for o in groups[0].options] == ["pies", "kot", "inne (jakie?)"]     # wording kept, bullet is no option
    blank = next(c for c in out.candidates if c.id == groups[0].options[2].blank)
    assert blank.kind == "leader" and blank.label.text == "inne (jakie?)"
    assert [o.blank for o in groups[0].options[:2]] == [None, None]
    _covered(out, pm)


# ---------------------------------------------------------------- negative controls


def test_an_information_sheet_has_no_candidates_and_says_not_a_form():
    pm = model(flow("INFORMACJA O GODZINACH PRACY URZEDU", "Urzad jest czynny od poniedzialku do piatku...",
                    "Kasa przyjmuje wplaty do godziny 15."), fmt="docx")
    out = find(pm, STRICT)
    assert out.candidates == [] and [w.code for w in out.warnings] == ["NOT_A_FORM"]
    _covered(out, pm)
    assert [w.code for w in find(model(Page(number=1, origin="flow")), STRICT).warnings] == ["NOT_A_FORM"]


def test_an_instruction_with_ticked_example_boxes_is_not_a_group():
    pm = model(flow("1. Pola wyboru oznaczaj ☒ lub ☑.", "2. WYPELNIJ WIELKIMI LITERAMI.", "Imie: " + DOTS), fmt="docx")
    out = find(pm, STRICT)
    assert _kinds(out) == ["leader"] and _labels(out) == ["Imie"]
    assert [out.roles[r] for r in ("f1r0", "f1r1")] == ["instruction", "instruction"]

    n = Native()                                                # the same, with the example boxes drawn
    n.text(215, 300, "2. Pola wyboru oznaczaj", w=105)
    n.rect(323, 297, 13, 13)
    n.text(338, 300, "lub", w=13)
    n.rect(354, 297, 13, 13)
    n.text(369, 300, ".", w=3)
    assert find(model(n.page()), STRICT).candidates == []


def test_the_data_protection_clause_yields_no_candidate_and_ends_at_the_signature_line():
    pm = model(flow("Imie i nazwisko: " + DOTS, "KLAUZULA INFORMACYJNA",
                    "Administratorem Panstwa danych osobowych jest Wojt Gminy, tel. " + DOTS + " (sekretariat).",
                    "□ Dane beda przetwarzane w celu rozpatrzenia wniosku.", DOTS, "(podpis wnioskodawcy)"), fmt="docx")
    out = find(pm, STRICT)
    assert _kinds(out) == ["leader", "signature"]
    assert [out.roles[f"f1r{i}"] for i in (1, 2, 3)] == ["clause"] * 3


# ---------------------------------------------------------------- order, sections, owners (drills 3, 4, 10)


def test_drill_3_two_columns_keep_label_box_and_owner_together_pdf():
    def draw(c):  # noqa: ANN001
        c.setFont("Helvetica-Bold", 12)
        c.drawString(150, 780, "WNIOSEK O WYDANIE ZASWIADCZENIA")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, 730, "1. WNIOSKODAWCA")
        c.drawString(320, 730, "2. PELNOMOCNIK")
        c.setFont("Helvetica", 10)
        c.drawString(50, 705, "PESEL")
        c.drawString(320, 705, "PESEL")
        for k in range(11):
            c.rect(90 + 14 * k, 700, 14, 18)
            c.rect(360 + 14 * k, 700, 14, 18)

    pm = pdf(draw)
    out = find(pm, STRICT)
    assert [(c.kind, c.cells) for c in out.candidates] == [("comb", 11), ("comb", 11)]
    titles = {s.id: (s.number, s.title) for s in out.sections}
    runs = pm.run_index()
    left, right = sorted(out.candidates, key=lambda c: c.box[0])
    assert titles[left.section] == ("1", "WNIOSKODAWCA") and titles[right.section] == ("2", "PELNOMOCNIK")
    assert runs[left.label.runs[0]][1].box[0] < 100 and left.box[0] < 100       # label, box and owner together
    assert runs[right.label.runs[0]][1].box[0] > 300 and right.box[0] > 300
    assert not [w for w in out.warnings if w.code == "LOW_CONFIDENCE"]


def test_drill_4_text_boxes_in_another_file_order_keep_their_sections():
    items = [(60, 100, "1. DANE WNIOSKODAWCY", True, 150), (60, 125, "Imie:", False, 30), (95, 125, DOTS, False, 200),
             (60, 150, "2. DANE PELNOMOCNIKA", True, 150), (60, 175, "Nazwisko:", False, 50), (115, 175, DOTS, False, 200)]

    def membership(order: list[int]) -> tuple[list[str], dict[str, str]]:
        runs = [Run(id=f"r{i}", text=items[i][2], box=(items[i][0], items[i][1], items[i][0] + items[i][4], items[i][1] + 10),
                    size=10.0, bold=items[i][3], anchor=f"p[{k}]") for k, i in enumerate(order)]
        out = find(model(Page(number=1, width=595.0, height=842.0, origin="native", runs=runs), fmt="docx"), STRICT)
        titles = {s.id: s.title for s in out.sections}
        return [s.title for s in out.sections], {c.label.text: titles[c.section] for c in out.candidates}

    straight = membership(list(range(6)))
    assert straight == (["DANE WNIOSKODAWCY", "DANE PELNOMOCNIKA"],
                        {"Imie": "DANE WNIOSKODAWCY", "Nazwisko": "DANE PELNOMOCNIKA"})
    shuffled = list(range(6))
    random.Random(4).shuffle(shuffled)
    assert shuffled != list(range(6))
    assert membership(shuffled) == straight and membership(list(reversed(range(6)))) == straight


def test_a_section_printed_later_in_the_file_but_higher_on_the_page_comes_first():
    n = Native()
    n.text(63, 304, "B", w=7, bold=True)
    n.text(82, 300, "INFORMACJA O PSIE", w=120, bold=True)
    n.text(60, 330, "Rasa psa:", w=45)
    n.text(110, 330, DOTS, w=200)
    n.text(63, 100, "A", w=7, bold=True)
    n.text(82, 100, "DANE WNIOSKODAWCY", w=140, bold=True)
    n.text(60, 130, "Imie i nazwisko:", w=75)
    n.text(140, 130, DOTS, w=200)
    pm = model(n.page())
    out = find(pm, STRICT)
    assert [(s.number, s.title) for s in out.sections] == [("A", "DANE WNIOSKODAWCY"), ("B", "INFORMACJA O PSIE")]
    assert {c.label.text: c.section for c in out.candidates} == {"Imie i nazwisko": "s1", "Rasa psa": "s2"}
    assert out.order.index(out.sections[0].runs[0]) < out.order.index(out.sections[1].runs[0])
    _covered(out, pm)


def test_numbered_headings_make_a_tree_and_the_first_place_without_text_answers_to_its_heading():
    n = Native()
    n.text(60, 100, "2. Dane wnioskodawcy", w=120, bold=True)
    n.text(60, 120, "2.1. Uzasadnienie wniosku", w=140, bold=True)
    n.rect(60, 140, 400, 60)
    out = find(model(n.page()), STRICT)
    assert [(s.number, s.parent) for s in out.sections] == [("2", None), ("2.1", "s1")]
    c = out.candidates[0]
    assert (c.kind, c.section, c.label.how, c.label.text, c.label.runs) == ("cell", "s2", "header", "Uzasadnienie wniosku", [])
    assert c.conf.label == 0.5 and not out.warnings


def test_drill_10_a_table_that_continues_on_the_next_page_keeps_headers_and_section():
    head = ["Imie psa", "Rasa", "Wiek"]
    pm = model(flow_table(1, "tbl[0]", [head, ["", "", ""], ["", "", ""]], before=("WYKAZ POSIADANYCH PSOW",)),
               flow_table(2, "tbl[1]", [["", "", ""], ["", "", ""]]), fmt="docx")
    out = find(pm, STRICT)
    assert _kinds(out) == ["cell"] * 12                        # not a comb of three, not two tables
    assert [c.label.text for c in out.candidates] == head * 4
    assert {c.label.how for c in out.candidates} == {"header"}
    assert {c.section for c in out.candidates} == {"s1"} and [c.page for c in out.candidates] == [1] * 6 + [2] * 6
    _covered(out, pm)


def test_a_table_of_empty_cells_only_is_one_comb():
    pm = model(flow_table(1, "tbl[0]", [[""] * 26], before=("Nr rachunku",)), fmt="docx")
    out = find(pm, STRICT)
    assert [(c.kind, c.cells) for c in out.candidates] == [("comb", 26)]


def test_a_rule_that_fails_is_a_warning_unless_strict(monkeypatch):
    import app.find as pkg

    def boom(*_a, **_k):  # noqa: ANN002, ANN003
        raise RuntimeError("synthetic")

    monkeypatch.setattr(pkg, "run", boom)
    pm = model(flow("Imie: " + DOTS), fmt="docx")
    out = find(pm)
    assert out.candidates == [] and [w.code for w in out.warnings] == ["UNREADABLE_PART"]
    _covered(out, pm)
