"""Binary Word reader (design 6.2.1): our own reader of the Word 97-2003 binary format on olefile; origin "flow".

The OLE container gives the WordDocument stream; its file information block (FIB) names the table stream
(0Table or 1Table) and in it the piece table (Clx), which gives the text, piece by piece, as 8-bit code page
1252 or UTF-16. Read: the main story, then the text-box story. Kept marks: paragraph end, cell end, row end, page
break, tab, line break. Paragraph properties (the PAPX pages, a huge PAPX in the Data stream included) tell a
cell end from a row end and a table paragraph from a body one. Character properties (CHPX pages) give direct bold,
direct size and inserted symbols (sprmCSymbol; boxes of Wingdings become Unicode boxes, an unknown symbol is
U+FFFD, never the placeholder "(" the file stores). Fields: the instruction between field-begin and separator is
not text; FORMTEXT, FORMCHECKBOX and FORMDROPDOWN become widgets (a check box is written as a box); results are
kept as text. A tab whose tab stop (the paragraph's own sprmPChgTabsPapx or sprmPChgTabs) has a leader is written
as LEADER_LEN leader characters, as the docx reader writes it.

Output: one run per paragraph, anchored "p[n]" (n-th body paragraph), "tbl[m]/cell[r,c]/p[k]" (r-th row, c-th
cell of that row: the cell's ordinal, not a grid column), "txbx[j]/p[k]" (text box j of the story). Pages end at
page breaks only (the file does not record where Word broke pages). Nothing is placed: no widths, no merges, no
borders, no positions of text boxes; each such gap is one UNREADABLE_PART warning, so the finder knows the
grid is a flow. Encrypted and obfuscated files are ENCRYPTED; Word 6/95 files and broken piece tables are
UNREADABLE with the reason.
"""
from __future__ import annotations

import bisect
import io
import struct
from dataclasses import dataclass, field

import olefile

from app.model.common import Warning
from app.model.page import Cell, Page, Run, Table, Widget

from . import register
from ._base import Ids, ReaderError, ReadOptions, ReadResult

WORD_IDENT = 0xA5EC
NFIB_WORD97 = 0x00C1
F_WHICH_TBL, F_ENCRYPTED, F_OBFUSCATED = 0x0200, 0x0100, 0x8000
# fibRgFcLcb97 indices (MS-DOC 2.5.6)
FC_PLCF_BTE_CHPX, FC_PLCF_BTE_PAPX, FC_STTBF_FFN, FC_CLX, FC_PLCF_TXBX_TXT = 12, 13, 15, 33, 56
# sprms
SPRM_P_IN_TABLE, SPRM_P_TTP, SPRM_P_ITAP, SPRM_P_INNER_CELL, SPRM_P_INNER_TTP, SPRM_P_HUGE = (
    0x2416, 0x2417, 0x6649, 0x244B, 0x244C, 0x6646)
SPRM_C_BOLD, SPRM_C_HPS, SPRM_C_SYMBOL = 0x0835, 0x4A43, 0x6A09
SPRM_C_RG_FTC = (0x4A4F, 0x4A50, 0x4A51)   # sprmCRgFtc0, 1, 2: the run's ASCII, East Asian and other font
SPRM_T_DEF_TABLE, SPRM_P_CHG_TABS, SPRM_P_CHG_TABS_PAPX = 0xD608, 0xC615, 0xC60D
# TBD.tlc (MS-DOC 2.9.329): the leader of a tab stop, written as LEADER_LEN characters like the docx reader does
_TAB_LEADERS = {1: ".", 2: "-", 3: "_", 4: "_", 5: "·"}
TBD_JC_BAR = 4   # a bar tab draws a vertical line and takes no tab character
LEADER_LEN = 10
CHECK_OFF = "☐"
UNKNOWN_SYMBOL = "�"
_SYMBOLS = {
    "wingdings": {0x6F: "□", 0x71: "❑", 0x72: "❒", 0xA8: "□", 0x6E: "■",
                  0xFE: "☑", 0xFD: "☒", 0x78: "☒", 0xA1: "○", 0x6C: "●", 0x9F: "•"},
    "wingdings 2": {0xA3: "□", 0x2A: "□", 0x52: "☑", 0x54: "☒", 0x53: "☒", 0x51: "☒"},
    "symbol": {0xB7: "•"},
}
_DROP = {0x01, 0x02, 0x03, 0x04, 0x05, 0x08, 0x1F}  # picture, note marks, separators, drawn object, soft hyphen
_WIDGETS = {"FORMTEXT": "text", "FORMCHECKBOX": "checkbox", "FORMDROPDOWN": "choice"}


