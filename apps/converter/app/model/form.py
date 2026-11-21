"""The PARTNER's form tree: title, tabs, components, flow.links (contracts/coi/form.schema.json, D1-D7).

This is the only object the conversion endpoint answers with. No key of ours ever appears in it: origins,
evidence and confidence live in the sidecar (meta), keyed by the ids of this tree.

Two readings of one model:
- strict (default, `Form.model_validate(data)`): what we emit. UUID ids, every option with a techName,
  `validation` a list, no `minItemRows`, the one-column grid of D4, techNames unique, slug-shaped, at most 60
  characters (D7), links between existing pages.
- tolerant (`Form.from_partner_export(data)`): what the partner's own exports contain. Link ids that are not
  UUIDs, an option without techName, `validation: {}` (read as []), `minItemRows`, a field without `states`.
  Nothing else is relaxed: any other unknown key is refused in both readings.

Serialisation (`to_partner`, `to_json_bytes`) emits exactly the partner's keys, in the order of their exports,
with the D3 defaults filled: options [], validation [], readOnly, repeatingSectionGrid [], states [],
tooltipMessage "". Optional keys appear only when set. Build components with the helpers at the end of this
module so that no default and no grid number is forgotten.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from .common import canonical_json

SECTION_TYPES = ("SECTION", "REPEATING_SECTION")
COMPONENT_TYPES = ("TEXT_FIELD", "CHECKBOX", "NUMBER", "CONSENT_SECTION", "SELECT", "TEXTAREA",
                   "FILE_UPLOADER", "RADIO", "DATEPICKER", "TEXT_BLOCK", "INFO_SECTION")
FieldType = Literal["SECTION", "REPEATING_SECTION", "TEXT_FIELD", "CHECKBOX", "NUMBER", "CONSENT_SECTION", "SELECT",
                    "TEXTAREA", "FILE_UPLOADER", "RADIO", "DATEPICKER", "TEXT_BLOCK", "INFO_SECTION"]
# The partner's predefined validators (D8). Nothing else is ever written into a form.
Validator = Literal["REQUIRED", "EMAIL", "PESEL", "NIP", "REGON", "ZIP_CODE", "EPUAP", "ADE", "SERIAL_NUMBER_ID_CARD"]
EMPTY_HTML = "<html><head></head><body></body></html>"
GRID_X, GRID_COLS = 0, 3

_UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_TECHNAME = re.compile(r"^[a-z][a-z0-9_]*$")
_TECHNAME_MAX = 60


def _tolerant(info: ValidationInfo) -> bool:
    return bool(info.context and info.context.get("tolerant"))


def _uuid(value: str, what: str, info: ValidationInfo) -> str:
    if not _tolerant(info) and not _UUID.match(value):
        raise ValueError(f"{what} must be a UUID, got {value!r}")
    return value


class Partner(BaseModel):
    """Base of the partner's objects: unknown keys refused; declaration order is the export's key order."""

    model_config = ConfigDict(extra="forbid")


class Option(Partner):
    id: str
    name: str
    techName: str | None = None

    @model_validator(mode="after")
    def _strict_tech_name(self, info: ValidationInfo) -> Self:
        if self.techName is None and not _tolerant(info):
            raise ValueError(f"option {self.name!r} has no techName")
        return self

    @classmethod
    def of(cls, text: str, tech_name: str) -> Option:
        """As in the exports: id and name are the visible text, techName its slug."""
        return cls(id=text, name=text, techName=tech_name)


class State(Partner):
    type: Literal["SHOW", "READ_ONLY"]
    query: str = Field(min_length=1)


class ConsentItem(Partner):
    description: str
    required: bool | None = None


class ConsentConfig(Partner):
    consents: list[ConsentItem] = Field(min_length=1)
    required: bool | None = None
    files: list[Any] = []


class FormField(Partner):
    id: str
    type: FieldType
    techName: str
    title: str
    description: str = ""
    dictionaryName: str | None = None
    options: list[Option] = []
    multiLevelTree: bool | None = None
    validation: list[Validator] = []
    searchEnabled: bool | None = None
    readOnly: bool = False
    repeatingSectionGrid: list[Question] = []
    defaultValue: str | list[str] | None = None
    defaultValueType: Literal["EXTERNAL_SYSTEM", ""] | None = None
    consentSectionConfig: ConsentConfig | None = None
    states: list[State] = []
    questionOrder: int = Field(ge=0)
    tooltipMessage: str = ""

    @field_validator("validation", mode="before")
    @classmethod
    def _empty_object_is_empty_list(cls, v: Any, info: ValidationInfo) -> Any:
        if isinstance(v, dict) and not v and _tolerant(info):
            return []
        return v

    @field_validator("id")
    @classmethod
    def _id_uuid(cls, v: str, info: ValidationInfo) -> str:
        return _uuid(v, "field id", info)

    @model_validator(mode="after")
    def _shape(self, info: ValidationInfo) -> Self:
        if len(set(self.validation)) != len(self.validation):
            raise ValueError(f"{self.techName}: a validator is listed twice")
        if self.type in COMPONENT_TYPES and self.repeatingSectionGrid:
            raise ValueError(f"{self.techName}: a {self.type} has an empty repeatingSectionGrid; sections are never nested")
        if self.type in SECTION_TYPES:
            if not self.repeatingSectionGrid:
                raise ValueError(f"{self.techName}: a section holds at least one component")
            nested = [q.field.techName for q in self.repeatingSectionGrid if q.field.type in SECTION_TYPES]
            if nested:
                raise ValueError(f"{self.techName}: sections are never nested, found {nested}")
        if not _tolerant(info):
            if not _TECHNAME.match(self.techName) or len(self.techName) > _TECHNAME_MAX:
                raise ValueError(f"techName {self.techName!r}: lower-case ASCII slug of at most {_TECHNAME_MAX} characters (D7)")
            if self.type != "SELECT" and (self.dictionaryName, self.multiLevelTree, self.searchEnabled) != (None, None, None):
                raise ValueError(f"{self.techName}: dictionaryName, multiLevelTree, searchEnabled belong to a SELECT")
            if (self.type == "CONSENT_SECTION") != (self.consentSectionConfig is not None):
                raise ValueError(f"{self.techName}: consentSectionConfig is present exactly on a CONSENT_SECTION")
        return self


class Question(Partner):
    x: int = Field(default=GRID_X, ge=0)
    y: int = Field(ge=0)
    rows: int = Field(default=1, ge=1)
    cols: int = Field(default=GRID_COLS, ge=1)
    minItemRows: int | None = None
    field: FormField

    @model_validator(mode="after")
    def _grid(self, info: ValidationInfo) -> Self:
        if _tolerant(info):
            return self
        if self.minItemRows is not None:
            raise ValueError("minItemRows is read from the partner's exports but never written (strict profile)")
        if (self.x, self.cols) != (GRID_X, GRID_COLS) or self.y != self.field.questionOrder:
            raise ValueError(f"{self.field.techName}: one column (x 0, cols 3) and y equal to questionOrder (D4)")
        if self.field.type in COMPONENT_TYPES and self.rows != 1:
            raise ValueError(f"{self.field.techName}: a component has rows 1 (D4)")
        if self.field.type in SECTION_TYPES and sorted(q.y for q in self.field.repeatingSectionGrid) != list(range(len(self.field.repeatingSectionGrid))):
            raise ValueError(f"{self.field.techName}: component y counts 0, 1, 2 ... (D4)")
        return self


class Tab(Partner):
    id: str
    title: str = Field(min_length=1)
    type: Literal["MAIN", "FINISH"]
    questions: list[Question] = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def _id_uuid(cls, v: str, info: ValidationInfo) -> str:
        return _uuid(v, "page id", info)

    @model_validator(mode="after")
    def _sections_only(self, info: ValidationInfo) -> Self:
        loose = [q.field.techName for q in self.questions if q.field.type not in SECTION_TYPES]
        if loose:
            raise ValueError(f"page {self.title!r}: components live only inside sections, found {loose}")
        if not _tolerant(info):
            y = 0
            for q in self.questions:
                if q.y != y:
                    raise ValueError(f"page {self.title!r}: section {q.field.techName} has y {q.y}, expected {y} (D4)")
                y = q.y + q.rows
        return self


class Link(Partner):
    id: str
    source: str
    target: str

    @model_validator(mode="after")
    def _uuids(self, info: ValidationInfo) -> Self:
        for what, v in (("link id", self.id), ("link source", self.source), ("link target", self.target)):
            _uuid(v, what, info)
        return self


class Flow(Partner):
    links: list[Link] = []


class Form(Partner):
    title: str = Field(min_length=1, max_length=255)
    tabs: list[Tab] = Field(min_length=2)
    flow: Flow

    @model_validator(mode="after")
    def _form_wide(self, info: ValidationInfo) -> Self:
        if _tolerant(info):
            return self
        fields = list(self.iter_fields())
        dup = sorted(n for n, c in Counter(f.techName for f in fields).items() if c > 1)
        if dup:
            raise ValueError(f"techName must be unique in the whole form (D7): {dup}")
        ids = [t.id for t in self.tabs] + [f.id for f in fields] + [link.id for link in self.flow.links]
        dup = sorted(n for n, c in Counter(ids).items() if c > 1)
        if dup:
            raise ValueError(f"ids must be unique: {dup}")
        pages = {t.id for t in self.tabs}
        bad = [link.id for link in self.flow.links if link.source not in pages or link.target not in pages]
        if bad:
            raise ValueError(f"links point to pages that do not exist: {bad}")
        return self

    # -- reading ------------------------------------------------------------------------------------------

    @classmethod
    def from_partner_export(cls, data: dict[str, Any]) -> Form:
        """Read one of the partner's own exports, keeping every component (tolerant reading, see module doc)."""
        return cls.model_validate(data, context={"tolerant": True})

    def iter_fields(self):  # noqa: ANN201 - a generator of FormField
        """Every field of the form, sections and their components, in document order."""
        for t in self.tabs:
            for q in t.questions:
                yield q.field
                for c in q.field.repeatingSectionGrid:
                    yield c.field

    # -- writing ------------------------------------------------------------------------------------------

    def to_partner(self) -> dict[str, Any]:
        """The partner's object and nothing else: keys in the exports' order, optional keys only when set."""
        return self.model_dump(mode="json", exclude_none=True)

    def to_json_bytes(self) -> bytes:
        return canonical_json(self.to_partner())

    @classmethod
    def build(cls, title: str, tabs: list[Tab], link_ids: list[str]) -> Form:
        """Chain the pages in order (D4); link ids come from the composer (D10: uuid5 from meaning)."""
        if len(link_ids) != len(tabs) - 1:
            raise ValueError(f"{len(tabs)} pages need {len(tabs) - 1} link ids, got {len(link_ids)}")
        links = [Link(id=i, source=a.id, target=b.id) for i, a, b in zip(link_ids, tabs, tabs[1:], strict=False)]
        return cls.model_validate({"title": title, "tabs": [t.model_dump() for t in tabs], "flow": {"links": [x.model_dump() for x in links]}})


