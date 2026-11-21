"""Native tests of the vulnerability gate and the digest tool (WP-F20b). No network."""
from __future__ import annotations

import json
import sys
from pathlib import Path

CI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CI))

import image_digest  # noqa: E402
import vuln_gate  # noqa: E402


def match(sev: str, state: str, versions=None, vid="CVE-0000-0001") -> dict:
    return {"vulnerability": {"id": vid, "severity": sev, "fix": {"state": state, "versions": versions or []}},
            "artifact": {"name": "pkg", "version": "1.0"}}


def report(tmp_path, *matches) -> str:
    path = tmp_path / "grype.json"
    path.write_text(json.dumps({"matches": list(matches)}), encoding="utf-8")
    return str(path)


def test_critical_with_a_fix_blocks(tmp_path):
    assert vuln_gate.main([report(tmp_path, match("Critical", "fixed", ["1.1"]))]) == 1


def test_everything_else_is_listed_and_does_not_block(tmp_path, capsys):
    rep = report(tmp_path, match("Critical", "not-fixed", vid="CVE-A"), match("High", "fixed", ["2"], vid="CVE-B"),
                 match("Low", "unknown", vid="CVE-C"))
    assert vuln_gate.main([rep]) == 0
    out = capsys.readouterr().out
    assert all(v in out for v in ("CVE-A", "CVE-B", "CVE-C")) and "Blocking (critical with a fix): 0" in out


def test_clean_report_passes_and_unreadable_report_is_not_a_pass(tmp_path):
    assert vuln_gate.main([report(tmp_path)]) == 0
    assert vuln_gate.main([str(tmp_path / "missing.json")]) == 2
    bad = tmp_path / "bad.json"
    bad.write_text("{}", encoding="utf-8")
    assert vuln_gate.main([str(bad)]) == 2


def test_image_digest_tags():
    assert image_digest.tag_for("abc", "core") == "abc"
    assert image_digest.tag_for("abc", "plus") == "abc-plus"
