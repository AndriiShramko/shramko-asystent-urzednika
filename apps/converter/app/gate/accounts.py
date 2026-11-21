"""G11 the ledger closes and the coverage has no unassigned run; G12 no value from a fill area is in the form.

Both need more than the form: G11 the sidecar (`ledger`, `coverage` of meta.schema.json, WP-F15), G12 the texts
found inside the fill areas of the paper (WP-F3, WP-F17). Without them the check is not_applicable with the reason,
never passed.
"""
from __future__ import annotations

import html
import re
from typing import Any, Iterable

from pydantic import ValidationError

from app.gate.report import CheckResult, Finding
from app.gate.walk import Index, strings
from app.model.meta import Coverage, Ledger

UNASSIGNED_WORDS = 3      # design 7.4: an unassigned run of more than three words fails
MIN_VALUE = 4             # shorter fill values ("X", "Tak") match labels by chance and are not judged


def _errors(e: ValidationError) -> list[str]:
    return [f"{'.'.join(map(str, x['loc']))}: {x['msg']}"[:200] for x in e.errors()]


def g11_ledger(sidecar: dict[str, Any] | None, ix: Index) -> CheckResult:
    r = CheckResult("G11", "ledger")
    if sidecar is None:
        r.status, r.reason = "not_applicable", "no sidecar was given: the ledger and the coverage come from WP-F15"
        return r
    ids = {n.field.get("id") for n in ix.nodes()}
    raw = sidecar.get("ledger")
    if raw is None:
        r.findings.append(Finding("", "the sidecar has no ledger"))
    else:
        try:
            ledger = Ledger.model_validate(raw)
            for row in ledger.rows:
                if row.fate == "FIELD" and row.field not in ids:
                    r.findings.append(Finding("", f"ledger row {row.candidate}: field {row.field} is not in the form"))
        except ValidationError as e:
            r.findings += [Finding("", "ledger " + m) for m in _errors(e)]
    raw = sidecar.get("coverage")
    if raw is None:
        r.findings.append(Finding("", "the sidecar has no coverage"))
    else:
        try:
            cov = Coverage.model_validate(raw)
            for run in cov.unassigned:
                if len(run.split()) > UNASSIGNED_WORDS:
                    r.findings.append(Finding("", f"coverage: a run of {len(run.split())} words has no role"))
            for page in cov.silent_pages:
                r.findings.append(Finding("", f"coverage: page {page} has ink and no candidate"))
        except ValidationError as e:
            r.findings += [Finding("", "coverage " + m) for m in _errors(e)]
    return r


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", text))).strip().casefold()


def g12_paper_values(form: dict, values: Iterable[str] | None) -> CheckResult:
    """The finding names the place, never the value: a value from a fill area may be personal data."""
    r = CheckResult("G12", "no_paper_values")
    if values is None:
        r.status, r.reason = "not_applicable", "no fill-area values were given: they come from the finder (WP-F3, WP-F17)"
        return r
    wanted = {_norm(v) for v in values if isinstance(v, str)}
    judged = {v for v in wanted if len(v) >= MIN_VALUE}
    r.detail.update(values=len(judged), too_short=len(wanted - judged))
    if judged:
        for path, _key, s in strings(form):
            text = _norm(s)
            hits = sum(v in text for v in judged)
            if hits:
                r.findings.append(Finding(path, f"{hits} value(s) from a fill area of the paper appear here"))
    return r
