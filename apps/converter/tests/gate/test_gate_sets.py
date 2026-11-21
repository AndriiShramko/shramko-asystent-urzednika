"""The gate on the partner's own two exports (local only): if the gate disagrees with their forms, the gate is wrong.

Snapshots of the journeys live in snapshots/<set>.json: which techNames each journey shows. The expectations inside
journeys/standard.json were predicted by hand before the first run; the snapshot pins the full visible set.
Rewrite the snapshots after a deliberate change:  GATE_UPDATE_SNAPSHOTS=1 bash tools/gate.sh py -m pytest tests/gate
"""
from __future__ import annotations

import json
import os

import pytest
from gate_helpers import SNAPSHOTS

from app.gate import check

pytestmark = pytest.mark.sets
SETS = ["reference-01-numer-porzadkowy", "reference-05-nadplata-podatku"]


def export(set_id: str) -> dict:
    from eval.golden import expected_forms
    return json.loads(expected_forms()[set_id].read_text(encoding="utf-8"))


@pytest.fixture(scope="module", params=SETS)
def judged(request):
    return request.param, export(request.param), check(export(request.param), profile="tolerant")


def test_exports_pass_g1_to_g10_tolerant(judged):
    _, _, r = judged
    assert {c.id: c.status for c in r.checks if c.id not in ("G11", "G12")} == {f"G{i}": "passed" for i in range(1, 11)}, \
        [(c.id, c.findings[:2]) for c in r.failed]


def test_zero_answer_hides_every_conditional_component(judged):
    """Every component or section with a SHOW state is judged hidden, except those decided by a default value."""
    _, form, r = judged
    nodes = [q["field"] for t in form["tabs"] for q in t["questions"]]
    nodes += [c["field"] for f in list(nodes) for c in f["repeatingSectionGrid"]]
    conditional = sum(1 for f in nodes if any(s.get("type") == "SHOW" for s in f.get("states") or []))
    d = r.get("G7").detail
    assert r.get("G7").status == "passed" and d["judged"] + d["decided_by_default"] == conditional


def test_journeys_as_predicted_by_hand(judged):
    _, _, r = judged
    status = {j.id: j.status for j in r.journeys}
    assert [s for k, s in status.items() if k != "J7_statutory_representative"] == ["passed"] * 6
    assert status["J7_statutory_representative"] == "not_applicable"   # the exports have no statutory path (D16 is ours)


def test_journey_snapshots(judged):
    set_id, _, r = judged
    got = {j.id: {"status": j.status, "visible": j.visible} for j in r.journeys}
    path = SNAPSHOTS / f"{set_id}.json"
    if os.environ.get("GATE_UPDATE_SNAPSHOTS") == "1" or not path.exists():
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(got, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        pytest.skip(f"snapshot written: {path.name}")
    assert got == json.loads(path.read_text(encoding="utf-8"))


def test_country_poland_then_abroad_on_export_1():
    """The cheapest test that would prove us wrong (WP-F14): Polska, then Niemcy, in the country of the address."""
    r = check(export(SETS[0]), profile="tolerant")
    j5, j6 = (next(j for j in r.journeys if j.id.startswith(k)) for k in ("J5", "J6"))
    assert {"ulica", "kod_pocztowy", "wojewodztwo"} <= set(j5.visible) and not {"ulica_zagranica"} & set(j5.visible)
    assert {"ulica_zagranica", "kod_pocztowy_zagranica", "miejscowosc_zagranica"} <= set(j6.visible)
    assert not {"ulica", "kod_pocztowy", "wojewodztwo"} & set(j6.visible)


def test_strict_profile_refuses_the_exports(judged):
    """Strict is what we write; the exports depart from it (export 5 link ids, export 1 validation {}, their HTML)."""
    _, form, _ = judged
    assert not check(form, profile="strict", journeys=False).passed