FormField.model_rebuild()
Question.model_rebuild()


# -- constructor helpers: one per type; grid numbers are set by section() and tab() ---------------------------

def _component(type_: str, id: str, tech_name: str, title: str, **kw: Any) -> Question:  # noqa: A002
    field = {"id": id, "type": type_, "techName": tech_name, "title": title, "questionOrder": 0}
    field.update({k: v for k, v in kw.items() if v is not None})
    return Question.model_validate({"y": 0, "field": field}, context={"tolerant": True})


def _common(description: str, validation: list[str] | None, read_only: bool, states: list[State] | None, tooltip: str) -> dict[str, Any]:
    return {"description": description, "validation": list(validation or []), "readOnly": read_only,
            "states": [s.model_dump() for s in states or []], "tooltipMessage": tooltip}


def text_field(id: str, tech_name: str, title: str, *, description: str = "", validation: list[str] | None = None,  # noqa: A002
               read_only: bool = False, states: list[State] | None = None, tooltip: str = "",
               default_value: str | None = None, default_value_type: str | None = None) -> Question:
    return _component("TEXT_FIELD", id, tech_name, title, **_common(description, validation, read_only, states, tooltip),
                      defaultValue=default_value, defaultValueType=default_value_type)


def textarea(id: str, tech_name: str, title: str, *, description: str = "", validation: list[str] | None = None,  # noqa: A002
             read_only: bool = False, states: list[State] | None = None, tooltip: str = "") -> Question:
    return _component("TEXTAREA", id, tech_name, title, **_common(description, validation, read_only, states, tooltip))


