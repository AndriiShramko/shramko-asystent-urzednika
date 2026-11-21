"""Run one corpus item: natively in a subprocess (timeout 120 s) or through `docker run --network none --read-only`."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from eval.chain.corpora import ROOT, Item
from eval.chain.worker import is_polish

TIMEOUT_S = 120


def _failed(item: Item, error: str, seconds: float) -> dict:
    return {"outcome": "failed", "gate": "n/a", "lint_errors": 0, "fields": 0, "fields_matter": 0, "no_label": 0,
            "warnings": {}, "error": error, "seconds": round(seconds, 2)}


def run_native(item: Item, timeout: int = TIMEOUT_S, env: dict | None = None) -> dict:
    t0 = time.monotonic()
    cmd = [sys.executable, "-m", "eval.chain.worker", str(item.path), item.name]
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout, env={**os.environ, **(env or {})})
    except subprocess.TimeoutExpired:
        return _failed(item, "Timeout", time.monotonic() - t0)
    lines = [ln for ln in p.stdout.splitlines() if ln.startswith("{")]
    if p.returncode != 0 or not lines:
        return _failed(item, f"WorkerCrash:exit{p.returncode}", time.monotonic() - t0)
    return json.loads(lines[-1])


def docker_command(ref: str, item: Item) -> list[str]:
    return ["docker", "run", "--rm", "--network", "none", "--read-only", "--tmpfs", "/tmp",
            "-v", f"{item.path.resolve()}:/work/in/{item.name}:ro", ref,
            "python", "-m", "converter", "convert", f"/work/in/{item.name}"]


def run_image(item: Item, ref: str, timeout: int = TIMEOUT_S, runner=subprocess.run) -> dict:
    """Exit 0: converted (the form is on stdout, checked here); 2: refused (problem JSON on stderr); else failed."""
    t0 = time.monotonic()
    try:
        p = runner(docker_command(ref, item), capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return _failed(item, "Timeout", time.monotonic() - t0)
    secs = time.monotonic() - t0
    if p.returncode == 0:
        from tools.coi_lint import check

        try:
            form = json.loads(p.stdout)
        except ValueError:
            return _failed(item, "BadOutput", secs)
        n = sum(1 for lv, _ in check(form, "strict") if lv == "ERROR")
        fields = sum(len(q["field"]["repeatingSectionGrid"]) for t in form["tabs"] for q in t["questions"])
        return {"outcome": "converted", "gate": "passed", "lint_errors": n, "fields": fields, "fields_matter": 0,
                "no_label": 0, "warnings": {}, "error": "", "seconds": round(secs, 2)}
    if p.returncode == 2:
        try:
            body = json.loads(p.stderr.strip().splitlines()[-1])
        except (ValueError, IndexError):
            return _failed(item, "RefusalUnparsable", secs)
        if body.get("code") == "GATE_FAILED":
            return {**_failed(item, "GATE_FAILED", secs), "gate": "failed"}
        if is_polish(body.get("detail", "")):
            return {**_failed(item, "", secs), "outcome": "refused", "problem_code": body.get("code", "")}
        return _failed(item, "RefusalWithoutPolishReason", secs)
    return _failed(item, f"ContainerExit{p.returncode}", secs)


def run_item(item: Item, image: str | None = None, timeout: int = TIMEOUT_S) -> dict:
    rec = run_image(item, image, timeout) if image else run_native(item, timeout)
    return {"corpus": item.corpus, "key": item.key, "format": item.fmt, **rec}
