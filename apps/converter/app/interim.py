"""INTERIM stand-in for the finder (WP-F3) and the understanding step (WP-F4).

`brief_from_pages(page_model)` builds the smallest honest brief: the title of the paper (found by a plain rule) and
nothing else. Every other statement of the brief is `not_found`, there is no matter section and no field: this
module never invents one. WP-F3 and WP-F4 replace it; `app.pipeline` is the only caller.

`NOT_READ_WARNING` is the sidecar warning that tells the official the fields of the matter are not read yet.
"""
from __future__ import annotations

import re

from app.model.brief import Addressee, Applicants, Brief, Declarations
from app.model.common import Evidence, InputRef, Stated
from app.model.page import Page, PageModel, Run

NOT_READ_CODE = "BRIEF_NOT_READ"
NOT_READ_WARNING = {
    "code": NOT_READ_CODE,
    "detail": "Pola sprawy nie zostały jeszcze odczytane z tego dokumentu: formularz zawiera tytuł dokumentu i "
              "standardowe sekcje. Pola dotyczące sprawy trzeba uzupełnić ręcznie.",
}

# Page furniture and the lines around a title that are never one (design 6.4.3 "PAGE_FURNITURE", the place-and-date
# line, the addressee block, leader lines, hints in brackets, labels that end with a colon).
_FURNITURE = re.compile(
    r"""^\s*(
        zał(ącznik|\.)\s*(nr|do)\b.*
      | strona\s+\d+.*
      | \d+\s*(/|z)\s*\d+
      | \d+
      | [\w .\-ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]{2,40},\s*(dnia\b.*|\d{1,2}[.\-/ ]\d{1,2}[.\-/ ]\d{2,4}.*)
      | (miejscowość|data|dnia|nr\s+sprawy|znak\s+sprawy)\b.*
      | (urząd|wójt|burmistrz|prezydent|starosta|starostwo|gmina|miasto|powiat|do\s+(wójta|burmistrza|prezydenta|starosty))\b.*
      | \(.*\)\W*
      | [^\n]*:
      | [.\s_\-…]+
    )\s*$""",
    re.IGNORECASE | re.VERBOSE,
)
_LEADER = re.compile(r"(\.{3,}|…|_{3,})")
# What a Polish form calls itself: a short line that starts with one of these is preferred as the title.
_KIND = re.compile(
    r"^\s*(wniosek|wnioski|deklaracja|zgłoszenie|oświadczenie|zawiadomienie|informacja|formularz|karta|podanie|"
    r"zaświadczenie|zapytanie|zlecenie|skarga|odwołanie|ankieta|rejestr)\b",
    re.IGNORECASE,
)
_NUMBERED = re.compile(r"^\s*([IVX]+|\d+)[.)]\s")  # the heading of a next section, not a continuation
_LOOKAHEAD_RUNS = 60  # a heading is among the first runs of a page


def _is_furniture(text: str) -> bool:
    t = text.strip()
    return not t or bool(_FURNITURE.match(t)) or bool(_LEADER.search(t) and len(_LEADER.sub("", t).strip()) < 25)


def _weight(run: Run) -> float:
    """Visual weight of a run: its font size (or the height of its box), a bold run counts a little more."""
    size = run.size or ((run.box[3] - run.box[1]) if run.box else 0.0)
    return size * (1.05 if run.bold else 1.0)


def _continues(prev: Run, nxt: Run, top: Run) -> bool:
    """A heading may wrap onto the next line(s): the next run has the same look and sits directly below."""
    if abs(_weight(nxt) - _weight(top)) > 0.6 or nxt.bold != top.bold or _NUMBERED.match(nxt.text) or _KIND.match(nxt.text):
        return False
    if prev.box is None or nxt.box is None:
        # a flow paragraph: a bold heading goes on in a second bold paragraph that starts in lower case ("o ...")
        return top.bold and nxt.text.strip()[:1].islower()
    size = prev.size or (prev.box[3] - prev.box[1])
    return 0 <= nxt.box[1] - prev.box[3] <= 0.8 * size or abs(nxt.box[1] - prev.box[1]) <= 0.3 * size


def _heading(page: Page) -> tuple[str, list[Run]] | None:
    runs = [r for r in page.runs if not _is_furniture(r.text)][:_LOOKAHEAD_RUNS]
    if not runs:
        return None
    named = [r for r in runs if _KIND.match(r.text) and len(r.text.strip()) <= 120]
    pool = named or runs[:14]
    top = max(pool, key=lambda r: (round(_weight(r), 1), -runs.index(r)))
    group = [top]
    for nxt in runs[runs.index(top) + 1: runs.index(top) + 3]:
        if not _continues(group[-1], nxt, top):
            break
        group.append(nxt)
    return " ".join(r.text.strip() for r in group), group


def _evidence(page: Page, runs: list[Run], text: str) -> Evidence:
    boxes = [r.box for r in runs if r.box is not None]
    if boxes:
        box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
        return Evidence(page=page.number, box=box, runs=[r.id for r in runs], quote=text)
    return Evidence(page=page.number, anchor=runs[0].anchor, runs=[r.id for r in runs], quote=text)


def find_title(model: PageModel) -> Stated:
    for page in model.pages:
        if not page.runs:
            continue
        found = _heading(page)
        if found is None:
            continue
        text = re.sub(r"\s+", " ", found[0]).strip()
        if text:
            return Stated(status="stated", value=text, evidence=[_evidence(page, found[1], text)])
        break  # the first page with text has no usable heading: do not look for one further in
    return Stated(status="not_found")


def brief_from_pages(model: PageModel) -> Brief:
    """The interim brief: the title and standard parts only."""
    missing = Stated(status="not_found")
    return Brief(
        input=InputRef(sha256=model.source.sha256, format=model.source.format),
        title=find_title(model),
        addressee=Addressee(status="not_found"),
        applicants=Applicants(status="not_found"),
        declarations=Declarations(clause=missing),
        fee=missing,
        legal_basis=missing,
    )
