"""Pieces shared by our own contracts (page model, finder output, brief, meta).

Conventions of every contract of ours (decisions in docs/03-plan/wip/WP-F0b.status.md, WP-F0c.status.md):
- unknown keys are refused (extra="forbid");
- absent means none: a key is left out instead of written as null, and an explicit null is refused, so the
  JSON Schema written from these models (app.model.schemas) has no nullable types;
- coordinates are points with the origin at the top left of the page: box = [x0, y0, x1, y1];
- output is deterministic: key order is the declaration order, maps keyed by ids are sorted, no timestamps;
- revision 1.1 is additive: every key it adds is optional and left out while unused (None, or an empty list
  through `omit_empty`), so a document that does not use it is written byte for byte as in revision 1.0.

Closed code lists live here. A new code is added in THIS file, with a comment naming the design section or
acceptance list that needs it; the schema files are then regenerated (python -m app.model.schemas).
"""
from __future__ import annotations

import json
import math
from typing import Annotated, Any, Literal, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, GetCoreSchemaHandler, model_validator
from pydantic_core import CoreSchema


def _check_box(b: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = b
    if x1 < x0 or y1 < y0:
        raise ValueError(f"box must be [x0, y0, x1, y1] with x0 <= x1 and y0 <= y1, got {list(b)}")
    return b


class Box(tuple):  # type: ignore[type-arg]
    """[x0, y0, x1, y1] in points, origin top left. A horizontal line has y0 == y1.

    Used as an annotation; a validated box is a plain tuple of four floats (the schema and the values are those of
    revision 1.0). Readers turn raw coordinates into a box with `Box.from_raw` (revision 1.1).
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return handler.generate_schema(Annotated[tuple[float, float, float, float], AfterValidator(_check_box)])

    @staticmethod
    def from_raw(x0: Any, y0: Any, x1: Any, y1: Any) -> tuple[float, float, float, float] | None:
        """Reader boundary: reversed endpoints are swapped; a coordinate that is not a finite number gives None
        (the element cannot be placed: the caller skips it with UNREADABLE_PART and never invents a box)."""
        try:
            v = [float(x0), float(y0), float(x1), float(y1)]
        except (TypeError, ValueError):
            return None
        if not all(math.isfinite(x) for x in v):
            return None
        return (min(v[0], v[2]), min(v[1], v[3]), max(v[0], v[2]), max(v[1], v[3]))


Anchor = Annotated[str, Field(min_length=1, description='Place in a file without geometry: "p[12]", "p[12]/cell[2,3]", "Arkusz1!B7".')]
Unit = Annotated[float, Field(ge=0.0, le=1.0)]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
PageNo = Annotated[int, Field(ge=1)]

# Content kind of the input, not its extension: .jpg and .jpeg are both "jpeg" (design 6.2, task card).
Format = Literal["pdf", "doc", "docx", "ods", "xlsx", "jpeg", "png", "rtf", "xls", "txt", "heic"]

# Reasons for something of the paper that does not become a field (design 6.4.3, 5.3 "dropped", 5.4
# "omissions", ledger fate LEFT_OUT). Add a code here with the design row that needs it.
ReasonCode = Literal[
    "PAPER_INSTRUCTION",    # 6.4.3 "WYPEŁNIJ WIELKIMI LITERAMI"
    "COVERED_BY_STANDARD",  # 6.4.3 applicant block -> standard sections
    "SIGNATURE_AND_DATE",   # 6.4.3 "miejscowość, data", "podpis"
    "OFFICE_USE",           # 6.4.3 "wypełnia organ"
    "PAGE_FURNITURE",       # 6.4.3 page numbers, version marks
    "GRAMMAR_VARIANT",      # 6.4.3 alternatives that are only grammar
    "CLAUSE_LINKED",        # 6.4.3 data-protection clause -> consent with a link
    "EXPLANATION",          # 6.4.3 explanations keyed to positions, the rest
    "COMPUTED_VALUE",       # 6.4.3 printed arithmetic -> unsupported
]

# Warnings of any step (design 3, 6.3-6.5, 7.4, 7.5; acceptance lists of F2, F3, F4, F15, F17).
# Add a code here with the section or acceptance item that needs it.
WarningCode = Literal[
    "NOT_A_FORM",            # F3: an information sheet without places to fill
    "UNREADABLE_PART",       # design 3: a partly unreadable file still answers 200, with warnings
    "OCR_USED",              # 6.2: a page took the image way; its text has OCR confidence
    "HIDDEN_SHEET",          # F2b: hidden sheets are read and reported
    "ACTIVE_CONTENT",        # design 3, 8: macros or DDE seen, never executed
    "FILLED_FORM",           # design 4, 8: the paper looks filled in
    "SILENT_PAGE",           # 7.4, F15: a page with ink and no candidate, reported by number
    "LABEL_NOT_FOUND",       # 6.3.4: a place to fill without a label: honest gap, not a guess
    "LABEL_RAW",             # 6.4.3: label kept as raw words, no nominative form found
    "AMBIGUOUS_GROUP",       # 7.5: a choice group whose options or question are uncertain
    "UNRESOLVED_REFERENCE",  # 6.4.3, 7.5: a condition names a position that does not resolve
    "REQUIRED_INFERRED",     # 6.4.3, F4: required was our call, not the paper's
    "ADDRESSEE_CONFLICT",    # 6.4.1, F4: two different offices named
    "COMPOSITE_UNRESOLVED",  # 6.4.4: several applications in one paper, no selector
    "INFERRED_SHAPE",        # 6.5.4, skill rule 14: a component shape no export shows
    "LOW_CONFIDENCE",        # 7.5: confidence below the review threshold
    # revision 1.1, verification plan 5 #7: required_basis "paper" without evidence (brief.check_paper_evidence)
    "REQUIRED_WITHOUT_EVIDENCE",
    # revision 1.1, WP-F5 request 3: the composer's remark codes (app.compose.Remark.code), carried by F15
    "CONDITION_NOT_WRITTEN", "SECTION_SPLIT", "REPEATING_FLATTENED", "STEP_NOTE_ADDED", "MARKUP_IN_LABEL",
    "TITLE_MISSING", "ADDRESSEE_MISSING", "APPLICANTS_ASSUMED", "SOLE_TRADER_AS_ENTITY", "CLAUSE_LINK_MISSING",
    "NO_MATTER", "EXTRA_NOT_PLACED",
    # WP-H4: the three outcomes of the model step; `app.engine.engine_of` reads them. Not emitted until WP-H1.
    "MODEL_USED",            # the model step ran and its answer was applied: engine rules+model
    "MODEL_FALLBACK",        # the model step was tried and failed; the output is the output of the rules
    "MODEL_SKIPPED",         # a model is configured and the step had nothing to ask: engine rules
    # A8 VB-1: the codes app.pipeline writes itself (sidecar.schema.json): a note of the guard, the ledger that did
    # not close, the interim path (interim.NOT_READ_CODE), a failed non-blocking check of the gate (D19)
    "INPUT_NOTE", "LEDGER_NOT_CLOSED", "BRIEF_NOT_READ",
    "GATE_G5", "GATE_G6", "GATE_G7", "GATE_G8", "GATE_G9", "GATE_G10", "GATE_G11", "GATE_G12",
]

Status = Literal["stated", "not_found", "ambiguous"]

# The five fates of a blank (design 5.4). The order is the order of the counts in the ledger. Revision 1.1 moved
# both lists here from meta so that the brief's dispositions use the same words (app.model.meta re-exports them).
Fate = Literal["FIELD", "MERGED", "STANDARD", "LEFT_OUT", "AWAITING_DECISION"]
# Why a blank was merged into another (design 5.4 example, 6.3.3, 6.4.3). Add a code here with its rule.
MergeWhy = Literal["COMB_CELLS", "GROUP_MEMBER", "LINE_BLOCK", "SAME_ALTERNATIVE", "TABLE_ROW"]


def _refuse_nulls(data: Any) -> Any:
    if isinstance(data, dict):
        nulls = sorted(k for k, v in data.items() if v is None)
        if nulls:
            raise ValueError(f"null is not written in our contracts, leave the key out: {nulls}")
    return data


class Contract(BaseModel):
    """Base of our own contracts: unknown keys refused, explicit null refused, deterministic JSON."""

    model_config = ConfigDict(extra="forbid", validate_assignment=False)

    @model_validator(mode="before")
    @classmethod
    def _no_nulls(cls, data: Any) -> Any:
        return _refuse_nulls(data)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)

    def to_json_bytes(self) -> bytes:
        return canonical_json(self.to_dict())


def canonical_json(obj: Any) -> bytes:
    """The one serialisation of every JSON we write: UTF-8, two-space indent, key order kept, newline at end."""
    return (json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _empty(v: Any) -> bool:
    return not v


def omit_empty(**kw: Any) -> Any:
    """A list or map added in revision 1.1: empty by default and left out of the JSON while empty, so a document
    that does not use it is written byte for byte as in revision 1.0."""
    kw.setdefault("default_factory", list)
    return Field(exclude_if=_empty, **kw)


def placed(obj: Any, what: str) -> None:
    """Shared rule (revision 1.1): an element carries a box, an anchor, or both (a text box anchored to a
    paragraph); never neither. Which of the two the page demands is the page's rule (app.model.page)."""
    if getattr(obj, "box", None) is None and getattr(obj, "anchor", None) is None:
        raise ValueError(f"{what} {getattr(obj, 'id', '')!s} must carry a box or an anchor (or both), not neither")


exactly_one_place = placed  # the revision 1.0 name, kept for importers

ONE_PLACE_SCHEMA: dict[str, Any] = {"anyOf": [{"required": ["box"]}, {"required": ["anchor"]}]}


class Span(Contract):
    """Characters [start, end) of one run's text (Python string indices, end exclusive): a mark, a label or an
    option that shares its run with others ("❑ pies ❑ suka"). Revision 1.1. A whole run is still named by its id
    alone. That a span lies inside its run's text is checked against the page model (FinderOutput.check_spans)."""

    run: str = Field(min_length=1)
    start: int = Field(ge=0)
    end: int = Field(ge=1)

    @model_validator(mode="after")
    def _ordered(self) -> Self:
        if self.end <= self.start:
            raise ValueError(f"span of run {self.run}: end {self.end} must be greater than start {self.start}")
        return self


class Evidence(Contract):
    """Where a statement comes from: a quote, and the place on the paper when it is known.

    Revision 1.1: a record may carry box and anchor together (an anchored text box), and may leave out the quote
    when it locates a drawn blank with a box or an anchor. A Stated value still needs a quote (see Stated).
    """

    page: PageNo | None = None
    box: Box | None = None
    anchor: Anchor | None = None
    runs: list[str] = []
    quote: str | None = Field(default=None, min_length=1)
    candidate: str | None = None
    spans: list[Span] = omit_empty()

    @model_validator(mode="after")
    def _quote_or_place(self) -> Self:
        if self.quote is None and self.box is None and self.anchor is None:
            raise ValueError("evidence without a quote locates the blank with a box or an anchor")
        return self


class Stated(Contract):
    """A value the paper states, does not state, or states in competing ways (design 5.3).

    stated: evidence with at least one quote; not_found: no value and no evidence; ambiguous: the competing quotes.
    A value is never filled in without one of the three.
    """

    status: Status
    value: str | None = None
    evidence: list[Evidence] = []

    @model_validator(mode="after")
    def _status_has_its_evidence(self) -> Self:
        quoted = any(e.quote is not None for e in self.evidence)
        if self.status == "stated" and not quoted:
            raise ValueError("status 'stated' needs evidence with a quote")
        if self.status == "ambiguous" and not quoted:
            raise ValueError("status 'ambiguous' needs the competing quotes as evidence")
        if self.status == "not_found" and (self.value is not None or self.evidence):
            raise ValueError("status 'not_found' carries no value and no evidence")
        return self


class ProposedFee(Contract):
    """1.1: a fee we propose (from a statute or a guide), kept apart from the paper's fee: it never turns a
    `not_found` fee into `stated` (brief.proposed_fee, meta proposals.fee)."""

    value: str = Field(min_length=1)
    why: str = Field(min_length=1)
    evidence: list[Evidence] = []


class Warning(Contract):  # noqa: A001 - the name of the thing in the design
    """One honest gap: what, where, and the quotes that show it."""

    id: str | None = None
    code: WarningCode
    page: PageNo | None = None
    box: Box | None = None
    anchor: Anchor | None = None
    field: str | None = None
    candidate: str | None = None
    evidence: list[Evidence] = []
    detail: str | None = None


class Dropped(Contract):
    """Something of the paper left out on purpose, with its reason (brief "dropped", meta "omissions")."""

    what: str = Field(min_length=1)
    reason: ReasonCode
    page: PageNo | None = None
    runs: list[str] = []
    count: int | None = Field(default=None, ge=1)


class InputRef(Contract):
    sha256: Sha256
    format: Format


def unique(ids: list[str], what: str) -> None:
    seen: set[str] = set()
    dup = sorted({i for i in ids if i in seen or seen.add(i)})  # type: ignore[func-returns-value]
    if dup:
        raise ValueError(f"duplicate {what}: {dup}")
