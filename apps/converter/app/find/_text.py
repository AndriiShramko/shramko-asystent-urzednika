"""Text layer of the finder: runs become atoms, atoms become lines; every character keeps its run and offset.

A reader cuts a run where the font changes ("❑ p" + "ies"), and a paragraph of a flow file is one run with tabs
and line breaks inside. The finder therefore works on lines: a stretch of text that is read together. A line
knows which characters of which run it is made of, so a mark, a label or an option is reported as whole runs or
as spans (run, start, end) of the page model.

Geometry page (every run has a box): atoms on one row whose gap is small are one line. Otherwise (flow) every
atom is its own line in the file's order; atoms after a tab are side columns of the same row (col > 0).
Positions inside a run that was cut by the finder are estimated in proportion to the characters: an estimate for
ordering and for nearness, never reported as a measured box of a run.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.model.page import Page, Run

Box = tuple[float, float, float, float]

_SPLIT = re.compile(r"\n|\t| {4,}")
_SPLIT_KEEP_TABS = re.compile(r"\n| {4,}")
JOIN_GAP = 0.75      # gap / font size up to which two atoms of a row are one line
JOIN_GAP_MIN = 5.0   # ... and never less than this many points
SPACE_GAP = 0.15     # gap / font size above which a space is written between two joined atoms
TAB_LEADER = "\x00"  # stands in the view of a line for a tab whose leader the source declares


@dataclass
class Atom:
    run: Run
    s: int
    e: int
    box: Box | None
    col: int
    nl: int
    seq: int

    @property
    def size(self) -> float:
        if self.run.size:
            return float(self.run.size)
        return (self.box[3] - self.box[1]) if self.box else 10.0


@dataclass(eq=False)
class TLine:
    page: int
    atoms: list[Atom]
    text: str = ""
    view: str = ""
    starts: list[int] = field(default_factory=list)
    box: Box | None = None
    row: tuple[int, int] = (0, 0)
    col: int = 0
    idx: int = 0
    pos: int = -1
    role: str | None = None
    used: bool = False
    toks: list[tuple[int, int, str]] = field(default_factory=list)
    section: object | None = None
    made: list[object] = field(default_factory=list)

    @property
    def anchor(self) -> str | None:
        return self.atoms[0].run.anchor

    @property
    def size(self) -> float:
        return max(a.size for a in self.atoms)

    def parts(self, a: int, b: int) -> list[tuple[str, int, int]]:
        """Characters [a, b) of the line as (run id, start, end) in the runs' own text; white space trimmed."""
        while a < b and self.text[a].isspace():
            a += 1
        while b > a and self.text[b - 1].isspace():
            b -= 1
        out: list[tuple[str, int, int]] = []
        for at, st in zip(self.atoms, self.starts):
            lo, hi = max(a, st), min(b, st + at.e - at.s)
            if lo < hi:
                out.append((at.run.id, at.s + lo - st, at.s + hi - st))
        return out

    def box_of(self, a: int, b: int) -> Box | None:
        """Estimated place of characters [a, b): exact when they are whole atoms, in proportion otherwise."""
        if self.box is None:
            return None
        xs: list[float] = []
        ys: list[float] = []
        for at, st in zip(self.atoms, self.starts):
            n = at.e - at.s
            lo, hi = max(a, st), min(b, st + n)
            if lo < hi and at.box is not None:
                w = at.box[2] - at.box[0]
                xs += [at.box[0] + w * (lo - st) / n, at.box[0] + w * (hi - st) / n]
                ys += [at.box[1], at.box[3]]
        if not xs:
            return self.box
        return (round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2))


def _trim(seg: str, keep_tabs: bool) -> tuple[int, int]:
    chars = " \xa0\r\n" if keep_tabs else None
    left = len(seg) - len(seg.lstrip(chars))
    right = len(seg.rstrip(chars))
    return left, right


