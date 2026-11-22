"""Composer, without the partner's sets: the gate on every composed form, stability, the switches, the controls."""
from __future__ import annotations

import os
import uuid
from collections import Counter

import jsonata
import pytest
from compose_helpers import SNAPSHOTS, brief, brief_dict, everyone, load_brief, outline, visible, visible_text

from app.compose import EXPORT_1, EXPORT_5, ComposeOptions, compose, pages_without_fixed_content
from app.compose.html import is_ours
from app.compose.names import slug
from app.compose.query import All, Any, Is, Not, Place, write
from app.model.form import Form
from tools.coi_lint import check

FIELD = {"key": "pole", "label": "Pole", "type": "TEXT_FIELD"}


def _hundred() -> dict:
    return brief_dict(matter=[{"title": "Wykaz", "role": "matter/wykaz", "fields": [
        {"key": f"pozycja_{i}", "label": f"Pozycja {i}", "type": "TEXT_FIELD"} for i in range(1, 101)]}])


def _conditional_only() -> dict:
    choice = {"key": "rodzaj", "label": "Wybierz rodzaj wniosku", "type": "RADIO", "options": ["Pierwszy", "Drugi"]}
    filler = [{"key": f"f{i}", "label": f"Dane {i}", "type": "TEXT_FIELD"} for i in range(9)]
    return brief_dict(matter=[
        {"title": "Rodzaj wniosku", "role": "matter/rodzaj", "fields": [choice, *filler]},
        {"title": "Wariant drugi", "role": "matter/wariant_drugi", "show_if": {"field": "rodzaj", "is": "Drugi"},
         "fields": [{"key": "opis", "label": "Opis", "type": "TEXTAREA"}]}])


def _rich() -> dict:
    """Every component type and every optional part of a brief, synthetic."""
    return brief_dict(
        applicants=everyone(),
        applicant_extras=[{"concept": "pesel", "party": "self"}, {"concept": "regon", "party": "entity"},
                          {"concept": "krs", "party": "entity"}, {"concept": "pesel", "party": "other_person"}],
        matter=[
            {"title": "Zwierzę", "role": "matter/zwierze", "fields": [
                {"key": "plec", "label": "Płeć", "type": "RADIO", "options": ["pies", "suka"], "required": True, "required_basis": "paper"},
                {"key": "cechy", "label": "Cechy", "type": "CHECKBOX", "options": ["Tatuaż", "Mikroprocesor", "Inne"]},
                {"key": "inne_cechy", "label": "Inne cechy", "type": "TEXT_FIELD", "show_if": {"field": "cechy", "is": "Inne"}},
                {"key": "data_urodzenia", "label": "Data urodzenia", "type": "DATEPICKER", "concept": "date"},
                {"key": "rasa", "label": "Rasa", "type": "SELECT", "options": [f"Rasa {i}" for i in range(1, 18)]},
                {"key": "email_hodowcy", "label": "Adres e-mail hodowcy", "type": "TEXT_FIELD", "concept": "email",
                 "hint": "Podaj adres, pod którym odbierasz wiadomości."},
                {"key": "pouczenie", "label": "Zezwolenie wydaje się na czas oznaczony.", "type": "TEXT_BLOCK"}]},
            {"title": "Osoby", "role": "matter/osoby", "repeating": True, "fields": [
                {"key": "osoba_imie", "label": "Imię", "type": "TEXT_FIELD"},
                {"key": "osoba_pesel", "label": "PESEL", "type": "TEXT_FIELD", "concept": "pesel"}]}],
        attachments=[{"label": "Dokument stwierdzający udzielenie pełnomocnictwa", "covered_by": "standard/pelnomocnictwo"},
                     {"label": "Mapa z zaznaczonym terenem", "required": True},
                     {"label": "Zgoda współwłaściciela", "show_if": {"field": "plec", "is": "suka"}}],
        declarations={"consents": [{"text": "Oświadczam, że dane są zgodne z prawdą."}],
                      "clause": {"status": "stated", "value": "https://przykladowo.example/rodo", "evidence": [{"quote": "Klauzula"}]}},
        fee={"status": "stated", "value": "Opłata skarbowa – 82 zł", "evidence": [{"quote": "Opłata skarbowa – 82 zł"}]})


