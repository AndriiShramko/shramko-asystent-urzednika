"""What the paper says about itself (design 6.4.1, 6.4.2): title, variants of a composite paper, addressee, who may
apply, legal basis, fee, the data-protection clause. Each answer is stated with a quote, not_found or ambiguous."""
from __future__ import annotations

import re
from dataclasses import dataclass

from app import interim, lexicon
from app.model.brief import Addressee, Applicants
from app.model.common import Dropped, Evidence, Stated, Warning
from app.model.page import Run

from ._doc import NUMBERING, Doc, neutral, sentence_case

_WORDS = "|".join(re.escape(r["word"]) for r in lexicon.rows("title_kinds"))
KIND = re.compile(rf"^\W*({_WORDS})\b", re.IGNORECASE)
_KIND_ANY = re.compile(rf"\b({_WORDS})", re.IGNORECASE)
_FURNITURE = lexicon.regex("habits", habit="furniture_title")
_LEGAL_REF = re.compile(r"\(\s*(?:t\.\s*j\.\s*)?Dz\.\s*U\.[^)]*\)|\bna podstawie\b.*$", re.IGNORECASE)
_FEE = lexicon.regex("habits", habit="fee")
_PERSONAL_ONLY = lexicon.regex("habits", habit="personal_only")
_ADDR_SECTION = lexicon.regex("habits", habit="addressee_section")
_LEGAL_SECTION = lexicon.regex("habits", habit="legal_section")
_HEAD_NO = re.compile(r"^\s*(?:[IVX]{1,4}|[A-Z]|\d{1,2}(?:\.\d{1,2})*)[.)]\s+(?=\S)")   # "II. Wniosek ..."
_TO = re.compile(r"^(?:do|adresat\s*:?)\s+", re.IGNORECASE)
NOT_FOUND = Stated(status="not_found")


@dataclass(frozen=True)
class Variant:
    """One application of a composite paper (design 6.4.4): where its title stands and how it reads."""

    pos: int
    title: str
    runs: tuple[str, ...]


# -- title --------------------------------------------------------------------------------------------------------

def _weight(run: Run) -> float:
    size = run.size or ((run.box[3] - run.box[1]) if run.box else 0.0)
    return size * (1.05 if run.bold else 1.0)


def _title_like(doc: Doc) -> list[str]:
    """Runs that look like a title: they start with what a paper calls itself and stand out (bold, capitals or a
    heading of the finder). A header "Załącznik nr 2 do Regulaminu ..." is never one."""
    out = []
    for rid in doc.order:
        if doc.role(rid) not in ("body", "heading"):
            continue
        run, t = doc.runs[rid][1], doc.text(rid)
        if rid in doc.heading:
            t = _HEAD_NO.sub("", t)
        if not t or len(t) > 120 or _FURNITURE.search(t) or not KIND.search(t):
            continue
        if run.bold or rid in doc.heading or t.isupper():
            out.append(rid)
    return out


def _group(doc: Doc, top: str) -> list[str]:
    """The title and the lines it wraps onto: the same look, in lower case or all in capitals like the first."""
    first, group = doc.runs[top][1], [top]
    for rid in doc.order[doc.pos[top] + 1: doc.pos[top] + 4]:
        run, t = doc.runs[rid][1], doc.text(rid)
        same_look = run.bold == first.bold and abs(_weight(run) - _weight(first)) <= (1.6 if t[:1].islower() else 0.7)   # "WNIOSEK" over a smaller "o wydanie ..."
        same_heading = rid in doc.heading and doc.heading[rid] == doc.heading.get(top)   # the finder joined them
        wraps = t[:1].islower() or same_heading or (doc.text(top).isupper() and t.isupper())
        numbered = rid in doc.heading and not same_heading and doc.sections[doc.heading[rid]].number is not None   # "B ...": the next section
        if not (t and doc.role(rid) in ("body", "heading") and same_look and wraps and not numbered and len(t) <= 120
                and not NUMBERING.match(t) and not KIND.search(t) and not _FURNITURE.search(t)):
            break
        group.append(rid)
    return group


def tidy_title(raw: str, strike: bool) -> str:
    t = neutral(_LEGAL_REF.sub("", _HEAD_NO.sub("", raw)), strike)
    return sentence_case(re.sub(r"\s+", " ", t).strip(" :.,;"))


def find_title(doc: Doc) -> tuple[Stated, list[str]]:
    like = _title_like(doc)
    if not like:
        old = interim.find_title(doc.pm)   # a paper whose title does not stand out: the plain rule of WP-F1
        value = old.value or ""
        if old.status != "stated" or _FURNITURE.search(value) or not _KIND_ANY.search(value):
            return NOT_FOUND, []
        return Stated(status="stated", value=tidy_title(value, doc.strike), evidence=old.evidence), list(old.evidence[0].runs)
    page = doc.page(like[0])
    pool = [r for r in like if doc.page(r) == page]
    top = max(pool, key=lambda r: (round(_weight(doc.runs[r][1]), 1), -doc.pos[r]))
    group = _group(doc, top)
    raw = " ".join(doc.text(r) for r in group)
    return Stated(status="stated", value=tidy_title(raw, doc.strike), evidence=[doc.evidence(group, raw)]), group


