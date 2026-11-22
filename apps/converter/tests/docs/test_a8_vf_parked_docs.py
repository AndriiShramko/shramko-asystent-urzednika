"""AUDIT-8 VF-8: the pre-event demo scripts and jury table describe the parked counter product; each must say so at
the top and point to the converter's jury answers, so a juror does not take them for the built product."""
from __future__ import annotations

from pathlib import Path

import pytest

HACK = Path(__file__).resolve().parents[4] / "docs" / "05-hackathon"


@pytest.mark.parametrize("name", ["demo-script-formularze.md", "demo-script.md", "jury-qa.md"])
def test_parked_doc_says_so_at_the_top(name):
    head = "\n".join((HACK / name).read_text(encoding="utf-8").splitlines()[:5])
    assert "parked" in head and "not built" in head, f"{name} reads as the built product"
    assert "(jury-qa-formularze.md)" in head and (HACK / "jury-qa-formularze.md").exists()
