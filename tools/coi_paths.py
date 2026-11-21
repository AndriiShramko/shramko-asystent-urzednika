#!/usr/bin/env python3
"""Where the partner's task sets are on this machine.

Some sets are kept out of git (see data/coi/README.md), so a git worktree of a work package does not
contain them. Every test or evaluation that needs them asks this module instead of building a path:

    from tools.coi_paths import coi_dir, sets
    for folder in sets("judged"): ...

Order: the environment variable COI_DATA_DIR; the data/coi of this checkout if it holds the judged sets;
the data/coi of the main checkout (found through git's common directory).
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


def _has_sets(p: Path) -> bool:
    return p.is_dir() and any(p.glob("judged-*"))


def coi_dir() -> Path:
    env = os.environ.get("COI_DATA_DIR", "").strip()
    if env and Path(env).is_dir():
        return Path(env)
    local = HERE / "data" / "coi"
    if _has_sets(local):
        return local
    try:
        common = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=HERE, capture_output=True, text=True, timeout=10).stdout.strip()
        main = Path(common).parent / "data" / "coi"
        if _has_sets(main):
            return main
    except (OSError, subprocess.SubprocessError):
        pass
    return local


def sets(kind: str = "") -> list[Path]:
    """Folders of the task sets; kind is "judged", "reference" or "" for both."""
    base = coi_dir()
    out = [p for p in sorted(base.iterdir()) if p.is_dir() and p.name.startswith(("judged-", "reference-"))] if base.is_dir() else []
    return [p for p in out if p.name.startswith(kind)] if kind else out


if __name__ == "__main__":
    print(coi_dir())
    for s in sets():
        print(" ", s.name, len(list(s.iterdir())), "files")
