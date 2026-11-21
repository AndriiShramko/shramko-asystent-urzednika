#!/usr/bin/env python3
"""SBOM and licence gate of the final image (WP-F20, design 9.2 step 5).

    python tools/ci/sbom_gate.py --image converter:core --lock apps/converter/requirements.lock --out reports/sbom-core.json

Runs the image's own interpreter (no network, read-only) to list the installed Python distributions with their
licence metadata, writes a CycloneDX 1.5 JSON document, and fails (exit 1) when
  - a distribution is under a GPL, AGPL or LGPL licence (AGENTS.md rule 4);
  - a distribution is under MPL (allowed only after the lead says yes: reported as a finding until `--allow-mpl NAME`);
  - an installed distribution is not in the lock file, or its version differs (the image holds what was hashed);
  - a distribution has no licence metadata at all (an honest gap: named in the findings, never a silent pass).
Build-time tool: it calls docker, not the network. The pure functions are tested in tools/ci/tests.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

LISTER = (
    "import importlib.metadata as m, json\n"
    "out = []\n"
    "for d in m.distributions():\n"
    "    md = d.metadata\n"
    "    out.append({'name': md['Name'], 'version': md['Version'], 'license': md.get('License-Expression') or md.get('License') or '',\n"
    "                'classifiers': [c for c in (md.get_all('Classifier') or []) if c.startswith('License')]})\n"
    "print(json.dumps(out))\n"
)

COPYLEFT = re.compile(r"\b(A?GPL|LGPL|GNU (Lesser |Affero )?General Public)", re.I)
MPL = re.compile(r"\bMPL\b|Mozilla Public", re.I)


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def lock_versions(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s;\\]+)", line)
        if m:
            out[norm(m.group(1))] = m.group(2)
    return out


def licence_text(d: dict) -> str:
    lic = d.get("license", "")
    if len(lic) > 200:  # a whole licence text pasted into the field: the classifiers say more
        lic = ""
    return " | ".join([lic] + d.get("classifiers", [])).strip(" |")


def findings_of(dists: list[dict], lock: dict[str, str], allow_mpl: set[str]) -> list[str]:
    out = []
    for d in dists:
        n, lic = norm(d["name"]), licence_text(d)
        if COPYLEFT.search(lic):
            out.append(f"{d['name']} {d['version']}: copyleft licence ({lic})")
        elif MPL.search(lic) and n not in allow_mpl:
            out.append(f"{d['name']} {d['version']}: MPL needs the lead's yes ({lic})")
        elif not lic:
            out.append(f"{d['name']} {d['version']}: no licence metadata")
        if n in ("pip", "setuptools", "wheel"):
            continue
        if n not in lock:
            out.append(f"{d['name']} {d['version']}: installed but not in the lock file")
        elif lock[n] != d["version"]:
            out.append(f"{d['name']}: installed {d['version']}, lock says {lock[n]}")
    return out


def cyclonedx(dists: list[dict], image: str) -> dict:
    return {
        "bomFormat": "CycloneDX", "specVersion": "1.5", "version": 1,
        "metadata": {"component": {"type": "container", "name": image}},
        "components": [
            {"type": "library", "name": d["name"], "version": d["version"],
             "purl": f"pkg:pypi/{norm(d['name'])}@{d['version']}",
             "licenses": [{"license": {"name": licence_text(d) or "NOASSERTION"}}]}
            for d in sorted(dists, key=lambda x: norm(x["name"]))
        ],
    }


def list_installed(image: str) -> list[dict]:
    r = subprocess.run(
        ["docker", "run", "--rm", "--network", "none", "--read-only", "--cap-drop", "ALL", "--entrypoint", "python",
         image, "-I", "-c", LISTER], capture_output=True, text=True, timeout=120)
    if r.returncode:
        raise SystemExit(f"cannot list the distributions: {r.stderr[-500:]}")
    return json.loads(r.stdout)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--lock", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--allow-mpl", action="append", default=[])
    a = ap.parse_args()
    dists = list_installed(a.image)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cyclonedx(dists, a.image), indent=1, sort_keys=True), encoding="utf-8")
    found = findings_of(dists, lock_versions(Path(a.lock).read_text(encoding="utf-8")), {norm(x) for x in a.allow_mpl})
    print(f"{len(dists)} distributions, {len(found)} findings, SBOM {out}")
    for f in found:
        print("  -", f)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
