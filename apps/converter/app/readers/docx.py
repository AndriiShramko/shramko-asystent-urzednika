"""DOCX reader (design 6.2): own reader on zipfile + lxml, two kinds of documents.

Flow (origin "flow", reader "docx.flow"): a document of ordinary paragraphs and tables. One run per paragraph,
anchored, never placed: "p[n]" (n-th body paragraph), "tbl[m]", "tbl[m]/cell[r,c]", "tbl[m]/cell[r,c]/p[k]",
"p[n]/txbx[j]/p[k]" (text box j drawn in paragraph n), "fn[i]/p[k]" (footnote i). Pages end at explicit page
breaks, at the page breaks Word rendered last (w:lastRenderedPageBreak) and at section breaks.

Native (origin "native", reader "docx.native"): a document made of anchored text boxes (a PDF converted to Word:
sets 2 and 8 hold 130 and 1,302 of them and no body text). Each text box gives runs placed at its anchor offset,
each visible drawn shape gives a line or a rectangle. Chosen when the text inside anchored text boxes is at least
NATIVE_SHARE of all text. What cannot be placed (a position relative to a character, body text between the boxes)
is counted in an UNREADABLE_PART warning, never placed by a guess.

Text rules: tabs are "\t", a tab whose tab stop has a leader is written as LEADER_LEN leader characters, three or
more underlined blanks are written as underscores (the paper shows a line), Wingdings boxes become Unicode boxes,
an unknown symbol is U+FFFD, a legacy check box is written as a box, field codes and hidden or deleted text are
not text. Content controls and legacy form fields become widgets; a content control showing its placeholder
contributes no text.

List markers: a paragraph with w:numPr (directly or through its paragraph style) starts with the marker Word shows
for it ("1.", "a)", "2.1.", a bullet), computed from word/numbering.xml in document order (see _Numbering). A symbol
box bullet becomes the box the finder knows, any other bullet becomes "•" or "-". Paragraphs without numbering are
unchanged.
"""
from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass, field
from typing import Iterator

from lxml import etree

from app.model.common import Warning
from app.model import page as pm
from app.model.page import Cell, Line, Page, Rect, Table

from . import register
from ._base import Ids, ReaderError, ReadOptions, ReadResult, nn, r2


def Run(**kw: object) -> pm.Run:  # noqa: N802 - the model's constructor without the None arguments
    return pm.Run(**nn(**kw))


def Widget(**kw: object) -> pm.Widget:  # noqa: N802
    return pm.Widget(**nn(**kw))

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "wps": "http://schemas.microsoft.com/office/word/2010/wordprocessingShape",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "v": "urn:schemas-microsoft-com:vml",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
}
W = "{%s}" % NS["w"]
EMU = 12700.0        # EMU per point
TWIP = 20.0          # twentieths of a point
NATIVE_SHARE = 0.8   # share of the text inside anchored text boxes above which the document is read as native
LEADER_LEN = 10
LINE_MAX_THICKNESS = 3.0
PICTURE_BOX_MAX = 24.0  # a picture no larger than this both ways is drawn as a rectangle (a box glyph)
UNKNOWN_SYMBOL = "�"

# Symbol fonts: code (low byte) -> Unicode. Boxes, ticks and circles only; the rest is UNKNOWN_SYMBOL.
_SYMBOLS = {
    "wingdings": {0x6F: "□", 0x71: "❑", 0x72: "❒", 0xA8: "□", 0x6E: "■",
                  0xFE: "☑", 0xFD: "☒", 0x78: "☒", 0xA1: "○", 0x6C: "●", 0x9F: "•"},
    "wingdings 2": {0xA3: "□", 0x2A: "□", 0x52: "☑", 0x54: "☒", 0x53: "☒", 0x51: "☒"},
    "symbol": {0xB7: "•"},
}
_SYMBOL_FONTS = ("wingdings", "webdings", "symbol", "zapf dingbats")
_LEADERS = {"dot": ".", "hyphen": "-", "underscore": "_", "heavy": "_", "middleDot": "·"}
CHECK_OFF, CHECK_ON = "☐", "☒"


def _q(tag: str) -> str:
    p, local = tag.split(":")
    return "{%s}%s" % (NS[p], local)


def _local(el: etree._Element) -> str:
    return etree.QName(el).localname if isinstance(el.tag, str) else ""


def _on(el: etree._Element | None) -> bool:
    """A Word toggle property: present and not switched off."""
    return el is not None and el.get(W + "val", "true").lower() not in ("false", "0", "off", "none")


# ---------------------------------------------------------------- package


def _open(data: bytes, options: ReadOptions) -> zipfile.ZipFile:
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except (zipfile.BadZipFile, ValueError, OSError):
        raise ReaderError("UNREADABLE", "not a ZIP package, so not a DOCX file") from None
    if "word/document.xml" not in z.namelist():
        raise ReaderError("UNREADABLE", "the package has no word/document.xml, so it is not a Word document")
    return z


def _part(z: zipfile.ZipFile, name: str, options: ReadOptions) -> etree._Element | None:
    try:
        info = z.getinfo(name)
    except KeyError:
        return None
    if info.flag_bits & 0x1:
        raise ReaderError("ENCRYPTED", f"the part {name} is encrypted")
    if info.file_size > options.max_part_bytes:
        raise ReaderError("TOO_LARGE", f"the part {name} unpacks to {info.file_size} bytes")
    if info.compress_size and info.file_size / info.compress_size > options.max_ratio:
        raise ReaderError("TOO_LARGE", f"the part {name} unpacks {info.file_size // info.compress_size} times its size")
    raw = z.read(name)
    if b"<!DOCTYPE" in raw[:4096] or b"<!ENTITY" in raw:
        raise ReaderError("UNREADABLE", f"the part {name} declares a document type or entities (refused)")
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False,
                             remove_comments=True, remove_pis=True)
    try:
        return etree.fromstring(raw, parser)
    except etree.XMLSyntaxError:
        raise ReaderError("UNREADABLE", f"the part {name} is not well-formed XML") from None


# ---------------------------------------------------------------- styles


