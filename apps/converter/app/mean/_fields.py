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
_RESERVED_ROLES = frozenset({f"matter/{SELECTOR_KEY}", "matter/wybor_zalacznika"})   # sections the rules make


def _habit(name: str) -> re.Pattern[str]:
    return lexicon.regex("habits", habit=name)


_DATE_PLACE, _SIGN_SECTION = _habit("date_place"), _habit("signature_section")
_EXCLUSIVE, _EXCLUSIVE_WORDING, _MULTIPLE = _habit("exclusive_option"), _habit("exclusive_wording"), _habit("multiple_wording")
_COMPUTED, _ATTACH, _DECLARATION, _FUNCTION = _habit("computed"), _habit("attachments_section"), _habit("declaration"), _habit("function_word")
_PHRASES = {r["phrase"]: r["label"] for r in lexicon.rows("phrases")}
_ENUM = re.compile(r"^\s*(?:\d+[.)]|[a-z]\)|[-–•])\s*")
_LINE_KINDS = ("leader", "line_block", "blank_in_sentence")


_YES_NO = {"tak", "nie"}
# A name asked of a third person (the candidate, the ward) is a field of the matter, never the applicant's own name
# (set judged-09 ODS/XLSX: "Imię i nazwisko kandydata" under the heading "Wnioskodawca").
_THIRD_PERSON = re.compile(r"(kandydat|podopieczn|zawodnik|sportowc|trener|dzieck|uczestnik)\w*")
# "A/B* lub C D/E F*" with "niepotrzebne skreślić": two starred alternatives joined by "lub" are one choice of two
# phrases (set judged-07 PDF); each side keeps its own words.
_ALT_OR = re.compile(r"(\w[\w-]*(?:\s*/\s*\w[\w-]*)+)\s*\*+\s+lub\s+((?:[\w-]+\s+){0,3}\w[\w-]*(?:\s*/\s*\w[\w-]*)+(?:\s+[\w-]+){0,2})\s*\*+")
_DECLARE = re.compile(r"oświadczam\b", re.IGNORECASE)
# Attachments named in running text (audit T2): a list under "Załączniki ...:", "należy / można dołączyć X",
# "w załączeniu X", "X załączyć do wniosku"; a row "N. X  TAK  NIE" of an attachments table.
_ATT_LIST = re.compile(r"^(?:\d{1,2}\.\s*)?(?:załączniki\b[^:]{0,40}|do wniosku\s+(?:należy|można)\s+(?:dołączyć|załączyć))\s*:$", re.IGNORECASE)
_ATT_ITEM = re.compile(r"^\s*(?:[-–•]|\d{1,2}[.)]|[a-z]\))\s*(?=\w)")
_ATT_SAY = re.compile(r"\b(?:należy|można|trzeba)\s+(?:dołączyć|załączyć)\s+(?!:)(.+)|\bw\s+załączeniu\s+(.+)", re.IGNORECASE)
_ATT_BEFORE = re.compile(r"(?:^|[(,;:–-]\s*)([^(),;:–-]{6,80}?)\s+(?:należy\s+)?załączyć\s+do\s+wniosku", re.IGNORECASE)
# The words after the verb do not name a document: "w terminie 7 dni", "do akt sprawy", "(zaznaczyć właściwe):", a list
# header with words before its colon ("następujące dokumenty:", "przedkładam:").
_ATT_NOT_ITEM = re.compile(r"\(|(?:do|w|we|na|po|przed|od|z|ze|nr|najpóźniej|niezwłocznie|następując\w*|poniższ\w*|niżej|przedkładam|przesyłam"
                           r"|przekazuję|przedstawiam|składam)\b|.*:\s*$", re.IGNORECASE)
_ATT_IF = re.compile(r",?\s+(?:jeżeli|jeśli|w\s+przypadku|gdy)\b", re.IGNORECASE)
# The condition of an either-or pair says the OTHER item is not required ("jeżeli nie jest wymagany X"), not just "nie".
_NOT_REQUIRED = re.compile(r"\bnie\s+(?:jest|są|będzie|będą)\s+(?:wymagan|konieczn|potrzebn)\w*|\bnie\s+dotyczy\b|\bw\s+przypadku\s+braku\b",
                           re.IGNORECASE)
_ATT_MAY = re.compile(r"\bmożna\b|\bewentualn|opcjonaln|w\s+przypadku|\bjeżeli\b|\bjeśli\b", re.IGNORECASE)
# WP-C1: a negation that stands at most _NEGATION_REACH characters before a required cue blocks the cue: the word
# "nie" ("nie jest wymagany", "nie są wymagane", "nie dotyczy ... wymaganego"), or "nie" glued to the cue
# ("niewymagane", and "niejestwymagane" of a footnote, whose whitespace is removed).
_NEGATION = re.compile(r"\bnie\b|niedotyczy|nie(?:jest|są|będzie|będą)?$")
_NEGATION_REACH = 40
_REQUIRED_WORDING = _habit("required_wording")      # "należy wypełnić", "musi zawierać"


