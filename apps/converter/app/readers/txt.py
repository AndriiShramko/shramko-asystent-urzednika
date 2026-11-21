"""TXT reader (WP-F20f, D24): a plain text file is one flow page; every non-empty line is a paragraph "p[n]".

Encodings: UTF-8 (with or without a byte-order mark), UTF-16 with a byte-order mark, then cp1250. The guard has
proved it is text (no NUL byte outside UTF-16, no control characters); this reader decodes by the same rule. A form
typed as text keeps its lines as they are: a line is not joined to the next one. Not read: nothing is skipped.
"""
from __future__ import annotations

from app.guard.checks import decode_text
from app.model.page import Page, Run

from . import register
from ._base import Ids, ReaderError, ReadOptions, ReadResult


@register("txt")
def read(data: bytes, options: ReadOptions) -> ReadResult:
    got = decode_text(data)
    if got is None:
        raise ReaderError("UNREADABLE", "the file is not plain text in a supported encoding")
    ids, runs = Ids(), []
    n = 0
    for line in got[0].replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n").split("\n"):
        text = line.strip()
        if not text:
            continue
        if n >= options.max_cells:
            raise ReaderError("TOO_LARGE", f"the text has more than {options.max_cells} lines")
        runs.append(Run(id=ids.next("r"), text=text, anchor=f"p[{n}]"))
        n += 1
    return ReadResult(reader="txt", pages=[Page(number=1, origin="flow", runs=runs)])
