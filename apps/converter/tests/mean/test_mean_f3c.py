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

def _attach_list() -> Native:
    n = Native()
    n.text(50, 40, "Załącznik nr 2 do Regulaminu korzystania z sal", 300)
    n.text(70, 70, "WNIOSEK O ZAJECIE TERENU", 300, bold=True)
    n.text(50, 100, "Nazwa ulicy", 80)
    n.text(140, 100, DOTS, 200)
    n.text(50, 130, "4. Załączniki do wniosku:", 150)
    items = [("- Plan sytuacyjny w skali 1:500 z zaznaczeniem granic i podaniem", "wymiarow zajecia."),
             ("- Harmonogram robot.", None),
             ("- Projekt organizacji ruchu, jeżeli zajecie terenu wplywa na ruch.", None),
             ("- Informacja o zabezpieczeniu robot, jeżeli nie jest wymagany projekt organizacji ruchu.", None),
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
