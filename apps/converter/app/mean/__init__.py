"""Understanding: from the finder's candidates to the brief (design 5.3, 6.4). One entry:

    from app.mean import understand
    brief = understand(page_model, finder_output)      # -> app.model.brief.Brief

Rules only (decision D12); the wording they look for is data in `app/lexicon/`. The order: title and addressee;
the fate of every candidate (applicant block -> standard sections, signature and office parts left out with a
reason, the rest fields of the matter); who may apply from the wording of the applicant block; required or not;
labels by the standard's rules; composite papers. What a rule cannot decide is said, never guessed: `not_found`,
`ambiguous`, a disposition AWAITING_DECISION, or a warning (REQUIRED_INFERRED, LABEL_RAW, LABEL_NOT_FOUND,
AMBIGUOUS_GROUP, ADDRESSEE_CONFLICT). Every finder candidate gets exactly one disposition.

Options: `strict` (tests: let a rule's exception through). Without it a failing rule gives the smallest honest
brief, every candidate waiting for a decision, and the warning UNREADABLE_PART.
"""
from __future__ import annotations

from typing import Any, Mapping

from app.model.brief import Applicants, Addressee, Brief, Declarations, Disposition, check_paper_evidence
from app.model.candidate import FinderOutput
from app.model.common import Evidence, InputRef, Stated, Warning
from app.model.page import PageModel

from ._doc import Doc, some
from ._fields import read_fields
from ._head import clause_text, find_addressee, find_applicants, find_clause, find_fee, find_legal_basis, find_title, find_variants, prune_by_exclusion

__all__ = ["understand"]

_NOT_FOUND = Stated(status="not_found")


def understand(page_model: PageModel, finder_output: FinderOutput, options: Mapping[str, Any] | None = None) -> Brief:
    """The brief of one document. Never raises unless `strict` is set."""
    if (options or {}).get("strict"):
        return _run(page_model, finder_output)
    try:
        return _run(page_model, finder_output)
    except Exception as e:  # noqa: BLE001 - a rule that fails on an unseen paper is an honest gap, not a 500
        return Brief(
            input=InputRef(sha256=page_model.source.sha256, format=page_model.source.format),
            title=_NOT_FOUND, addressee=Addressee(status="not_found"), applicants=Applicants(status="not_found"),
            declarations=Declarations(clause=_NOT_FOUND), fee=_NOT_FOUND, legal_basis=_NOT_FOUND, mandatory_attachments=_NOT_FOUND,
            warnings=[Warning(code="UNREADABLE_PART",
                              detail=f"the understanding step could not follow this document ({type(e).__name__}); no field was read")],
            dispositions=[Disposition(candidate=c.id, fate="AWAITING_DECISION", decision="understanding_failed")
                          for c in finder_output.candidates],
        )


def _clause_text(doc: Doc):
    try:   # the text of the clause is a courtesy of the consent: a slip here never costs the brief
        return clause_text(doc)
    except Exception:  # noqa: BLE001
        return None


def _run(pm: PageModel, fo: FinderOutput) -> Brief:
    doc = Doc(pm, fo)
    title, title_runs = find_title(doc)
    read = read_fields(doc, title_runs, find_variants(doc, title_runs))
    addressee, conflicts = find_addressee(doc)
    clause, clause_dropped = find_clause(doc)
    # Who may apply is read from the applicant block: its labels, its headings, and the loose lines of the head of
    # the paper ("adres zamieszkania/siedziba firmy" printed under a line).
    signals = list(read.signals)
    if title_runs:
        page, end = doc.page(title_runs[0]), doc.pos[title_runs[0]]
        signals += [(doc.text(r), Evidence(quote=doc.text(r), page=page, runs=[r])) for r in doc.order[:end]
                    if doc.page(r) == page and doc.role(r) == "body" and doc.text(r)]
    applicants, excluded = prune_by_exclusion(doc, find_applicants(signals))
    brief = Brief(
        input=InputRef(sha256=pm.source.sha256, format=pm.source.format),
        title=title, addressee=addressee, applicants=applicants, applicant_extras=read.extras,
        matter=read.matter, attachments=read.attachments,
        declarations=Declarations(consents=read.consents, clause=clause, **some(clause_text=_clause_text(doc))),
        fee=find_fee(doc), legal_basis=find_legal_basis(doc), mandatory_attachments=_NOT_FOUND,
        dropped=read.dropped + clause_dropped + excluded, warnings=conflicts + read.warnings, dispositions=read.dispositions,
    )
    brief.warnings += check_paper_evidence(brief)
    return brief
