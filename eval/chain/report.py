"""Summary, baseline and the compare step. Files keep keys (hashes) and numbers only: never a name, never content."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUMMARY = HERE / "summary.json"
BASELINE = HERE / "baseline.json"
LAST_RUN = HERE / "last-run.jsonl"
FALL = 0.20


def _totals(rows: list[dict]) -> dict:
    t = {"files": len(rows), "converted": 0, "refused": 0, "failed": 0, "gate_failed": 0, "lint_errors": 0,
         "fields": 0, "fields_matter": 0, "no_label": 0, "seconds": 0.0, "warnings": {}}
    for r in rows:
        t[r["outcome"]] += 1
        t["gate_failed"] += r["gate"] == "failed"
        for k in ("lint_errors", "fields", "fields_matter", "no_label"):
            t[k] += r.get(k, 0)
        t["seconds"] = round(t["seconds"] + r.get("seconds", 0), 2)
        for c, n in r.get("warnings", {}).items():
            t["warnings"][c] = t["warnings"].get(c, 0) + n
    t["warnings"] = dict(sorted(t["warnings"].items()))
    return t


def summarize(rows: list[dict]) -> dict:
    out: dict = {"total": _totals(rows), "corpora": {}}
    for corpus in sorted({r["corpus"] for r in rows}):
        mine = [r for r in rows if r["corpus"] == corpus]
        out["corpora"][corpus] = {
            **_totals(mine),
            "formats": {f: _totals([r for r in mine if r["format"] == f]) for f in sorted({r["format"] for r in mine})},
        }
    return out


def to_baseline(rows: list[dict]) -> dict:
    return {"files": {f"{r['corpus']}:{r['key']}": {k: r.get(k, 0) for k in ("outcome", "gate", "lint_errors", "fields")}
                      for r in sorted(rows, key=lambda r: (r["corpus"], r["key"]))}}


def write_run(rows: list[dict], last_run: Path | None = None, summary: Path | None = None) -> dict:
    last_run, summary = last_run or LAST_RUN, summary or SUMMARY
    last_run.write_text("".join(json.dumps(r, ensure_ascii=True) + "\n" for r in rows), encoding="utf-8")
    s = summarize(rows)
    summary.write_text(json.dumps(s, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return s


def compare(rows: list[dict], baseline: dict) -> tuple[list[str], list[str], list[str]]:
    """(regressions, improvements, notes). Regressions decide the exit code."""
    base = baseline["files"]
    bad: list[str] = []
    good: list[str] = []
    notes: list[str] = []
    for r in rows:
        k = f"{r['corpus']}:{r['key']}"
        b = base.get(k)
        if b is None:
            notes.append(f"{k}: not in the baseline ({r['outcome']})")
            if r["outcome"] == "failed":
                bad.append(f"{k}: new file failed ({r['error']})")
            if r["gate"] == "failed":
                bad.append(f"{k}: new file fails the gate")
            continue
        if r["outcome"] == "failed" and b["outcome"] != "failed":
            bad.append(f"{k}: was {b['outcome']}, now failed ({r['error']})")
        elif b["outcome"] == "failed" and r["outcome"] != "failed":
            good.append(f"{k}: was failed, now {r['outcome']}")
        if r["gate"] == "failed" and b["gate"] != "failed":
            bad.append(f"{k}: the gate now fails")
        elif b["gate"] == "failed" and r["gate"] != "failed":
            good.append(f"{k}: the gate no longer fails")
        if r["lint_errors"] > b["lint_errors"]:
            notes.append(f"{k}: strict-linter errors {b['lint_errors']} -> {r['lint_errors']}")
        elif r["lint_errors"] < b["lint_errors"]:
            good.append(f"{k}: strict-linter errors {b['lint_errors']} -> {r['lint_errors']}")
        bf, nf = b["fields"], r["fields"]
        if nf > bf:
            good.append(f"{k}: fields {bf} -> {nf}")
        elif nf < bf:
            fell = bf > 0 and nf < bf * (1 - FALL)
            (bad if fell and r["corpus"] == "sets" else notes).append(f"{k}: fields {bf} -> {nf}" + (" (fall over 20 %)" if fell else ""))
    for k in sorted(set(base) - {f"{r['corpus']}:{r['key']}" for r in rows}):
        notes.append(f"{k}: in the baseline, not in this run")
    return bad, good, notes


def print_compare(bad: list[str], good: list[str], notes: list[str]) -> None:
    print(f"compare: {len(bad)} worse (decide the exit code), {len(good)} better, {len(notes)} notes")
    for title, lines in (("WORSE", bad), ("BETTER", good), ("NOTE", notes)):
        for ln in lines:
            print(f"  {title}: {ln}")