def _u16(b: bytes, o: int) -> int:
    return struct.unpack_from("<H", b, o)[0]


def _u32(b: bytes, o: int) -> int:
    return struct.unpack_from("<I", b, o)[0]


@dataclass
class _Fib:
    flags: int
    lw: tuple[int, ...]
    fclcb: list[tuple[int, int]]

    def pair(self, i: int) -> tuple[int, int]:
        return self.fclcb[i] if i < len(self.fclcb) else (0, 0)

    def ccp(self, i: int) -> int:  # fibRgLw97: 3 text, 4 ftn, 5 hdd, 6 mcr, 7 atn, 8 edn, 9 txbx, 10 hdrtxbx
        return max(0, self.lw[i]) if i < len(self.lw) else 0


def parse_fib(wd: bytes) -> _Fib:
    if len(wd) < 34 or _u16(wd, 0) != WORD_IDENT:
        raise ReaderError("UNREADABLE", "the WordDocument stream does not start with a Word file information block")
    flags = _u16(wd, 0x0A)
    if flags & (F_ENCRYPTED | F_OBFUSCATED):
        raise ReaderError("ENCRYPTED", "the Word document is encrypted or obfuscated")
    if _u16(wd, 2) < NFIB_WORD97:
        raise ReaderError("UNREADABLE", "a Word 6 or Word 95 binary document; only Word 97 and later are read")
    try:
        pos = 32
        csw = _u16(wd, pos)
        pos += 2 + 2 * csw
        cslw = _u16(wd, pos)
        lw = struct.unpack_from(f"<{cslw}i", wd, pos + 2)
        pos += 2 + 4 * cslw
        cb = _u16(wd, pos)
        fclcb = [struct.unpack_from("<II", wd, pos + 2 + 8 * i) for i in range(cb)]
    except struct.error:
        raise ReaderError("UNREADABLE", "the file information block of the Word document is cut short") from None
    return _Fib(flags, lw, fclcb)


@dataclass
class _Piece:
    cp0: int
    cp1: int
    fc: int          # byte offset in the WordDocument stream of the first character
    wide: bool       # UTF-16 (2 bytes per character) or 8-bit code page 1252


def parse_clx(clx: bytes, stream_len: int) -> list[_Piece]:
    """Clx (MS-DOC 2.9.38): Prc records (0x01), then one Pcdt (0x02) holding the PlcPcd."""
    i = 0
    try:
        while i < len(clx) and clx[i] == 0x01:
            cb = struct.unpack_from("<h", clx, i + 1)[0]
            if cb < 0:   # a negative length would stand still or go back: an endless loop on a hostile file
                raise ReaderError("UNREADABLE", "the piece table of the Word document is missing or broken")
            i += 3 + cb
        if i >= len(clx) or clx[i] != 0x02:
            raise ReaderError("UNREADABLE", "the piece table of the Word document is missing or broken")
        lcb = _u32(clx, i + 1)
        plc = clx[i + 5:i + 5 + lcb]
        n = (len(plc) - 4) // 12
        if n < 1 or len(plc) < 4 * (n + 1) + 8 * n:
            raise ReaderError("UNREADABLE", "the piece table of the Word document is empty or cut short")
        cps = struct.unpack_from(f"<{n + 1}I", plc, 0)
        pieces = []
        for k in range(n):
            raw = _u32(plc, 4 * (n + 1) + 8 * k + 2)
            wide = not raw & 0x40000000
            fc = raw & 0x3FFFFFFF if wide else (raw & 0x3FFFFFFF) // 2
            cp0, cp1 = cps[k], cps[k + 1]
            if cp1 < cp0 or fc + (cp1 - cp0) * (2 if wide else 1) > stream_len:
                raise ReaderError("UNREADABLE", "the piece table points outside the Word document stream")
            pieces.append(_Piece(cp0, cp1, fc, wide))
    except struct.error:
        raise ReaderError("UNREADABLE", "the piece table of the Word document is cut short") from None
    return pieces


