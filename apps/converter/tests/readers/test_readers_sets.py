"""Readers on the partner's task sets (local only; skipped where they are absent, e.g. in CI). WP-F2a acceptance."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.readers import read_document

pytestmark = [pytest.mark.sets, pytest.mark.slow]  # about 20 s on the laptop: full gate, not the fast one


def _inputs(fmt: str) -> list[Path]:
    from eval.golden import golden_inputs, judged_inputs

    return [p for p in golden_inputs() + judged_inputs() if p.suffix.lower() == f".{fmt}" and p.exists()]


def _one(set_key: str, fmt: str) -> Path:
    hits = [p for p in _inputs(fmt) if set_key in p.parent.name]
    assert len(hits) == 1, f"{set_key} {fmt}: {len(hits)} files"
    return hits[0]


@pytest.mark.parametrize("fmt", ["pdf", "docx"])
def test_every_file_of_the_sets_reads(fmt):
    files = _inputs(fmt)
    assert len(files) >= 8
    for f in files:
        m = read_document(f.read_bytes(), fmt)
        assert m.pages and sum(len(p.runs) for p in m.pages) > 10, f.parent.name


@pytest.mark.parametrize("set_key,minimum", [("judged-02", 60), ("judged-08", 600)])
def test_text_box_docx_gives_runs_with_boxes(set_key, minimum):
    m = read_document(_one(set_key, "docx").read_bytes(), "docx")
    assert m.source.reader == "docx.native"
    boxed = [r for p in m.pages for r in p.runs if r.box is not None]
    assert len(boxed) >= minimum
    assert sum(len(p.lines) for p in m.pages) > 100


def test_set_8_docx_and_pdf_agree_on_pages():
    pdf = read_document(_one("judged-08", "pdf").read_bytes(), "pdf")
    docx = read_document(_one("judged-08", "docx").read_bytes(), "docx")
    assert len(pdf.pages) == len(docx.pages) == 6


def test_set_9_flow_docx_and_pdf_have_sixteen_pages():
    assert len(read_document(_one("judged-09", "pdf").read_bytes(), "pdf").pages) == 16
    docx = read_document(_one("judged-09", "docx").read_bytes(), "docx")
    assert docx.source.reader == "docx.flow" and len(docx.pages) == 16


def test_no_pdf_of_the_sets_needs_the_image_way():
    for f in _inputs("pdf"):
        m = read_document(f.read_bytes(), "pdf")
        assert not [w for w in m.warnings if w.code in ("UNREADABLE_PART", "OCR_USED")], f.parent.name
