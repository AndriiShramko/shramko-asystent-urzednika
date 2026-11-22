"""One document as the rules see it: runs in reading order with their roles, sections, candidates, and the small
text operations every rule shares (numbering, crossed-out alternatives, sentence case, keys)."""
from __future__ import annotations

import math
import re
import unicodedata
from typing import Any, Iterable

from app import lexicon
from app.model.candidate import Candidate, FinderOutput
from app.model.common import Evidence
from app.model.page import PageModel, Run

_PL = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
# "2.1 ", "B.3 ", "A. ", "1) ", "17. ", "a) " in front of a heading or a label; never "W przypadku", never "17 zł".
NUMBERING = re.compile(r"^\s*(?:[a-z]\)|[A-Z](?:\.\d*|\d+)(?:\.\d+)*\.?|(?=\d*[.)])\d+(?:\.\d+)*[.)]?)\s+(?=\S)")
BULLET = re.compile(r"[-❑□☐■▪•◻❏❐]")
# "wynajęcie/użyczenie*": alternatives joined by a slash and marked with a star (design 6.4.3 rows 3 and 4).
ALT = re.compile(r"(\w[\w-]*(?:\s*/\s*\w[\w-]*)+)\s*\*+")
_ACRONYM = lexicon.regex("habits", habit="acronym")
OPTIONAL = lexicon.regex("habits", habit="optional")
REQUIRED = lexicon.regex("habits", habit="required")
_STRIKE = lexicon.regex("habits", habit="strike_out")


def some(**kw: Any) -> dict[str, Any]:
    """Keyword arguments without the None ones: our contracts refuse an explicit null."""
    return {k: v for k, v in kw.items() if v is not None}


def key_of(text: str, fallback: str = "pole", limit: int = 60) -> str:
    """A brief key: lower-case ASCII words joined by `_`, starting with a letter, cut at a word."""
    s = unicodedata.normalize("NFKD", text.translate(_PL))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    if not s:
        s = fallback
    elif not s[0].isalpha():
        s = f"{fallback}_{s}"
    if len(s) > limit:
        head = s[: limit + 1]
        s = (head[: head.rindex("_")] if "_" in head else s[:limit]).strip("_")[:limit]
    return s


class Keys:
    """Unique keys of one brief: the base, then the base with a number."""

    def __init__(self, reserved: Iterable[str] = ()) -> None:
        self._used = set(reserved)

    def unique(self, base: str) -> str:
        name, n = base, 1
        while name in self._used:
            n += 1
            name = f"{base[: 60 - len(str(n)) - 1].rstrip('_')}_{n}"
        self._used.add(name)
        return name


_ROMAN = re.compile(r"(?=[IVXLCDM]+$)M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})")


def is_roman(word: str) -> bool:
    """A Roman section number ("II.", "IV)", "XII"): kept in capitals. A bare one-letter "I" is the conjunction "i"
    of a shouted title, and "MI", "CI" are words, so a number needs a dot or bracket, or only the letters I, V, X."""
    core = word.strip(",:;(/")
    bare = core.rstrip(".)")
    if not bare or not _ROMAN.fullmatch(bare):
        return False
    return core != bare or (len(bare) >= 2 and set(bare) <= set("IVX"))


def sentence_case(text: str) -> str:
    """Words printed in capitals go to lower case (acronyms and Roman numbers stay), the first letter is a capital."""
    words = text.split()
    shout = sum(w.isupper() for w in words) * 2 > len(words)
    out = [w.lower() if w.isupper() and (len(w) > 1 or shout) and not _ACRONYM.match(w.strip(".,:;()/"))
           and not is_roman(w) else w for w in words]
    t = " ".join(out)
    return t[:1].upper() + t[1:]


def alt_words(m: re.Match[str]) -> list[str]:
    return [w.strip() for w in m.group(1).split("/")]


def _prefix(a: str, b: str) -> int:
    n = 0
    while n < min(len(a), len(b)) and a[n] == b[n]:
        n += 1
    return n


def is_grammar(words: list[str]) -> bool:
    """Alternatives that are only grammar ("charta/chartów", "zapoznałem/am"): the same stem, or a bare ending."""
    a = words[0].casefold()
    for other in words[1:]:
        b = other.casefold()
        same_stem = _prefix(a, b) >= max(2, math.ceil(0.6 * min(len(a), len(b))))
        if not (same_stem or (len(b) <= 3 and len(a) >= 6)):
            return False
    return True


def same_choice(a: list[str], b: list[str]) -> bool:
    """The same alternatives worded slightly differently ("wynajęcie/użyczenie", "wynajem/użyczenie")."""
    return len(a) == len(b) and all(_prefix(x.casefold(), y.casefold()) >= 4 for x, y in zip(a, b))


def neutral(text: str, strike: bool) -> str:
    """Starred alternatives in running words: grammar keeps the first form; a real choice reads "a lub b" when
    the paper tells to strike one out. The stars go."""
    def sub(m: re.Match[str]) -> str:
        words = alt_words(m)
        if is_grammar(words):
            return words[0]
        return " lub ".join(words) if strike else "/".join(words)
    return ALT.sub(sub, text).replace("*", "")


