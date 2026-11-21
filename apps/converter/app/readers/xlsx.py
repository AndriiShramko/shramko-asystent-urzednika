"""XLSX reader (design 6.2): own reader on zipfile + lxml; one sheet is one page of origin "flow".

What is read: the sheets in workbook order with their state (hidden and very hidden sheets are read and
reported), cell values (shared, inline, formula results, numbers as written), the bold and size of the cell's
font, the four borders of the cell's style, merged ranges, row heights, column widths, hidden rows and columns,
and data-validation lists (classic and the Excel 2010 extension) as choice widgets. The grid rules are in
_sheet.py. Number formats are not applied: a number is written as stored, shortest form ("1", "0.5").
Column widths: Excel stores characters of the default font's widest digit, padding included; we write
width x 7 px x 0.75 pt (Calibri 11), an approximation the finder may use for proportions only.
"""
from __future__ import annotations

import re

from lxml import etree

from app.model.common import Warning

from . import register
from . import _zip
from ._base import Ids, ReaderError, ReadOptions, ReadResult
from ._sheet import MAX_COL, Sheet, Text, Validation, build_page, parse_a1, parse_range

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_X14 = "http://schemas.microsoft.com/office/spreadsheetml/2009/9/main"
NS_XM = "http://schemas.microsoft.com/office/excel/2006/main"
M = "{%s}" % NS_MAIN
PT_PER_CHAR = 7 * 0.75
DEFAULT_COL_CHARS = 8.43 + 5 / 7   # Excel's default column: 64 px


def _f(v: str | None, default: float | None = None) -> float | None:
    try:
        x = float(v) if v is not None else default
    except ValueError:
        return default
    return x if x is None or x == x else default


def _on(el: etree._Element | None) -> bool:
    return el is not None and el.get("val", "1").lower() not in ("0", "false")


def _number(v: str) -> str:
    x = _f(v)
    if x is None:
        return v
    if x == int(x) and abs(x) < 1e15:
        return str(int(x))
    return f"{x:.15g}"


class _Styles:
    def __init__(self, root: etree._Element | None):
        self.fonts: list[tuple[bool, float | None]] = []
        self.borders: list[str] = []
        self.xfs: list[tuple[int, int]] = []
        if root is None:
            return
        for font in root.iterfind(f"{M}fonts/{M}font"):
            sz = font.find(f"{M}sz")
            self.fonts.append((_on(font.find(f"{M}b")), _f(sz.get("val")) if sz is not None else None))
        for b in root.iterfind(f"{M}borders/{M}border"):
            sides = ""
            for tag, s in (("top", "t"), ("right", "r"), ("bottom", "b"), ("left", "l")):
                el = b.find(M + tag)
                if el is not None and el.get("style") not in (None, "", "none"):
                    sides += s
            self.borders.append(sides)
        for xf in root.iterfind(f"{M}cellXfs/{M}xf"):
            self.xfs.append((int(xf.get("fontId", "0") or 0), int(xf.get("borderId", "0") or 0)))

    def of(self, s: str | None) -> tuple[bool, float | None, str]:
        try:
            font_id, border_id = self.xfs[int(s or 0)]
        except (ValueError, IndexError):
            return False, None, ""
        bold, size = self.fonts[font_id] if 0 <= font_id < len(self.fonts) else (False, None)
        sides = self.borders[border_id] if 0 <= border_id < len(self.borders) else ""
        return bold, size, sides


def _text_of(si: etree._Element) -> str:
    """Text of a shared string or an inline string: every t, rich runs included, phonetic runs left out."""
    return "".join(t.text or "" for t in si.iter(f"{M}t") if t.getparent().tag != f"{M}rPh")


def _rels(z, path: str, options: ReadOptions) -> dict[str, str]:
    folder, _, name = path.rpartition("/")
    root = _zip.part(z, f"{folder}/_rels/{name}.rels" if folder else f"_rels/{name}.rels", options)
    if root is None:
        return {}
    return {r.get("Id", ""): _zip.join(folder, r.get("Target", ""))
            for r in root.iter("{%s}Relationship" % NS_PKG_REL) if r.get("TargetMode") != "External"}


def _workbook_path(z, options: ReadOptions) -> str:
    root = _zip.part(z, "_rels/.rels", options)
    if root is not None:
        for r in root.iter("{%s}Relationship" % NS_PKG_REL):
            if r.get("Type", "").endswith("/officeDocument"):
                return _zip.join("", r.get("Target", ""))
    return "xl/workbook.xml"


