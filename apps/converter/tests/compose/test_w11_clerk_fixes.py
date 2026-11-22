"""W11 CLERK-S: every remark the converter can answer carries a ready `fix` (applied, choice or input), and a remark
it resolved itself is not shown to the official. Synthetic briefs only: the offices and the places are invented."""
from __future__ import annotations

import copy
import json
from typing import Any

from app.compose import CLAUSE_OCR_ATTACH, ComposeOptions, compose, fixes
from app.model.form import EMPTY_HTML
from app.model.sidecar import RunWarning
from tests.compose.compose_helpers import brief

PAPER = ComposeOptions(required_policy="paper")
EV = {"page": 2, "box": [50.0, 400.0, 500.0, 412.0], "quote": "Administratorem danych jest Burmistrz Miasta Przykładowa"}
EV2 = {"page": 1, "box": [300.0, 90.0, 520.0, 102.0], "quote": "Urząd Gminy Wzorcowo"}


def _office(name: str, ev: dict[str, Any], kind: str = "office") -> dict[str, Any]:
    return {"kind": kind, "name": name, "evidence": ev}


def _run(b: Any, options: ComposeOptions | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """The form as JSON and the composer's remarks as the sidecar carries them (the pipeline does the same)."""
    r = compose(b, options or ComposeOptions())
    form = json.loads(r.form.to_json_bytes())
    warnings = [{"code": x.code, "detail": x.detail} for x in r.remarks]
    hints = {i: x.fix for i, x in enumerate(r.remarks) if x.fix}
    out = fixes.attach(form, warnings, hints, r.paths, r.brief_keys)
    for w in out:
        RunWarning.model_validate(w)          # the contract of the sidecar holds
    return form, out


def _at(form: dict[str, Any], pointer: str) -> Any:
    node: Any = form
    for part in pointer.strip("/").split("/"):
        node = node[int(part)] if isinstance(node, list) else node[part]
    return node


def _apply(form: dict[str, Any], sets: list[dict[str, Any]], typed: str | None = None) -> dict[str, Any]:
    out = copy.deepcopy(form)
    for s in sets:
        head, _, last = s["pointer"].rpartition("/")
        parent = _at(out, head)                # the node itself always exists: a set never adds a tab, a question or a cell
        assert isinstance(parent, dict) and "techName" in parent, s["pointer"]
        parent[last] = typed if s.get("from") == "input" else s["value"]   # the key may be new (defaultValue is left out when none)
    return out


def _fix(warnings: list[dict[str, Any]], code: str) -> dict[str, Any]:
    return next(w for w in warnings if w["code"] == code)["fix"]


# -- ADDRESSEE_MISSING ---------------------------------------------------------------------------------------------------

def test_no_office_on_the_paper_is_an_input_with_the_place() -> None:
    form, ws = _run(brief(addressee={"status": "not_found"}))
    fix = _fix(ws, "ADDRESSEE_MISSING")
    assert fix["kind"] == "input" and fix["rule"] == "addressee.not_on_paper"
    node = _at(form, fix["target"]["pointer"])
    assert node["id"] == fix["target"]["id"] and node["techName"] == "nazwa_urzedu" and fix["target"]["tab"] == "Dane"
    typed = _apply(form, fix["input"]["set"], "Urząd Gminy Wpisany")
    assert _at(typed, fix["target"]["pointer"])["defaultValue"] == "Urząd Gminy Wpisany"
    assert fixes.seen_by_clerk({"code": "ADDRESSEE_MISSING", "fix": fix})


def test_one_office_found_on_the_paper_is_written_and_not_shown_to_the_official() -> None:
    a = {"status": "stated", "kind": "body", "name": "Burmistrz Miasta Przykładowa", "evidence": [EV],
         "candidates": [_office("Burmistrz Miasta Przykładowa", EV, "body")]}
    form, ws = _run(brief(addressee=a))
    fix = _fix(ws, "ADDRESSEE_MISSING")
    assert (fix["kind"], fix["value"]) == ("applied", "Burmistrz Miasta Przykładowa")
    assert fix["source"] == {"type": "paper", **EV}
    node = _at(form, fix["target"]["pointer"])
    assert node["defaultValue"] == "Burmistrz Miasta Przykładowa" and node["readOnly"] is True and node["techName"] == "nazwa_organu"
    assert not fixes.seen_by_clerk({"code": "ADDRESSEE_MISSING", "fix": fix})


def test_several_offices_are_a_choice_with_the_most_likely_written() -> None:
    a = {"status": "ambiguous", "kind": "office", "name": "Urząd Gminy Wzorcowo", "evidence": [EV2, EV],
         "candidates": [_office("Urząd Gminy Wzorcowo", EV2), _office("Burmistrz Miasta Przykładowa", EV, "body")]}
    form, ws = _run(brief(addressee=a))
    fix = _fix(ws, "ADDRESSEE_MISSING")
    assert fix["kind"] == "choice" and [o["current"] for o in fix["options"]] == [True, False]
    assert [o["source"]["page"] for o in fix["options"]] == [1, 2]
    assert _at(form, fix["target"]["pointer"])["defaultValue"] == "Urząd Gminy Wzorcowo"       # the first is in the form
    assert _apply(form, fix["options"][0]["set"]) == form                                        # the current option changes nothing
    picked = _at(_apply(form, fix["options"][1]["set"]), fix["target"]["pointer"])
    assert picked["defaultValue"] == "Burmistrz Miasta Przykładowa" and picked["readOnly"] is True
    assert fix["input"]["set"][0]["from"] == "input"                                             # the last door: another office


def test_an_addressee_block_gives_no_remark_as_before() -> None:
    _form, ws = _run(brief())
    assert "ADDRESSEE_MISSING" not in {w["code"] for w in ws}


# -- CLAUSE_LINK_MISSING -------------------------------------------------------------------------------------------------

def _clause(origin: str, conf: float) -> dict[str, Any]:
    return {"consents": [], "clause": {"status": "stated", "evidence": [{"page": 2, "quote": "Klauzula informacyjna"}]},
            "clause_text": {"paragraphs": ["Klauzula informacyjna", "1. Administratorem danych jest Wójt Gminy Wzorcowo <b>."],
                            "origin": origin, "conf": conf, "evidence": [{"page": 2, "box": [40.0, 300.0, 550.0, 700.0], "quote": "Klauzula informacyjna"}]}}


def _consent_section(form: dict[str, Any], fix: dict[str, Any]) -> dict[str, Any]:
    node = _at(form, fix["target"]["pointer"])
    assert node["type"] == "SECTION" and [c["field"]["type"] for c in node["repeatingSectionGrid"]] == ["CONSENT_SECTION"]
    return node


def test_no_clause_on_the_paper_is_the_consent_of_the_exports_and_no_question() -> None:
    form, ws = _run(brief())
    fix = _fix(ws, "CLAUSE_LINK_MISSING")
    assert (fix["kind"], fix["rule"], fix["source"]["type"]) == ("applied", "clause.as_partner_exports", "rule")
    assert _consent_section(form, fix)["description"] == EMPTY_HTML


def test_the_clause_printed_on_the_paper_is_attached_to_the_consent() -> None:
    form, ws = _run(brief(declarations=_clause("native", 1.0)))
    fix = _fix(ws, "CLAUSE_LINK_MISSING")
    assert (fix["kind"], fix["rule"]) == ("applied", "clause.text_from_paper")
    assert fix["source"]["type"] == "paper" and fix["source"]["page"] == 2 and fix["source"]["box"] == [40.0, 300.0, 550.0, 700.0]
    html = _consent_section(form, fix)["description"]
    assert "<p>Klauzula informacyjna</p>" in html and "Wójt Gminy Wzorcowo &lt;b&gt;." in html        # text of the paper is escaped


def test_a_clause_read_by_ocr_is_a_choice_and_low_confidence_is_not_written() -> None:
    good_form, good = _run(brief(declarations=_clause("ocr", CLAUSE_OCR_ATTACH)))
    fix = _fix(good, "CLAUSE_LINK_MISSING")
    assert fix["kind"] == "choice" and [(o["value"], o["current"]) for o in fix["options"]] == [("text", True), ("none", False)]
    assert "Wzorcowo" in _consent_section(good_form, fix)["description"]
    assert _consent_section(_apply(good_form, fix["options"][1]["set"]), fix)["description"] == EMPTY_HTML

    weak_form, weak = _run(brief(declarations=_clause("ocr", CLAUSE_OCR_ATTACH - 0.01)))
    fix = _fix(weak, "CLAUSE_LINK_MISSING")
    assert [(o["value"], o["current"]) for o in fix["options"]] == [("none", True), ("text", False)]
    assert _consent_section(weak_form, fix)["description"] == EMPTY_HTML
    assert "Wzorcowo" in _consent_section(_apply(weak_form, fix["options"][1]["set"]), fix)["description"]


# -- REQUIRED_INFERRED ---------------------------------------------------------------------------------------------------

def _matter(*fields: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"title": "Dane sprawy", "role": "matter/dane", "fields": list(fields)}]