BRIEFS = {
    "reference_01": lambda: load_brief("brief_reference_01"),
    "reference_05": lambda: load_brief("brief_reference_05"),
    "person_only": lambda: brief(),
    "entity_only": lambda: brief(applicants={"status": "stated", "entity": True, "evidence": [{"quote": "nazwa, siedziba"}]}),
    "person_and_other": lambda: brief(applicants={"status": "stated", "self": True, "other_person": True, "evidence": [{"quote": "imię"}]}),
    "nothing_stated": lambda: brief(title={"status": "not_found"}, addressee={"status": "not_found"},
                                    applicants={"status": "not_found"}, matter=[]),
    "hundred_fields": lambda: brief(**{k: v for k, v in _hundred().items()}),
    "conditional_only": lambda: brief(**{k: v for k, v in _conditional_only().items()}),
    "rich": lambda: brief(**{k: v for k, v in _rich().items()}),
}
OPTION_SETS = {
    "default": ComposeOptions(),
    "exports_way": ComposeOptions(validators=False, statutory_representative=False, standard=EXPORT_1),
    "all_switches": ComposeOptions(finish_style="info_section", repeating_style="section", poa_exemption=True, standard=EXPORT_5),
}


def _html_strings(form: Form) -> list[str]:
    out = [f.description for f in form.iter_fields()]
    return out + [c.description for f in form.iter_fields() if f.consentSectionConfig for c in f.consentSectionConfig.consents]


@pytest.mark.parametrize("options", OPTION_SETS)
@pytest.mark.parametrize("name", BRIEFS)
def test_every_composed_form_passes_the_gate(name: str, options: str) -> None:
    result = compose(BRIEFS[name](), OPTION_SETS[options])
    doc = result.form.to_partner()
    assert sorted(doc) == ["flow", "tabs", "title"]                      # D1: the partner's object and nothing else
    Form.model_validate(doc)                                             # strict reading of our own output
    assert [f for f in check(doc, "strict") if f[0] == "ERROR"] == []    # schema of the strict profile and the partner rules
    assert pages_without_fixed_content(result.form) == []                # no page can be empty on any journey
    assert all(is_ours(h) for h in _html_strings(result.form))           # D11: every HTML string passes the allow-list
    for f in result.form.iter_fields():                                  # every condition is JSONata that parses
        for s in f.states:
            jsonata.Jsonata(s.query)
    ids = [f.id for f in result.form.iter_fields()]
    assert set(result.origins) == set(ids) and set(result.origins.values()) <= {"paper", "standard"}
    assert set(result.brief_keys) <= set(ids) and set(ids) <= set(result.paths)
    assert doc["tabs"][-1]["type"] == "FINISH" and [t["type"] for t in doc["tabs"][:-1]] == ["MAIN"] * (len(doc["tabs"]) - 1)


@pytest.mark.parametrize("name", BRIEFS)
def test_two_runs_are_byte_identical(name: str) -> None:
    assert compose(BRIEFS[name]()).form.to_json_bytes() == compose(BRIEFS[name]()).form.to_json_bytes()


