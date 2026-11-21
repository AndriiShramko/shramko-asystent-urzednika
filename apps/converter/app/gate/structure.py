"""G1 schema, G2 the partner's rules, G3 grid and names, G4 ids and links, G9 dictionaries and initial data.

G2 runs `tools/coi_lint.py` as a module. Its messages are routed to the check that owns the rule (table ROUTES), so
that one broken rule fails one check: an id used twice is G4, a dictionary rule is G9, a dangling state is G5.
When the checker or the schema files are not in the build, the check FAILS with that finding: the gate never
passes what it could not look at.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

from app.gate.report import CheckResult, Finding
from app.gate.walk import Index, _dict, _list

try:  # lead-owned checker; in the image it must be copied beside the app (request in the status file of WP-F14)
    from tools import coi_lint
except ImportError:  # pragma: no cover - exercised only in a build that lacks the file
    coi_lint = None

TOP_KEYS = ("title", "tabs", "flow")
ALWAYS = ("options", "validation", "readOnly", "repeatingSectionGrid", "states", "tooltipMessage")   # D3
KNOWN_DICTIONARIES = frozenset({"Kraje", "TERYT_DOWODOWY", "TERYT_4G_DOWODOWY"})                        # D9
UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
TECH_MAX = 60                                                                                          # D7

# Message of coi_lint -> the check that owns the rule. First match wins; the rest is G2.
ROUTES: tuple[tuple[str, str], ...] = (
    ("id used twice", "G4"),
    ("flow link points at a page", "G4"),
    ("state refers to", "G5"),
    ("repetingSectionGrid", "G3"),
    ("techName repeats", "G3"),
    ("dictionary on a", "G9"),
    ("options must be empty when a dictionary", "G9"),
    ("unknown initial data", "G9"),
    ("title is longer than", "G10"),
)


@lru_cache(maxsize=2)
def _validator(profile: str):
    import jsonschema
    if coi_lint is None:
        raise FileNotFoundError("tools/coi_lint.py is not in this build")
    path = coi_lint.PROFILES[profile]
    return jsonschema.Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))


def g1_schema(form: Any, profile: str) -> CheckResult:
    r = CheckResult("G1", "schema")
    if not isinstance(form, dict):
        r.findings.append(Finding("", f"the form is a {type(form).__name__}, not an object"))
        return r
    keys = list(form)
    if sorted(keys) != sorted(TOP_KEYS):
        r.findings.append(Finding("", f"top keys must be exactly {', '.join(TOP_KEYS)}; found {', '.join(map(str, keys))} (D1)"))
    try:
        v = _validator(profile)
    except (OSError, KeyError) as e:
        r.findings.append(Finding("", f"the schema of the profile {profile!r} cannot be loaded: {e}"))
        return r
    for e in v.iter_errors(form):
        r.findings.append(Finding("/" + "/".join(map(str, e.absolute_path)), e.message[:200]))
    return r


def _where(message: str, ix: Index) -> str:
    """Best-effort pointer for a coi_lint message: it names "page/section/component: ..." or "techName: ..."."""
    head = message.split(": ", 1)[0]
    return ix.path_of(head.rsplit("/", 1)[-1]) if ": " in message else ""


def lint_routed(form: dict, ix: Index) -> tuple[dict[str, list[Finding]], list[Finding], str]:
    """coi_lint ERROR lines by owning check, its WARN lines, and a crash note ("" when it ran)."""
    by: dict[str, list[Finding]] = {}
    if coi_lint is None:
        return by, [], "tools/coi_lint.py is not in this build"
    try:
        out = coi_lint.lint(form)
    except Exception as e:  # a form too broken for the checker: G1 says why; G2 must not pass it
        return by, [], f"the rules checker cannot read this form ({type(e).__name__}: {e})"
    warns = []
    for kind, msg in out:
        f = Finding(_where(msg, ix), msg)
        if kind != "ERROR":
            warns.append(f)
            continue
        owner = next((c for pat, c in ROUTES if pat in msg), "G2")
        by.setdefault(owner, []).append(f)
    return by, warns, ""


def g2_partner_rules(routed: dict[str, list[Finding]], warns: list[Finding], crash: str) -> CheckResult:
    r = CheckResult("G2", "partner_rules", findings=list(routed.get("G2", [])), warnings=warns)
    if crash:
        r.findings.append(Finding("", crash))
    return r


def g3_grid(ix: Index, profile: str, routed: dict[str, list[Finding]]) -> CheckResult:
    r = CheckResult("G3", "grid", findings=list(routed.get("G3", [])))
    seen: dict[str, str] = {}
    for n in ix.nodes():
        c = n.cell
        if c.get("x") != 0 or c.get("cols") != 3:
            r.findings.append(Finding(n.path, f"x={c.get('x')} cols={c.get('cols')}: one column is x 0, cols 3 (D4)"))
        if n.section is not None and c.get("rows") != 1:
            r.findings.append(Finding(n.path, f"component rows={c.get('rows')}, must be 1 (D4)"))
        t = n.tech
        if t in seen:
            r.findings.append(Finding(n.path, f"techName {t!r} is used twice in the form, first at {seen[t]} (D7)"))
        elif t:
            seen[t] = n.path
        if len(t) > TECH_MAX:
            r.findings.append(Finding(n.path, f"techName has {len(t)} characters, at most {TECH_MAX} (D7)"))
        if profile == "strict":
            missing = [k for k in ALWAYS if k not in n.field]
            if missing:
                r.findings.append(Finding(n.path, f"missing always-present keys {missing} (D3)"))
            if "validation" in n.field and not isinstance(n.field["validation"], list):
                r.findings.append(Finding(n.path + "/validation", "validation must be a list (D3)"))
    return r


def g4_ids(form: dict, ix: Index, profile: str, routed: dict[str, list[Finding]]) -> CheckResult:
    r = CheckResult("G4", "ids_and_links", findings=list(routed.get("G4", [])))
    for p, tab in enumerate(ix.pages):
        if not UUID.match(str(tab.get("id", ""))):
            r.findings.append(Finding(f"/tabs/{p}/id", f"page id {tab.get('id')!r} is not a UUID"))
    for n in ix.nodes():
        if not UUID.match(str(n.field.get("id", ""))):
            r.findings.append(Finding(n.path + "/id", f"id {n.field.get('id')!r} is not a UUID"))
    links = _list(_dict(form.get("flow")).get("links"))
    for i, link in enumerate(links):
        link = _dict(link)
        keys = ("id", "source", "target") if profile == "strict" else ("source", "target")  # export 5: link ids a16ec
        for k in keys:
            if not UUID.match(str(link.get(k, ""))):
                r.findings.append(Finding(f"/flow/links/{i}/{k}", f"{k} {link.get(k)!r} is not a UUID"))
    return r


def g9_dictionaries(ix: Index, routed: dict[str, list[Finding]]) -> CheckResult:
    r = CheckResult("G9", "dictionaries", findings=list(routed.get("G9", [])))
    for n in ix.components:
        name = n.field.get("dictionaryName")
        if name and name not in KNOWN_DICTIONARIES:
            r.findings.append(Finding(n.path + "/dictionaryName",
                                      f"dictionary {name!r} is not a known name ({', '.join(sorted(KNOWN_DICTIONARIES))}); "
                                      "propose it in the sidecar (D9)"))
    return r