def _operand_len(sprm: int, g: bytes, i: int) -> int | None:
    spra = sprm >> 13
    if spra in (0, 1):
        return 1
    if spra in (2, 4, 5):
        return 2
    if spra == 3:
        return 4
    if spra == 7:
        return 3
    if i >= len(g):
        return None
    if sprm == SPRM_T_DEF_TABLE:
        return 2 + _u16(g, i) - 1 if i + 2 <= len(g) else None
    if sprm == SPRM_P_CHG_TABS and g[i] == 255:
        return None  # a long tab change: the rest of this property list is not read
    return 1 + g[i]


def parse_sprms(g: bytes) -> dict[int, bytes]:
    """A grpprl -> {sprm: operand}; the last of a repeated sprm wins; a broken tail is dropped."""
    out: dict[int, bytes] = {}
    i = 0
    while i + 2 <= len(g):
        sprm = _u16(g, i)
        n = _operand_len(sprm, g, i + 2)
        if n is None or i + 2 + n > len(g):
            break
        out[sprm] = g[i + 2:i + 2 + n]
        i += 2 + n
    return out


def tab_stops(props: dict[int, bytes]) -> list[tuple[int, int]]:
    """(position in twips, leader code) of the tab stops a paragraph's own properties set, by position:
    sprmPChgTabsPapx (PChgTabsPapxOperand) and sprmPChgTabs (whose delete list also carries rgdxaClose).
    Tab stops of the paragraph style are not read (the style sheet is not parsed)."""
    stops: dict[int, int] = {}
    for sprm_code in (SPRM_P_CHG_TABS_PAPX, SPRM_P_CHG_TABS):
        g = props.get(sprm_code)
        if not g:
            continue
        try:
            ndel = g[1]
            dels = struct.unpack_from(f"<{ndel}h", g, 2)
            i = 2 + 2 * ndel + (2 * ndel if sprm_code == SPRM_P_CHG_TABS else 0)
            nadd = g[i]
            pos = struct.unpack_from(f"<{nadd}h", g, i + 1)
            tbd = g[i + 1 + 2 * nadd:i + 1 + 3 * nadd]
        except (IndexError, struct.error):
            continue
        for d in dels:
            stops.pop(d, None)
        for p, t in zip(pos, tbd):
            if t & 7 != TBD_JC_BAR:
                stops[p] = (t >> 3) & 7
    return sorted(stops.items())


def with_leaders(text: str, stops: list[tuple[int, int]]) -> str:
    """The n-th tab of the paragraph goes to its n-th tab stop (as in the docx reader); a stop with a leader makes
    the tab LEADER_LEN leader characters, the paper's place to write."""
    if "\t" not in text or not any(t in _TAB_LEADERS for _p, t in stops):
        return text
    parts = text.split("\t")
    out = [parts[0]]
    for n, part in enumerate(parts[1:]):
        lead = _TAB_LEADERS.get(stops[n][1]) if n < len(stops) else None
        out.append(lead * LEADER_LEN if lead else "\t")
        out.append(part)
    return "".join(out)


