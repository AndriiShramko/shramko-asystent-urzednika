"""The partner's two exports load through Form.from_partner_export and dump back with no component lost.
Local only: the exports are part of the task sets, found through tools/coi_paths.py and never copied."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from app.model import Form


def _exports() -> list[Path]:
    try:
        from tools.coi_paths import sets

        return [f for s in sets("reference") for f in sorted(s.glob("*.json"))]
    except Exception:  # noqa: BLE001 - absent sets: the marker skips the tests
        return []


def _fields(d: dict):
    for t in d["tabs"]:
        for q in t["questions"]:
            yield q, q["field"]
            for c in q["field"]["repeatingSectionGrid"]:
                yield c, c["field"]


def _normalised(d: dict) -> dict:
    """The input as we read it: `validation: {}` is an empty list, a missing `states` is an empty list."""
    for _, f in _fields(d):
        if f.get("validation") == {}:
            f["validation"] = []
        f.setdefault("states", [])
    return d


@pytest.mark.sets
def test_both_exports_are_found() -> None:
    assert len(_exports()) == 2


@pytest.mark.sets
@pytest.mark.parametrize("index", [0, 1])
def test_export_round_trip_loses_no_component(index: int) -> None:
    path = _exports()[index]
    src = json.loads(path.read_text(encoding="utf-8"))
    out = Form.from_partner_export(src).to_partner()

    def by_type(d: dict) -> Counter:
        return Counter(f["type"] for _, f in _fields(d))

    def tech_names(d: dict) -> set:
        return {f["techName"] for _, f in _fields(d)}

    assert by_type(out) == by_type(src) and sum(by_type(out).values()) > 50
    assert tech_names(out) == tech_names(src)
    # stronger: nothing changed but the two documented normalisations, and the key order is theirs
    assert out == _normalised(json.loads(path.read_text(encoding="utf-8")))
    for (q_in, f_in), (q_out, f_out) in zip(_fields(src), _fields(out), strict=True):
        assert list(q_out) == list(q_in)
        if "states" in f_in:
            assert list(f_out) == list(f_in), f_in["techName"]
