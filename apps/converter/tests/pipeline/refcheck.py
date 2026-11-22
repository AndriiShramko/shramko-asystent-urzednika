"""BL13 DATE-D: compare a converted form with the partner's own export of the same paper, field by field.

A field is (section title, type, label). Labels and section titles are normalised (case, Polish letters, punctuation,
spaces) and folded through a short table of synonyms that the partner's two exports and our library use for the same
thing. Matching is by label over the whole form (tolerant to order and to the section a field was put in); the type is
compared afterwards and reported, not matched on. Used by test_reference_recall.py and by the local measurement.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

CONTAINERS = ("SECTION", "REPEATING_SECTION")
# Components that carry no answer: text of the form, not a field.
NOT_FIELDS = ("TEXT", "HTML", "PARAGRAPH", "INFO", "STATIC_TEXT")

# Same meaning, other words (left -> right). Labels and section titles both pass through this table.
SYNONYMS = {
    "nazwa organu": "nazwa urzedu",
    "organ": "nazwa urzedu",
    "informacje o budynku": "szczegoly sprawy",
    "dane sprawy": "szczegoly sprawy",
    "nr telefonu": "numer telefonu",
    "telefon": "numer telefonu",
    "adres e mail": "adres email",
    "e mail": "adres email",
    "email": "adres email",
    "nr domu": "numer domu",
    "nr lokalu": "numer lokalu",
    "nr budynku": "numer domu",
    "teryt 4g dowodowy": "teryt dowodowy",
    "oplata skarbowa za pelnomonictwo": "oplata skarbowa za pelnomocnictwo",   # the partner's own typo
}

DATE_WORDS = re.compile(r"\b(data|dnia|w dniu|termin|od dnia|do dnia|urodzenia)\b")


def norm(text: str) -> str:
    """Case, Polish letters, markup, punctuation and spaces folded; then the synonym table."""
    t = re.sub(r"<[^>]+>", " ", text or "")
    t = unicodedata.normalize("NFKD", t.replace("ł", "l").replace("Ł", "L"))
    t = "".join(ch for ch in t if not unicodedata.combining(ch)).casefold()
    t = re.sub(r"[^a-z0-9]+", " ", t).strip()
    return SYNONYMS.get(t, t)


@dataclass(frozen=True)
class Leaf:
    section: str
    type: str
    label: str

    @property
    def is_date(self) -> bool:
        return self.type == "DATEPICKER" or bool(DATE_WORDS.search(self.label))


def leaves(form: dict) -> list[Leaf]:
    """Every answerable component of the form with its nearest section title (or the tab title)."""
    out: list[Leaf] = []

    def walk(questions: list, sec: str) -> None:
        for q in questions or []:
            f = q.get("field") or {}
            t = f.get("type", "")
            if t in CONTAINERS:
                walk(f.get("repeatingSectionGrid") or [], norm(f.get("title") or f.get("techName") or sec))
                continue
            if t in NOT_FIELDS or not f.get("title"):
                continue
            out.append(Leaf(sec, t, norm(f["title"])))

    for tab in form.get("tabs") or []:
        walk(tab.get("questions") or [], norm(tab.get("title", "")))
    return out


@dataclass
class Match:
    partner: int
    ours: int
    found: list[tuple[Leaf, Leaf]] = field(default_factory=list)
    missing: list[Leaf] = field(default_factory=list)
    extra: list[Leaf] = field(default_factory=list)

    @property
    def recall(self) -> float:
        return len(self.found) / self.partner if self.partner else 1.0

    @property
    def type_agree(self) -> int:
        return sum(1 for a, b in self.found if a.type == b.type)

    @property
    def missing_dates(self) -> list[Leaf]:
        return [m for m in self.missing if m.is_date and m.type in ("DATEPICKER", "TEXT_FIELD")]

    def lines(self) -> list[str]:
        out = [f"recall {len(self.found)}/{self.partner} = {self.recall:.3f}; types agree {self.type_agree}/{len(self.found)}; "
               f"ours {self.ours}, extra {len(self.extra)}"]
        out += [f"  missing {m.section} | {m.type} | {m.label}" for m in self.missing]
        out += [f"  extra   {m.section} | {m.type} | {m.label}" for m in self.extra]
        out += [f"  type    {a.label}: partner {a.type}, ours {b.type}" for a, b in self.found if a.type != b.type]
        return out


def compare(partner: dict, ours: dict) -> Match:
    """Partner fields matched to ours by label, same section preferred; each of ours is used once."""
    theirs, mine = leaves(partner), leaves(ours)
    pool: dict[str, list[Leaf]] = {}
    for leaf in mine:
        pool.setdefault(leaf.label, []).append(leaf)
    res = Match(partner=len(theirs), ours=len(mine))
    # same section first, so that two "Miejscowość" (address and matter) pair with their own
    for p in sorted(theirs, key=lambda x: not any(c.section == x.section for c in pool.get(x.label, []))):
        cands = pool.get(p.label) or []
        pick = next((c for c in cands if c.section == p.section), cands[0] if cands else None)
        if pick is None:
            res.missing.append(p)
            continue
        cands.remove(pick)
        res.found.append((p, pick))
    # an upload box is named by its section ("Opłata skarbowa"), its own label is free wording: second pass by section
    rest = [leaf for r in pool.values() for leaf in r]
    for p in [m for m in res.missing if m.type == "FILE_UPLOADER"]:
        pick = next((c for c in rest if c.type == "FILE_UPLOADER" and c.section == p.section), None)
        if pick is not None:
            rest.remove(pick)
            res.missing.remove(p)
            res.found.append((p, pick))
    res.extra = rest
    return res


def counts(form: dict) -> Counter:
    return Counter(leaf.type for leaf in leaves(form))
