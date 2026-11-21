"""The conditions the composer needs, written in exactly the notation of the partner's exports.

    ("O" in tabs['P' in title].questions['S' in field.techName].field.repeatingSectionGrid['F' in field.techName].field.__userAnswer)

joined with `and`, `or`, brackets and `$not(...)`. A predicate names a field by a reference ("std:kraj",
"brief:<key>"); the place of the field (page title, section and field techName) is resolved when the form is
written, so a renamed page or label can never leave a stale path. The conditions package (WP-F7) owns the full
resolver, the evaluation and the notation for repeating sections; this module stays the small writer.
"""
from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass

from app.model.brief import Cond

from .names import ComposeError


@dataclass(frozen=True)
class Is:
    ref: str
    option: str


@dataclass(frozen=True)
class Not:
    inner: Pred


@dataclass(frozen=True)
class All:
    parts: tuple[Pred, ...]


@dataclass(frozen=True)
class Any:
    parts: tuple[Pred, ...]


Pred = Is | Not | All | Any


@dataclass(frozen=True)
class Place:
    page_title: str
    section: str
    field: str


def all_of(*parts: Pred | None) -> Pred | None:
    """Conjunction; None means "always" and is dropped."""
    kept = tuple(x for x in parts if x is not None)
    return None if not kept else kept[0] if len(kept) == 1 else All(kept)


def any_of(*parts: Pred | None) -> Pred | None:
    """Disjunction; one "always" (None) makes the whole "always"."""
    if not parts or any(x is None for x in parts):
        return None
    return parts[0] if len(parts) == 1 else Any(tuple(x for x in parts if x is not None))


def from_brief(cond: Cond | None) -> Pred | None:
    if cond is None:
        return None
    if cond.field is not None:
        return Is(f"brief:{cond.field}", cond.is_ or "")
    if cond.not_ is not None:
        return Not(from_brief(cond.not_))  # type: ignore[arg-type]
    parts = tuple(from_brief(c) for c in (cond.all_of or cond.any_of or []))
    return All(parts) if cond.all_of is not None else Any(parts)  # type: ignore[arg-type]


def refs(pred: Pred) -> Iterator[str]:
    if isinstance(pred, Is):
        yield pred.ref
    elif isinstance(pred, Not):
        yield from refs(pred.inner)
    else:
        for part in pred.parts:
            yield from refs(part)


def _literal(text: str, quote: str) -> str:
    """A JSONata string. Its escapes are those of JSON, so a single quote cannot be escaped inside single quotes:
    a name with `'` or a backslash is written in double quotes."""
    if quote == "'" and "'" not in text and "\\" not in text:
        return f"'{text}'"
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _atom(pred: Is, places: Mapping[str, Place]) -> str:
    place = places.get(pred.ref)
    if place is None:
        raise ComposeError(f"a condition names {pred.ref!r}, which is not a field of this form")
    option, page = _literal(pred.option, '"'), _literal(place.page_title, "'")
    section, field = _literal(place.section, "'"), _literal(place.field, "'")
    return (f"{option} in tabs[{page} in title].questions[{section} in field.techName]"
            f".field.repeatingSectionGrid[{field} in field.techName].field.__userAnswer")


def write(pred: Pred, places: Mapping[str, Place]) -> str:
    if isinstance(pred, Is):
        return f"({_atom(pred, places)})"
    if isinstance(pred, Not):
        inner = _atom(pred.inner, places) if isinstance(pred.inner, Is) else write(pred.inner, places)
        return f"$not({inner})"
    joiner = " and " if isinstance(pred, All) else " or "
    return joiner.join(write(x, places) if isinstance(x, (Is, Not)) else f"({write(x, places)})" for x in pred.parts)
