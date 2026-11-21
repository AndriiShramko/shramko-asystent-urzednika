"""The fate of every candidate and the fields of the matter (design 6.4.3 "paper habits", 6.4.4 composite papers).

Every finder candidate gets exactly one disposition: FIELD, MERGED, STANDARD, LEFT_OUT or AWAITING_DECISION.
A place without a label is never given one: it waits for the official's decision.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app import lexicon
from app.model.brief import ApplicantExtra, Attachment, BriefField, Cond, Consent, Disposition, MatterSection
from app.model.candidate import Candidate, ChoiceOption
from app.model.common import Dropped, Evidence, Warning

from ._doc import ALT, NUMBERING, OPTIONAL, REQUIRED, Doc, Keys, alt_words, clean_label, clean_option, is_grammar, key_of, same_choice, sentence_case, some
from ._head import Variant

DEFAULT_TITLE = "Szczegóły sprawy"
SELECTOR_KEY = "rodzaj_wniosku"
SELECTOR_LABEL = "Wybierz rodzaj wniosku"


def _habit(name: str) -> re.Pattern[str]:
    return lexicon.regex("habits", habit=name)


_DATE_PLACE, _SIGN_SECTION = _habit("date_place"), _habit("signature_section")
_EXCLUSIVE, _EXCLUSIVE_WORDING, _MULTIPLE = _habit("exclusive_option"), _habit("exclusive_wording"), _habit("multiple_wording")
_COMPUTED, _ATTACH, _DECLARATION, _FUNCTION = _habit("computed"), _habit("attachments_section"), _habit("declaration"), _habit("function_word")
_PHRASES = {r["phrase"]: r["label"] for r in lexicon.rows("phrases")}
_ENUM = re.compile(r"^\s*(?:\d+[.)]|[a-z]\)|[-–•])\s*")
_LINE_KINDS = ("leader", "line_block", "blank_in_sentence")


_YES_NO = {"tak", "nie"}


@dataclass
class Fields:
    matter: list[MatterSection] = field(default_factory=list)
    attachments: list[Attachment] = field(default_factory=list)
    consents: list[Consent] = field(default_factory=list)
    dispositions: list[Disposition] = field(default_factory=list)
    dropped: list[Dropped] = field(default_factory=list)
    warnings: list[Warning] = field(default_factory=list)
    signals: list[tuple[str, Evidence]] = field(default_factory=list)
    extras: list[ApplicantExtra] = field(default_factory=list)


def read_fields(doc: Doc, title_runs: list[str], variants: list[Variant]) -> Fields:
    return _Reader(doc, title_runs, variants).run()


class _Reader:
    def __init__(self, doc: Doc, title_runs: list[str], variants: list[Variant]) -> None:
        self.doc, self.variants = doc, variants
        self.head_runs = set(title_runs) | {r for v in variants for r in v.runs}
        self.title_pos = doc.pos[title_runs[0]] if title_runs else None
        self.title_page = doc.page(title_runs[0]) if title_runs else None
        self.keys = Keys({SELECTOR_KEY} if variants else ())
        self.out = Fields()
        self.secs: dict[str, dict[str, Any]] = {}       # role -> section under construction
        self.disp: dict[str, Disposition] = {}          # candidate id -> its fate
        self.field_of: dict[str, BriefField] = {}       # candidate id -> the field it became
        self.role_of: dict[str, str] = {}               # candidate id -> role of the section of its field
        self.standard: dict[str, list[str]] = {}        # standard role -> labels it covers
        self.row_heads: set[str] = set()
        self.open_attachment: str | None = None
        self.last: BriefField | None = None

    # -- the pass ---------------------------------------------------------------------------------------------------

    def run(self) -> Fields:
        doc = self.doc
        self._alternatives()
        rows = self._table_rows()
        blank_of = {o.blank: (c.id, o) for c in doc.fo.candidates for o in c.options if o.blank}
        prev: Candidate | None = None
        for c in doc.fo.candidates:
            if c.group is not None and c.group in doc.cands:
                self._set(c, "MERGED", into=c.group, why="GROUP_MEMBER")
                continue
            self._one(c, rows, blank_of, prev)
            prev = c
        self._declarations()
        self._text_roles()
        for role, labels in self.standard.items():
            self.out.dropped.append(Dropped(what=f"{role}: {', '.join(labels)}"[:300], reason="COVERED_BY_STANDARD", count=len(labels)))
        self._composite()
        self.out.matter = [MatterSection(**some(title=s["title"], role=s["role"], repeating=s["repeating"], show_if=s.get("show_if"),
                                                fields=s["fields"])) for s in self.secs.values() if s["fields"]]
        keys = {f.key for m in self.out.matter for f in m.fields}
        self.out.warnings = [w for w in self.out.warnings if w.field is None or w.field in keys]
        self.out.dispositions = [self.disp[c.id] for c in doc.fo.candidates]
        return self.out

    def _one(self, c: Candidate, rows: dict[str, str], blank_of: dict[str, tuple[str, ChoiceOption]], prev: Candidate | None) -> None:
        doc = self.doc
        raw = c.label.text if c.label else ""
        label, hint, optional = clean_label(raw, doc.strike)
        chain = [NUMBERING.sub("", t).strip() for t in doc.chain(c)]
        if c.kind == "signature":
            return self._left(c, "SIGNATURE_AND_DATE", label or "podpis")
        if c.kind == "office_use":
            return self._left(c, "OFFICE_USE", label or "adnotacja urzędu")
        if c.id in rows:
            return self._set(c, "MERGED", into=rows[c.id], why="TABLE_ROW")
        low = label.casefold()
        before = self.title_pos is not None and c.page == self.title_page and doc.cand_pos(c) < self.title_pos
        if label and _DATE_PLACE.search(low) and (low.endswith("dnia") or before or any(_SIGN_SECTION.search(t) for t in chain)):
            return self._left(c, "SIGNATURE_AND_DATE", label)
        if c.id in blank_of and blank_of[c.id][0] in self.field_of and self._option_blank(c, *blank_of[c.id]):
            return None
        attach = any(_ATTACH.search(t) for t in chain)
        if not label and c.kind == "choice_group" and chain and not attach:
            label, low = sentence_case(chain[0]), chain[0].casefold()   # the heading is the question
        if label and self._standard(c, raw, low, label, chain, before):
            return None
        if attach:
            return self._attachment(c, label)
        if not label:
            return self._unlabelled(c, prev)
        return self._field(c, raw, label, hint, optional)

    # -- fates ------------------------------------------------------------------------------------------------------

    def _set(self, c: Candidate, fate: str, **kw: Any) -> None:
        self.disp[c.id] = Disposition(candidate=c.id, fate=fate, **kw)

    def _left(self, c: Candidate, reason: str, what: str) -> None:
        self._set(c, "LEFT_OUT", reason=reason)
        self.out.dropped.append(Dropped(what=what[:200], reason=reason, page=c.page))

    def _standard(self, c: Candidate, raw: str, low: str, label: str, chain: list[str], before: bool) -> bool:
        """The applicant block (design 6.4.3): a label the standard sections ask, standing in the head of the paper
        or under a heading of the applicant. The same label elsewhere is a field of the matter."""
        sec_role, in_section = None, False
        for t in chain:
            for rx, row in lexicon.compiled("applicants", table="section"):
                if rx.search(t):
                    in_section, sec_role = True, sec_role or row.get("role")
        if not (before or in_section):
            return False
        for rx, row in lexicon.compiled("applicants", table="label"):
            if rx.search(low):
                role = sec_role or row["role"]
                self._set(c, "STANDARD", role=role)
                self.standard.setdefault(role, []).append(label)
                self.out.signals.append((raw, self.doc.cand_evidence(c)))
                self.out.signals += [(t, Evidence(quote=t, page=c.page)) for t in chain]
                if row.get("concept") and role != "standard/pelnomocnictwo":
                    extra = ApplicantExtra(concept=row["concept"], party=row["party"])
                    if extra not in self.out.extras:
                        self.out.extras.append(extra)
                return True
        return False

    def _unlabelled(self, c: Candidate, prev: Candidate | None) -> None:
        """A dotted line right under a field of the matter is its next line; any other place without a label waits."""
        doc = self.doc
        if prev is not None and c.kind in ("leader", "line_block") and prev.kind in _LINE_KINDS \
                and prev.section == c.section and prev.page == c.page and self._adjacent(prev, c):
            root = prev.id
            while root in self.disp and self.disp[root].fate == "MERGED" and self.disp[root].why == "LINE_BLOCK":
                root = self.disp[root].into or ""
            target = self.field_of.get(root)
            if target is not None:
                if target.type == "TEXT_FIELD" and target.concept is None:
                    target.type, target.length = "TEXTAREA", None
                return self._set(c, "MERGED", into=prev.id, why="LINE_BLOCK")
        self._set(c, "AWAITING_DECISION", decision=f"label_{c.id}")
        self.out.warnings.append(Warning(code="LABEL_NOT_FOUND", page=c.page, candidate=c.id,
                                         detail="a place to fill without a label: the official decides what it asks"))

    def _adjacent(self, prev: Candidate, c: Candidate) -> bool:
        doc = self.doc
        a = [doc.pos[r] for r in prev.runs if r in doc.pos]
        b = [doc.pos[r] for r in c.runs if r in doc.pos]
        if not a or not b or min(b) < max(a):
            return False
        mine = set(doc.cand_runs(prev)) | set(c.runs)
        return all(r in mine for r in doc.order[max(a) + 1: min(b)])

    def _attachment(self, c: Candidate, label: str) -> None:
        """Design 6.4.3 "Załączniki": one upload per named item; open lines become one "Inne załączniki"."""
        doc = self.doc
        named = [(clean_option(o.text), list(o.runs)) for o in c.options] if c.kind == "choice_group" else \
            [(label, list(c.label.runs) if c.label else [])] if c.kind == "box" and label else []
        made: list[tuple[str, str | None]] = []
        for text, runs in named:
            if not text or text.strip(" .:").casefold() in _YES_NO:   # a column of answers, not a named item
                continue
            cover = next((row["role"] for rx, row in lexicon.compiled("habits", habit="attachment_cover") if rx.search(text)), None)
            key = self.keys.unique(key_of(text, "zalacznik"))
            self.out.attachments.append(Attachment(**some(label=text, covered_by=cover, key=key,
                                                          evidence=[Evidence(page=c.page, runs=runs, quote=text, candidate=c.id)])))
            made.append((key, cover))
        own = [k for k, cover in made if cover is None]
        if own:
            return self._set(c, "FIELD", key=own[0])
        if made:
            return self._set(c, "STANDARD", role=made[0][1])
        if c.kind in ("choice_group", "box"):
            return self._set(c, "AWAITING_DECISION", decision=f"attachment_{c.id}")
        if self.open_attachment is None:
            key = self.keys.unique("inne_zalaczniki")
            self.out.attachments.append(Attachment(label="Inne załączniki", key=key, evidence=[doc.cand_evidence(c)]))
            self.open_attachment = c.id
            return self._set(c, "FIELD", key=key)
        return self._set(c, "MERGED", into=self.open_attachment, why="LINE_BLOCK")

    def _option_blank(self, c: Candidate, gid: str, option: ChoiceOption) -> bool:
        """Design 6.4.3 "an option followed by a blank": a text field shown when the option is chosen."""
        group, text = self.field_of[gid], clean_option(option.text)
        if text not in group.options:
            return False
        f = BriefField(key=self.keys.unique(key_of(f"{group.key} {text}")), label=f"{group.label}: {text}", type="TEXT_FIELD",
                       show_if=Cond(field=group.key, is_=text), candidate=c.id, conf=self._conf(c), evidence=[self.doc.cand_evidence(c)])
        self._add(c, f, self.role_of[gid])
        return True

    # -- a field of the matter ----------------------------------------------------------------------------------------

    def _field(self, c: Candidate, raw: str, label: str, hint: str | None, optional: bool) -> None:
        doc, low = self.doc, label.casefold()
        options: list[str] = []
        concept = length = None
        shown = sentence_case(label)
        if c.kind == "box":
            # One box outside any group: an option of a question the finder could not group, or a yes-or-no
            # question. Reading it as a field would look right and may be wrong; the official decides.
            self._set(c, "AWAITING_DECISION", decision=f"box_{c.id}")
            self.out.warnings.append(Warning(code="AMBIGUOUS_GROUP", page=c.page, candidate=c.id,
                                             detail=f"a single box outside any group: {label[:80]!r}; an option or a yes-or-no question"))
            return None
        if c.kind == "choice_group":
            for o in c.options:
                text = clean_option(o.text)
                if text and text not in options:
                    options.append(text)
            if len(options) < 2:
                self._set(c, "AWAITING_DECISION", decision=f"options_{c.id}")
                self.out.warnings.append(Warning(code="AMBIGUOUS_GROUP", page=c.page, candidate=c.id, detail="a choice group with fewer than two readable options"))
                return None
            kind = self._choice_kind(c, raw, options)
        else:
            kind, concept, length, shown = self._typing(c, label, low, shown)
        key = self.keys.unique(key_of(shown))
        notes = [doc.footnote(m) for m in c.footnotes]
        optional = optional or bool(OPTIONAL.search(low)) or any(OPTIONAL.search(n) for n in notes)
        marked = bool(REQUIRED.search(low)) or any(REQUIRED.search(n) for n in notes)
        required = not optional
        basis = ("paper" if marked else "inferred") if required else None
        f = BriefField(**some(key=key, label=shown, type=kind, concept=concept, required=required, required_basis=basis,
                              hint=hint or self._hint_after(c), options=options, length=length if kind == "TEXT_FIELD" else None,
                              candidate=c.id, conf=self._conf(c), evidence=[doc.cand_evidence(c)]))
        if basis == "inferred":
            self.out.warnings.append(Warning(code="REQUIRED_INFERRED", field=key, candidate=c.id, page=c.page,
                                             detail="the paper does not say whether this is required; marked required by our rule"))
        if _COMPUTED.search(low):
            self.out.dropped.append(Dropped(what=f"{label}: printed arithmetic, the value is typed", reason="COMPUTED_VALUE", page=c.page))
        self._add(c, f, self._section(c)["role"])
        return None

    def _typing(self, c: Candidate, label: str, low: str, shown: str) -> tuple[str, str | None, int | None, str]:
        """Type, concept, length and wording of a plain place (design 6.4.3 rows 1 and 2, the label rules)."""
        doc = self.doc
        if low in ("do", "do dnia") and self.last is not None and self.last.type == "DATEPICKER" and self.last.label.endswith(" od"):
            return "DATEPICKER", "date", None, self.last.label[:-2] + "do"   # "od ... do ...": two dates in one section
        if c.kind == "comb" and c.mask and re.search(r"[DMR]{2}", c.mask):
            return "DATEPICKER", "date", None, shown
        for rx, row in lexicon.compiled("concepts"):
            if rx.search(low):
                return row["type"], row.get("concept"), row.get("length"), row.get("label") or _PHRASES.get(low) or shown
        if low in _PHRASES:
            shown = _PHRASES[low]
        elif (c.label is not None and c.label.how == "sentence") or _FUNCTION.search(label):
            self.out.warnings.append(Warning(code="LABEL_RAW", page=c.page, candidate=c.id,
                                             detail=f"label kept as the paper's words: {label[:80]!r}"))
        return ("TEXTAREA" if c.kind == "line_block" else "TEXT_FIELD"), None, (c.cells if c.kind == "comb" else None), shown

    def _choice_kind(self, c: Candidate, raw: str, options: list[str]) -> str:
        """Design 6.4.3 "tick boxes that share a question"."""
        wording = raw.casefold()
        if len(options) > 5:
            return "SELECT"
        if _MULTIPLE.search(wording):
            return "CHECKBOX"
        if len(options) == 2 or _EXCLUSIVE_WORDING.search(wording) or any(_EXCLUSIVE.search(o.casefold()) for o in options):
            return "RADIO"
        self.out.warnings.append(Warning(code="AMBIGUOUS_GROUP", page=c.page, candidate=c.id,
                                         detail="the paper does not say whether one or several options may be marked; several are allowed"))
        return "CHECKBOX"

    def _hint_after(self, c: Candidate) -> str | None:
        """ "(rodzaj uroczystości, np. wesele ...)" under a line is the hint of the field."""
        doc = self.doc
        place = [doc.pos[r] for r in c.runs if r in doc.pos]
        if not place or max(place) + 1 >= len(doc.order):
            return None
        nxt = doc.order[max(place) + 1]
        t = doc.text(nxt)
        if doc.role(nxt) in ("body", "instruction") and t.startswith("(") and t.endswith(")") and len(t) > 4:
            return t[1:-1].strip()
        return None

    @staticmethod
    def _conf(c: Candidate) -> float:
        return round(min(c.conf.geometry, c.conf.label, c.conf.text), 2)

    def _variant(self, c: Candidate) -> int | None:
        p, hit = self.doc.cand_pos(c), None
        for i, v in enumerate(self.variants):
            if v.pos <= p:
                hit = i
        return hit

    def _section(self, c: Candidate | None) -> dict[str, Any]:
        """The matter section of a field: the paper's heading above it; the title of the paper heads no section."""
        s = self.doc.sections.get(c.section or "") if c is not None else None
        v = self._variant(c) if c is not None else None
        title = DEFAULT_TITLE
        if s is not None and not (set(s.runs) & self.head_runs):
            title = sentence_case(NUMBERING.sub("", s.title).strip(" :")) or DEFAULT_TITLE
        repeating = c is not None and c.id in self.row_heads
        if repeating:
            title += " – pozycje"
        role = "matter/" + (f"w{v + 1}/" if v is not None else "") + key_of(title, "sekcja")
        return self.secs.setdefault(role, {"title": title, "role": role, "fields": [], "repeating": repeating, "variant": v})

    def _add(self, c: Candidate, f: BriefField, role: str) -> None:
        self.secs[role]["fields"].append(f)
        self.field_of[c.id], self.role_of[c.id], self.last = f, role, f
        self._set(c, "FIELD", key=f.key)

    # -- rules over the whole paper -----------------------------------------------------------------------------------

    def _alternatives(self) -> None:
        """ "wynajęcie/użyczenie*" with "*niepotrzebne skreślić": one RADIO, asked once however often it recurs;
        alternatives that are only grammar give no field (reason GRAMMAR_VARIANT)."""
        doc = self.doc
        if not doc.strike:
            return
        seen: list[list[str]] = []
        grammar: set[str] = set()
        for rid in doc.order:
            if doc.fo.roles.get(rid) in ("clause", "page_furniture"):
                continue
            for m in ALT.finditer(doc.text(rid)):
                words = alt_words(m)
                if is_grammar(words):
                    if m.group(1).casefold() not in grammar:
                        grammar.add(m.group(1).casefold())
                        self.out.dropped.append(Dropped(what=m.group(1), reason="GRAMMAR_VARIANT", page=doc.page(rid), runs=[rid]))
                    continue
                if any(same_choice(words, s) for s in seen):
                    continue
                seen.append(words)
                f = BriefField(key=self.keys.unique(key_of("_".join(words))), label=sentence_case(" lub ".join(words)), type="RADIO",
                               options=words, required=True, required_basis="paper", evidence=[doc.evidence([rid], doc.text(rid))])
                self._section(None)["fields"].append(f)

    def _table_rows(self) -> dict[str, str]:
        """A table of equal rows (design 6.4.3): the same run of labels three or more times in one section. The
        first row gives the fields of a repeating section, the others are merged into it (TABLE_ROW)."""
        doc = self.doc
        tops = [c for c in doc.fo.candidates if c.group is None and c.label is not None
                and c.kind not in ("signature", "office_use", "choice_group", "box")]
        labs = [clean_label(c.label.text, doc.strike)[0].casefold() for c in tops]   # type: ignore[union-attr]
        out: dict[str, str] = {}
        i = 0
        while i < len(tops):
            step = 1
            for p in range(2, 7):
                row = labs[i: i + p]
                if len(row) < p or not all(row) or len(set(row)) != p:
                    continue
                k = 1
                while labs[i + k * p: i + (k + 1) * p] == row:
                    k += 1
                if k >= 3 and len({c.section for c in tops[i: i + k * p]}) == 1:
                    for j in range(i + p, i + k * p):
                        out[tops[j].id] = tops[i + (j - i) % p].id
                    self.row_heads.update(c.id for c in tops[i: i + p])
                    step = k * p
                    break
            i += step
        return out

    def _declarations(self) -> None:
        """ "Oświadczam, że ..." (design 6.4.3): each item one declaration, in the paper's own words."""
        doc, order = self.doc, self.doc.order
        free = lambda rid: doc.role(rid) in ("body", "note")   # noqa: E731
        i = 0
        while i < len(order):
            rid = order[i]
            i += 1
            if not free(rid) or not _DECLARATION.search(doc.text(rid)):
                continue
            stem, used, items, depth = NUMBERING.sub("", doc.text(rid)), [rid], [], 0
            while i < len(order) and len(used) < 40:
                t = doc.text(order[i])
                if not free(order[i]):
                    break
                if depth > 0 or (t.startswith("(") and not items):   # a remark in brackets inside the stem
                    depth = max(0, depth + t.count("(") - t.count(")"))
                elif t in ("", ":"):
                    pass
                elif _ENUM.match(t) and not _DECLARATION.search(t):
                    items.append(_ENUM.sub("", t))
                elif items and not items[-1].rstrip().endswith("."):
                    items[-1] += " " + t
                elif not items and len(used) < 3 and not stem.rstrip().endswith((".", ":")) and not _DECLARATION.search(t):
                    stem += " " + t
                else:
                    break
                used.append(order[i])
                i += 1
            stem = stem.strip().rstrip(":").strip()
            texts = [f"{stem} {it.strip().rstrip(',;')}" for it in items if it.strip()] or [stem]
            ev = doc.evidence(used, stem)
            for text in texts:
                if text not in {c.text for c in self.out.consents}:
                    self.out.consents.append(Consent(text=text, kind="declaration", evidence=[ev]))

    def _text_roles(self) -> None:
        """Instructions and page furniture are left out by name, with the count per page."""
        doc = self.doc
        for role, reason in (("instruction", "PAPER_INSTRUCTION"), ("page_furniture", "PAGE_FURNITURE")):
            by_page: dict[int, list[str]] = {}
            for rid in doc.order:
                if doc.fo.roles.get(rid) == role and doc.text(rid):
                    by_page.setdefault(doc.page(rid), []).append(rid)
            for page, rids in sorted(by_page.items()):
                self.out.dropped.append(Dropped(what=doc.text(rids[0])[:120], reason=reason, page=page, count=len(rids)))

    def _composite(self) -> None:
        """Design 6.4.4: one selector, every variant's sections shown by it; a section that is word for word the
        same in several variants is written once. Never a second form."""
        if not self.variants:
            return
        titles = [v.title for v in self.variants]
        first: dict[tuple, dict[str, Any]] = {}
        for role, s in list(self.secs.items()):
            if s["variant"] is None or not s["fields"]:
                continue
            same = (s["title"], tuple((f.label, f.type, tuple(f.options)) for f in s["fields"]))
            if same not in first:
                s["variants"] = {s["variant"]}
                first[same] = s
                continue
            kept = first[same]
            kept["variants"].add(s["variant"])
            into = {new.key: old.candidate for old, new in zip(kept["fields"], s["fields"])}
            for cid, d in list(self.disp.items()):
                if d.fate == "FIELD" and d.key in into and into[d.key]:
                    self.disp[cid] = Disposition(candidate=cid, fate="MERGED", into=into[d.key], why="SAME_ALTERNATIVE")
            del self.secs[role]
        for s in first.values():
            conds = [Cond(field=SELECTOR_KEY, is_=titles[v]) for v in sorted(s["variants"])]
            if len(conds) < len(titles):
                s["show_if"] = conds[0] if len(conds) == 1 else Cond(any_of=conds)
        quotes = [self.doc.evidence(list(v.runs), " ".join(self.doc.text(r) for r in v.runs)) for v in self.variants]
        selector = BriefField(key=SELECTOR_KEY, label=SELECTOR_LABEL, type="RADIO", options=titles, required=True,
                              required_basis="substance", evidence=quotes)
        head = {"title": "Rodzaj wniosku", "role": "matter/rodzaj_wniosku", "fields": [selector], "repeating": False, "variant": None}
        self.secs = {head["role"]: head, **self.secs}
