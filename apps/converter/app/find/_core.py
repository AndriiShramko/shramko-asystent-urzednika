"""The finder's rules (design 6.3): roles of text, sections, places to fill, groups, labels.

Order of work, each step a small rule set that a test can break:
  1. lines per page (_text), closed boxes per page (_shapes), reading order over both
  2. roles of lines in reading order: page furniture, notes, the data-protection clause (a mode that lasts until
     a heading of the form or a place to fill), headings (-> sections), instructions, legal basis
  3. places inside lines: leaders, blanks of a sentence, box characters with their words
  4. drawn places: combs, small boxes, empty ruled cells, table cells, declared widgets
  5. several full-width leaders in a row -> one line_block; boxes that share a row or a column -> one group
  6. labels by score for what has none yet; kinds signature and office_use from the label
A place the rules cannot label keeps no label and gets the warning LABEL_NOT_FOUND: never a guess.
"""
from __future__ import annotations

import bisect
import re
from dataclasses import dataclass, field
from typing import Any

from app.model.candidate import Candidate, ChoiceOption, Confidence, FinderOutput, Label, Section
from app.model.common import Box as ModelBox
from app.model.common import InputRef, Span, Warning
from app.model.page import Page, PageModel

from . import _shapes as sh
from ._text import TAB_LEADER, TLine, build_lines

Box = tuple[float, float, float, float]
Parts = list[tuple[str, int, int]]

BOX_CHARS = "□❑☐❏❐❒▢◻◽⬜"
TICKED_CHARS = "☑☒"
_I = re.IGNORECASE
LEAD_RE = re.compile(r"[.…_\x00](?:[ \xa0]?[.…_\x00])*")
MARK_RE = re.compile("[" + BOX_CHARS + TICKED_CHARS + "]")
# Symbol-font glyphs (private use area) that sets 3 and 9 print before each option of a list: a mark only at the
# start of a line and before a word. A symbol bullet (U+F0B7, U+F0A7) is not one of them.
PUA_MARKS = ""
TOP_LINES = 3
PUA_RE = re.compile(r"^\s*([" + PUA_MARKS + r"])\s*(?=\w)")
NUM_HEAD = re.compile(r"^(?:\d{1,2}(?:\.\d{1,2})*\.|[IVX]{1,4}\.|[A-Z]\.)\s+[A-ZĄĆĘŁŃÓŚŹŻ]")
FURNITURE = re.compile(r"^(?:strona|str\.)\s*\d+\s*(?:(?:z|/)\s*\d+)?$|\bstrona\s+\d+\s+z\s+\d+\b|^wersja\b"
                       r"|^załącznik\s+nr\s+\S+\s+do\b", _I)
PAGE_NO = re.compile(r"^-?\s*\d{1,3}\s*-?$")
CLAUSE_START = re.compile(r"klauzula\s+informacyjna|informacj\w*\s+(?:dotycząc\w*\s+|o\s+)przetwarzani\w*"
                          r"|obowiąz\w+\s+informacyjn\w+|art\.\s*13\b.*2016/679|2016/679.*art\.\s*13\b", _I)
CLAUSE_VOCAB = re.compile(r"dan(?:e|ych)\b|przetwarzan|administrator|inspektor|odbiorc|retencj|praw[ao]?\b|podstaw"
                          r"|zautomatyzowan|profilowan|obligatoryjn|okres|cel[ue]?\b|rodo|informacyjn", _I)
INSTR = re.compile(r"wypełni[ajć]\w*|oznacz\w*|zaznacz\w*|postaw\w*\s+(?:znak|„|\"|x\b)|niepotrzebne\s+skreślić"
                   r"|właściwe\s+(?:zaznaczyć|podkreślić|skreślić)|drukowanymi\s+literami|wielkimi\s+literami", _I)
INSTR_HEAD = re.compile(r"instrukcj|pouczeni|objaśnieni|sposób\s+wypełni", _I)
LEGAL = re.compile(r"^(?:na\s+podstawie|zgodnie\s+z)\s+(?:art|§|ustaw|rozporz)|^art\.\s*\d+.*\b(?:ustaw|rozporządz|kodeks)"
                   r"|\bDz\.\s?U\.", _I)
SIGN = re.compile(r"podpis|pieczę[ćc]|pieczątk", _I)
# a blank inside a sentence: not "niżej podpisany", which names the person
SIGN_WORD = re.compile(r"\bpodpis(?:y|em)?\b|pieczę[ćc]|pieczątk", _I)
SIGN_DATE = re.compile(r"^(?:data|dnia|miejscowość(?:,|\s+i)\s+data|data\s+i\s+miejscowość)$", _I)
OFFICE = re.compile(r"wypełnia\s+(?:organ|urząd|pracownik)|wypełnian\w*\s+przez\s+(?:organ|urząd|pracownik)"
                    r"|adnotacj\w+\s+(?:urzęd|organu)|miejsce\s+na\s+piecz"
                    r"|n(?:r|umer)\s+sprawy|znak\s+sprawy|data\s+wpływu|potwierdzenie\s+(?:przyjęcia|wpływu)", _I)
# a heading that gives its whole part to the office: word ends, so "wypełnia organizator" (the applicant of an event)
# and "wypełnia pracownik" (the employee on a staff form) keep their part
OFFICE_HEAD = re.compile(r"wypełnia\w*\s+(?:przez\s+)?(?:organ\b|urz[ąę]d|pracownik\w*\s+urzęd)"
                         r"|adnotacj\w+\s+(?:urzęd|organu)", _I)
NOTE = re.compile(r"^/?\s*(?:\d{1,2}\s?\)|\*{1,3}\)?)\s*\S")
CAPTION = re.compile(r"^\s*[(/]")
NUM = re.compile(r"^(\d{1,2}(?:\.\d{1,2})*)\.?\s+(\S.*)$")
LET = re.compile(r"^([A-Z]|[IVX]{1,4})[.)]\s+(\S.*)$")
LONE = re.compile(r"^([A-Z]|\d{1,2})\.?$")
FOOT = re.compile(r"(?<=[^\s\d])\s?(\d{1,2}\)|\*{1,3})$")
BULLET = re.compile(r"^[\s•·▪■●○◦‣\-–—*]+")
PATTERN = re.compile(r"^[A-Za-z]+(?:[-./ ][A-Za-z]+)+$")
WORD = re.compile(r"[^\W_]")


