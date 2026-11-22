"""The sidecar a run returns today (`app.pipeline.run`, `/v1/convert` meta, `results/*/meta.json`).

`Meta` (meta.schema.json, design 5.4) is the target with hashes, receipts, coverage and legal basis; no run writes it
yet. This model is the shape that is shipped, so that a client and a test can hold it: `contracts/coi/sidecar.schema.json`
is written from it (`python -m app.model.schemas`). Warnings use the same `Warning` and `WarningCode` as every step.
"""
from __future__ import annotations

from typing import Literal

from pydantic import Field

from .common import Contract, Warning
from .meta import FieldEvidence, Ledger, Proposals


class RunConverter(Contract):
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    pipeline: Literal["brief", "interim"] = Field(description="interim: the finder found no candidate, title and standard pages only.")
    reader: str = Field(min_length=1, description='The reader that read the file, e.g. "pdf.native".')


class RunCounts(Contract):
    pages: int = Field(ge=0, description="Pages (tabs) of the form.")
    fields: int = Field(ge=0, description="Components of the form, all pages.")
    source_pages: int = Field(ge=0, description="Pages of the uploaded file.")


class RunCheck(Contract):
    id: str = Field(pattern=r"^G([1-9]|1[0-2])$")
    name: str = Field(min_length=1)
    status: Literal["passed", "failed", "not_applicable"]
    reason: str | None = None


class DictionaryLink(Contract):
    """A8 DX-2: one field of the paper that names a dictionary of the partner (`compose.dictionaries.links`)."""
    field: str = Field(min_length=1, description="Form id of the field.")
    label: str
    dictionary: str = Field(min_length=1)
    written: bool = Field(description="True when the form JSON carries the link, false when it was only noted.")
    why: str = Field(min_length=1)


class RunMeta(Contract):
    origins: dict[str, Literal["paper", "standard", "reviewer"]] = {}
    brief_keys: dict[str, str] = Field(default={}, description="Form id -> key of the brief field it was composed from.")
    evidence: dict[str, list[FieldEvidence]] = Field(default={}, description="Form id -> where the field stands on the paper (A8 VB-4); fields of the matter only.")
    ledger: Ledger | None = Field(default=None, description="Absent on the interim path and when it does not close (LEDGER_NOT_CLOSED).")
    # A8 DX-1, DX-2 (`compose.dictionaries.sidecar_extras`): each key is written only when it has something to say.
    proposals: Proposals | None = Field(default=None, description="Proposed dictionaries; absent when there are none.")
    dictionary_links: list[DictionaryLink] = Field(default=[], description="Absent when no field names a dictionary.")


class Sidecar(Contract):
    version: Literal[1]
    converter: RunConverter
    counts: RunCounts
    warnings: list[Warning] = []
    checks: list[RunCheck] = Field(description="The import gate, G1 to G12, in order.")
    meta: RunMeta