def _inferred(key: str, label: str, **kw: Any) -> dict[str, Any]:
    return {"key": key, "label": label, "type": "TEXT_FIELD", "required": True, "required_basis": "inferred", **kw}


def test_silent_paper_gives_one_choice_and_each_option_writes_every_field() -> None:
    b = brief(matter=_matter(_inferred("cel", "Cel wniosku"), _inferred("telefon", "Telefon kontaktowy"), _inferred("kwota", "Kwota")))
    form, ws = _run(b, PAPER)
    fix = _fix(ws, "REQUIRED_INFERRED")
    assert fix["kind"] == "choice" and fix["rule"] == "required.paper_is_silent" and "target" not in fix
    assert [(o["value"], o["current"]) for o in fix["options"]] == [
        ("optional", True), ("required_but_usually_optional", False), ("required", False)]
    assert _apply(form, fix["options"][0]["set"]) == form

    def required(f: dict[str, Any]) -> dict[str, bool]:
        return {c["field"]["techName"]: "REQUIRED" in c["field"]["validation"]
                for t in f["tabs"] for q in t["questions"] for c in q["field"]["repeatingSectionGrid"]
                if c["field"]["techName"] in ("cel_wniosku", "telefon_kontaktowy", "kwota")}

    assert required(form) == {"cel_wniosku": False, "telefon_kontaktowy": False, "kwota": False}
    assert required(_apply(form, fix["options"][1]["set"])) == {"cel_wniosku": True, "telefon_kontaktowy": False, "kwota": True}
    assert required(_apply(form, fix["options"][2]["set"])) == {"cel_wniosku": True, "telefon_kontaktowy": True, "kwota": True}


