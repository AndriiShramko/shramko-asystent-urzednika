"""Synthetic files for WP-F20f: a minimal BIFF8 workbook (written from code, wrapped in a compound file) and RTF texts.
No file of the archive or of the task sets is read here."""
from __future__ import annotations

import struct

from sheet_doc_builders import ole_bytes


def rec(rid: int, body: bytes) -> bytes:
    return struct.pack("<HH", rid, len(body)) + body


def _font(weight: int) -> bytes:
    return rec(0x0031, struct.pack("<HHHHHBBBB", 200, 0, 0x7FFF, weight, 0, 0, 0, 0, 0) + bytes([5, 0]) + b"Arial")


def _xf(font: int, style: bool, borders: int = 0) -> bytes:
    prot = 0xFFF5 if style else 0x0001
    return rec(0x00E0, struct.pack("<HHHBBBBIIH", font, 0, prot, 0, 0, 0, 0xFC if style else 0, borders, 0, 0))


def biff8_workbook(cells: dict[tuple[int, int], str | float], bold: set[tuple[int, int]] = frozenset(),
                   boxed: set[tuple[int, int]] = frozenset(), merges: list[tuple[int, int, int, int]] = (),
                   name: str = "Arkusz1", version: int = 0x0600) -> bytes:
    """One sheet. XF 15 is plain, 16 bold, 17 boxed (all four borders thin); the first 15 XFs are style XFs."""
    glob = rec(0x0809, struct.pack("<HHHHII", version, 0x0005, 0x0DBB, 0x07CC, 0, 6))
    glob += rec(0x0042, struct.pack("<H", 1200))
    glob += _font(400) + _font(700)
    glob += b"".join(_xf(0, True) for _ in range(15))
    glob += _xf(0, False) + _xf(1, False) + _xf(0, False, borders=0x1111)
    bs_name = name.encode("latin-1")
    bs_len = 4 + 4 + 2 + 2 + len(bs_name)   # record header, offset, state and type, name length and flag, name
    eof = rec(0x000A, b"")
    sheet_at = len(glob) + bs_len + len(eof)
    glob += rec(0x0085, struct.pack("<IBB", sheet_at, 0, 0) + bytes([len(bs_name), 0]) + bs_name) + eof
    rows = [r for r, _ in cells] or [0]
    cols = [c for _, c in cells] or [0]
    sh = rec(0x0809, struct.pack("<HHHHII", version, 0x0010, 0x0DBB, 0x07CC, 0, 6))
    sh += rec(0x0200, struct.pack("<IIHHH", 0, max(rows) + 1, 0, max(cols) + 1, 0))
    for (r, c), v in sorted(cells.items()):
        xf = 16 if (r, c) in bold else 17 if (r, c) in boxed else 15
        if isinstance(v, str):
            sh += rec(0x0204, struct.pack("<HHHHB", r, c, xf, len(v), 0) + v.encode("latin-1"))
        else:
            sh += rec(0x0203, struct.pack("<HHHd", r, c, xf, v))
    if merges:
        sh += rec(0x00E5, struct.pack("<H", len(merges)) + b"".join(struct.pack("<HHHH", *m) for m in merges))
    sh += rec(0x000A, b"")
    return ole_bytes({"Workbook": glob + sh})


def xls_file(**kw) -> bytes:
    return biff8_workbook(**kw)


RTF_HEAD = r"{\rtf1\ansi\ansicpg1250\deff0{\fonttbl{\f0\fnil Arial;}}{\colortbl;\red0\green0\blue0;}"


def rtf(body: str, head: str = RTF_HEAD) -> bytes:
    """cp1250 file: `body` is plain text with RTF markup; characters above ASCII are written as raw cp1250 bytes."""
    body = body.replace("@u", chr(92) + "u")   # "@u8212" stands for the RTF word u8212 (keeps the source free of unicode escapes)
    return (head + body + "}").encode("cp1250")


def rtf_row(*cells: str, defs: str = "") -> str:
    ds = defs or "".join(rf"\cellx{1000 * (i + 1)}" for i in range(len(cells)))
    return r"\trowd" + ds + "".join(rf"\pard\intbl {c}\cell" for c in cells) + r"\row" + "\n"
