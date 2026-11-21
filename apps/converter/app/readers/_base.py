"""Pieces shared by the readers: options, the one error, ids, and small text rules.

A reader module of this package registers itself with `app.readers.register` and returns a `ReadResult`;
`app.readers.read_document` turns that into the page model (app/model/page.py). Underscore modules are not readers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from app.model.common import Warning
from app.model.page import Page


@dataclass(frozen=True)
class ReadOptions:
    """Limits and thresholds of the readers. WP-F1's configuration maps onto these names when it wires them."""

    ocr_min_chars: int = 20          # design 6.2: a PDF page with fewer characters takes the image way
    max_pages: int = 500             # a document with more pages is refused, not read halfway
    max_part_bytes: int = 64 << 20   # a ZIP part larger than this when unpacked is refused (DOCX)
    max_ratio: int = 200             # unpacked / packed size of a ZIP part above this is refused (zip bomb)
    max_cells: int = 200_000         # sheet cells a workbook may expand to (XLSX, ODS repeats), counted first

    @classmethod
    def of(cls, options: ReadOptions | Mapping[str, Any] | None) -> ReadOptions:
        if options is None:
            return cls()
        if isinstance(options, cls):
            return options
        known = {k: v for k, v in dict(options).items() if k in cls.__dataclass_fields__}
        return cls(**known)


class ReaderError(Exception):
    """The file cannot be read. The service answers 422 with `code` and `reason`; never a stack trace.

    Codes: UNREADABLE (broken or not what it claims), ENCRYPTED, TOO_LARGE, UNSUPPORTED_FORMAT.
    `reason` is a short sentence about the file's structure; it never quotes the file's content.
    """

    def __init__(self, code: str, reason: str):
        super().__init__(f"{code}: {reason}")
        self.code = code
        self.reason = reason


@dataclass
class ReadResult:
    reader: str
    pages: list[Page]
    warnings: list[Warning] = field(default_factory=list)


class Ids:
    """Document-wide ids: r1, r2 ... for runs, l for lines, q for rects, t for tables, w for widgets."""

    def __init__(self) -> None:
        self._n: dict[str, int] = {}

    def next(self, prefix: str) -> str:
        n = self._n.get(prefix, 0) + 1
        self._n[prefix] = n
        return f"{prefix}{n}"


# Characters that draw a place to fill when three or more stand in a row: dots, underscores, ellipses.
LEADER_CHARS = frozenset("._…‥․‒–—―ˍ＿")
LEADER_MIN = 3

_BOLD_MARKS = ("bold", "black", "heavy", "semibold", "demibold", "demi")


def is_bold_font(fontname: str | None) -> bool:
    """Bold by the font's name, after the subset prefix ("ABCDEF+Arial-BoldMT" -> True)."""
    if not fontname:
        return False
    name = fontname.split("+", 1)[-1].lower()
    return any(m in name for m in _BOLD_MARKS)


def leader_spans(text: str) -> list[tuple[int, int, bool]]:
    """Split text into (start, end, is_leader) spans; a leader is LEADER_MIN or more leader characters in a row."""
    spans: list[tuple[int, int, bool]] = []
    i, n = 0, len(text)
    start = 0
    while i < n:
        if text[i] in LEADER_CHARS:
            j = i
            while j < n and text[j] in LEADER_CHARS:
                j += 1
            if j - i >= LEADER_MIN:
                if i > start:
                    spans.append((start, i, False))
                spans.append((i, j, True))
                start = j
            i = j
        else:
            i += 1
    if start < n:
        spans.append((start, n, False))
    return spans


def nn(**kw: Any) -> dict[str, Any]:
    """Keyword arguments without the None ones: our contracts refuse an explicit null (absent means none)."""
    return {k: v for k, v in kw.items() if v is not None}


def r2(x: float) -> float:
    """Coordinates are written with two decimals: deterministic output, no false precision."""
    return round(float(x), 2) + 0.0
