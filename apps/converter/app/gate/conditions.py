"""G5 references, G6 values, G7 the zero-answer canary: every JSONata condition parsed and evaluated.

The evaluator is jsonata-python, inside the process (nothing calls out). Answers are written where the partner's
conditions read them, `field.__userAnswer`, always as a list of visible option names (the shape of the exports'
`defaultValue: ["Polska"]`; `"O" in [...]` and `"O" in "O"` agree). A field with a list default answers with it,
as a browser would; every other field is unanswered (no `__userAnswer` key).

In JSONata `'x' in y` with one string is equality, so a reference resolves only to the page whose title equals the
string, the section and the field whose techName equals it (coi-json-format 11.5). G6 and G7 judge only conditions
that G5 passed: an unresolved condition is G5's finding, never counted twice.
"""
from __future__ import annotations

import copy
import itertools
import json
import re
from dataclasses import dataclass, field
from typing import Any

import jsonata

from app.gate.report import CheckResult, Finding
from app.gate.walk import Index, Node

_Q = r"\s*'([^']*)'\s+in\s+"
REF = re.compile(r"tabs\[" + _Q + r"title\s*\]\s*\.\s*questions\[" + _Q + r"field\s*\.\s*techName\s*\]\s*\.\s*field\s*\.\s*"
                 r"repeatingSectionGrid\[" + _Q + r"field\s*\.\s*techName\s*\]\s*\.\s*field\s*\.\s*__userAnswer"
                 r"(?:\s*\[\s*\$repeatingSectionIndex\s*\])?")
LITERAL = re.compile(r'"((?:[^"\\]|\\.)*)"\s+in\s+(?=tabs\[)')
OTHER_VALUE = "__inna_wartosc__"     # a dictionary answer that no condition names
MAX_COMBINATIONS = 256


@dataclass
class Condition:
    node: Node
    index: int                        # position in states
    query: str
    compiled: Any = None
    reads: list[Node] = field(default_factory=list)   # the fields it reads, in order of first mention
    literals: list[tuple[str, Node]] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)

    @property
    def path(self) -> str:
        return f"{self.node.path}/states/{self.index}/query"

    @property
    def ok(self) -> bool:
        return not self.problems


def parse_conditions(ix: Index) -> list[Condition]:
    out = []
    titles = [p.get("title") for p in ix.pages]
    for n in ix.nodes():
        for i, s in enumerate(n.states):
            q = s.get("query")
            c = Condition(n, i, q if isinstance(q, str) else "")
            out.append(c)
            if not c.query.strip():
                c.problems.append("empty query")
                continue
            try:
                c.compiled = jsonata.Jsonata(c.query)
            except Exception as e:
                c.problems.append(f"does not parse: {str(e)[:120]}")
                continue
            if c.query.count("tabs[") != len(REF.findall(c.query)):
                c.problems.append("a reference is not of the form tabs['P' in title].questions['S' in field.techName]"
                                  ".field.repeatingSectionGrid['F' in field.techName].field.__userAnswer")
            at: dict[int, Node] = {}
            for m in REF.finditer(c.query):
                hit = _resolve(ix, titles, *m.groups())
                if isinstance(hit, str):
                    c.problems.append(hit)
                    continue
                at[m.start()] = hit
                if hit not in c.reads:
                    c.reads.append(hit)
            for m in LITERAL.finditer(c.query):
                if m.end() in at:
                    c.literals.append((json.loads(f'"{m.group(1)}"'), at[m.end()]))
            if not REF.search(c.query):
                c.problems.append("the condition reads no field")
    return out


def _resolve(ix: Index, titles: list, page: str, sec: str, comp: str) -> Node | str:
    pages = [i for i, t in enumerate(titles) if t == page]
    if len(pages) != 1:
        return f"page {page!r}: {len(pages)} pages have exactly this title, need one"
    secs = [s for s in ix.sections if s.page == pages[0] and s.tech == sec]
    if len(secs) != 1:
        return f"section {sec!r} on page {page!r}: {len(secs)} found, need one"
    comps = [c for c in ix.components if c.section is secs[0] and c.tech == comp]
    if len(comps) != 1:
        return f"field {comp!r} in section {sec!r}: {len(comps)} found, need one"
    return comps[0]


