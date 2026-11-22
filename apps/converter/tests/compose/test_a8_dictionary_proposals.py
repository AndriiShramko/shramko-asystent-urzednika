"""A8 DX-1: task card point II, "Zaproponowanie nowego słownika". A closed list of the paper that looks like reference
data becomes a dictionary PROPOSAL in the sidecar (`meta.proposals.dictionaries`, contract `ProposedDictionary`): a
name from the group's own label, the entries exactly as printed, the fields that would use it, the evidence. The
form itself never changes. Synthetic briefs only."""
from __future__ import annotations

import json

from compose_helpers import brief, brief_dict

from app.compose import compose
from app.compose.dictionaries import dictionary_name, proposals, sidecar_extras
from app.model.meta import Proposals, ProposedDictionary

SPORTS = ["hokej", "karate", "kolarstwo", "koszykówka", "lekkoatletyka", "piłka nożna", "tenis stołowy", "pływanie"]
EV = [{"page": 2, "quote": "Dyscypliny sportowe"}]


def _matter(*fields: dict) -> list[dict]:
    return [{"title": "Sprawa", "role": "matter/sprawa", "fields": list(fields)}]


def _run(*fields: dict) -> tuple[list[ProposedDictionary], dict]:
    b = brief(matter=_matter(*fields))
    c = compose(b)
    ids = {key: fid for fid, key in c.brief_keys.items()}
    return proposals(b, ids), sidecar_extras(b, c.brief_keys)


def test_one_long_list_of_short_options_is_proposed_as_printed() -> None:
    props, extras = _run({"key": "dyscyplina", "label": "Dyscypliny sportowe:", "type": "SELECT", "options": SPORTS, "evidence": EV})
    assert len(props) == 1
    p = props[0]
    assert p.name == "Dyscypliny sportowe"
    assert p.entries == SPORTS                                   # exactly as printed, in the printed order
    assert p.pages == [2] and p.field and p.fields == [p.field]
    assert p.why and p.use and "Dyscypliny sportowe" in p.use
    assert extras["proposals"]["dictionaries"][0]["entries"] == SPORTS
    Proposals.model_validate(extras["proposals"])               # the contract's own slot, closed schema


def test_the_same_list_on_two_fields_is_one_proposal_naming_both() -> None:
    units = ["sztuka", "kilogram", "metr bieżący"]
    props, _ = _run({"key": "jednostka_a", "label": "Jednostka miary", "type": "RADIO", "options": units},
                    {"key": "jednostka_b", "label": "Jednostka miary odpadu", "type": "RADIO", "options": units})
    assert len(props) == 1 and len(props[0].fields) == 2 and props[0].entries == units


def test_yes_no_short_lists_long_sentences_and_box_marks_are_not_proposed() -> None:
    marks = ["M M -", "R R R R"]                               # date boxes read as options: not reference data
    long_opts = [f"Oświadczam, że spełniam warunek numer {i} określony w regulaminie" for i in range(1, 8)]
    props, extras = _run(
        {"key": "a", "label": "Czy dotyczy", "type": "RADIO", "options": ["Tak", "Nie"]},
        {"key": "b", "label": "Czy dotyczy także", "type": "RADIO", "options": ["Tak", "Nie"]},
        {"key": "c", "label": "Data zdarzenia", "type": "RADIO", "options": marks},
        {"key": "d", "label": "Data zmiany", "type": "RADIO", "options": marks},
        {"key": "e", "label": "Rodzaj", "type": "CHECKBOX", "options": ["pierwszy", "drugi", "trzeci", "czwarty", "piąty"]},
        {"key": "f", "label": "Oświadczenia", "type": "CHECKBOX", "options": long_opts})
    assert props == [] and extras == {}


def test_a_form_without_such_a_list_keeps_form_and_sidecar_bytes() -> None:
    b = brief()
    c1, c2 = compose(b), compose(b)
    assert sidecar_extras(b, c1.brief_keys) == {}
    assert c1.form.to_json_bytes() == c2.form.to_json_bytes()


def test_the_form_never_carries_a_proposed_dictionary() -> None:
    b = brief(matter=_matter({"key": "dyscyplina", "label": "Dyscypliny sportowe", "type": "SELECT", "options": SPORTS}))
    form = json.loads(compose(b).form.to_json_bytes())
    names = [c["field"].get("dictionaryName") for t in form["tabs"] for q in t["questions"] for c in q["field"]["repeatingSectionGrid"]]
    assert "Dyscypliny sportowe" not in names                   # gate G9: only the partner's names go into the form (D9)


def test_name_comes_from_the_label_without_numbering_hints_or_colon() -> None:
    assert dictionary_name("3. Rodzaj dokumentu (zaznacz właściwe):") == "Rodzaj dokumentu"
    assert dictionary_name("rodzaj odpadu") == "Rodzaj odpadu"
    assert len(dictionary_name("słowo " * 30)) <= 60


def test_brief_dict_helper_is_unchanged() -> None:   # guards the helper this file relies on
    assert brief_dict()["matter"][0]["role"] == "matter/zakres"
