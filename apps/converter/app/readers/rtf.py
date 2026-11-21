"""RTF reader (WP-F20f, D24): our own, pure Python, no dependency; one flow page, the model of the ODT reader.

The file is one pass over a token stream with an explicit stack of group states (no recursion), so a deeply nested
file costs a refusal at MAX_DEPTH and never a stack overflow. What is read: the paragraphs of the body ("p[n]"), tables
(`\\trowd` ... `\\cell` ... `\\row`) as "tbl[n]" with cells "tbl[n]/cell[r,c]" (merged cells through `\\clmgf`,
`\\clmrg`, `\\clvmgf`, `\\clvmrg`; a nested table is flattened into the paragraphs of its cell), the result text of a field
(`\\fldrslt`), legacy form fields (`\\formfield`: `\\fftype1` is a checkbox, `\\fftype0` a text blank, written as the
glyph or a leader in the text and as a widget), the characters of the document code page (`\\ansicpg`, `\\'xx` and raw
8-bit bytes; `\\uN` with `\\ucN` skipping). Not read: destinations the file marks `\\*` (list numbers among them), font,
colour and style tables, document info, pictures, objects, headers, footers, footnotes, text boxes. Limits: nesting
depth, characters, groups, and cells plus paragraphs (ReadOptions.max_cells); each one a refusal, never a truncation.
"""
from __future__ import annotations

import re

from app.model.page import Cell, Page, Run, Table, Widget

from . import register
from ._base import Ids, ReaderError, ReadOptions, ReadResult, nn

MAX_DEPTH = 128
MAX_CHARS = 8_000_000
MAX_GROUPS = 2_000_000
MAX_BIN = 64 << 20
CHECK_OFF, CHECK_ON = "☐", "☒"
LEADER = "_" * 10

TOKEN = re.compile(
    r"\\([A-Za-z]{1,32})(-?\d{1,10})?[ ]?"      # 1 control word, 2 its number (the one space after it is a delimiter)
    r"|\\'([0-9A-Fa-f]{2})"                      # 3 hex byte
    r"|\\([^A-Za-z\r\n])"                         # 4 control symbol
    r"|\\(\r\n|\r|\n)"                            # 5 an escaped line end is \par
    r"|([{}])"                                    # 6 group
    r"|([^\\{}\r\n]+)"                            # 7 text
    r"|[\r\n]+"                                   # raw line ends carry no meaning
    r"|(\\)")                                     # 8 a lone backslash at the end

# Destinations whose content is never text of the document (the first control word of a group, with or without `\*`).
SKIP = frozenset("""fonttbl colortbl stylesheet info pict object header headerl headerr headerf footer footerl footerr
footerf listtable listoverridetable rsidtbl generator latentstyles themedata colorschememapping datastore xmlnstbl
pgptbl revtbl fchars lchars private footnote bkmkstart bkmkend shppict nonshppict datafield ffname ffdeftext ffformat
ffhelptext ffstattext ffentrymcr ffexitmcr falt panose fname ftnsep ftnsepc aftnsep aftnsepc upr pn pntext pnseclvl
listtext revtbl objdata result mmathPr wgrffmtfilter userprops""".split())

SYMBOLS = {"tab": "\t", "emdash": "—", "endash": "–", "bullet": "•", "lquote": "‘", "rquote": "’",
           "ldblquote": "“", "rdblquote": "”", "enspace": " ", "emspace": " ", "qmspace": " ", "~": " ", "_": "-",
           "\\": "\\", "{": "{", "}": "}"}
PARA_END = frozenset({"par", "line", "sect"})
CODEPAGES = {"mac": "mac_roman", "pc": "cp437", "pca": "cp850"}