def number(id: str, tech_name: str, title: str, *, description: str = "", validation: list[str] | None = None,  # noqa: A002
           read_only: bool = False, states: list[State] | None = None, tooltip: str = "") -> Question:
    return _component("NUMBER", id, tech_name, title, **_common(description, validation, read_only, states, tooltip))


def datepicker(id: str, tech_name: str, title: str, *, description: str = "", validation: list[str] | None = None,  # noqa: A002
               read_only: bool = False, states: list[State] | None = None, tooltip: str = "") -> Question:
    """No export shows a DATEPICKER: the sidecar reports INFERRED_SHAPE for each use (skill rule 14)."""
    return _component("DATEPICKER", id, tech_name, title, **_common(description, validation, read_only, states, tooltip))


def file_uploader(id: str, tech_name: str, title: str, *, description: str = "", validation: list[str] | None = None,  # noqa: A002
                  states: list[State] | None = None, tooltip: str = "") -> Question:
    return _component("FILE_UPLOADER", id, tech_name, title, **_common(description, validation, False, states, tooltip))


def radio(id: str, tech_name: str, title: str, options: list[Option], *, description: str = "",  # noqa: A002
          validation: list[str] | None = None, states: list[State] | None = None, tooltip: str = "") -> Question:
    return _component("RADIO", id, tech_name, title, **_common(description, validation, False, states, tooltip),
                      options=[o.model_dump(exclude_none=True) for o in options])