@dataclass
class _Style:
    based_on: str | None = None
    bold: bool | None = None
    size: float | None = None
    tabs: list[tuple[float, str]] = field(default_factory=list)
    borders: etree._Element | None = None


class _Styles:
    def __init__(self, root: etree._Element | None):
        self.by_id: dict[str, _Style] = {}
        self.default_size: float | None = None
        if root is None:
            return
        sz = root.find("w:docDefaults/w:rPrDefault/w:rPr/w:sz", NS)
        if sz is not None and (sz.get(W + "val") or "").isdigit():
            self.default_size = int(sz.get(W + "val")) / 2
        for st in root.findall("w:style", NS):
            sid = st.get(W + "styleId")
            if not sid:
                continue
            s = _Style()
            b = st.find("w:basedOn", NS)
            s.based_on = b.get(W + "val") if b is not None else None
            rpr = st.find("w:rPr", NS)
            if rpr is not None:
                be = rpr.find("w:b", NS)
                s.bold = _on(be) if be is not None else None
                s.size = _size(rpr)
            s.tabs = _tab_stops(st.find("w:pPr", NS))
            s.borders = st.find("w:tblPr/w:tblBorders", NS)
            self.by_id[sid] = s

    def chain(self, sid: str | None) -> Iterator[_Style]:
        seen: set[str] = set()
        while sid and sid in self.by_id and sid not in seen and len(seen) < 16:
            seen.add(sid)
            yield self.by_id[sid]
            sid = self.by_id[sid].based_on

    def bold(self, sid: str | None) -> bool:
        return next((s.bold for s in self.chain(sid) if s.bold is not None), False)

    def size(self, sid: str | None) -> float | None:
        return next((s.size for s in self.chain(sid) if s.size is not None), None)

    def tabs(self, sid: str | None) -> list[tuple[float, str]]:
        return next((s.tabs for s in self.chain(sid) if s.tabs), [])

    def borders(self, sid: str | None) -> etree._Element | None:
        return next((s.borders for s in self.chain(sid) if s.borders is not None), None)


def _size(rpr: etree._Element | None) -> float | None:
    sz = rpr.find("w:sz", NS) if rpr is not None else None
    val = sz.get(W + "val") if sz is not None else None
    try:
        return float(val) / 2 if val and float(val) > 0 else None
    except ValueError:
        return None


def _tab_stops(ppr: etree._Element | None) -> list[tuple[float, str]]:
    if ppr is None:
        return []
    stops = []
    for t in ppr.findall("w:tabs/w:tab", NS):
        if t.get(W + "val") == "clear":
            continue
        try:
            pos = float(t.get(W + "pos") or 0)
        except ValueError:
            pos = 0.0
        stops.append((pos, t.get(W + "leader") or "none"))
    return sorted(stops)


# ---------------------------------------------------------------- list numbering

LIST_BOX = "□"            # the first of the finder's BOX_CHARS (app/find/_core.py)
_BOXES = "□❑❒☐❏❐▢◻◽⬜■"
_DASHES = "-–—‐"
_MAX_LEVELS = 9