_QUOTED = re.compile(r'^"(.*)"$', re.S)


def _split_sheet_ref(formula: str, here: str) -> tuple[str, str] | None:
    """"'Lista 1'!$A$1:$A$3" -> ("Lista 1", "$A$1:$A$3"); "$A$1:$A$3" -> (here, ...)."""
    f = formula.strip().lstrip("=")
    if "!" in f:
        name, _, ref = f.rpartition("!")
        if name.startswith("'") and name.endswith("'"):
            name = name[1:-1].replace("''", "'")
        return name, ref
    return here, f


def read_workbook(data: bytes, options: ReadOptions) -> tuple[list[Sheet], list[Warning]]:
    z = _zip.open_package(data, "an XLSX workbook")
    warnings: list[Warning] = []
    with z:
        wb_path = _workbook_path(z, options)
        wb = _zip.part(z, wb_path, options)
        if wb is None or wb.find(f"{M}sheets") is None:
            raise ReaderError("UNREADABLE", "the package has no workbook part with sheets, so it is not a workbook")
        rels = _rels(z, wb_path, options)
        folder = wb_path.rpartition("/")[0]
        styles = _Styles(_zip.part(z, f"{folder}/styles.xml", options))
        sst_root = _zip.part(z, f"{folder}/sharedStrings.xml", options)
        shared = [_text_of(si) for si in sst_root.iterfind(f"{M}si")] if sst_root is not None else []
        names = {d.get("name", ""): (d.text or "") for d in wb.iterfind(f"{M}definedNames/{M}definedName")
                 if d.get("localSheetId") is None}
        sheets: list[Sheet] = []
        pending: list[tuple[Sheet, Validation, str]] = []
        budget = options.max_cells
        for el in wb.iterfind(f"{M}sheets/{M}sheet"):
            name = el.get("name") or f"Sheet{len(sheets) + 1}"
            sheet = Sheet(name=name, hidden=el.get("state", "visible") in ("hidden", "veryHidden"),
                          default_col=DEFAULT_COL_CHARS * PT_PER_CHAR)
            sheets.append(sheet)
            target = rels.get(el.get("{%s}id" % NS_REL, ""))
            root = _zip.part(z, target, options) if target else None
            if root is None or root.tag != f"{M}worksheet":
                warnings.append(Warning(code="UNREADABLE_PART", page=len(sheets),
                                        detail="a sheet that is not a worksheet (a chart sheet or a missing part) is not read"))
                continue
            budget = _read_sheet(root, sheet, styles, shared, budget, pending)
    by_name = {s.name: s for s in sheets}
    for sheet, v, formula in pending:
        v.options = _list_options(formula, sheet.name, by_name, names)
    return sheets, warnings


