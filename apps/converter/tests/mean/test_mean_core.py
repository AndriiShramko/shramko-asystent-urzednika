"""The understanding step on papers built from code (WP-F4, stage core). Synthetic words only: the offices and
the places are invented. The finder's output is written by hand here, so each rule is tested on exactly the
candidates it reads; one test at the end goes through the real finder."""
from __future__ import annotations

import json

import pytest

from app import gate, lexicon
from app.compose import compose
from app.find import find
from app.mean import understand
from app.model.brief import Brief, check_paper_evidence
from app.model.candidate import Candidate, ChoiceOption, Confidence, FinderOutput, Label, Section
from app.model.common import InputRef
from app.model.page import Page, PageModel, Run, Source

STRICT = {"strict": True}
DOTS = "." * 30
STRIKE = "* niepotrzebne skreślić"


class Paper:
    """A flow document and the finder's reading of it, written element by element in reading order."""

    def __init__(self) -> None:
        self.pages: list[list[Run]] = [[]]
        self.roles: dict[str, str] = {}
        self.sections: list[Section] = []
        self.cands: list[Candidate] = []
        self.n = 0

    def _run(self, text: str, bold: bool = False, size: float = 11.0) -> str:
        self.n += 1
        rid = f"r{self.n}"
        self.pages[-1].append(Run(id=rid, text=text, anchor=f"p[{self.n}]", size=size, bold=bold))
        return rid

    def new_page(self) -> None:
        self.pages.append([])

    def text(self, text: str, role: str = "body", **look) -> str:
        rid = self._run(text, **look)
        self.roles[rid] = role
        return rid

    def heading(self, title: str, number: str | None = None, parent: str | None = None, **look) -> str:
        rid = self._run(f"{number} {title}" if number else title, bold=True, **look)
        sid = f"s{len(self.sections) + 1}"
        kw = {k: v for k, v in {"number": number, "parent": parent}.items() if v is not None}
        self.sections.append(Section(id=sid, page=len(self.pages), title=title, runs=[rid], **kw))
        return sid

    def _cand(self, kind: str, label: str | None, how: str, runs: list[str], label_runs: list[str], **kw) -> str:
        cid = f"c{len(self.cands) + 1}"
        kw = {k: v for k, v in kw.items() if v is not None}
        if label is not None:
            kw["label"] = Label(text=label, runs=label_runs, how=how, margin=0.8)
        self.cands.append(Candidate(id=cid, kind=kind, page=len(self.pages), anchor=f"p[{self.n}]", runs=runs,
                                    conf=Confidence(geometry=0.95, label=0.8, text=1.0), **kw))
        return cid

    def blank(self, label: str | None, kind: str = "leader", section: str | None = None, how: str = "left", caption: bool = False,
              footnotes: tuple[str, ...] = (), **kw) -> str:
        """A label and the dots after it; `caption`: the dots first, the label under them."""
        if caption or label is None:
            place = self._run(DOTS)
            lab = [self._run(label)] if label is not None else []
        else:
            lab = [self._run(label)]
            place = self._run(DOTS)
        return self._cand(kind, label, how, [place], lab, section=section, footnotes=list(footnotes) or None, **kw)

    def group(self, question: str, options: list[str], section: str | None = None, blank_after: tuple[str, ...] = ()) -> str:
        q = self._run(question)
        gid = f"c{len(self.cands) + 1}"
        self.cands.append(None)   # type: ignore[arg-type]  # the group's place in the finder's order
        opts = []
        for text in options:
            run = self._run(text)
            box = self._cand("box", None, "left", [], [], section=section, group=gid)
            self.cands[-1] = self.cands[-1].model_copy(update={"anchor": f"p[{self.n}]"})
            after = self.blank(text, section=section, how="leader") if text in blank_after else None
            opts.append(ChoiceOption(text=text, runs=[run], mark=box, **({"blank": after} if after else {})))
        index = int(gid[1:]) - 1
        self.cands[index] = Candidate(id=gid, kind="choice_group", page=len(self.pages), anchor=f"p[{self.n}]", options=opts,
                                      label=Label(text=question, runs=[q], how="question", margin=0.7), section=section,
                                      conf=Confidence(geometry=0.9, label=0.7, text=1.0),
                                      **({} if section is None else {}))
        return gid

    def build(self) -> tuple[PageModel, FinderOutput]:
        pages = [Page(number=i, origin="flow", runs=runs) for i, runs in enumerate(self.pages, 1)]
        pm = PageModel(source=Source(sha256="0" * 64, format="docx", reader="test.built", pages=len(pages)), pages=pages)
        fo = FinderOutput(input=InputRef(sha256="0" * 64, format="docx"), order=[r.id for runs in self.pages for r in runs],
                          sections=self.sections, candidates=self.cands, roles=self.roles)
        return pm, fo

    def brief(self) -> Brief:
        pm, fo = self.build()
        brief = understand(pm, fo, STRICT)
        assert [d.candidate for d in brief.dispositions] == [c.id for c in fo.candidates], "one disposition per candidate"
        Brief.model_validate(brief.to_dict())
        return brief