@dataclass(frozen=True)
class FindOptions:
    min_leader: int = 8      # dots or underscores that make a leader (design 6.3.3)
    strict: bool = False     # tests: let an exception of a rule through instead of answering with a warning

    @classmethod
    def of(cls, options: Any) -> "FindOptions":
        if isinstance(options, cls):
            return options
        known = {k: v for k, v in dict(options or {}).items() if k in cls.__dataclass_fields__}
        return cls(**known)


@dataclass(eq=False)
class Lab:
    text: str
    parts: Parts
    how: str
    score: float
    margin: float
    foot: list[str] = field(default_factory=list)


@dataclass(eq=False)
class D:
    """A candidate while it is being worked out."""

    kind: str
    page: int
    pos: float
    box: Box | None = None
    anchor: str | None = None
    parts: Parts = field(default_factory=list)
    cells: int | None = None
    lines: int | None = None
    mask: str | None = None
    widget: str | None = None
    label: Lab | None = None
    options: list[tuple[str, Parts, "D", "D | None"]] = field(default_factory=list)
    group: "D | None" = None
    geom: float = 0.9
    line: TLine | None = None
    last: TLine | None = None
    bare: bool = False
    opt: tuple[str, Parts, "D | None"] | None = None
    question: Lab | None = None
    table: bool = False
    id: str = ""


@dataclass(eq=False)
class S:
    title: str
    number: str | None
    page: int
    pos: int
    lines: list[TLine]
    instr: bool = False
    id: str = ""


@dataclass(eq=False)
class P:
    page: Page
    lines: list[TLine]
    geo: bool
    hor: list[Box] = field(default_factory=list)
    ver: list[Box] = field(default_factory=list)
    leaf: list[Box] = field(default_factory=list)
    empty: list[Box] = field(default_factory=list)
    boxpos: dict[Box, int] = field(default_factory=dict)
    first: int = 0
    col0: list[TLine] = field(default_factory=list)


def clean(raw: str) -> tuple[str, list[str]]:
    """A label as printed, without what is not part of it: bullets, a footnote mark, the brackets of a caption."""
    t = BULLET.sub("", raw.replace("\xa0", " ")).strip()
    foot: list[str] = []
    m = FOOT.search(t)
    if m:
        foot.append(m.group(1).rstrip(")"))
        t = t[:m.start()].rstrip()
    if len(t) > 2 and ((t[0] == "(" and t[-1] == ")" and "(" not in t[1:]) or (t[0] == "/" and t[-1] == "/")):
        t = t[1:-1].strip()
    t = re.sub(r"\s+", " ", t).rstrip(":").strip()
    return (t if WORD.search(t) else ""), foot


def _yov(a: Box, b: Box) -> float:
    return min(a[3], b[3]) - max(a[1], b[1])


def _xov(a: Box, b: Box) -> float:
    return min(a[2], b[2]) - max(a[0], b[0])


