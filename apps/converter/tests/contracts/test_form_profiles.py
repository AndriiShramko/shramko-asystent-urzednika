"""WP-F0a: the two profiles of the form schema, the rule checker, the golden list.

Forms are built here from code (synthetic values only). The two partner exports and the golden inputs are
local only: tests that need them carry the `sets` marker and are skipped where the sets are absent.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from eval.golden import golden_inputs, judged_inputs, load
from tools.coi_lint import check
from tools.coi_paths import coi_dir, sets


def u() -> str:
    return str(uuid.uuid4())


def component(tech: str, kind: str = "TEXT_FIELD", **extra) -> dict:
    field = {"id": u(), "type": kind, "techName": tech, "title": tech.capitalize(), "description": "",
             "options": [], "validation": [], "readOnly": False, "repeatingSectionGrid": [],
             "questionOrder": 0, "tooltipMessage": "", "states": []}
    field.update(extra)
    return {"x": 0, "y": 0, "rows": 1, "cols": 3, "field": field}


def section(tech: str, inner: list[dict], y: int = 0) -> dict:
    q = component(tech, "SECTION")
    q["y"], q["rows"] = y, len(inner) + 1
    q["field"]["repeatingSectionGrid"] = inner
    for i, c in enumerate(inner):
        c["y"] = i
    return q


def minimal() -> dict:
    page1, page2 = u(), u()
    return {
        "title": "Synthetic request",
        "tabs": [
            {"id": page1, "title": "Dane", "type": "MAIN",
             "questions": [section("dane", [component("nazwa")])]},
            {"id": page2, "title": "Strona koncowa", "type": "FINISH",
             "questions": [section("podglad", [component("podglad_1", "TEXT_BLOCK")])]},
        ],
        "flow": {"links": [{"id": u(), "source": page1, "target": page2}]},
    }


def errors(doc: dict, profile: str = "strict") -> list[str]:
    return [m for k, m in check(doc, profile) if k == "ERROR"]


# ---- synthetic forms (always run) -------------------------------------------------------------

def test_minimal_form_passes_strict_and_tolerant():
    assert errors(minimal()) == []
    assert errors(minimal(), "tolerant") == []


def test_negative_control_fourth_top_level_key_fails_strict():
    doc = minimal()
    doc["meta"] = {"origin": "paper"}
    found = errors(doc)
    assert any("Additional properties" in m and "meta" in m for m in found), found
    # the tolerant profile does not forbid it
    assert errors(doc, "tolerant") == []


def _misspelled(d):
    f = d["tabs"][0]["questions"][0]["field"]
    f["repetingSectionGrid"] = f.pop("repeatingSectionGrid")


def _component_on_page(d):
    d["tabs"][0]["questions"].append(component("luzem"))


def _nested_section(d):
    d["tabs"][0]["questions"][0]["field"]["repeatingSectionGrid"].append(section("zagniezdzona", [component("x1")]))


def _input_on_finish(d):
    d["tabs"][1]["questions"][0]["field"]["repeatingSectionGrid"].append(component("pole_na_koncu"))


def _state_to_nowhere(d):
    c = d["tabs"][0]["questions"][0]["field"]["repeatingSectionGrid"][0]["field"]
    c["states"] = [{"type": "SHOW", "query": "tabs['Dane' in title].questions['nie_ma' in field.techName].field.options = 'a'"}]


def _duplicate_id(d):
    d["tabs"][1]["id"] = d["tabs"][0]["id"]


@pytest.mark.parametrize("mutate,needle", [
    (_misspelled, "repetingSectionGrid"),
    (_component_on_page, "sits directly on the page"),
    (_nested_section, "section inside a section"),
    (_input_on_finish, "FINISH page"),
    (_state_to_nowhere, "none exists"),
    (_duplicate_id, "id used twice"),
], ids=lambda x: getattr(x, "__name__", x))
def test_linter_negative_controls_still_fail(mutate, needle):
    doc = minimal()
    mutate(doc)
    found = errors(doc)
    assert any(needle in m for m in found), found


def test_strict_demands_the_d3_keys_and_lists():
    doc = minimal()
    inner = doc["tabs"][0]["questions"][0]["field"]["repeatingSectionGrid"][0]["field"]
    inner["validation"] = {}
    del inner["states"]
    found = errors(doc)
    assert any("validation" in m for m in found) and any("'states' is a required" in m for m in found), found
    assert errors(doc, "tolerant") == []


def test_tolerant_reads_the_partner_departures_as_warnings():
    doc = minimal()
    doc["flow"]["links"][0]["id"] = "a16ec"
    doc["tabs"][0]["questions"][0]["field"]["repeatingSectionGrid"][0]["field"]["options"] = [{"id": "1", "name": "A"}]
    doc["tabs"][0]["questions"][0]["minItemRows"] = 1
    assert errors(doc) != []
    assert errors(doc, "tolerant") == []
    warns = [m for k, m in check(doc, "tolerant") if k == "WARN"]
    assert sum(m.startswith("departs from strict") for m in warns) == 3, warns


def test_strict_is_not_loosened_for_ids_and_options():
    doc = minimal()
    doc["tabs"][0]["id"] = "not-a-uuid"
    assert any("does not match" in m for m in errors(doc))


# ---- the partner's exports (local only) -------------------------------------------------------

def _exports() -> list[Path]:
    out = []
    for s in sets("reference"):
        out += sorted(s.glob("*.json"))
    return out


@pytest.mark.sets
def test_both_exports_pass_tolerant_with_zero_errors():
    files = _exports()
    assert len(files) == 2, files
    for p in files:
        doc = json.loads(p.read_text(encoding="utf-8"))
        assert errors(doc, "tolerant") == [], p.name


@pytest.mark.sets
def test_both_exports_fail_strict_for_the_listed_reasons():
    reasons = {}
    for p in _exports():
        doc = json.loads(p.read_text(encoding="utf-8"))
        reasons[p.name] = "\n".join(errors(doc))
    one = next(v for k, v in reasons.items() if "Numeru" in k)
    five = next(v for k, v in reasons.items() if "Nadp" in k)
    # export 1: validation as {} (3), minItemRows, a section without states
    assert one.count("validation") == 3 and "minItemRows" in one and "'states' is a required" in one
    # export 5: three link ids that are not UUIDs and one option without techName
    assert five.count("flow/links") == 3 and "options" in five and "'techName' is a required" in five


# ---- the golden list ---------------------------------------------------------------------------

def test_golden_list_shape_is_relative_and_complete():
    data = load()
    assert [len(s["inputs"]) for s in data["reference"]] == [8, 7]
    assert len([s["expected"] for s in data["reference"] if s["expected"]]) == 2
    assert len(data["judged"]) == 7
    everything = [f for k in ("reference", "judged") for s in data[k] for f in s["inputs"]]
    everything += [s["expected"] for s in data["reference"]]
    for f in everything:
        assert not Path(f["path"]).is_absolute() and ":" not in f["path"] and ".." not in f["path"]
        assert f["path"].count("/") == 1 and f["size"] > 0
        assert f["format"] in {"pdf", "doc", "docx", "ods", "xlsx", "jpg", "jpeg", "png", "json"}


@pytest.mark.sets
def test_golden_files_exist_on_this_machine():
    assert len(golden_inputs()) == 15
    missing = [p.name for p in golden_inputs() + judged_inputs() if not p.exists()]
    assert missing == []
    data = load()
    for s in data["reference"]:
        assert (coi_dir() / s["expected"]["path"]).exists()
