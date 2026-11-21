"""The gate command line: exit codes and output."""
from __future__ import annotations

import json

from app.gate.__main__ import main


def test_unreadable_file_exits_2(tmp_path, capsys):
    assert main([str(tmp_path / "missing.json")]) == 2


def test_broken_form_exits_1_and_names_checks(tmp_path, capsys):
    p = tmp_path / "f.json"
    p.write_text(json.dumps({"not": "a form"}), encoding="utf-8")
    assert main([str(p), "--no-journeys"]) == 1
    out = capsys.readouterr().out
    assert "G1" in out and "failed" in out


def test_json_output_parses(tmp_path, capsys):
    p = tmp_path / "f.json"
    p.write_text("[]", encoding="utf-8")
    main([str(p), "--json"])
    assert "checks" in json.loads(capsys.readouterr().out)
