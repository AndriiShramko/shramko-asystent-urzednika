"""Reading a plain form dict without trusting it: pages, sections and components with their JSON pointers.

The gate judges any JSON (ours, the partner's exports, a broken one), so nothing here assumes a key exists or
has the right type: what is not a dict or a list is skipped, and the schema check (G1) reports it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator


def _list(x: Any) -> list:
    return x if isinstance(x, list) else []


def _dict(x: Any) -> dict:
    return x if isinstance(x, dict) else {}


@dataclass
class Node:
    """A section (component is None on the section itself) or a component, with the cell around its field."""

    path: str                 # JSON pointer of the field dict
    cell: dict                # the question: x, y, rows, cols, field
    field: dict
    page: int
    page_title: str
    section: "Node | None" = None

    @property
    def tech(self) -> str:
        t = self.field.get("techName")
        return t if isinstance(t, str) else ""

    @property
    def states(self) -> list[dict]:
        return [s for s in _list(self.field.get("states")) if isinstance(s, dict)]


@dataclass
class Index:
    form: dict
    pages: list[dict] = field(default_factory=list)
    sections: list[Node] = field(default_factory=list)
    components: list[Node] = field(default_factory=list)

    def __post_init__(self) -> None:
        for p, tab in enumerate(_list(self.form.get("tabs"))):
            tab = _dict(tab)
            self.pages.append(tab)
            title = tab.get("title") if isinstance(tab.get("title"), str) else ""
            for s, q in enumerate(_list(tab.get("questions"))):
                q = _dict(q)
                f = _dict(q.get("field"))
                sec = Node(f"/tabs/{p}/questions/{s}/field", q, f, p, title)
                self.sections.append(sec)
                for c, iq in enumerate(_list(f.get("repeatingSectionGrid"))):
                    iq = _dict(iq)
                    self.components.append(Node(f"{sec.path}/repeatingSectionGrid/{c}/field", iq, _dict(iq.get("field")),
                                                p, title, sec))

    def nodes(self) -> Iterator[Node]:
        yield from self.sections
        yield from self.components

    def by_tech(self, tech: str) -> list[Node]:
        return [n for n in self.nodes() if n.tech == tech]

    def path_of(self, tech: str) -> str:
        """Pointer of the one node with this techName; "" when there is none or more than one."""
        hits = self.by_tech(tech)
        return hits[0].path if len(hits) == 1 else ""


def strings(x: Any, path: str = "") -> Iterator[tuple[str, str, str]]:
    """Every string leaf as (pointer, key, value)."""
    if isinstance(x, dict):
        for k, v in x.items():
            if isinstance(v, str):
                yield f"{path}/{k}", str(k), v
            else:
                yield from strings(v, f"{path}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            if isinstance(v, str):
                yield f"{path}/{i}", "", v
            else:
                yield from strings(v, f"{path}/{i}")