class _Props:
    """FC ranges of the WordDocument stream -> sprms, from the FKP pages a PlcfBte names (PAPX or CHPX)."""

    def __init__(self, wd: bytes, table: bytes, fc: int, lcb: int, papx: bool, data: bytes = b""):
        self.starts: list[int] = []
        self.runs: list[tuple[int, int, dict[int, bytes]]] = []
        plc = table[fc:fc + lcb] if lcb else b""
        n = (len(plc) - 4) // 8 if len(plc) >= 12 else 0
        found = []
        for k in range(n):
            pn = _u32(plc, 4 * (n + 1) + 4 * k) & 0x3FFFFF
            page = wd[pn * 512:(pn + 1) * 512]
            if len(page) < 512:
                continue
            crun = page[511]
            if 4 * (crun + 1) + (13 if papx else 1) * crun > 511:
                continue
            rgfc = struct.unpack_from(f"<{crun + 1}I", page, 0)
            for i in range(crun):
                off = 2 * page[4 * (crun + 1) + (13 * i if papx else i)]
                grp = b""
                if off:
                    if papx:
                        cb = page[off]
                        grp = page[off + 2:off + 2 + 2 * page[off + 1]] if cb == 0 else page[off + 1:off + 2 * cb]
                        grp = grp[2:]  # istd
                    else:
                        grp = page[off + 1:off + 1 + page[off]]
                sprms = parse_sprms(grp)
                if papx and SPRM_P_HUGE in sprms and data:
                    at = _u32(sprms[SPRM_P_HUGE], 0)
                    if at + 2 <= len(data):
                        sprms.update(parse_sprms(data[at + 2:at + 2 + _u16(data, at)]))
                found.append((rgfc[i], rgfc[i + 1], sprms))
        found.sort(key=lambda x: x[0])
        self.runs = found
        self.starts = [x[0] for x in found]
        self.present = bool(found)

    def at(self, fc: int) -> dict[int, bytes]:
        i = bisect.bisect_right(self.starts, fc) - 1
        if i >= 0 and self.runs[i][0] <= fc < self.runs[i][1]:
            return self.runs[i][2]
        return {}


def _fonts(table: bytes, fc: int, lcb: int) -> list[str]:
    """SttbfFfn (MS-DOC 2.9.268): font names by index, lower case; [] when it cannot be read."""
    out: list[str] = []
    try:
        b = table[fc:fc + lcb]
        count, i = _u16(b, 0), 4
        for _ in range(count):
            size = b[i]
            ffn = b[i + 1:i + 1 + size]
            name = ffn[39:].decode("utf-16-le", "replace").split("\0", 1)[0] if len(ffn) > 39 else ""
            out.append(name.lower())
            i += 1 + size
    except (IndexError, struct.error):
        return out
    return out


def _symbol(font: str, code: int) -> str:
    font = font.replace(" ", "")   # "Wingdings2" and "Wingdings 2" are one font
    table = next((v for k, v in sorted(_SYMBOLS.items(), key=lambda kv: -len(kv[0]))
                  if font.startswith(k.replace(" ", ""))), None)
    return (table or {}).get(code & 0xFF, UNKNOWN_SYMBOL)


def _symbol_font(fonts: list[str], props: dict[int, bytes]) -> str | None:
    """The symbol font of a character typed in a symbol font (U+F0xx without sprmCSymbol): the first of the run's
    three fonts (sprmCRgFtc0, 1, 2) that has a symbol table; None when none has."""
    for code in SPRM_C_RG_FTC:
        g = props.get(code, b"")
        ftc = struct.unpack_from("<H", g, 0)[0] if len(g) >= 2 else len(fonts)
        if ftc < len(fonts) and any(fonts[ftc].replace(" ", "").startswith(k.replace(" ", "")) for k in _SYMBOLS):
            return fonts[ftc]
    return None


@dataclass
class _Char:
    ch: str
    fc: int


def story(wd: bytes, pieces: list[_Piece], cp0: int, cp1: int) -> list[_Char]:
    out: list[_Char] = []
    for p in pieces:
        a, b = max(cp0, p.cp0), min(cp1, p.cp1)
        if a >= b:
            continue
        if p.wide:
            start = p.fc + 2 * (a - p.cp0)
            text = wd[start:start + 2 * (b - a)].decode("utf-16-le", "replace")
            out.extend(_Char(ch, start + 2 * i) for i, ch in enumerate(text))
        else:
            start = p.fc + (a - p.cp0)
            text = wd[start:start + (b - a)].decode("cp1252", "replace")
            out.extend(_Char(ch, start + i) for i, ch in enumerate(text))
    return out


