"""ODS reader (design 6.2): own reader of content.xml (and styles.xml for named styles); one sheet, one page.

Repeat counts are bounded before anything is expanded. An office suite writes the unused rest of a sheet as one
row repeated about a million times and one cell repeated 1,024 or 16,384 times; such a row or cell carries no
text, no drawn border, no span and no validation, and it only moves the position: it is never expanded. A row or
cell WITH content is expanded once per repeat, and the product of the repeats is added to the cell budget
(ReadOptions.max_cells) before the first copy is made: over the budget the file is refused as TOO_LARGE. A row
with content repeated more than REPEAT_WARN times is kept and flagged (UNREADABLE_PART: the grid is uncertain).

What is read: sheets in order, hidden sheets (table:display="false") read and reported, cell text as displayed
(numbers are already formatted in the file), bold and size of the cell style, borders, spans (merged ranges),
row heights, column widths, hidden rows and columns, and content validations with a list as choice widgets.
The grid rules are in _sheet.py.
"""
from __future__ import annotations

import re

from lxml import etree

from app.model.common import Warning

from . import register
from . import _zip
from ._base import Ids, ReaderError, ReadOptions, ReadResult
from ._sheet import MAX_COL, MAX_ROW, Sheet, Text, Validation, build_page, parse_range

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    "fo": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
}
T, TX, S, FO = ("{%s}" % NS[k] for k in ("table", "text", "style", "fo"))
REPEAT_WARN = 100
_UNITS = {"pt": 1.0, "cm": 72 / 2.54, "mm": 72 / 25.4, "in": 72.0, "pc": 12.0, "px": 0.75}
_LEN = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*([a-z]+)\s*$")


def length_pt(v: str | None) -> float | None:
    m = _LEN.match(v or "")
    if not m or m.group(2) not in _UNITS:
        return None
    return float(m.group(1)) * _UNITS[m.group(2)]


def _drawn(v: str | None) -> bool:
    if not v:
        return False
    v = v.strip().lower()
    if v in ("none", "hidden") or " none" in f" {v}" or " hidden" in f" {v}":
        return False
    w = length_pt(v.split()[0]) if v.split() else None
    return w is None or w > 0


class _Styles:
    """Cell, row, column and table styles by name, parent chain followed (automatic over named over default)."""

    def __init__(self, *roots: etree._Element | None):
        self.by_name: dict[tuple[str, str], etree._Element] = {}
        self.default: dict[str, etree._Element] = {}
        for root in roots:
            if root is None:
                continue
            for st in root.iter(S + "style"):
                self.by_name.setdefault((st.get(S + "family", ""), st.get(S + "name", "")), st)
            for st in root.iter(S + "default-style"):
                self.default.setdefault(st.get(S + "family", ""), st)
        self._cell: dict[str | None, tuple[bool, float | None, str]] = {}

    def _chain(self, family: str, name: str | None):
        seen = 0
        while name and seen < 10:
            st = self.by_name.get((family, name))
            if st is None:
                break
            yield st
            name = st.get(S + "parent-style-name")
            seen += 1
        if family in self.default:
            yield self.default[family]

    def _prop(self, family: str, name: str | None, kind: str, attr: str) -> str | None:
        for st in self._chain(family, name):
            p = st.find(S + kind)
            if p is not None and p.get(attr) is not None:
                return p.get(attr)
        return None

    def cell(self, name: str | None) -> tuple[bool, float | None, str]:
        if name not in self._cell:
            bold = (self._prop("table-cell", name, "text-properties", FO + "font-weight") or "") in ("bold", "700",
                                                                                                    "800", "900")
            size = length_pt(self._prop("table-cell", name, "text-properties", FO + "font-size"))
            sides = ""
            all_ = self._prop("table-cell", name, "table-cell-properties", FO + "border")
            for side, s in (("top", "t"), ("right", "r"), ("bottom", "b"), ("left", "l")):
                one = self._prop("table-cell", name, "table-cell-properties", FO + f"border-{side}")
                if _drawn(one if one is not None else all_):
                    sides += s
            self._cell[name] = (bold, size, sides)
        return self._cell[name]

    def row_height(self, name: str | None) -> float | None:
        return length_pt(self._prop("table-row", name, "table-row-properties", S + "row-height"))

    def col_width(self, name: str | None) -> float | None:
        return length_pt(self._prop("table-column", name, "table-column-properties", S + "column-width"))

    def table_hidden(self, name: str | None) -> bool:
        return (self._prop("table", name, "table-properties", T + "display") or "true") == "false"


