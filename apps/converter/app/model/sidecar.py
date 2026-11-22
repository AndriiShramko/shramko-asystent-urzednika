"""The sidecar a run returns today (`app.pipeline.run`, `/v1/convert` meta, `results/*/meta.json`).

`Meta` (meta.schema.json, design 5.4) is the target with hashes, receipts, coverage and legal basis; no run writes it
yet. This model is the shape that is shipped, so that a client and a test can hold it: `contracts/coi/sidecar.schema.json`
is written from it (`python -m app.model.schemas`). Warnings use the same `Warning` and `WarningCode` as every step.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .common import Anchor, Box, Contract, PageNo, Warning
from .meta import FieldEvidence, Ledger, Proposals


# -- W11 CLERK-S: the ready fix of a remark (LEAD wave-11/clerk-contract.md) ----------------------------------------

class FixSource(Contract):
    """Where a proposal comes from: a place of the paper, a dictionary, or a rule of the converter."""
    type: Literal["paper", "dictionary", "rule"]
    name: str | None = Field(default=None, description="dictionary or rule: its name.")
    page: PageNo | None = None
    box: Box | None = None
    anchor: Anchor | None = None
    quote: str | None = None


class FixTarget(Contract):
    """The node of the form the remark is about."""
    id: str = Field(min_length=1, description="Form id of the field or section.")
    pointer: str = Field(pattern=r"^/", description="RFC 6901 pointer of the node's `field` object in the form JSON.")
    label: str
    tab: str = Field(description="Title of the form page the node stands on.")


class FixSet(Contract):
    """One write into the form JSON: the value at `pointer` is replaced; the shape above it never changes."""
    pointer: str = Field(pattern=r"^/")
    value: Any


class FixInputSet(Contract):
    pointer: str = Field(pattern=r"^/")
    from_: Literal["input"] = Field(alias="from")


class FixOption(Contract):
    label: str = Field(min_length=1, description="Polish, the text of the button.")
    value: str
    current: bool = Field(description="True on the one option the form JSON holds now.")
    set: list[FixSet]
    source: FixSource | None = None


class FixInput(Contract):
    label: str = Field(min_length=1)
    set: list[FixInputSet | FixSet] = Field(description="`from: input` takes the typed string; an entry with `value` is written as it is.")


class Fix(Contract):
    """applied: the converter decided and only tells what it did (never in the clerk's list); choice: 2 to 5 ready
    options, the most likely first; input: nothing could be proposed."""
    kind: Literal["applied", "choice", "input"]
    rule: str = Field(pattern=r"^[a-z_]+\.[a-z_]+$", description="Stable id of the decision.")
    text: str = Field(min_length=1, description="Polish, one sentence, ready to show.")
    target: FixTarget | None = None
    value: str | None = None
    options: list[FixOption] = Field(default=[], max_length=5)
    input: FixInput | None = None
    source: FixSource | None = None


class RunWarning(Warning):
    fix: Fix | None = None


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
    warnings: list[RunWarning] = []
    checks: list[RunCheck] = Field(description="The import gate, G1 to G12, in order.")
    meta: RunMeta
