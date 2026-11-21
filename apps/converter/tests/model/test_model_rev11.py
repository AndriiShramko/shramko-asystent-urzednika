"""Revision 1.1 of our four contracts (verification plan 5; WP-F0c): additive. Every 1.0 example still validates and
is written byte for byte as before; the 1.1 examples validate against the schema files and the models; each new
rule has a test, and the negative controls of the stage are here."""
from __future__ import annotations

import copy
import json
import math
import re
from pathlib import Path
from typing import get_args

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from app.model import (
    Box,
    Brief,
    FinderOutput,
    LedgerError,
    Line,
    Meta,
    PageModel,
    Rect,
    Run,
    Widget,
    assemble_ledger,
    canonical_json,
    check_paper_evidence,
    count_coverage,
)
from app.model.common import WarningCode
from app.model.schemas import CONTRACTS

EXAMPLES = CONTRACTS / "examples"
CASES = {"page-model": PageModel, "candidates": FinderOutput, "brief": Brief, "meta": Meta}
NEW_KEYS = {"spans", "leader", "region", "footnote", "pictures", "ink", "row_heights", "col_widths", "field", "values",
            "on_state", "options", "mandatory_attachments", "proposed_fee", "dispositions", "page_title", "kind", "gaps"}
FORM_IDS = {"gatunek": "00000000-0000-5000-8000-0000000000a1", "numer_dzialki": "00000000-0000-5000-8000-0000000000a2"}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema(name: str) -> Draft202012Validator:
    return Draft202012Validator(_load(CONTRACTS / f"{name}.schema.json"))


def _rev11(name: str, suffix: str = "rev11") -> dict:
    return _load(EXAMPLES / f"{name}.{suffix}.example.json")


ALL_EXAMPLES = sorted((n, p) for n in CASES for p in EXAMPLES.glob(f"{n}*.example.json"))


# -- the old examples, the new examples -------------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(CASES))
def test_negative_control_old_1_0_example_still_validates(name: str) -> None:
    data = _load(EXAMPLES / f"{name}.example.json")
    assert data[{"page-model": "model_version", "candidates": "finder_version", "brief": "brief_version",
                 "meta": "meta_version"}[name]] == 1
    assert list(_schema(name).iter_errors(data)) == []
    model = CASES[name].model_validate(data)
    out = canonical_json(model.to_dict())
    assert CASES[name].model_validate(json.loads(out)) == model


@pytest.mark.parametrize(("name", "path"), ALL_EXAMPLES, ids=[p.name for _, p in ALL_EXAMPLES])
def test_every_example_validates_and_round_trips(name: str, path: Path) -> None:
    data = _load(path)
    assert sorted(e.message for e in _schema(name).iter_errors(data)) == []
    model = CASES[name].model_validate(data)
    out = canonical_json(model.to_dict())
    again = CASES[name].model_validate(json.loads(out))
    assert again == model and canonical_json(again.to_dict()) == out
    assert list(_schema(name).iter_errors(json.loads(out))) == []


def _keys(obj: object) -> set[str]:
    if isinstance(obj, dict):
        return set(obj) | {k for v in obj.values() for k in _keys(v)}
    if isinstance(obj, list):
        return {k for v in obj for k in _keys(v)}
    return set()


@pytest.mark.parametrize("name", sorted(CASES))
def test_a_1_0_document_writes_no_1_1_key(name: str) -> None:
    """Left out while unused: the output of a 1.0 document has the same keys as revision 1.0 wrote."""
    out = json.loads(CASES[name].model_validate(_load(EXAMPLES / f"{name}.example.json")).to_json_bytes())
    old_keys = _keys(_load(EXAMPLES / f"{name}.example.json"))
    assert not ((_keys(out) - old_keys) & (NEW_KEYS - {"options", "field", "kind"}))
    if name == "brief":  # "kind" exists on the addressee in 1.0; a consent writes it only when it is a declaration
        data = _load(EXAMPLES / "brief.example.json")
        data["declarations"]["consents"] = [{"text": "Zgoda"}]
        assert "kind" not in json.loads(Brief.model_validate(data).to_json_bytes())["declarations"]["consents"][0]


def test_new_documents_say_1_1() -> None:
    data = _load(EXAMPLES / "page-model.example.json")
    del data["model_version"]
    assert json.loads(PageModel.model_validate(data).to_json_bytes())["model_version"] == 1.1
    data["model_version"] = 1.2
    with pytest.raises(ValidationError):
        PageModel.model_validate(data)


# -- 1. placement per element -----------------------------------------------------------------------------

def test_flow_page_mixes_paragraphs_and_anchored_boxes() -> None:
    model = PageModel.model_validate(_rev11("page-model"))
    run = model.pages[0].runs[4]
    assert run.box is not None and run.anchor == "p[6]"