def _roman(n: int) -> str:
    if n <= 0 or n >= 4000:
        return str(n)
    out = []
    for v, s in ((1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"), (50, "l"), (40, "xl"),
                 (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")):
        while n >= v:
            out.append(s)
            n -= v
    return "".join(out)


def _letters(n: int) -> str:
    """Word's letter numbering: a..z, then aa..zz, then aaa..."""
    if n <= 0:
        return str(n)
    return chr(ord("a") + (n - 1) % 26) * ((n - 1) // 26 + 1)


def _format_number(n: int, fmt: str) -> str:
    if fmt == "lowerLetter":
        return _letters(n)
    if fmt == "upperLetter":
        return _letters(n).upper()
    if fmt == "lowerRoman":
        return _roman(n)
    if fmt == "upperRoman":
        return _roman(n).upper()
    if fmt == "decimalZero":
        return f"{n:02d}"
    if fmt == "none":
        return ""
    return str(n)   # decimal and every format we do not draw


def _bullet(text: str, font: str) -> str:
    """The bullet as the later steps know it: a box stays a box (LIST_BOX), a dash stays "-", the rest is "•"."""
    ch = text.strip()[:1]
    if not ch:
        return ""
    code = ord(ch)
    if 0xF000 <= code <= 0xF0FF or font.startswith(_SYMBOL_FONTS):
        ch = _symbol(font, code)
    if ch in _BOXES:
        return LIST_BOX
    if ch in "☑☒":
        return ch
    if ch in _DASHES:
        return "-"
    return "•"


@dataclass
class _Level:
    fmt: str = "decimal"
    text: str = "%1."
    start: int = 1
    font: str = ""


class _Numbering:
    """word/numbering.xml: w:num -> w:abstractNum -> w:lvl, and the markers of the paragraphs in document order.
    Counters run per numId and level; a deeper level restarts when a shallower one advances; w:start and
    w:lvlOverride/w:startOverride give the first value."""

    def __init__(self, root: etree._Element | None, styles_root: etree._Element | None):
        self.abstract: dict[str, dict[int, _Level]] = {}
        self.abstract_link: dict[str, str] = {}          # abstractNumId -> numbering style it links to
        self.nums: dict[str, tuple[str, dict[int, int], dict[int, _Level]]] = {}
        self.style_num: dict[str, tuple[str | None, int | None, str | None]] = {}
        if styles_root is not None:
            for st in styles_root.findall("w:style", NS):
                sid = st.get(W + "styleId")
                if not sid:
                    continue
                b = st.find("w:basedOn", NS)
                num_id, ilvl = self._num_pr(st.find("w:pPr/w:numPr", NS))
                self.style_num[sid] = (num_id, ilvl, b.get(W + "val") if b is not None else None)
        if root is None:
            return
        for an in root.findall("w:abstractNum", NS):
            aid = an.get(W + "abstractNumId") or ""
            self.abstract[aid] = {i: lv for i, lv in (self._level(el) for el in an.findall("w:lvl", NS))}
            link = _val(an, "w:numStyleLink")
            if link:
                self.abstract_link[aid] = link
        for num in root.findall("w:num", NS):
            nid = num.get(W + "numId") or ""
            aid = _val(num, "w:abstractNumId") or ""
            starts: dict[int, int] = {}
            levels: dict[int, _Level] = {}
            for ov in num.findall("w:lvlOverride", NS):
                try:
                    i = int(ov.get(W + "ilvl") or 0)
                except ValueError:
                    continue
                so = _val(ov, "w:startOverride")
                if so and so.lstrip("-").isdigit():
                    starts[i] = int(so)
                lv = ov.find("w:lvl", NS)
                if lv is not None:
                    levels[i] = self._level(lv)[1]
            self.nums[nid] = (aid, starts, levels)
        self.counters: dict[str, list[int | None]] = {}

    @staticmethod
    def _num_pr(npr: etree._Element | None) -> tuple[str | None, int | None]:
        if npr is None:
            return None, None
        nid = _val(npr, "w:numId")
        il = _val(npr, "w:ilvl")
        return nid, int(il) if il and il.isdigit() else None

    @staticmethod
    def _level(el: etree._Element) -> tuple[int, _Level]:
        il = el.get(W + "ilvl") or "0"
        lv = _Level()
        lv.fmt = _val(el, "w:numFmt") or "decimal"
        txt = el.find("w:lvlText", NS)
        lv.text = txt.get(W + "val") or "" if txt is not None else ""
        st = _val(el, "w:start")
        lv.start = int(st) if st and st.lstrip("-").isdigit() else (0 if lv.fmt == "decimalZero" else 1)
        fonts = el.find("w:rPr/w:rFonts", NS)
        if fonts is not None:
            lv.font = (fonts.get(W + "ascii") or fonts.get(W + "hAnsi") or "").lower()
        return int(il) if il.isdigit() else 0, lv

    def _levels(self, nid: str) -> tuple[dict[int, _Level], dict[int, int]] | None:
        if nid not in self.nums:
            return None
        aid, starts, overrides = self.nums[nid]
        levels = self.abstract.get(aid)
        link = self.abstract_link.get(aid)
        if link and link in self.style_num:          # a list style: its numId points to the real definition
            target = self.style_num[link][0]
            if target and target in self.nums and target != nid:
                levels = self.abstract.get(self.nums[target][0], levels)
        if levels is None:
            return None
        return {**levels, **overrides}, starts

    def _paragraph_num(self, p: etree._Element) -> tuple[str | None, int | None]:
        ppr = p.find("w:pPr", NS)
        nid, ilvl = self._num_pr(ppr.find("w:numPr", NS) if ppr is not None else None)
        sid = _val(ppr, "w:pStyle") if ppr is not None else None
        seen: set[str] = set()
        while (nid is None or ilvl is None) and sid and sid in self.style_num and sid not in seen:
            seen.add(sid)
            snid, silvl, based = self.style_num[sid]
            nid = nid if nid is not None else snid
            ilvl = ilvl if ilvl is not None else silvl
            sid = based
        return nid, ilvl

    def marker(self, p: etree._Element) -> str:
        """The marker of the next paragraph in document order ("" when it has none); advances the counters."""
        nid, ilvl = self._paragraph_num(p)
        if not nid or nid == "0":
            return ""
        ilvl = min(max(ilvl or 0, 0), _MAX_LEVELS - 1)
        found = self._levels(nid)
        if found is None:
            return ""
        levels, starts = found
        lv = levels.get(ilvl)
        if lv is None:
            return ""

        def start(i: int) -> int:
            return starts.get(i, levels[i].start if i in levels else 1)

        cnt = self.counters.setdefault(nid, [None] * _MAX_LEVELS)
        cnt[ilvl] = start(ilvl) if cnt[ilvl] is None else cnt[ilvl] + 1
        for i in range(ilvl + 1, _MAX_LEVELS):
            cnt[i] = None
        if lv.fmt == "bullet":
            return _bullet(lv.text, lv.font)

        def repl(m: re.Match) -> str:
            i = int(m.group(1)) - 1
            if not 0 <= i < _MAX_LEVELS or i > ilvl:
                return ""
            n = cnt[i] if cnt[i] is not None else start(i)
            return _format_number(n, levels[i].fmt if i in levels else "decimal")

        return re.sub(r"%([1-9])", repl, lv.text).strip()

    def markers(self, body: etree._Element) -> dict[etree._Element, str]:
        """Markers of every numbered paragraph of the body, text boxes and tables included, in document order."""
        out: dict[etree._Element, str] = {}
        for p in body.iter(W + "p"):
            if any(_local(a) == "Fallback" for a in p.iterancestors()):   # the VML copy of a text box
                continue
            m = self.marker(p)
            if m:
                out[p] = m
        return out


# ---------------------------------------------------------------- paragraphs


@dataclass
class _WidgetSpec:
    kind: str
    name: str | None = None
    max_len: int | None = None
    options: list[str] = field(default_factory=list)


@dataclass
class _Para:
    text: str = ""
    bold: bool = False
    size: float | None = None
    widgets: list[_WidgetSpec] = field(default_factory=list)
    drawings: list[etree._Element] = field(default_factory=list)  # wp:anchor, wp:inline or w:pict, in order
    footnotes: list[str] = field(default_factory=list)            # footnote ids referenced, in order
    break_before: bool = False
    break_after: bool = False


class _Reader:
    def __init__(self, styles: _Styles, footnote_order: dict[str, int]):
        self.styles = styles
        self.footnote_order = footnote_order
        self.current_note = ""
        self.markers: dict[etree._Element, str] = {}   # list markers of numbered paragraphs (_Numbering.markers)

    # -- one paragraph ------------------------------------------------------------------------------------------

    def para(self, p: etree._Element) -> _Para:
        out = _Para()
        ppr = p.find("w:pPr", NS)
        pstyle_el = ppr.find("w:pStyle", NS) if ppr is not None else None
        pstyle = pstyle_el.get(W + "val") if pstyle_el is not None else None
        tabs = _tab_stops(ppr) or self.styles.tabs(pstyle)
        if ppr is not None and _on(ppr.find("w:pageBreakBefore", NS)):
            out.break_before = True
        st = _State(pstyle=pstyle, tabs=tabs)
        self._walk(p, out, st)
        text = "".join(st.parts)
        marker = self.markers.get(p)
        out.text = f"{marker} {text}" if marker else text
        weights = [b for b, t in st.weights if t.strip()]
        out.bold = bool(weights) and all(weights)
        out.size = st.size or self.styles.size(pstyle) or self.styles.default_size
        return out

    def _walk(self, el: etree._Element, out: _Para, st: _State) -> None:
        for ch in el:
            name = _local(ch)
            ns = etree.QName(ch).namespace if isinstance(ch.tag, str) else None
            if not name:
                continue
            if ns == NS["mc"] and name == "AlternateContent":
                target = ch.find("mc:Choice", NS)
                if target is None:
                    target = ch.find("mc:Fallback", NS)
                if target is not None:
                    self._walk(target, out, st)
            elif ns != NS["w"]:
                continue
            elif name == "r":
                self._run(ch, out, st)
            elif name == "sdt":
                self._sdt(ch, out, st)
            elif name in ("hyperlink", "smartTag", "customXml", "ins", "fldSimple", "moveTo", "sdtContent", "dir",
                          "bdo"):
                self._walk(ch, out, st)
            # pPr, del, moveFrom, bookmarks, proofErr ...: no text

    def _sdt(self, sdt: etree._Element, out: _Para, st: _State) -> None:
        spec = _sdt_widget(sdt.find("w:sdtPr", NS))
        if spec is not None:
            out.widgets.append(spec)
        pr = sdt.find("w:sdtPr", NS)
        if pr is not None and pr.find("w:showingPlcHdr", NS) is not None:
            return
        content = sdt.find("w:sdtContent", NS)
        if content is not None:
            self._walk(content, out, st)

    def _run(self, r: etree._Element, out: _Para, st: _State) -> None:
        rpr = r.find("w:rPr", NS)
        if rpr is not None and (_on(rpr.find("w:vanish", NS)) or _on(rpr.find("w:specVanish", NS))):
            return
        rstyle_el = rpr.find("w:rStyle", NS) if rpr is not None else None
        rstyle = rstyle_el.get(W + "val") if rstyle_el is not None else None
        b_el = rpr.find("w:b", NS) if rpr is not None else None
        bold = _on(b_el) if b_el is not None else (self.styles.bold(rstyle) or self.styles.bold(st.pstyle))
        underlined = rpr is not None and _on(rpr.find("w:u", NS))
        fonts = rpr.find("w:rFonts", NS) if rpr is not None else None
        font = ""
        if fonts is not None:
            font = (fonts.get(W + "ascii") or fonts.get(W + "hAnsi") or fonts.get(W + "cs") or "").lower()
        size = _size(rpr) or self.styles.size(rstyle)
        for ch in r:
            name = _local(ch)
            if etree.QName(ch).namespace == NS["mc"] and name == "AlternateContent":
                choice = ch.find("mc:Choice", NS)
                target = choice if choice is not None else ch.find("mc:Fallback", NS)
                for d in (target if target is not None else []):
                    self._drawing(d, out)
                continue
            if name == "fldChar":
                st.field_char(ch)
                continue
            if name == "instrText":
                st.instr(ch.text or "")
                continue
            if name in ("drawing", "pict", "object"):
                self._drawing(ch, out)
                continue
            if name == "lastRenderedPageBreak" or (name == "br" and ch.get(W + "type") == "page"):
                if "".join(st.parts).strip():
                    out.break_after = True
                else:
                    out.break_before = True
                continue
            if st.in_code():
                continue
            if name == "t":
                text = ch.text or ""
                if font.startswith(_SYMBOL_FONTS):
                    text = "".join(_symbol(font, ord(c)) if not c.isspace() else c for c in text)
                if underlined:
                    text = _underline_blanks(text)
                st.emit(text, bold, size)
            elif name == "tab":
                st.emit(st.tab(underlined), bold, size)
            elif name in ("br", "cr"):
                st.emit("\n", bold, size)
            elif name == "sym":
                f = (ch.get(W + "font") or font).lower()
                try:
                    code = int(ch.get(W + "char") or "0", 16)
                except ValueError:
                    code = 0
                st.emit(_symbol(f, code), bold, size)
            elif name == "noBreakHyphen":
                st.emit("-", bold, size)
            elif name == "footnoteReference":
                fid = ch.get(W + "id") or ""
                out.footnotes.append(fid)
                if not _on(ch.find("w:customMarkFollows", NS)) and ch.get(W + "customMarkFollows") not in ("1", "true", "on"):
                    st.emit(str(self.footnote_order.get(fid, "")), bold, size)
            elif name == "footnoteRef":  # the number at the start of the footnote itself
                st.emit(str(self.footnote_order.get(self.current_note, "")), bold, size)
        for spec, checked in st.take_finished():
            out.widgets.append(spec)
            if spec.kind == "checkbox":
                st.emit(CHECK_ON if checked else CHECK_OFF, bold, size)

    def _drawing(self, el: etree._Element, out: _Para) -> None:
        if _local(el) in ("pict", "object"):
            out.drawings.append(el)
            return
        for d in el:
            if _local(d) in ("anchor", "inline"):
                out.drawings.append(d)


class _State:
    """Text being collected for one paragraph, with the stack of fields (legacy form fields among them)."""

    def __init__(self, pstyle: str | None, tabs: list[tuple[float, str]]):
        self.pstyle = pstyle
        self.tabs = tabs
        self.tab_count = 0
        self.parts: list[str] = []
        self.weights: list[tuple[bool, str]] = []
        self.size: float | None = None
        self.fields: list[dict] = []
        self.finished: list[tuple[_WidgetSpec, bool]] = []

    def emit(self, text: str, bold: bool, size: float | None) -> None:
        if not text:
            return
        self.parts.append(text)
        self.weights.append((bold, text))
        if self.size is None and size and text.strip():
            self.size = size

    def tab(self, underlined: bool) -> str:
        i = self.tab_count
        self.tab_count += 1
        if i < len(self.tabs) and self.tabs[i][1] in _LEADERS:
            return _LEADERS[self.tabs[i][1]] * LEADER_LEN
        return "_" * LEADER_LEN if underlined else "\t"

    def in_code(self) -> bool:
        return any(f["phase"] == "code" for f in self.fields)

    def field_char(self, ch: etree._Element) -> None:
        kind = ch.get(W + "fldCharType")
        if kind == "begin":
            self.fields.append({"phase": "code", "instr": "", "ff": ch.find("w:ffData", NS)})
        elif kind == "separate" and self.fields:
            self.fields[-1]["phase"] = "result"
        elif kind == "end" and self.fields:
            f = self.fields.pop()
            spec = _legacy_widget(f["instr"], f["ff"])
            if spec is not None:
                self.finished.append(spec)

    def instr(self, text: str) -> None:
        if self.fields and self.fields[-1]["phase"] == "code":
            self.fields[-1]["instr"] += text

    def take_finished(self) -> list[tuple[_WidgetSpec, bool]]:
        out, self.finished = self.finished, []
        return out


def _symbol(font: str, code: int) -> str:
    low = code - 0xF000 if 0xF000 <= code <= 0xF0FF else code
    for name, table in _SYMBOLS.items():
        if font == name or (font.startswith(name) and name != "wingdings"):
            return table.get(low, UNKNOWN_SYMBOL)
    if font.startswith("wingdings"):
        return _SYMBOLS["wingdings"].get(low, UNKNOWN_SYMBOL)
    if font.startswith(_SYMBOL_FONTS):
        return UNKNOWN_SYMBOL
    return chr(code) if code else UNKNOWN_SYMBOL


def _underline_blanks(text: str) -> str:
    out, i = [], 0
    while i < len(text):
        if text[i].isspace():
            j = i
            while j < len(text) and text[j].isspace():
                j += 1
            out.append("_" * (j - i) if j - i >= 3 else text[i:j])
            i = j
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def _val(el: etree._Element | None, path: str) -> str | None:
    x = el.find(path, NS) if el is not None else None
    return x.get(W + "val") if x is not None else None


def _legacy_widget(instr: str, ff: etree._Element | None) -> tuple[_WidgetSpec, bool] | None:
    code = instr.strip().split(" ", 1)[0].upper() if instr.strip() else ""
    if code not in ("FORMTEXT", "FORMCHECKBOX", "FORMDROPDOWN"):
        return None
    name = _val(ff, "w:name") or None
    if code == "FORMCHECKBOX":
        cb = ff.find("w:checkBox", NS) if ff is not None else None
        checked = cb is not None and (_on(cb.find("w:checked", NS)) or _val(cb, "w:default") in ("1", "true"))
        return _WidgetSpec("checkbox", name), checked
    if code == "FORMDROPDOWN":
        opts = [e.get(W + "val") or "" for e in (ff.findall("w:ddList/w:listEntry", NS) if ff is not None else [])]
        return _WidgetSpec("choice", name, options=opts), False
    ti = ff.find("w:textInput", NS) if ff is not None else None
    kind = "date" if _val(ti, "w:type") == "date" else "text"
    ml = _val(ti, "w:maxLength")
    return _WidgetSpec(kind, name, max_len=int(ml) if ml and ml.isdigit() and int(ml) >= 1 else None), False


def _sdt_widget(pr: etree._Element | None) -> _WidgetSpec | None:
    if pr is None:
        return None
    name = _val(pr, "w:alias") or _val(pr, "w:tag") or None
    if pr.find("w14:checkbox", NS) is not None:
        return _WidgetSpec("checkbox", name)
    for tag in ("w:dropDownList", "w:comboBox"):
        lst = pr.find(tag, NS)
        if lst is not None:
            opts = [i.get(W + "displayText") or i.get(W + "value") or "" for i in lst.findall("w:listItem", NS)]
            return _WidgetSpec("choice", name, options=opts)
    if pr.find("w:date", NS) is not None:
        return _WidgetSpec("date", name)
    if pr.find("w:text", NS) is not None or pr.find("w:richText", NS) is not None:
        return _WidgetSpec("text", name)
    if any(pr.find(t, NS) is not None for t in ("w:docPartObj", "w:docPartList", "w:picture", "w:group",
                                                  "w:citation", "w:bibliography", "w:equation")):
        return None
    # A control with no type element is a rich-text control by Word's default.
    return _WidgetSpec("text", name) if name or pr.find("w:id", NS) is not None else None


# ---------------------------------------------------------------- drawings: text boxes and shapes


def _txbx(drawing: etree._Element) -> etree._Element | None:
    tb = drawing.find(".//wps:txbx/w:txbxContent", NS)
    if tb is None:
        tb = drawing.find(".//v:textbox/w:txbxContent", NS)
    return tb


def _txbx_paras(tb: etree._Element) -> list[etree._Element]:
    """Paragraphs of a text box in order, through tables and controls, not into nested text boxes."""
    out: list[etree._Element] = []

    def walk(el: etree._Element) -> None:
        for ch in el:
            n = _local(ch)
            if n == "p":
                out.append(ch)
            elif n in ("tbl", "tr", "tc", "sdt", "sdtContent", "customXml"):
                walk(ch)

    walk(tb)
    return out


def _visible_fill(sppr: etree._Element | None) -> bool:
    if sppr is None:
        return False
    fill = sppr.find("a:solidFill", NS)
    if fill is None:
        return False
    color = fill.find("a:srgbClr", NS)
    if color is not None:
        if (color.get("val") or "").upper() == "FFFFFF":
            return False
        alpha = color.find("a:alpha", NS)
        if alpha is not None and alpha.get("val") == "0":
            return False
    return True


def _visible_outline(sppr: etree._Element | None, style: etree._Element | None) -> bool:
    ln = sppr.find("a:ln", NS) if sppr is not None else None
    if ln is not None:
        if ln.find("a:noFill", NS) is not None:
            return False
        if ln.find("a:solidFill", NS) is not None:
            return True
    ref = style.find("a:lnRef", NS) if style is not None else None
    return ref is not None and ref.get("idx", "0") != "0"


def _shape_kind(anchor: etree._Element) -> str:
    """'text' (text box), 'line', 'rect', 'picture' or '' (invisible or unknown)."""
    if _txbx(anchor) is not None:
        return "text"
    if anchor.find(".//pic:pic", NS) is not None:
        return "picture"
    wsp = anchor.find(".//wps:wsp", NS)
    if wsp is None:
        return ""
    sppr = wsp.find("wps:spPr", NS)
    geom = sppr.find("a:prstGeom", NS) if sppr is not None else None
    prst = geom.get("prst") if geom is not None else ""
    visible_line = _visible_outline(sppr, wsp.find("wps:style", NS))
    if prst in ("line", "straightConnector1"):
        return "line" if visible_line else ""
    if _visible_fill(sppr):
        return "fill"
    return "rect" if visible_line else ""


# ---------------------------------------------------------------- tables


def _cell_borders(tc_pr: etree._Element | None, tbl_borders: etree._Element | None, r: int, c: int, rs: int,
                  cs: int, rows: int, cols: int) -> str:
    def drawn(el: etree._Element | None) -> bool | None:
        if el is None:
            return None
        return (el.get(W + "val") or "nil") not in ("nil", "none")

    tcb = tc_pr.find("w:tcBorders", NS) if tc_pr is not None else None
    out = ""
    for side, names, edge, inside in (
        ("t", ("top",), r == 0, "insideH"),
        ("r", ("right", "end"), c + cs >= cols, "insideV"),
        ("b", ("bottom",), r + rs >= rows, "insideH"),
        ("l", ("left", "start"), c == 0, "insideV"),
    ):
        own = None
        for n in names:
            own = drawn(tcb.find(f"w:{n}", NS)) if tcb is not None else None
            if own is not None:
                break
        if own is None and tbl_borders is not None:
            for n in (names if edge else (inside,)):
                own = drawn(tbl_borders.find(f"w:{n}", NS))
                if own is not None:
                    break
        if own:
            out += side
    return out


# ---------------------------------------------------------------- document


@dataclass
class _Builder:
    ids: Ids
    pages: list[Page] = field(default_factory=list)
    cur: dict = field(default_factory=lambda: {"runs": [], "tables": [], "widgets": []})

    def busy(self) -> bool:
        return any(self.cur[k] for k in self.cur)

    def new_page(self) -> None:
        if self.busy():
            self.pages.append(Page(number=len(self.pages) + 1, origin="flow", **self.cur))
            self.cur = {"runs": [], "tables": [], "widgets": []}

    def run(self, para: _Para, anchor: str) -> str | None:
        text = para.text.strip()
        if not text:
            return None
        rid = self.ids.next("r")
        self.cur["runs"].append(Run(id=rid, text=text, anchor=anchor, size=para.size, bold=para.bold))
        return rid

    def widgets(self, para: _Para, anchor: str) -> None:
        for w in para.widgets:
            self.cur["widgets"].append(Widget(id=self.ids.next("w"), kind=w.kind, name=w.name, anchor=anchor,
                                              max_len=w.max_len, options=w.options))

    def finish(self) -> list[Page]:
        self.new_page()
        if not self.pages:
            self.pages.append(Page(number=1, origin="flow"))
        return self.pages


def _section_breaks(p: etree._Element) -> bool:
    sp = p.find("w:pPr/w:sectPr", NS)
    return sp is not None and _val(sp, "w:type") != "continuous"


def _read_flow(body: etree._Element, rd: _Reader, ids: Ids, notes: dict[str, etree._Element]) -> list[Page]:
    b = _Builder(ids)
    fn_page: dict[str, int] = {}
    counters = {"p": 0, "tbl": 0}

    def paragraph(p: etree._Element, anchor: str, top_level: bool) -> str | None:
        para = rd.para(p)
        if top_level and para.break_before:
            b.new_page()
        rid = b.run(para, anchor)
        b.widgets(para, anchor)
        for j, d in enumerate(para.drawings):
            tb = _txbx(d)
            if tb is None:
                continue
            for k, tp in enumerate(_txbx_paras(tb)):
                inner = rd.para(tp)
                b.run(inner, f"{anchor}/txbx[{j}]/p[{k}]")
                b.widgets(inner, f"{anchor}/txbx[{j}]/p[{k}]")
        for fid in para.footnotes:
            fn_page.setdefault(fid, len(b.pages) + 1)
        if top_level and (para.break_after or _section_breaks(p)):
            b.new_page()
        return rid

    def table(tbl: etree._Element, anchor: str) -> None:
        tid = ids.next("t")
        tpr = tbl.find("w:tblPr", NS)
        borders = tpr.find("w:tblBorders", NS) if tpr is not None else None
        if borders is None:
            borders = rd.styles.borders(_val(tpr, "w:tblStyle"))
        rows = [tr for tr in tbl if _local(tr) == "tr"]
        cols = len(tbl.findall("w:tblGrid/w:gridCol", NS))
        cells: list[dict] = []
        open_by_col: dict[int, dict] = {}
        nested: list[etree._Element] = []
        table_index = len(b.cur["tables"])
        b.cur["tables"].append(None)  # keep the table before its nested tables
        for r, tr in enumerate(rows):
            c = int(_val(tr.find("w:trPr", NS), "w:gridBefore") or 0)
            tcs = [x for x in tr if _local(x) == "tc"] + [
                x for s in tr if _local(s) == "sdt" for x in s.findall("w:sdtContent/w:tc", NS)]
            for tc in tcs:
                tc_pr = tc.find("w:tcPr", NS)
                span = int(_val(tc_pr, "w:gridSpan") or 1)
                vm = tc_pr.find("w:vMerge", NS) if tc_pr is not None else None
                if vm is not None and vm.get(W + "val", "continue") == "continue" and c in open_by_col:
                    cell = open_by_col[c]
                    cell["rs"] = r - cell["r"] + 1
                else:
                    cell = {"r": r, "c": c, "rs": 1, "cs": span, "pr": tc_pr, "runs": []}
                    cells.append(cell)
                    if vm is not None:
                        open_by_col[c] = cell
                    else:
                        open_by_col.pop(c, None)
                base = f"{anchor}/cell[{cell['r']},{cell['c']}]"
                k = len(cell["runs"])
                for x in tc:
                    n = _local(x)
                    if n == "p":
                        rid = paragraph(x, f"{base}/p[{k}]", top_level=False)
                        k += 1
                        if rid:
                            cell["runs"].append(rid)
                    elif n == "tbl":
                        nested.append((x, f"{base}/tbl[{len(nested)}]"))
                    elif n == "sdt":
                        for y in x.findall("w:sdtContent/w:p", NS):
                            rid = paragraph(y, f"{base}/p[{k}]", top_level=False)
                            k += 1
                            if rid:
                                cell["runs"].append(rid)
                c += span
            cols = max(cols, c)
        b.cur["tables"][table_index] = Table(id=tid, anchor=anchor, cells=[
            Cell(r=x["r"], c=x["c"], rs=x["rs"], cs=x["cs"], anchor=f"{anchor}/cell[{x['r']},{x['c']}]",
                 runs=x["runs"], borders=_cell_borders(x["pr"], borders, x["r"], x["c"], x["rs"], x["cs"],
                                                       len(rows), cols))
            for x in cells])
        for el, a in nested:
            table(el, a)

    def blocks(container: etree._Element) -> None:
        for el in container:
            n = _local(el)
            if n == "p":
                paragraph(el, f"p[{counters['p']}]", top_level=True)
                counters["p"] += 1
            elif n == "tbl":
                table(el, f"tbl[{counters['tbl']}]")
                counters["tbl"] += 1
            elif n in ("sdt", "customXml"):
                spec = _sdt_widget(el.find("w:sdtPr", NS)) if n == "sdt" else None
                if spec is not None:
                    b.cur["widgets"].append(Widget(id=ids.next("w"), kind=spec.kind, name=spec.name,
                                                   anchor=f"p[{counters['p']}]", max_len=spec.max_len,
                                                   options=spec.options))
                content = el.find("w:sdtContent", NS) if n == "sdt" else el
                if content is not None:
                    blocks(content)

    blocks(body)
    pages = b.finish()
    # Footnotes go to the page that refers to them, after its own content.
    by_page: dict[int, list[Run]] = {}
    for fid, note in notes.items():
        page_no = min(fn_page.get(fid, len(pages)), len(pages))
        rd.current_note = fid
        for k, p in enumerate(x for x in note if _local(x) == "p"):
            para = rd.para(p)
            text = para.text.strip()
            if text:
                by_page.setdefault(page_no, []).append(
                    Run(id=ids.next("r"), text=text, anchor=f"fn[{fid}]/p[{k}]", size=para.size, bold=para.bold))
    if by_page:
        pages = [pg.model_copy(update={"runs": [*pg.runs, *by_page.get(pg.number, [])]}) for pg in pages]
    return pages


def _emu(el: etree._Element | None) -> float | None:
    if el is None or el.text is None:
        return None
    try:
        return float(el.text.strip()) / EMU
    except ValueError:
        return None


def _read_native(body: etree._Element, rd: _Reader, ids: Ids) -> tuple[list[Page], list[Warning]]:
    # Pages and the section that governs each.
    body_sect = body.find("w:sectPr", NS)
    groups: list[dict] = [{"paras": [], "sect": None}]
    for p in body.iter(W + "p"):
        if any(_local(a) in ("txbxContent", "Fallback") for a in p.iterancestors()):
            continue
        para = rd.para(p)
        if para.break_before and groups[-1]["paras"]:
            groups.append({"paras": [], "sect": None})
        groups[-1]["paras"].append((p, para))
        sp = p.find("w:pPr/w:sectPr", NS)
        if sp is not None:
            for g in reversed(groups):  # a section break closes every page of its section
                if g["sect"] is not None:
                    break
                g["sect"] = sp
        if para.break_after or (sp is not None and _val(sp, "w:type") != "continuous"):
            groups.append({"paras": [], "sect": None})
    groups = [g for g in groups if g["paras"]] or [{"paras": [], "sect": None}]
    pages: list[Page] = []
    unplaced = {"position": 0, "body_chars": 0, "pictures": 0, "vml": 0}
    for g in groups:
        sect = g["sect"] if g["sect"] is not None else body_sect
        pg_sz = sect.find("w:pgSz", NS) if sect is not None else None
        mar = sect.find("w:pgMar", NS) if sect is not None else None

        def tw(el: etree._Element | None, key: str, default: float) -> float:
            v = el.get(W + key) if el is not None else None
            try:
                return float(v) / TWIP if v is not None else default
            except ValueError:
                return default

        width, height = tw(pg_sz, "w", 595.3), tw(pg_sz, "h", 841.9)
        left, top = tw(mar, "left", 72.0), tw(mar, "top", 72.0)
        right, bottom = tw(mar, "right", 72.0), tw(mar, "bottom", 72.0)
        runs: list[Run] = []
        lines: list[Line] = []
        rects: list[Rect] = []
        widgets: list[Widget] = []
        for idx, (p, para) in enumerate(g["paras"]):
            unplaced["body_chars"] += len(para.text.strip())
            for d in para.drawings:
                if _local(d) != "anchor":
                    if _txbx(d) is not None:
                        unplaced["vml" if _local(d) in ("pict", "object") else "position"] += 1
                    continue
                box = _anchor_box(d, width, height, left, top, right, bottom, first=idx == 0)
                kind = _shape_kind(d)
                if box is None:
                    if kind:
                        unplaced["position"] += 1
                    continue
                x0, y0, x1, y1 = box
                if kind == "text":
                    for tp in _txbx_paras(_txbx(d)):
                        inner = rd.para(tp)
                        text = inner.text.strip()
                        if text:
                            runs.append(Run(id=ids.next("r"), text=text, box=box, size=inner.size, bold=inner.bold))
                        for w in inner.widgets:
                            widgets.append(Widget(id=ids.next("w"), kind=w.kind, name=w.name, box=box,
                                                  max_len=w.max_len, options=w.options))
                elif kind in ("line", "fill", "rect"):
                    w, h = x1 - x0, y1 - y0
                    if kind in ("line", "fill") and h <= LINE_MAX_THICKNESS and w > h:
                        y = r2((y0 + y1) / 2)
                        lines.append(Line(id=ids.next("l"), box=(x0, y, x1, y)))
                    elif kind in ("line", "fill") and w <= LINE_MAX_THICKNESS and h > w:
                        x = r2((x0 + x1) / 2)
                        lines.append(Line(id=ids.next("l"), box=(x, y0, x, y1)))
                    elif kind != "line":
                        rects.append(Rect(id=ids.next("q"), box=box))
                elif kind == "picture":
                    if x1 - x0 <= PICTURE_BOX_MAX and y1 - y0 <= PICTURE_BOX_MAX:
                        rects.append(Rect(id=ids.next("q"), box=box))
                    else:
                        unplaced["pictures"] += 1
        pages.append(Page(number=len(pages) + 1, width=r2(width), height=r2(height), origin="native",
                          runs=runs, lines=lines, rects=rects, widgets=widgets))
    warnings: list[Warning] = []
    if unplaced["position"]:
        warnings.append(Warning(code="UNREADABLE_PART", detail=f"{unplaced['position']} drawings have a position "
                                "this reader cannot place (relative to a character or aligned); they are not read"))
    if unplaced["vml"]:
        warnings.append(Warning(code="UNREADABLE_PART", detail=f"{unplaced['vml']} text boxes in the old VML form "
                                "only; their position is not read"))
    if unplaced["body_chars"]:
        warnings.append(Warning(code="UNREADABLE_PART", detail=f"{unplaced['body_chars']} characters of body text "
                                "between the text boxes have no position on the page; they are not read"))
    if unplaced["pictures"]:
        warnings.append(Warning(code="UNREADABLE_PART", detail=f"{unplaced['pictures']} pictures larger than a box "
                                "glyph; their pixels are not read"))
    return pages, warnings


def _anchor_box(d: etree._Element, width: float, height: float, left: float, top: float, right: float,
                bottom: float, first: bool) -> tuple[float, float, float, float] | None:
    ext = d.find("wp:extent", NS)
    try:
        cx = float(ext.get("cx")) / EMU if ext is not None else 0.0
        cy = float(ext.get("cy")) / EMU if ext is not None else 0.0
    except (TypeError, ValueError):
        return None
    if d.get("simplePos") in ("1", "true"):
        sp = d.find("wp:simplePos", NS)
        try:
            x, y = float(sp.get("x")) / EMU, float(sp.get("y")) / EMU
        except (AttributeError, TypeError, ValueError):
            return None
    else:
        ph, pv = d.find("wp:positionH", NS), d.find("wp:positionV", NS)
        ox = _emu(ph.find("wp:posOffset", NS)) if ph is not None else None
        oy = _emu(pv.find("wp:posOffset", NS)) if pv is not None else None
        if ox is None or oy is None:
            return None
        base_x = {"page": 0.0, "margin": left, "column": left, "leftMargin": 0.0, "insideMargin": 0.0,
                  "rightMargin": width - right, "outsideMargin": width - right}.get(ph.get("relativeFrom") or "")
        # "paragraph" and "line" are measured from the anchoring paragraph: known only for the first one of a page,
        # which starts at the top margin.
        rel_v = pv.get("relativeFrom") or ""
        base_y = {"page": 0.0, "margin": top, "topMargin": 0.0, "bottomMargin": height - bottom,
                  "insideMargin": 0.0, "outsideMargin": height - bottom}.get(rel_v)
        if base_y is None and rel_v in ("paragraph", "line") and first:
            base_y = top
        if base_x is None or base_y is None:
            return None
        x, y = base_x + ox, base_y + oy
    return (r2(x), r2(y), r2(x + cx), r2(y + cy))


def _text_shares(body: etree._Element) -> tuple[int, int]:
    """Characters inside anchored text boxes, characters elsewhere (fallback copies of drawings ignored)."""
    boxed = other = 0
    for t in body.iter(W + "t"):
        n = len((t.text or "").strip())
        if not n:
            continue
        anchored = in_box = fallback = False
        for a in t.iterancestors():
            name = _local(a)
            if name == "Fallback":
                fallback = True
                break
            if name == "txbxContent":
                in_box = True
            elif name == "anchor" and in_box:
                anchored = True
        if fallback:
            continue
        if anchored:
            boxed += n
        else:
            other += n
    return boxed, other


@register("docx")
def read(data: bytes, options: ReadOptions) -> ReadResult:
    z = _open(data, options)
    with z:
        doc = _part(z, "word/document.xml", options)
        styles_root = _part(z, "word/styles.xml", options)
        styles = _Styles(styles_root)
        notes_root = _part(z, "word/footnotes.xml", options)
        numbering_root = _part(z, "word/numbering.xml", options)
    body = doc.find("w:body", NS) if doc is not None else None
    if body is None:
        raise ReaderError("UNREADABLE", "word/document.xml has no body")
    notes: dict[str, etree._Element] = {}
    if notes_root is not None:
        for fnote in notes_root.findall("w:footnote", NS):
            if fnote.get(W + "type") in (None, "normal"):
                notes[fnote.get(W + "id") or ""] = fnote
    order: dict[str, int] = {}
    for ref in body.iter(W + "footnoteReference"):
        order.setdefault(ref.get(W + "id") or "", len(order) + 1)
    notes = {k: notes[k] for k in sorted(notes, key=lambda k: order.get(k, 10**6))}
    rd = _Reader(styles, order)
    if numbering_root is not None:
        rd.markers = _Numbering(numbering_root, styles_root).markers(body)
    ids = Ids()
    boxed, other = _text_shares(body)
    if boxed and boxed >= NATIVE_SHARE * (boxed + other):
        pages, warnings = _read_native(body, rd, ids)
        if notes:
            warnings.append(Warning(code="UNREADABLE_PART", detail=f"{len(notes)} footnotes in a document made of "
                                    "text boxes have no position; they are not read"))
        return ReadResult(reader="docx.native", pages=pages, warnings=warnings)
    return ReadResult(reader="docx.flow", pages=_read_flow(body, rd, ids, notes))