class _State:
    __slots__ = ("skip", "mute", "uc", "star", "field", "form", "owns_form", "first")

    def __init__(self) -> None:
        self.skip = False          # the group is a destination whose content is dropped
        self.mute = False          # text is dropped, control words still count (field instruction, form field)
        self.uc = 1                # bytes to skip after \uN
        self.star = False          # the last token was \*
        self.field: dict | None = None
        self.form: dict | None = None
        self.owns_form = False
        self.first = True          # no token has followed the opening brace yet

    def child(self) -> "_State":
        s = _State()
        s.skip, s.mute, s.uc, s.field, s.form = self.skip, self.mute, self.uc, self.field, self.form
        return s


def _codepage(n: int) -> str:
    for name in (f"cp{n}", str(n)):
        try:
            import codecs

            codecs.lookup(name)
            return name
        except LookupError:
            continue
    return "cp1252"


class _Rtf:
    def __init__(self, options: ReadOptions) -> None:
        self.options = options
        self.ids = Ids()
        self.runs: list[Run] = []
        self.tables: list[Table] = []
        self.widgets: list[Widget] = []
        self.codepage = "cp1252"
        self.buf: list[str] = []
        self.pend = bytearray()
        self.para_widgets: list[tuple[str, int | None]] = []
        self.chars = 0
        self.budget = options.max_cells
        self.p = 0
        self.t = 0
        # table state
        self.in_row = False
        self.cell_paras: list[tuple[str, list]] = []
        self.cells: list[list[tuple[str, list]]] = []
        self.defs: list[tuple[str, str]] = []
        self.flags = ["", ""]
        self.tbl: list[dict] | None = None
        self.tbl_rows = 0
        self.vorigin: dict[int, dict] = {}

    # ---- text -------------------------------------------------------------------------------------------------
    def flush(self) -> None:
        if self.pend:
            self.buf.append(bytes(self.pend).decode(self.codepage, "replace"))
            self.pend.clear()

    def add(self, text: str) -> None:
        self.chars += len(text)
        if self.chars > MAX_CHARS:
            raise ReaderError("TOO_LARGE", f"the document has more than {MAX_CHARS} characters")
        self.flush()
        self.buf.append(text)

    def spend(self, n: int = 1) -> None:
        self.budget -= n
        if self.budget < 0:
            raise ReaderError("TOO_LARGE", f"the document has more than {self.options.max_cells} paragraphs and cells")

    def take_para(self) -> tuple[str, list]:
        self.flush()
        text = "".join(self.buf)
        self.buf.clear()
        widgets, self.para_widgets = self.para_widgets, []
        text = text.encode("utf-16-le", "surrogatepass").decode("utf-16-le", "replace")
        return text.strip(), widgets

    def run(self, text: str, anchor: str) -> str:
        rid = self.ids.next("r")
        self.runs.append(Run(id=rid, text=text, anchor=anchor))
        return rid

    def put_widgets(self, widgets: list, anchor: str) -> None:
        for kind, max_len in widgets:
            self.widgets.append(Widget(id=self.ids.next("w"), **nn(kind=kind, anchor=anchor, max_len=max_len)))

    # ---- paragraphs and tables -----------------------------------------------------------------------------------
    def end_para(self) -> None:
        text, widgets = self.take_para()
        if self.in_row:
            self.cell_paras.append((text, widgets))
            return
        self.close_table()
        self.spend()
        anchor = f"p[{self.p}]"
        self.p += 1
        if text:
            self.run(text, anchor)
            self.put_widgets(widgets, anchor)

    def end_cell(self) -> None:
        if not self.in_row:
            self.end_para()
            return
        text, widgets = self.take_para()
        if text or widgets:
            self.cell_paras.append((text, widgets))
        self.cells.append(self.cell_paras)
        self.cell_paras = []

    def start_row(self) -> None:
        if self.cells:
            self.end_row()
        self.in_row = True
        self.defs = []
        self.flags = ["", ""]

    def end_row(self) -> None:
        if self.cell_paras:
            self.cells.append(self.cell_paras)
            self.cell_paras = []
        if self.tbl is None:
            self.tbl, self.tbl_rows, self.vorigin = [], 0, {}
        r, origin = self.tbl_rows, None
        for idx, paras in enumerate(self.cells):
            self.spend()
            h, v = self.defs[idx] if idx < len(self.defs) else ("", "")
            if h == "cont" and origin is not None:
                origin["cs"] += 1
                continue
            if v == "cont" and idx in self.vorigin:
                self.vorigin[idx]["rs"] += 1
                continue
            rec = {"r": r, "c": idx, "rs": 1, "cs": 1, "paras": paras}
            self.tbl.append(rec)
            origin = rec if h == "first" else None
            if v == "first":
                self.vorigin[idx] = rec
            elif idx in self.vorigin:
                del self.vorigin[idx]
        self.tbl_rows += 1
        self.cells = []
        self.in_row = False

    def close_table(self) -> None:
        if self.tbl is None:
            return
        anchor = f"tbl[{self.t}]"
        self.t += 1
        out: list[Cell] = []
        for rec in self.tbl:
            texts = [(t, w) for t, w in rec["paras"] if t]
            if not texts:
                continue
            base = f"{anchor}/cell[{rec['r']},{rec['c']}]"
            rids = []
            for i, (t, w) in enumerate(texts):
                rids.append(self.run(t, f"{base}/p[{i}]"))
                self.put_widgets(w, f"{base}/p[{i}]")
            out.append(Cell(r=rec["r"], c=rec["c"], rs=rec["rs"], cs=rec["cs"], anchor=base, runs=rids))
        if out:
            self.tables.append(Table(id=self.ids.next("t"), anchor=anchor, cells=out))
        self.tbl = None

    # ---- the pass ----------------------------------------------------------------------------------------------------
    def parse(self, text: str) -> None:
        stack: list[_State] = []
        st = _State()
        pos, n, groups, skipchars = 0, len(text), 0, 0
        while pos < n:
            m = TOKEN.match(text, pos)
            if m is None:   # cannot happen: every character matches an alternative; keep the loop finite anyway
                pos += 1
                continue
            pos = m.end()
            word, num, hexb, sym, esc, brace, chunk, stray = m.groups()
            if brace == "{":
                groups += 1
                if groups > MAX_GROUPS:
                    raise ReaderError("TOO_LARGE", f"the document has more than {MAX_GROUPS} groups")
                if len(stack) >= MAX_DEPTH:
                    raise ReaderError("UNREADABLE", "the document nests deeper than the reader follows")
                stack.append(st)
                st = st.child()
                skipchars = 0
                continue
            if brace == "}":
                skipchars = 0
                if not stack:
                    continue   # a stray closing brace
                if st.owns_form and st.form is not None:
                    self.finish_form(st)
                st = stack.pop()
                continue
            if chunk is not None:
                if skipchars:
                    drop = min(skipchars, len(chunk))
                    chunk, skipchars = chunk[drop:], skipchars - drop
                if chunk and not st.skip and not st.mute:
                    if chunk.isascii():
                        self.add(chunk)
                    else:
                        self.chars += len(chunk)
                        self.pend.extend(chunk.encode("latin-1", "replace"))
                st.first = False
                continue
            if hexb is not None:
                if skipchars:
                    skipchars -= 1
                elif not st.skip and not st.mute:
                    self.chars += 1
                    self.pend.append(int(hexb, 16))
                st.first = False
                continue
            skipchars = 0
            if esc is not None:
                if not st.skip and not st.mute:
                    self.end_para()
                st.first = False
                continue
            if sym is not None:
                if sym == "*":
                    st.star = True
                    continue
                st.first = False
                if sym in SYMBOLS and not st.skip and not st.mute:
                    self.add(SYMBOLS[sym])
                continue
            if stray is not None:
                continue
            # a control word
            was_first, st.first = st.first, False
            if word == "bin":
                pos += min(int(num or 0), MAX_BIN)
                continue
            if st.star or was_first:
                starred, st.star = st.star, False
                if word == "formfield" and starred:
                    st.mute, st.form, st.owns_form = True, {}, True
                    continue
                if word == "fldinst":
                    st.mute = True
                    continue
                if word == "fldrslt":
                    if st.field is not None and st.field.get("form"):
                        st.mute = True
                    continue
                if word == "field":
                    st.field = {}
                    continue
                if starred or word in SKIP:
                    st.skip = True
                    continue
            if st.skip:
                continue
            self.word(st, word, int(num) if num is not None else None)
            if word == "u" and num is not None and not st.mute:
                skipchars = max(0, st.uc)
        self.flush()

    def word(self, st: _State, word: str, num: int | None) -> None:
        if word == "uc":
            st.uc = num if num is not None else 1
        elif word == "u":
            if num is not None and not st.mute:
                code = num % 65536   # the value is a signed 16-bit number
                self.add(chr(code))   # a lone surrogate half is repaired when the paragraph is taken
        elif word == "ansicpg" and num:
            self.codepage = _codepage(num)
        elif word in CODEPAGES:
            self.codepage = CODEPAGES[word]
        elif word in PARA_END:
            if not st.mute:
                self.end_para()
        elif word == "cell":
            if not st.mute:
                self.end_cell()
        elif word in ("nestcell", "nestrow"):
            self.nest_break()
        elif word == "row":
            if self.in_row or self.cells:
                self.end_row()
        elif word == "trowd":
            self.start_row()
        elif word in ("clmgf", "clmrg"):
            self.flags[0] = "first" if word == "clmgf" else "cont"
        elif word in ("clvmgf", "clvmrg"):
            self.flags[1] = "first" if word == "clvmgf" else "cont"
        elif word == "cellx":
            self.defs.append((self.flags[0], self.flags[1]))
            self.flags = ["", ""]
        elif st.form is not None:
            if word == "fftype":
                st.form["type"] = num
            elif word == "ffres":
                st.form["res"] = num
            elif word == "ffdefres":
                st.form["defres"] = num
            elif word == "ffmaxlen":
                st.form["max"] = num
        elif word in SYMBOLS and not st.mute:
            self.add(SYMBOLS[word])

    def nest_break(self) -> None:
        """The end of a cell or row of a nested table: flattened, so only a paragraph break of the enclosing cell."""
        if not self.in_row:
            self.end_para()
            return
        text, widgets = self.take_para()
        if text or widgets:
            self.cell_paras.append((text, widgets))

    def finish_form(self, st: _State) -> None:
        form = st.form or {}
        kind = form.get("type")
        if st.field is not None:
            st.field["form"] = True
        if kind == 1:
            res = form.get("res")
            checked = (res if res is not None else form.get("defres")) == 1
            self.add(CHECK_ON if checked else CHECK_OFF)
            self.para_widgets.append(("checkbox", None))
        elif kind == 0:
            self.add(LEADER)
            maxlen = form.get("max")
            self.para_widgets.append(("text", maxlen if maxlen and maxlen > 0 else None))

    def finish(self) -> Page:
        if self.cells or self.cell_paras:
            self.end_row()
        self.in_row = False
        text, widgets = self.take_para()
        if text:
            self.spend()
            anchor = f"p[{self.p}]"
            self.p += 1
            self.close_table()
            self.run(text, anchor)
            self.put_widgets(widgets, anchor)
        self.close_table()
        return Page(number=1, origin="flow", runs=self.runs, tables=self.tables, widgets=self.widgets)


@register("rtf")
def read(data: bytes, options: ReadOptions) -> ReadResult:
    if not data.startswith(b"{\\rtf"):
        raise ReaderError("UNREADABLE", "the file does not start as an RTF document")
    rd = _Rtf(options)
    rd.parse(data.decode("latin-1"))
    return ReadResult(reader="rtf", pages=[rd.finish()])
