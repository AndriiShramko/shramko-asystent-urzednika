"""Weak pages, numbered lines, and the merge of a model's line roles into the page model (ORDER M2 step 3).

The merge is additive and only on pages of origin "ocr": a label line gets a synthetic dotted leader run to its
right (the finder's text-leader rule labels it by geometry), an option line gets a box character run before it,
a heading line becomes bold. A line number outside the page, a line that already has a leader or a box, or a
line too close to the right edge is skipped. Synthetic runs have ids "v<page>_<n>", so the sidecar can tell them.
Printed text is never changed and never added: an instruction printed on the page can only ever mark one of the
page's own lines, it cannot add a field, a value or a validator.
"""
from __future__ import annotations

import difflib
import re

from app.find._core import BOX_CHARS, INSTR, LEAD_RE, TICKED_CHARS
from app.find._text import JOIN_GAP, TLine, build_lines
from app.model.page import Page, PageModel, Run

MIN_LABEL_WORD = 2      # a label line needs at least this many letters
MIN_LEADER_PT = 36.0    # a synthetic leader is at least this wide, or the line is skipped
WEAK_LABELLED = 3       # fewer labelled places than this on an OCR page makes it weak
WEAK_CONF = 0.6
MAX_LABEL_WORDS = 16    # a longer line is a sentence, not the name of a place
# A line that talks to a machine is never a label: printed instructions cannot add a field (prompt injection).
INJECTION = re.compile(r"zignoruj|ignoruj|\bignore\b|instrukcj|poprzedni\w*\s+polece|\bprompt|\bsystem\b|zwr[óo]ć\s+je"
                       r"|dodaj\s+(?:do\s+odpowiedzi|pol[ea])|\bhas[łl]o\b|\bPIN\b", re.IGNORECASE)


def page_lines(page: Page) -> list[TLine]:
    """The lines the model sees, in the finder's own reading order; empty lines are left out."""
    lines, _ = build_lines(page)
    return [ln for ln in lines if ln.text.strip()]


def numbered(page: Page) -> list[str]:
    return [" ".join(ln.text.split()) for ln in page_lines(page)]


def weak_pages(model: PageModel, finder, max_pages: int, trigger: str = "weak") -> list[int]:
    """Pages of origin "ocr" with ink where the rules are weak: fewer than 3 labelled places, an empty finder, or a
    mean OCR word confidence below 0.6. At most `max_pages`, in page order. `trigger="all"`: every OCR page."""
    if trigger == "all":
        return [p.number for p in model.pages if p.origin == "ocr" and p.ink and p.runs][:max_pages]
    labelled: dict[int, int] = {}
    for c in finder.candidates:
        if c.label is not None:
            labelled[c.page] = labelled.get(c.page, 0) + 1
    out = []
    for p in model.pages:
        if p.origin != "ocr" or not p.ink or not p.runs:
            continue
        conf = sum(r.conf for r in p.runs) / len(p.runs)
        if not finder.candidates or labelled.get(p.number, 0) < WEAK_LABELLED or conf < WEAK_CONF:
            out.append(p.number)
        if len(out) >= max_pages:
            break
    return out


def _has_place(text: str) -> bool:
    if any(ch in text for ch in BOX_CHARS + TICKED_CHARS):
        return True
    return any(len(m.group()) >= 8 for m in LEAD_RE.finditer(text))


def _letters(text: str) -> int:
    return sum(ch.isalpha() for ch in text)


MIN_FIX_RATIO = 0.6     # the model's spelling replaces an OCR line only when at most ~40 % of it changes


def _fixes(lines: list[TLine], fixes) -> dict[str, Run | None]:
    """Run id -> corrected run (or None: merged into the line's first run). Only whole-word runs, ratio >= 0.6,
    and never a text that brings in machine-talk the printed line did not have."""
    out: dict[str, Run | None] = {}
    for n, text in fixes or []:
        if not (isinstance(n, int) and 1 <= n <= len(lines)) or not isinstance(text, str):
            continue
        ln = lines[n - 1]
        old = " ".join(ln.text.split())
        new = " ".join(text.split())
        if not new or new == old or (INJECTION.search(new) and not INJECTION.search(old)) or _has_place(new):
            continue
        if difflib.SequenceMatcher(None, old.lower(), new.lower(), autojunk=False).ratio() < MIN_FIX_RATIO:
            continue
        if any(a.s != 0 or a.e != len(a.run.text) or a.run.id in out for a in ln.atoms):
            continue
        words = new.split()
        if len(words) == len(ln.atoms):
            for a, w in zip(ln.atoms, words):
                out[a.run.id] = a.run.model_copy(update={"text": w})
        elif ln.box is not None:
            first = ln.atoms[0].run
            out[first.id] = first.model_copy(update={"text": new, "box": list(ln.box)})
            for a in ln.atoms[1:]:
                out[a.run.id] = None
    return out


