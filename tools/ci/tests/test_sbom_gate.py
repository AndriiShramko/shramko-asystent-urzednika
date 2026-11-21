"""Tests of tools/ci/sbom_gate.py: each rule refuses its planted fault, a clean list passes."""
from __future__ import annotations

import sys
from pathlib import Path

CI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CI))

import sbom_gate  # noqa: E402

LOCK = sbom_gate.lock_versions("pydantic==2.9.0 \\\n    --hash=sha256:aa\nsome_pkg==1.0 ; python_version >= '3.13' \\\n")
CLEAN = [
    {"name": "pydantic", "version": "2.9.0", "license": "MIT", "classifiers": []},
    {"name": "some-pkg", "version": "1.0", "license": "", "classifiers": ["License :: OSI Approved :: BSD License"]},
    {"name": "pip", "version": "99", "license": "MIT", "classifiers": []},
]


def test_clean_list_passes():
    assert sbom_gate.findings_of(CLEAN, LOCK, set()) == []


def test_lock_parsing_normalises_names():
    assert LOCK == {"pydantic": "2.9.0", "some-pkg": "1.0"}


def test_each_fault_is_refused():
    def with_(**kw):
        d = dict(CLEAN[0]); d.update(kw)
        return sbom_gate.findings_of([d], LOCK, set())
    assert "copyleft" in with_(license="GNU Lesser General Public License v3")[0]
    assert "copyleft" in with_(license="", classifiers=["License :: OSI Approved :: GNU Affero General Public License v3"])[0]
    assert "MPL" in with_(license="MPL-2.0")[0]
    assert sbom_gate.findings_of([dict(CLEAN[0], license="MPL-2.0")], LOCK, {"pydantic"}) == []
    assert "no licence" in with_(license="")[0]
    assert "not in the lock" in with_(name="stranger")[0]
    assert "lock says" in with_(version="2.8.0")[0]


def test_sbom_is_cyclonedx_with_purl():
    bom = sbom_gate.cyclonedx(CLEAN, "converter:core")
    assert bom["bomFormat"] == "CycloneDX" and len(bom["components"]) == 3
    assert bom["components"][0]["purl"].startswith("pkg:pypi/")
