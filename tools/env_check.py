"""Step 0 of WP-F1: one line per piece of the build machine. Reads only; never changes the machine.

    python tools/env_check.py            # prints a table, exit code 0 always
    python tools/env_check.py --md       # the same as a markdown table (for docs/03-plan/wip/environment.md)

The product never asks which path was taken: the result decides nothing in the code.
"""
from __future__ import annotations

import shutil
import subprocess
import sys

FIX = {
    "Python 3.14": "install per user (no administrator rights); until then develop on 3.13",
    "Docker": "owner only: WSL 2 and Docker Desktop (administrator rights, restart); else CI builds the image (WP-F20)",
    "WSL": "owner only: wsl.exe --install",
    "Tesseract + pol": "install for the user, or go on: the second OCR engine stands in, Tesseract tests run in CI",
    "Node 22": "install Node 22",
}


def run(cmd: list[str]) -> tuple[bool, str]:
    if shutil.which(cmd[0]) is None:
        return False, "not found"
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, type(exc).__name__
    raw = p.stdout + p.stderr
    # wsl.exe writes UTF-16: drop the NUL bytes before decoding
    text = raw.replace(b"\x00", b"").decode("utf-8", "replace").strip()
    return p.returncode == 0, (text.splitlines() or [""])[0][:100]


def checks() -> list[tuple[str, bool, str]]:
    out: list[tuple[str, bool, str]] = []
    ok, txt = run(["py", "-3.14", "--version"])
    out.append(("Python 3.14", ok, txt if ok else "absent (running " + sys.version.split()[0] + ")"))
    out.append(("Python in use", True, sys.version.split()[0]))
    ok, txt = run(["docker", "version", "--format", "{{.Server.Version}}"])
    out.append(("Docker", ok, txt))
    ok, txt = run(["wsl", "--status"])
    out.append(("WSL", ok, txt))
    ok, txt = run(["tesseract", "--list-langs"])
    if ok:
        try:
            langs = subprocess.run(["tesseract", "--list-langs"], capture_output=True, timeout=20, text=True).stdout.split()
        except (OSError, subprocess.TimeoutExpired):
            langs = []
        ok = "pol" in langs
        txt = "pol present" if ok else "installed, no pol"
    out.append(("Tesseract + pol", ok, txt))
    ok, txt = run(["node", "--version"])
    out.append(("Node 22", ok and txt.startswith("v22"), txt))
    return out


def main() -> int:
    md = "--md" in sys.argv
    rows = checks()
    if md:
        print("| Piece | State | Detail | If missing |\n|---|---|---|---|")
    for name, ok, txt in rows:
        fix = "" if ok else FIX.get(name, "")
        if md:
            print(f"| {name} | {'ok' if ok else 'MISSING'} | {txt} | {fix} |")
        else:
            print(f"{'ok     ' if ok else 'MISSING'}  {name:<16} {txt}" + (f"   -> {fix}" if fix else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
