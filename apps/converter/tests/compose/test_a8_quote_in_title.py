"""A8 VB-2 (analysis 13-F2): a page title with an apostrophe or a backslash still gives conditions the gate reads.

The partner's exports and both reference readers (`app.gate.conditions.REF`, `tools/coi_lint.REF`) know only the
single-quoted reference `tabs['P' in title]`. A JSONata string in single quotes cannot hold `'`, so a matter page
titled from the paper ("Oświadczenie 'A'", a path "C:\\x") used to be written in double quotes: G5 failed, G6 to G8
skipped the condition, and the form shipped with only a GATE_G5 warning.
"""
from __future__ import annotations

import json

import pytest

from app.compose import compose
from app.gate import check
from compose_helpers import brief
from tools import coi_lint


def _brief(title: str):
    return brief(matter=[{"title": title, "role": "matter/oswiadczenie", "fields": [
        {"key": "tryb", "label": "Czy wniosek jest pilny", "type": "RADIO", "options": ["Tak", "Nie"]},
        {"key": "uzasadnienie", "label": "Uzasadnienie pilności", "type": "TEXTAREA",
         "show_if": {"field": "tryb", "is": "Tak"}}]}])


@pytest.mark.parametrize("title", ["Oświadczenie 'A'", "Oświadczenie A\\B", "Dane l'urzędu \"X\""])
def test_conditions_on_a_quoted_page_title_pass_the_gate(title: str) -> None:
    form = json.loads(compose(_brief(title)).form.to_json_bytes())
    queries = [s["query"] for t in form["tabs"] for q in t["questions"] for c in q["field"]["repeatingSectionGrid"]
               for s in c["field"].get("states", [])]
    assert any("tabs[" in q for q in queries), "the brief's condition was not written"
    report = check(form)
    failed = {c.id: [f.message for f in c.findings][:2] for c in report.failed}
    assert failed == {}
    g6 = report.get("G6")
    assert g6.status == "passed"
    assert [m for lvl, m in coi_lint.lint(form) if lvl == "ERROR"] == []


def test_a_plain_title_is_untouched() -> None:
    form = json.loads(compose(_brief("Oświadczenie A")).form.to_json_bytes())
    assert "Oświadczenie A" in [t["title"] for t in form["tabs"]]