def _says_required(text: str) -> bool:
    """The paper's own words mark this text required: a cue of the habits `required` and `required_wording` that no
    negation precedes. An asterisk is no cue: on these papers it marks a footnote ("niepotrzebne skreślić")."""
    low = text.casefold()
    return any(not _NEGATION.search(low[max(0, m.start() - _NEGATION_REACH): m.start()])
               for rx in (REQUIRED, _REQUIRED_WORDING) for m in rx.finditer(low))


_OPTIONAL_WORDING, _CONDITIONAL = _habit("optional_wording"), _habit("conditional")
_BRACKET = re.compile(r"\(([^()]*)\)")      # an aside of a section title: "Dane do kontaktu (pola obowiązkowe)"


def _aside_says_required(text: str) -> bool:
    """A hint, or a bracket of a section title, marks required unless a condition stands beside the cue
    ("wymagane w przypadku ..."): that is a condition of the paper, not its "required"."""
    return _says_required(text) and not _CONDITIONAL.search(text.casefold())


def _says_optional(text: str) -> bool:
    """The paper's own words mark this text optional: the habit `optional`, or the wording "ewentualne", "jeśli
    różni się od", "w razie potrzeby", "nie jest wymagane"."""
    low = text.casefold()
    return bool(OPTIONAL.search(low) or _OPTIONAL_WORDING.search(low))


