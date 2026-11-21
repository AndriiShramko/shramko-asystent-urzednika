"""WP-F3c, matter quality round 2 (audit round 2): choice groups, attachments, no fragments. Papers built from code
with synthetic words; each rule has a negative case."""
from __future__ import annotations

from app.find import find
from app.mean import understand
from tests.find.find_builders import DOTS, Native, model
from tests.mean.test_mean_core import Paper


def _run(n: Native):
    m = model(n.page())
    return understand(m, find(m))


def _fields(b) -> dict:
    return {f.label: f for s in b.matter for f in s.fields}


# -- item 1 (T1): choice groups -----------------------------------------------------------------------------------

def _strike(note: bool, star_apart: bool = True) -> Native:
    n = Native()
    n.text(70, 60, "WNIOSEK O ZEZWOLENIE", 300, bold=True)
    if star_apart:   # a PDF writes the footnote star as a run of its own
        n.text(50, 120, "Prosze o wydanie zgody na sadzenie/podlewanie", 250)
        n.text(301, 120, "*", 4)
    else:
        n.text(50, 120, "Prosze o wydanie zgody na sadzenie/podlewanie*", 255)
    n.text(50, 140, "Nazwa ogrodu", 80)
    n.text(140, 140, DOTS, 200)
    if note:
        n.text(50, 700, "* niepotrzebne skreślić", 150)
    return n


def test_a_starred_alternative_split_from_its_star_is_one_radio() -> None:
    got = _fields(_run(_strike(note=True)))
    radios = [f for f in got.values() if f.type == "RADIO"]
    assert [f.options for f in radios] == [["sadzenie", "podlewanie"]]


def test_without_the_strike_out_note_slashes_are_no_choice() -> None:
    got = _fields(_run(_strike(note=False)))
    assert not [f for f in got.values() if f.type == "RADIO"]


def test_two_starred_alternatives_joined_by_lub_are_one_choice_of_two_phrases() -> None:
    n = Native()
    n.text(70, 60, "WNIOSEK O ZEZWOLENIE", 300, bold=True)
    n.text(50, 120, "na hodowanie ogara/ogarow", 150)
    n.text(201, 120, "*", 4)
    n.text(50, 133, "lub mieszanca ogara/mieszancow ogarow", 200)
    n.text(251, 133, "*", 4)
    n.text(50, 700, "* niepotrzebne skreślić", 150)
    radios = [f for f in _fields(_run(n)).values() if f.type == "RADIO"]
    assert [f.options for f in radios] == [["ogara/ogarow", "mieszanca ogara/mieszancow ogarow"]]


def _declared(label: str) -> Native:
    n = Native()
    n.text(70, 60, "DEKLARACJA", 300, bold=True)
    n.text(50, 100, "D. OSWIADCZENIE", 200, bold=True)
    n.text(60, 120, "□", 8)
    n.text(75, 120, label, 400)
    n.text(75, 132, "w ktorym kompostuje bioodpady.", 200)
    return n


def test_one_box_beside_oswiadczam_is_a_checkbox_declaration_with_the_whole_sentence() -> None:
    got = [f for f in _fields(_run(_declared("Oświadczam, że nieruchomosc ma kompostownik,"))).values() if f.type == "CHECKBOX"]
    assert len(got) == 1 and got[0].required is False
    assert got[0].label.endswith("kompostuje bioodpady") and got[0].label.startswith("Oświadczam")


def test_one_box_with_another_label_still_waits_for_the_official() -> None:
    b = _run(_declared("Nieruchomosc ma kompostownik,"))
    assert not [f for f in _fields(b).values() if f.type == "CHECKBOX"]
    assert any(w.code == "AMBIGUOUS_GROUP" for w in b.warnings)


def _kinds(colon_line: bool) -> Native:
    n = Native()
    n.text(70, 60, "WNIOSEK O NAGRODE", 300, bold=True)
    n.text(50, 100, "Wskaz rodzaje uprawianych sportow", 250)
    y = 118
    for opt in ("druzynowy", "indywidualny", "mieszany"):
        n.text(60, y, "□ " + opt, 120)
        y += 16
    n.text(50, y, "Sporty:" if colon_line else "Sporty", 60)
    y += 16
    for opt in ("plywanie", "bieganie", "wioslarstwo", "szermierka"):
        n.text(60, y, "□ " + opt, 120)
        y += 16
    return n


def test_a_line_ending_in_a_colon_between_options_splits_the_group_in_two() -> None:
    choices = [f for f in _fields(_run(_kinds(True))).values() if f.options]
    assert [len(f.options) for f in choices] == [3, 4]
    assert choices[1].label == "Sporty"


