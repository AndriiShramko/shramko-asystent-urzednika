"""AUDIT-8 VF-6: SECURITY.md may name only tools that exist, and may not call the repository a specification package
while it holds the converter service. Reads files only."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DOC = ROOT / "SECURITY.md"


def test_named_repository_paths_exist_or_are_marked_not_built():
    bad = []
    for line in DOC.read_text(encoding="utf-8").splitlines():
        for path in re.findall(r"`((?:tools|docs|apps)/[^`\s]+)`", line):
            if not (ROOT / path).exists() and "not built" not in line:
                bad.append(path)
    assert not bad, f"SECURITY.md names paths that do not exist: {bad}"


def test_scope_mentions_the_converter_when_it_exists():
    text = DOC.read_text(encoding="utf-8")
    if (ROOT / "apps" / "converter" / "app" / "main.py").exists():
        assert "This repository is a specification and research package." not in text
        assert "apps/converter" in text


def test_udip_commitments_are_not_presented_as_the_converter():
    text = DOC.read_text(encoding="utf-8")
    m = re.search(r"^## Design commitments[^\n]*", text, re.M)
    assert m and ("UDIP" in m.group(0) or "parked" in m.group(0)), \
        "the commitments (end-to-end encryption, language models, clerk approval) belong to the parked UDIP assistant"