def test_negative_control_element_with_neither_box_nor_anchor_is_refused() -> None:
    data = _rev11("page-model")
    del data["pages"][0]["runs"][4]["box"]
    del data["pages"][0]["runs"][4]["anchor"]
    with pytest.raises(ValidationError, match="box or an anchor"):
        PageModel.model_validate(data)
    assert list(_schema("page-model").iter_errors(data))
    cand = _rev11("candidates")
    del cand["candidates"][3]["box"], cand["candidates"][3]["anchor"]
    with pytest.raises(ValidationError, match="box or an anchor"):
        FinderOutput.model_validate(cand)


def test_flow_page_still_needs_anchors_and_size_for_drawings() -> None:
    data = _rev11("page-model")
    del data["pages"][0]["runs"][4]["anchor"]  # a box alone on a flow page
    with pytest.raises(ValidationError, match="anchor, not a box"):
        PageModel.model_validate(data)
    data = _rev11("page-model")
    del data["pages"][0]["width"], data["pages"][0]["height"]  # lines and pictures without the page size
    with pytest.raises(ValidationError, match="states its size"):
        PageModel.model_validate(data)
    data = _rev11("page-model")
    del data["pages"][0]["height"]
    with pytest.raises(ValidationError, match="together"):
        PageModel.model_validate(data)


# -- 3. spans and coverage --------------------------------------------------------------------------------

def test_spans_resolve_and_coverage_counts_them() -> None:
    pages, finder = PageModel.model_validate(_rev11("page-model")), FinderOutput.model_validate(_rev11("candidates"))
    finder.check_spans(pages)
    text = pages.run_index()["r4"][1].text
    assert [text[s.start:s.end] for _, s in finder.all_spans()] == ["Gatunek:", "pies", "kot", "❑", "❑"]
    cov = count_coverage(finder, pages)
    assert cov == Meta.model_validate(_rev11("meta")).coverage
    data = _rev11("candidates")
    data["candidates"][0]["options"][1]["spans"] = [{"run": "r4", "start": 18, "end": 20}]  # "ko", not "kot"
    cov = count_coverage(FinderOutput.model_validate(data), pages)
    assert (cov.assigned, cov.unassigned, [(g.run, g.start, g.end) for g in cov.gaps]) == (6, ["r4"], [("r4", 20, 21)])


def test_negative_control_span_past_the_text_of_its_run_is_refused() -> None:
    pages = PageModel.model_validate(_rev11("page-model"))
    data = _rev11("candidates")
    data["candidates"][0]["options"][1]["spans"] = [{"run": "r4", "start": 18, "end": 22}]  # the run has 21 characters
    finder = FinderOutput.model_validate(data)
    with pytest.raises(ValueError, match="runs past the text of run r4"):
        finder.check_spans(pages)
    with pytest.raises(ValueError, match="runs past"):
        count_coverage(finder, pages)
    data["candidates"][0]["options"][1]["spans"] = [{"run": "r99", "start": 0, "end": 1}]
    with pytest.raises(ValueError, match="r99 is not in the page model"):
        FinderOutput.model_validate(data).check_spans(pages)
    data["candidates"][0]["options"][1]["spans"] = [{"run": "r4", "start": 5, "end": 5}]
    with pytest.raises(ValidationError, match="greater than start"):
        FinderOutput.model_validate(data)


# -- 2. dispositions and the ledger -----------------------------------------------------------------------

def test_ledger_is_assembled_from_the_dispositions() -> None:
    finder, brief = FinderOutput.model_validate(_rev11("candidates")), Brief.model_validate(_rev11("brief"))
    ledger = assemble_ledger(finder, brief.dispositions, FORM_IDS)
    assert ledger == Meta.model_validate(_rev11("meta")).ledger


def test_negative_control_ledger_missing_a_finder_candidate_is_refused() -> None:
    finder, brief = FinderOutput.model_validate(_rev11("candidates")), Brief.model_validate(_rev11("brief"))
    with pytest.raises(LedgerError, match=r"without a disposition: \['c51'\]"):
        assemble_ledger(finder, brief.dispositions[:-1], FORM_IDS)
    data = _rev11("candidates")
    data["candidates"] = data["candidates"][:-1]
    with pytest.raises(LedgerError, match=r"the finder does not have: \['c51'\]"):
        assemble_ledger(FinderOutput.model_validate(data), brief.dispositions, FORM_IDS)


