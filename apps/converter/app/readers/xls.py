"""XLS reader (WP-F20f, D24): the old binary workbook (BIFF5 to BIFF8) through `xlrd` 2.0.2 (BSD-3-Clause).

The same model as the XLSX reader: one sheet is one page of origin "flow"; the grid rules are in _sheet.py. What is
read: sheets in order with their state (hidden and very hidden are read and reported), cell values (text, numbers as
written in their shortest form, booleans, error codes), the bold and size of the cell's font, the four borders of the
cell's style, merged ranges, row heights, column widths and hidden rows and columns. `formatting_info=True` gives
the styles; where xlrd cannot supply them (BIFF5 and older) the workbook is read again without them, with a warning.
Not read: data-validation lists (xlrd does not expose them), formulas (the stored result is the value), macros,
pictures, charts. Number formats are not applied, as in the XLSX reader. A password-protected workbook is refused as
ENCRYPTED (xlrd does not decrypt).
"""
from __future__ import annotations

import io

import xlrd

from app.model.common import Warning

from . import register
from ._base import Ids, ReaderError, ReadOptions, ReadResult
from ._sheet import MAX_COL, MAX_ROW, Sheet, Text, build_page
from .xlsx import DEFAULT_COL_CHARS, PT_PER_CHAR, _number

_SIDES = (("t", "top_line_style"), ("r", "right_line_style"), ("b", "bottom_line_style"), ("l", "left_line_style"))


def _open(data: bytes, styles: bool) -> xlrd.Book:
    return xlrd.open_workbook(file_contents=data, formatting_info=styles, on_demand=False, logfile=io.StringIO())


def _value(ctype: int, v: object) -> str:
    if ctype == xlrd.XL_CELL_TEXT:
        return str(v)
    if ctype in (xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_DATE):   # a date is a number of days; formats are not applied
        return _number(repr(float(v))) if isinstance(v, (int, float)) else ""
    if ctype == xlrd.XL_CELL_BOOLEAN:
        return "TRUE" if v else "FALSE"
    if ctype == xlrd.XL_CELL_ERROR:
        try:
            return xlrd.error_text_from_code[int(v)]
        except (KeyError, ValueError, TypeError):
            return ""
    return ""


def read_workbook(data: bytes, options: ReadOptions) -> tuple[list[Sheet], list[Warning]]:
    warnings: list[Warning] = []
    styled = True
    try:
        try:
            book = _open(data, True)
        except NotImplementedError:   # formatting_info is not implemented for the oldest BIFF versions
            styled = False
            book = _open(data, False)
            warnings.append(Warning(code="UNREADABLE_PART",
                                    detail="the workbook is in an old format whose fonts and borders are not read"))
    except xlrd.XLRDError as exc:
        if "crypt" in str(exc).lower() or "password" in str(exc).lower():
            raise ReaderError("ENCRYPTED", "the workbook is password-protected") from None
        raise ReaderError("UNREADABLE", "the file is not a workbook the reader can follow") from None
    if book.nsheets > options.max_pages:
        raise ReaderError("TOO_LARGE", f"{book.nsheets} sheets, the limit is {options.max_pages}")
    sheets: list[Sheet] = []
    budget = options.max_cells
    for i in range(book.nsheets):
        xs = book.sheet_by_index(i)
        sheet = Sheet(name=xs.name or f"Sheet{i + 1}", hidden=xs.visibility != 0, default_col=DEFAULT_COL_CHARS * PT_PER_CHAR)
        sheets.append(sheet)
        budget = _read_sheet(book, xs, sheet, styled, budget)
    return sheets, warnings


def _read_sheet(book: xlrd.Book, xs: xlrd.sheet.Sheet, sheet: Sheet, styled: bool, budget: int) -> int:
    for r in range(min(xs.nrows, MAX_ROW)):
        n = min(xs.row_len(r), MAX_COL)
        budget -= n
        if budget < 0:
            raise ReaderError("TOO_LARGE", "the workbook holds more cells than the reader may expand")
        types, values = xs.row_types(r, 0, n), xs.row_values(r, 0, n)
        for c in range(n):
            bold, size, sides = False, None, ""
            if styled:
                try:
                    xf = book.xf_list[xs.cell_xf_index(r, c)]
                    font = book.font_list[xf.font_index]
                    bold = bool(font.bold) or font.weight >= 700
                    size = font.height / 20 if font.height else None
                    sides = "".join(k for k, attr in _SIDES if getattr(xf.border, attr, 0))
                except (IndexError, AttributeError):
                    pass
            if sides:
                sheet.borders[(r, c)] = sides
            text = _value(types[c], values[c])
            if text.strip():
                sheet.texts[(r, c)] = Text(text=text, bold=bold, size=size)
    if styled:
        for rlo, rhi, clo, chi in xs.merged_cells:   # upper bounds are exclusive in xlrd
            sheet.merges.append((rlo, clo, rhi - 1, chi - 1))
        for r, info in xs.rowinfo_map.items():
            if info.hidden:
                sheet.rows[r] = 0.0
            elif info.height:
                sheet.rows[r] = info.height / 20
        if xs.default_row_height:
            sheet.default_row = xs.default_row_height / 20
        if xs.defcolwidth:
            sheet.default_col = xs.defcolwidth * PT_PER_CHAR
        for c in sorted(xs.colinfo_map):
            info = xs.colinfo_map[c]
            width = 0.0 if info.hidden else (info.width / 256) * PT_PER_CHAR
            sheet.cols.append((c, min(c, MAX_COL - 1), width))
    return budget


@register("xls")
def read(data: bytes, options: ReadOptions) -> ReadResult:
    sheets, warnings = read_workbook(data, options)
    ids = Ids()
    pages = [build_page(i, s, ids, warnings) for i, s in enumerate(sheets, 1)]
    return ReadResult(reader="xls", pages=pages, warnings=warnings)
