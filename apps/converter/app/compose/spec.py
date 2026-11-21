"""The composer's own plan of a form, before names, ids and conditions are resolved.

Builders of the library and the matter step return these; `compose` turns them into the partner's tree through the
constructor helpers of app.model.form. Nothing here is serialised.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.model.form import EMPTY_HTML

from .query import Pred


@dataclass
class Comp:
    key: str                               # meaning inside the section: the last segment of the id path (D10)
    type: str
    title: str
    tech: str | None = None                # fixed techName of the library; None: slug of the title, made unique
    name_from: str | None = None           # the text the techName is made from when it is not the title
    html: str = ""                         # description, written by compose.html only (D11)
    options: tuple[str, ...] = ()
    show: Pred | None = None
    validation: tuple[str, ...] = ()       # dropped when validators are off (D8)
    read_only: bool = False
    default: str | list[str] | None = None
    default_type: str | None = None
    dictionary: str | None = None
    multi_level: bool | None = None
    search: bool | None = None
    consents: tuple[tuple[str, bool], ...] = ()   # (html, required)
    ref: str | None = None                 # the name conditions use for this field
    origin: str = "standard"               # "paper" | "standard" (two ink colours)
    brief_key: str | None = None


@dataclass
class Sec:
    role: str                              # id path of the section: "dane/twoje_dane", "matter/zwrot"
    title: str
    tech: str | None
    comps: list[Comp]
    html: str = EMPTY_HTML
    show: Pred | None = None
    repeating: bool = False
    origin: str = "standard"
    name_from: str | None = None           # the text the techName is made from when it is not the title


@dataclass
class Page:
    role: str
    title: str
    secs: list[Sec] = field(default_factory=list)
    finish: bool = False