def test_ledger_targets_must_resolve() -> None:
    finder, brief = FinderOutput.model_validate(_rev11("candidates")), Brief.model_validate(_rev11("brief"))
    with pytest.raises(LedgerError, match="'numer_dzialki' has no form id"):
        assemble_ledger(finder, brief.dispositions, {"gatunek": FORM_IDS["gatunek"]})
    data = _rev11("brief")
    data["dispositions"][0] = {"candidate": "c40", "fate": "MERGED", "into": "c41", "why": "GROUP_MEMBER"}
    with pytest.raises(LedgerError, match="circle"):
        assemble_ledger(finder, Brief.model_validate(data).dispositions, FORM_IDS)
    data = _rev11("brief")
    data["dispositions"][4] = {"candidate": "c51", "fate": "AWAITING_DECISION", "decision": "dec-7"}
    disp = Brief.model_validate(data).dispositions
    assert assemble_ledger(finder, disp, FORM_IDS).awaiting_decision == 1
    with pytest.raises(LedgerError, match="dec-7 is not listed"):
        assemble_ledger(finder, disp, FORM_IDS, decisions={"dec-1"})


def test_dispositions_are_checked_in_the_brief() -> None:
    for change, msg in [
        ({"candidate": "c40", "fate": "FIELD", "key": "nie_ma"}, "not a field or attachment"),
        ({"candidate": "c40", "fate": "FIELD"}, "needs key"),
        ({"candidate": "c40", "fate": "FIELD", "key": "gatunek", "reason": "OFFICE_USE"}, "does not take"),
        ({"candidate": "c40", "fate": "MERGED", "into": "c99", "why": "GROUP_MEMBER"}, "has no disposition"),
        ({"candidate": "c40", "fate": "MERGED", "into": "c40", "why": "GROUP_MEMBER"}, "into itself"),
        ({"candidate": "c41", "fate": "LEFT_OUT", "reason": "OFFICE_USE"}, "duplicate candidates"),
    ]:
        data = _rev11("brief")
        data["dispositions"][0] = change
        with pytest.raises(ValidationError, match=msg):
            Brief.model_validate(data)


# -- 4. applicant options ---------------------------------------------------------------------------------

def test_applicant_selector_is_a_condition_target_only_with_options() -> None:
    brief = Brief.model_validate(_rev11("brief"))
    assert [o.key for o in brief.applicants.options] == ["osobiscie", "pelnomocnik_osoby"]
    data = _rev11("brief")
    data["attachments"][0]["show_if"]["is"] = "reprezentant_podmiotu"
    with pytest.raises(ValidationError, match="not an applicant option"):
        Brief.model_validate(data)
    data = _rev11("brief")
    del data["applicants"]["options"]
    with pytest.raises(ValidationError, match="'applicant', which is not in the brief"):
        Brief.model_validate(data)
    data = _rev11("brief")
    data["applicants"]["options"].append({"key": "osobiscie", "party": "entity"})
    with pytest.raises(ValidationError, match="duplicate applicant option keys"):
        Brief.model_validate(data)


# -- 6. widgets and the yes-or-no checkbox ----------------------------------------------------------------

def test_widget_values_and_the_optionless_checkbox() -> None:
    w = PageModel.model_validate(_rev11("page-model")).pages[0].widgets
    assert (w[0].field, w[0].values[0].export, w[1].on_state) == ("Zwrot", "gotowka", "przelew")
    data = _rev11("brief")
    data["matter"][1]["show_if"]["is"] = "tak"
    with pytest.raises(ValidationError, match="'true' or 'false'"):
        Brief.model_validate(data)
    data = _rev11("brief")
    data["matter"][0]["fields"][0]["options"] = []
    with pytest.raises(ValidationError, match="RADIO lists its options"):
        Brief.model_validate(data)


# -- 5. reader facts --------------------------------------------------------------------------------------

def test_sheet_sizes_and_reader_facts() -> None:
    sheet = PageModel.model_validate(_rev11("page-model", "rev11-sheet")).pages[0]
    assert (sheet.row_heights, sheet.col_widths, sheet.ink) == ([15.0, 15.0, 30.0], [48.0, 120.0], True)
    data = _rev11("page-model", "rev11-sheet")
    data["pages"][0]["row_heights"][0] = -1
    with pytest.raises(ValidationError, match="not negative"):
        PageModel.model_validate(data)
    data = _rev11("page-model")
    data["pages"][0]["runs"][2]["leader"] = "stars"
    with pytest.raises(ValidationError):
        PageModel.model_validate(data)


# -- 7. evidence ------------------------------------------------------------------------------------------