def fields(brief: Brief) -> dict[str, object]:
    return {f.key: f for s in brief.matter for f in s.fields}


def fates(brief: Brief) -> dict[str, str]:
    return {d.candidate: d.fate for d in brief.dispositions}


def hall(office: str = "WÓJT GMINY ZMYŚLONA", title: tuple[str, ...] = ("WNIOSEK", "o", "wynajęcie/użyczenie* świetlicy wiejskiej")) -> Paper:
    """A request to rent a village hall: the head block, the addressee, a three-line title, the matter."""
    p = Paper()
    p.text("Załącznik nr 2 do Regulaminu składania wniosków o świetlice", role="page_furniture")
    p.blank("(imię i nazwisko wnioskodawcy)", caption=True, how="leader")
    p.blank("(adres zamieszkania)", caption=True, how="leader")
    p.blank("(nr telefonu)", caption=True, how="leader", footnotes=("1",))
    p.blank("(miejscowość i data)", caption=True, how="leader")
    p.text(office, bold=True)
    p.text("Zmyślona 8", bold=True)
    for line in title:
        p.text(line, bold=True)
    p.blank("Proszę o wynajem/użyczenie* świetlicy wiejskiej w", how="leader")
    p.blank("wraz z wyposażeniem w terminie od", kind="blank_in_sentence", how="sentence")
    p.blank("do", kind="blank_in_sentence", how="sentence")
    p.blank("1. Cel wynajęcia świetlicy:", how="leader")
    p.text("( rodzaj uroczystości, np. wesele, urodziny, zabawa itp.)")
    p.blank("2. Przewidywana ilość uczestników :", how="leader", footnotes=("1",))
    p.text("4. Jednocześnie oświadczam, że")
    p.text("(w przypadku innej osoby niż wnioskodawca, zbiorcze oświadczenie tej osoby")
    p.text("załączyć do wniosku)")
    p.text(":")
    p.text("1) zapoznałem/am się z warunkami wynajmu świetlicy wiejskiej,", role="note")
    p.text("2) w czasie najmu odpowiadam za ład i porządek w świetlicy oraz na terenie przyległym do", role="note")
    p.text("świetlicy.")
    p.blank("(czytelny podpis wnioskodawcy)", kind="signature", caption=True, how="leader")
    p.text(STRIKE, role="note")
    p.text("1 ) D", role="note")
    p.text("ane nieobowiązkowe.", role="note")
    return p


# -- title and addressee (design 6.4.1) -------------------------------------------------------------------------------

def test_title_joins_its_lines_and_keeps_crossed_alternatives_as_lub():
    b = hall().brief()
    assert b.title.status == "stated"
    assert b.title.value == "Wniosek o wynajęcie lub użyczenie świetlicy wiejskiej"
    assert b.title.evidence[0].quote == "WNIOSEK o wynajęcie/użyczenie* świetlicy wiejskiej" and len(b.title.evidence[0].runs) == 3


def test_an_annex_header_never_becomes_the_title():
    b = hall().brief()
    assert "Załącznik" not in b.title.value and "Regulamin" not in b.title.value
    assert any(d.reason == "PAGE_FURNITURE" for d in b.dropped)
    alone = Paper()
    alone.text("Załącznik nr 2 do Regulaminu składania wniosków o świetlice", bold=True)   # bold body text, not even furniture
    alone.blank("Nazwa sali")
    assert alone.brief().title.status == "not_found"