class Finder:
    def __init__(self, pm: PageModel, o: FindOptions) -> None:
        self.pm, self.o = pm, o
        self.runs = pm.run_index()
        self.pages: list[P] = []
        self.cands: list[D] = []
        self.marks: list[D] = []
        self.sections: list[S] = []
        self.warn: list[tuple[str, D | None, str]] = []
        self.run_lines: dict[str, list[TLine]] = {}
        # lines of body text seen so far on each page: a numbered line that is not bold is a heading only among
        # the first lines of its page (set 9 PDF starts every section on a new page; set 8 numbers its labels)
        self.page_rank: dict[int, int] = {}

    # ------------------------------------------------------------------ 1. lines, boxes, order

    def tokens(self, ln: TLine) -> list[tuple[int, int, str]]:
        out = []
        for m in LEAD_RE.finditer(ln.view):
            s = m.group()
            if s.count(".") + s.count("_") + 3 * s.count("…") + 8 * s.count(TAB_LEADER) >= self.o.min_leader:
                out.append((m.start(), m.end(), "lead"))
        out += [(m.start(), m.end(), "mark") for m in MARK_RE.finditer(ln.view)]
        pua = PUA_RE.match(ln.view)
        if pua:
            out.append((pua.start(1), pua.end(1), "mark"))
        return sorted(out)

    def read(self) -> None:
        pos = 0
        for page in self.pm.pages:
            lines, geo = build_lines(page)
            p = P(page, lines, geo, first=pos)
            for ln in lines:
                ln.toks = self.tokens(ln)
                for at in ln.atoms:
                    self.run_lines.setdefault(at.run.id, []).append(ln)
            if geo:
                p.hor, p.ver = sh.ruled(page)
                bx = sh.boxes(page, p.hor, p.ver)
                p.leaf = [b for b in bx
                          if not any(o is not b and sh.inside(o, b) and sh.area(b) > 1.5 * sh.area(o) for o in bx)]
                p.empty = [b for b in p.leaf if not any(sh.centre_in(ln.box, b) for ln in lines)]  # type: ignore[arg-type]
                items: list[tuple[Box, object]] = [(ln.box, ln) for ln in lines] + [(b, b) for b in p.empty]  # type: ignore[misc]
                seq = [obj for _, obj in sh.reading_order(items)]
            else:
                seq = list(lines)
                p.col0 = [ln for ln in lines if ln.col == 0]
            for obj in seq:
                if isinstance(obj, TLine):
                    obj.pos = pos
                else:
                    p.boxpos[obj] = pos  # type: ignore[index]
                pos += 1
            self.pages.append(p)

    def ordered(self) -> list[tuple[P, TLine]]:
        return sorted(((p, ln) for p in self.pages for ln in p.lines), key=lambda t: t[1].pos)

    # ------------------------------------------------------------------ 2. roles and sections

    def heading_of(self, ln: TLine) -> tuple[str | None, str] | None:
        if ln.toks:
            return None
        full = ln.text.strip()
        lead_end = 0
        for at, st in zip(ln.atoms, ln.starts):
            if not at.run.bold:
                break
            lead_end = st + at.e - at.s
        lead = ln.text[:lead_end].strip().rstrip("(").strip()
        if lead:
            m = NUM.match(lead) or LET.match(lead)
            if m and WORD.search(m.group(2)):
                return m.group(1), m.group(2).strip()
        top = self.page_rank.get(ln.page, 0) < TOP_LINES
        if top and NUM_HEAD.match(full) and len(full.split()) <= 10 and full[-1] not in ".:,;":
            # a numbered heading that is not bold (set 9 PDF): "1. Wnioskodawca", "II. Wniosek o ..."
            m = NUM.match(full) or LET.match(full)
            if m and WORD.search(m.group(2)):
                return m.group(1).rstrip("."), m.group(2).strip()
        cand = lead or full
        letters = [ch for ch in cand if ch.isalpha()]
        if cand.endswith(".") or not letters or any(ch != ch.upper() for ch in letters):
            return None
        if (lead and len(letters) >= 6) or (len(letters) >= 10 and len(cand.split()) >= 2):
            return None, cand
        return None

    def wraps(self, head: TLine | None, ln: TLine) -> bool:
        """A line of one or two words right under a heading, not left of its text and not numbered, continues it,
        when it has the heading's style (bold, about the size) or the heading line runs nearly the full width."""
        if head is None or head.role != "heading" or ln.toks or head.box is None or ln.box is None or head.page != ln.page:
            return False
        t = ln.text.strip()
        height = head.box[3] - head.box[1]
        page = next((p.page for p in self.pages if p.page.number == head.page), None)
        full = bool(page and page.width and head.box[2] >= 0.6 * page.width)
        h_bold = bool(head.atoms) and all(a.run.bold for a in head.atoms)
        l_bold = bool(ln.atoms) and all(a.run.bold for a in ln.atoms)
        same_style = h_bold and l_bold and 0.6 * height <= ln.box[3] - ln.box[1] <= 1.3 * height
        if not (same_style or full):
            return False
        return (0 < len(t.split()) <= 2 and t[:1].isupper() and t[-1:] not in ".:;," and not NUM_HEAD.match(t + " X")
                and 0 <= ln.box[1] - head.box[3] <= height and ln.box[0] >= head.box[0] - 2)

    def roles(self) -> None:
        clause = instr = False
        cur: S | None = None
        prev: TLine | None = None
        for p, ln in self.ordered():
            t = ln.text.strip()
            regions = {a.run.region for a in ln.atoms}
            edge = p.geo and ln.box is not None and p.page.height and (
                ln.box[1] < 0.07 * p.page.height or ln.box[3] > 0.93 * p.page.height)
            if FURNITURE.search(t) or regions & {"header", "footer"} or (edge and PAGE_NO.match(t)):
                ln.role = "page_furniture"
                continue
            low = p.geo and ln.box is not None and p.page.height and ln.box[1] > 0.55 * p.page.height
            if "footnote" in regions or (ln.anchor or "").startswith("fn[") or (low and NOTE.match(t)):
                ln.role = "note"
                continue
            if CLAUSE_START.search(t):
                clause, ln.role = True, "clause"
                continue
            if cur is not None and cur.lines[-1] is prev and self.wraps(prev, ln):
                # "I. Wniosek o ... Rady Miasta" / "Zgierza": the heading goes on in a short line under it
                cur.lines.append(ln)
                cur.title = f"{cur.title} {t}"
                ln.role, ln.used = "heading", True
                prev = ln
                continue
            prev = ln
            head = self.heading_of(ln)
            self.page_rank[ln.page] = self.page_rank.get(ln.page, 0) + 1
            if clause:
                # the clause lasts until a heading of the form or a line that is only a leader (a signature line);
                # dots inside its sentences are not places to fill
                bare = len(ln.toks) == 1 and ln.toks[0][2] == "lead" and not WORD.search(
                    ln.text[:ln.toks[0][0]] + ln.text[ln.toks[0][1]:])
                if (head is not None and not CLAUSE_VOCAB.search(t)) or bare:
                    clause = False
                else:
                    ln.role = "clause"
                    continue
            bold_start = ln.atoms[0].run.bold
            if INSTR.search(t) and not bold_start and not OFFICE.search(t) and (
                    not ln.toks or all(k == "mark" and ln.view[a] in TICKED_CHARS for a, _, k in ln.toks)):
                ln.role = "instruction"
                continue
            if head is not None:
                cur = S(title=head[1], number=head[0], page=ln.page, pos=ln.pos, lines=[ln])
                cur.instr = instr = bool(INSTR_HEAD.search(head[1]))
                if cur.number is None and p.geo:
                    for o in p.lines:
                        ob, hb = o.box, ln.box
                        assert ob is not None and hb is not None
                        beside = (0 <= hb[0] - ob[2] <= 30
                                  and abs((ob[1] + ob[3]) / 2 - (hb[1] + hb[3]) / 2) <= 1.2 * (hb[3] - hb[1]))
                        if o is not ln and beside and o.role is None and LONE.match(o.text.strip()):
                            cur.number = LONE.match(o.text.strip()).group(1)  # type: ignore[union-attr]
                            cur.lines.insert(0, o)
                            o.role, o.used = "heading", True
                self.sections.append(cur)
                ln.role, ln.used = "heading", True
                continue
            if instr:
                ln.role = "instruction"
            elif LEGAL.search(t) and not ln.toks:
                ln.role = "legal_basis"

    def sec(self, pos: float) -> S | None:
        i = bisect.bisect_right([s.pos for s in self.sections], pos)
        return self.sections[i - 1] if i else None

    # ------------------------------------------------------------------ 3. places inside lines

    def lab(self, ln: TLine, a: int, b: int, how: str, score: float = 0.9) -> Lab | None:
        text, foot = clean(ln.text[a:b])
        if not text:
            return None
        return Lab(text, ln.parts(a, b), how, score, score, foot)

    def add(self, d: D) -> D:
        self.cands.append(d)
        if d.line is not None:
            d.line.made.append(d)
        return d

    def inline(self) -> None:
        for _p, ln in self.ordered():
            if ln.role is not None or not ln.toks:
                continue
            ln.used = True
            if any(k == "mark" for _, _, k in ln.toks):
                self.inline_marks(ln)
                continue
            leads = ln.toks
            if len(leads) == 1 and not WORD.search(ln.text[:leads[0][0]] + ln.text[leads[0][1]:]):
                a, b, _ = leads[0]
                self.add(D("leader", ln.page, ln.pos, box=ln.box_of(a, b), anchor=ln.anchor, parts=ln.parts(a, b),
                           line=ln, last=ln, bare=True))
                continue
            tail = ln.text[leads[-1][1]:]
            kind = "blank_in_sentence" if len(leads) >= 2 or WORD.search(tail) else "leader"
            how = "sentence" if kind == "blank_in_sentence" else "leader"
            prev = 0
            made: list[D] = []
            for a, b, _ in leads:
                made.append(self.add(D(kind, ln.page, ln.pos + a / 10000, box=ln.box_of(a, b), anchor=ln.anchor,
                                       parts=ln.parts(a, b), label=self.lab(ln, prev, a, how), line=ln, last=ln)))
                prev = b
            if made[0].label is None and len(made) == 1:
                made[0].label = self.lab(ln, prev, len(ln.text), how, 0.7)

    def inline_marks(self, ln: TLine) -> None:
        marks = [t for t in ln.toks if t[2] == "mark"]
        leads = [t for t in ln.toks if t[2] == "lead"]
        question = self.lab(ln, 0, marks[0][0], "question")
        for k, (a, b, _) in enumerate(marks):
            end = marks[k + 1][0] if k + 1 < len(marks) else len(ln.text)
            inner = [t for t in leads if b <= t[0] < end]
            stop = inner[0][0] if inner else end
            text, _foot = clean(ln.text[b:stop])
            blank: D | None = None
            if inner:
                la, lb, _ = inner[0]
                blank = self.add(D("leader", ln.page, ln.pos + la / 10000, box=ln.box_of(la, lb), anchor=ln.anchor,
                                   parts=ln.parts(la, lb), line=ln, last=ln,
                                   label=Lab(text, [], "leader", 0.9, 0.9) if text else None))
            m = self.add(D("box", ln.page, ln.pos + a / 10000, box=ln.box_of(a, b), anchor=ln.anchor,
                           parts=ln.parts(a, b), line=ln, geom=0.9 if ln.box else 0.7))
            m.opt = (text, ln.parts(b, stop), blank)
            m.question = question if k == 0 else None
            self.marks.append(m)

    # ------------------------------------------------------------------ 4. drawn places

    def example(self, p: P, b: Box, pos: float) -> bool:
        """A drawn box that only shows how to mark: it sits in an instruction."""
        s = self.sec(pos)
        if s is not None and s.instr:
            return True
        return any(ln.role == "instruction" and _yov(ln.box, b) > 0 and _xov(ln.box, b) > -40 for ln in p.lines)  # type: ignore[arg-type]

    def shapes(self) -> None:
        for p in self.pages:
            if not p.geo:
                continue
            n = p.page.number

            def gap_text(g: Box) -> str:
                return " ".join(ln.text for ln in p.lines if sh.centre_in(ln.box, g))  # type: ignore[arg-type]

            chains, rest = sh.combs(p.empty, gap_text)
            for ch in chains:
                box = sh.union(ch)
                if self.example(p, box, p.boxpos[ch[0]]):
                    continue
                w = ch[0][2] - ch[0][0]
                mask, parts, seps = "", [], False
                for a, b in zip(ch, ch[1:]):
                    mask += "_"
                    if b[0] - a[2] > 0.4 * w:
                        seps, t = True, ""
                        for ln in p.lines:
                            if sh.centre_in(ln.box, (a[2], a[1], b[0], a[3])) and not ln.used and ln.role is None:  # type: ignore[arg-type]
                                t += ln.text.strip()
                                parts += ln.parts(0, len(ln.text))
                                ln.used = True
                        mask += t or " "
                mask += "_"
                d = self.add(D("comb", n, p.boxpos[ch[0]], box=box, cells=len(ch), mask=mask if seps else None,
                               parts=parts, geom=0.95))
                h = box[3] - box[1]
                for ln in p.lines:
                    t = ln.text.strip()
                    if ln.used or ln.role is not None or not PATTERN.match(t) or _xov(ln.box, box) <= 0:  # type: ignore[arg-type]
                        continue
                    near = 0 <= ln.box[1] - box[3] <= 1.5 * h or 0 <= box[1] - ln.box[3] <= 1.5 * h  # type: ignore[index]
                    if near and re.sub(r"[A-Za-z]", "_", t) == mask:
                        d.mask, ln.used = t, True
                        d.parts += ln.parts(0, len(ln.text))
                        break
            for b in rest:
                w, h = b[2] - b[0], b[3] - b[1]
                if self.example(p, b, p.boxpos[b]):
                    continue
                if w <= 26 and h <= 26 and 0.6 <= w / h <= 1.7:
                    self.drawn_mark(p, b)
                elif w >= 30 and h >= 9:
                    self.add(D("cell", n, p.boxpos[b], box=b, geom=0.95))

    def labelled_cells(self) -> None:
        """A ruled cell with its label printed in its top left corner and room to write under or after it. Runs
        after the labels: a text that already answers for a place beside it ("Płeć:" left of two boxes) is taken."""
        for p in self.pages:
            if not p.geo:
                continue
            n = p.page.number
            for b in p.leaf:
                if b in p.empty or b[2] - b[0] < 60:
                    continue
                inside = [ln for ln in p.lines if sh.centre_in(ln.box, b)]  # type: ignore[arg-type]
                if len(inside) != 1:
                    continue
                ln = inside[0]
                lb = ln.box
                assert lb is not None
                corner = lb[0] - b[0] <= 12 and lb[1] - b[1] <= 0.35 * (b[3] - b[1])
                room = b[3] - lb[3] >= lb[3] - lb[1] or (
                    ln.text.rstrip().endswith(":") and b[2] - lb[2] >= max(60.0, 0.4 * (b[2] - b[0])))
                if ln.used or ln.role is not None or ln.toks or len(ln.text) > 60 or not (corner and room):
                    continue
                taken = any(o.box is not None and o.page == n and sh.inter(o.box, b) > 0.5 * sh.area(o.box)
                            for o in self.cands)
                lab = self.lab(ln, 0, len(ln.text), "same_cell", 0.8)
                if lab is not None and not taken:
                    ln.used = True
                    self.add(D("cell", n, ln.pos, box=b, label=lab, geom=0.85))

    def kinds(self) -> None:
        signed: set[int] = set()
        for d in self.cands:
            if d.label is not None and d.kind in ("leader", "line_block", "cell", "blank_in_sentence"):
                s = self.sec(d.pos)
                if OFFICE.search(d.label.text) or (s is not None and OFFICE_HEAD.search(s.title)):
                    # an office-use place: by its own label, or under a heading that gives the part to the office
                    d.kind = "office_use"
                elif SIGN.search(d.label.text) and (d.kind != "blank_in_sentence" or (
                        len(d.label.text.split()) <= 4 and SIGN_WORD.search(d.label.text))):
                    # a blank inside a sentence is a signature only when its own label is short ("Data ... Podpis
                    # ...", "...... (podpis)"); a long sentence that names a signature asks something else
                    d.kind = "signature"
                    if d.line is not None:
                        signed.add(id(d.line))
        for d in self.cands:
            # the date (or place and date) blank on the line of a signature is the date of the signature
            if d.kind == "blank_in_sentence" and d.label is not None and d.line is not None and id(d.line) in signed \
                    and SIGN_DATE.match(d.label.text.strip()):
                d.kind = "signature"

    def drawn_mark(self, p: P, b: Box) -> None:
        d = self.add(D("box", p.page.number, p.boxpos[b], box=b, geom=0.95))
        best: TLine | None = None
        for ln in p.lines:
            lb = ln.box
            assert lb is not None
            gap = lb[0] - b[2]
            if ln.role is None and _yov(lb, b) >= 0.4 * (lb[3] - lb[1]) and -2 <= gap <= 3 * (b[2] - b[0]):
                if best is None or gap < best.box[0] - b[2]:  # type: ignore[index]
                    best = ln
        if best is not None and not best.used:
            text, _foot = clean(best.text)
            d.opt = (text, best.parts(0, len(best.text)), None)
            best.used = True
        elif best is not None and len(best.made) == 1 and best.made[0].kind in ("leader", "blank_in_sentence") \
                and best.made[0].label is not None and not best.made[0].bare:
            blank = best.made[0]
            lab = blank.label
            assert lab is not None
            d.opt = (lab.text, lab.parts, blank)
            blank.kind, blank.label = "leader", Lab(lab.text, [], "leader", lab.score, lab.margin, lab.foot)
        d.line = best
        self.marks.append(d)

    def tables(self) -> None:
        carried: tuple[int, int, list[str], float, int] | None = None  # page, columns, header texts, pos, rows so far
        for p in self.pages:
            for ti, t in enumerate(p.page.tables):
                if not t.cells:
                    continue
                grid = {(r, c): cell for cell in t.cells for r in range(cell.r, cell.r + cell.rs)
                        for c in range(cell.c, cell.c + cell.cs)}
                ncols = max(c for _, c in grid) + 1
                nrows = max(r for r, _ in grid) + 1

                def text(cell) -> str:  # noqa: ANN001
                    return " ".join(self.runs[r][1].text for r in cell.runs).strip() if cell is not None else ""

                heads = [text(grid.get((0, c))) for c in range(ncols)]
                own = nrows >= 2 and sum(bool(WORD.search(h)) for h in heads) >= 2 and all(WORD.search(h) for h in heads)
                cont = (not own and carried is not None and ti == 0 and carried[0] == p.page.number - 1
                        and carried[1] == ncols)
                if cont:
                    heads = carried[2]  # type: ignore[index]
                at = p.first
                if not cont and not any(WORD.search(text(c)) for c in t.cells):
                    # a table of empty cells only is a drawn row of boxes: three or more in a row are one comb
                    for r in range(nrows):
                        row = sorted((c for c in t.cells if c.r == r), key=lambda c: c.c)
                        if len(row) >= 3:
                            self.add(D("comb", p.page.number, at + (ti + 1) / 1000 + r / 100000, box=row[0].box,
                                       anchor=row[0].anchor, cells=len(row), table=True, geom=0.9 if row[0].box else 0.7))
                    if all(sum(c.r == r for c in t.cells) >= 3 for r in range(nrows)):
                        carried = None
                        continue
                for cell in sorted(t.cells, key=lambda c: (c.r, c.c)):
                    lines = [ln for r in cell.runs for ln in self.run_lines.get(r, [])]
                    at = max([at] + [ln.pos for ln in lines])
                    if WORD.search(text(cell)) or (own and cell.r == 0):
                        continue
                    parts = [(r, 0, len(self.runs[r][1].text)) for r in cell.runs if self.runs[r][1].text.strip()]
                    for ln in lines:
                        ln.used = True
                        for made in ln.made:
                            if made in self.cands:
                                self.cands.remove(made)
                    lab: Lab | None = None
                    left = grid.get((cell.r, cell.c - 1))
                    if (own or cont) and WORD.search(heads[cell.c]):
                        hc = grid.get((0, cell.c)) if own else None
                        hparts = [(r, 0, len(self.runs[r][1].text)) for r in hc.runs] if hc is not None else []
                        lab = Lab(clean(heads[cell.c])[0] or heads[cell.c], hparts, "header", 0.8, 0.8)
                        for r in (hc.runs if hc is not None else []):
                            for ln in self.run_lines.get(r, []):
                                ln.used = True
                    elif left is not None and left is not cell and WORD.search(text(left)):
                        tx, foot = clean(text(left))
                        if tx:
                            lab = Lab(tx, [(r, 0, len(self.runs[r][1].text)) for r in left.runs], "left", 0.8, 0.8, foot)
                            for r in left.runs:
                                for ln in self.run_lines.get(r, []):
                                    ln.used = True
                    base = carried[4] if cont and carried else 0  # rows of the same table on earlier pages
                    pos = (carried[3] if cont and carried else at) + ((base + cell.r) * 100 + cell.c + 1) / 100000
                    self.add(D("cell", p.page.number, pos, box=cell.box, anchor=cell.anchor, parts=parts, label=lab,
                               table=True, geom=0.9 if cell.box else 0.7))
                if own or cont:
                    carried = (p.page.number, ncols, heads, carried[3] if cont and carried else at,
                               (carried[4] if cont and carried else 0) + nrows)
                else:
                    carried = None

    def widgets(self) -> None:
        for p in self.pages:
            for w in p.page.widgets:
                n = p.page.number
                if w.box is not None and any(o.box is not None and o.page == n and o.kind != "widget"
                                             and sh.inter(o.box, w.box) > 0.5 * sh.area(o.box) for o in self.cands):
                    # the widget lies over a place the paper draws (a box, a cell, a dotted line): that place is
                    # already a candidate with the paper's own label; a second one would duplicate the field
                    continue
                pos = float(p.first)
                if p.geo and w.box is not None and p.lines:
                    near = min(p.lines, key=lambda ln: abs(ln.box[1] - w.box[1]) + abs(ln.box[0] - w.box[0]) / 10)  # type: ignore[index]
                    pos = near.pos + 0.5
                name = (w.name or "").strip()
                self.add(D("widget", p.page.number, pos, box=w.box, anchor=w.anchor, widget=w.id, geom=1.0,
                           label=Lab(name, [], "widget_name", 0.7, 0.7) if name else None))

    # ------------------------------------------------------------------ 5. blocks and groups

    def blocks(self) -> None:
        by_page = {p.page.number: p for p in self.pages}
        prev: D | None = None
        for d in sorted([d for d in self.cands if d.bare], key=lambda d: d.pos):
            p = by_page[d.page]
            if prev is not None and prev.page == d.page and self.stacked(p, prev, d):
                prev.kind, prev.lines = "line_block", (prev.lines or 1) + 1
                prev.parts += d.parts
                if prev.box and d.box:
                    prev.box = sh.union([prev.box, d.box])
                prev.last = d.line
                self.cands.remove(d)
            else:
                prev = d

    def stacked(self, p: P, a: D, b: D) -> bool:
        if not p.geo:
            la, lb = a.last, b.line
            if la is None or lb is None or la not in p.col0 or lb not in p.col0:
                return False
            return p.col0.index(lb) - p.col0.index(la) == 1
        assert a.box is not None and b.box is not None and a.last is not None and a.last.box is not None
        last = a.last.box
        h = max(last[3] - last[1], 8.0)
        if _xov(last, b.box) < 0.5 * min(last[2] - last[0], b.box[2] - b.box[0]) or not -1 <= b.box[1] - last[3] <= 2.2 * h:
            return False
        for ln in p.lines:
            lb_ = ln.box
            assert lb_ is not None
            if ln.role != "page_furniture" and lb_[1] >= last[3] - 1 and lb_[3] <= b.box[1] + 1 and _xov(lb_, b.box) > 0:
                return False
        # a ruled line between two leaders is a row border of a table: two answers, not one long text
        return not any(last[3] + 1.5 < (r[1] + r[3]) / 2 < b.box[1] - 1.5 and r[0] <= b.box[2] and r[2] >= b.box[0]
                       for r in p.hor)

    def same_group(self, p: P, g: list[D], m: D) -> bool:
        last = g[-1]
        if last.page != m.page:
            return False
        if not p.geo or m.box is None or last.box is None:
            return m.line is not None and last.line is not None and 0 <= m.line.idx - last.line.idx <= 1
        if _yov(last.box, m.box) >= 0.5 * min(last.box[3] - last.box[1], m.box[3] - m.box[1]):
            return True
        for q in g:
            assert q.box is not None
            h = max(q.box[3] - q.box[1], 8.0)
            if abs(q.box[0] - m.box[0]) <= 4 and 0 <= m.box[1] - q.box[3] <= 2.5 * h:
                # strictly between the two boxes: their own borders are not a row border of a table
                ruled = any(q.box[3] + 1.5 < (r[1] + r[3]) / 2 < m.box[1] - 1.5 and r[0] <= m.box[2] and r[2] >= m.box[0]
                            for r in p.hor)
                if not ruled:
                    return True
        return False

    _NUMBERED = re.compile(r"\s*(\d{1,2})\s*[.)]\s+\S")

    def numbered_singles(self, chains: list[list[D]]) -> list[list[D]]:
        """Single boxes whose words are numbered 1., 2., 3. in reading order, on one page under one heading, are the
        options of one question even when other places sit between them (two columns of "1. first declaration",
        "2. new declaration", ...). Fewer than two, or a gap in the numbers, leaves them single."""
        out: list[list[D]] = []
        run: list[D] = []
        kept: list[list[D]] = []   # the chains of the run as they were, when it is not one question

        def num(d: D) -> int | None:
            m = self._NUMBERED.match(d.opt[0]) if d.opt and d.opt[0] else None
            return int(m.group(1)) if m else None

        def flush() -> None:
            nums = sorted(num(r) or 0 for r in run)
            if len(run) >= 2 and nums == list(range(1, len(run) + 1)):
                out.append(sorted(run, key=lambda r: num(r) or 0))
            else:
                out.extend(kept)
            run.clear()
            kept.clear()

        for ch in chains:
            if any(num(m) is None for m in ch) or (len(ch) > 1 and len({m.page for m in ch}) > 1):
                flush()
                out.append(ch)
                continue
            if run and not (run[-1].page == ch[0].page and self.sec(run[-1].pos) is self.sec(ch[0].pos)
                            and not {num(m) for m in ch} & {num(r) for r in run}):
                flush()
            run.extend(ch)
            kept.append(ch)
        flush()
        return out

    def groups(self) -> None:
        by_page = {p.page.number: p for p in self.pages}
        chains: list[list[D]] = []
        for m in sorted(self.marks, key=lambda d: d.pos):
            if m not in self.cands:
                continue
            if not (m.opt and m.opt[0]):
                self.warn.append(("LABEL_NOT_FOUND", m, "a box without words beside it"))
                continue
            if chains and self.same_group(by_page[m.page], chains[-1], m):
                chains[-1].append(m)
            else:
                chains.append([m])
        chains = self.numbered_singles(chains)
        for ch in chains:
            first = ch[0]
            if len(ch) == 1:
                text, parts, _blank = first.opt  # type: ignore[misc]
                first.label = Lab(text, parts, "question", 0.8, 0.8)
                continue
            boxes = [m.box for m in ch if m.box is not None]
            g = self.add(D("choice_group", first.page, first.pos - 0.00005, box=sh.union(boxes) if boxes else None,
                           anchor=first.anchor, geom=min(m.geom for m in ch), label=first.question))
            g.line = first.line
            for m in ch:
                m.group = g
                g.options.append((m.opt[0], m.opt[1], m, m.opt[2]))  # type: ignore[index]

    # ------------------------------------------------------------------ 6. labels

    def geo_label(self, p: P, d: D) -> tuple[TLine, str, float, float] | None:
        cb = d.box
        assert cb is not None
        others = [o.box for o in self.cands if o is not d and o.page == d.page and o.box is not None and o.group is not d]
        found: list[tuple[float, TLine, str]] = []
        for ln in p.lines:
            if ln.used or ln.role is not None or ln.toks or not WORD.search(ln.text):
                continue
            lb = ln.box
            assert lb is not None
            lh = lb[3] - lb[1]
            sc: float | None = None
            how = ""
            if _yov(lb, cb) >= 0.4 * min(lh, cb[3] - cb[1]) and lb[2] <= cb[0] + 2:
                dist = max(0.0, cb[0] - lb[2])
                between = (lb[2] + 1, max(lb[1], cb[1]), cb[0] - 1, min(lb[3], cb[3]))
                if dist <= 320 and not any(sh.inter(o, between) > 0 for o in others):
                    ruled = any(between[0] < (v[0] + v[2]) / 2 < between[2] and v[1] <= between[3] and v[3] >= between[1]
                                for v in p.ver)
                    sc, how = 0.9 - dist / 800 - (0.1 if ruled else 0.0), "left"
            elif lb[1] >= cb[3] - 2 and lb[1] - cb[3] <= 14 and _xov(lb, cb) > 0 and CAPTION.match(ln.text):
                sc, how = 0.85 - (lb[1] - cb[3]) / 100, "leader"
            elif lb[3] <= cb[1] + 2 and cb[1] - lb[3] <= 30 and (_xov(lb, cb) > 0 or abs(lb[0] - cb[0]) <= 20):
                between = (max(lb[0], cb[0]), lb[3] + 1, min(lb[2], cb[2]), cb[1] - 1)
                if not any(sh.inter(o, between) > 0 for o in others):
                    ruled = any(between[1] < (r[1] + r[3]) / 2 < between[3] and r[0] <= between[2] and r[2] >= between[0]
                                for r in p.hor)
                    sc, how = 0.7 - (cb[1] - lb[3]) / 100 - (0.45 if ruled else 0.0), "above"
            if sc is not None:
                found.append((sc + (0.05 if ln.text.rstrip().endswith(":") else 0.0), ln, how))
        found.sort(key=lambda f: -f[0])
        if not found or found[0][0] < 0.3:
            return None
        margin = found[0][0] - found[1][0] if len(found) > 1 else found[0][0]
        return found[0][1], found[0][2], found[0][0], margin

    def flow_label(self, p: P, d: D) -> tuple[TLine, str, float, float] | None:
        first, last = d.line, d.last or d.line
        if first is None or last is None or first not in p.col0 or last not in p.col0:
            return None
        i, j = p.col0.index(first), p.col0.index(last)
        nxt = p.col0[j + 1] if j + 1 < len(p.col0) else None
        if nxt is not None and not nxt.used and nxt.role is None and not nxt.toks and CAPTION.match(nxt.text) \
                and d.kind != "choice_group":
            return nxt, "leader", 0.85, 0.85
        prv = p.col0[i - 1] if i > 0 else None
        if prv is not None and not prv.used and prv.role is None and not prv.toks and WORD.search(prv.text) \
                and len(prv.text) <= 90:
            return prv, "above", 0.6, 0.6
        return None

    def labels(self) -> None:
        by_page = {p.page.number: p for p in self.pages}
        seen: set[int] = set()
        for d in sorted(self.cands, key=lambda d: d.pos):
            s = self.sec(d.pos)
            if d.label is None and d.group is None and not (d.kind == "box" and d in self.marks) and not d.table:
                p = by_page[d.page]
                hit = self.geo_label(p, d) if (p.geo and d.box is not None) else self.flow_label(p, d)
                if hit is not None:
                    ln, how, score, margin = hit
                    lab = self.lab(ln, 0, len(ln.text), "question" if d.kind == "choice_group" else how, score)
                    if lab is not None:
                        lab.margin = margin
                        d.label, ln.used = lab, True
                        if margin < 0.05:
                            self.warn.append(("LOW_CONFIDENCE", d, "two texts are equally near; the label is the first of them"))
            if d.label is None and d.group is None and not (d.kind == "box" and d in self.marks):
                if s is not None and id(s) not in seen:
                    # the first place under a heading that has no text of its own answers to the heading
                    d.label = Lab(s.title, [], "header", 0.5, 0.0)
                else:
                    self.warn.append(("AMBIGUOUS_GROUP" if d.kind == "choice_group" else "LABEL_NOT_FOUND", d,
                                      "no question above or beside the boxes" if d.kind == "choice_group"
                                      else "no text that this place belongs to"))
            if s is not None and d.group is None:
                seen.add(id(s))

    # ------------------------------------------------------------------ output

    def refs(self, parts: Parts) -> tuple[list[str], list[Span]]:
        by: dict[str, list[tuple[int, int]]] = {}
        for rid, s, e in parts:
            if e > s:
                by.setdefault(rid, []).append((s, e))
        runs: list[str] = []
        spans: list[Span] = []
        for rid, rs in by.items():
            text = self.runs[rid][1].text
            cov = {i for s, e in rs for i in range(s, e)}
            if all(i in cov for i, ch in enumerate(text) if not ch.isspace()):
                runs.append(rid)
            else:
                spans += [Span(run=rid, start=s, end=e) for s, e in sorted(set(rs))]
        return runs, spans

    def place(self, d: D) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if d.box is not None:
            b = ModelBox.from_raw(*d.box)
            if b is not None and b[2] > b[0] and b[3] > b[1]:
                out["box"] = b
        if d.anchor:
            out["anchor"] = d.anchor
        if not out:
            out["anchor"] = f"page[{d.page}]"
        return out

    def output(self) -> FinderOutput:
        claimed: dict[str, set[int]] = {}

        def claim(parts: Parts) -> None:
            for rid, s, e in parts:
                claimed.setdefault(rid, set()).update(range(s, e))

        self.sections.sort(key=lambda s: s.pos)
        numbers: dict[str, str] = {}
        sections: list[Section] = []
        for i, s in enumerate(self.sections, 1):
            s.id = f"s{i}"
            parts = [pt for ln in s.lines for pt in ln.parts(0, len(ln.text))]
            claim(parts)
            parent = None
            if s.number and "." in s.number:
                parent = numbers.get(s.number.rsplit(".", 1)[0])
            if s.number:
                numbers[s.number] = s.id
            kw: dict[str, Any] = {"id": s.id, "page": s.page, "title": s.title, "runs": list(dict.fromkeys(r for r, _, _ in parts))}
            if s.number:
                kw["number"] = s.number
            if parent:
                kw["parent"] = parent
            sections.append(Section(**kw))

        cands = sorted(self.cands, key=lambda d: d.pos)
        for i, d in enumerate(cands, 1):
            d.id = f"c{i}"
        out: list[Candidate] = []
        for d in cands:
            runs, spans = self.refs(d.parts)
            claim(d.parts)
            kw = {"id": d.id, "kind": d.kind, "page": d.page, **self.place(d), "runs": runs, "spans": spans}
            for key in ("cells", "lines", "mask", "widget"):
                if getattr(d, key) is not None and (key != "lines" or d.kind == "line_block" or d.lines):
                    kw[key] = getattr(d, key)
            used = [rid for rid, _, _ in d.parts]
            foot: list[str] = []
            score = 0.0
            if d.label is not None:
                lr, ls = self.refs(d.label.parts)
                claim(d.label.parts)
                used += [rid for rid, _, _ in d.label.parts]
                kw["label"] = Label(text=d.label.text, runs=lr, how=d.label.how, spans=ls,  # type: ignore[arg-type]
                                    margin=round(min(1.0, max(0.0, d.label.margin)), 2))
                foot, score = d.label.foot, d.label.score
            options = []
            for text, parts, mark, blank in d.options:
                orr, osp = self.refs(parts)
                claim(parts)
                used += [rid for rid, _, _ in parts]
                okw: dict[str, Any] = {"text": text, "runs": orr, "spans": osp, "mark": mark.id}
                if blank is not None:
                    okw["blank"] = blank.id
                options.append(ChoiceOption(**okw))
            if options:
                kw["options"] = options
                score = max(score, 0.5)
            if d.group is not None:
                kw["group"] = d.group.id
                score = 0.8
            s = self.sec(d.pos)
            if s is not None:
                kw["section"] = s.id
            if foot:
                kw["footnotes"] = foot
            text_conf = min([self.runs[rid][1].conf for rid in used] or [1.0])
            kw["conf"] = Confidence(geometry=d.geom, label=round(min(1.0, max(0.0, score)), 2), text=text_conf)
            out.append(Candidate(**kw))

        roles: dict[str, str] = {}
        for pg in self.pm.pages:
            for r in pg.runs:
                need = {i for i, ch in enumerate(r.text) if not ch.isspace()}
                if need and need <= claimed.get(r.id, set()):
                    continue
                found = [ln.role for ln in self.run_lines.get(r.id, []) if ln.role not in (None, "heading")]
                roles[r.id] = found[0] if found else "body"

        order = list(dict.fromkeys(a.run.id for _p, ln in self.ordered() for a in ln.atoms))
        order += [r.id for pg in self.pm.pages for r in pg.runs if r.id not in set(order)]

        warnings: list[Warning] = []
        for code, d, detail in self.warn:
            if d is not None and d not in cands:
                continue
            wk: dict[str, Any] = {"code": code, "detail": detail}
            if d is not None:
                wk.update(page=d.page, candidate=d.id, **self.place(d))
            warnings.append(Warning(**wk))
        if not out:
            warnings.append(Warning(code="NOT_A_FORM", detail="no place to fill was found on any page"))
        result = FinderOutput(input=InputRef(sha256=self.pm.source.sha256, format=self.pm.source.format),
                              order=order, sections=sections, candidates=out, roles=roles, warnings=warnings)  # type: ignore[arg-type]
        result.check_spans(self.pm)
        return result


def run(pm: PageModel, o: FindOptions) -> FinderOutput:
    f = Finder(pm, o)
    f.read()
    f.roles()
    f.inline()
    f.shapes()
    f.tables()
    f.widgets()
    f.blocks()
    f.groups()
    f.labels()
    f.labelled_cells()
    f.kinds()
    return f.output()