def test_without_the_colon_line_the_group_stays_one() -> None:
    choices = [f for f in _fields(_run(_kinds(False))).values() if f.options]
    assert [len(f.options) for f in choices] == [7]


def _applicant_group(options: list[str]):
    p = Paper()
    p.text("WNIOSEK O NAGRODĘ", bold=True)
    s = p.heading("Wnioskodawca", number="1")
    p.group("Wnioskodawca", options, section=s)
    p.blank("Nazwa sali", section=s)
    return p.brief()


def test_boxes_under_the_applicant_heading_that_are_not_kinds_of_applicant_are_a_question_of_the_matter() -> None:
    got = _fields(_applicant_group(["Burmistrz Miasta", "Klub sportowy"]))
    assert got["Wnioskodawca"].type == "RADIO" and got["Wnioskodawca"].options == ["Burmistrz Miasta", "Klub sportowy"]


def test_boxes_that_name_kinds_of_applicant_stay_with_the_standard_pages() -> None:
    got = _fields(_applicant_group(["Klub sportowy", "Spółdzielnia mieszkaniowa"]))
    assert "Wnioskodawca" not in got


# -- item 2 (T2): attachments named in running text ---------------------------------------------------------------

def _attach_list(info_if: str = "jeżeli nie jest wymagany projekt organizacji ruchu.") -> Native:
    n = Native()
    n.text(50, 40, "Załącznik nr 2 do Regulaminu korzystania z sal", 300)
    n.text(70, 70, "WNIOSEK O ZAJECIE TERENU", 300, bold=True)
    n.text(50, 100, "Nazwa ulicy", 80)
    n.text(140, 100, DOTS, 200)
    n.text(50, 130, "4. Załączniki do wniosku:", 150)
    items = [("- Plan sytuacyjny w skali 1:500 z zaznaczeniem granic i podaniem", "wymiarow zajecia."),
             ("- Harmonogram robot.", None),
             ("- Projekt organizacji ruchu, jeżeli zajecie terenu wplywa na ruch.", None),
             (f"- Informacja o zabezpieczeniu robot, {info_if}", None),
             ("- Pełnomocnictwo, gdy wystepuje pelnomocnik.", None)]
    y = 145
    for first, more in items:
        n.text(55, y, first, 450)
        y += 12
        if more:
            n.text(70, y, more, 200)
            y += 12
    n.text(50, y + 20, "Do wniosku można dołączyć dyplomy sportowe.", 300)
    n.text(50, y + 40, "Oswiadczam, ze zwierze jest zaszczepione – w załączeniu kopia zaswiadczenia.", 400)
    return n


def test_every_item_of_an_attachments_list_and_of_a_sentence_is_an_upload_with_its_own_label() -> None:
    b = _run(_attach_list())
    own = {a.label: a for a in b.attachments if a.covered_by is None}
    assert own["Plan sytuacyjny w skali 1:500 z zaznaczeniem granic i podaniem wymiarow zajecia"].required is True
    assert own["Harmonogram robot"].required is True
    assert own["Dyplomy sportowe"].required is False
    assert own["Kopia zaswiadczenia"].required is True
    assert [a.covered_by for a in b.attachments if a.label.startswith("Pełnomocnictwo")] == ["standard/pelnomocnictwo"]


def test_an_item_wanted_only_without_the_other_makes_an_either_or_pair() -> None:
    b = _run(_attach_list())
    choice = [f for f in _fields(b).values() if f.type == "RADIO"]
    assert len(choice) == 1 and choice[0].options == ["Projekt organizacji ruchu", "Informacja o zabezpieczeniu robot"]
    shown = {a.label: a.show_if for a in b.attachments if a.show_if is not None}
    assert {c.is_ for c in shown.values()} == set(choice[0].options) and {c.field for c in shown.values()} == {choice[0].key}


def test_a_negation_that_does_not_say_the_other_item_is_not_required_is_no_either_or() -> None:
    """Critic finding: any "nie" in the condition plus two shared word stems made an either-or pair."""
    b = _run(_attach_list("jeżeli projekt organizacji ruchu nie przewiduje zamknięcia drogi."))
    assert [f for f in _fields(b).values() if f.type == "RADIO"] == []
    assert all(a.show_if is None for a in b.attachments)


def _one_line_paper(line: str):
    n = Native()
    n.text(70, 60, "WNIOSEK O WYNAJEM", 300, bold=True)
    n.text(50, 100, "Nazwa sali", 80)
    n.text(140, 100, DOTS, 200)
    n.text(50, 140, line, 400)
    return _run(n)


def test_the_item_before_the_verb_is_the_upload_not_the_words_after_it() -> None:
    """Critic round 2: "Kopię dowodu należy załączyć do wniosku" made an upload called "Do wniosku"."""
    got = [(a.label, a.required) for a in _one_line_paper("Kopię dowodu należy załączyć do wniosku.").attachments]
    assert got == [("Kopię dowodu", True)]


