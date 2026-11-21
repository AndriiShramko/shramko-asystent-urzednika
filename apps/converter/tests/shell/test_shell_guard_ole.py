"""Integration findings from the partner's sets, each pinned with a synthetic file.

1. Real Word 97 files carry an Office theme package inside one of their streams: the zip proof must not make such a
   file a polyglot; a zip appended at the end of it still is one.
2. Two forms of the sets are named .DOC but hold a DOCX package: read by content, as DOCX. The other swaps stay
   refused (a DOCX named .xlsx, a legacy workbook named .doc).
"""
from __future__ import annotations

import factory as fx
import pytest

from app.config import Settings
from app.guard import ProblemError, inspect_upload

S = Settings(auth_mode="off", max_upload_bytes=200_000)


def _doc_with_embedded_zip() -> bytes:
    base, pkg = fx.doc(), fx.zip_of({"[Content_Types].xml": b"<x/>", "theme/theme1.xml": b"<t/>"})
    return base[:-4096] + pkg + b"\0" * (4096 - len(pkg))


def _code(name: str, data: bytes) -> str:
    with pytest.raises(ProblemError) as ei:
        inspect_upload(name, data, S)
    return ei.value.code


def test_a_legacy_word_file_with_a_theme_package_inside_is_still_a_doc():
    assert inspect_upload("a.doc", _doc_with_embedded_zip(), S).kind == "doc"


def test_a_legacy_word_file_with_a_zip_appended_is_still_a_polyglot():
    assert _code("a.doc", fx.doc() + fx.zip_of({"a.txt": b"x"})) == "TYPE_MISMATCH"


@pytest.mark.parametrize("name", ["a.doc", "A.DOC"])
def test_a_docx_named_doc_is_read_as_docx(name):
    info = inspect_upload(name, fx.docx(), S)
    assert (info.kind, info.ext) == ("docx", "doc")


def test_the_other_swaps_stay_refused():
    assert _code("a.xlsx", fx.zip_of({"hello.bin": b"x"})) == "TYPE_MISMATCH"
    assert _code("a.doc", fx.ole("Other")) == "TYPE_MISMATCH"
    assert _code("a.doc", fx.zip_of({"hello.bin": b"x"})) == "TYPE_MISMATCH"
