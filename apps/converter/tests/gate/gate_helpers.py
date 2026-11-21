"""Helpers of the gate tests: a synthetic form from the composer, and small surgery on a plain form dict."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from app.compose import compose
from app.model.brief import Brief

HERE = Path(__file__).resolve().parent
SNAPSHOTS = HERE / "snapshots"
COMPOSE_FIXTURES = HERE.parent / "compose" / "fixtures"   # read only: the fixture briefs of WP-F5


def brief_dict(**over: Any) -> dict[str, Any]:
    """A synthetic brief: everyone may apply, one section of the matter. Synthetic values only."""
    quote = [{"page": 1, "quote": "tekst z papieru"}]
    base: dict[str, Any] = {
        "input": {"sha256": "b" * 64, "format": "pdf"},
        "title": {"status": "stated", "value": "Wniosek o wydanie zaświadczenia", "evidence": quote},
        "addressee": {"status": "stated", "kind": "office", "name": "Urząd Gminy Przykładowo", "evidence": quote},
        "applicants": {"status": "stated", "self": True, "other_person": True, "entity": True, "evidence": quote},
        "matter": [{"title": "Zakres zaświadczenia", "role": "matter/zakres", "fields": [
            {"key": "cel", "label": "Cel wydania zaświadczenia", "type": "TEXT_FIELD", "required": True, "required_basis": "paper"},
            {"key": "liczba_egzemplarzy", "label": "Liczba egzemplarzy", "type": "NUMBER", "concept": "count"}]}],
        "declarations": {"consents": [], "clause": {"status": "not_found"}},
        "fee": {"status": "not_found"},
        "legal_basis": {"status": "not_found"},
    }
    base.update(over)
    return base


def synthetic_form(**over: Any) -> dict[str, Any]:
    return compose(Brief.model_validate(brief_dict(**over))).form.to_partner()


def reference_form(name: str) -> dict[str, Any]:
    """Our form composed from a fixture brief of a reference set (the brief is in git; the export is not)."""
    brief = Brief.model_validate(json.loads((COMPOSE_FIXTURES / f"{name}.json").read_text(encoding="utf-8")))
    return compose(brief).form.to_partner()


def fields(form: dict[str, Any]) -> list[dict[str, Any]]:
    secs = [q["field"] for t in form["tabs"] for q in t["questions"]]
    return secs + [c["field"] for s in secs for c in s["repeatingSectionGrid"]]


def field(form: dict[str, Any], tech: str) -> dict[str, Any]:
    hits = [f for f in fields(form) if f["techName"] == tech]
    assert len(hits) == 1, f"{tech}: {len(hits)} found"
    return hits[0]


def matter_field(form: dict[str, Any]) -> dict[str, Any]:
    """The first field of the matter: first component of the first section on the second page."""
    return form["tabs"][1]["questions"][0]["field"]["repeatingSectionGrid"][0]["field"]


def mutate(form: dict[str, Any], fn) -> dict[str, Any]:
    out = copy.deepcopy(form)
    fn(out)
    return out