def _repeat(el: etree._Element, attr: str) -> int:
    try:
        return max(1, int(el.get(T + attr, "1")))
    except ValueError:
        raise ReaderError("UNREADABLE", f"a repeat count of the sheet is not a number ({attr})") from None


def _span(el: etree._Element, attr: str) -> int:
    try:
        return max(1, int(el.get(T + attr, "1")))
    except ValueError:
        return 1


def _text(el: etree._Element) -> str:
    """Displayed text of a cell: paragraphs joined by new lines; spaces, tabs and line breaks kept; notes left out."""
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
            elif tag.startswith(TX) and tag not in (TX + "note", TX + "bookmark", TX + "bookmark-start",
                                                     TX + "bookmark-end"):
                walk(ch)
            if ch.tail:
                out.append(ch.tail)

    paras = [p for p in el if isinstance(p.tag, str) and p.tag in (TX + "p", TX + "h")]
    texts = []
    for p in paras:
        out.clear()
        walk(p)
        texts.append("".join(out))
    return "\n".join(texts)


def _rows(container: etree._Element):
    """Rows in order, through row groups and header rows."""
    for el in container:
        tag = el.tag if isinstance(el.tag, str) else ""
        if tag == T + "table-row":
            yield el
        elif tag in (T + "table-row-group", T + "table-header-rows", T + "table-rows"):
            yield from _rows(el)


def _columns(container: etree._Element):
    for el in container:
        tag = el.tag if isinstance(el.tag, str) else ""
        if tag == T + "table-column":
            yield el
        elif tag in (T + "table-column-group", T + "table-header-columns", T + "table-columns"):
            yield from _columns(el)


_IN_LIST = re.compile(r"cell-content-is-in-list\s*\((.*)\)\s*$", re.S)
_ODS_REF = re.compile(r"^\[?\$?'?([^.'\]]*?)'?\.\$?([A-Z]+\$?\d+)(?::\$?'?[^.'\]]*?'?\.\$?([A-Z]+\$?\d+))?\]?$")


def _validations(root: etree._Element) -> dict[str, str]:
    """Name of a content validation -> the inside of cell-content-is-in-list(...)."""
    out: dict[str, str] = {}
    for cv in root.iter(T + "content-validation"):
        m = _IN_LIST.search(cv.get(T + "condition", ""))
        if m:
            out[cv.get(T + "name", "")] = m.group(1).strip()
    return out


def _list_options(arg: str, here: str, sheets: dict[str, Sheet]) -> list[str] | None:
    if arg.startswith('"'):
        items = re.findall(r'"((?:[^"]|"")*)"', arg)
        return [x.replace('""', '"').strip() for x in items if x.strip()] or None
    m = _ODS_REF.match(arg.strip())
    if not m:
        return None
    name = m.group(1) or here
    rng = parse_range(m.group(2).replace("$", "") + (":" + m.group(3).replace("$", "") if m.group(3) else ""))
    if name not in sheets or rng is None or (rng[2] - rng[0] + 1) * (rng[3] - rng[1] + 1) > 10_000:
        return None
    src = sheets[name]
    out = [src.texts[(r, c)].text.strip() for r in range(rng[0], rng[2] + 1) for c in range(rng[1], rng[3] + 1)
           if (r, c) in src.texts and src.texts[(r, c)].text.strip()]
    return out or None


def read_workbook(data: bytes, options: ReadOptions) -> tuple[list[Sheet], list[Warning]]:
    z = _zip.open_package(data, "an ODS spreadsheet")
    with z:
        mt = _zip.part_bytes(z, "mimetype", options)
        if mt is not None and mt.strip() != b"application/vnd.oasis.opendocument.spreadsheet":
            raise ReaderError("UNREADABLE", "the package is an OpenDocument file but not a spreadsheet")
        content = _zip.part(z, "content.xml", options)
        styles_root = _zip.part(z, "styles.xml", options)
    if content is None:
        raise ReaderError("UNREADABLE", "the package has no content.xml, so it is not an ODS spreadsheet")
    body = content.find("office:body/office:spreadsheet", NS)
    if body is None:
        raise ReaderError("UNREADABLE", "content.xml holds no spreadsheet")
    styles = _Styles(content.find("office:automatic-styles", NS), styles_root)
    rules = _validations(content)
    warnings: list[Warning] = []
    sheets: list[Sheet] = []
    pending: list[tuple[Sheet, Validation, str]] = []
    budget = options.max_cells
    for tbl in body.iterfind("table:table", NS):
        sheet = Sheet(name=tbl.get(T + "name") or f"Sheet{len(sheets) + 1}",
                      hidden=styles.table_hidden(tbl.get(T + "style-name")))
        sheets.append(sheet)
        budget = _read_table(tbl, sheet, styles, rules, budget, pending, warnings, len(sheets))
    by_name = {s.name: s for s in sheets}
    for sheet, v, arg in pending:
        v.options = _list_options(arg, sheet.name, by_name)
    return sheets, warnings


