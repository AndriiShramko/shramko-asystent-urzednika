#!/usr/bin/env python3
"""Print the lines of the job logs of one commit's runs that match a pattern (WP-F20i, build-time tool).

    python tools/ci/job_log.py COMMIT [--job "image (core)"] [--grep "^(PASS|FAIL)  "] [--workflow image.yml]

The rows of tools/ci/container_check.py ("PASS  check  (detail)") live only in the job log and in the step
summary; this prints them, so a status file can quote a number of a run. The token is handled by wait_run.py
(from `git credential fill`, in memory, sent only to api.github.com, never printed). Exit 1 when no line matched.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wait_run  # noqa: E402

STAMP = re.compile(r"^\d{4}-\d\d-\d\dT[\d:.]+Z ")   # the time stamp GitHub puts before every log line


def matching(log: str, pattern: str) -> list[str]:
    rx = re.compile(pattern)
    lines = (STAMP.sub("", line) for line in log.splitlines())
    return [line for line in lines if rx.search(line)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("commit")
    ap.add_argument("--job", help="only jobs whose name contains this text")
    ap.add_argument("--grep", default=r"^(PASS|FAIL)  |^\d+ passed, \d+ failed")
    ap.add_argument("--workflow", default="image.yml")
    args = ap.parse_args()
    token = wait_run.credential()
    if not token:
        print("no credential for github.com", file=sys.stderr)
        return 3
    found = 0
    for run in wait_run.runs_of(args.commit, token, args.workflow):
        jobs = wait_run.get(f"/repos/{wait_run.REPO}/actions/runs/{run['id']}/jobs?per_page=100", token).get("jobs", [])
        for job in jobs:
            if args.job and args.job not in job["name"]:
                continue
            try:
                log = wait_run.get(f"/repos/{wait_run.REPO}/actions/jobs/{job['id']}/logs", token, raw=True)
            except RuntimeError as exc:
                print(f"JOB {job['name']} of actions/runs/{run['id']}: {exc}")
                continue
            lines = matching(log, args.grep)
            print(f"JOB {job['name']} of actions/runs/{run['id']} ({job['conclusion']}): {len(lines)} lines")
            for line in lines:
                print("  " + line)
            found += len(lines)
    return 0 if found else 1


if __name__ == "__main__":
    sys.exit(main())
