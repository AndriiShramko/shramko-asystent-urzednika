"""Brief: what the paper asks, in the terms of the partner's form, each answer with its evidence (design 5.3, 6.4).

Every value the paper may or may not state is a `Stated`: status stated (with a quote), not_found, or ambiguous
(with the competing quotes). Field keys are unique in the brief; every condition names an existing key and,
for `is`, one of its options.
"""
from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from .common import Contract, Dropped, Evidence, InputRef, Stated, Unit, Warning, unique

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

Key = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$", max_length=60)]
Role = Annotated[str, Field(pattern=r"^[a-z0-9_]+(/[a-z0-9_]+)*$")]


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


class Applicants(Stated):
    self_: bool = Field(default=False, alias="self")
    other_person: bool = False
    entity: bool = False
    capacities: list[Capacity] = []

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
        if self.type in ("RADIO", "CHECKBOX") and not self.options:
            raise ValueError(f"field {self.key}: a {self.type} lists its options")
        return self


class MatterSection(Contract):
    title: str = Field(min_length=1)
    role: Role
    repeating: bool = False
    show_if: Cond | None = None
    fields: list[BriefField] = Field(min_length=1)


class Attachment(Contract):
    label: str = Field(min_length=1)
    covered_by: Role | None = Field(default=None, description='Standard section that already asks for it, e.g. "standard/pelnomocnictwo".')
    required: bool = False
    show_if: Cond | None = None
    evidence: list[Evidence] = []


class Consent(Contract):
    text: str = Field(min_length=1)
    required: bool = True
    evidence: list[Evidence] = []


class Declarations(Contract):
    consents: list[Consent] = []
    clause: Stated


class Brief(Contract):
    brief_version: Literal[1] = 1
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

    @model_validator(mode="after")
    def _references_resolve(self) -> Self:
        fields = {f.key: f for s in self.matter for f in s.fields}
        unique([f.key for s in self.matter for f in s.fields], "field keys in the brief")
        unique([s.role for s in self.matter], "roles of matter sections")
        conds = [c for s in self.matter for c in (s.show_if, *(f.show_if for f in s.fields)) if c is not None]
        conds += [a.show_if for a in self.attachments if a.show_if is not None]
        for cond in conds:
            for leaf in cond.leaves():
                target = fields.get(leaf.field or "")
                if target is None:
                    raise ValueError(f"condition names field {leaf.field!r}, which is not in the brief")
                if target.options and leaf.is_ not in target.options:
                    raise ValueError(f"condition on {leaf.field!r} names option {leaf.is_!r}, which the field does not have")
        return self


Cond.model_rebuild()