def test_a_condition_naming_another_item_does_not_cover_this_one_and_a_ban_is_no_upload() -> None:
    cond = _one_line_paper("Kopię umowy należy załączyć do wniosku, jeżeli pełnomocnictwo nie jest wymagane.")
    assert [(a.label, a.covered_by) for a in cond.attachments] == [("Kopię umowy", None)]
    ban = _one_line_paper("Nie można dołączyć kopii dowodu.")
    assert ban.attachments == []


def test_a_regulation_annex_line_and_a_bare_attachments_heading_give_no_upload() -> None:
    n = Native()
    n.text(50, 40, "Załącznik nr 2 do Regulaminu korzystania z sal", 300)
    n.text(70, 70, "WNIOSEK O WYNAJEM", 300, bold=True)
    n.text(50, 100, "Nazwa sali", 80)
    n.text(140, 100, DOTS, 200)
    n.text(50, 130, "Załączniki", 80)
    n.text(50, 150, "Wniosek nalezy zlozyc w sekretariacie.", 300)
    b = _run(n)
    assert b.attachments == [] and "Regulaminu" not in (b.title.value or "")


# -- item 3 (T3): sentence tails, stubs, headings and printed amounts are no fields ------------------------------------

def _left(b) -> list[str]:
    return [d.reason for d in b.dispositions if d.fate == "LEFT_OUT"]


def test_a_printed_rate_is_text_of_the_form_not_a_field() -> None:
    p = Paper()
    p.text("WNIOSEK O ZWOLNIENIE", bold=True)
    p.blank("15 zł 00 gr", how="above")
    p.blank("Stawka 15 zł", how="left")
    b = p.brief()
    assert list(_fields(b)) == ["Stawka 15 zł"] and _left(b) == ["EXPLANATION"]


def _tail(above: str) -> Paper:
    p = Paper()
    p.text("WNIOSEK O ZGODĘ", bold=True)
    p.text(above)
    p.blank("akceptuję wszystkie jego postanowienia.", how="above")
    p.text("Data")
    return p


def test_the_last_line_of_a_sentence_is_no_label_the_caption_under_the_blank_is() -> None:
    b = _tail("Oświadczam, że zapoznałem się z regulaminem przyznawania nagród i").brief()
    assert list(_fields(b)) == ["Data"] and _fields(b)["Data"].type == "DATEPICKER"
    assert _fields(b)["Data"].evidence[0].quote == "Data"


def test_a_short_complete_caption_ending_in_a_full_stop_stays_a_label() -> None:
    b = _tail("Dane osoby składającej oświadczenie").brief()      # four words: no sentence that goes on
    assert list(_fields(b)) == ["Akceptuję wszystkie jego postanowienia."]


def test_a_stub_of_fewer_than_four_letters_takes_the_caption_under_the_blank_when_there_is_one() -> None:
    p = Paper()
    p.text("WNIOSEK O ZEZWOLENIE", bold=True)
    p.blank("Mui", how="above")
    p.text("nazwa drogi oraz jej nr")
    p.blank("Ul.", how="left")
    b = p.brief()
    assert list(_fields(b)) == ["Nazwa drogi oraz jej nr", "Ul."]
    alone = Paper()
    alone.text("WNIOSEK O ZEZWOLENIE", bold=True)
    alone.blank("Cel", how="above")      # a short word with no caption is still a label: the paper may mean it
    assert list(_fields(alone.brief())) == ["Cel"]


def test_tj_before_a_blank_with_dni_after_it_is_a_count_of_days() -> None:
    p = Paper()
    p.text("WNIOSEK O ZEZWOLENIE", bold=True)
    p.blank("tj.", kind="blank_in_sentence", how="sentence")
    p.text("dni, zgodnie z załączonym harmonogramem.")
    f = _fields(p.brief())["Liczba dni"]
    assert f.type == "NUMBER" and f.concept == "count"


def _band(gap: float) -> Native:
    n = Native()
    n.text(50, 100, "E. OŚWIADCZENIE O WYSOKOŚCI OPŁATY", 300, bold=True)
    n.rect(50, 110 + gap, 120, 11)
    n.text(50, 160, "Opłata stanowi sumę iloczynów ilości gospodarstw domowych oraz stawki.", 400)
    return n


def test_a_strip_flush_under_a_heading_is_the_edge_of_the_heading_not_a_place_to_write() -> None:
    b = _run(_band(0))
    assert not b.matter and _left(b) == ["EXPLANATION"]


