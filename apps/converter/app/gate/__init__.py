"""The pre-import gate (design 7.1, 7.2): checks G1 ... G12 over a PLAIN form dict, so it can judge any JSON.

    from app.gate import check
    report = check(form_dict, profile="strict")          # "tolerant" reads the partner's own exports
    report.passed; report.failed; report.get("G6"); report.journeys
    report.raise_for_failure()                            # GateFailed: the service answers 500 GATE_FAILED, no form

| id  | name                  | what fails it |
| G1  | schema                | the profile's schema (contracts/coi), top keys other than title, tabs, flow (D1) |
| G2  | partner_rules         | tools/coi_lint.py: pages, FINISH last, no input on it, sections not nested, links chain |
| G3  | grid                  | x 0 and cols 3, component rows 1, techName unique in the form and at most 60; strict: D3 keys |
| G4  | ids_and_links         | ids not UUIDs or used twice, a link to a page that does not exist |
| G5  | condition_references  | a condition that does not parse, or names a page, section or field not exactly once |
| G6  | condition_values      | a condition not boolean, constant, naming an option the field lacks, or true for other options |
| G7  | zero_answer           | something conditional is visible before anything is answered |
| G8  | journeys              | a page that can become empty; a journey that shows or hides other than it promises |
| G9  | dictionaries          | a dictionary name outside the known ones; options beside a dictionary; unknown initial data |
| G10 | html                  | HTML outside the allow-list, a script target, a title over 255 |
| G11 | ledger                | (needs the sidecar) the ledger does not close; coverage has an unassigned run or a silent page |
| G12 | no_paper_values       | (needs the fill-area values) a value from the paper's fill areas appears in the form |

A check that raises is failed with the exception as its finding: the gate never crashes and never passes what it
could not look at. `journeys=False` skips the replay of the journeys (G8 keeps its empty-page rule).
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from app.gate.accounts import g11_ledger, g12_paper_values
from app.gate.conditions import Evaluator, g5_references, g6_values, g7_zero_answer, parse_conditions
from app.gate.htmlcheck import g10_html, html_problems
from app.gate.journeys import g8_journeys, load_journeys
from app.gate.report import CheckResult, Finding, GateFailed, GateReport, JourneyResult
from app.gate.structure import (KNOWN_DICTIONARIES, g1_schema, g2_partner_rules, g3_grid, g4_ids, g9_dictionaries,
                                lint_routed)
from app.gate.walk import Index

__all__ = ["check", "GateReport", "CheckResult", "JourneyResult", "Finding", "GateFailed", "NAMES",
           "KNOWN_DICTIONARIES", "html_problems", "load_journeys"]

NAMES = {"G1": "schema", "G2": "partner_rules", "G3": "grid", "G4": "ids_and_links", "G5": "condition_references",
         "G6": "condition_values", "G7": "zero_answer", "G8": "journeys", "G9": "dictionaries", "G10": "html",
         "G11": "ledger", "G12": "no_paper_values"}


def _guard(cid: str, fn: Callable[[], CheckResult]) -> CheckResult:
    try:
        r = fn()
    except Exception as e:
        return CheckResult(cid, NAMES[cid], "failed", [Finding("", f"the check could not run: {type(e).__name__}: {e}"[:300])])
    if r.status == "passed" and r.findings:
        r.status = "failed"
    return r


def check(form: Any, profile: str = "strict", journeys: bool = True, *, sidecar: dict[str, Any] | None = None,
          fill_values: Iterable[str] | None = None) -> GateReport:
    """Judge one form. `sidecar` (meta with `ledger` and `coverage`) enables G11; `fill_values` (texts inside the
    fill areas of the paper) enables G12; without them those two checks are not_applicable."""
    if profile not in ("strict", "tolerant"):
        raise ValueError(f"profile must be strict or tolerant, not {profile!r}")
    g1 = _guard("G1", lambda: g1_schema(form, profile))
    if not isinstance(form, dict):
        rest = [CheckResult(c, n, "failed", [Finding("", "the form is not an object")]) for c, n in NAMES.items() if c != "G1"]
        return GateReport(profile, [g1, *rest])
    ix = Index(form)
    routed, warns, crash = lint_routed(form, ix)
    conds = parse_conditions(ix)
    ev = Evaluator(form)
    journey_results: list[JourneyResult] = []

    def g8() -> CheckResult:
        r, js = g8_journeys(ix, conds, ev, journeys)
        journey_results.extend(js)
        return r

    checks = [
        g1,
        _guard("G2", lambda: g2_partner_rules(routed, warns, crash)),
        _guard("G3", lambda: g3_grid(ix, profile, routed)),
        _guard("G4", lambda: g4_ids(form, ix, profile, routed)),
        _guard("G5", lambda: g5_references(conds, routed)),
        _guard("G6", lambda: g6_values(conds, ev)),
        _guard("G7", lambda: g7_zero_answer(conds, ev)),
        _guard("G8", g8),
        _guard("G9", lambda: g9_dictionaries(ix, routed)),
        _guard("G10", lambda: g10_html(form, profile, routed)),
        _guard("G11", lambda: g11_ledger(sidecar, ix)),
        _guard("G12", lambda: g12_paper_values(form, fill_values)),
    ]
    return GateReport(profile, checks, journey_results)