def test_legal_reference_leaves_the_title():
    p = Paper()
    p.text("WNIOSEK", bold=True)
    p.text("o stwierdzenie nadpłaty podatku (Dz. U. z 2025 r. poz. 111)", bold=True)
    p.blank("w kwocie", kind="blank_in_sentence", how="sentence")
    assert p.brief().title.value == "Wniosek o stwierdzenie nadpłaty podatku"


def test_a_body_gives_organ_and_an_office_named_on_two_lines_gives_urzad():
    b = hall().brief()
    assert (b.addressee.status, b.addressee.kind, b.addressee.name) == ("stated", "body", "Wójt Gminy Zmyślona")
    assert b.addressee.evidence[0].quote == "WÓJT GMINY ZMYŚLONA"
    p = Paper()
    p.text("Urząd Gminy")
    p.text("Zmyślona-Kolonia")
    p.text("ul. Wymyślona 57")
    p.text("WNIOSEK O WYDANIE ZAŚWIADCZENIA", bold=True)
    p.blank("Rodzaj zaświadczenia")
    b = p.brief()
    assert (b.addressee.kind, b.addressee.name) == ("office", "Urząd Gminy Zmyślona-Kolonia")
    assert not [w for w in b.warnings if w.code == "ADDRESSEE_CONFLICT"]


def test_two_different_offices_give_addressee_conflict_with_both_quotes():
    p = hall()
    p.new_page()
    p.text("KLAUZULA INFORMACYJNA", role="clause")
    p.text("Administratorem danych jest Urząd Gminy Wymyślin, ul. Polna 1.", role="clause")
    b = p.brief()
    conflicts = [w for w in b.warnings if w.code == "ADDRESSEE_CONFLICT"]
    assert len(conflicts) == 1 and [e.quote for e in conflicts[0].evidence] == ["WÓJT GMINY ZMYŚLONA", "Urząd Gminy Wymyślin"]
    assert b.addressee.name == "Wójt Gminy Zmyślona", "the addressee block wins"
    same = hall()
    same.new_page()
    same.text("Administratorem danych jest Wójt Gminy Zmyślona, a dane przetwarza się w Urzędzie Gminy w Zmyślonej.", role="clause")
    assert not [w for w in same.brief().warnings if w.code == "ADDRESSEE_CONFLICT"]


def test_no_office_on_the_paper_is_not_found():
    p = Paper()
    p.text("WNIOSEK O WPIS", bold=True)
    p.blank("Nazwa sali")
    assert p.brief().addressee.status == "not_found"


# -- the fate of every candidate (design 6.4.3) -----------------------------------------------------------------------

def test_head_block_goes_to_the_standard_signature_and_date_are_left_out_the_rest_is_the_matter():
    b = hall().brief()
    assert list(fates(b).values()) == ["STANDARD", "STANDARD", "STANDARD", "LEFT_OUT", "FIELD", "FIELD", "FIELD", "FIELD", "FIELD", "LEFT_OUT"]
    roles = [d.role for d in b.dispositions if d.fate == "STANDARD"]
    assert roles == ["standard/twoje_dane", "standard/adres", "standard/dane_do_kontaktu"]
    assert [d.reason for d in b.dispositions if d.fate == "LEFT_OUT"] == ["SIGNATURE_AND_DATE", "SIGNATURE_AND_DATE"]
    assert {d.reason for d in b.dropped} >= {"COVERED_BY_STANDARD", "SIGNATURE_AND_DATE", "PAGE_FURNITURE"}


def test_fields_of_the_matter_have_types_labels_hints_and_one_choice_asked_once():
    f = fields(hall().brief())
    choice = f["wynajecie_uzyczenie"]
    assert (choice.type, choice.options, choice.required_basis) == ("RADIO", ["wynajęcie", "użyczenie"], "paper")
    assert sum(x.type == "RADIO" for x in f.values()) == 1, "wynajem/użyczenie* in the sentence is the same choice"
    assert (f["termin_od"].type, f["termin_do"].type, f["termin_do"].label) == ("DATEPICKER", "DATEPICKER", "Termin do")
    goal = f["cel_wynajecia_swietlicy"]
    assert (goal.label, goal.type, goal.hint) == ("Cel wynajęcia świetlicy", "TEXT_FIELD", "rodzaj uroczystości, np. wesele, urodziny, zabawa itp.")
    count = f["przewidywana_ilosc_uczestnikow"]
    assert (count.type, count.concept, count.label) == ("NUMBER", "count", "Przewidywana ilość uczestników")
    assert f["prosze_o_wynajem_lub_uzyczenie_swietlicy_wiejskiej_w"].label.startswith("Proszę o wynajem lub użyczenie")