_YES_NO_ROW = re.compile(r"^\s*(?:\d{1,2}[.)]\s*)?(.+?)\s+TAK\s+NIE\s*$")
_SENTENCE_END = (".", "!", "?")
# No fragments (audit T3 to T5): the kinds of place that take a label from the text around them, the labels that are
# the place's own (heading, widget name, cell, group question), words that end a line in the middle of a sentence, a
# printed amount ("15 zł 00 gr"), a unit printed after a blank ("dni").
_PLAIN = ("leader", "line_block", "blank_in_sentence", "cell", "comb")
_OWN_LABEL = ("header", "widget_name", "same_cell", "question")
_GLUE = {"i", "oraz", "lub", "w", "na", "do", "o", "z", "dla", "przy", "a", "że", "który", "które", "która", "się", "od", "po", "za"}
_ABBR = {"od", "do", "nr", "ul", "tel", "kod", "woj", "gm", "pow", "m"}   # short words that are labels by themselves
_AMOUNT = re.compile(r"^\W*\d[\d\s.,]*\s*(?:zł|pln)\b(?:\s*\d{1,2}\s*gr)?\W*$", re.IGNORECASE)
_UNIT = re.compile(r"(dni|miesi\w+|lat|godzin\w*|sztuk\w*)\b", re.IGNORECASE)


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
        self.quote: dict[str, Evidence] = {}            # candidate id -> evidence of a label made of several printed lines

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
        self._attachments_in_text()
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
        if self._heading_edge(c):
            return self._left(c, "EXPLANATION", label)
        if c.label is not None and c.kind in _PLAIN and c.label.how not in _OWN_LABEL:
            new = self._clarify(c, raw, label)
            if new != raw:
                raw = new
                label, hint, optional = clean_label(raw, doc.strike)
        if label and _AMOUNT.match(label):
            return self._left(c, "EXPLANATION", label)    # a printed rate or amount: text of the form
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
        if self._caption_line(c, prev):
            return None
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
        if c.kind == "choice_group" and c.label is not None and not all(any(rx.search(o.text) for rx, _ in lexicon.compiled("applicants", table="wording"))
                                                for o in c.options):
            # Boxes under the applicant heading whose options are not kinds of applicant the standard pages ask
            # ("Prezydent Miasta" / "Klub sportowy", set judged-09): the paper's own question, a field of the matter.
            # Only a group with a label of its own: an unlabelled group would be asked under the bare heading.
            return False
        for rx, row in lexicon.compiled("applicants", table="label"):
            if rx.search(low):
                if row.get("role") == "standard/twoje_dane" and not row.get("concept") and _THIRD_PERSON.search(low):
                    return False
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

    # -- no fragments (audit T3, T4, T5) --------------------------------------------------------------------------------

    def _heading_edge(self, c: Candidate) -> bool:
        """A drawn strip of one line, flush under the heading that is its only label, is the heading's own edge
        (set judged-08: two heading bands and an attachments heading became fields), not a place to write."""
        s = self.doc.sections.get(c.section or "")
        if c.kind != "cell" or c.label is None or c.label.how != "header" or c.box is None or s is None or not s.runs:
            return False
        hb = self.doc.runs[s.runs[-1]][1].box if s.runs[-1] in self.doc.runs else None
        if hb is None:
            return False
        b = c.box
        return -2 <= b[1] - hb[3] <= 3 and b[3] - b[1] <= 1.6 * (hb[3] - hb[1]) and min(b[2], hb[2]) - max(b[0], hb[0]) > 0

    def _above(self, rid: str) -> str | None:
        """The run printed right above this one: by geometry on a page with boxes (nearest above, covering the left
        edge of this run up to an indent), by reading order in a flow document."""
        doc = self.doc
        if rid not in doc.runs:
            return None
        page, run = doc.runs[rid]
        if run.box is None:
            i = doc.pos[rid] - 1
            return doc.order[i] if i >= 0 and doc.page(doc.order[i]) == page else None
        lb = run.box
        h = max(4.0, lb[3] - lb[1])
        best: tuple[float, str] | None = None
        for o in doc.order:
            ob = doc.runs[o][1].box
            if o == rid or doc.page(o) != page or ob is None or not doc.text(o):
                continue
            gap = lb[1] - ob[3]
            if -2 <= gap <= 1.6 * h and ob[0] - lb[0] <= 45 and ob[2] > lb[0] and ob[1] < lb[1]:
                if best is None or gap < best[0]:
                    best = (gap, o)
        return best[1] if best else None

    def _wraps_into(self, rid: str) -> bool:
        """The line above says its sentence goes on: no full stop, long enough to be a sentence, or it ends on a
        conjunction or a preposition."""
        t = self.doc.text(rid)
        words = t.split()
        return bool(t) and (t[-1].isalnum() or t[-1] == ",") and (len(words) >= 5 or words[-1].casefold() in _GLUE)

    def _lead_in(self, c: Candidate, raw: str) -> tuple[str, list[str]] | None:
        """A label that starts lower-case continues the body line above ("... przy" + "ocenie wniosku"; the row
        header of a counting row): the lines it continues, up to three, are prepended. A numbered heading above
        the wrapped lines opens the question. None when nothing is above that says its sentence goes on."""
        doc = self.doc
        assert c.label is not None
        first = min((r for r in c.label.runs if r in doc.runs), key=lambda r: doc.pos[r], default=None)
        if first is None or c.label.spans and c.label.spans[0].start > 0:
            return None
        leaders = {r for o in doc.fo.candidates if o.kind in _LINE_KINDS for r in o.runs}
        taken: list[str] = []
        at = first
        while len(taken) < 3:
            up = self._above(at)
            if up is None or up in leaders or up in self.head_runs or doc.text(up).isupper() or not self._wraps_into(up):
                break           # a title, a line in capitals or a blank is no sentence that goes on
            above = self._above(up)
            role = doc.role(up)
            if role == "heading":
                if taken and NUMBERING.match(doc.text(up)):
                    taken.append(up)
                break
            if role != "body" or (above is not None and above in leaders):
                break           # a caption printed under a blank belongs to that blank
            taken.append(up)
            at = up
            if not doc.text(up)[:1].islower():
                break
        if not taken:
            return None
        return " ".join(doc.text(r) for r in reversed(taken)), list(reversed(taken))

    def _clarify(self, c: Candidate, raw: str, label: str) -> str:
        """The label of a place as the paper means it. A lower-case start continues the line above; the last line
        of a sentence ("... i akceptuję wszystkie jego postanowienia.") and a stub of fewer than four letters
        ("Mui") are no label: the caption under the blank, or the unit after it, is taken, else nothing."""
        doc = self.doc
        assert c.label is not None
        text = NUMBERING.sub("", raw).strip()
        low = text.casefold()
        letters = sum(ch.isalpha() for ch in text)
        known = letters >= 4 or low.rstrip(".") in _ABBR or low in _PHRASES or any(rx.search(low) for rx, _ in lexicon.compiled("concepts")) \
            or bool(_DATE_PLACE.search(low))
        first = next((r for r in c.label.runs if r in doc.runs), None)
        above = self._above(first) if first else None
        end_of_sentence = c.kind != "line_block" and text.endswith(".") and len(text.split()) >= 4 and above is not None and self._wraps_into(above)
        if known and not end_of_sentence:
            if text[:1].islower() and low not in _PHRASES:    # a phrase the lexicon knows is a whole label ("w miejscowości")
                lead = self._lead_in(c, raw)
                if lead is not None:
                    self.quote[c.id] = doc.evidence([*lead[1], *c.label.runs], f"{lead[0]} {text}", c.id)
                    return f"{lead[0]} {text}"
            return raw
        place = [doc.pos[r] for r in c.runs if r in doc.pos]
        nxt = doc.order[max(place) + 1] if place and max(place) + 1 < len(doc.order) else None
        inside = c.spans[-1] if c.spans and c.spans[-1].run in doc.runs else None
        tail = doc.runs[inside.run][1].text[inside.end:].strip() if inside else ""   # the same printed line goes on
        unit = _UNIT.match(tail or (doc.text(nxt) if nxt is not None and doc.role(nxt) == "body" else ""))
        if unit and not end_of_sentence:
            return f"Liczba {unit.group(1).casefold()}"
        if nxt is not None and not tail and doc.role(nxt) == "body" and doc.page(nxt) == c.page:
            t = doc.text(nxt)
            if 1 <= len(t.split()) <= 5 and not t.endswith((".", "!", "?", ":", ";")) and t[:1].isalpha():
                self.quote[c.id] = doc.evidence([nxt], t, c.id)
                return t
        # nothing better found: the last line of a sentence is no label; a short word may still be one ("Cel")
        return "" if end_of_sentence else raw

    def _caption_line(self, c: Candidate, prev: Candidate | None) -> bool:
        """Audit T4: a second dotted line whose only label is the caption under it, in brackets or between slashes,
        belongs to the blank above; the caption becomes that field's hint (set judged-06)."""
        doc = self.doc
        if prev is None or c.kind not in ("leader", "line_block") or prev.kind not in _LINE_KINDS or c.label is None \
                or c.label.how != "leader" or len(c.label.runs) != 1 or prev.section != c.section or prev.page != c.page:
            return False
        def caption(t: str) -> bool:
            return len(t) > 4 and ((t[0] == "(" and t[-1] == ")") or (t[0] == "/" and t[-1] == "/"))

        cap = doc.text(c.label.runs[0]) if c.label.runs[0] in doc.runs else ""
        if not caption(cap):
            return False
        if prev.label is not None and len(prev.label.runs) == 1 and prev.label.runs[0] in doc.runs and caption(doc.text(prev.label.runs[0])):
            return False        # the blank above is named by a caption of its own: two captioned blanks, never one field
        root = prev.id
        while root in self.disp and self.disp[root].fate == "MERGED" and self.disp[root].why == "LINE_BLOCK":
            root = self.disp[root].into or ""
        target = self.field_of.get(root)
        if target is None or target.hint or not self._adjacent(prev, c):
            return False        # a field that has its caption already is not given the caption of the next blank
        target.hint = target.hint or cap[1:-1].strip()
        if target.type == "TEXT_FIELD" and target.concept is None:
            target.type, target.length = "TEXTAREA", None
        self._set(c, "MERGED", into=prev.id, why="LINE_BLOCK")
        return True

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
        answers = c.kind == "choice_group" and bool(c.options) and all(t.strip(" .:").casefold() in _YES_NO for t, _ in named)
        if answers:
            # "1. Załącznik A  TAK  NIE" (set judged-08): each row of the table names an attachment the filer may add;
            # a row the finder merged into the group is read from its own printed line.
            rids = list(dict.fromkeys([*(c.label.runs if c.label else []), *(r for o in c.options for r in [*o.runs, *(s.run for s in o.spans)])]))
            named = [(label, list(c.label.runs) if c.label else [])] if label else []
            for rid in rids:
                m = _YES_NO_ROW.match(doc.text(rid)) if rid in doc.runs else None
                if m:
                    named.append((clean_label(m.group(1))[0], [rid]))
        made: list[tuple[str, str | None]] = []
        for text, runs in named:
            if not text or text.strip(" .:").casefold() in _YES_NO:   # a column of answers, not a named item
                continue
            if any(a.label.casefold() == text.casefold() for a in self.out.attachments):
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

    def _attachments_in_text(self) -> None:
        """Audit T2: attachments the paper names in running text become uploads of the matter, each labelled with
        its item. Optional when the paper says "można", "ewentualnie", "jeżeli", "w przypadku"; an item whose
        condition is the absence of another item ("..., jeżeli nie jest wymagany <the other>") makes an either-or
        pair: one choice and two uploads shown by it. Standard pages (proxy, fee) cover theirs."""
        doc = self.doc
        lines = self._lines()
        found: list[tuple[str, list[str], bool]] = []          # (item text, runs, optional by wording)
        i = 0
        while i < len(lines):
            rids, text = lines[i]
            if _ATT_LIST.match(text):
                may = bool(_ATT_MAY.search(text))
                i += 1
                mark0, count = None, 0
                while i < len(lines) and _ATT_ITEM.match(lines[i][1]):
                    mark = _ATT_ITEM.match(lines[i][1]).group(0).strip()
                    kind = "n" if mark[0].isdigit() else "a" if mark[0].isalpha() else "-"
                    count += 1
                    if mark0 is None:
                        mark0 = kind
                    if kind != mark0 or (kind == "n" and int(re.match(r"\d+", mark).group(0)) != count) or doc.role(lines[i][0][0]) == "heading":
                        break       # "5. Oświadczenie" after the items "1." and "2." (or after dashes) is the next section, not an item
                    item, used = _ATT_ITEM.sub("", lines[i][1]), list(lines[i][0])
                    x0 = self._x0(lines[i][0])
                    i += 1
                    while i < len(lines) and not _ATT_ITEM.match(lines[i][1]) and x0 is not None \
                            and (self._x0(lines[i][0]) or 0) > x0 + 4 and doc.page(lines[i][0][0]) == doc.page(used[0]):
                        item, used = item + " " + lines[i][1], used + list(lines[i][0])
                        i += 1
                    found.append((item, used, may))
                continue
            window, used = text, list(rids)
            for k in (1, 2):                                   # the sentence may wrap over two more lines
                if window.rstrip().endswith((".", ")")) or i + k >= len(lines) or not lines[i + k][1][:1].islower():
                    break
                window, used = window + " " + lines[i + k][1], used + list(lines[i + k][0])
            m = _ATT_SAY.search(window)
            if m and (_ATT_NOT_ITEM.match(m.group(1) or m.group(2) or "")
                      or re.search(r"\bnie\s*$", window[: m.start()], re.IGNORECASE)):
                m = None        # "X należy załączyć do wniosku" names X before the verb; "nie można dołączyć X" forbids it
            if m and m.start() < len(text):
                k = 1 if m.group(1) else 2
                found.append((m.group(k).split(". ")[0], used, bool(_ATT_MAY.search(window[: m.start(k)]))))
            else:
                b = _ATT_BEFORE.search(window)
                if b and b.start(1) < len(text) and not re.search(r"\bnie$|^\s*(?:należy|można|trzeba)\s*$", b.group(1), re.IGNORECASE):
                    found.append((b.group(1), used, bool(_ATT_MAY.search(window))))
            i += 1
        made: list[tuple[Attachment, str]] = []                # (upload, its condition)
        for item, used, may in found:
            item = re.sub(r"\s+", " ", item).strip(" .;,)")
            cut = _ATT_IF.search(item)
            cond = item[cut.end():].strip() if cut else ""
            label = item[: cut.start()] if cut else item
            if len(label) > 90:
                stop = re.search(r",\s|\s\(", label[20:])
                label = label[: 20 + stop.start()] if stop else label
            label = sentence_case(label.strip(" ,.;:–-"))
            if len(label) < 4 or any(a.label.casefold() == label.casefold() for a in self.out.attachments):
                continue
            cover = next((row["role"] for rx, row in lexicon.compiled("habits", habit="attachment_cover") if rx.search(label)), None)   # the item, not its condition
            a = Attachment(**some(label=label, covered_by=cover, key=self.keys.unique(key_of(label, "zalacznik")),
                                  required=not (may or cut) and cover is None,
                                  evidence=[doc.evidence(used, " ".join(doc.text(r) for r in used)[:400])]))
            self.out.attachments.append(a)
            if cover is None:
                made.append((a, cond))
        self._either_or(made)

    def _either_or(self, made: list[tuple[Attachment, str]]) -> None:
        """"B, jeżeli nie jest wymagany A": the filer gives A or B. One RADIO of the two labels, each upload shown by
        its option and required there."""
        stem = lambda t: {w[:5] for w in re.findall(r"\w{4,}", t.casefold())}   # noqa: E731
        for b, cond in made:
            if not _NOT_REQUIRED.search(cond):
                continue
            a = next((x for x, _ in made if x is not b and x.show_if is None and len(stem(x.label) & stem(cond)) >= 2), None)
            if a is None or b.show_if is not None:
                continue
            key = self.keys.unique(key_of(f"{a.label} lub {b.label}", "wybor_zalacznika"))
            f = BriefField(key=key, label="Który z dokumentów załączasz?", type="RADIO", options=[a.label, b.label], required=True,
                           required_basis="paper", evidence=[*a.evidence, *b.evidence])
            sec = self.secs.setdefault("matter/wybor_zalacznika", {"title": "Załączniki", "role": "matter/wybor_zalacznika",
                                                                    "fields": [], "repeating": False, "variant": None})
            sec["fields"].append(f)
            for x in (a, b):
                x.show_if, x.required = Cond(field=key, is_=x.label), True

    def _x0(self, rids: list[str]) -> float | None:
        box = self.doc.runs[rids[0]][1].box if rids and rids[0] in self.doc.runs else None
        return box[0] if box is not None else None

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

    def _field(self, c: Candidate, raw: str, label: str, hint: str | None, optional: bool, opts: list[ChoiceOption] | None = None) -> None:
        doc, low = self.doc, label.casefold()
        if c.kind == "choice_group" and opts is None:
            parts = self._split_group(c)
            if len(parts) > 1:
                for i, (sub, part) in enumerate(parts):
                    self._field(c, raw if i == 0 else sub, label if i == 0 else sub, hint if i == 0 else None, optional, part)
                    if i == 0:
                        first = self.disp.get(c.id)
                if first is not None:
                    self.disp[c.id] = first
                return None
        options: list[str] = []
        concept = length = None
        shown = sentence_case(label)
        if c.kind == "box" and _DECLARE.match(label):
            return self._declared_box(c, label, optional)
        if c.kind == "box":
            # One box outside any group: an option of a question the finder could not group, or a yes-or-no
            # question. Reading it as a field would look right and may be wrong; the official decides.
            self._set(c, "AWAITING_DECISION", decision=f"box_{c.id}")
            self.out.warnings.append(Warning(code="AMBIGUOUS_GROUP", page=c.page, candidate=c.id,
                                             detail=f"a single box outside any group: {label[:80]!r}; an option or a yes-or-no question"))
            return None
        if c.kind == "choice_group":
            for o in (c.options if opts is None else opts):
                text = clean_option(o.text)
                if text and text not in options:
                    options.append(text)
            if len(options) < 2:
                self._set(c, "AWAITING_DECISION", decision=f"options_{c.id}")
                self.out.warnings.append(Warning(code="AMBIGUOUS_GROUP", page=c.page, candidate=c.id, detail="a choice group with fewer than two readable options"))
                return None
            kind = self._choice_kind(c, raw, options)
        else:
            kind, concept, length, shown = self._typing(c, label, low, shown, hint or self._hint_after(c))
        key = self.keys.unique(key_of(shown))
        notes = [doc.footnote(m) for m in c.footnotes]
        said = hint or self._hint_after(c) or ""
        optional = optional or _says_optional(low) or any(_says_optional(n) for n in notes) or _says_optional(said)
        marked = _says_required(low) or any(_says_required(n) for n in notes) or _aside_says_required(said)
        if not (optional or marked):        # the field's own words (label, hint, footnote) outrank the title of its section
            head = doc.sections.get(c.section or "")
            title = head.title if head is not None else ""
            optional = _says_optional(title)
            marked = any(_aside_says_required(aside) for aside in _BRACKET.findall(title))
        required = not optional
        basis = ("paper" if marked else "inferred") if required else None
        f = BriefField(**some(key=key, label=shown, type=kind, concept=concept, required=required, required_basis=basis,
                              hint=hint or self._hint_after(c), options=options, length=length if kind == "TEXT_FIELD" else None,
                              candidate=c.id, conf=self._conf(c), evidence=[self.quote.get(c.id) or doc.cand_evidence(c)]))
        if basis == "inferred":
            self.out.warnings.append(Warning(code="REQUIRED_INFERRED", field=key, candidate=c.id, page=c.page,
                                             detail="the paper does not say whether this is required; marked required by our rule"))
        if _COMPUTED.search(low):
            self.out.dropped.append(Dropped(what=f"{label}: printed arithmetic, the value is typed", reason="COMPUTED_VALUE", page=c.page))
        self._add(c, f, self._section(c)["role"])
        return None

    def _split_group(self, c: Candidate) -> list[tuple[str, list[ChoiceOption]]]:
        """A free line ending in ":" printed between the options of one group ("Rodzaje ...:" boxes, "Dyscypliny:"
        boxes; set judged-09 PDF) heads a second group: each part keeps at least two options. No such line: one part."""
        doc = self.doc
        where = [[doc.pos[r] for r in [*o.runs, *(s.run for s in o.spans)] if r in doc.pos] for o in c.options]
        if not where or not all(where):      # an empty group cannot come from the finder; no crash if one ever does
            return [("", list(c.options))]
        parts: list[tuple[str, list[ChoiceOption]]] = [("", [c.options[0]])]
        for i in range(1, len(c.options)):
            head = next((doc.text(doc.order[p]) for p in range(max(where[i - 1]) + 1, min(where[i]))
                         if doc.role(doc.order[p]) == "body" and doc.text(doc.order[p]).endswith(":")
                         and 1 <= len(doc.text(doc.order[p]).split()) <= 6), None)
            if head and len(parts[-1][1]) >= 2 and len(c.options) - i >= 2:
                parts.append((head.rstrip(" :"), []))
            parts[-1][1].append(c.options[i])
        return parts

    def _declared_box(self, c: Candidate, label: str, optional: bool) -> None:
        """One box beside "Oświadczam, że ..." (set judged-08 PDF, the composter): the applicant ticks it to declare.
        A CHECKBOX of the matter whose label is the whole sentence; never required, the paper asks it only of some."""
        doc = self.doc
        runs = list(c.label.runs) if c.label else []
        text = label
        for rid in self._below(runs, 3) if not text.endswith(_SENTENCE_END) else []:
            text += " " + doc.text(rid)
            runs.append(rid)
            if text.endswith(_SENTENCE_END):
                break
        text = text.rstrip(" .")
        f = BriefField(key=self.keys.unique(key_of(text)), label=text, type="CHECKBOX", required=False, candidate=c.id,
                       conf=self._conf(c), evidence=[doc.evidence(runs, text, c.id)])
        self._add(c, f, self._section(c)["role"])

    def _below(self, runs: list[str], limit: int) -> list[str]:
        """Free body lines printed right under the last of these runs, starting near its left edge: the rest of a
        wrapped sentence. Geometry only; a flow document gives none."""
        doc = self.doc
        boxed = [(doc.runs[r][0], doc.runs[r][1].box) for r in runs if r in doc.runs and doc.runs[r][1].box is not None]
        if not boxed:
            return []
        page, first = boxed[0]
        out: list[str] = []
        last = boxed[-1][1]
        for _ in range(limit):
            h = max(4.0, last[3] - last[1])
            near = [r for r in doc.order if doc.page(r) == page and doc.role(r) == "body" and r not in runs and r not in out
                    and doc.runs[r][1].box is not None and 0 <= doc.runs[r][1].box[1] - last[1] <= 2.2 * h
                    and doc.runs[r][1].box[1] > last[1] + 0.5 * h and abs(doc.runs[r][1].box[0] - first[0]) <= 30]
            if not near:
                break
            r = min(near, key=lambda x: doc.runs[x][1].box[1])
            out.append(r)
            last = doc.runs[r][1].box
        return out

    def _typing(self, c: Candidate, label: str, low: str, shown: str, hint: str | None = None) -> tuple[str, str | None, int | None, str]:
        """Type, concept, length and wording of a plain place (design 6.4.3 rows 1 and 2, the label rules)."""
        doc = self.doc
        if low in ("do", "do dnia") and self.last is not None and self.last.type == "DATEPICKER" and self.last.label.endswith(" od"):
            return "DATEPICKER", "date", None, self.last.label[:-2] + "do"   # "od ... do ...": two dates in one section
        if c.kind == "comb" and c.mask and re.search(r"[DMR]{2}", c.mask):
            return "DATEPICKER", "date", None, shown
        for rx, row in lexicon.compiled("concepts"):
            if rx.search(low) or (hint and row["type"] == "DATEPICKER" and rx.search(hint.casefold())):   # "(DD-MM-RRRR)"
                return row["type"], row.get("concept"), row.get("length"), row.get("label") or _PHRASES.get(low) or shown
        if low in _PHRASES:
            shown = _PHRASES[low]
        elif (c.label is not None and c.label.how == "sentence") or _FUNCTION.search(label):
            self.out.warnings.append(Warning(code="LABEL_RAW", page=c.page, candidate=c.id,
                                             detail=f"label kept as the paper's words: {label[:80]!r}"))
        return ("TEXTAREA" if c.kind == "line_block" else "TEXT_FIELD"), None, (c.cells if c.kind == "comb" else None), shown

    def _choice_kind(self, c: Candidate, raw: str, options: list[str]) -> str:
        """Design 6.4.3 "tick boxes that share a question"."""
        wording = " ".join([raw, *self._instructions_before(c)]).casefold()
        if _MULTIPLE.search(wording):     # "zaznacz wszystkie" over a long list is still several, not a SELECT
            return "CHECKBOX"
        if len(options) > 5:
            return "SELECT"
        if len(options) == 2 or _EXCLUSIVE_WORDING.search(wording) or any(_EXCLUSIVE.search(o.casefold()) for o in options):
            return "RADIO"
        # The paper does not say. One choice is the safe reading: the partner's exports hold no CHECKBOX group, and
        # an official widens a RADIO to several more easily than a citizen undoes a contradictory set of ticks.
        self.out.warnings.append(Warning(code="AMBIGUOUS_GROUP", page=c.page, candidate=c.id,
                                         detail="the paper does not say whether one or several options may be marked; one is asked"))
        return "RADIO"

    def _instructions_before(self, c: Candidate, reach: int = 4) -> list[str]:
        """The instruction lines right above a group, up to its heading ("(można zaznaczyć kilka odpowiedzi)"): the
        finder gives them the role instruction, so they are never the group's label."""
        doc = self.doc
        first = [doc.pos[r] for o in c.options for r in o.runs if r in doc.pos]
        at = min(first) if first else doc.cand_pos(c)   # from the first option: the label may be the heading above
        own = set(doc.cand_runs(c))
        out: list[str] = []
        seen = 0
        for rid in reversed(doc.order[:at]):
            text = doc.text(rid)
            role = doc.role(rid)
            if rid in own or not any(ch.isalnum() for ch in text):
                continue    # the group's own question, its box glyphs
            if role == "heading" or role == "owned" or seen >= reach:
                break       # the heading, a place of another candidate, or too far up
            seen += 1
            if role == "instruction":
                out.append(text)
        return out

    def _hint_after(self, c: Candidate) -> str | None:
        """ "(rodzaj uroczystości, np. wesele ...)" under a line is the hint of the field."""
        doc = self.doc
        place = [doc.pos[r] for r in c.runs if r in doc.pos]
        if not place or max(place) + 1 >= len(doc.order):
            return None
        nxt = doc.order[max(place) + 1]
        t = doc.text(nxt)
        if doc.role(nxt) in ("body", "instruction") and len(t) > 4 and (
                (t.startswith("(") and t.endswith(")")) or (t.startswith("/") and t.endswith("/"))):
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
        if role in _RESERVED_ROLES:
            role += "_papier"     # a paper heading "Rodzaj wniosku" must not overwrite the selector's section
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
        lines = self._lines()
        skip = 0                      # offset in this line up to which a pair that began on the line above reaches
        for i, (rids, text) in enumerate(lines):
            nxt = lines[i + 1] if i + 1 < len(lines) and doc.page(lines[i + 1][0][0]) == doc.page(rids[0]) else None
            window = text + " " + nxt[1] if nxt else text
            taken: list[tuple[int, int]] = [(0, skip)] if skip else []
            skip = 0
            for m in _ALT_OR.finditer(window):
                if m.start() >= len(text) or any(a <= m.start() < b for a, b in taken):
                    continue
                taken.append(m.span())
                skip = max(skip, m.end() - len(text) - 1)
                words = [re.sub(r"\s*/\s*", "/", m.group(k)).strip() for k in (1, 2)]
                if not any(same_choice(words, s) for s in seen):
                    seen.append(words)
                    self._alt_field(words, rids + (nxt[0] if nxt and m.end() > len(text) else []), m.group(0))
            for m in ALT.finditer(text):
                if any(a <= m.start() < b for a, b in taken):
                    continue
                words = alt_words(m)
                if is_grammar(words):
                    if m.group(1).casefold() not in grammar:
                        grammar.add(m.group(1).casefold())
                        self.out.dropped.append(Dropped(what=m.group(1), reason="GRAMMAR_VARIANT", page=doc.page(rids[0]), runs=rids))
                    continue
                if any(same_choice(words, s) for s in seen):
                    continue
                seen.append(words)
                self._alt_field(words, rids, text)

    def _alt_field(self, words: list[str], rids: list[str], quote: str) -> None:
        f = BriefField(key=self.keys.unique(key_of("_".join(words))), label=sentence_case(" lub ".join(words)), type="RADIO",
                       options=words, required=True, required_basis="paper", evidence=[self.doc.evidence(rids, quote)])
        self._section(None)["fields"].append(f)

    def _lines(self) -> list[tuple[list[str], str]]:
        """Runs of one printed line joined in reading order (a PDF splits "utrzymywanie" and its "*" into two runs);
        a run without a box (a flow document) is a line of its own. Clauses and page furniture are left out."""
        doc = self.doc
        out: list[tuple[list[str], str]] = []
        for rid in doc.order:
            if doc.fo.roles.get(rid) in ("clause", "page_furniture"):
                continue
            page, run = doc.runs[rid]
            if out and run.box is not None:
                prev = doc.runs[out[-1][0][-1]]
                pb, b = prev[1].box, run.box
                if prev[0] == page and pb is not None and abs(pb[1] - b[1]) <= 3 and b[0] >= pb[2] - 2:
                    out[-1] = (out[-1][0] + [rid], out[-1][1] + (" " if b[0] - pb[2] > 1.5 else "") + run.text)
                    continue
            out.append(([rid], run.text))
        return [(r, re.sub(r"\s+", " ", t).strip()) for r, t in out]

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
