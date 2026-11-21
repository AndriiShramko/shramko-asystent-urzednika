"""WP-F2a integration: the readers refuse by content, and one form in two formats reads as the same form."""
from __future__ import annotations

import io
import re
import zipfile

import pytest

from app.readers import ReaderError, read_document

from readers_builders import docx_bytes, p, pdf_bytes


def _pdf() -> bytes:
    def draw(c):  # noqa: ANN001
        c.drawString(72, 700, "Wniosek o wydanie zaswiadczenia")

    return pdf_bytes(draw)


def _xlsx_like() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("xl/workbook.xml", "<workbook/>")
    return buf.getvalue()


@pytest.mark.parametrize("data,fmt", [
    (b"just a text file, named .docx by the user\n" * 20, "docx"),
    (b"just a text file, named .pdf by the user\n" * 20, "pdf"),
    (_pdf(), "docx"),
    (docx_bytes(p("Wniosek")), "pdf"),
    (_xlsx_like(), "docx"),
    (b"", "pdf"),
])
def test_swapped_suffix_is_refused_by_content(data, fmt):
    with pytest.raises(ReaderError) as e:
        read_document(data, fmt)
    assert e.value.code in {"UNREADABLE", "UNSUPPORTED_FORMAT"}
    assert "Traceback" not in str(e.value)


def test_the_same_title_reads_from_pdf_and_docx():
    pdf = read_document(_pdf(), "pdf")
    docx = read_document(docx_bytes(p("Wniosek o wydanie zaswiadczenia")), "docx")
    norm = lambda s: re.sub(r"\W+", " ", s.lower()).strip()  # noqa: E731
    assert norm(pdf.pages[0].runs[0].text) == norm(docx.pages[0].runs[0].text)


@pytest.mark.sets
@pytest.mark.slow
def test_each_set_in_pdf_and_docx_shares_its_opening_runs():
    from collections import defaultdict

    from eval.golden import golden_inputs, judged_inputs

    by_set: dict[str, dict[str, object]] = defaultdict(dict)
    for f in golden_inputs() + judged_inputs():
        if f.suffix.lower() in (".pdf", ".docx") and f.exists():
            by_set[f.parent.name][f.suffix.lower()[1:]] = f
    norm = lambda s: re.sub(r"\W+", " ", s.lower()).strip()  # noqa: E731
    pairs = {k: v for k, v in by_set.items() if len(v) == 2}
    assert len(pairs) >= 7
    for name, d in pairs.items():
        first = {fmt: {norm(r.text) for r in read_document(f.read_bytes(), fmt).pages[0].runs[:20]
                       if len(norm(r.text)) > 8} for fmt, f in d.items()}
        assert len(first["pdf"] & first["docx"]) >= 3, name
