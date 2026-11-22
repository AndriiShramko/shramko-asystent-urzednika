"""Sidecar `meta`: everything that is not the partner's form, keyed by the ids of the form (design 5.4, 7.4, D2).

The ledger must close: blanks_found equals the sum of the five fates, every blank has exactly one row, and the
counts equal the rows by fate. It is a ledger and never "accuracy": a blank the finder missed is outside it.
`resources` is the one part that differs between runs; `to_json_bytes(deterministic=True)` leaves it out.

Revision 1.1 (additive): `evidence` maps a form id to one record (1.0) or to a list of records; `evidence_of(id)`
reads both as a list. A record may locate a drawn blank without a quote. `proposals.fee` keeps a proposed fee apart
from `receipts.fee`. `coverage.gaps` lists the character spans of partly covered runs. The ledger is assembled
from the brief's dispositions by app.model.ledger.assemble_ledger.
"""
from __future__ import annotations

from typing import Any, Literal, Self

from pydantic import Field, field_serializer, model_validator

from .common import (  # noqa: F401 - Fate and MergeWhy are re-exported (their 1.0 home)
    Anchor,
    Box,
    Contract,
    Dropped,
    Evidence,
    Fate,
    MergeWhy,
    PageNo,
    ProposedFee,
    ReasonCode,
    Sha256,
    Span,
    Stated,
    Unit,
    Warning,
    canonical_json,
    omit_empty,
    unique,
)

Origin = Literal["paper", "standard", "reviewer"]
Check = Literal["pass", "fail", "skipped"]
# Validators the partner has not named (design 6.6, 6.8): proposals only, never in the form (D8, D9).
ProposedValidator = Literal["NRB", "KRS", "KW", "PHONE_PL", "DATE_RANGE", "PARCEL_ID"]


class Converter(Contract):
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    image: Literal["core", "plus"]
    profile: str = Field(description='Switches that shaped the output, e.g. "FINISH_STYLE=export;VALIDATORS=on".')


class Hashes(Contract):
    input_sha256: Sha256
    form_sha256: Sha256
    brief_sha256: Sha256


class FieldEvidence(Contract):
    page: PageNo | None = None
    box: Box | None = None
    anchor: Anchor | None = None
    quote: str | None = Field(default=None, min_length=1, description="1.1: may be left out when box or anchor locate a drawn blank.")
    candidate: str | None = None
    runs: list[str] = omit_empty(description="1.1: run ids of the quote or of the blank.")

    @model_validator(mode="after")
    def _quote_or_place(self) -> Self:
        if self.quote is None and self.box is None and self.anchor is None:
            raise ValueError("field evidence without a quote locates the blank with a box or an anchor")
        return self


class ConfidenceParts(Contract):
    geometry: Unit | None = None
    label: Unit | None = None
    text: Unit | None = None
    rule: Unit | None = None


class FieldConfidence(Contract):
    value: Unit
    parts: ConfidenceParts


class LedgerRow(Contract):
    candidate: str = Field(min_length=1)
    fate: Fate
    field: str | None = Field(default=None, description="FIELD: id of the form component.")
    into: str | None = Field(default=None, description="MERGED: candidate it was merged into.")
    why: MergeWhy | None = None
    section: str | None = Field(default=None, description="STANDARD: techName of the standard section.")
    reason: ReasonCode | None = Field(default=None, description="LEFT_OUT: reason code.")
    decision: str | None = Field(default=None, description="AWAITING_DECISION: id of the decision.")

    @model_validator(mode="after")
    def _fate_has_its_key(self) -> Self:
        need = {"FIELD": "field", "MERGED": "into", "STANDARD": "section", "LEFT_OUT": "reason", "AWAITING_DECISION": "decision"}[self.fate]
        if getattr(self, need) is None:
            raise ValueError(f"ledger row {self.candidate}: fate {self.fate} needs {need}")
        if self.fate == "MERGED" and self.why is None:
            raise ValueError(f"ledger row {self.candidate}: MERGED needs why")
        return self


class Ledger(Contract):
    blanks_found: int = Field(ge=0)
    became_field: int = Field(ge=0)
    merged: int = Field(ge=0)
    covered_by_standard: int = Field(ge=0)
    left_out: int = Field(ge=0)
    awaiting_decision: int = Field(ge=0)
    rows: list[LedgerRow] = []

    @model_validator(mode="after")
    def _closes(self) -> Self:
        counts = (self.became_field, self.merged, self.covered_by_standard, self.left_out, self.awaiting_decision)
        if self.blanks_found != sum(counts):
            raise ValueError(f"the ledger does not close: blanks_found {self.blanks_found} != sum of the five fates {sum(counts)}")
        if len(self.rows) != self.blanks_found:
            raise ValueError(f"the ledger does not close: {self.blanks_found} blanks but {len(self.rows)} rows")
        unique([r.candidate for r in self.rows], "candidates in the ledger")
        by_fate = tuple(sum(r.fate == f for r in self.rows) for f in ("FIELD", "MERGED", "STANDARD", "LEFT_OUT", "AWAITING_DECISION"))
        if by_fate != counts:
            raise ValueError(f"the ledger does not close: counts {counts} but rows by fate {by_fate}")
        return self


class Receipts(Contract):
    fee: Stated
    who_may_apply: Stated
    mandatory_attachments: Stated