def test_required_is_marked_by_the_paper_or_flagged_as_inferred():
    b = hall().brief()
    f = fields(b)
    assert f["przewidywana_ilosc_uczestnikow"].required is False, "footnote 1) says the data are not obligatory"
    inferred = {w.field for w in b.warnings if w.code == "REQUIRED_INFERRED"}
    required = {k for k, x in f.items() if x.required}
    assert required and all(f[k].evidence if f[k].required_basis in ("paper", "substance") else k in inferred for k in required)
    assert check_paper_evidence(b) == []


def test_grammar_alternatives_give_no_field_and_a_real_choice_gives_one():
    p = Paper()
    p.text("WNIOSEK", bold=True)
    p.text("o wydanie zezwolenia na hodowanie/utrzymywanie* charta/chartów*", bold=True)
    p.blank("Rasa psa")
    p.text(STRIKE, role="note")
    b = p.brief()
    radios = [x for x in fields(b).values() if x.type == "RADIO"]
    assert [x.options for x in radios] == [["hodowanie", "utrzymywanie"]]
    assert [d.what for d in b.dropped if d.reason == "GRAMMAR_VARIANT"] == ["charta/chartów"]
    assert b.title.value == "Wniosek o wydanie zezwolenia na hodowanie lub utrzymywanie charta"


def test_without_the_strike_out_note_a_star_is_only_a_footnote_mark():
    p = Paper()
    p.text("WNIOSEK O WPIS", bold=True)
    p.blank("Imię/nazwa* zwierzęcia")
    assert [x.type for x in fields(p.brief()).values()] == ["TEXT_FIELD"]


def dog() -> Paper:
    p = Paper()
    p.text("WNIOSEK O WYDANIE ZEZWOLENIA", bold=True)
    b = p.heading("INFORMACJA O POSIADANYM PSIE", number="B")
    p.blank("Rasa psa", section=b)
    p.blank("Data szczepienia (w przypadku jego braku)", section=b)
    p.group("Płeć", ["❑ pies", "❑ suka"], section=b)
    p.group("Sposób oznakowania psa", ["mikroprocesor", "tatuaż", "brak"], section=b, blank_after=("mikroprocesor", "tatuaż"))
    p.blank("Opis miejsca i warunków", kind="line_block", section=b, how="above", lines=3)
    p.blank(None, section=b)
    a = p.heading("DANE IDENTYFIKACYJNE WNIOSKODAWCY", number="A")
    p.blank("Imię i nazwisko", kind="cell", section=a, how="same_cell")
    p.blank("Kod pocztowy", kind="cell", section=a, how="same_cell")
    p.blank("Nr sprawy", kind="office_use")
    return p


def test_boxes_that_share_a_question_are_one_choice_and_a_blank_after_an_option_is_shown_by_it():
    b = dog().brief()
    f = fields(b)
    assert (f["plec"].type, f["plec"].options) == ("RADIO", ["pies", "suka"])
    marking = f["sposob_oznakowania_psa"]
    assert (marking.type, marking.options) == ("RADIO", ["mikroprocesor", "tatuaż", "brak"]), "'brak' excludes the others"
    chip = f["sposob_oznakowania_psa_mikroprocesor"]
    assert chip.show_if.to_dict() == {"field": "sposob_oznakowania_psa", "is": "mikroprocesor"} and chip.required is False
    assert (f["data_szczepienia"].type, f["data_szczepienia"].hint) == ("DATEPICKER", "w przypadku jego braku")
    merged = [d for d in b.dispositions if d.fate == "MERGED"]
    assert [d.why for d in merged] == ["GROUP_MEMBER"] * 5 + ["LINE_BLOCK"]
    assert [s.title for s in b.matter] == ["Informacja o posiadanym psie"]


