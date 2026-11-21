"""WP-F3b, composer second pass: a single yes-or-no box passes the strict linter; an attachment keeps its brief key."""
from __future__ import annotations

import json

from app.compose import compose
from tests.compose.compose_helpers import brief
from tools import coi_lint


def _matter(*fields: dict) -> list[dict]:
    return [{"title": "Szczegóły sprawy", "role": "matter/szczegoly", "fields": list(fields)}]


def test_a_single_box_is_a_checkbox_with_one_option_and_passes_the_strict_linter() -> None:
    b = brief(matter=_matter({"key": "wysylka_poczta", "label": "Proszę o wysłanie decyzji pocztą", "type": "CHECKBOX"}))
    result = compose(b)
    form = json.loads(result.form.to_json_bytes())
    boxes = [q["field"] for t in form["tabs"] for s in t["questions"] for q in s["field"]["repeatingSectionGrid"]
             if q["field"]["type"] == "CHECKBOX"]
    assert len(boxes) == 1
    assert boxes[0]["title"] == "Proszę o wysłanie decyzji pocztą"
    assert [o["name"] for o in boxes[0]["options"]] == ["Tak"]
    assert [m for k, m in coi_lint.check(form, "strict") if k == "ERROR"] == []
    assert any(r.code == "INFERRED_SHAPE" for r in result.remarks)


def test_a_checkbox_with_options_keeps_its_options() -> None:
    b = brief(matter=_matter({"key": "zakres", "label": "Zakres", "type": "CHECKBOX", "options": ["Pierwszy", "Drugi"]}))
    form = json.loads(compose(b).form.to_json_bytes())
    opts = [[o["name"] for o in q["field"]["options"]] for t in form["tabs"] for s in t["questions"]
            for q in s["field"]["repeatingSectionGrid"] if q["field"]["type"] == "CHECKBOX"]
    assert opts == [["Pierwszy", "Drugi"]]


def test_an_attachment_with_a_key_is_named_in_brief_keys() -> None:
    b = brief(attachments=[{"label": "Kopia umowy najmu", "key": "kopia_umowy", "required": True}])
    result = compose(b)
    assert "kopia_umowy" in result.brief_keys.values()
    form = json.loads(result.form.to_json_bytes())
    uploads = {result.brief_keys.get(q["field"]["id"]) for t in form["tabs"] for s in t["questions"]
               for q in s["field"]["repeatingSectionGrid"] if q["field"]["type"] == "FILE_UPLOADER"}
    assert "kopia_umowy" in uploads
