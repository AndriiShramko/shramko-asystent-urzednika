#!/usr/bin/env python3
"""Vulnerability gate over a Grype JSON report (WP-F20, decided by the lead; build-time, CI only).

    python tools/ci/vuln_gate.py GRYPE.json [--label core]

Grype (Apache-2.0) scans the CycloneDX SBOM of a target; the full report is an artefact of the run. This script
reads that report, lists every finding in the job summary (severity, id, package, fix), and fails (exit 1)
only for a finding of severity Critical that has a fix. Everything else is listed, never silently dropped.
Exit 2 when the report cannot be read: a scan that did not happen is not a pass.
"""
from __future__ import annotations

import json
import os
import sys

ORDER = ["Critical", "High", "Medium", "Low", "Negligible", "Unknown"]


def findings_of(report: dict) -> list[dict]:
    out = []
    for m in report.get("matches") or []:
        v, a = m.get("vulnerability", {}), m.get("artifact", {})
        fix = v.get("fix") or {}
        out.append({"severity": str(v.get("severity") or "Unknown").capitalize(), "id": v.get("id", "?"),
                    "package": f"{a.get('name', '?')} {a.get('version', '')}".strip(),
                    "fixed": fix.get("state") == "fixed" and bool(fix.get("versions")),
                    "fix": ", ".join(fix.get("versions") or []) or fix.get("state", "unknown")})
    return sorted(out, key=lambda f: (ORDER.index(f["severity"]) if f["severity"] in ORDER else 99, f["id"]))


def blocking(found: list[dict]) -> list[dict]:
    """Critical with a fix: the only blocking class."""
    return [f for f in found if f["severity"] == "Critical" and f["fixed"]]


def markdown(found: list[dict], label: str) -> str:
    counts = {s: sum(1 for f in found if f["severity"] == s) for s in ORDER}
    head = ", ".join(f"{n} {s.lower()}" for s, n in counts.items() if n) or "no findings"
    lines = [f"### Vulnerabilities of `{label}` (Grype on the SBOM): {head}",
             f"Blocking (critical with a fix): {len(blocking(found))}", ""]
    if found:
        lines += ["| Severity | Id | Package | Fix |", "|---|---|---|---|"]
        lines += [f"| {f['severity']} | {f['id']} | {f['package']} | {f['fix']} |" for f in found]
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    label = "image"
    if "--label" in argv:
        i = argv.index("--label")
        label = argv[i + 1]
        del argv[i:i + 2]
    if len(argv) != 1:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    try:
        with open(argv[0], encoding="utf-8") as fh:
            report = json.load(fh)
        if "matches" not in report:
            raise ValueError("no 'matches' key")
    except (OSError, ValueError) as exc:
        print(f"vuln gate: cannot read the report: {type(exc).__name__}", file=sys.stderr)
        return 2
    found = findings_of(report)
    md = markdown(found, label)
    print(md)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(md + "\n")
    bad = blocking(found)
    for f in bad:
        print(f"BLOCKING: {f['id']} in {f['package']}, fixed in {f['fix']}", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
