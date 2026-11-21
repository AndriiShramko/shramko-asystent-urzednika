"""Helpers of the composer tests: fixture briefs, synthetic briefs, the comparison with an export, journeys."""
from __future__ import annotations

import copy
import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any

import jsonata

from app.model.brief import Brief
from app.model.form import Form

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
SNAPSHOTS = HERE / "snapshots"
REFERENCE = {"reference-01-numer-porzadkowy": "brief_reference_01", "reference-05-nadplata-podatku": "brief_reference_05"}


def load_brief(name: str) -> Brief:
    return Brief.model_validate(json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8")))


def brief_dict(**over: Any) -> dict[str, Any]:
    """A small synthetic brief: one natural person, one section of the matter. Override any top key."""
    quote = [{"page": 1, "quote": "tekst z papieru"}]
    base: dict[str, Any] = {
        "input": {"sha256": "a" * 64, "format": "pdf"},
        "title": {"status": "stated", "value": "Wniosek o wydanie zaświadczenia", "evidence": quote},
        "addressee": {"status": "stated", "kind": "office", "name": "Urząd Gminy Przykładowo", "evidence": quote},
        "applicants": {"status": "stated", "self": True, "evidence": quote},
        "matter": [{"title": "Zakres zaświadczenia", "role": "matter/zakres", "fields": [
            {"key": "cel", "label": "Cel wydania zaświadczenia", "type": "TEXT_FIELD", "required": True, "required_basis": "paper"},
            {"key": "liczba_egzemplarzy", "label": "Liczba egzemplarzy", "type": "NUMBER", "concept": "count"}]}],
        "declarations": {"consents": [], "clause": {"status": "not_found"}},
        "fee": {"status": "not_found"},
        "legal_basis": {"status": "not_found"},
    }
    base.update(over)
    return base


def brief(**over: Any) -> Brief:
    return Brief.model_validate(brief_dict(**over))


def everyone() -> dict[str, Any]:
    return {"status": "stated", "self": True, "other_person": True, "entity": True, "evidence": [{"quote": "imię i nazwisko / nazwa"}]}


# -- reading a form (ours or an export) as plain data ---------------------------------------------------------------

def visible_text(markup: str) -> str:
    """The text a reader sees: block ends are spaces, inline tags vanish, entities are decoded."""
    text = re.sub(r"(?i)</(p|li|ul|ol|pre|div)>|<br\s*/?>", " ", markup)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", "", text))).strip()


def norm_field(field: dict[str, Any]) -> dict[str, Any]:
    """A field without ids and grid; HTML as its visible text; conditions without white space."""
    cfg = field.get("consentSectionConfig") or {}
    return {
        "type": field["type"], "title": field["title"], "description": visible_text(field.get("description", "")),
        "options": [(o.get("name"), o.get("techName")) for o in field.get("options", [])],
        "validation": field.get("validation") or [], "readOnly": field.get("readOnly", False),
        "defaultValue": field.get("defaultValue"), "defaultValueType": field.get("defaultValueType"),
        "dictionaryName": field.get("dictionaryName"), "multiLevelTree": field.get("multiLevelTree"),
        "searchEnabled": field.get("searchEnabled"),
        "states": [(s["type"], re.sub(r"\s+", "", s["query"])) for s in field.get("states", [])],
        "consents": [(visible_text(c["description"]), c.get("required")) for c in cfg.get("consents", [])],
    }


def sections(doc: dict[str, Any], pages: set[str] | None = None) -> dict[str, dict[str, Any]]:
    """techName of a section -> its field, for the named pages (all when None)."""
    return {q["field"]["techName"]: q["field"] for t in doc["tabs"] if pages is None or t["title"] in pages for q in t["questions"]}


def components(sec: dict[str, Any]) -> list[dict[str, Any]]:
    return [c["field"] for c in sorted(sec["repeatingSectionGrid"], key=lambda c: c["y"])]


def section_diff(theirs: dict[str, Any], ours: dict[str, Any]) -> set[tuple[str, str, str]]:
    """Differences of one section as (section, component or "", key). "missing": in the export only; "extra": ours only."""
    name = theirs["techName"]
    out = {(name, "", k) for k, v in norm_field(theirs).items() if norm_field(ours)[k] != v}
    a, b = {c["techName"]: c for c in components(theirs)}, {c["techName"]: c for c in components(ours)}
    out |= {(name, t, "missing") for t in a.keys() - b.keys()} | {(name, t, "extra") for t in b.keys() - a.keys()}
    if list(a) != list(b) and a.keys() == b.keys():
        out.add((name, "", "order"))
    for t in a.keys() & b.keys():
        na, nb = norm_field(a[t]), norm_field(b[t])
        out |= {(name, t, k) for k in na if na[k] != nb[k]}
    return out


def outline(form: Form) -> str:
    """A readable snapshot: one line per page, section and component, then the hash of the exact bytes."""
    lines = [f"TITLE {form.title}"]
    for t in form.tabs:
        lines.append(f"PAGE {t.type} {t.title}")
        for q in t.questions:
            f = q.field
            lines.append(f"  {f.type} {f.techName} | {f.title} | y={q.y} rows={q.rows}{' | cond' if f.states else ''}")
            for c in f.repeatingSectionGrid:
                x = c.field
                flags = [k for k, on in (("cond", x.states), ("ro", x.readOnly), (f"def={x.defaultValue}", x.defaultValue is not None),
                                         (f"dict={x.dictionaryName}", x.dictionaryName), (f"opts={len(x.options)}", x.options),
                                         (f"val={','.join(x.validation)}", x.validation), ("html", x.description)) if on]
                lines.append(f"    {x.type} {x.techName} | {x.title} | {' '.join(flags)}".rstrip(" |"))
    lines.append(f"sha256 {hashlib.sha256(form.to_json_bytes()).hexdigest()}")
    return "\n".join(lines) + "\n"


# -- journeys: the conditions of a form evaluated on answers ------------------------------------------------------------

def visible(form: Form, answers: dict[str, Any] | None = None) -> set[str]:
    """techNames of the sections and components shown for the answers (techName -> answer). Fields with a default
    value answer with it, as a browser would; every other field is unanswered."""
    doc = copy.deepcopy(form.to_partner())
    fields = [q["field"] for t in doc["tabs"] for q in t["questions"]]
    fields += [c["field"] for f in list(fields) for c in f["repeatingSectionGrid"]]
    for f in fields:
        if isinstance(f.get("defaultValue"), list) and f["defaultValue"]:
            f["__userAnswer"] = f["defaultValue"]
        if answers and f["techName"] in answers:
            f["__userAnswer"] = answers[f["techName"]]

    def shown(f: dict[str, Any]) -> bool:
        return all(bool(jsonata.Jsonata(s["query"]).evaluate(doc)) for s in f["states"])

    out: set[str] = set()
    for t in doc["tabs"]:
        for q in t["questions"]:
            if shown(q["field"]):
                out.add(q["field"]["techName"])
                out |= {c["field"]["techName"] for c in q["field"]["repeatingSectionGrid"] if shown(c["field"])}
    return out