def _atoms(run: Run, seq: int) -> list[Atom]:
    text = run.text
    keep_tabs = run.leader in ("dots", "underscores")
    rows = text.split("\n")
    widest = max((len(r) for r in rows), default=1) or 1
    out: list[Atom] = []
    i, col, nl, row_start = 0, 0, 0, 0
    marks = list((_SPLIT_KEEP_TABS if keep_tabs else _SPLIT).finditer(text)) + [None]
    for m in marks:
        end = m.start() if m else len(text)
        seg = text[i:end]
        left, right = _trim(seg, keep_tabs)
        if right > left:
            s, e = i + left, i + right
            box: Box | None = None
            if run.box is not None:
                x0, y0, x1, y1 = run.box
                if len(rows) == 1 and s == 0 and e == len(text):
                    box = (x0, y0, x1, y1)
                else:
                    w, h = x1 - x0, (y1 - y0) / len(rows)
                    box = (x0 + w * (s - row_start) / widest, y0 + h * nl,
                           x0 + w * (e - row_start) / widest, y0 + h * (nl + 1))
            out.append(Atom(run, s, e, box, col, nl, seq))
        if m is not None:
            if m.group() == "\n":
                nl, col, row_start = nl + 1, 0, m.end()
            else:
                col += 1
            i = m.end()
    return out


def _line(page: int, atoms: list[Atom], geo: bool) -> TLine:
    ln = TLine(page=page, atoms=atoms)
    prev: Atom | None = None
    for at in atoms:
        seg = at.run.text[at.s:at.e]
        if prev is not None and geo and prev.box and at.box:
            gap = at.box[0] - prev.box[2]
            if gap > SPACE_GAP * max(prev.size, at.size) and not ln.text.endswith(" "):
                ln.text += " "
        ln.starts.append(len(ln.text))
        ln.text += seg
        prev = at
    declared = any(a.run.leader in ("dots", "underscores") for a in atoms)
    ln.view = ln.text.replace("\t", TAB_LEADER) if declared else ln.text
    boxes = [a.box for a in atoms if a.box is not None]
    if boxes and len(boxes) == len(atoms):
        ln.box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    ln.col = atoms[0].col
    ln.row = (atoms[0].seq, atoms[0].nl)
    return ln


def build_lines(page: Page) -> tuple[list[TLine], bool]:
    """Lines of one page and whether the page is worked by geometry (every run has a box)."""
    atoms = [a for seq, r in enumerate(page.runs) for a in _atoms(r, seq)]
    geo = bool(atoms) and all(a.box is not None for a in atoms) and page.width is not None
    lines: list[TLine] = []
    if not geo:
        lines = [_line(page.number, [a], False) for a in atoms]
    else:
        atoms.sort(key=lambda a: ((a.box[1] + a.box[3]) / 2, a.box[0]))  # type: ignore[index]
        rows: list[list[Atom]] = []
        for a in atoms:
            for row in reversed(rows[-6:]):
                ref = row[0]
                ov = min(a.box[3], ref.box[3]) - max(a.box[1], ref.box[1])  # type: ignore[index]
                low = min(a.box[3] - a.box[1], ref.box[3] - ref.box[1])  # type: ignore[index]
                if low > 0 and ov >= 0.5 * low:
                    row.append(a)
                    break
            else:
                rows.append([a])
        for k, row in enumerate(rows):
            row.sort(key=lambda a: (a.box[0], a.seq))  # type: ignore[index]
            cur = [row[0]]
            for a in row[1:]:
                p = cur[-1]
                gap = a.box[0] - p.box[2]  # type: ignore[index]
                if gap <= max(JOIN_GAP * max(p.size, a.size), JOIN_GAP_MIN):
                    cur.append(a)
                else:
                    lines.append(_line(page.number, cur, True))
                    lines[-1].row = (k, 0)
                    cur = [a]
            lines.append(_line(page.number, cur, True))
            lines[-1].row = (k, 0)
    for i, ln in enumerate(lines):
        ln.idx = i
    return lines, geo
