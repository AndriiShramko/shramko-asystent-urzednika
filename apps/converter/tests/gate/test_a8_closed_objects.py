"""A8 VB-7 (13-F5): an unknown key inside an option item, a state item, consentSectionConfig or one of its consents
must fail G1, as an unknown key on a field already does. form.schema.json left those four objects open, so such a key
passed G1 to G4 although the strict model forbids it.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from app import gate

ROOT = Path(__file__).resolve().parents[4]
RESULTS = sorted((ROOT / "results").glob("judged-*/form.json"))


def _fields(node):
    if isinstance(node, dict):
        if "type" in node and "techName" in node:
            yield node
        for v in node.values():
            yield from _fields(v)
    elif isinstance(node, list):
        for v in node:
            yield from _fields(v)


def _first(form: dict, key: str) -> dict | None:
    return next((f for f in _fields(form) if f.get(key)), None)


def _option(form):
    f = _first(form, "options")
    return f and f["options"][0]


def _state(form):
    f = _first(form, "states")
    return f and f["states"][0]


def _consent_config(form):
    f = _first(form, "consentSectionConfig")
    return f and f["consentSectionConfig"]


def _consent(form):
    c = _consent_config(form)
    return c and c["consents"][0]


PLACES = {"option item": _option, "state item": _state, "consentSectionConfig": _consent_config, "consent": _consent}


@pytest.fixture(scope="module")
def forms() -> list[dict]:
    if not RESULTS:
        pytest.skip("no committed results in this checkout")
    return [json.loads(p.read_text(encoding="utf-8")) for p in RESULTS]


def test_committed_results_still_pass_g1(forms) -> None:
    for form in forms:
        assert "G1" not in [c.id for c in gate.check(form).failed]


@pytest.mark.parametrize("place", sorted(PLACES))
def test_unknown_key_fails_g1(forms, place: str) -> None:
    tried = 0
    for form in forms:
        f = copy.deepcopy(form)
        target = PLACES[place](f)
        if not target:
            continue
        target["zzUnknown"] = 1
        assert "G1" in [c.id for c in gate.check(f).failed], place
        tried += 1
    assert tried, f"no {place} in the committed results"