def test_the_applicant_section_printed_after_the_matter_is_still_the_standard_and_office_use_is_left_out():
    b = dog().brief()
    by = {d.candidate: d for d in b.dispositions}
    assert [(d.fate, d.role) for d in list(by.values())[-3:-1]] == [("STANDARD", "standard/twoje_dane"), ("STANDARD", "standard/adres")]
    assert list(by.values())[-1].reason == "OFFICE_USE"
    assert (b.applicants.status, b.applicants.self_, b.applicants.other_person, b.applicants.entity) == ("stated", True, True, False)
    assert b.applicants.capacities == ["pelnomocnik"]


def test_a_place_without_a_label_waits_for_a_decision_and_is_never_named():
    p = Paper()
    p.blank(None)
    p.text("WNIOSEK O WPIS", bold=True)
    p.blank("Nazwa sali")
    b = p.brief()
    assert fates(b) == {"c1": "AWAITING_DECISION", "c2": "FIELD"}
    assert [w.candidate for w in b.warnings if w.code == "LABEL_NOT_FOUND"] == ["c1"]


def test_a_single_box_outside_a_group_waits_for_a_decision():
    p = Paper()
    p.text("WNIOSEK O WPIS", bold=True)
    p.blank("Nazwa sali")
    p.blank("Dane pełnomocnika klubu", kind="box", how="question")
    b = p.brief()
    assert fates(b) == {"c1": "FIELD", "c2": "AWAITING_DECISION"} and list(fields(b)) == ["nazwa_sali"]
    assert [w.candidate for w in b.warnings if w.code == "AMBIGUOUS_GROUP"] == ["c2"]


def test_person_and_entity_wording_opens_all_three_parties_and_nip_goes_to_the_entity():
    p = Paper()
    s = p.heading("Dane wnioskodawcy", number="2")
    p.blank("Nazwa /Imię i nazwisko", kind="cell", section=s)
    p.blank("NIP", kind="comb", section=s, cells=10)
    p.blank("Adres siedziby lub miejsca zamieszkania", kind="cell", section=s)
    r = p.heading("Dane pełnomocnika", number="2.4", parent=s)
    p.blank("Imię i nazwisko", kind="cell", section=r)
    m = p.heading("Informacje o opłacie skarbowej", number="3")
    p.blank("Data uiszczenia opłaty", kind="comb", section=m, cells=8, mask="DD-MM-RRRR")
    p.blank("Wysokość opłaty", kind="cell", section=m)
    p.blank("Nr rachunku", kind="cell", section=m)
    p.blank("Kod pocztowy banku", kind="comb", section=m, cells=5, mask="__-___")
    z = p.heading("Załączniki", number="7")
    p.group("1.", ["Dokument stwierdzający udzielenie pełnomocnictwa", "Dowód uiszczenia opłaty skarbowej za pełnomocnictwo", "Mapa terenu"], section=z)
    p.blank(None, section=z)
    p.blank(None, section=z)
    e = p.heading("Data i podpis wnioskodawcy", number="8")
    p.blank("Data", kind="comb", section=e, cells=8, mask="DD-MM-RRRR")
    b = p.brief()
    a = b.applicants
    assert (a.self_, a.other_person, a.entity, a.capacities) == (True, True, True, ["pelnomocnik", "reprezentant"])
    assert [(x.concept, x.party) for x in b.applicant_extras] == [("nip", "entity")]
    assert [d.role for d in b.dispositions[:4]] == ["standard/twoje_dane", "standard/dane_podmiotu", "standard/adres", "standard/pelnomocnictwo"]
    f = fields(b)
    assert [(x.type, x.concept, x.length) for x in f.values()] == [("DATEPICKER", "date", None), ("NUMBER", "amount_pln", None),
                                                                   ("TEXT_FIELD", "nrb", 26), ("TEXT_FIELD", "zip_code", None)]
    assert [(x.label, x.covered_by) for x in b.attachments] == [
        ("Dokument stwierdzający udzielenie pełnomocnictwa", "standard/pelnomocnictwo"),
        ("Dowód uiszczenia opłaty skarbowej za pełnomocnictwo", "standard/oplata_skarbowa"), ("Mapa terenu", None), ("Inne załączniki", None)]
    assert b.dispositions[-1].reason == "SIGNATURE_AND_DATE" and b.dispositions[-2].why == "LINE_BLOCK"
    assert b.mandatory_attachments.status == "not_found"