def _read_table(tbl: etree._Element, sheet: Sheet, styles: _Styles, rules: dict[str, str], budget: int,
                pending: list[tuple[Sheet, Validation, str]], warnings: list[Warning], page: int) -> int:
    col_default: list[tuple[int, int, str | None]] = []
    c = 0
    for col in _columns(tbl):
        n = _repeat(col, "number-columns-repeated")
        hidden = col.get(T + "visibility", "visible") != "visible"
        width = 0.0 if hidden else styles.col_width(col.get(T + "style-name"))
        if width is not None:
            sheet.cols.append((c, min(c + n, MAX_COL) - 1, width))
        if col.get(T + "default-cell-style-name"):
            col_default.append((c, c + n - 1, col.get(T + "default-cell-style-name")))
        c += n
        if c > MAX_COL:
            break

    def cell_style(c: int, own: str | None, row_default: str | None) -> str | None:
        if own:
            return own
        for c0, c1, name in col_default:
            if c0 <= c <= c1:
                return name
        return row_default

    r = 0
    for row in _rows(tbl):
        n = _repeat(row, "number-rows-repeated")
        if r >= MAX_ROW:
            break
        row_default = row.get(T + "default-cell-style-name")
        # One pass over the cells of the row, nothing expanded: (column, repeat, text, sides, spans, rule).
        specs: list[tuple[int, int, Text | None, str, int, int, str | None]] = []
        c = 0
        for cell in row:
            tag = cell.tag if isinstance(cell.tag, str) else ""
            if tag not in (T + "table-cell", T + "covered-table-cell"):
                continue
            k = _repeat(cell, "number-columns-repeated")
            bold, size, sides = styles.cell(cell_style(c, cell.get(T + "style-name"), row_default))
            text = _text(cell) if tag == T + "table-cell" else ""
            rs, cs = (_span(cell, "number-rows-spanned"), _span(cell, "number-columns-spanned")) \
                if tag == T + "table-cell" else (1, 1)
            rule = rules.get(cell.get(T + "content-validation-name", ""))
            if text.strip() or sides or rs > 1 or cs > 1 or rule is not None:
                specs.append((c, k, Text(text, bold, size) if text.strip() else None, sides, rs, cs, rule))
            c += k
            if c > MAX_COL:
                break
        hidden = row.get(T + "visibility", "visible") != "visible"
        height = 0.0 if hidden else styles.row_height(row.get(T + "style-name"))
        if specs:
            positions = sum(min(k, MAX_COL - c0) for c0, k, *_ in specs) * min(n, MAX_ROW - r)
            budget -= positions
            if budget < 0:
                raise ReaderError("TOO_LARGE", "the sheet repeats rows or cells with content beyond the limit of "
                                               "cells the reader may expand")
            if n > REPEAT_WARN:
                warnings.append(Warning(code="UNREADABLE_PART", page=page,
                                        detail=f"a row with content is repeated {n} times from row {r + 1}: the grid "
                                               "is uncertain, every copy is kept"))
            for i in range(min(n, MAX_ROW - r)):
                for c0, k, text, sides, rs, cs, rule in specs:
                    for j in range(min(k, MAX_COL - c0)):
                        pos = (r + i, c0 + j)
                        if text is not None:
                            sheet.texts[pos] = text
                        if sides:
                            sheet.borders[pos] = sides
                        if rs > 1 or cs > 1:
                            sheet.merges.append((pos[0], pos[1], pos[0] + rs - 1, pos[1] + cs - 1))
                        if rule is not None:
                            v = Validation(pos[0], pos[1], pos[0], pos[1], options=None)
                            sheet.validations.append(v)
                            pending.append((sheet, v, rule))
            if height is not None:
                for i in range(min(n, MAX_ROW - r)):
                    sheet.rows[r + i] = height
        elif height is not None and n <= REPEAT_WARN:
            for i in range(n):
                sheet.rows[r + i] = height
        r += n
    return budget


@register("ods")
def read(data: bytes, options: ReadOptions) -> ReadResult:
    sheets, warnings = read_workbook(data, options)
    if len(sheets) > options.max_pages:
        raise ReaderError("TOO_LARGE", f"{len(sheets)} sheets, the limit is {options.max_pages}")
    ids = Ids()
    pages = [build_page(i, s, ids, warnings) for i, s in enumerate(sheets, 1)]
    return ReadResult(reader="ods", pages=pages, warnings=warnings)
