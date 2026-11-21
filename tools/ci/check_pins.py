#!/usr/bin/env python3
"""Refuse an unpinned supply chain (WP-F20, design 8 "supply chain").

    python tools/ci/check_pins.py [--dockerfile apps/converter/Dockerfile] [--workflows .github/workflows]

Rules, each a finding with file and line:
  - every FROM of the Dockerfile that is not an earlier stage names an image by digest (@sha256:<64 hex>),
    after the ARG defaults are substituted; a tag alone, `latest` or no digest is refused;
  - every `pip install` of the Dockerfile has --require-hashes, --only-binary=:all: and -r <lock file>
    (a dependency with only a source distribution then fails the build);
  - every `uses:` of a workflow names an action by a full 40-character commit hash (local ./ actions excepted;
    docker:// images need a digest).
Exit 1 when a finding exists. Runs in the first step of the image workflow, before anything is built.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIGEST = re.compile(r"@sha256:[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def logical_lines(text: str) -> list[tuple[int, str]]:
    """Dockerfile lines with backslash continuations joined; comments dropped. (line number, text)."""
    out, buf, start = [], "", 0
    for no, line in enumerate(text.splitlines(), start=1):
        if not buf and line.lstrip().startswith("#"):
            continue
        if not buf:
            start = no
        if line.rstrip().endswith("\\"):
            buf += line.rstrip()[:-1] + " "
            continue
        buf += line
        if buf.strip():
            out.append((start, buf.strip()))
        buf = ""
    if buf.strip():
        out.append((start, buf.strip()))
    return out


def check_dockerfile(path: Path) -> list[str]:
    findings, args, stages = [], {}, set()
    text = path.read_text(encoding="utf-8")
    for no, line in logical_lines(text):
        word, _, rest = line.partition(" ")
        word = word.upper()
        if word == "ARG":
            name, eq, value = rest.strip().partition("=")
            if eq:
                args[name.strip()] = value.strip().strip('"')
        elif word == "FROM":
            parts = [p for p in rest.split() if not p.startswith("--")]
            ref = parts[0] if parts else ""
            ref = re.sub(r"\$\{(\w+)\}|\$(\w+)", lambda m: args.get(m.group(1) or m.group(2), m.group(0)), ref)
            if len(parts) >= 3 and parts[1].upper() == "AS":
                stages.add(parts[2].lower())
            if ref.lower() in stages - ({parts[2].lower()} if len(parts) >= 3 else set()) or ref == "scratch":
                continue
            if "$" in ref:
                findings.append(f"{path.name}:{no}: FROM {ref}: an ARG without a default, the base cannot be checked")
            elif not DIGEST.search(ref):
                findings.append(f"{path.name}:{no}: FROM {ref}: base image not pinned by digest")
            elif ref.split("@")[0].endswith(":latest"):
                findings.append(f"{path.name}:{no}: FROM {ref}: tag latest")
        if re.search(r"\bpip3?\b.*\binstall\b", line) or re.search(r"-m pip install", line):
            for flag in ("--require-hashes", "--only-binary=:all:"):
                if flag not in line:
                    findings.append(f"{path.name}:{no}: pip install without {flag}")
            if not re.search(r"(-r|--requirement)\s+\S+\.lock", line):
                findings.append(f"{path.name}:{no}: pip install not from a .lock file")
    return findings


def check_workflow(path: Path) -> list[str]:
    findings = []
    for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        m = re.match(r"\s*(?:-\s*)?uses:\s*['\"]?([^'\"\s#]+)", line)
        if not m:
            continue
        ref = m.group(1)
        if ref.startswith("./"):
            continue
        if ref.startswith("docker://"):
            if not DIGEST.search(ref):
                findings.append(f"{path.name}:{no}: {ref}: container action not pinned by digest")
            continue
        _, at, version = ref.partition("@")
        if not at or not SHA40.match(version):
            findings.append(f"{path.name}:{no}: {ref}: action not pinned by a full commit hash")
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dockerfile", type=Path, action="append")
    ap.add_argument("--workflows", type=Path, default=ROOT / ".github" / "workflows")
    args = ap.parse_args(argv)
    dockerfiles = args.dockerfile or [ROOT / "apps" / "converter" / "Dockerfile"]
    findings: list[str] = []
    for d in dockerfiles:
        findings += check_dockerfile(d)
    flows = sorted(args.workflows.glob("*.yml")) + sorted(args.workflows.glob("*.yaml")) \
        if args.workflows.is_dir() else []
    for w in flows:
        findings += check_workflow(w)
    for f in findings:
        print("PIN  " + f)
    print(f"check_pins: {len(dockerfiles)} Dockerfile(s), {len(flows)} workflow(s), {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
