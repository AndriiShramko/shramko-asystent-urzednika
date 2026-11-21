"""The readers' registry: one entry, self-registering modules, every failure a ReaderError (WP-F2a)."""
from __future__ import annotations

import pytest

from app import readers
from app.readers import ReaderError, ReadResult, formats, read_document


def test_pdf_and_docx_registered():
    assert {"pdf", "docx"} <= set(formats())


def test_unknown_format_refused():
    with pytest.raises(ReaderError) as e:
        read_document(b"abc", "nope")
    assert e.value.code == "UNSUPPORTED_FORMAT"


def test_any_exception_of_a_reader_becomes_unreadable(monkeypatch):
    def broken(data, options):  # noqa: ANN001
        raise KeyError("internal detail")

    monkeypatch.setitem(readers._READERS, "png", broken)
    with pytest.raises(ReaderError) as e:
        read_document(b"\x89PNG", "png")
    assert e.value.code == "UNREADABLE" and "internal detail" not in e.value.reason


def test_an_invalid_page_model_is_unreadable_not_a_crash(monkeypatch):
    monkeypatch.setitem(readers._READERS, "png", lambda data, options: ReadResult(reader="Bad Name!", pages=[]))
    with pytest.raises(ReaderError) as e:
        read_document(b"x", "png")
    assert e.value.code == "UNREADABLE"


def test_two_readers_for_one_format_refused():
    with pytest.raises(RuntimeError):
        readers.register("pdf")(lambda data, options: None)


def test_options_from_a_mapping_ignore_unknown_keys():
    assert readers.ReadOptions.of({"ocr_min_chars": 5, "something_else": 1}).ocr_min_chars == 5
