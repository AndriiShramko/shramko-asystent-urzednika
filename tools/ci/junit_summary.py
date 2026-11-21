#!/usr/bin/env python3
"""Count a pytest JUnit report: passed, failed, skipped, and WHY tests were skipped (WP-F20).

    python tools/ci/junit_summary.py REPORT.xml [REPORT2.xml ...]

Skipped is never passed (track rule 3): the run page shows how many were skipped and the reason of each group,
for example the tests marked `sets`, which need the partner's task sets that are never in git. Writes the same
table to $GITHUB_STEP_SUMMARY when set. Exit 1 when a report has a failure or an error, or cannot be read.
"""
from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET  # our own pytest output, not untrusted input
from collections import Counter


def summarise(paths: list[str]) -> tuple[dict, Counter]:
    totals = {"tests": 0, "failed": 0, "errors": 0, "skipped": 0}
    reasons: Counter = Counter()
    for path in paths:
        root = ET.parse(path).getroot()
        for case in root.iter("testcase"):
            totals["tests"] += 1
            for child in case:
                if child.tag == "failure":
                    totals["failed"] += 1
                elif child.tag == "error":
                    totals["errors"] += 1
                elif child.tag == "skipped":
                    totals["skipped"] += 1
                    msg = (child.get("message") or "").strip()
                    reasons[msg[:160] or "(no reason given)"] += 1
    totals["passed"] = totals["tests"] - totals["failed"] - totals["errors"] - totals["skipped"]
    return totals, reasons


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    try:
        totals, reasons = summarise(argv)
    except (OSError, ET.ParseError) as exc:
        print(f"cannot read the report: {exc}", file=sys.stderr)
        return 1
    head = (f"{totals['passed']} passed, {totals['failed']} failed, {totals['errors']} errors, "
            f"{totals['skipped']} skipped (of {totals['tests']})")
    lines = [head] + [f"  skipped {n}: {why}" for why, n in reasons.most_common()]
    print("\n".join(lines))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        md = ["### Native test suite", "", head, "", "| Skipped | Reason |", "|---|---|"]
        md += [f"| {n} | {why.replace('|', '/')} |" for why, n in reasons.most_common()]
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("\n".join(md) + "\n\n")
    return 1 if totals["failed"] or totals["errors"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
