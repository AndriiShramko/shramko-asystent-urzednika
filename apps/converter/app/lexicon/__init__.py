"""Lexicons of the understanding step (design 6.4): data files, so a rule changes without code.

One JSON file per table: `{"lexicon": name, "about": ..., "rows": [...]}`. Every row carries `source` (the design
section, the research file or the task set the row was seen in) and `date`; a row without them is refused at load.
A row mined with a hosted model enters a file only after a rule test uses it (D14).

    from app import lexicon
    lexicon.rows("offices")                      # the rows, in file order (order is preference)
    lexicon.regex("habits", habit="optional")    # one pattern: the union of the rows' `pattern`
    lexicon.compiled("concepts")                 # [(compiled pattern, row), ...]
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

_DIR = Path(__file__).parent


def names() -> list[str]:
    return sorted(p.stem for p in _DIR.glob("*.json"))


@lru_cache(maxsize=None)
def rows(name: str) -> tuple[dict[str, Any], ...]:
    data = json.loads((_DIR / f"{name}.json").read_text(encoding="utf-8"))
    out = tuple(data["rows"])
    for i, row in enumerate(out):
        if not row.get("source") or not row.get("date"):
            raise ValueError(f"lexicon {name}, row {i}: every row carries a source and a date")
    return out


def _where(name: str, where: dict[str, Any]) -> list[dict[str, Any]]:
    return [r for r in rows(name) if all(r.get(k) == v for k, v in where.items())]


@lru_cache(maxsize=None)
def _regex(name: str, key: str, where: tuple[tuple[str, Any], ...]) -> re.Pattern[str]:
    parts = [f"(?:{r[key]})" for r in _where(name, dict(where)) if r.get(key)]
    return re.compile("|".join(parts) if parts else r"(?!x)x", re.IGNORECASE)


def regex(name: str, key: str = "pattern", **where: Any) -> re.Pattern[str]:
    """The union of one key of the rows that match `where`, case-insensitive. No row: a pattern that never matches."""
    return _regex(name, key, tuple(sorted(where.items())))


@lru_cache(maxsize=None)
def _compiled(name: str, where: tuple[tuple[str, Any], ...]) -> tuple[tuple[re.Pattern[str], dict[str, Any]], ...]:
    return tuple((re.compile(r["pattern"], re.IGNORECASE), r) for r in _where(name, dict(where)))


def compiled(name: str, **where: Any) -> tuple[tuple[re.Pattern[str], dict[str, Any]], ...]:
    """Rows that match `where`, each with its own compiled pattern, in file order."""
    return _compiled(name, tuple(sorted(where.items())))
