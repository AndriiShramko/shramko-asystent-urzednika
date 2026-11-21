"""The partner's form model on a synthetic form built with the helpers: strict reading, D3 defaults, the
exports' key order, the schema of contracts/coi/form.schema.json, byte-stable output, the negative controls."""
from __future__ import annotations

import copy
import json
import uuid

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from app.model import (
    EMPTY_HTML,
    ConsentItem,
    Form,
    Option,
    State,
    consent_section,
    datepicker,
    file_uploader,
    radio,
    section,
    select,
    tab,
    text_block,
    text_field,
)
from app.model.schemas import CONTRACTS

NS = uuid.UUID("6f1c2b1e-0000-5000-8000-000000000000")  # synthetic namespace of this test
FIELD_KEYS = ["id", "type", "techName", "title", "description", "dictionaryName", "options", "multiLevelTree",
              "validation", "searchEnabled", "readOnly", "repeatingSectionGrid", "defaultValue", "defaultValueType",
              "consentSectionConfig", "states", "questionOrder", "tooltipMessage"]  # order of the partner's exports
ALWAYS = ["id", "type", "techName", "title", "description", "options", "validation", "readOnly",
          "repeatingSectionGrid", "states", "questionOrder", "tooltipMessage"]


def uid(path: str) -> str:
    return str(uuid.uuid5(NS, f"test-form/{path}"))


def build() -> Form:
    q = '("Przelewem" in tabs[\'Sprawa\' in title].questions[\'zwrot\' in field.techName].field.repeatingSectionGrid[\'sposob\' in field.techName].field.__userAnswer)'
    dane = tab(uid("dane"), "Dane", [
        section(uid("dane/twoje_dane"), "twoje_dane", "Twoje dane", [
            text_field(uid("dane/twoje_dane/imie"), "imie", "Imię", read_only=True,
                       default_value="MLPZ.name", default_value_type="EXTERNAL_SYSTEM"),
            select(uid("dane/twoje_dane/kraj"), "kraj", "Kraj", dictionary_name="Kraje", default_value=["Polska"]),
        ]),
    ])
    sprawa = tab(uid("sprawa"), "Sprawa", [
        section(uid("sprawa/zwrot"), "zwrot", "Sposób zwrotu", [
            radio(uid("sprawa/zwrot/sposob"), "sposob", "Wybierz sposób zwrotu",
                  [Option.of("Gotówką", "gotowka"), Option.of("Przelewem", "przelewem")], validation=["REQUIRED"]),
            text_field(uid("sprawa/zwrot/numer"), "numer_rachunku", "Numer rachunku", states=[State(type="SHOW", query=q)]),
            datepicker(uid("sprawa/zwrot/data"), "data_uiszczenia", "Data uiszczenia opłaty"),
        ]),
        section(uid("sprawa/zalaczniki"), "zalaczniki", "Załączniki", [
            file_uploader(uid("sprawa/zalaczniki/dowod"), "dowod_wplaty", "Dowód wpłaty"),
            consent_section(uid("sprawa/zalaczniki/zgody"), "zgody", "Zgody",
                            [ConsentItem(description="<html><head></head><body><p>Oświadczam.</p></body></html>", required=True)]),
        ]),
    ])
    koniec = tab(uid("koniec"), "Strona końcowa", [
        section(uid("koniec/info"), "informacja", "Informacja", [
            text_block(uid("koniec/info/tekst"), "tekst", "Tekst", "<html><head></head><body><p>Sprawdź podgląd.</p></body></html>"),
        ]),
    ], finish=True)
    return Form.build("Wniosek o zwrot opłaty skarbowej", [dane, sprawa, koniec], [uid("flow/1"), uid("flow/2")])


def _fields(d: dict):
    for t in d["tabs"]:
        for q in t["questions"]:
            yield q["field"]
            for c in q["field"]["repeatingSectionGrid"]:
                yield c["field"]


def test_helpers_fill_d3_defaults_and_the_exports_key_order() -> None:
    d = build().to_partner()
    assert list(d) == ["title", "tabs", "flow"]
    for f in _fields(d):
        assert all(k in f for k in ALWAYS), f["techName"]
        assert isinstance(f["validation"], list) and f["tooltipMessage"] == ""
        keys = list(f)
        assert keys == [k for k in FIELD_KEYS if k in keys], f["techName"]
    assert d["tabs"][0]["questions"][0]["field"]["description"] == EMPTY_HTML
    assert list(d["tabs"][0]) == ["id", "title", "type", "questions"]
    assert list(d["tabs"][0]["questions"][0]) == ["x", "y", "rows", "cols", "field"]