@dataclass
class _Field:
    instr: list[str] = field(default_factory=list)
    sep: bool = False


@dataclass
class _Out:
    ids: Ids
    page_no: int = 1
    pages: list[Page] = field(default_factory=list)
    cur: dict = field(default_factory=lambda: {"runs": [], "tables": [], "widgets": []})
    warnings: list[Warning] = field(default_factory=list)

    def new_page(self) -> None:
        if any(self.cur.values()):
            self.pages.append(Page(number=len(self.pages) + 1, origin="flow", **self.cur))
            self.cur = {"runs": [], "tables": [], "widgets": []}

    def run(self, text: str, anchor: str, bold: bool, size: float | None) -> str | None:
        text = text.strip()
        if not text:
            return None
        run, ws = Run.safe(len(self.pages) + 1, id=self.ids.next("r"), text=text, anchor=anchor, bold=bold,
                           size=size)
        self.warnings.extend(ws)
        if run is None:
            return None
        self.cur["runs"].append(run)
        return run.id

    def widget(self, kind: str, anchor: str) -> None:
        w, ws = Widget.safe(len(self.pages) + 1, id=self.ids.next("w"), kind=kind, anchor=anchor)
        self.warnings.extend(ws)
        if w is not None:
            self.cur["widgets"].append(w)


