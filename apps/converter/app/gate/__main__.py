"""Command line: judge a form JSON with the gate.

    python -m app.gate FILE.json [--profile strict|tolerant] [--no-journeys] [--json]

Exit code 0 when the report passes, 1 when a check fails, 2 when the file cannot be read.
The gate itself never calls out; it only reads the file given.
"""
from __future__ import annotations

import argparse
import json
import sys

from . import check


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m app.gate")
    ap.add_argument("file")
    ap.add_argument("--profile", default="strict", choices=["strict", "tolerant"])
    ap.add_argument("--no-journeys", action="store_true")
    ap.add_argument("--json", action="store_true", help="print the whole report as JSON")
    args = ap.parse_args(argv)
    try:
        with open(args.file, encoding="utf-8") as fh:
            form = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"cannot read {args.file}: {exc}", file=sys.stderr)
        return 2
    report = check(form, profile=args.profile, journeys=not args.no_journeys)
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        for c in report.checks:
            print(f"{c.id:4} {c.status:14} {c.name}")
            for f in c.findings[:5]:
                print(f"       {f.path or '/'}: {f.message}")
        for j in report.journeys:
            print(f"{j.id:4} {j.status:14} {j.name}" + (f" ({j.reason})" if j.reason else ""))
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