REQUIRE_EVIDENCE = False   # lab switch: keep a label only when our raster shows a line or a box beside or below it


def _evidence(page: Page, ln: TLine) -> bool:
    """A drawn line (solid or dotted) or a box starts right of the label on its row, or lies just below it."""
    x0, y0, x1, y1 = ln.box
    h = max(1.0, y1 - y0)
    for b in [el.box for el in page.lines] + [el.box for el in page.rects]:
        bx0, by0, bx1, by1 = b
        same_row = by1 >= y0 - 0.6 * h and by0 <= y1 + 0.6 * h and bx1 > x1 - 2 and bx0 < x1 + 320
        below = by0 >= y1 - 0.2 * h and by0 <= y1 + 1.8 * h and bx1 > x0 and bx0 < x1 + 40
        if same_row or below:
            return True
    return False


def merge_page(page: Page, roles: dict[str, list[int]]) -> tuple[Page, int]:
    """Return the page with synthetic marks and the number of marks added."""
    if page.origin != "ocr":
        return page, 0
    lines = page_lines(page)
    if not lines:
        return page, 0
    fixed = _fixes(lines, roles.get("fix"))
    right_edge = (page.width or 0) * 0.95
    new_runs: list[Run] = []
    bold_ids: set[str] = set()
    k = 0
    for n in roles.get("heading", []):
        ln = lines[n - 1]
        if _has_place(ln.text) or _letters(ln.text) < 3 or INJECTION.search(ln.text):
            continue
        bold_ids.update(a.run.id for a in ln.atoms)
    for kind in ("label", "option"):
        for n in roles.get(kind, []):
            ln = lines[n - 1]
            if ln.box is None or _has_place(ln.text) or _letters(ln.text) < MIN_LABEL_WORD:
                continue
            if len(ln.text.split()) > MAX_LABEL_WORDS or INJECTION.search(ln.text):
                continue
            if kind == "option" and INSTR.search(ln.text):   # "Pola wyboru oznaczaj X" is advice, not an option
                continue
            if kind == "label" and REQUIRE_EVIDENCE and not _evidence(page, ln):
                continue
            x0, y0, x1, y1 = ln.box
            last = ln.atoms[-1].box or ln.box
            h = max(1.0, last[3] - last[1])
            size = max(a.run.size or h for a in ln.atoms)
            if kind == "label":
                start = x1 + min(0.5 * size, JOIN_GAP * size * 0.8)
                end = right_edge
                # stop before the next line of the same row, if one stands to the right
                for other in lines:
                    if other is ln or other.box is None:
                        continue
                    ov = min(other.box[3], y1) - max(other.box[1], y0)
                    if ov > 0.5 * h and other.box[0] > x1:
                        end = min(end, other.box[0] - 0.5 * size)
                if end - start < MIN_LEADER_PT:
                    continue
                dots = max(8, int((end - start) / 2.2))
                box = [round(start, 2), round(last[1], 2), round(end, 2), round(last[3], 2)]
                text = "." * dots
            else:
                first = ln.atoms[0].box or ln.box
                w = 0.8 * h
                if first[0] - w - 0.3 * h < 0:
                    continue
                box = [round(first[0] - w - 0.3 * h, 2), round(first[1], 2), round(first[0] - 0.3 * h, 2), round(first[3], 2)]
                text = BOX_CHARS[0]
            k += 1
            run, _ = Run.safe(page.number, id=f"v{page.number}_{k}", text=text, box=box, size=round(size, 2), conf=1.0)
            if run is not None:
                new_runs.append(run)
    if not new_runs and not bold_ids and not fixed:
        return page, 0
    runs = []
    for r in page.runs:
        if r.id in fixed:
            r = fixed[r.id]
            if r is None:
                continue
        runs.append(r.model_copy(update={"bold": True}) if r.id in bold_ids else r)
    return page.model_copy(update={"runs": runs + new_runs}), len(new_runs) + (1 if bold_ids else 0) + (1 if fixed else 0)


def merge(model: PageModel, answers: dict[int, dict[str, list[int]]]) -> tuple[PageModel, int]:
    pages, added = [], 0
    for p in model.pages:
        if p.number in answers:
            p2, n = merge_page(p, answers[p.number])
            pages.append(p2)
            added += n
        else:
            pages.append(p)
    return model.model_copy(update={"pages": pages}), added