def _read_sheet(root: etree._Element, sheet: Sheet, styles: _Styles, shared: list[str], budget: int,
                pending: list[tuple[Sheet, Validation, str]]) -> int:
    fmt = root.find(f"{M}sheetFormatPr")
    if fmt is not None:
        sheet.default_row = _f(fmt.get("defaultRowHeight"), 15.0) or 15.0
        dcw = _f(fmt.get("defaultColWidth"))
        if dcw is None and _f(fmt.get("baseColWidth")) is not None:
            dcw = (_f(fmt.get("baseColWidth")) or 8) + 5 / 7
        if dcw is not None:
            sheet.default_col = dcw * PT_PER_CHAR
    for col in root.iterfind(f"{M}cols/{M}col"):
        try:
            c0, c1 = int(col.get("min", "0")) - 1, min(int(col.get("max", "0")), MAX_COL) - 1
        except ValueError:
            continue
        if c0 < 0 or c1 < c0:
            continue
        width = 0.0 if _on_attr(col.get("hidden")) else (_f(col.get("width"), None) or 0.0) * PT_PER_CHAR
        if col.get("width") is None and not _on_attr(col.get("hidden")):
            width = sheet.default_col
        sheet.cols.append((c0, c1, width))
    next_row = 0
    for row in root.iterfind(f"{M}sheetData/{M}row"):
        r = _int(row.get("r"), next_row + 1) - 1
        next_row = r + 1
        if _on_attr(row.get("hidden")):
            sheet.rows[r] = 0.0
        elif row.get("ht") is not None and _f(row.get("ht")) is not None:
            sheet.rows[r] = max(0.0, _f(row.get("ht")) or 0.0)
        next_col = 0
        for c in row.iterfind(f"{M}c"):
            budget -= 1
            if budget < 0:
                raise ReaderError("TOO_LARGE", "the workbook holds more cells than the reader may expand")
            pos = parse_a1(c.get("r", "")) if c.get("r") else (r, next_col)
            if pos is None:
                continue
            next_col = pos[1] + 1
            bold, size, sides = styles.of(c.get("s"))
            if sides:
                sheet.borders[pos] = sides
            text = _value(c, shared)
            if text and text.strip():
                sheet.texts[pos] = Text(text=text, bold=bold, size=size)
    for mc in root.iterfind(f"{M}mergeCells/{M}mergeCell"):
        rng = parse_range(mc.get("ref", ""))
        if rng:
            sheet.merges.append(rng)
    for dv in root.iterfind(f"{M}dataValidations/{M}dataValidation"):
        f1 = dv.find(f"{M}formula1")
        _validation(sheet, dv.get("type"), dv.get("sqref", ""), f1.text if f1 is not None else None, pending)
    for dv in root.iter("{%s}dataValidation" % NS_X14):
        f1 = dv.find("{%s}formula1/{%s}f" % (NS_X14, NS_XM))
        sq = dv.find("{%s}sqref" % NS_XM)
        _validation(sheet, dv.get("type"), sq.text if sq is not None else "", f1.text if f1 is not None else None,
                    pending)
    return budget


def _int(v: str | None, default: int) -> int:
    try:
        return int(v) if v is not None else default
    except ValueError:
        return default


def _on_attr(v: str | None) -> bool:
    return v is not None and v.lower() in ("1", "true")


def _value(c: etree._Element, shared: list[str]) -> str:
    t = c.get("t", "n")
    if t == "inlineStr":
        is_ = c.find(f"{M}is")
        return _text_of(is_) if is_ is not None else ""
    v = c.find(f"{M}v")
    raw = v.text if v is not None and v.text is not None else ""
    if t == "s":
        try:
            return shared[int(raw)]
        except (ValueError, IndexError):
            return ""
    if t == "b":
        return {"1": "TRUE", "0": "FALSE"}.get(raw, raw)
    if t in ("str", "e"):
        return raw
    return _number(raw) if raw else ""


def _validation(sheet: Sheet, kind: str | None, sqref: str, formula: str | None,
                pending: list[tuple[Sheet, Validation, str]]) -> None:
    if kind != "list":
        return
    for token in (sqref or "").split():
        rng = parse_range(token)
        if rng is None:
            continue
        v = Validation(*rng, options=None)
        sheet.validations.append(v)
        if formula is not None:
            pending.append((sheet, v, formula))


def _list_options(formula: str, here: str, sheets: dict[str, Sheet], names: dict[str, str], depth: int = 0
                  ) -> list[str] | None:
    """A quoted list ("Tak,Nie"), a range of cells, or a defined name for one. Anything else: None."""
    f = formula.strip()
    m = _QUOTED.match(f)
    if m:
        return [x.strip() for x in m.group(1).replace('""', '"').split(",") if x.strip()]
    if f in names and depth < 3:
        return _list_options(names[f], here, sheets, names, depth + 1)
    split = _split_sheet_ref(f, here)
    if split is None or split[0] not in sheets:
        return None
    rng = parse_range(split[1])
    if rng is None or (rng[2] - rng[0] + 1) * (rng[3] - rng[1] + 1) > 10_000:
        return None
    src = sheets[split[0]]
    out = [src.texts[(r, c)].text.strip() for r in range(rng[0], rng[2] + 1) for c in range(rng[1], rng[3] + 1)
           if (r, c) in src.texts and src.texts[(r, c)].text.strip()]
    return out or None


@register("xlsx")
def read(data: bytes, options: ReadOptions) -> ReadResult:
    sheets, warnings = read_workbook(data, options)
    if len(sheets) > options.max_pages:
        raise ReaderError("TOO_LARGE", f"{len(sheets)} sheets, the limit is {options.max_pages}")
    ids = Ids()
    pages = [build_page(i, s, ids, warnings) for i, s in enumerate(sheets, 1)]
    return ReadResult(reader="xlsx", pages=pages, warnings=warnings)
