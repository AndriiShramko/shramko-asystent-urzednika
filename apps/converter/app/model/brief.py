"""Brief: what the paper asks, in the terms of the partner's form, each answer with its evidence (design 5.3, 6.4).

Every value the paper may or may not state is a `Stated`: status stated (with a quote), not_found, or ambiguous
(with the competing quotes). Field keys are unique in the brief; every condition names an existing key and,
for `is`, one of its options.

Revision 1.1 (additive, every new key optional and left out while unused):
- `dispositions`: one per finder candidate id: FIELD (brief key), MERGED (candidate and why), STANDARD (role),
  LEFT_OUT (reason code), AWAITING_DECISION (decision id). app.model.ledger.assemble_ledger turns them into the
  meta ledger and checks them against the finder's ids.
- `applicants.options`: who may apply as items (stable key, party, capacity, evidence). When they are given, the
  applicant selector (key APPLICANT_SELECTOR) and its option keys are legal targets of a condition.
- a CHECKBOX without options is one yes-or-no box (a condition on it says "true" or "false"); RADIO still lists
  its options. No option is made up from the question's label.
- `mandatory_attachments` (a Stated receipt), `proposed_fee` (never changes `fee`), `Consent.kind`
  (consent | declaration, default consent), `MatterSection.page_title` and `hint`, `Attachment.key`.
- `check_paper_evidence` returns warnings for a field required by the paper with no evidence.
"""
from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from .common import Contract, Dropped, Evidence, Fate, InputRef, MergeWhy, ProposedFee, ReasonCode, Stated, Unit, Warning, omit_empty, unique

# Inner component types of the partner's format (contracts/coi/form.schema.json, innerQuestion).
ComponentType = Literal[
    "TEXT_FIELD", "CHECKBOX", "NUMBER", "CONSENT_SECTION", "SELECT", "TEXTAREA",
    "FILE_UPLOADER", "RADIO", "DATEPICKER", "TEXT_BLOCK", "INFO_SECTION",
]
# What a value is (design 6.8, 5.3). Drives validators and proposals. Add a concept here with its 6.8 row.
Concept = Literal[
    "pesel", "nip", "regon", "zip_code", "email", "epuap", "ade", "id_card",
    "nrb", "krs", "kw", "parcel_id", "phone", "date", "amount_pln", "count", "area",
]
# Design 6.4.2: the capacity in which the person at the keyboard acts for the party.
Capacity = Literal["pelnomocnik", "reprezentant", "przedstawiciel_ustawowy"]
Party = Literal["self", "other_person", "entity"]
# Why a field is required (design 6.4.3): marked on the paper, the substance of the request, or our inference
# (which the sidecar shows as REQUIRED_INFERRED).
RequiredBasis = Literal["paper", "substance", "inferred"]
# 1.1: an item of the declarations is a consent (a box to tick) or a declaration the applicant affirms.
ConsentKind = Literal["consent", "declaration"]

Key = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$", max_length=60)]
Role = Annotated[str, Field(pattern=r"^[a-z0-9_]+(/[a-z0-9_]+)*$")]

# 1.1: the key a condition uses for the applicant selector of the standard sections. Legal as a condition target
# only when the brief lists applicant options; then no matter field may take this key.
APPLICANT_SELECTOR = "applicant"


class Cond(Contract):
    """Predicate tree (design 6.7): exactly one of {field, is} | any_of | all_of | not."""

    field: Key | None = None
    is_: str | None = Field(default=None, alias="is")
    any_of: list[Cond] | None = None
    all_of: list[Cond] | None = None
    not_: Cond | None = Field(default=None, alias="not")

    model_config = Contract.model_config | {"populate_by_name": True, "serialize_by_alias": True}

    @model_validator(mode="after")
    def _one_form(self) -> Self:
        forms = [self.field is not None or self.is_ is not None, self.any_of is not None, self.all_of is not None, self.not_ is not None]
        if sum(forms) != 1 or ((self.field is None) != (self.is_ is None)):
            raise ValueError("a condition is exactly one of {field, is}, any_of, all_of, not")
        if (self.any_of is not None and len(self.any_of) < 2) or (self.all_of is not None and len(self.all_of) < 2):
            raise ValueError("any_of and all_of join at least two conditions")
        return self

    def leaves(self) -> list[Cond]:
        if self.field is not None:
            return [self]
        subs = self.any_of or self.all_of or ([self.not_] if self.not_ else [])
        return [leaf for s in subs for leaf in s.leaves()]


