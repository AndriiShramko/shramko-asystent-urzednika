"""G8: no page can become empty, and the journeys of journeys/*.json show what they promise (design 7.2, D16).

"Can become empty" is decided by a rule, not by searching the answers: every page must hold at least one section
without a condition that holds at least one component without a condition (the rule the composer keeps with
`pages_without_fixed_content`). It is sufficient, so no answer can empty such a page; it is stricter than needed
for two complementary conditional sections, and then the finding names the page.

A journey that the form cannot take (a required field or option is missing) is not_applicable, never passed.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.gate.conditions import Condition, Evaluator, by_node
from app.gate.report import CheckResult, Finding, JourneyResult
from app.gate.walk import Index, Node

JOURNEYS = Path(__file__).resolve().parent / "journeys"


@lru_cache(maxsize=1)
def load_journeys() -> tuple[dict[str, Any], ...]:
    out: list[dict[str, Any]] = []
    for path in sorted(JOURNEYS.glob("*.json")):
        out += json.loads(path.read_text(encoding="utf-8"))["journeys"]
    return tuple(out)


def pages_without_fixed_content(ix: Index) -> list[int]:
    fixed = {s.page for s in ix.sections if not s.states and any(not c.states for c in ix.components if c.section is s)}
    return [p for p in range(len(ix.pages)) if p not in fixed]


def visible(ix: Index, conds: dict[str, list[Condition]], ev: Evaluator) -> set[str]:
    """techNames shown for the answers now set on the evaluator. A state that is not SHOW does not hide; a SHOW
    state that G5 rejected hides (fail-closed)."""
    def shown(n: Node) -> bool:
        cs = [c for c in conds.get(n.path, []) if str(n.states[c.index].get("type", "")) == "SHOW"]
        return all(c.ok for c in cs) and ev.shown(cs)
    out: set[str] = set()
    for s in ix.sections:
        if shown(s):
            out.add(s.tech)
            out |= {c.tech for c in ix.components if c.section is s and shown(c)}
    return out


def _option_names(n: Node) -> list[str]:
    return [o.get("name") for o in n.field.get("options") or [] if isinstance(o, dict)]


def run_journey(j: dict[str, Any], ix: Index, conds: dict[str, list[Condition]], ev: Evaluator) -> JourneyResult:
    answers: dict[str, list] = {}
    for a in j["answers"]:
        hits = [n for n in ix.components if n.tech == a["field"]]
        why = ""
        if len(hits) != 1:
            why = f"the form has {len(hits)} fields {a['field']!r}"
        elif not hits[0].field.get("dictionaryName") and a["value"] not in _option_names(hits[0]):
            why = f"{a['field']!r} does not offer {a['value']!r}"
        if why:
            if a.get("required", True):
                return JourneyResult(j["id"], j["name"], "not_applicable", reason=why)
            continue
        answers[hits[0].path] = [a["value"]]
    ev.answer(answers)
    seen = visible(ix, conds, ev)
    r = JourneyResult(j["id"], j["name"], "passed", visible=sorted(seen))
    for t in j.get("expect_visible", []):
        if t not in seen:
            exists = ix.path_of(t)
            r.findings.append(Finding(exists, f"{t!r} should be visible on this journey" if exists else f"{t!r} does not exist"))
    for t in j.get("expect_hidden", []):
        if t in seen:
            r.findings.append(Finding(ix.path_of(t), f"{t!r} should be hidden on this journey"))
    if r.findings:
        r.status = "failed"
    return r


def g8_journeys(ix: Index, conds: list[Condition], ev: Evaluator, journeys: bool) -> tuple[CheckResult, list[JourneyResult]]:
    r = CheckResult("G8", "journeys")
    for p in pages_without_fixed_content(ix):
        r.findings.append(Finding(f"/tabs/{p}", f"page {ix.pages[p].get('title')!r} can become empty: no section without "
                                                "a condition holds a component without a condition"))
    results: list[JourneyResult] = []
    if journeys:
        grouped = by_node(conds)
        results = [run_journey(j, ix, grouped, ev) for j in load_journeys()]
        for j in results:
            r.findings += [Finding(f.path, f"{j.id}: {f.message}") for f in j.findings]
    r.detail.update({s: sum(j.status == s for j in results) for s in ("passed", "failed", "not_applicable")})
    return r, results
