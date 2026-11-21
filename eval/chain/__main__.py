"""`bash tools/gate.sh py -m eval.chain` : see eval/chain/__init__.py. Exit 1 on any `failed`, or on a regression with
--compare. Logs only counts and hashes."""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from eval.chain import corpora, report, runner


def collect(names: list[str], archive: Path) -> list[corpora.Item]:
    items: list[corpora.Item] = []
    if "sets" in names:
        items += corpora.sets_items()
    if "unseen" in names:
        items += corpora.unseen_items(archive)
    if "hostile" in names:
        items += corpora.hostile_items()
    return items


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="eval.chain", description="Run the check chain.")
    ap.add_argument("--corpus", default="sets,unseen,hostile", help="comma list of: sets, unseen, hostile")
    ap.add_argument("--image", metavar="REF", help="run through docker run --network none --read-only instead of natively")
    ap.add_argument("--archive", default=str(corpora.ARCHIVE_DIR), help="folder of the downloaded city archive")
    ap.add_argument("--timeout", type=int, default=runner.TIMEOUT_S)
    ap.add_argument("--jobs", type=int, default=2, help="files in parallel")
    ap.add_argument("--compare", action="store_true", help="compare with baseline.json; exit 1 on a regression")
    ap.add_argument("--update-baseline", action="store_true", help="rewrite baseline.json from this run")
    ap.add_argument("--build-sample", action="store_true", help="choose the seeded sample from the archive and write sample.json")
    a = ap.parse_args(argv)

    if a.build_sample:
        spec = corpora.build_sample(Path(a.archive))
        corpora.SAMPLE.write_text(json.dumps(spec, indent=1) + "\n", encoding="utf-8")
        print(f"sample: {spec['total']} files of {spec['archive_files']} (seed {spec['seed']})")
        return 0 if spec["total"] >= corpora.MIN_TOTAL else 1

    names = [n for n in a.corpus.split(",") if n]
    items = collect(names, Path(a.archive))
    with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as pool:
        rows = list(pool.map(lambda it: runner.run_item(it, a.image, a.timeout), items))
    summary = report.write_run(rows)
    t = summary["total"]
    print(f"chain: {t['files']} files: {t['converted']} converted, {t['refused']} refused, {t['failed']} failed; "
          f"gate failures {t['gate_failed']}; strict-lint errors {t['lint_errors']}; {t['seconds']} s")
    for c, s in summary["corpora"].items():
        print(f"  {c}: {s['files']} files, {s['converted']} converted, {s['refused']} refused, {s['failed']} failed")
    for r in rows:
        if r["outcome"] == "failed":
            print(f"  FAILED {r['corpus']}:{r['key']} ({r['format']}) {r['error']}")
    code = 1 if t["failed"] else 0
    if a.update_baseline:
        report.BASELINE.write_text(json.dumps(report.to_baseline(rows), indent=1) + "\n", encoding="utf-8")
        print("baseline rewritten")
    if a.compare:
        if not report.BASELINE.exists():
            print("compare: no baseline.json yet (run with --update-baseline)")
            return 1
        bad, good, notes = report.compare(rows, json.loads(report.BASELINE.read_text(encoding="utf-8")))
        report.print_compare(bad, good, notes)
        code = code or (1 if bad else 0)
    return code


if __name__ == "__main__":
    sys.exit(main())