@pytest.mark.parametrize("name", ["reference_01", "reference_05", "rich"])
def test_snapshot_of_our_own_output(name: str) -> None:
    text, path = outline(compose(BRIEFS[name]()).form), SNAPSHOTS / f"{name}.txt"
    if os.environ.get("COMPOSE_SNAPSHOT_UPDATE") == "1":
        path.parent.mkdir(exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    assert path.read_text(encoding="utf-8") == text, "rerun with COMPOSE_SNAPSHOT_UPDATE=1 after reading the difference"


def test_one_changed_label_changes_that_title_and_no_id() -> None:
    data = brief_dict(**_rich())
    before = compose(brief(**data))
    data["matter"][0]["fields"][5]["label"] = "Adres poczty elektronicznej hodowcy"
    after = compose(brief(**data))
    a, b = list(before.form.iter_fields()), list(after.form.iter_fields())
    assert [f.id for f in a] == [f.id for f in b]
    assert [t.id for t in before.form.tabs] == [t.id for t in after.form.tabs]
    assert [x.id for x in before.form.flow.links] == [x.id for x in after.form.flow.links]
    assert [(x.title, y.title) for x, y in zip(a, b, strict=True) if x.title != y.title] == [
        ("Adres e-mail hodowcy", "Adres poczty elektronicznej hodowcy")]


def test_ids_come_from_the_meaning_path_and_the_namespace() -> None:
    base = compose(brief())
    for id_, path in base.paths.items():
        assert id_ == str(uuid.uuid5(ComposeOptions().id_namespace, path))
    assert "wniosek_o_wydanie_zaswiadczenia/dane/twoje_dane/imie" in base.paths.values()
    assert "wniosek_o_wydanie_zaswiadczenia/matter/zakres/cel" in base.paths.values()
    keyed = compose(brief(title={"status": "stated", "value": "Inny tytuł", "evidence": [{"quote": "x"}]}), ComposeOptions(form_key="wniosek_o_wydanie_zaswiadczenia"))
    assert list(keyed.paths) == list(base.paths)                          # FORM_KEY keeps the ids when the title changes
    other = compose(brief(), ComposeOptions(id_namespace=uuid.UUID(int=7)))
    assert not set(other.paths) & set(base.paths)
    moved = brief_dict()
    moved["matter"][0]["fields"].reverse()
    assert set(compose(brief(**moved)).paths) == set(base.paths)          # a moved field keeps its id


def test_origins_and_brief_keys_for_the_sidecar() -> None:
    r = compose(load_brief("brief_reference_05"))
    by_tech = {f.techName: f.id for f in r.form.iter_fields()}
    assert r.origins[by_tech["kwota"]] == "paper" and r.brief_keys[by_tech["kwota"]] == "kwota"
    assert r.origins[by_tech["rozliczenie_nadplaty"]] == "paper"
    assert r.origins[by_tech["twoje_dane"]] == "standard" and by_tech["imie"] not in r.brief_keys
    # Export 5 has 73 nodes: 63 standard and 10 of the matter. Ours adds the three nodes of D16 to the standard ones.
    assert Counter(r.origins.values()) == {"standard": 66, "paper": 10}
    # The cheapest test that would prove us wrong: without the standard nodes the matter still says what the service is.
    paper = [f.title for f in r.form.iter_fields() if r.origins[f.id] == "paper"]
    assert {"Podatek, którego dotyczy nadpłata", "Kwota", "Uzasadnienie", "Numer rachunku"} <= set(paper)


# -- the switches ------------------------------------------------------------------------------------------------------

def test_finish_style_switch_d5() -> None:
    last = compose(brief()).form.tabs[-1]
    assert [(q.field.type, [c.field.type for c in q.field.repeatingSectionGrid]) for q in last.questions] == [("SECTION", ["TEXT_BLOCK"])]
    r = compose(brief(), ComposeOptions(finish_style="info_section"))
    assert [c.field.type for c in r.form.tabs[-1].questions[0].field.repeatingSectionGrid] == ["INFO_SECTION"]
    assert "INFERRED_SHAPE" in {x.code for x in r.remarks}


def test_validators_switch_d8() -> None:
    on = {f.techName: f.validation for f in compose(brief(**_rich())).form.iter_fields()}
    assert on["plec"] == ["REQUIRED"] and on["adres_e_mail_hodowcy"] == ["EMAIL"] and on["pesel"] == ["PESEL"]
    assert on["kod_pocztowy"] == ["REQUIRED", "ZIP_CODE"] and on["kod_pocztowy_zagranica"] == [] and on["nip"] == ["REQUIRED", "NIP"] and on["regon"] == ["REGON"]
    assert on["adres_e_mail"] == ["EMAIL"] and on["numer_pesel_inna_osoba"] == ["REQUIRED", "PESEL"] and on["mapa_z_zaznaczonym_terenem"] == ["REQUIRED"]
    off = compose(brief(**_rich()), ComposeOptions(validators=False))
    assert all(f.validation == [] for f in off.form.iter_fields())


def test_repeating_style_switch() -> None:
    native = compose(brief(**_rich()))
    kinds = {f.techName: f.type for f in native.form.iter_fields()}
    assert kinds["osoby"] == "REPEATING_SECTION"
    assert any(x.code == "INFERRED_SHAPE" and "REPEATING_SECTION" in x.detail for x in native.remarks)
    flat = compose(brief(**_rich()), ComposeOptions(repeating_style="section"))
    assert {f.techName: f.type for f in flat.form.iter_fields()}["osoby"] == "SECTION"
    assert "REPEATING_FLATTENED" in {x.code for x in flat.remarks}


def test_a_condition_inside_a_repeating_section_is_reported_not_guessed() -> None:
    data = brief_dict(matter=[{"title": "Osoby", "role": "matter/osoby", "repeating": True, "fields": [
        {"key": "rola", "label": "Rola", "type": "RADIO", "options": ["A", "B"]},
        {"key": "opis_roli", "label": "Opis roli", "type": "TEXT_FIELD", "show_if": {"field": "rola", "is": "B"}}]}])
    r = compose(brief(**data))
    assert {f.techName: f.states for f in r.form.iter_fields()}["opis_roli"] == []
    assert [x.code for x in r.remarks].count("CONDITION_NOT_WRITTEN") == 1


JOURNEY_PARTY, JOURNEY_AS, JOURNEY_AS_OTHER = "wybierz_w_czyim_imieniu_wnioskujesz", "wybierz_jako_kto_wnioskujesz", "wybierz_jako_kto_wnioskujesz_inna_osoba"
ENTITY = "Osoby prawnej lub jednostki organizacyjnej"
CONDITIONAL = {"dane_podmiotu", "adres_siedziby", "potwierdzenie_ze_jestes_reprezentantem", "dane_innej_osoby",
               "adres_zamieszkania_osoby_ktorej_jestes_pelnomocnikiem", "potwierdzenie_ze_jestes_przedstawicielem_ustawowym",
               "pelnomocnictwo", "oplata_skarbowa_pelnomocnictwo_1", "oplata_skarbowa_pelnomocnictwo_2"}


def test_seven_journeys_and_the_zero_answer_canary_d16() -> None:
    form = compose(load_brief("brief_reference_05")).form                # statutory representative on by default

    def shown(answers: dict) -> set[str]:
        return visible(form, answers) & CONDITIONAL

    assert shown({}) == set()                                            # nothing chosen: every conditional section hidden
    assert shown({JOURNEY_PARTY: "Swoim"}) == set()
    other = {"dane_innej_osoby", "adres_zamieszkania_osoby_ktorej_jestes_pelnomocnikiem"}
    assert shown({JOURNEY_PARTY: "Innej osoby"}) == other                # the capacity is not chosen yet: no proof asked
    assert shown({JOURNEY_PARTY: "Innej osoby", JOURNEY_AS_OTHER: "Pełnomocnik"}) == other | {"pelnomocnictwo", "oplata_skarbowa_pelnomocnictwo_1"}
    assert shown({JOURNEY_PARTY: "Innej osoby", JOURNEY_AS_OTHER: "Przedstawiciel ustawowy"}) == other | {
        "potwierdzenie_ze_jestes_przedstawicielem_ustawowym"}            # D16: its own proof, no stamp duty
    entity = {"dane_podmiotu", "adres_siedziby"}
    assert shown({JOURNEY_PARTY: ENTITY, JOURNEY_AS: "Reprezentant"}) == entity | {"potwierdzenie_ze_jestes_reprezentantem"}
    assert shown({JOURNEY_PARTY: ENTITY, JOURNEY_AS: "Pełnomocnik"}) == entity | {"pelnomocnictwo", "oplata_skarbowa_pelnomocnictwo_2"}
    home, abroad = visible(form, {}), visible(form, {"kraj": ["Niemcy"]})
    assert {"wojewodztwo", "kod_pocztowy", "ulica"} <= home and not {"miejscowosc_zagranica", "ulica_zagranica"} & home
    assert {"miejscowosc_zagranica", "kod_pocztowy_zagranica", "ulica_zagranica"} <= abroad and "wojewodztwo" not in abroad
    paid = visible(form, {JOURNEY_PARTY: "Innej osoby", JOURNEY_AS_OTHER: "Pełnomocnik", "czy_zlozenie_pelnomocnictwa_wymaga_oplaty_skarbowej": "Tak"})
    assert {"oplata_info_1", "plik_z_potwierdzeniem_przelewu"} <= paid
    assert {"nazwa_podatku", "numer_rachunku"} & visible(form, {"wybierz_co_mamy_zrobic_z_nadplata": "Zwrócić przelewem na rachunek bankowy"}) == {"numer_rachunku"}


def test_statutory_representative_off_is_the_exports_block() -> None:
    form = compose(load_brief("brief_reference_05"), ComposeOptions(statutory_representative=False)).form
    names = {f.techName for f in form.iter_fields()}
    assert not {JOURNEY_AS_OTHER, "potwierdzenie_ze_jestes_przedstawicielem_ustawowym"} & names
    assert visible(form, {JOURNEY_PARTY: "Innej osoby"}) & CONDITIONAL == {
        "dane_innej_osoby", "adres_zamieszkania_osoby_ktorej_jestes_pelnomocnikiem", "pelnomocnictwo", "oplata_skarbowa_pelnomocnictwo_1"}


def test_poa_exemption_switch_d17() -> None:
    reason = "wybierz_powod_zwolnienia_z_oplaty_skarbowej"
    assert reason not in {f.techName for f in compose(load_brief("brief_reference_05")).form.iter_fields()}      # off by default
    form = compose(load_brief("brief_reference_05"), ComposeOptions(poa_exemption=True)).form
    answers = {JOURNEY_PARTY: "Innej osoby", JOURNEY_AS_OTHER: "Pełnomocnik", "czy_zlozenie_pelnomocnictwa_wymaga_oplaty_skarbowej": "Nie"}
    assert reason in visible(form, answers) and "oplata_info_1" not in visible(form, answers)
    assert reason not in visible(form, {**answers, "czy_zlozenie_pelnomocnictwa_wymaga_oplaty_skarbowej": "Tak"})


def test_a_sole_trader_takes_the_entity_path_d18() -> None:
    r = compose(brief(applicant_extras=[{"concept": "nip", "party": "self"}, {"concept": "regon", "party": "self"}]))
    by_section = {q.field.techName: [c.field.techName for c in q.field.repeatingSectionGrid] for t in r.form.tabs for q in t.questions}
    assert by_section["twoje_dane"] == ["imie", "nazwisko"]              # a person's block never carries NIP or REGON
    assert by_section["dane_podmiotu"] == ["nazwa", "nip", "regon"]
    assert "SOLE_TRADER_AS_ENTITY" in {x.code for x in r.remarks}
    assert [o.name for f in r.form.iter_fields() if f.techName == JOURNEY_PARTY for o in f.options] == ["Swoim", ENTITY]


def test_who_may_apply_selects_the_standard_sections() -> None:
    def names(**over: object) -> set[str]:
        return {q.field.techName for q in compose(brief(**over), ComposeOptions(statutory_representative=False)).form.tabs[0].questions}

    assert names() == {"urzad_do_ktorego_jest_skladany_wniosek", "twoje_dane", "adres_zamieszkania"}          # in person: no "Podmiot wniosku"
    entity = names(applicants={"status": "stated", "entity": True, "evidence": [{"quote": "nazwa"}]})
    assert entity == {"urzad_do_ktorego_jest_skladany_wniosek", "podmiot_wniosku", "twoje_dane", "dane_podmiotu", "adres_siedziby",
                      "potwierdzenie_ze_jestes_reprezentantem", "pelnomocnictwo", "oplata_skarbowa_pelnomocnictwo_2"}
    body = compose(brief(addressee={"status": "stated", "kind": "body", "name": "Wójt Gminy Przykładowo", "evidence": [{"quote": "Wójt"}]})).form
    first = body.tabs[0].questions[0].field
    assert (first.techName, first.repeatingSectionGrid[0].field.techName) == ("organ_do_ktorego_jest_skladany_wniosek", "nazwa_organu")
    assert (first.repeatingSectionGrid[0].field.defaultValue, first.repeatingSectionGrid[0].field.readOnly) == ("Wójt Gminy Przykładowo", True)


def test_honest_gaps_are_remarks_never_silent_defaults() -> None:
    r = compose(BRIEFS["nothing_stated"]())
    assert {"TITLE_MISSING", "ADDRESSEE_MISSING", "APPLICANTS_ASSUMED", "NO_MATTER", "CLAUSE_LINK_MISSING"} <= {x.code for x in r.remarks}
    name = r.form.tabs[0].questions[0].field.repeatingSectionGrid[0].field
    assert name.defaultValue is None and name.readOnly is False          # no invented office
    assert [t.title for t in r.form.tabs] == ["Dane", "Kontakt i zgody", "Strona końcowa"]
    linked = compose(brief(**_rich())).form
    consent = next(f for f in linked.iter_fields() if f.techName == "zgoda").consentSectionConfig.consents[0].description
    assert '<a href="https://przykladowo.example/rodo"' in consent
    fee = next(f for f in linked.iter_fields() if f.type == "TEXT_BLOCK" and "82 zł" in f.description)
    assert visible_text(fee.description) == "Opłata skarbowa – 82 zł"    # stated on the paper: quoted, with a proof upload


# -- negative controls of the acceptance list ---------------------------------------------------------------------------

def test_two_sections_with_the_same_title_give_unique_technames() -> None:
    twin = [{"title": "Dane pojazdu", "role": f"matter/pojazd_{n}", "fields": [{"key": f"marka_{n}", "label": "Marka", "type": "TEXT_FIELD"}]} for n in (1, 2)]
    twin.append({"title": "Twoje dane", "role": "matter/twoje", "fields": [{"key": "imie_psa", "label": "Imię", "type": "TEXT_FIELD"},
                                                                         {"key": "lodz", "label": "Łódź", "type": "TEXT_FIELD"},
                                                                         {"key": "lodz_2", "label": "Lodz", "type": "TEXT_FIELD"}]})
    form = compose(brief(matter=twin)).form
    names = [f.techName for f in form.iter_fields()]
    assert len(names) == len(set(names))
    assert {"dane_pojazdu", "dane_pojazdu_pojazd_2", "marka", "marka_pojazd_2", "twoje_dane", "twoje_dane_twoje", "imie", "imie_twoje",
            "lodz", "lodz_twoje"} <= set(names)
    assert next(f for f in form.iter_fields() if f.techName == "twoje_dane").title == "Twoje dane"       # the library keeps its names


def test_a_label_with_markup_arrives_as_text() -> None:
    hostile = "<img src=x onerror=1>"
    data = brief_dict(
        title={"status": "stated", "value": f"Wniosek {hostile}", "evidence": [{"quote": "x"}]},
        applicants=everyone(),
        matter=[{"title": hostile, "role": "matter/a", "fields": [
            {"key": "a", "label": hostile, "type": "RADIO", "options": [hostile, "<script>alert(1)</script>"], "hint": hostile},
            {"key": "b", "label": hostile, "type": "TEXT_BLOCK"},
            {"key": "c", "label": "Zależne", "type": "TEXT_FIELD", "show_if": {"field": "a", "is": hostile}}]}],
        declarations={"consents": [{"text": f"Oświadczam {hostile}"}],
                      "clause": {"status": "stated", "value": "javascript:alert(1)", "evidence": [{"quote": "x"}]}},
        fee={"status": "stated", "value": hostile, "evidence": [{"quote": hostile}]})
    r = compose(brief(**data))
    assert [f for f in check(r.form.to_partner(), "strict") if f[0] == "ERROR"] == []
    markup = _html_strings(r.form)
    assert all(is_ours(h) for h in markup)
    assert not any("<img" in h or "<script" in h or "onerror=1>" in h or "javascript:" in h for h in markup)
    assert sum("&lt;img src=x onerror=1&gt;" in h for h in markup) == 6  # hint, text block, consent, fee, the transfer title in both fee notes
    field = next(f for f in r.form.iter_fields() if r.brief_keys.get(f.id) == "a")
    assert field.title == hostile and field.options[0].name == hostile   # a title is text, kept as text
    # The section has the same hostile title and takes the plain slug; the field gets the role suffix.
    assert field.techName == "img_src_x_onerror_1_a" and field.options[1].techName == "script_alert_1_script"
    assert sum(x.code == "MARKUP_IN_LABEL" for x in r.remarks) == 2      # the section and the field: shown to the reviewer
    dependent = next(f for f in r.form.iter_fields() if r.brief_keys.get(f.id) == "c")
    assert "c" in {r.brief_keys.get(f.id) for f in r.form.iter_fields() if f.techName in visible(r.form, {field.techName: hostile})}
    assert dependent.techName not in visible(r.form, {})


def test_a_hundred_fields_in_one_section_are_split_over_pages() -> None:
    r = compose(BRIEFS["hundred_fields"]())
    matter = r.form.tabs[1:-2]
    assert len(matter) == 10 and all(sum(len(q.field.repeatingSectionGrid) for q in t.questions) == 10 for t in matter)
    assert len({t.title for t in r.form.tabs}) == len(r.form.tabs)
    assert [t.title for t in matter][:2] == ["Wykaz", "Wykaz (część 2)"]
    assert sum(1 for k in r.brief_keys.values() if k.startswith("pozycja_")) == 100
    assert "SECTION_SPLIT" in {x.code for x in r.remarks}
    assert len(r.form.flow.links) == len(r.form.tabs) - 1


def test_a_page_of_conditional_sections_gets_an_unconditional_note() -> None:
    r = compose(BRIEFS["conditional_only"]())
    page = next(t for t in r.form.tabs if t.title == "Wariant drugi")
    assert [(q.field.type, bool(q.field.states)) for q in page.questions] == [("SECTION", False), ("SECTION", True)]
    assert page.questions[0].field.repeatingSectionGrid[0].field.type == "TEXT_BLOCK"
    assert "STEP_NOTE_ADDED" in {x.code for x in r.remarks}
    assert [q.field.techName for q in page.questions] == ["krok_wariant_drugi", "wariant_drugi"]
    assert "wariant_drugi" not in visible(r.form, {}) and "opis" in visible(r.form, {"wybierz_rodzaj_wniosku": "Drugi"})


# -- small parts ----------------------------------------------------------------------------------------------------------

def test_slug_and_condition_notation() -> None:
    assert slug("Łódź, ul. Żółta 5") == "lodz_ul_zolta_5" and slug("1. Imię") == "pole_1_imie" and slug("—") == "pole"
    assert len(slug("bardzo długa etykieta " * 10)) <= 60 and not slug("bardzo długa etykieta " * 10).endswith("_")
    places = {"a": Place("Dane", "s", "f"), "b": Place("Strona „O'Neill”", "s2", "f2")}
    assert write(Is("a", "Tak"), places) == "(\"Tak\" in tabs['Dane' in title].questions['s' in field.techName].field.repeatingSectionGrid['f' in field.techName].field.__userAnswer)"
    assert write(Not(Is("a", "Polska")), places).startswith('$not("Polska" in tabs[')
    nested = write(Any((Is("a", "x"), All((Is("a", "y"), Is("b", 'cudzy"słów'))))), places)
    assert nested.count(" or ") == 1 and nested.count(" and ") == 1 and "tabs[\"Strona „O'Neill”\" in title]" in nested
    jsonata.Jsonata(nested)
