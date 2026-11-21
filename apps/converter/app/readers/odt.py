"""ODT reader (WP-F20e), modelled on the ODS reader: zip + XML with the same limits, one flow page.

What is read: the paragraphs and headings of the body in order (also inside sections and lists), and tables with
their rows, columns, spans and cell text. A paragraph is one run anchored "p[n]"; a table is "tbl[n]" and its cells
"tbl[n]/cell[r,c]", as the DOCX reader does. Not read: styles (bold and size stay unknown), borders, text frames and
pictures, footnotes. Repeated empty cells and rows (an office suite writes them for blank space) only move the
position; repeats with content are expanded once per repeat and counted against ReadOptions.max_cells before the
first copy is made. The package is opened by `_zip` (the part limits of ODS and DOCX; XML with a document type or
entity declarations is refused).
"""
from __future__ import annotations

from lxml import etree

from . import register
from . import _zip
from ._base import Ids, ReaderError, ReadOptions, ReadResult
from app.model.common import Warning
from app.model.page import Cell, Page, Run, Table

from .ods import NS, T, TX

_TEXT_MIME = b"application/vnd.oasis.opendocument.text"
_SKIP = (TX + "note", TX + "bookmark", TX + "bookmark-start", TX + "bookmark-end")
_PARA = (TX + "p", TX + "h")
MAX_DEPTH = 40


def _local(el: etree._Element) -> str:
    return etree.QName(el).localname if isinstance(el.tag, str) else ""


def _ptext(p: etree._Element) -> str:
    out: list[str] = []

    def walk(node: etree._Element) -> None:
        if node.text:
            out.append(node.text)
        for ch in node:
            tag = ch.tag if isinstance(ch.tag, str) else ""
            if tag == TX + "s":
                try:
                    out.append(" " * min(int(ch.get(TX + "c", "1")), 1000))
                except ValueError:
                    out.append(" ")
            elif tag == TX + "tab":
                out.append("\t")
            elif tag == TX + "line-break":
                out.append("\n")
            elif tag.startswith(TX) and tag not in _SKIP:
                walk(ch)
            if ch.tail:
                out.append(ch.tail)

    walk(p)
    return "".join(out).strip()


def _count(el: etree._Element, attr: str) -> int:
    try:
        return max(1, min(int(el.get(T + attr, "1")), 1_048_576))
    except ValueError:
        return 1


class _Reader:
    def __init__(self, options: ReadOptions) -> None:
        self.options = options
        self.ids = Ids()
        self.runs: list[Run] = []
        self.tables: list[Table] = []
        self.warnings: list[Warning] = []
        self.p = 0
        self.t = 0
        self.budget = options.max_cells

    def run(self, text: str, anchor: str) -> str | None:
        if not text:
            return None
        rid = self.ids.next("r")
        self.runs.append(Run(id=rid, text=text, anchor=anchor))
        return rid

    def blocks(self, container: etree._Element, depth: int = 0) -> None:
        if depth > MAX_DEPTH:
            raise ReaderError("UNREADABLE", "the document nests deeper than the reader follows")
        for el in container:
            tag = el.tag if isinstance(el.tag, str) else ""
            if tag in _PARA:
                self.run(_ptext(el), f"p[{self.p}]")
                self.p += 1
            elif tag == T + "table":
                self.table(el, depth)
            elif tag in (TX + "section", TX + "list", TX + "list-item", TX + "list-header", TX + "index-body",
                         TX + "table-of-content", TX + "alphabetical-index", TX + "numbered-paragraph"):
                self.blocks(el, depth + 1)
            elif tag.startswith(TX + "index") or tag.endswith("-index-body"):
                self.blocks(el, depth + 1)

    def table(self, tbl: etree._Element, depth: int) -> None:
        anchor = f"tbl[{self.t}]"
        self.t += 1
        cells: list[Cell] = []
        r = 0
        for row in self._rows(tbl):
            rep = _count(row, "number-rows-repeated")
            has = any(_text_of(c) for c in row if _local(c) == "table-cell")
            copies = rep if has else 1
            if copies > 1:
                self._spend(copies * max(1, len(row)))
            for k in range(copies):
                c = 0
                for cell in row:
                    name = _local(cell)
                    if name not in ("table-cell", "covered-table-cell"):
                        continue
                    crep = _count(cell, "number-columns-repeated")
                    if name == "covered-table-cell":
                        c += crep
                        continue
                    rs, cs = _count(cell, "number-rows-spanned"), _count(cell, "number-columns-spanned")
                    texts = _text_of(cell)
                    ncopies = crep if texts else 1
                    if ncopies > 1:
                        self._spend(ncopies)
                    for j in range(ncopies):
                        if texts:
                            self._spend(1)
                            base = f"{anchor}/cell[{r},{c + j * cs}]"
                            rids = [x for x in (self.run(t, f"{base}/p[{i}]") for i, t in enumerate(texts)) if x]
                            cells.append(Cell(r=r, c=c + j * cs, rs=rs, cs=cs, anchor=base, runs=rids))
                    c += crep * cs
                r += 1
        if cells:
            self.tables.append(Table(id=self.ids.next("t"), anchor=anchor, cells=cells))

    def _rows(self, node: etree._Element):
        for ch in node:
            n = _local(ch)
            if n == "table-row":
                yield ch
            elif n in ("table-header-rows", "table-row-group", "table-rows"):
                yield from self._rows(ch)

    def _spend(self, n: int) -> None:
        self.budget -= n
        if self.budget < 0:
            raise ReaderError("TOO_LARGE", f"the tables expand to more than {self.options.max_cells} cells")


def _text_of(cell: etree._Element) -> list[str]:
    """Texts of the paragraphs of a cell (lists and sections inside it included), empty ones left out."""
    out: list[str] = []
    for p in cell.iter(*_PARA):
        t = _ptext(p)
        if t:
            out.append(t)
    return out


@register("odt")
def read(data: bytes, options: ReadOptions) -> ReadResult:
    z = _zip.open_package(data, "an ODT document")
    mime = _zip.part_bytes(z, "mimetype", options)
    if mime is None or mime.strip() != _TEXT_MIME:
        raise ReaderError("UNREADABLE", "the package is not an ODT text document")
    root = _zip.part(z, "content.xml", options)
    if root is None:
        raise ReaderError("UNREADABLE", "the package has no content.xml")
    body = root.find("office:body/office:text", NS)
    if body is None:
        raise ReaderError("UNREADABLE", "the document has no text body")
    rd = _Reader(options)
    rd.blocks(body)
    page = Page(number=1, origin="flow", runs=rd.runs, tables=rd.tables)
    return ReadResult(reader="odt", pages=[page], warnings=rd.warnings)