def find_variants(doc: Doc, title_runs: list[str]) -> list[Variant]:
    """Design 6.4.4: the title pattern repeated at the top of later pages, each with its own places to fill.
    Fewer than two different titles: an ordinary paper, no variant."""
    if not title_runs or not KIND.search(_HEAD_NO.sub("", doc.text(title_runs[0]))):
        return []
    word = KIND.search(_HEAD_NO.sub("", doc.text(title_runs[0]))).group(1).casefold()   # type: ignore[union-attr]
    first = " ".join(doc.text(r) for r in title_runs)
    found = [Variant(doc.pos[title_runs[0]], tidy_title(first, doc.strike), tuple(title_runs))]
    top_of_page: dict[int, list[str]] = {}
    for rid in doc.order:
        top_of_page.setdefault(doc.page(rid), []).append(rid)
    for rid in _title_like(doc):
        page = doc.page(rid)
        if page <= doc.page(found[-1].runs[0]) or rid not in top_of_page[page][:8]:
            continue
        if KIND.search(_HEAD_NO.sub("", doc.text(rid))).group(1).casefold() != word:   # type: ignore[union-attr]
            continue
        group = _group(doc, rid)
        title = tidy_title(" ".join(doc.text(r) for r in group), doc.strike)
        if title.casefold() not in {v.title.casefold() for v in found}:
            found.append(Variant(doc.pos[rid], title, tuple(group)))
    starts = [v.pos for v in found] + [len(doc.order) + 1]
    owns = [any(starts[i] <= doc.cand_pos(c) < starts[i + 1] for c in doc.fo.candidates) for i in range(len(found))]
    found = [v for v, has in zip(found, owns) if has]
    return found if len(found) >= 2 else []


# -- addressee ----------------------------------------------------------------------------------------------------

def _office_pattern() -> tuple[re.Pattern[str], dict[str, dict]]:
    forms: dict[str, dict] = {}
    for row in lexicon.rows("offices"):
        for form in (row["base"], *row.get("forms", [])):
            forms[form.casefold()] = row
    alt = "|".join(re.escape(f).replace(r"\ ", " ") for f in sorted(forms, key=len, reverse=True))
    # the phrase in any letter case, then the proper name: up to three words that start with a capital
    return re.compile(rf"(?<!\w)((?i:{alt}))(?!\w)(?:\s+we?(?=\s))?((?:\s+[A-ZĄĆĘŁŃÓŚŹŻ][\w-]*){{0,3}})"), forms


_OFFICE, _FORMS = _office_pattern()


def _name_words(tail: str) -> set[str]:
    return {w.casefold()[:4] for w in re.findall(r"[^\W\d_]{4,}", tail)}


def _named(m: re.Match[str], tail: str) -> tuple[str, str]:
    row = _FORMS[m.group(1).casefold()]
    tail = " ".join(tail.split())
    return row["kind"], f"{row['base']} {tail.title() if tail.isupper() else tail}".strip()


def find_addressee(doc: Doc) -> tuple[Addressee, list[Warning]]:
    """The block that names an office or a body, or the section "Organ, do którego ...". When another place of
    the paper names a different office, the block wins and the warning ADDRESSEE_CONFLICT carries both quotes."""
    hit: tuple[list[str], re.Match[str], str] | None = None
    for s in doc.sections.values():   # 1. the section that says so
        if not _ADDR_SECTION.search(s.title) or not s.runs:
            continue
        for rid in doc.order[doc.pos.get(s.runs[-1], len(doc.order)) + 1:]:
            if rid in doc.heading:
                break
            m = _OFFICE.search(doc.text(rid))
            if m and m.group(2).strip():
                hit = ([rid], m, m.group(2))
                break
    if hit is None and doc.order:     # 2. a line of the first page that starts with the name
        first_page = doc.page(doc.order[0])
        for i, rid in enumerate(doc.order):
            if doc.page(rid) != first_page or doc.role(rid) not in ("body", "heading"):
                continue
            t = _TO.sub("", doc.text(rid))
            m = _OFFICE.match(t)
            if not m:
                continue
            if m.group(2).strip():
                hit = ([rid], m, m.group(2))
                break
            nxt = doc.order[i + 1] if i + 1 < len(doc.order) else None
            if m.end() == len(t) and nxt and doc.role(nxt) in ("body", "heading"):   # the name goes on in the next line
                more = doc.text(nxt)
                if more[:1].isupper() and not re.search(r"\d", more) and len(more.split()) <= 4:
                    hit = ([rid, nxt], m, more)
                    break
    if hit is None:
        return Addressee(status="not_found"), []
    rids, m, tail = hit
    kind, name = _named(m, tail)
    quote = " ".join(doc.text(r) for r in rids)
    ev = doc.evidence(rids, quote)
    warnings: list[Warning] = []
    mine = _name_words(tail)
    for rid in doc.order:
        if rid in rids or not mine:
            continue
        for other in _OFFICE.finditer(doc.text(rid)):
            theirs = _name_words(other.group(2))
            if theirs and not (mine & theirs):
                warnings.append(Warning(code="ADDRESSEE_CONFLICT", page=doc.page(rids[0]),
                                        evidence=[ev, doc.evidence([rid], other.group(0).strip())],
                                        detail="the paper names two different offices; the addressee block wins"))
                return Addressee(status="stated", kind=kind, name=name, evidence=[ev]), warnings
    return Addressee(status="stated", kind=kind, name=name, evidence=[ev]), warnings