class _Reader:
    def __init__(self, papx: _Props, chpx: _Props, fonts: list[str], out: _Out):
        self.papx, self.chpx, self.fonts, self.out = papx, chpx, fonts, out
        self.tables_known = papx.present
        self.n_para = 0
        self.n_tbl = 0
        self.tbl: dict | None = None
        self.unknown_widgets = 0

    # ------------------------------------------------------------ characters
    def _char(self, c: _Char) -> tuple[str, bool | None, float | None]:
        """Text of one ordinary character and its direct bold and size (None: not declared)."""
        props = self.chpx.at(c.fc)
        ch = c.ch
        if SPRM_C_SYMBOL in props and len(props[SPRM_C_SYMBOL]) >= 4:
            ftc, xchar = struct.unpack_from("<HH", props[SPRM_C_SYMBOL], 0)
            ch = _symbol(self.fonts[ftc] if ftc < len(self.fonts) else "", xchar)
        elif 0xF000 <= ord(ch) <= 0xF0FF:  # a character typed in a symbol font: the font is one of the run's fonts
            font = _symbol_font(self.fonts, props)
            ch = _symbol(font, ord(ch)) if font is not None else UNKNOWN_SYMBOL
        elif ch == "\x1e":
            ch = "-"
        elif ch == "\x0b":
            ch = "\n"
        elif ord(ch) < 0x20 and ch != "\t":
            ch = ""
        bold = props[SPRM_C_BOLD][0] in (1, 0x81) if SPRM_C_BOLD in props else None
        size = _u16(props[SPRM_C_HPS], 0) / 2 if SPRM_C_HPS in props and len(props[SPRM_C_HPS]) >= 2 else None
        return ch, bold, size

    # ------------------------------------------------------------ the story
    def read(self, chars: list[_Char], anchor_of_body) -> None:
        buf: list[str] = []
        bolds: list[bool] = []
        sizes: list[float] = []
        widgets: list[str] = []
        fields: list[_Field] = []
        for c in chars:
            o = ord(c.ch)
            if o == 0x13:
                fields.append(_Field())
                continue
            if o == 0x14:
                if fields:
                    fields[-1].sep = True
                continue
            if o == 0x15:
                if fields:
                    f = fields.pop()
                    words = "".join(f.instr).split()
                    kind = _WIDGETS.get(words[0].upper()) if words else None
                    if kind and (not fields or fields[-1].sep):
                        widgets.append(kind)
                        if kind == "checkbox":
                            buf.append(CHECK_OFF)
                        if kind == "choice":
                            self.unknown_widgets += 1
                continue
            if fields and not fields[-1].sep:
                if o not in (0x0D, 0x07):
                    fields[-1].instr.append(c.ch)
                    continue
            if o in (0x0D, 0x07, 0x0C, 0x0E):
                self._end_paragraph(c, "".join(buf), bolds, sizes, widgets, anchor_of_body)
                buf, bolds, sizes, widgets = [], [], [], []
                if o == 0x0C:
                    self._close_table()
                    self.out.new_page()
                continue
            if o in _DROP:
                continue
            ch, bold, size = self._char(c)
            if not ch:
                continue
            buf.append(ch)
            if not ch.isspace():
                bolds.append(bool(bold))
                if size:
                    sizes.append(size)
        if "".join(buf).strip() or widgets:
            self._end_paragraph(None, "".join(buf), bolds, sizes, widgets, anchor_of_body)
        self._close_table()

    def _end_paragraph(self, mark: _Char | None, text: str, bolds: list[bool], sizes: list[float],
                       widgets: list[str], anchor_of_body) -> None:
        bold = bool(bolds) and sum(bolds) * 2 > len(bolds)
        size = max(set(sizes), key=sizes.count) if sizes else None
        props = self.papx.at(mark.fc) if mark is not None and self.tables_known else {}
        in_table = bool(props.get(SPRM_P_IN_TABLE, b"\0")[0]) or (
            SPRM_P_ITAP in props and len(props[SPRM_P_ITAP]) >= 4 and _u32(props[SPRM_P_ITAP], 0) >= 1)
        row_end = mark is not None and mark.ch == "\x07" and bool(props.get(SPRM_P_TTP, b"\0")[0])
        text = with_leaders(text, tab_stops(props))
        if not in_table:
            self._close_table()
            anchor = anchor_of_body(self.n_para)
            self.n_para += 1
            self.out.run(text, anchor, bold, size)
            for kind in widgets:
                self.out.widget(kind, anchor)
            return
        t = self._open_table()
        if row_end:
            if t["cell_runs"] or t["k"]:  # text before a row mark without its own cell mark: keep it in a cell
                self._end_cell(t)
            t["r"] += 1
            t["c"] = 0
            return
        anchor = f"tbl[{t['m']}]/cell[{t['r']},{t['c']}]/p[{t['k']}]"
        rid = self.out.run(text, anchor, bold, size)
        for kind in widgets:
            self.out.widget(kind, anchor)
        if rid:
            t["cell_runs"].append(rid)
        t["k"] += 1
        if mark is not None and mark.ch == "\x07":
            self._end_cell(t)

    def _open_table(self) -> dict:
        if self.tbl is None:
            self.tbl = {"m": self.n_tbl, "id": self.out.ids.next("t"), "r": 0, "c": 0, "k": 0, "cell_runs": [],
                        "cells": []}
            self.n_tbl += 1
        return self.tbl

    def _end_cell(self, t: dict) -> None:
        a = f"tbl[{t['m']}]/cell[{t['r']},{t['c']}]"
        t["cells"].append(Cell(r=t["r"], c=t["c"], anchor=a, runs=t["cell_runs"]))
        t["c"] += 1
        t["k"] = 0
        t["cell_runs"] = []

    def _close_table(self) -> None:
        t, self.tbl = self.tbl, None
        if t is None:
            return
        if t["cell_runs"]:
            self._end_cell(t)
        if t["cells"]:
            self.out.cur["tables"].append(Table(id=t["id"], anchor=f"tbl[{t['m']}]", cells=t["cells"]))


def _stream(ole: olefile.OleFileIO, name: str) -> bytes:
    return ole.openstream(name).read() if ole.exists(name) else b""