class Addressee(Stated):
    kind: Literal["office", "body"] | None = None
    name: str | None = None


class ApplicantOption(Contract):
    """1.1: one way of applying: who the party is and, when someone acts for it, in which capacity."""

    key: Key
    party: Party
    capacity: Capacity | None = Field(default=None, description="Absent: the party applies in person.")
    evidence: list[Evidence] = []


class Applicants(Stated):
    self_: bool = Field(default=False, alias="self")
    other_person: bool = False
    entity: bool = False
    capacities: list[Capacity] = []
    options: list[ApplicantOption] = omit_empty(description="1.1: the ways of applying as items, beside the flags.")

    model_config = Stated.model_config | {"populate_by_name": True, "serialize_by_alias": True}


class ApplicantExtra(Contract):
    concept: Concept
    party: Party
    required: bool = False


class BriefField(Contract):
    key: Key
    label: str = Field(min_length=1)
    type: ComponentType
    concept: Concept | None = None
    required: bool = False
    required_basis: RequiredBasis | None = None
    hint: str | None = None
    options: list[str] = []
    length: int | None = Field(default=None, ge=1)
    show_if: Cond | None = None
    candidate: str | None = None
    conf: Unit | None = None
    evidence: list[Evidence] = []

    @model_validator(mode="after")
    def _required_has_basis(self) -> Self:
        if self.required and self.required_basis is None:
            raise ValueError(f"field {self.key}: required needs its basis (paper, substance or inferred)")
        if not self.required and self.required_basis is not None:
            raise ValueError(f"field {self.key}: required_basis given for a field that is not required")
        if self.type == "RADIO" and not self.options:
            raise ValueError(f"field {self.key}: a {self.type} lists its options")
        return self


class MatterSection(Contract):
    title: str = Field(min_length=1)
    role: Role
    repeating: bool = False
    show_if: Cond | None = None
    fields: list[BriefField] = Field(min_length=1)
    page_title: str | None = Field(default=None, min_length=1, description="1.1: title of the page this section opens, when it differs from the section title.")
    hint: str | None = Field(default=None, min_length=1, description="1.1: description of the section.")


class Attachment(Contract):
    label: str = Field(min_length=1)
    covered_by: Role | None = Field(default=None, description='Standard section that already asks for it, e.g. "standard/pelnomocnictwo".')
    required: bool = False
    show_if: Cond | None = None
    evidence: list[Evidence] = []
    key: Key | None = Field(default=None, description="1.1: stable key; the composer makes the id from it when present, from the label otherwise.")


class Consent(Contract):
    text: str = Field(min_length=1)
    required: bool = True
    evidence: list[Evidence] = []
    kind: ConsentKind = Field(default="consent", exclude_if=lambda v: v == "consent",
                              description="1.1: consent (default) or a declaration the applicant affirms.")


class Declarations(Contract):
    consents: list[Consent] = []
    clause: Stated


class Disposition(Contract):
    """1.1: what became of one finder candidate, decided by the understanding step (design 5.4 fates)."""

    candidate: str = Field(min_length=1)
    fate: Fate
    key: Key | None = Field(default=None, description="FIELD: key of the brief field or attachment it became.")
    into: str | None = Field(default=None, min_length=1, description="MERGED: candidate it was merged into.")
    why: MergeWhy | None = Field(default=None, description="MERGED: why.")
    role: Role | None = Field(default=None, description='STANDARD: role of the standard section, e.g. "standard/twoje_dane".')
    reason: ReasonCode | None = Field(default=None, description="LEFT_OUT: reason code.")
    decision: str | None = Field(default=None, min_length=1, description="AWAITING_DECISION: id of the decision.")

    @model_validator(mode="after")
    def _fate_has_its_key(self) -> Self:
        own = {"FIELD": ("key",), "MERGED": ("into", "why"), "STANDARD": ("role",), "LEFT_OUT": ("reason",),
               "AWAITING_DECISION": ("decision",)}
        for k in own[self.fate]:
            if getattr(self, k) is None:
                raise ValueError(f"disposition of {self.candidate}: fate {self.fate} needs {k}")
        stray = sorted(k for keys in own.values() for k in keys if k not in own[self.fate] and getattr(self, k) is not None)
        if stray:
            raise ValueError(f"disposition of {self.candidate}: fate {self.fate} does not take {stray}")
        if self.into == self.candidate:
            raise ValueError(f"disposition of {self.candidate}: merged into itself")
        return self