def checkbox(id: str, tech_name: str, title: str, options: list[Option], *, description: str = "",  # noqa: A002
             validation: list[str] | None = None, states: list[State] | None = None, tooltip: str = "") -> Question:
    """No export shows a CHECKBOX: the sidecar reports INFERRED_SHAPE for each use (skill rule 14)."""
    return _component("CHECKBOX", id, tech_name, title, **_common(description, validation, False, states, tooltip),
                      options=[o.model_dump(exclude_none=True) for o in options])


def select(id: str, tech_name: str, title: str, *, options: list[Option] | None = None,  # noqa: A002
           dictionary_name: str | None = None, multi_level_tree: bool | None = None, search_enabled: bool | None = None,
           default_value: str | list[str] | None = None, default_value_type: str | None = None, description: str = "",
           validation: list[str] | None = None, read_only: bool = False, states: list[State] | None = None,
           tooltip: str = "") -> Question:
    return _component("SELECT", id, tech_name, title, **_common(description, validation, read_only, states, tooltip),
                      options=[o.model_dump(exclude_none=True) for o in options or []], dictionaryName=dictionary_name,
                      multiLevelTree=multi_level_tree, searchEnabled=search_enabled, defaultValue=default_value,
                      defaultValueType=default_value_type)


def text_block(id: str, tech_name: str, title: str, html: str, *, states: list[State] | None = None) -> Question:  # noqa: A002
    """`html` must come from our templates (D11); this helper does not sanitise."""
    return _component("TEXT_BLOCK", id, tech_name, title, **_common(html, None, False, states, ""))


def info_section(id: str, tech_name: str, title: str, html: str, *, states: list[State] | None = None) -> Question:  # noqa: A002
    """No export shows an INFO_SECTION (D5 switch FINISH_STYLE=info_section); reported as INFERRED_SHAPE."""
    return _component("INFO_SECTION", id, tech_name, title, **_common(html, None, False, states, ""))


def consent_section(id: str, tech_name: str, title: str, consents: list[ConsentItem], *,  # noqa: A002
                    required: bool | None = None, states: list[State] | None = None) -> Question:
    cfg = ConsentConfig(consents=consents, required=required, files=[])
    return _component("CONSENT_SECTION", id, tech_name, title, **_common("", None, False, states, ""),
                      consentSectionConfig=cfg.model_dump(exclude_none=True))


def section(id: str, tech_name: str, title: str, components: list[Question], *, description: str = EMPTY_HTML,  # noqa: A002
            states: list[State] | None = None, repeating: bool = False, rows: int | None = None) -> Question:
    """A section with its components laid out: component y = questionOrder = 0, 1, 2 ...; rows = components + 1
    unless given (measured on the exports: 28 of 34 sections). REPEATING_SECTION is INFERRED_SHAPE (skill rule 14)."""
    grid = []
    for i, c in enumerate(components):
        grid.append({**c.model_dump(exclude_none=True), "y": i, "field": {**c.field.model_dump(exclude_none=True), "questionOrder": i}})
    q = _component("REPEATING_SECTION" if repeating else "SECTION", id, tech_name, title,
                   **_common(description, None, False, states, ""), repeatingSectionGrid=grid)
    return q.model_copy(update={"rows": rows if rows is not None else len(components) + 1})


def tab(id: str, title: str, sections: list[Question], *, finish: bool = False) -> Tab:  # noqa: A002
    """A page with its sections laid out: section y continues from the previous y + rows; questionOrder = y."""
    out, y = [], 0
    for s in sections:
        out.append({**s.model_dump(exclude_none=True), "y": y, "field": {**s.field.model_dump(exclude_none=True), "questionOrder": y}})
        y += s.rows
    return Tab.model_validate({"id": id, "title": title, "type": "FINISH" if finish else "MAIN", "questions": out})
