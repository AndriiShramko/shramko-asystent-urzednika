"""Finder output: places to fill, the role of every other text run, sections and groups (design 5.2, 6.3).

One document per input. Every run of the page model ends up in exactly one of: the runs of a candidate (the
dots, the boxes), the label or an option of a candidate, a section heading, or `roles`. Groups are candidates of
kind choice_group: their options name the member candidates, and each member points back with `group`.

Revision 1.1 (additive): a candidate, a label and an option may name `spans` (run id, start, end) when they share
one run with others ("❑ pies ❑ suka": two box candidates, two options, one run); a whole run is still named in
`runs`. `check_spans(page_model)` refuses a span whose run does not exist or that runs past the run's text.
A candidate may carry a box and an anchor together, never neither.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Self

from pydantic import ConfigDict, Field, field_serializer, model_validator

from .common import ONE_PLACE_SCHEMA, Anchor, Box, Contract, InputRef, PageNo, Span, Unit, Warning, omit_empty, placed, unique

if TYPE_CHECKING:
    from .page import PageModel

# Design 5.2. Add a kind here with the finder rule that needs it.
CandidateKind = Literal[
    "leader",             # dots or underscores to write on
    "line_block",         # several dotted lines: a long text
    "comb",               # a row of equal boxes: one value
    "box",                # one small square
    "choice_group",       # boxes or crossed-out alternatives that share a question
    "cell",               # an empty table cell under or beside a header
    "widget",             # declared by the format
    "blank_in_sentence",  # a blank inside running text
    "signature",
    "office_use",
]
# Design 5.2, plus "body" for ordinary running text that is none of the others (so no run is left without a role).
TextRole = Literal["heading", "note", "instruction", "legal_basis", "clause", "page_furniture", "body"]
# Design 6.3.4, in order of preference; "sentence" is the text around a blank_in_sentence.
LabelHow = Literal["widget_name", "same_cell", "leader", "left", "above", "header", "question", "sentence"]


class Label(Contract):
    text: str = Field(min_length=1)
    runs: list[str] = []
    how: LabelHow
    margin: Unit = Field(description="Score distance to the second-best label; small means doubtful.")
    spans: list[Span] = omit_empty(description="1.1: parts of runs that hold the label, when the run holds more.")


class Confidence(Contract):
    geometry: Unit
    label: Unit
    text: Unit


class ChoiceOption(Contract):
    """One alternative of a choice_group: its text, the box marking it (if drawn), the blank after it (if any)."""

    text: str = Field(min_length=1)
    runs: list[str] = []
    mark: str | None = Field(default=None, description="Id of the box candidate that marks this option.")
    blank: str | None = Field(default=None, description='Id of the candidate written after the option ("inne ……").')
    spans: list[Span] = omit_empty(description="1.1: parts of runs that hold the option's text, when the run holds more.")


class Candidate(Contract):
    model_config = ConfigDict(json_schema_extra=ONE_PLACE_SCHEMA)

    id: str = Field(min_length=1)
    kind: CandidateKind
    page: PageNo
    box: Box | None = None
    anchor: Anchor | None = None
    runs: list[str] = Field(default=[], description="Runs that are the place itself (dots, box characters).")
    spans: list[Span] = omit_empty(description="1.1: parts of runs that are the place itself (one box character of a longer run).")
    cells: int | None = Field(default=None, ge=1, description="Comb: number of boxes.")
    lines: int | None = Field(default=None, ge=1, description="line_block: number of lines.")
    mask: str | None = Field(default=None, description='Printed separators of a comb, e.g. "__-___", "DD-MM-RRRR".')
    widget: str | None = Field(default=None, description="Id of the page-model widget, for kind widget.")
    label: Label | None = None
    options: list[ChoiceOption] = []
    group: str | None = Field(default=None, description="Id of the choice_group this candidate belongs to.")
    section: str | None = None
    footnotes: list[str] = []
    conf: Confidence

    @model_validator(mode="after")
    def _shape(self) -> Self:
        placed(self, "candidate")
        if self.kind == "choice_group" and len(self.options) < 2:
            raise ValueError(f"candidate {self.id}: a choice_group has at least two options")
        if self.kind != "choice_group" and self.options:
            raise ValueError(f"candidate {self.id}: only a choice_group has options")
        if self.kind == "comb" and self.cells is None:
            raise ValueError(f"candidate {self.id}: a comb states its number of cells")
        if self.kind == "widget" and self.widget is None:
            raise ValueError(f"candidate {self.id}: a widget candidate names its widget")
        return self


class Section(Contract):
    """A heading of the paper and what it heads; numbering as printed ("2.1", "B.3")."""

    id: str = Field(min_length=1)
    page: PageNo
    title: str = Field(min_length=1)
    number: str | None = None
    runs: list[str] = []
    parent: str | None = None


class FinderOutput(Contract):
    finder_version: Literal[1, 1.1] = Field(default=1.1, description="Revision of this contract; 1 (1.0) still validates.")
    input: InputRef
    order: list[str] = Field(default=[], description="Run ids in reading order (design 6.3.1).")
    sections: list[Section] = []
    candidates: list[Candidate] = []
    roles: dict[str, TextRole] = Field(default={}, description="Run id -> role, for runs that belong to no candidate, label or heading.")
    warnings: list[Warning] = []

    @field_serializer("roles")
    def _sorted_roles(self, v: dict[str, str]) -> dict[str, str]:
        return dict(sorted(v.items()))

    @model_validator(mode="after")
    def _references_resolve(self) -> Self:
        unique([s.id for s in self.sections] + [c.id for c in self.candidates], "ids of sections and candidates")
        unique(self.order, "runs in the reading order")
        sec = {s.id for s in self.sections}
        kinds = {c.id: c.kind for c in self.candidates}
        for s in self.sections:
            if s.parent is not None and s.parent not in sec:
                raise ValueError(f"section {s.id}: parent {s.parent} does not exist")
        for c in self.candidates:
            if c.section is not None and c.section not in sec:
                raise ValueError(f"candidate {c.id}: section {c.section} does not exist")
            if c.group is not None and kinds.get(c.group) != "choice_group":
                raise ValueError(f"candidate {c.id}: group {c.group} is not a choice_group candidate")
            for o in c.options:
                for ref in (o.mark, o.blank):
                    if ref is not None and ref not in kinds:
                        raise ValueError(f"candidate {c.id}: option {o.text!r} names {ref}, which does not exist")
        return self

    def all_spans(self) -> list[tuple[str, Span]]:
        """Every span of the output with the id of its owner: candidate, its label, its options."""
        out: list[tuple[str, Span]] = []
        for c in self.candidates:
            out += [(c.id, s) for s in c.spans]
            if c.label is not None:
                out += [(f"{c.id}/label", s) for s in c.label.spans]
            out += [(f"{c.id}/option[{i}]", s) for i, o in enumerate(c.options) for s in o.spans]
        return out

    def check_spans(self, pages: PageModel) -> None:
        """Refuse (ValueError) a span whose run is not in the page model or that runs past the run's text."""
        runs = pages.run_index()
        bad = []
        for owner, s in self.all_spans():
            hit = runs.get(s.run)
            if hit is None:
                bad.append(f"{owner}: run {s.run} is not in the page model")
            elif s.end > len(hit[1].text):
                bad.append(f"{owner}: span [{s.start}, {s.end}) runs past the text of run {s.run} ({len(hit[1].text)} characters)")
        if bad:
            raise ValueError("spans do not resolve: " + "; ".join(bad))