def test_equal_rows_become_one_repeating_section():
    p = Paper()
    p.text("WNIOSEK O ZAJĘCIE PASA DROGOWEGO", bold=True)
    for _ in range(3):
        for label in ("długość", "szerokość", "razem"):
            p.blank(label, kind="blank_in_sentence", how="sentence")
    b = p.brief()
    assert [(s.repeating, [x.label for x in s.fields]) for s in b.matter] == [(True, ["Długość", "Szerokość", "Razem"])]
    assert all(x.type == "NUMBER" for x in fields(b).values())
    assert [d.why for d in b.dispositions[3:]] == ["TABLE_ROW"] * 6 and b.dispositions[5].into == "c3"
    assert any(d.reason == "COMPUTED_VALUE" for d in b.dropped)


def test_a_sentence_fragment_without_a_phrase_keeps_its_words_and_says_so():
    p = Paper()
    p.text("WNIOSEK O NUMER", bold=True)
    p.blank("w miejscowości", kind="blank_in_sentence", how="sentence")
    p.blank("na okres trwania", kind="blank_in_sentence", how="sentence")
    b = p.brief()
    assert [x.label for x in fields(b).values()] == ["Miejscowość", "Na okres trwania"]
    assert [w.candidate for w in b.warnings if w.code == "LABEL_RAW"] == ["c2"]


# -- declarations, clause, fee, legal basis ---------------------------------------------------------------------------

def test_declarations_are_items_in_the_papers_words():
    b = hall().brief()
    assert [(c.kind, c.text) for c in b.declarations.consents] == [
        ("declaration", "Jednocześnie oświadczam, że zapoznałem/am się z warunkami wynajmu świetlicy wiejskiej"),
        ("declaration", "Jednocześnie oświadczam, że w czasie najmu odpowiadam za ład i porządek w świetlicy oraz na terenie przyległym do świetlicy."),
    ]


def test_the_clause_never_becomes_fields_and_is_linked():
    p = hall()
    p.new_page()
    p.text("KLAUZULA INFORMACYJNA", role="clause", bold=True)
    p.text("Podanie danych: imię, nazwisko, PESEL, adres zamieszkania jest wymagane. Oświadczam, że wiem.", role="clause")
    before, after = hall().brief(), p.brief()
    assert fields(after).keys() == fields(before).keys() and len(after.declarations.consents) == len(before.declarations.consents)
    assert after.declarations.clause.status == "stated" and before.declarations.clause.status == "not_found"
    assert [d.count for d in after.dropped if d.reason == "CLAUSE_LINKED"] == [2]


def test_a_fee_that_is_not_on_the_paper_stays_not_found():
    assert hall().brief().fee.status == "not_found"
    p = hall()
    p.text("Informacje o opłacie skarbowej podaje urząd.")
    assert p.brief().fee.status == "not_found", "the word without an amount states nothing"
    p.text("Opłata za wydanie zaświadczenia wynosi 17 zł (od każdego egzemplarza).")
    fee = p.brief().fee
    assert fee.status == "stated" and "17 zł" in fee.value and fee.evidence[0].quote == fee.value
    p.text("Opłata skarbowa za pełnomocnictwo: 82,00 zł.")
    assert p.brief().fee.status == "ambiguous"


def test_legal_basis_is_quoted_or_not_found():
    assert hall().brief().legal_basis.status == "not_found"
    p = hall()
    p.text("Na podstawie art. 75 ustawy z dnia 29 sierpnia 1997 r.", role="legal_basis")
    assert p.brief().legal_basis.value.startswith("Na podstawie art. 75")


# -- composite papers (design 6.4.4) ----------------------------------------------------------------------------------

