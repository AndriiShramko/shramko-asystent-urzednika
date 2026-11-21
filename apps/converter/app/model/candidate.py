"""Finder output: places to fill, the role of every other text run, sections and groups (design 5.2, 6.3).

One document per input. Every run of the page model ends up in exactly one of: the runs of a candidate (the
dots, the boxes), the label or an option of a candidate, a section heading, or `roles`. Groups are candidates of
kind choice_group: their options name the member candidates, and each member points back with `group`.
"""
from __future__ import annotations

from typing import Literal, Self

from pydantic import ConfigDict, Field, field_serializer, model_validator

from .common import ONE_PLACE_SCHEMA, Anchor, Box, Contract, InputRef, PageNo, Unit, Warning, exactly_one_place, unique

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


class Candidate(Contract):
    model_config = ConfigDict(json_schema_extra=ONE_PLACE_SCHEMA)

    id: str = Field(min_length=1)
    kind: CandidateKind
    page: PageNo
    box: Box | None = None
    anchor: Anchor | None = None
    runs: list[str] = Field(default=[], description="Runs that are the place itself (dots, box characters).")
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
        exactly_one_place(self, "candidate")
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
    finder_version: Literal[1] = 1
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
