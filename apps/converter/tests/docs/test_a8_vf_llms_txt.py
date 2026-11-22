"""AUDIT-8 VF-7: llms.txt (the entry for agents and answer engines) must describe what the repository builds today,
the forms converter, and link only to files that exist. Reads files only."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DOC = ROOT / "llms.txt"


def test_summary_names_the_converter_when_it_exists():
    text = DOC.read_text(encoding="utf-8")
    if (ROOT / "apps" / "converter" / "app" / "main.py").exists():
        summary = next(line for line in text.splitlines() if line.startswith("> "))
        assert "Cyfryzacja formularzy" in summary, "the summary line still describes only the parked UDIP brief"
        assert "apps/converter/README.md" in text, "no link to the converter's own README"


def test_repository_links_point_to_existing_files():
    missing = [p for p in re.findall(r"blob/main/([^)\s]+)", DOC.read_text(encoding="utf-8"))
               if not (ROOT / p).exists()]
    assert not missing, f"llms.txt links to files that do not exist: {missing}"