def test_three_applications_in_one_file_are_one_selector_and_no_second_form():
    p = Paper()
    for n, what in enumerate(("stypendium sportowe", "nagrodę sportową", "wyróżnienie dla trenera")):
        if n:
            p.new_page()
        p.text(f"WNIOSEK O {what.upper()}", bold=True)
        s = p.heading("Dane sportowca", number="2")
        p.blank("Dyscyplina", section=s)
        p.blank("Data urodzenia", section=s)
        t = p.heading("Osiągnięcia", number="3")
        p.blank(f"Opis osiągnięć na {what}", section=t, kind="line_block", lines=2)
    b = p.brief()
    f = fields(b)
    titles = ["Wniosek o stypendium sportowe", "Wniosek o nagrodę sportową", "Wniosek o wyróżnienie dla trenera"]
    assert b.title.value == titles[0]
    assert (f["rodzaj_wniosku"].type, f["rodzaj_wniosku"].options) == ("RADIO", titles)
    assert sum(x.type == "RADIO" for x in f.values()) == 1
    shared = [s for s in b.matter if s.title == "Dane sportowca"]
    assert len(shared) == 1 and shared[0].show_if is None, "word for word the same in all three: written once"
    own = [s for s in b.matter if s.title == "Osiągnięcia"]
    assert [s.show_if.to_dict() for s in own] == [{"field": "rodzaj_wniosku", "is": t} for t in titles]
    assert [d.why for d in b.dispositions if d.fate == "MERGED"] == ["SAME_ALTERNATIVE"] * 4


def test_an_ordinary_paper_has_no_selector():
    assert "rodzaj_wniosku" not in fields(hall().brief())


# -- invariance, the gate, the lexicons, failure ------------------------------------------------------------------------

def test_another_municipality_and_another_title_do_not_change_the_fields_of_the_matter():
    a = hall().brief()
    b = hall(office="BURMISTRZ MIASTA WYMYŚLIN", title=("WNIOSEK", "o", "wynajęcie/użyczenie* sali gimnastycznej")).brief()
    shape = lambda brief: [(s.role, [(x.key, x.label, x.type, x.required, x.options) for x in s.fields]) for s in brief.matter]  # noqa: E731
    assert a.title.value != b.title.value and a.addressee.name != b.addressee.name
    assert shape(a) == shape(b)


@pytest.mark.parametrize("paper", [hall, dog])
def test_the_composed_form_passes_the_gate(paper):
    brief = paper().brief()
    form = json.loads(compose(brief).form.to_json_bytes())
    report = gate.check(form)
    assert report.passed, [(c.id, [x.message for x in c.findings[:3]]) for c in report.failed]
    matter_keys = set(fields(brief))
    assert matter_keys and matter_keys <= set(compose(brief).brief_keys.values()) | set(compose(brief).brief_keys)


def test_every_lexicon_row_has_a_source_and_a_date():
    assert set(lexicon.names()) >= {"title_kinds", "offices", "applicants", "concepts", "phrases", "habits"}
    for name in lexicon.names():
        assert lexicon.rows(name) and all(r["source"] and r["date"] for r in lexicon.rows(name))


def test_a_rule_that_fails_is_a_warning_and_every_candidate_waits(monkeypatch):
    import app.mean as mean

    pm, fo = hall().build()
    monkeypatch.setattr(mean, "find_title", lambda doc: 1 / 0)
    with pytest.raises(ZeroDivisionError):
        understand(pm, fo, STRICT)
    b = understand(pm, fo)
    assert [w.code for w in b.warnings] == ["UNREADABLE_PART"] and not b.matter
    assert set(fates(b).values()) == {"AWAITING_DECISION"} and len(b.dispositions) == len(fo.candidates)


def test_through_the_real_finder_every_candidate_is_accounted_for():
    texts = ["WNIOSEK O WYDANIE ZAŚWIADCZENIA", f"Rodzaj zaświadczenia: {DOTS}", f"Cel wydania: {DOTS}", f"(podpis wnioskodawcy) {DOTS}"]
    runs = [Run(id=f"f{i}", text=t, anchor=f"p[{i}]", size=11.0, bold=i == 0) for i, t in enumerate(texts)]
    pm = PageModel(source=Source(sha256="0" * 64, format="docx", reader="test.built", pages=1), pages=[Page(number=1, origin="flow", runs=runs)])
    fo = find(pm)
    b = understand(pm, fo, STRICT)
    assert b.title.value == "Wniosek o wydanie zaświadczenia"
    assert [d.candidate for d in b.dispositions] == [c.id for c in fo.candidates]
    assert len(fo.candidates) == 0 or fields(b) or b.warnings