def test_helpers_lay_out_the_grid() -> None:
    d = build().to_partner()
    sprawa = d["tabs"][1]["questions"]
    assert [(q["y"], q["rows"], q["field"]["questionOrder"]) for q in sprawa] == [(0, 4, 0), (4, 3, 4)]
    comps = sprawa[0]["field"]["repeatingSectionGrid"]
    assert [(c["x"], c["y"], c["rows"], c["cols"], c["field"]["questionOrder"]) for c in comps] == [(0, i, 1, 3, i) for i in range(3)]
    assert [(link["source"], link["target"]) for link in d["flow"]["links"]] == [(uid("dane"), uid("sprawa")), (uid("sprawa"), uid("koniec"))]


def test_form_passes_the_strict_schema_file_and_reads_back_strictly() -> None:
    d = build().to_partner()
    schema = json.loads((CONTRACTS / "form.schema.json").read_text(encoding="utf-8"))
    assert [e.message for e in Draft202012Validator(schema).iter_errors(d)] == []
    assert Form.model_validate(d) == build()


def test_two_builds_give_identical_bytes() -> None:
    a, b = build().to_json_bytes(), build().to_json_bytes()
    assert a == b
    assert Form.model_validate(json.loads(a)).to_json_bytes() == a


def test_negative_component_with_an_unknown_key_is_refused() -> None:
    d = build().to_partner()
    d["tabs"][1]["questions"][0]["field"]["repeatingSectionGrid"][0]["field"]["confidence"] = 0.9
    with pytest.raises(ValidationError, match="confidence"):
        Form.model_validate(d)
    with pytest.raises(ValidationError):
        Form.from_partner_export(d)  # tolerant reading relaxes only the named quirks


def test_negative_fourth_top_level_key_is_refused() -> None:
    d = build().to_partner() | {"meta": {}}
    with pytest.raises(ValidationError):
        Form.model_validate(d)


@pytest.mark.parametrize("quirk", ["validation_object", "link_id", "option_without_tech_name", "min_item_rows", "no_states"])
def test_partner_quirks_strict_refuses_tolerant_reads(quirk: str) -> None:
    d = build().to_partner()
    comp = d["tabs"][1]["questions"][0]["field"]["repeatingSectionGrid"]
    if quirk == "validation_object":
        comp[1]["field"]["validation"] = {}
    elif quirk == "link_id":
        d["flow"]["links"][0]["id"] = "a16ec"
    elif quirk == "option_without_tech_name":
        del comp[0]["field"]["options"][0]["techName"]
    elif quirk == "min_item_rows":
        d["tabs"][1]["questions"][0] = {**d["tabs"][1]["questions"][0], "minItemRows": 2}
    else:
        del comp[1]["field"]["states"]
    if quirk != "no_states":
        with pytest.raises(ValidationError):
            Form.model_validate(copy.deepcopy(d))
    form = Form.from_partner_export(copy.deepcopy(d))
    out = form.to_partner()
    assert [f["techName"] for f in _fields(out)] == [f["techName"] for f in _fields(d)]
    if quirk == "validation_object":
        assert list(_fields(out))[5]["validation"] == []
    if quirk == "no_states":
        assert list(_fields(out))[5]["states"] == []


@pytest.mark.parametrize("breakage", ["duplicate_tech_name", "nested_section", "loose_component", "bad_validator",
                                      "tech_name_too_long", "tech_name_not_slug", "grid_x", "non_uuid_id", "one_page"])
def test_strict_rules(breakage: str) -> None:
    d = build().to_partner()
    secs = d["tabs"][1]["questions"]
    comps = secs[0]["field"]["repeatingSectionGrid"]
    match breakage:
        case "duplicate_tech_name":
            comps[1]["field"]["techName"] = "imie"
        case "nested_section":
            comps.append({**secs[1], "y": 3})
        case "loose_component":
            d["tabs"][1]["questions"].append(comps[0])
        case "bad_validator":
            comps[1]["field"]["validation"] = ["NRB"]
        case "tech_name_too_long":
            comps[1]["field"]["techName"] = "a" * 61
        case "tech_name_not_slug":
            comps[1]["field"]["techName"] = "Numer rachunku"
        case "grid_x":
            comps[1]["x"] = 1
        case "non_uuid_id":
            comps[1]["field"]["id"] = "field-7"
        case "one_page":
            d["tabs"] = d["tabs"][:1]
            d["flow"]["links"] = []
    with pytest.raises(ValidationError):
        Form.model_validate(d)
