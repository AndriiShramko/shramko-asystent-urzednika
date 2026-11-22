"""AUDIT-8 VD-5 (api-analyses 15 F1, F2): a negative length in a hostile file made a reader loop forever.

DOC: a Prc record of the piece table with cbGrpprl -3 leaves the position where it was. RTF: `\\bin-6` moves the
read position back to the start of its own token. Both must end at once: a reader error for the DOC, the rest of
the text for the RTF. Each call runs in a daemon thread, so a regression fails the test instead of hanging it.
"""
from __future__ import annotations

import threading

import pytest

from app.readers import read_document
from app.readers._base import ReaderError
from app.readers.doc import parse_clx

LIMIT_S = 5.0


def _within_limit(fn):  # noqa: ANN001, ANN202
    out: dict[str, object] = {}

    def run() -> None:
        try:
            out["value"] = fn()
        except Exception as e:  # noqa: BLE001
            out["error"] = e

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(LIMIT_S)
    assert not t.is_alive(), "the reader did not finish: endless loop"
    return out


def test_doc_prc_with_negative_length_is_a_reader_error():
    out = _within_limit(lambda: parse_clx(b"\x01\xfd\xff" + b"\x00" * 16, 4096))
    assert isinstance(out.get("error"), ReaderError)


def test_rtf_bin_with_negative_count_ends():
    data = b"{\\rtf1\\ansi Imie\\bin-6 Nazwisko\\par}"
    out = _within_limit(lambda: read_document(data, "rtf"))
    if "error" in out:
        assert isinstance(out["error"], ReaderError)
    else:
        text = " ".join(r.text for p in out["value"].pages for r in p.runs)
        assert "Imie" in text


@pytest.mark.parametrize("cb", [b"\x00\x00", b"\x02\x00"])
def test_doc_prc_with_valid_length_still_reaches_the_piece_table(cb):
    # a Prc of length 0 or 2 is skipped; what follows is not a Pcdt here, so the usual error comes, not a hang
    out = _within_limit(lambda: parse_clx(b"\x01" + cb + b"\x00\x00" + b"\x09" * 8, 4096))
    assert isinstance(out.get("error"), ReaderError)
