"""WP-F4 acceptance on the partner's judged sets (local only): fields of the matter per set, the addressee conflict
of set 6, one selector and no second form on set 9, and the stored briefs of eval/briefs/."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.config import Settings, read_options
from app.find import find
from app.mean import understand
from app.readers import read_document
from tools.coi_paths import sets

pytestmark = pytest.mark.sets

SETTINGS = Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false"})
BRIEFS = Path(__file__).resolve().parents[4] / "eval" / "briefs"
# floor of fields of the matter per set number (measured at the acceptance stage, minus nothing: a drop is a regression)
FLOOR = {"02": 5, "03": 2, "04": 6, "06": 16, "07": 10, "08": 24, "09": 42}


def briefs_of(number: str):
    for folder in sets("judged"):
        if folder.name.startswith(f"judged-{number}"):
            for f in sorted(folder.iterdir()):
                if f.suffix.lower() in (".pdf", ".docx"):
                    model = read_document(f.read_bytes(), f.suffix.lower()[1:], read_options(SETTINGS))
                    yield f.suffix.lower(), understand(model, find(model))


def matter_labels(brief) -> list[str]:
    return [x.label for s in brief.matter for x in s.fields]


@pytest.mark.parametrize("number", sorted(FLOOR))
def test_each_judged_set_holds_fields_of_the_matter(number):
    seen = 0
    for ext, brief in briefs_of(number):
        assert len(matter_labels(brief)) >= FLOOR[number], (number, ext)
        seen += 1
    assert seen >= 1


def test_set_6_names_two_offices_and_warns_with_both_quotes():
    for ext, brief in briefs_of("06"):
        conflicts = [w for w in brief.warnings if w.code == "ADDRESSEE_CONFLICT"]
        assert conflicts and len(conflicts[0].evidence) == 2, ext


def test_set_9_has_one_selector_and_no_second_form_from_the_docx():
    for ext, brief in briefs_of("09"):
        if ext != ".docx":
            continue
        keys = [x.key for s in brief.matter for x in s.fields]
        assert keys.count("rodzaj_wniosku") == 1


def test_the_stored_briefs_cover_every_judged_set():
    stored = {p.name.split(".")[0] for p in BRIEFS.glob("judged-*.json")}
    if not stored:
        pytest.skip("eval/briefs/*.json are local only (they quote the partner's forms); run eval/briefs/make_briefs.py")
    assert {f.name for f in sets("judged")} <= stored
    for p in BRIEFS.glob("judged-*.json"):
        assert "matter" in json.loads(p.read_text(encoding="utf-8"))