@register("doc")
def read(data: bytes, options: ReadOptions) -> ReadResult:
    if not olefile.isOleFile(data=data):
        raise ReaderError("UNREADABLE", "not an OLE compound file, so not a binary Word document")
    try:
        ole = olefile.OleFileIO(io.BytesIO(data))
    except (OSError, ValueError, struct.error):
        raise ReaderError("UNREADABLE", "the OLE container of the document is broken") from None
    with ole:
        if not ole.exists("WordDocument"):
            raise ReaderError("UNREADABLE", "the OLE container has no WordDocument stream, so it is not a Word file")
        sizes = [ole.get_size(n) for n in ("WordDocument", "0Table", "1Table", "Data") if ole.exists(n)]
        if any(s > options.max_part_bytes for s in sizes):
            raise ReaderError("TOO_LARGE", "a stream of the Word document is larger than the reader may load")
        wd = _stream(ole, "WordDocument")
        fib = parse_fib(wd)
        table = _stream(ole, "1Table" if fib.flags & F_WHICH_TBL else "0Table")
        data_stream = _stream(ole, "Data")
    if not table:
        raise ReaderError("UNREADABLE", "the table stream the Word document names is missing")
    fc, lcb = fib.pair(FC_CLX)
    if not lcb or fc + lcb > len(table):
        raise ReaderError("UNREADABLE", "the piece table of the Word document is missing or outside its stream")
    pieces = parse_clx(table[fc:fc + lcb], len(wd))
    papx = _Props(wd, table, *fib.pair(FC_PLCF_BTE_PAPX), papx=True, data=data_stream)
    chpx = _Props(wd, table, *fib.pair(FC_PLCF_BTE_CHPX), papx=False)
    fonts = _fonts(table, *fib.pair(FC_STTBF_FFN))

    out = _Out(Ids())
    rd = _Reader(papx, chpx, fonts, out)
    main_end = fib.ccp(3)
    rd.read(story(wd, pieces, 0, main_end), lambda n: f"p[{n}]")
    # The text-box story follows footnotes, headers, macros, comments and endnotes in the CP space.
    txbx0 = main_end + sum(fib.ccp(i) for i in (4, 5, 6, 7, 8))
    n_txbx = fib.ccp(9)
    boxes = 0
    if n_txbx:
        chars = story(wd, pieces, txbx0, txbx0 + n_txbx)
        bounds = _txbx_bounds(table, *fib.pair(FC_PLCF_TXBX_TXT))
        rd.tables_known = papx.present
        for j, (a, b) in enumerate(bounds or [(0, len(chars))]):
            part = chars[a:b]
            if any(ch.ch.strip("\r\x07\x0c ") for ch in part):
                boxes += 1
            rd.n_para = 0
            rd.read(part, lambda n, j=j: f"txbx[{j}]/p[{n}]")
    out.new_page()
    if not out.pages:
        raise ReaderError("UNREADABLE", "no text could be read from the Word document")
    warnings = out.warnings
    if not papx.present:
        warnings.append(Warning(code="UNREADABLE_PART", detail="paragraph properties of the Word document could not "
                                "be read: table cells are read as paragraphs, cell and row ends are not told apart"))
    if any(p.tables for p in out.pages):
        warnings.append(Warning(code="UNREADABLE_PART", detail="binary Word: tables are read as rows of cells in "
                                "file order; widths, merges and borders are not read (flow only)"))
    if boxes:
        warnings.append(Warning(code="UNREADABLE_PART", detail=f"binary Word: {boxes} text boxes are read in the "
                                "order of their story after the body; their place on the page is not known"))
    if rd.unknown_widgets:
        warnings.append(Warning(code="UNREADABLE_PART", detail=f"binary Word: {rd.unknown_widgets} drop-down "
                                "fields are read without their options"))
    return ReadResult(reader="doc.flow", pages=out.pages, warnings=warnings)


def _txbx_bounds(table: bytes, fc: int, lcb: int) -> list[tuple[int, int]]:
    """PlcftxbxTxt: (n+1) CPs relative to the text-box story and n FTXBXS of 22 bytes; the last box is a dummy."""
    if lcb < 4 + 4 + 22:
        return []
    n = (lcb - 4) // 26
    try:
        cps = struct.unpack_from(f"<{n + 1}I", table, fc)
    except struct.error:
        return []
    return [(cps[k], cps[k + 1]) for k in range(n) if cps[k + 1] > cps[k]]