class Evaluator:
    """Answers set on a private copy of the form; one result per (condition, answers of the fields it reads)."""

    def __init__(self, form: dict) -> None:
        self.doc = copy.deepcopy(form)
        self.ix = Index(self.doc)
        self._by_path = {n.path: n.field for n in self.ix.nodes()}
        self._defaults = {n.path: n.field["defaultValue"] for n in self.ix.components
                          if isinstance(n.field.get("defaultValue"), list) and n.field["defaultValue"]}
        self._now: dict[str, Any] = {}
        self._cache: dict[tuple, Any] = {}

    def default(self, n: Node) -> list | None:
        return self._defaults.get(n.path)

    def answer(self, answers: dict[str, list | None]) -> None:
        """answers: pointer of a field -> list of names, or None for "unanswered". Others take their default."""
        now = dict(self._defaults)
        now.update(answers)
        for path, f in self._by_path.items():
            f.pop("__userAnswer", None)
            if now.get(path) is not None:
                f["__userAnswer"] = now[path]
        self._now = now

    def evaluate(self, c: Condition) -> Any:
        key = (c.query, tuple(json.dumps(self._now.get(r.path), ensure_ascii=False) for r in c.reads))
        if key not in self._cache:
            try:
                self._cache[key] = c.compiled.evaluate(self.doc)
            except Exception as e:
                self._cache[key] = e
        return self._cache[key]

    def shown(self, conds: list[Condition]) -> bool:
        return all(_truthy(self.evaluate(c)) for c in conds)


def _truthy(v: Any) -> bool:
    return bool(v) and not isinstance(v, Exception)


def g5_references(conds: list[Condition], routed: dict[str, list[Finding]]) -> CheckResult:
    r = CheckResult("G5", "condition_references", findings=list(routed.get("G5", [])))
    for c in conds:
        r.findings += [Finding(c.path, p) for p in c.problems]
    r.detail["conditions"] = len(conds)
    return r


def _domain(c: Condition, field_node: Node, ev: Evaluator, all_conds: list[Condition]) -> list[list | None]:
    f = field_node.field
    names = [o.get("name") for o in f.get("options") or [] if isinstance(o, dict)]
    if names and not f.get("dictionaryName"):
        return [None] + [[n] for n in names]
    seen = [lit for k in all_conds for lit, node in k.literals if node is field_node]
    values = ([ev.default(field_node)] if ev.default(field_node) else []) + [[v] for v in dict.fromkeys(seen)] + [[OTHER_VALUE]]
    return [None] + list({json.dumps(v): v for v in values}.values())


def g6_values(conds: list[Condition], ev: Evaluator) -> CheckResult:
    r = CheckResult("G6", "condition_values")
    judged = combos_total = 0
    for c in conds:
        if not c.ok:
            continue
        judged += 1
        for lit, node in c.literals:
            f = node.field
            names = [o.get("name") for o in f.get("options") or [] if isinstance(o, dict)]
            if not f.get("dictionaryName") and lit not in names:
                r.findings.append(Finding(c.path, f"{lit!r} is not an option of {node.tech!r} (options: {names})"))
        domains = [_domain(c, n, ev, conds) for n in c.reads]
        combos = list(itertools.islice(itertools.product(*domains), MAX_COMBINATIONS))
        if len(combos) == MAX_COMBINATIONS:
            r.warnings.append(Finding(c.path, f"more than {MAX_COMBINATIONS} combinations of answers; the first ones were judged"))
        results = []
        for combo in combos:
            ev.answer({n.path: v for n, v in zip(c.reads, combo)})
            results.append(ev.evaluate(c))
        combos_total += len(combos)
        bad = [v for v in results if not isinstance(v, bool)]
        if bad:
            r.findings.append(Finding(c.path, f"the result is not a boolean for some answers: {bad[0]!r}"[:200]))
            continue
        if all(results) or not any(results):
            r.findings.append(Finding(c.path, f"the condition is {'always' if all(results) else 'never'} true, whatever is answered"))
            continue
        if len(c.reads) == 1 and "$not" not in c.query and "$" not in c.query.replace("$repeatingSectionIndex", ""):
            true_for = {combo[0][0] for combo, v in zip(combos, results) if v and combo[0] is not None}
            named = {lit for lit, _ in c.literals}
            if true_for != named:
                r.findings.append(Finding(c.path, f"true for {sorted(true_for)}, but it names {sorted(named)}"))
    r.detail.update(evaluated=judged, combinations=combos_total)
    return r


def by_node(conds: list[Condition]) -> dict[str, list[Condition]]:
    out: dict[str, list[Condition]] = {}
    for c in conds:
        out.setdefault(c.node.path, []).append(c)
    return out


def g7_zero_answer(conds: list[Condition], ev: Evaluator) -> CheckResult:
    """With nothing answered, every component or section with a SHOW state is hidden. A condition that reads a field
    with a default value (the country preset to Polska) is decided by that default, not by the citizen: it is
    counted in detail["decided_by_default"] and not judged."""
    r = CheckResult("G7", "zero_answer")
    ev.answer({})
    judged = by_default = 0
    for path, cs in by_node(conds).items():
        shows = [c for c in cs if c.node.field.get("states") and _state_type(c) == "SHOW"]
        if not shows or not all(c.ok for c in shows):
            continue
        if any(ev.default(n) for c in shows for n in c.reads):
            by_default += 1
            continue
        judged += 1
        if ev.shown(shows):
            r.findings.append(Finding(path, f"{shows[0].node.tech!r} is visible before anything is answered"))
    r.detail.update(judged=judged, decided_by_default=by_default)
    return r


def _state_type(c: Condition) -> str:
    return str(c.node.states[c.index].get("type", ""))