def test_evidence_lists_and_located_blanks() -> None:
    meta = Meta.model_validate(_rev11("meta"))
    assert [len(meta.evidence_of(i)) for i in sorted(FORM_IDS.values())] == [2, 1]
    assert meta.evidence_of("nie-ma") == []
    old = Meta.model_validate(_load(EXAMPLES / "meta.example.json"))
    assert old.evidence_of("00000000-0000-5000-8000-000000000026")[0].quote == "Numer rachunku"
    data = _rev11("meta")
    data["evidence"]["00000000-0000-5000-8000-0000000000a2"] = []
    with pytest.raises(ValidationError, match="not empty"):
        Meta.model_validate(data)
    data = _rev11("meta")
    del data["evidence"]["00000000-0000-5000-8000-0000000000a2"]["box"], data["evidence"]["00000000-0000-5000-8000-0000000000a2"]["anchor"]
    with pytest.raises(ValidationError, match="box or an anchor"):
        Meta.model_validate(data)


def test_stated_still_needs_a_quote() -> None:
    data = _rev11("brief")
    data["title"]["evidence"] = [{"page": 1, "anchor": "p[0]"}]
    with pytest.raises(ValidationError, match="needs evidence with a quote"):
        Brief.model_validate(data)


def test_paper_requirement_without_evidence_is_a_warning() -> None:
    assert check_paper_evidence(Brief.model_validate(_rev11("brief"))) == []
    old = Brief.model_validate(_load(EXAMPLES / "brief.example.json"))  # 1.0 data loads; the check only warns
    assert [(w.code, w.field) for w in check_paper_evidence(old)] == [("REQUIRED_WITHOUT_EVIDENCE", "sposob_zwrotu")]


# -- 8. receipts, proposed fee, declarations --------------------------------------------------------------

def test_receipt_fee_proposal_and_declaration() -> None:
    brief = Brief.model_validate(_rev11("brief"))
    assert brief.fee.status == "not_found" and brief.proposed_fee is not None and brief.proposed_fee.value == "17 zł"
    assert brief.mandatory_attachments is not None and brief.mandatory_attachments.status == "not_found"
    assert brief.declarations.consents[0].kind == "declaration"
    meta = Meta.model_validate(_rev11("meta"))
    assert meta.receipts.fee.status == "not_found" and meta.proposals.fee is not None
    data = _rev11("brief")
    data["declarations"]["consents"][0]["kind"] = "promise"
    with pytest.raises(ValidationError):
        Brief.model_validate(data)


# -- 9. constructors at the reader boundary ---------------------------------------------------------------

def test_box_from_raw_normalises_and_refuses_to_invent() -> None:
    assert Box.from_raw(10, 20, 5, 8) == (5.0, 8.0, 10.0, 20.0)
    assert Box.from_raw(0, 0, math.nan, 1) is None
    assert Box.from_raw(0, 0, "x", 1) is None


def test_safe_builders_warn_instead_of_raising() -> None:
    run, warns = Run.safe(3, id="r1", text="Nazwisko", box=(100, 50, 20, 40), size=0)
    assert run is not None and run.box == (20.0, 40.0, 100.0, 50.0) and run.size is None
    assert [(w.code, w.page, w.box) for w in warns] == [("UNREADABLE_PART", 3, (20.0, 40.0, 100.0, 50.0))]
    run, warns = Run.safe(1, id="r2", text="x", box=(0, 0, math.inf, 1))
    assert run is None and len(warns) == 2 and all(w.code == "UNREADABLE_PART" for w in warns)
    run, warns = Run.safe(1, id="r3", text="x", anchor="p[2]", conf=1.5)
    assert run is not None and run.conf == 1.0 and warns[0].anchor == "p[2]"
    rect, warns = Rect.safe(1, id="q1", box=[9, 9, 1, 1])
    assert rect is not None and rect.box == (1.0, 1.0, 9.0, 9.0) and warns == []
    line, warns = Line.safe(1, id="l1", box=None)
    assert line is None and "skipped" in (warns[0].detail or "")
    widget, warns = Widget.safe(1, id="w1", kind="text", box=(0, 0, 10, 10), max_len=0)
    assert widget is not None and widget.max_len is None and "max_len" in (warns[0].detail or "")


# -- 10. composer requests --------------------------------------------------------------------------------

def test_composer_remark_codes_are_warning_codes() -> None:
    src = "\n".join(p.read_text(encoding="utf-8") for p in (Path(__file__).resolve().parents[2] / "app" / "compose").glob("*.py"))
    codes = set(re.findall(r'Remark\(\s*"([A-Z_]+)"', src))
    assert len(codes) >= 10
    assert codes <= set(get_args(WarningCode))


def test_matter_page_title_hint_and_attachment_key() -> None:
    brief = Brief.model_validate(_rev11("brief"))
    assert (brief.matter[0].page_title, brief.attachments[0].key) == ("Informacje o zwierzęciu", "pelnomocnictwo")
    data = _rev11("brief")
    data["attachments"].append(copy.deepcopy(data["attachments"][0]))
    with pytest.raises(ValidationError, match="duplicate attachment keys"):
        Brief.model_validate(data)