def clean_label(raw: str, strike: bool = False) -> tuple[str, str | None, bool]:
    """(label, hint, optional): numbering, bullets, the colon, the brackets around a caption and footnote stars go;
    a bracket at the end is the hint, or the mark "optional"."""
    t = re.sub(r"\s+", " ", BULLET.sub(" ", raw)).strip()
    t = neutral(NUMBERING.sub("", t), strike)
    hint, optional = None, False
    m = re.search(r"\(([^()]*)\)\s*:?\s*$", t)
    if m and m.start() > 0:
        inner = m.group(1).strip()
        t = t[: m.start()]
        if OPTIONAL.search(inner):
            optional = True
        elif inner:
            hint = inner
    t = t.strip(" :;,/").strip()
    if t.startswith("(") and t.endswith(")"):
        t = t[1:-1].strip()
    if re.fullmatch(r"[\W\d_]*[^\W\d_]?[\W\d_]*", t):   # "1.", "a)", "-": an enumerator, not a label
        t = ""
    return t, hint, optional


def clean_option(text: str) -> str:
    t = re.sub(r"\s+", " ", BULLET.sub(" ", text)).strip()
    return NUMBERING.sub("", t).replace("*", "").strip(" :;,.").strip()


class Doc:
    def __init__(self, pm: PageModel, fo: FinderOutput) -> None:
        self.pm, self.fo = pm, fo
        self.runs: dict[str, tuple[int, Run]] = {r.id: (p.number, r) for p in pm.pages for r in p.runs}
        seen: set[str] = set()
        self.order = [r for r in fo.order if r in self.runs and not (r in seen or seen.add(r))]  # type: ignore[func-returns-value]
        self.order += [r for r in self.runs if r not in seen]
        self.pos = {r: i for i, r in enumerate(self.order)}
        self.sections = {s.id: s for s in fo.sections}
        self.heading = {r: s.id for s in fo.sections for r in s.runs}
        self.cands = {c.id: c for c in fo.candidates}
        self.owned: set[str] = set()
        for c in fo.candidates:
            self.owned.update(self.cand_runs(c))
        self.strike = bool(_STRIKE.search(" ".join(r.text for _, r in self.runs.values())))

    @staticmethod
    def cand_runs(c: Candidate) -> list[str]:
        out = [*c.runs, *(s.run for s in c.spans)]
        if c.label is not None:
            out += [*c.label.runs, *(s.run for s in c.label.spans)]
        for o in c.options:
            out += [*o.runs, *(s.run for s in o.spans)]
        return out

    def role(self, rid: str) -> str:
        """The finder's role of a run; "heading" for a section heading; "owned" for a run of a candidate."""
        return self.fo.roles.get(rid) or ("heading" if rid in self.heading else "owned" if rid in self.owned else "body")

    def text(self, rid: str) -> str:
        return re.sub(r"\s+", " ", self.runs[rid][1].text).strip()

    def page(self, rid: str) -> int:
        return self.runs[rid][0]

    def cand_pos(self, c: Candidate) -> int:
        """Where a candidate stands in the reading order: its first run, or the first run of its page."""
        hits = [self.pos[r] for r in self.cand_runs(c) if r in self.pos]
        if hits:
            return min(hits)
        return next((i for i, r in enumerate(self.order) if self.runs[r][0] >= c.page), len(self.order))

    def chain(self, c: Candidate) -> list[str]:
        """Titles of the candidate's section and of the sections above it, nearest first."""
        out, sid, seen = [], c.section, set()
        while sid in self.sections and sid not in seen:
            seen.add(sid)
            out.append(self.sections[sid].title)
            sid = self.sections[sid].parent
        return out

    def evidence(self, rids: list[str], quote: str | None, candidate: str | None = None) -> Evidence:
        hit = [self.runs[r] for r in rids if r in self.runs]
        boxes = [r.box for _, r in hit if r.box is not None]
        box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)) if boxes else None
        anchor = None if boxes else next((r.anchor for _, r in hit if r.anchor), None)
        return Evidence(**some(page=hit[0][0] if hit else None, box=box, anchor=anchor, runs=[r for r in rids if r in self.runs],
                               quote=quote or None, candidate=candidate))

    def cand_evidence(self, c: Candidate) -> Evidence:
        return Evidence(**some(page=c.page, box=c.box, anchor=c.anchor, runs=list(c.label.runs) if c.label else [],
                               quote=(c.label.text.strip() or None) if c.label else None, candidate=c.id))

    def footnote(self, mark: str) -> str:
        """Text of the footnote with this mark, whitespace removed (readers split footnotes into pieces)."""
        notes = "".join(self.runs[r][1].text for r in self.order if self.fo.roles.get(r) == "note")
        notes = re.sub(r"\s+", "", notes)
        if mark and set(mark) == {"*"}:
            pat = re.compile(r"(?<!\*)\*{%d}(?!\*)\)?" % len(mark))
        else:
            pat = re.compile(r"(?<!\d)" + re.escape(mark) + r"\)")
        found = []
        for m in pat.finditer(notes):   # an enumerated item may carry the same mark: every reading is returned
            rest = notes[m.end(): m.end() + 160]
            cut = re.search(r"\d\)|\*", rest)
            found.append(rest[: cut.start()] if cut else rest)
        return " ".join(found)