class Brief(Contract):
    brief_version: Literal[1, 1.1] = Field(default=1.1, description="Revision of this contract; 1 (1.0) still validates.")
    input: InputRef
    title: Stated
    addressee: Addressee
    applicants: Applicants
    applicant_extras: list[ApplicantExtra] = []
    matter: list[MatterSection] = []
    attachments: list[Attachment] = []
    declarations: Declarations
    fee: Stated
    legal_basis: Stated
    dropped: list[Dropped] = []
    warnings: list[Warning] = []
    mandatory_attachments: Stated | None = Field(default=None, description="1.1: receipt: does the paper say which attachments are mandatory.")
    proposed_fee: ProposedFee | None = Field(default=None, description="1.1: a fee we propose; `fee` stays what the paper states.")
    dispositions: list[Disposition] = omit_empty(description="1.1: one per finder candidate id.")

    @model_validator(mode="after")
    def _references_resolve(self) -> Self:
        fields = {f.key: f for s in self.matter for f in s.fields}
        unique([f.key for s in self.matter for f in s.fields], "field keys in the brief")
        unique([s.role for s in self.matter], "roles of matter sections")
        att_keys = [a.key for a in self.attachments if a.key is not None]
        unique(att_keys, "attachment keys in the brief")
        opt_keys = [o.key for o in self.applicants.options]
        unique(opt_keys, "applicant option keys")
        if opt_keys and APPLICANT_SELECTOR in fields:
            raise ValueError(f"field key {APPLICANT_SELECTOR!r} is the applicant selector when applicant options are given")
        conds = [c for s in self.matter for c in (s.show_if, *(f.show_if for f in s.fields)) if c is not None]
        conds += [a.show_if for a in self.attachments if a.show_if is not None]
        for cond in conds:
            for leaf in cond.leaves():
                if opt_keys and leaf.field == APPLICANT_SELECTOR:
                    if leaf.is_ not in opt_keys:
                        raise ValueError(f"condition on the applicant selector names option {leaf.is_!r}, which is not an applicant option")
                    continue
                target = fields.get(leaf.field or "")
                if target is None:
                    raise ValueError(f"condition names field {leaf.field!r}, which is not in the brief")
                if target.type == "CHECKBOX" and not target.options and leaf.is_ not in ("true", "false"):
                    raise ValueError(f"condition on the yes-or-no checkbox {leaf.field!r} names {leaf.is_!r}, not 'true' or 'false'")
                if target.options and leaf.is_ not in target.options:
                    raise ValueError(f"condition on {leaf.field!r} names option {leaf.is_!r}, which the field does not have")
        cands = [d.candidate for d in self.dispositions]
        unique(cands, "candidates in the dispositions")
        keys = set(fields) | set(att_keys)
        for d in self.dispositions:
            if d.key is not None and d.key not in keys:
                raise ValueError(f"disposition of {d.candidate}: key {d.key!r} is not a field or attachment of the brief")
            if d.into is not None and d.into not in cands:
                raise ValueError(f"disposition of {d.candidate}: merged into {d.into}, which has no disposition")
        return self


def check_paper_evidence(brief: Brief) -> list[Warning]:
    """1.1: a field whose requirement comes from the paper needs evidence. Returns one warning
    REQUIRED_WITHOUT_EVIDENCE per field without any (a check, not a validation error: 1.0 briefs still load)."""
    return [Warning(code="REQUIRED_WITHOUT_EVIDENCE", field=f.key,
                    detail=f"{f.key}: required_basis paper but no evidence of the paper")
            for s in brief.matter for f in s.fields if f.required_basis == "paper" and not f.evidence]


Cond.model_rebuild()
