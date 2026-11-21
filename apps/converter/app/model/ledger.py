"""Revision 1.1: the meta ledger and the coverage, assembled from what the steps hand over (verification plan 5 #2, #3).

    ledger = assemble_ledger(finder, brief.dispositions, form_ids, decisions={d.id for d in meta_decisions})
    coverage = count_coverage(finder, page_model)

`form_ids` maps a brief key to its form id. The composer returns the other direction
(`ComposeResult.brief_keys`: form id -> key); invert it: `{key: fid for fid, key in result.brief_keys.items()}`.

Both functions refuse (LedgerError, a ValueError) instead of guessing: a candidate of the finder without a
disposition, a disposition of a candidate the finder does not have, a key without a form id, a merge whose target
is not a candidate or that never reaches a fate other than MERGED, a decision that is not listed.
"""
from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping

from .brief import Disposition
from .candidate import FinderOutput
from .common import Span
from .meta import Coverage, Ledger, LedgerRow
from .page import PageModel


class LedgerError(ValueError):
    """The ledger cannot be assembled honestly from these inputs."""


def assemble_ledger(finder: FinderOutput, dispositions: Iterable[Disposition], form_ids: Mapping[str, str],
                    decisions: Collection[str] | None = None) -> Ledger:
    """One ledger row per finder candidate, in the finder's order. STANDARD rows carry the brief's role verbatim
    in `section`. `decisions`, when given, are the ids a row AWAITING_DECISION may name."""
    disp = {d.candidate: d for d in dispositions}
    order = [c.id for c in finder.candidates]
    problems: list[str] = []
    missing = [c for c in order if c not in disp]
    extra = sorted(set(disp) - set(order))
    if missing:
        problems.append(f"finder candidates without a disposition: {missing}")
    if extra:
        problems.append(f"dispositions of candidates the finder does not have: {extra}")
    rows: list[LedgerRow] = []
    for cid in order:
        d = disp.get(cid)
        if d is None:
            continue
        if d.fate == "FIELD":
            fid = form_ids.get(d.key or "")
            if fid is None:
                problems.append(f"{cid}: key {d.key!r} has no form id")
                continue
            rows.append(LedgerRow(candidate=cid, fate="FIELD", field=fid))
        elif d.fate == "MERGED":
            seen = {cid}
            target = d.into
            while target in disp and disp[target].fate == "MERGED" and target not in seen:
                seen.add(target)
                target = disp[target].into
            if target not in disp:
                problems.append(f"{cid}: merged into {d.into}, which is not a finder candidate")
                continue
            if target in seen:
                problems.append(f"{cid}: the merges from it go round in a circle")
                continue
            rows.append(LedgerRow(candidate=cid, fate="MERGED", into=d.into, why=d.why))
        elif d.fate == "STANDARD":
            rows.append(LedgerRow(candidate=cid, fate="STANDARD", section=d.role))
        elif d.fate == "LEFT_OUT":
            rows.append(LedgerRow(candidate=cid, fate="LEFT_OUT", reason=d.reason))
        else:
            if decisions is not None and d.decision not in decisions:
                problems.append(f"{cid}: decision {d.decision} is not listed")
                continue
            rows.append(LedgerRow(candidate=cid, fate="AWAITING_DECISION", decision=d.decision))
    if problems:
        raise LedgerError("the ledger cannot be assembled: " + "; ".join(problems))
    by = {f: sum(r.fate == f for r in rows) for f in ("FIELD", "MERGED", "STANDARD", "LEFT_OUT", "AWAITING_DECISION")}
    return Ledger(blanks_found=len(rows), became_field=by["FIELD"], merged=by["MERGED"], covered_by_standard=by["STANDARD"],
                  left_out=by["LEFT_OUT"], awaiting_decision=by["AWAITING_DECISION"], rows=rows)


def count_coverage(finder: FinderOutput, pages: PageModel, silent_pages: Iterable[int] = ()) -> Coverage:
    """Coverage over runs and spans. A run is assigned when the finder names it whole (candidate, label, option or
    section runs, roles) or when its spans cover every character that is not white space; a partly covered run is
    unassigned and its uncovered stretches are listed in `gaps`. Spans are checked first (FinderOutput.check_spans)."""
    finder.check_spans(pages)
    whole: set[str] = set(finder.roles)
    for c in finder.candidates:
        whole.update(c.runs)
        if c.label is not None:
            whole.update(c.label.runs)
        for o in c.options:
            whole.update(o.runs)
    for s in finder.sections:
        whole.update(s.runs)
    covered: dict[str, set[int]] = {}
    for _, sp in finder.all_spans():
        covered.setdefault(sp.run, set()).update(range(sp.start, sp.end))
    unassigned: list[str] = []
    gaps: list[Span] = []
    runs = [r for p in pages.pages for r in p.runs]
    for r in runs:
        if r.id in whole:
            continue
        need = [i for i, ch in enumerate(r.text) if not ch.isspace()]
        hit = covered.get(r.id, set())
        left = [i for i in need if i not in hit]
        if not left and (need or r.id in covered):
            continue
        unassigned.append(r.id)
        if r.id in covered:
            start = prev = left[0]
            for i in left[1:] + [None]:  # type: ignore[list-item]
                if i is not None and i == prev + 1:
                    prev = i
                    continue
                gaps.append(Span(run=r.id, start=start, end=prev + 1))
                if i is not None:
                    start = prev = i
    return Coverage(runs_total=len(runs), assigned=len(runs) - len(unassigned), unassigned=unassigned,
                    silent_pages=sorted(set(silent_pages)), gaps=gaps)
