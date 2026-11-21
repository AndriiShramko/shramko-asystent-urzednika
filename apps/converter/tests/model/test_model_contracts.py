"""Our four contracts: every example validates against its schema file and its model, model -> JSON -> model is
lossless and byte-stable, the schema files match the models, and the negative controls are refused."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from app.model import Brief, FinderOutput, Meta, PageModel, canonical_json
from app.model.schemas import CONTRACTS, SCHEMAS, main, schema_for

EXAMPLES = CONTRACTS / "examples"
CASES = {"page-model": PageModel, "candidates": FinderOutput, "brief": Brief, "meta": Meta}


def _example(name: str) -> dict:
    return json.loads((EXAMPLES / f"{name}.example.json").read_text(encoding="utf-8"))


def _schema(name: str) -> Draft202012Validator:
    schema = json.loads((CONTRACTS / f"{name}.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_schema_files_match_the_models() -> None:
    assert set(SCHEMAS) == set(CASES)
    assert main(["--check"]) == 0
    for name in SCHEMAS:
        assert schema_for(name)["$schema"] == "https://json-schema.org/draft/2020-12/schema"


@pytest.mark.parametrize("name", sorted(CASES))
def test_example_validates_against_schema_and_model(name: str) -> None:
    data = _example(name)
    errors = sorted(e.message for e in _schema(name).iter_errors(data))
    assert errors == []
    CASES[name].model_validate(data)


@pytest.mark.parametrize("name", sorted(CASES))
def test_round_trip_is_lossless_and_byte_stable(name: str) -> None:
    model = CASES[name].model_validate(_example(name))
    out = canonical_json(model.to_dict())  # everything, resources of meta included
    again = CASES[name].model_validate(json.loads(out))
    assert again == model
    assert canonical_json(again.to_dict()) == out
    assert again.to_json_bytes() == model.to_json_bytes()
    # what we write also passes the schema
    assert list(_schema(name).iter_errors(json.loads(out))) == []


@pytest.mark.parametrize("name", sorted(CASES))
def test_negative_extra_top_level_key_fails_schema_and_model(name: str) -> None:
    data = _example(name) | {"accuracy": 0.97}
    assert any(e.validator == "additionalProperties" for e in _schema(name).iter_errors(data))
    with pytest.raises(ValidationError):
        CASES[name].model_validate(data)


def test_explicit_null_is_refused() -> None:
    data = _example("candidates")
    data["candidates"][0]["group"] = None
    with pytest.raises(ValidationError, match="null is not written"):
        FinderOutput.model_validate(data)
    assert list(_schema("candidates").iter_errors(data))


# -- page model -------------------------------------------------------------------------------------------

def test_negative_run_with_neither_box_nor_anchor_is_refused() -> None:
    data = _example("page-model")
    del data["pages"][0]["runs"][0]["box"]
    with pytest.raises(ValidationError, match="box or an anchor"):
        PageModel.model_validate(data)
    assert list(_schema("page-model").iter_errors(data))


def test_run_with_both_box_and_anchor_is_taken_since_1_1() -> None:
    """Revision 1.1 (placement per element): a native run may carry an anchor beside its box."""
    data = _example("page-model")
    data["pages"][0]["runs"][0]["anchor"] = "p[1]"
    PageModel.model_validate(data)
    assert list(_schema("page-model").iter_errors(data)) == []


def _flow_doc() -> dict:
    return {
        "source": {"sha256": "a" * 64, "format": "doc", "reader": "doc.native", "pages": 1},
        "pages": [{"number": 1, "origin": "flow",
                   "runs": [{"id": "r1", "text": "Wniosek o wydanie zaświadczenia", "anchor": "p[0]"},
                            {"id": "r2", "text": "Imię i nazwisko", "anchor": "p[3]/cell[0,0]"}],
                   "tables": [{"id": "t1", "anchor": "p[3]", "cells": [{"r": 0, "c": 0, "anchor": "p[3]/cell[0,0]", "runs": ["r2"]}]}]}],
    }


def test_flow_page_takes_anchors_and_refuses_boxes() -> None:
    model = PageModel.model_validate(_flow_doc())
    assert PageModel.model_validate(json.loads(model.to_json_bytes())) == model
    bad = _flow_doc()
    bad["pages"][0]["runs"][0] = {"id": "r1", "text": "x", "box": [0, 0, 1, 1]}
    with pytest.raises(ValidationError, match="anchor, not a box"):
        PageModel.model_validate(bad)


def test_native_page_refuses_anchors_and_needs_size() -> None:
    data = _example("page-model")
    run = data["pages"][0]["runs"][0]
    del run["box"]
    run["anchor"] = "p[1]"
    with pytest.raises(ValidationError, match="box, not an anchor"):
        PageModel.model_validate(data)
    data = _example("page-model")
    del data["pages"][0]["width"]
    with pytest.raises(ValidationError, match="width and height"):
        PageModel.model_validate(data)


def test_ids_unique_in_the_document_and_cell_runs_resolve() -> None:
    data = _example("page-model")
    data["pages"][0]["lines"][0]["id"] = "r17"
    with pytest.raises(ValidationError, match="duplicate ids"):
        PageModel.model_validate(data)
    data = _example("page-model")
    data["pages"][0]["tables"][0]["cells"][0]["runs"] = ["r999"]
    with pytest.raises(ValidationError, match="r999"):
        PageModel.model_validate(data)


def test_page_count_and_inverted_box() -> None:
    data = _example("page-model")
    data["source"]["pages"] = 2
    with pytest.raises(ValidationError, match="source.pages"):
        PageModel.model_validate(data)
    data = _example("page-model")
    data["pages"][0]["rects"][0]["box"] = [10, 10, 5, 20]
    with pytest.raises(ValidationError, match="x0 <= x1"):
        PageModel.model_validate(data)


# -- finder output ----------------------------------------------------------------------------------------

def test_candidate_references_resolve() -> None:
    data = _example("candidates")
    data["candidates"][2]["group"] = "c12"  # a comb, not a choice_group
    with pytest.raises(ValidationError, match="not a choice_group"):
        FinderOutput.model_validate(data)
    data = _example("candidates")
    data["candidates"][1]["options"] = data["candidates"][1]["options"][:1]
    with pytest.raises(ValidationError, match="at least two options"):
        FinderOutput.model_validate(data)
    data = _example("candidates")
    data["candidates"][0]["kind"] = "flower"
    with pytest.raises(ValidationError):
        FinderOutput.model_validate(data)


def test_roles_serialise_sorted() -> None:
    data = _example("candidates")
    data["roles"] = {"r90": "clause", "r1": "page_furniture", "r5": "body"}
    out = json.loads(FinderOutput.model_validate(data).to_json_bytes())
    assert list(out["roles"]) == ["r1", "r5", "r90"]


# -- brief ------------------------------------------------------------------------------------------------

def test_status_needs_its_evidence() -> None:
    data = _example("brief")
    data["title"]["evidence"] = []
    with pytest.raises(ValidationError, match="'stated' needs evidence"):
        Brief.model_validate(data)
    data = _example("brief")
    data["fee"] = {"status": "not_found", "value": "82 zł"}
    with pytest.raises(ValidationError, match="not_found"):
        Brief.model_validate(data)
    data = _example("brief")
    data["fee"] = {"status": "ambiguous"}
    with pytest.raises(ValidationError, match="competing quotes"):
        Brief.model_validate(data)


def test_required_needs_a_basis_and_conditions_resolve() -> None:
    data = _example("brief")
    del data["matter"][0]["fields"][0]["required_basis"]
    with pytest.raises(ValidationError, match="basis"):
        Brief.model_validate(data)
    data = _example("brief")
    data["matter"][2]["fields"][1]["show_if"] = {"field": "sposob_zwrotu", "is": "Czekiem"}
    with pytest.raises(ValidationError, match="Czekiem"):
        Brief.model_validate(data)
    data = _example("brief")
    data["matter"][2]["fields"][1]["show_if"] = {"field": "nie_ma_takiego", "is": "x"}
    with pytest.raises(ValidationError, match="nie_ma_takiego"):
        Brief.model_validate(data)
    data = _example("brief")
    data["matter"][1]["fields"][0]["key"] = "wysokosc_oplaty"
    with pytest.raises(ValidationError, match="duplicate field keys"):
        Brief.model_validate(data)


def test_condition_tree_shapes() -> None:
    data = _example("brief")
    leaf = {"field": "sposob_zwrotu", "is": "Przelewem na rachunek w banku"}
    data["matter"][2]["fields"][2]["show_if"] = {"not": {"any_of": [leaf, {"field": "sposob_zwrotu", "is": "Gotówką w kasie organu"}]}}
    brief = Brief.model_validate(data)
    assert json.loads(brief.to_json_bytes())["matter"][2]["fields"][2]["show_if"]["not"]["any_of"][0] == leaf
    data["matter"][2]["fields"][2]["show_if"] = {"field": "sposob_zwrotu", "is": "Gotówką w kasie organu", "any_of": [leaf, leaf]}
    with pytest.raises(ValidationError, match="exactly one of"):
        Brief.model_validate(data)


# -- meta -------------------------------------------------------------------------------------------------

def test_negative_ledger_that_does_not_close_is_refused() -> None:
    data = _example("meta")
    data["ledger"]["blanks_found"] = 5
    with pytest.raises(ValidationError, match="does not close"):
        Meta.model_validate(data)


def test_deleting_the_fate_of_one_candidate_is_refused() -> None:
    """F15 negative control: a blank without its row cannot pass, even when the counts are adjusted."""
    data = _example("meta")
    data["ledger"]["rows"].pop()
    with pytest.raises(ValidationError, match="does not close"):
        Meta.model_validate(data)
    data["ledger"]["blanks_found"], data["ledger"]["left_out"] = 3, 0
    Meta.model_validate(data)  # consistent again: 3 blanks, 3 rows
    data["ledger"]["rows"][0]["fate"] = "LEFT_OUT"
    data["ledger"]["rows"][0]["reason"] = "OFFICE_USE"
    with pytest.raises(ValidationError, match="rows by fate"):
        Meta.model_validate(data)


def test_ledger_row_needs_the_key_of_its_fate() -> None:
    data = _example("meta")
    del data["ledger"]["rows"][1]["into"]
    with pytest.raises(ValidationError, match="MERGED needs into"):
        Meta.model_validate(data)
    data = _example("meta")
    data["ledger"]["rows"][3]["reason"] = "BECAUSE"
    with pytest.raises(ValidationError):
        Meta.model_validate(data)


def test_decisions_resolve_warnings_and_coverage_adds_up() -> None:
    data = _example("meta")
    data["decisions"][0]["resolves"].append("warning-9")
    with pytest.raises(ValidationError, match="warning-9"):
        Meta.model_validate(data)
    data = _example("meta")
    data["coverage"]["unassigned"] = ["r7"]
    with pytest.raises(ValidationError, match="coverage"):
        Meta.model_validate(data)


def test_meta_is_deterministic_without_resources() -> None:
    a = _example("meta")
    b = copy.deepcopy(a)
    b["resources"]["wall_ms"] = 12345
    b["origins"] = dict(reversed(list(b["origins"].items())))
    assert Meta.model_validate(a).to_json_bytes() == Meta.model_validate(b).to_json_bytes()
    assert Meta.model_validate(a).to_json_bytes(deterministic=False) != Meta.model_validate(b).to_json_bytes(deterministic=False)


def test_the_word_accuracy_is_not_in_the_meta_contract() -> None:
    text = (CONTRACTS / "meta.schema.json").read_text(encoding="utf-8").lower()
    assert "accuracy" not in text
    assert Path(EXAMPLES / "meta.example.json").read_text(encoding="utf-8").lower().count("accuracy") == 0