class Coverage(Contract):
    runs_total: int = Field(ge=0)
    assigned: int = Field(ge=0)
    unassigned: list[str] = []
    silent_pages: list[PageNo] = Field(default=[], description="Pages with ink and no candidate (design 7.4).")
    gaps: list[Span] = omit_empty(description="1.1: characters of partly covered runs that no span covers (such runs are unassigned).")

    @model_validator(mode="after")
    def _adds_up(self) -> Self:
        if self.assigned + len(self.unassigned) != self.runs_total:
            raise ValueError("coverage: assigned plus unassigned must equal runs_total")
        return self


class Decision(Contract):
    id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    resolves: list[str] = Field(min_length=1, description="Ids of the warnings this one answer settles.")
    options: list[str] = []
    default: str | None = None


class Unsupported(Contract):
    what: str = Field(min_length=1)
    code: str = Field(min_length=1, description='Kind of behaviour, e.g. "COMPUTED_VALUE".')
    page: PageNo | None = None
    evidence: list[Evidence] = []


class ProposedDictionary(Contract):
    name: str = Field(min_length=1)
    entries: list[str] = []
    variants: list[str] = []
    pages: list[PageNo] = []
    field: str | None = None
    # A8 DX-1 (additive, left out while empty): every form id that would take the dictionary, why it is proposed and
    # how a field uses it (the partner asks for "nazwę, strukturę i zastosowanie"), and the quotes of the paper.
    fields: list[str] = omit_empty()
    why: str | None = Field(default=None, min_length=1)
    use: str | None = Field(default=None, min_length=1)
    evidence: list[Evidence] = omit_empty()


class ProposedSource(Contract):
    field: str
    source: str = Field(pattern=r"^[A-Z][A-Z_]*\.[A-Za-z_]+$", description='Partner notation, e.g. "KRS.name".')
    why: str


class ProposedValidatorRow(Contract):
    field: str
    name: ProposedValidator
    why: str


class ProposedOther(Contract):
    what: str = Field(min_length=1)
    why: str = Field(min_length=1)


class Proposals(Contract):
    dictionaries: list[ProposedDictionary] = []
    initial_data: list[ProposedSource] = []
    validators: list[ProposedValidatorRow] = []
    other: list[ProposedOther] = Field(default=[], description="E.g. an e-Delivery field, a third capacity (design 6.6).")
    fee: ProposedFee | None = Field(default=None, description="1.1: a proposed fee; receipts.fee stays what the paper states.")


class LegalBasis(Stated):
    eli: str | None = None


class ConditionChecks(Contract):
    total: int = Field(ge=0)
    evaluated: int = Field(ge=0)
    failed: int = Field(ge=0)


class JourneyChecks(Contract):
    run: int = Field(ge=0)
    passed: int = Field(ge=0)
    not_applicable: int = Field(ge=0)


class Checks(Contract):
    schema_: Check = Field(alias="schema")
    partner_rules: Check
    grid: Check
    conditions: ConditionChecks
    journeys: JourneyChecks
    zero_answer: Check
    html: Check

    model_config = Contract.model_config | {"populate_by_name": True, "serialize_by_alias": True}


class Resources(Contract):
    wall_ms: int = Field(ge=0)
    cpu_ms: int = Field(ge=0)
    peak_rss_mb: int = Field(ge=0)
    pages: int = Field(ge=0)
    ocr_pages: int = Field(ge=0)


class Meta(Contract):
    meta_version: Literal[1, 1.1] = Field(default=1.1, description="Revision of this contract; 1 (1.0) still validates.")
    converter: Converter
    hashes: Hashes
    origins: dict[str, Origin] = {}
    evidence: dict[str, FieldEvidence | list[FieldEvidence]] = Field(
        default={}, description="Form id -> one evidence record (1.0) or a non-empty list of them (1.1).")
    confidence: dict[str, FieldConfidence] = {}
    ledger: Ledger
    omissions: list[Dropped] = []
    receipts: Receipts
    coverage: Coverage
    decisions: list[Decision] = []
    warnings: list[Warning] = []
    unsupported: list[Unsupported] = []
    proposals: Proposals = Proposals()
    concepts: dict[str, str] = {}
    legal_basis: LegalBasis
    checks: Checks | None = None
    resources: Resources | None = None

    @field_serializer("origins", "evidence", "confidence", "concepts")
    def _sorted_by_id(self, v: dict[str, Any]) -> dict[str, Any]:
        return dict(sorted(v.items()))

    @model_validator(mode="after")
    def _references_resolve(self) -> Self:
        empty = sorted(k for k, v in self.evidence.items() if isinstance(v, list) and not v)
        if empty:
            raise ValueError(f"evidence lists are not empty, leave the id out: {empty}")
        unique([d.id for d in self.decisions], "decision ids")
        wid = [w.id for w in self.warnings if w.id is not None]
        unique(wid, "warning ids")
        for d in self.decisions:
            missing = sorted(set(d.resolves) - set(wid))
            if missing:
                raise ValueError(f"decision {d.id} resolves warnings that do not exist: {missing}")
        dec = {d.id for d in self.decisions}
        for r in self.ledger.rows:
            if r.decision is not None and r.decision not in dec:
                raise ValueError(f"ledger row {r.candidate}: decision {r.decision} does not exist")
        return self

    def evidence_of(self, form_id: str) -> list[FieldEvidence]:
        """The evidence records of one form id as a list, whichever of the two shapes was written."""
        v = self.evidence.get(form_id)
        return [] if v is None else list(v) if isinstance(v, list) else [v]

    def to_json_bytes(self, deterministic: bool = True) -> bytes:
        d = self.to_dict()
        if deterministic:
            d.pop("resources", None)
        return canonical_json(d)