def test_a_paper_that_marks_required_fields_itself_needs_no_question() -> None:
    marked = {"key": "nazwa", "label": "Nazwa (pole obowiązkowe)", "type": "TEXT_FIELD", "required": True, "required_basis": "paper",
              "evidence": [{"page": 1, "quote": "Nazwa (pole obowiązkowe)"}]}
    _form, ws = _run(brief(matter=_matter(marked, _inferred("cel", "Cel wniosku"))), PAPER)
    fix = _fix(ws, "REQUIRED_INFERRED")
    assert (fix["kind"], fix["rule"], fix["source"]["type"]) == ("applied", "required.paper_marks_its_own", "paper")


def test_the_papers_own_optional_word_is_applied_with_its_place() -> None:
    f = _inferred("uwagi", "Uwagi", hint="nieobowiązkowe", evidence=[{"page": 1, "box": [10.0, 20.0, 30.0, 40.0], "quote": "Uwagi (nieobowiązkowe)"}])
    form, ws = _run(brief(matter=_matter(f)))
    fix = _fix(ws, "REQUIRED_INFERRED")
    assert (fix["kind"], fix["rule"], fix["source"]["box"]) == ("applied", "required.paper_optional", [10.0, 20.0, 30.0, 40.0])
    assert _at(form, fix["target"]["pointer"])["title"] == "Uwagi"


def test_per_field_warning_of_the_brief_under_the_inferred_policy() -> None:
    b = brief(matter=_matter(_inferred("cel", "Cel wniosku"), _inferred("e_mail", "Adres e-mail")))
    r = compose(b, ComposeOptions())
    form = json.loads(r.form.to_json_bytes())
    warnings = [{"code": "REQUIRED_INFERRED", "field": "cel"}, {"code": "REQUIRED_INFERRED", "field": "e_mail"},
                {"code": "REQUIRED_INFERRED", "field": "gone"}]
    out = fixes.attach(form, warnings, fixes.brief_hints(warnings, b), r.paths, r.brief_keys)
    assert out[0]["fix"]["kind"] == "applied" and out[0]["fix"]["rule"] == "required.unmarked_blank"
    choice = out[1]["fix"]
    assert choice["kind"] == "choice" and [(o["value"], o["current"]) for o in choice["options"]] == [("required", True), ("optional", False)]
    assert "REQUIRED" in _at(form, choice["target"]["pointer"])["validation"]
    assert "REQUIRED" not in _at(_apply(form, choice["options"][1]["set"]), choice["target"]["pointer"])["validation"]
    assert "fix" not in out[2]                                  # a field that is not in the form: the remark stays as it was


# -- the resolver --------------------------------------------------------------------------------------------------------

def test_a_hint_that_does_not_resolve_leaves_the_remark_untouched() -> None:
    r = compose(brief())
    form = json.loads(r.form.to_json_bytes())
    w = [{"code": "ADDRESSEE_MISSING", "detail": "x"}]
    hint = {"kind": "input", "rule": "addressee.not_on_paper", "text": "t", "target": "dane/nie_ma/takiego",
            "input": {"label": "l", "props": ["defaultValue"]}}
    assert fixes.attach(form, w, {0: hint}, r.paths, r.brief_keys) == w
    assert fixes.attach({"tabs": None}, w, {0: hint}, r.paths, r.brief_keys) == w      # a broken form never costs the report
    assert fixes.seen_by_clerk(w[0]) and fixes.seen_by_clerk({"code": "X", "fix": {"kind": "choice"}})


def test_the_form_bytes_do_not_depend_on_the_fix() -> None:
    """The fix lives in the sidecar only: composing twice gives the same form, with or without reading the hints."""
    b = brief(declarations=_clause("native", 1.0))
    assert compose(b).form.to_json_bytes() == compose(b).form.to_json_bytes()
