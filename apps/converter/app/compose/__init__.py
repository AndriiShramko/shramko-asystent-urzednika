"""Composer (design 6.5): a brief in, the partner's form out, with what the sidecar needs to account for it.

    from app.compose import ComposeOptions, compose
    result = compose(brief, ComposeOptions())
    result.form.to_json_bytes()      # the partner's object and nothing else (D1)
    result.origins                   # form id -> "paper" | "standard"
    result.brief_keys                # form id -> key of the brief field it was made from
    result.paths                     # form id -> the meaning path the id was made from (D10)
    result.remarks                   # what the composer inferred, left out or could not do: never silent

The form is built only through the constructor helpers of app.model.form. Standard sections come from
`compose.library`; names and ids from `compose.names`; HTML from `compose.html`; conditions from `compose.query`.
The same brief and options always give the same bytes.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, replace
from dataclasses import field as dc_field
from typing import Any, Mapping

from app import lexicon
from app.model.brief import Addressee, Brief, BriefField
from app.model.form import (
    EMPTY_HTML,
    ConsentItem,
    Form,
    Option,
    Question,
    State,
    checkbox,
    consent_section,
    datepicker,
    file_uploader,
    info_section,
    number,
    radio,
    section,
    select,
    tab,
    text_block,
    text_field,
    textarea,
)

from . import dictionaries
from . import fixes
from . import library as lib
from . import required as required_rule
from . import validators
from .html import doc, p
from .library import EXPORT_1, EXPORT_5, Standard, Who
from .names import ID_NAMESPACE, ComposeError, Ids, Names, slug
from .query import Place, Pred, from_brief, refs, write
from .spec import Comp, Page, Sec

__all__ = ["EXPORT_1", "EXPORT_5", "ComposeError", "ComposeOptions", "ComposeResult", "Remark", "Standard", "compose",
           "pages_without_fixed_content"]

TITLE_MISSING = "Formularz bez tytułu"
NO_MATTER_TEXT = ("Z dokumentu nie odczytano żadnego pola sprawy: formularz zawiera tylko sekcje standardowe "
                  "(i ewentualnie teksty lub opłatę z papieru). Pola sprawy trzeba uzupełnić ręcznie.")
# Concept of a brief field -> the partner's validator (D8): the table and the rule live in compose.validators.
CONCEPT_VALIDATORS = validators.CONCEPT_VALIDATORS
# Shapes that no export shows (skill rule 14): each use is a remark.
INFERRED_SHAPES = ("DATEPICKER", "CHECKBOX", "INFO_SECTION")
SINGLE_BOX_OPTION = "Tak"
_NO_VALIDATION = ("TEXT_BLOCK", "INFO_SECTION", "CONSENT_SECTION")
# W11 CLERK-S. Meaning paths of the two standard nodes a ready fix writes to (compose.fixes).
ADDRESSEE_NODE = "dane/adresat/nazwa"
CONSENT_NODE = "kontakt/zgoda"
# The clause read by OCR is attached to the consent by default only when the mean word confidence of its page is
# at least this (Tesseract's own number, 0 to 1); below it the official is offered the text and it is not written.
CLAUSE_OCR_ATTACH = 0.85
USUALLY_OPTIONAL = fixes._USUALLY_OPTIONAL


@dataclass(frozen=True)
class ComposeOptions:
    finish_style: str = "export"              # D5: "export" (SECTION with a TEXT_BLOCK) | "info_section"
    validators: bool = True                   # D8: False gives empty lists everywhere, as in the exports
    required_policy: str = "inferred"         # compose.required: "inferred" (design 6.4.3) | "paper" (no inferred REQUIRED)
    repeating_style: str = "native"           # "native" (REPEATING_SECTION) | "section" (one plain section)
    statutory_representative: bool = True     # D16
    poa_exemption: bool = False               # D17
    form_key: str | None = None               # D10: None is the slug of the title
    id_namespace: uuid.UUID = ID_NAMESPACE
    standard: Standard | None = None          # where the exports differ; None: our defaults, switched by the brief
    max_fields_per_page: int = 10             # design 6.5.2


@dataclass(frozen=True)
class Remark:
    """One thing the composer did that a reviewer should see. Codes: INFERRED_SHAPE, CONDITION_NOT_WRITTEN,
    SECTION_SPLIT, REPEATING_FLATTENED, STEP_NOTE_ADDED, MARKUP_IN_LABEL, TITLE_MISSING, ADDRESSEE_MISSING,
    APPLICANTS_ASSUMED, SOLE_TRADER_AS_ENTITY, CLAUSE_LINK_MISSING, NO_MATTER, EXTRA_NOT_PLACED."""

    code: str
    detail: str
    field: str | None = None                  # form id, when the remark is about one node
    # W11 CLERK-S: the ready fix as a hint (places named by meaning); `compose.fixes.resolve` makes the final object
    fix: Mapping[str, Any] | None = dc_field(default=None, compare=False, hash=False)


@dataclass(frozen=True)
class ComposeResult:
    form: Form
    origins: dict[str, str]
    brief_keys: dict[str, str]
    paths: dict[str, str]
    remarks: tuple[Remark, ...]
    # Brief keys of the fields the brief requires by inference and the composer wrote without REQUIRED
    # (compose.required): for such a key the brief's own warning REQUIRED_INFERRED no longer describes the form.
    required_dropped: tuple[str, ...] = ()


def compose(brief: Brief, options: ComposeOptions | None = None) -> ComposeResult:
    o = options or ComposeOptions()
    if o.required_policy not in required_rule.POLICIES:
        raise ComposeError(f"required_policy {o.required_policy!r} is not one of {required_rule.POLICIES}")
    remarks: list[Remark] = []
    dropped: list[str] = []
    title = brief.title.value.strip()[:255] if brief.title.status == "stated" and (brief.title.value or "").strip() else ""
    if not title:
        title = TITLE_MISSING
        remarks.append(Remark("TITLE_MISSING", f"the brief states no title ({brief.title.status}); a placeholder is written"))
    form_key = o.form_key or slug(title, fallback="formularz")
    std, who = _standard(brief, o, remarks)

    pages = [Page("dane", "Dane", _parties(brief, std, who, o, std.transfer_title or title, remarks))]
    pages += _matter_pages(brief, o, remarks, dropped)
    pages.append(Page("kontakt", std.contact_page_title, _contact(brief, std, remarks)))
    pages.append(Page("koniec", "Strona końcowa", [lib.finish(std.finish_text, o.finish_style)], finish=True))
    _unique_page_titles(pages)
    _keep_pages_non_empty(pages, remarks)
    return replace(_emit(title, form_key, pages, o, remarks), required_dropped=tuple(dropped))


def pages_without_fixed_content(form: Form) -> list[str]:
    """Titles of the pages that could be empty on some journey: no section without a condition that holds a
    component without a condition (design 6.5.3). The composer never returns such a page; the gate may ask again."""
    return [t.title for t in form.tabs
            if not any(not q.field.states and any(not c.field.states for c in q.field.repeatingSectionGrid) for q in t.questions)]


# -- the standard scaffold --------------------------------------------------------------------------------------

def _standard(brief: Brief, o: ComposeOptions, remarks: list[Remark]) -> tuple[Standard, Who]:
    a = brief.applicants
    own, other, entity = a.self_, a.other_person, a.entity
    if a.status != "stated" or not (own or other or entity):
        own = other = entity = True
        remarks.append(Remark("APPLICANTS_ASSUMED", f"the brief does not say who may apply ({a.status}); the full "
                                                    "standard block of both exports is written"))
    std = o.standard or Standard()
    for extra in brief.applicant_extras:
        if extra.concept == "pesel" and extra.party == "self":
            std = replace(std, pesel=True, identity_source="PESEL")
        elif extra.concept == "pesel" and extra.party == "other_person":
            std = replace(std, other_pesel=True)
        elif extra.concept in ("nip", "regon", "krs"):
            if extra.party != "entity" and not entity:
                # D18: a sole trader takes the entity path; a person's block never carries NIP, REGON or KRS.
                entity = True
                remarks.append(Remark("SOLE_TRADER_AS_ENTITY", f"{extra.concept} asked of {extra.party}: the entity path is "
                                                               "opened and the number is asked there (D18)"))
            std = replace(std, entity_regon=std.entity_regon or extra.concept == "regon", entity_krs=std.entity_krs or extra.concept == "krs")
        else:
            remarks.append(Remark("EXTRA_NOT_PLACED", f"{extra.concept} of {extra.party} has no place in the standard sections"))
    return std, Who(own, other, entity, statutory=o.statutory_representative and other)


def _parties(brief: Brief, std: Standard, who: Who, o: ComposeOptions, transfer_title: str, remarks: list[Remark]) -> list[Sec]:
    a = brief.addressee
    name = a.name if a.status == "stated" or (a.status == "ambiguous" and a.candidates and a.name) else None
    if name is None:
        remarks.append(Remark("ADDRESSEE_MISSING", f"the brief names no addressee ({a.status}); the field is left empty and editable", fix={
            "kind": "input", "rule": "addressee.not_on_paper", "target": ADDRESSEE_NODE,
            "text": "Na druku nie znaleziono nazwy urzędu ani organu. Wpisz adresata wniosku.",
            "input": {"label": "Nazwa urzędu lub organu", "props": ["defaultValue"], "fixed": {"readOnly": True}}}))
    elif a.candidates:
        remarks.append(_addressee_remark(a))
    secs = [lib.addressee(a.kind or "office", name)]
    choice = lib.party(who)
    if choice is not None:
        secs.append(choice)
    secs.append(lib.your_data(std.identity_source, std.pesel))
    if who.self_:
        secs.append(lib.address("self", std.teryt_self))
    if who.entity:
        on = who.party(lib.ENTITY)
        secs += [lib.entity_data(std.entity_regon, std.entity_krs, show=on), lib.address("entity", std.teryt_entity, show=on),
                 lib.representative_proof(show=who.entity_as(lib.REPRESENTATIVE))]
    if who.other:
        on = who.party(lib.OTHER)
        secs += [lib.other_person(std.other_pesel, show=on), lib.address("other", std.teryt_other, show=on)]
        if who.statutory:
            secs.append(lib.statutory_proof(show=who.other_as(lib.STATUTORY)))
    if who.other or who.entity:
        secs.append(lib.power_of_attorney(std.upload_wording, show=who.power_of_attorney()))
    if who.other:
        secs.append(lib.stamp_duty_person(transfer_title, std.upload_wording, o.poa_exemption, show=who.other_as(lib.POA)))
    if who.entity:
        secs.append(lib.stamp_duty_entity(transfer_title, std.upload_wording, show=who.entity_as(lib.POA)))
    return secs


def _addressee_remark(a: Addressee) -> Remark:
    """No addressee block on the paper, and the search of the whole paper found one office (written, the remark only
    tells) or several (the most likely is written, the official picks by a click)."""
    def option(c: Any, current: bool) -> dict[str, Any]:
        return {"label": c.name, "value": c.name, "current": current, "props": {"defaultValue": c.name, "readOnly": True},
                "source": fixes.paper(c.evidence)}

    first = a.candidates[0]
    if len(a.candidates) == 1:
        return Remark("ADDRESSEE_MISSING", "no addressee block on the paper; the one office the paper names was written", fix={
            "kind": "applied", "rule": "addressee.one_office", "target": ADDRESSEE_NODE, "value": first.name,
            "text": f"Adresat odczytany z druku: {first.name}.", "source": fixes.paper(first.evidence)})
    n = len(a.candidates)
    return Remark("ADDRESSEE_MISSING", f"no addressee block on the paper; the paper names {n} offices, the most likely was written", fix={
        "kind": "choice", "rule": "addressee.several_offices", "target": ADDRESSEE_NODE,
        "text": f"Na druku znaleziono kilka nazw urzędów lub organów ({n}). Wskaż adresata wniosku.",
        "options": [option(c, i == 0) for i, c in enumerate(a.candidates)],
        "input": {"label": "Inny urząd lub organ", "props": ["defaultValue"], "fixed": {"readOnly": True}}})


def _clause(brief: Brief, sec: Sec, remarks: list[Remark]) -> None:
    """CLAUSE_LINK_MISSING with its fix. The clause printed on the paper is attached to the consent section (its
    description); a clause read by OCR below CLAUSE_OCR_ATTACH is only offered. No clause on the paper: the consent
    reads as in both exports of the partner, which name the clause without an address: nothing for the official."""
    detail = "no https address of the information clause is known; the consent names the clause without a link"
    ct = brief.declarations.clause_text
    if ct is None:
        remarks.append(Remark("CLAUSE_LINK_MISSING", detail, fix={
            "kind": "applied", "rule": "clause.as_partner_exports", "target": CONSENT_NODE,
            "text": "Na druku nie ma klauzuli informacyjnej: zgoda ma brzmienie z wzorcowych formularzy (bez odnośnika).",
            "source": fixes.rule_source("partner-exports")}))
        return
    html = doc(*[p(t) for t in ct.paragraphs])
    source = fixes.paper(ct.evidence[0]) if ct.evidence else fixes.rule_source("clause-runs")
    if ct.origin != "ocr":
        sec.html = html
        remarks.append(Remark("CLAUSE_LINK_MISSING", "the clause printed on the paper is attached to the consent section as its description", fix={
            "kind": "applied", "rule": "clause.text_from_paper", "target": CONSENT_NODE, "value": ct.paragraphs[0][:160],
            "text": "Treść klauzuli informacyjnej przeniesiono z druku do sekcji zgody.", "source": source}))
        return
    attach = ct.conf >= CLAUSE_OCR_ATTACH
    if attach:
        sec.html = html
    options = [{"label": "Treść klauzuli odczytana ze skanu", "value": "text", "current": attach, "props": {"description": html}, "source": source},
               {"label": "Bez treści klauzuli", "value": "none", "current": not attach, "props": {"description": EMPTY_HTML},
                "source": fixes.rule_source("partner-exports")}]
    remarks.append(Remark("CLAUSE_LINK_MISSING", f"the clause was read by OCR (mean word confidence {ct.conf}); "
                          f"its text is {'attached to' if attach else 'offered for'} the consent section", fix={
        "kind": "choice", "rule": "clause.text_from_scan", "target": CONSENT_NODE,
        "text": "Klauzulę informacyjną odczytano ze skanu. Porównaj jej treść z drukiem.",
        "options": options if attach else options[::-1]}))


def _contact(brief: Brief, std: Standard, remarks: list[Remark]) -> list[Sec]:
    secs = [lib.contact()]
    if brief.declarations.consents:
        items = tuple((doc(p(c.text)), c.required) for c in brief.declarations.consents)
        secs.append(Sec("kontakt/oswiadczenia", "Oświadczenia", "oswiadczenia",
                        [Comp("oswiadczenia", "CONSENT_SECTION", "", "oswiadczenia_tresc", consents=items, origin="paper")], origin="paper"))
    clause = brief.declarations.clause
    url = clause.value if clause.status == "stated" and (clause.value or "").startswith("https://") else None
    consent = lib.consent(std.consent_section, url)
    if url is None:
        _clause(brief, consent, remarks)
    secs.append(consent)
    return secs


# -- the matter: what the paper asks ------------------------------------------------------------------------------

def _brief_comp(f: BriefField, section_title: str, policy: str, remarks: list[Remark], unstated: list[str], dropped: list[str]) -> Comp:
    common = {"key": f.key, "type": f.type, "show": from_brief(f.show_if), "ref": f"brief:{f.key}", "origin": "paper", "brief_key": f.key}
    if f.type in ("TEXT_BLOCK", "INFO_SECTION"):
        return Comp(title="", html=doc(p(f.label), *([p(f.hint)] if f.hint else [])), **common)
    if f.type == "CONSENT_SECTION":
        return Comp(title="", consents=((doc(p(f.label)), f.required),), **common)
    named, withheld = validators.identifier(f.type, f.concept, f.label)
    if withheld:
        # An honest gap (hard rule 9). The code is the nearest of the sidecar's list: we are not sure what value
        # the field takes, so the official looks at it.
        remarks.append(Remark("LOW_CONFIDENCE", f"field {f.key}: no validator of the value is written; {withheld}"))
    must, why = required_rule.written(f, section_title, policy)
    if why is not None:
        dropped.append(f.key)
        if why == required_rule.UNSTATED:
            unstated.append(f.key)     # counted, reported once for the form
        else:
            remarks.append(Remark("REQUIRED_INFERRED", f"field {f.key}: REQUIRED is not written; {why}", fix={
                "kind": "applied", "rule": "required.paper_optional", "target": f"brief:{f.key}", "value": "optional",
                "text": f"Pole „{f.label[:80]}” jest nieobowiązkowe: tak wynika ze słów druku.",
                "source": fixes.paper(f.evidence[0]) if f.evidence else fixes.rule_source("paper-words")}))
    validation = (("REQUIRED",) if must else ()) + ((named,) if named else ())
    options = tuple(f.options)
    if f.type == "CHECKBOX" and not options:
        # a single yes-or-no box (brief 1.1): the partner's grammar wants options, so the box is one option "Tak"
        # under the question; no export shows a CHECKBOX, the shape is flagged INFERRED_SHAPE like every CHECKBOX
        options = (SINGLE_BOX_OPTION,)
    link = dictionaries.link_of(f)
    if link is not None and link.written:
        # A8 DX-2 (point I): the label names a country or a territorial unit, so the field takes the partner's
        # dictionary; a dictionary is bound only to a drop-down list. The sidecar row says why (meta.dictionary_links).
        return Comp(title=f.label, html=doc(p(f.hint)) if f.hint else "", validation=("REQUIRED",) if must else (),
                    dictionary=link.dictionary, multi_level=link.multi_level, search=True, **{**common, "type": "SELECT"})
    return Comp(title=f.label, html=doc(p(f.hint)) if f.hint else "", options=options, validation=validation,
                search=True if f.type == "SELECT" and len(f.options) > 15 else None, **common)


def _required_fix(brief: Brief, unstated: list[str]) -> dict[str, Any]:
    """The fix of the one REQUIRED_INFERRED remark of the policy "paper" (no REQUIRED where the paper marks none).
    The paper marks its required fields itself: the unmarked ones are optional by the paper's own convention, the
    remark only tells. The paper marks nothing: only the official knows, so he gets a choice by one click; the form
    keeps what it has (no REQUIRED) as the first option."""
    fields = {f.key: f for m in brief.matter for f in m.fields if f.key}
    # the paper's own word "obowiązkowe" or "wymagane" on a field: the paper has a convention of marking them
    marked = [f for f in fields.values() if f.required and f.required_basis == "paper"
              and required_rule.REQUIRED_WORD.search(f"{f.label} {f.hint or ''}")]
    n = len(unstated)
    if marked:
        return {"kind": "applied", "rule": "required.paper_marks_its_own", "value": "optional",
                "text": f"Druk sam oznacza pola obowiązkowe ({len(marked)}); pozostałych ({n}) nie oznacza, więc nie są obowiązkowe.",
                "source": fixes.paper(marked[0].evidence[0]) if marked[0].evidence else fixes.rule_source("paper-words")}
    soft = [k for k in unstated if k in fields and USUALLY_OPTIONAL.search(fields[k].label)]
    hard = [k for k in unstated if k not in soft]
    options = [{"label": "Zostaw nieobowiązkowe (druk tego nie oznacza)", "value": "optional", "current": True,
                "fields": {k: {"REQUIRED": False} for k in unstated}, "source": fixes.rule_source("required-only-when-the-paper-says")}]
    if soft and hard:
        names = ", ".join(fields[k].label[:30] for k in soft[:4])
        options.append({"label": f"Obowiązkowe ({len(hard)}), bez: {names}", "value": "required_but_usually_optional", "current": False,
                        "fields": {**{k: {"REQUIRED": True} for k in hard}, **{k: {"REQUIRED": False} for k in soft}},
                        "source": {"type": "dictionary", "name": "usually-optional"}})
    options.append({"label": f"Wszystkie obowiązkowe ({n})", "value": "required", "current": False,
                    "fields": {k: {"REQUIRED": True} for k in unstated}, "source": fixes.rule_source("unmarked-blank-is-required")})
    return {"kind": "choice", "rule": "required.paper_is_silent", "options": options,
            "text": f"Druk nie mówi, które pola są obowiązkowe (dotyczy {n}). Wybierz gotową odpowiedź."}


def _matter_pages(brief: Brief, o: ComposeOptions, remarks: list[Remark], dropped: list[str]) -> list[Page]:
    secs: list[Sec] = []
    unstated: list[str] = []
    for m in brief.matter:
        native = m.repeating and o.repeating_style == "native"
        if m.repeating and not native:
            remarks.append(Remark("REPEATING_FLATTENED", f"{m.role}: written as one plain section (REPEATING_STYLE={o.repeating_style})"))
        comps = [_brief_comp(f, m.title, o.required_policy, remarks, unstated, dropped) for f in m.fields]
        secs.append(Sec(m.role, m.title, None, comps, show=from_brief(m.show_if), repeating=native, origin="paper"))
    if unstated:
        n = len(unstated)
        remarks.append(Remark("REQUIRED_INFERRED", f"{n} field{'s are' if n != 1 else ' is'} required only by our rule and the paper does not "
                                                   f"mark {'them' if n != 1 else 'it'}: REQUIRED is not written (required policy 'paper'); "
                                                   f"first: {', '.join(unstated[:6])}", fix=_required_fix(brief, unstated)))
    uploads = [a for a in brief.attachments if a.covered_by is None]
    if uploads:
        secs.append(Sec("matter/zalaczniki", "Załączniki", None, [
            Comp(a.key or slug(a.label, fallback="zalacznik"), "FILE_UPLOADER", a.label, show=from_brief(a.show_if),
                 validation=("REQUIRED",) if a.required else (), origin="paper", brief_key=a.key) for a in uploads], origin="paper"))
    if brief.fee.status == "stated":
        quotes = [brief.fee.value] if brief.fee.value else [e.quote for e in brief.fee.evidence]
        secs.append(Sec("matter/oplata_za_wniosek", "Opłata", None, [
            Comp("informacja", "TEXT_BLOCK", "", html=doc(*[p(q) for q in quotes]), origin="paper"),
            Comp("potwierdzenie_oplaty", "FILE_UPLOADER", "Potwierdzenie opłaty")], origin="paper"))
    # A8 DX-3: "no field read from the paper" is the honest gap, whatever text or fee the matter still shows; the
    # reviewer reads this text as it is, so it is Polish. Before, NO_MATTER came only when no section was made at all.
    if not any(c.origin == "paper" and c.type not in ("TEXT_BLOCK", "INFO_SECTION") for s in secs for c in s.comps):
        remarks.append(Remark("NO_MATTER", NO_MATTER_TEXT))
    if not secs:
        return []

    limit = max(1, o.max_fields_per_page)
    parts: list[Sec] = []
    for s in secs:
        if s.repeating or len(s.comps) <= limit:   # the rows of a repeating section stay together
            parts.append(s)
            continue
        chunks = [s.comps[i: i + limit] for i in range(0, len(s.comps), limit)]
        remarks.append(Remark("SECTION_SPLIT", f"{s.role}: {len(s.comps)} fields over {len(chunks)} parts of at most {limit}"))
        for n, chunk in enumerate(chunks, 1):
            parts.append(replace(s, comps=chunk) if n == 1 else
                         replace(s, role=f"{s.role}#{n}", title=f"{s.title} (część {n})", comps=chunk))
    pages: list[Page] = []
    count = 0
    for s in parts:
        if not pages or count + len(s.comps) > limit:
            # The page takes the role and the title of the section that opens it: a meaning, not a position (D10).
            pages.append(Page(f"matter/{s.role.removeprefix('matter/')}", s.title))
            count = 0
        pages[-1].secs.append(s)
        count += len(s.comps)
    return pages


def _unique_page_titles(pages: list[Page]) -> None:
    """Conditions select a page by its title (design 6.7): two pages never share one."""
    seen: set[str] = set()
    for page in reversed(pages):   # the standard pages keep their titles; a matter page gives way
        if page.role.startswith("matter/"):
            continue
        seen.add(page.title)
    for page in pages:
        if not page.role.startswith("matter/"):
            continue
        # A8 VB-2: a condition names the page in single quotes, the only notation of the exports and of both
        # reference readers (gate G5, coi_lint); a JSONata string in single quotes cannot hold ' or \.
        page.title = page.title.replace("'", "’").replace("\\", "/")
        base, n = page.title, 2
        while page.title in seen:
            page.title = f"{base} ({n})"
            n += 1
        seen.add(page.title)


def _keep_pages_non_empty(pages: list[Page], remarks: list[Remark]) -> None:
    """No page may become empty on any journey (design 6.5.3): a page whose every component depends on an answer
    gets a short unconditional note naming the step."""
    for page in pages:
        if any(s.show is None and (s.repeating or any(c.show is None for c in s.comps)) for s in page.secs):
            continue
        note = doc(p(f"Ten krok dotyczy części „{page.title}”. Pola do wypełnienia pojawią się tutaj, jeśli wynikają z Twoich "
                     "wcześniejszych odpowiedzi. Jeśli nic się nie pojawia, przejdź dalej."))
        # Named after the step, so that the paper's own section keeps the plain slug of its title.
        page.secs.insert(0, Sec(f"{page.role}/krok", page.title, None, name_from=f"krok {page.title}",
                                comps=[Comp("informacja", "TEXT_BLOCK", "", html=note, name_from=f"informacja o kroku {page.title}")]))
        remarks.append(Remark("STEP_NOTE_ADDED", f"page {page.title!r}: every component is conditional, an unconditional note is added"))


# -- writing the partner's tree -------------------------------------------------------------------------------------

def _base(role: str) -> str:
    return role.split("#")[0]


def _tail(role: str) -> str:
    return slug(_base(role).rsplit("/", 1)[-1], fallback="sekcja")


def _question(c: Comp, id_: str, states: list[State] | None, validation: list[str]) -> Question:
    common = {"description": c.html, "validation": validation, "states": states}
    options = _options(c.options)
    match c.type:
        case "TEXT_FIELD":
            return text_field(id_, c.tech, c.title, read_only=c.read_only, default_value=c.default, default_value_type=c.default_type, **common)
        case "TEXTAREA":
            return textarea(id_, c.tech, c.title, **common)
        case "NUMBER":
            return number(id_, c.tech, c.title, **common)
        case "DATEPICKER":
            return datepicker(id_, c.tech, c.title, **common)
        case "FILE_UPLOADER":
            return file_uploader(id_, c.tech, c.title, **common)
        case "RADIO":
            return radio(id_, c.tech, c.title, options, **common)
        case "CHECKBOX":
            return checkbox(id_, c.tech, c.title, options, **common)
        case "SELECT":
            return select(id_, c.tech, c.title, options=options, dictionary_name=c.dictionary, multi_level_tree=c.multi_level,
                          search_enabled=c.search, default_value=c.default, default_value_type=c.default_type, **common)
        case "TEXT_BLOCK":
            return text_block(id_, c.tech, c.title, c.html, states=states)
        case "INFO_SECTION":
            return info_section(id_, c.tech, c.title, c.html, states=states)
        case "CONSENT_SECTION":
            return consent_section(id_, c.tech, c.title, [ConsentItem(description=h, required=r) for h, r in c.consents], states=states)
    raise ComposeError(f"component type {c.type!r} has no constructor")


def _options(texts: tuple[str, ...]) -> list[Option]:
    """As in the exports: id and name are the visible text, techName its slug; unique inside the field."""
    names = Names()
    return [Option.of(text, names.unique(slug(text, fallback="opcja"))) for text in texts]


def _emit(title: str, form_key: str, pages: list[Page], o: ComposeOptions, remarks: list[Remark]) -> ComposeResult:
    names = Names()
    for page in pages:                                   # the library's fixed names first: they never give way
        for s in page.secs:
            for fixed in [s.tech, *(c.tech for c in s.comps)]:
                if fixed is not None:
                    names.reserve(fixed)
    places: dict[str, Place] = {}
    in_repeating: set[str] = set()
    for page in pages:                                   # then the slugs of the paper's labels, in document order
        for s in page.secs:
            if s.tech is None:
                s.tech = names.unique(slug(s.name_from or s.title, fallback="sekcja"), _tail(s.role))
            for c in s.comps:
                if c.tech is None:
                    c.tech = names.unique(slug(c.name_from or c.title or c.key), _tail(s.role))
                if c.ref is not None:
                    places[c.ref] = Place(page.title, s.tech, c.tech)
                    if s.repeating:
                        in_repeating.add(c.ref)

    def states(pred: Pred | None, inside_repeating: bool, what: str) -> list[State] | None:
        if pred is None:
            return None
        if inside_repeating or any(r in in_repeating for r in refs(pred)):
            # The second notation of the rules (__userAnswer[$repeatingSectionIndex]) belongs to the conditions step.
            remarks.append(Remark("CONDITION_NOT_WRITTEN", f"{what}: a condition inside a repeating section, or on a field of one, is not written here"))
            return None
        return [State(type="SHOW", query=write(pred, places))]

    ids = Ids(o.id_namespace, form_key)
    origins: dict[str, str] = {}
    brief_keys: dict[str, str] = {}
    paths: dict[str, str] = {}

    def new_id(*path: str) -> str:
        id_, key = ids.of(*path)
        paths[id_] = key
        return id_

    def note_label(text: str, id_: str) -> None:
        if re.search(r"[<>]", text):
            remarks.append(Remark("MARKUP_IN_LABEL", "the label holds angle brackets; it is written as text, never as markup", id_))

    tabs = []
    for page in pages:
        sections = []
        for s in page.secs:
            sid = new_id(s.role)
            origins[sid] = s.origin
            note_label(s.title, sid)
            if s.repeating:
                remarks.append(Remark("INFERRED_SHAPE", "REPEATING_SECTION: no export shows one", sid))
            comps = []
            for c in s.comps:
                cid = new_id(_base(s.role), c.key)
                origins[cid] = c.origin
                if c.brief_key is not None:
                    brief_keys[cid] = c.brief_key
                note_label(c.title, cid)
                if c.type in INFERRED_SHAPES:
                    remarks.append(Remark("INFERRED_SHAPE", f"{c.type}: no export shows one", cid))
                validation = list(c.validation) if o.validators and c.type not in _NO_VALIDATION else []
                comps.append(_question(c, cid, states(c.show, s.repeating, c.tech or c.key), validation))
            sections.append(section(sid, s.tech, s.title, comps, description=s.html, states=states(s.show, False, s.tech or s.role),
                                    repeating=s.repeating))
        tabs.append(tab(new_id("page", page.role), page.title, sections, finish=page.finish))
    links = [new_id("flow", f"{a.role}→{b.role}") for a, b in zip(pages, pages[1:], strict=False)]
    return ComposeResult(Form.build(title, tabs, links), origins, brief_keys, paths, tuple(remarks))
