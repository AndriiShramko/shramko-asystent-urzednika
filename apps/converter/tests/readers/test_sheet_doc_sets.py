"""WP-F2b readers on the partner's task sets (local only; skipped where they are absent, e.g. in CI)."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.readers import read_document

pytestmark = [pytest.mark.sets, pytest.mark.slow]  # about 20 s on the laptop: full gate, not the fast one

TITLE_WORDS = ("wniosek", "deklaracja")


def _inputs(fmt: str) -> list[Path]:
    from eval.golden import golden_inputs, judged_inputs

    return [p for p in golden_inputs() + judged_inputs() if p.suffix.lower() == f".{fmt}" and p.exists()]


def _ole_docs() -> list[Path]:
    return [p for p in _inputs("doc") if p.read_bytes()[:8] == bytes.fromhex("d0cf11e0a1b11ae1")]


@pytest.mark.parametrize("fmt,minimum", [("xlsx", 7), ("ods", 9)])
def test_every_sheet_of_the_sets_reads(fmt, minimum):
    files = _inputs(fmt)
    assert len(files) >= minimum
    for f in files:
        m = read_document(f.read_bytes(), fmt)
        assert m.source.reader == fmt and all(p.origin == "flow" and p.name for p in m.pages)
        assert sum(len(p.runs) for p in m.pages) > 10 and all(p.tables for p in m.pages), f.parent.name


def test_xlsx_and_ods_of_one_set_agree_on_sheets_and_title():
    pairs = 0
    for x in _inputs("xlsx"):
        o = [p for p in _inputs("ods") if p.parent == x.parent]
        if not o:
            continue
        mx, mo = read_document(x.read_bytes(), "xlsx"), read_document(o[0].read_bytes(), "ods")
        assert [p.name for p in mx.pages] == [p.name for p in mo.pages], x.parent.name
        tx = [r.text.lower() for p in mx.pages for r in p.runs]
        to = [r.text.lower() for p in mo.pages for r in p.runs]
        assert abs(len(tx) - len(to)) <= 1, x.parent.name
        assert next(t for t in tx if any(w in t for w in TITLE_WORDS)) in to, x.parent.name
        pairs += 1
    assert pairs >= 7


def test_every_binary_doc_gives_its_title_in_the_first_twenty_runs():
    files = _ole_docs()
    assert len(files) >= 7
    for f in files:
        m = read_document(f.read_bytes(), "doc")
        first = [r.text.lower() for p in m.pages for r in p.runs][:20]
        assert any(w in t for t in first for w in TITLE_WORDS), f.parent.name


def test_text_box_docs_of_sets_2_and_8_read_their_boxes():
    for key, minimum in (("judged-02", 60), ("judged-08", 600)):
        f = next(p for p in _ole_docs() if key in p.parent.name)
        runs = [r for p in read_document(f.read_bytes(), "doc").pages for r in p.runs]
        assert len(runs) >= minimum and any(r.anchor.startswith("txbx[") for r in runs), key