# -- who may apply ------------------------------------------------------------------------------------------------

def find_applicants(signals: list[tuple[str, Evidence]]) -> Applicants:
    """Design 6.4.2, the wording table: data of a person, of an entity, or both, and the capacities named."""
    found: dict[str, Evidence] = {}
    for text, ev in signals:
        for rx, row in lexicon.compiled("applicants", table="wording"):
            if row["signal"] not in found and rx.search(text):
                found[row["signal"]] = ev if ev.quote else Evidence(quote=text)
    person, entity = "person" in found, "entity" in found
    if not person and not entity:
        return Applicants(status="not_found")
    capacities = ["pelnomocnik"] + (["reprezentant"] if entity else [])
    if "przedstawiciel_ustawowy" in found:
        capacities.append("przedstawiciel_ustawowy")
    evidence, seen = [], set()
    for ev in found.values():
        if ev.quote not in seen:
            seen.add(ev.quote)
            evidence.append(ev)
    return Applicants(status="stated", self_=person, other_person=person, entity=entity, capacities=capacities, evidence=evidence)


def prune_by_exclusion(doc: Doc, a: Applicants) -> tuple[Applicants, list[Dropped]]:
    """D20: the proxy route (other person, entity, power of attorney) is removed only when the paper says it in so
    many words ("Wniosek składa się wyłącznie osobiście"); the quote stays in the evidence and in the dropped list."""
    if a.status != "stated":
        return a, []
    for rid in doc.order:
        t = re.sub(r"\s+", " ", doc.text(rid))
        m = _PERSONAL_ONLY.search(t)
        if m and doc.role(rid) in ("body", "note", "heading"):
            ev = doc.evidence([rid], t)
            # only the route the sentence names goes: a proxy. A company or a statutory representative stays.
            kept = [c for c in a.capacities if c != "pelnomocnik"]
            pruned = a.model_copy(update={"self_": a.self_ or not a.entity, "other_person": False, "capacities": kept,
                                          "evidence": [*a.evidence, ev]})
            return pruned, [Dropped(what=f"route of a proxy or an entity: {t[:160]}", reason="PAPER_INSTRUCTION", page=doc.page(rid), runs=[rid])]
    return a, []


# -- legal basis, fee, clause ---------------------------------------------------------------------------------------

def find_legal_basis(doc: Doc) -> Stated:
    rids = [r for r in doc.order if doc.fo.roles.get(r) == "legal_basis"]
    if not rids:
        for s in doc.sections.values():
            if _LEGAL_SECTION.search(NUMBERING.sub("", s.title)) and s.runs:
                for rid in doc.order[doc.pos.get(s.runs[-1], len(doc.order)) + 1:]:
                    if doc.role(rid) != "body":
                        break
                    rids.append(rid)
    if not rids:
        return NOT_FOUND
    group = [rids[0]]
    for rid in rids[1:]:
        if doc.pos[rid] != doc.pos[group[-1]] + 1:
            break
        group.append(rid)
    quote = " ".join(doc.text(r) for r in group)
    return Stated(status="stated", value=quote, evidence=[doc.evidence(group, quote)]) if quote else NOT_FOUND


def find_fee(doc: Doc) -> Stated:
    """Stated only when the paper prints an amount in złoty next to the word; two different amounts: ambiguous."""
    hits: dict[str, Evidence] = {}
    for rid in doc.order:
        if doc.fo.roles.get(rid) in ("clause", "page_furniture"):
            continue
        m = _FEE.search(doc.text(rid))
        if m:
            amount = next(g for g in m.groups() if g) if any(m.groups()) else m.group(0)
            hits.setdefault(re.sub(r"\s+", "", amount), doc.evidence([rid], doc.text(rid)))
    if not hits:
        return NOT_FOUND
    if len(hits) == 1:
        ev = next(iter(hits.values()))
        return Stated(status="stated", value=ev.quote, evidence=[ev])
    return Stated(status="ambiguous", evidence=list(hits.values()))


def find_clause(doc: Doc) -> tuple[Stated, list[Dropped]]:
    """The data-protection clause is linked, never copied and never read as fields (design 6.4.3)."""
    rids = [r for r in doc.order if doc.fo.roles.get(r) == "clause"]
    if not rids:
        return NOT_FOUND, []
    quote = doc.text(rids[0]) or "klauzula informacyjna"
    return (Stated(status="stated", evidence=[doc.evidence(rids[:1], quote)]),
            [Dropped(what=quote[:120], reason="CLAUSE_LINKED", page=doc.page(rids[0]), count=len(rids))])