def test_a_box_with_room_under_a_heading_keeps_the_heading_as_its_question() -> None:
    n = Native()
    n.text(50, 100, "E. UZASADNIENIE", 300, bold=True)
    n.rect(50, 125, 400, 60)
    b = _run(n)
    assert [f.label for s in b.matter for f in s.fields] == ["Uzasadnienie"]


# -- item 5 (T5, T9): a lower-case label continues the line above; types from the paper's own hints ------------------

def _lead(above: str, bold: bool = False) -> Paper:
    p = Paper()
    p.text("WNIOSEK O STYPENDIUM", bold=True)
    p.text(above, bold=bold)
    p.blank("ocenie wniosku", how="above")
    return p


def test_a_lower_case_label_takes_the_body_line_above_it() -> None:
    b = _lead("Opisz osiągnięcia sportowe kandydata, które będą brane pod uwagę przy").brief()
    (f,) = _fields(b).values()
    assert f.label == "Opisz osiągnięcia sportowe kandydata, które będą brane pod uwagę przy ocenie wniosku"
    assert f.evidence[0].quote == f.label and len(f.evidence[0].runs) == 2


def test_a_short_line_a_line_in_capitals_or_a_caption_of_a_blank_above_is_not_taken() -> None:
    assert list(_fields(_lead("Dane wnioskodawcy").brief())) == ["Ocenie wniosku"]
    assert list(_fields(_lead("OSIĄGNIĘCIA SPORTOWE KANDYDATA, KTÓRE BĘDĄ BRANE POD UWAGĘ PRZY").brief())) == ["Ocenie wniosku"]
    p = Paper()
    p.text("WNIOSEK O STYPENDIUM", bold=True)
    p.blank("Klub", how="left")
    p.text("nazwa przedsiębiorstwa lub osoby fizycznej")
    p.blank("ocenie wniosku", how="above")
    assert list(_fields(p.brief())) == ["Klub", "Ocenie wniosku"]


def test_a_row_of_a_table_of_counts_takes_the_numbered_heading_and_the_line_of_its_row_header() -> None:
    n = Native()
    n.text(50, 100, "36. Liczba gospodarstw domowych zajmujących", 200, bold=True)
    n.text(68, 112, "lokale mieszkalne o powierzchni użytkowej", 180)
    n.text(68, 124, "nie przekraczającej 45 m²", 110)
    n.text(200, 124, DOTS, 120)
    f = next(iter(_fields(_run(n)).values()))
    assert f.label == "Liczba gospodarstw domowych zajmujących lokale mieszkalne o powierzchni użytkowej nie przekraczającej 45 m²"
    assert f.type == "NUMBER"


def test_types_from_the_papers_own_hints() -> None:
    p = Paper()
    p.text("WNIOSEK O ZEZWOLENIE", bold=True)
    p.blank("Termin zakończenia (DD-MM-RRRR)", how="left")
    p.blank("Czas trwania w dni", how="left")
    p.blank("Dni tygodnia", how="left")
    f = _fields(p.brief())
    assert f["Termin zakończenia"].type == "DATEPICKER" and f["Czas trwania w dni"].type == "NUMBER"
    assert f["Dni tygodnia"].type == "TEXT_FIELD"


# -- item 4 (T4): a caption under a blank belongs to the blank above ---------------------------------------------------

def test_a_second_dotted_line_with_only_a_caption_in_slashes_is_the_same_field_with_a_hint() -> None:
    p = Paper()
    p.text("WNIOSEK O ZEZWOLENIE", bold=True)
    p.blank("w celu wykonania", how="leader")
    p.blank("/ rodzaj robót i sposób wykonania /", caption=True, how="leader")
    b = p.brief()
    (f,) = _fields(b).values()
    assert f.type == "TEXTAREA" and f.hint == "rodzaj robót i sposób wykonania"
    assert [d.why for d in b.dispositions if d.fate == "MERGED"] == ["LINE_BLOCK"]


def test_a_caption_without_brackets_or_under_a_blank_of_its_own_label_makes_no_merge() -> None:
    p = Paper()
    p.text("WNIOSEK O ZEZWOLENIE", bold=True)
    p.blank("Cel", how="leader")
    p.blank("rodzaj robót", caption=True, how="leader")
    p.blank("Adres", how="left")
    p.blank("/ nr domu /", caption=True, how="left")
    assert len(_fields(p.brief())) == 4


def test_a_caption_in_slashes_right_under_a_blank_is_its_hint() -> None:
    p = Paper()
    p.text("WNIOSEK O ZEZWOLENIE", bold=True)
    p.blank("Cel wynajęcia", how="leader")
    p.text("/ np. wesele, urodziny /")
    assert _fields(p.brief())["Cel wynajęcia"].hint == "np. wesele, urodziny"
