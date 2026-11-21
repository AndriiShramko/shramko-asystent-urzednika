#!/usr/bin/env python3
"""Wait for the GitHub Actions runs of one commit and print what they did (WP-F20, build-time tool).

    python tools/ci/wait_run.py COMMIT [--workflow image.yml] [--timeout 540] [--log-lines 60]

The token comes from `git credential fill` (protocol https, host github.com), stays in memory and is never
printed, logged or passed on: it is sent only to api.github.com, never to the storage host a log redirects to.
Polls the runs of the commit until every run has ended or the timeout passes (at most 540 s per call, so the
shell tool, which stops at 600 s, always sees the summary). Then prints each run, each job, each step with its
conclusion and, for every failed job, the log lines that end at its last error line.

Exit codes: 0 all runs succeeded; 1 a run failed or was cancelled; 2 still running or no run found (call again);
3 no credential.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

REPO = "AndriiShramko/shramko-asystent-urzednika"
API = "https://api.github.com"
MAX_WAIT = 540


def credential() -> str | None:
    """The password field of `git credential fill`; nothing is echoed."""
    try:
        out = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
                             capture_output=True, text=True, timeout=30,
                             env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    for line in out.splitlines():
        if line.startswith("password="):
            return line[len("password="):] or None
    return None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: ANN002, ANN003 - keep the token off the redirect host
        return None


_api = urllib.request.build_opener(_NoRedirect)


def get(path: str, token: str, raw: bool = False):
    req = urllib.request.Request(API + path, headers={
        "Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "wait-run"})
    try:
        with _api.open(req, timeout=30) as r:
            body = r.read()
    except urllib.error.HTTPError as exc:
        if exc.code in (301, 302, 303, 307, 308) and raw:
            where = exc.headers.get("Location", "")
            plain = urllib.request.Request(where, headers={"User-Agent": "wait-run"})  # no token here
            with urllib.request.urlopen(plain, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        raise RuntimeError(f"GET {path}: HTTP {exc.code}") from None
    return body.decode("utf-8", "replace") if raw else json.loads(body)


def runs_of(commit: str, token: str, workflow: str | None) -> list[dict]:
    data = get(f"/repos/{REPO}/actions/runs?head_sha={commit}&per_page=50", token)
    runs = data.get("workflow_runs", [])
    if workflow:
        runs = [r for r in runs if r.get("path", "").endswith(workflow)]
    return runs


def failed_tail(log: str, n: int) -> list[str]:
    """The n lines ending at the last error line of a job log (the failing step), else the last n lines."""
    lines = log.splitlines()
    end = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        if "##[error]" in lines[i]:
            end = i + 1
            break
    return lines[max(0, end - n):end]


def report(run: dict, token: str, n: int) -> None:
    print(f"RUN {run['name']} #{run['run_number']} event={run['event']} branch={run['head_branch']} "
          f"status={run['status']} conclusion={run['conclusion']} {run['html_url']}")
    jobs = get(f"/repos/{REPO}/actions/runs/{run['id']}/jobs?per_page=100", token).get("jobs", [])
    for job in jobs:
        print(f"  JOB {job['name']}: {job['status']}/{job['conclusion']}")
        for step in job.get("steps", []):
            mark = "" if step.get("conclusion") in ("success", "skipped", None) else "   <=="
            print(f"    {step['number']:>2} {step['name']}: {step.get('conclusion') or step.get('status')}{mark}")
        if job.get("conclusion") == "failure":
            try:
                log = get(f"/repos/{REPO}/actions/jobs/{job['id']}/logs", token, raw=True)
            except Exception as exc:  # noqa: BLE001 - a missing log must not hide the summary
                print(f"    (log not available: {exc})")
                continue
            print(f"    --- last {n} lines up to the last error of job {job['name']} ---")
            for line in failed_tail(log, n):
                print("    | " + line[29:] if len(line) > 29 and line[4] == "-" else "    | " + line)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("commit")
    ap.add_argument("--workflow", default=None, help="only runs of this workflow file, e.g. image.yml")
    ap.add_argument("--timeout", type=int, default=MAX_WAIT)
    ap.add_argument("--log-lines", type=int, default=60)
    ap.add_argument("--interval", type=int, default=20)
    args = ap.parse_args()
    token = credential()
    if not token:
        print("no credential for github.com from `git credential fill`", file=sys.stderr)
        return 3
    commit = subprocess.run(["git", "rev-parse", args.commit], capture_output=True, text=True).stdout.strip() \
        or args.commit
    deadline = time.monotonic() + min(args.timeout, MAX_WAIT)
    runs: list[dict] = []
    while True:
        runs = runs_of(commit, token, args.workflow)
        if runs and all(r["status"] == "completed" for r in runs):
            break
        if time.monotonic() > deadline:
            break
        time.sleep(args.interval)
    if not runs:
        print(f"no run for {commit[:10]} yet")
        return 2
    for run in runs:
        report(run, token, args.log_lines)
    if any(r["status"] != "completed" for r in runs):
        print("still running: call again")
        return 2
    return 0 if all(r["conclusion"] == "success" for r in runs) else 1


if __name__ == "__main__":
    sys.exit(main())
