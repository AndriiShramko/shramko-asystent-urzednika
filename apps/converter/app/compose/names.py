"""Names and ids of the composed form: slugs, unique techNames (D7), deterministic ids from meaning (D10)."""
from __future__ import annotations

import re
import unicodedata
import uuid

TECHNAME_MAX = 60
# Fixed namespace of our form ids (D10). Changing it changes every id of every form: do not.
ID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "urn:formularze-converter:form-ids:v1")

_PL = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")


class ComposeError(ValueError):
    """The composer refuses to write a form it cannot name consistently (a bug of the library, not of the paper)."""


def cut(name: str, limit: int = TECHNAME_MAX) -> str:
    """At most `limit` characters, cut at a word boundary when there is one."""
    if len(name) <= limit:
        return name
    head = name[: limit + 1]
    head = head[: head.rindex("_")] if "_" in head else name[:limit]
    return head.strip("_") or name[:limit]


def slug(text: str, limit: int = TECHNAME_MAX, fallback: str = "pole") -> str:
    """Lower-case ASCII words joined by `_`, starting with a letter (skill rule 5)."""
    s = unicodedata.normalize("NFKD", text.translate(_PL))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    if not s:
        s = fallback
    elif not s[0].isalpha():
        s = f"{fallback}_{s}"
    return cut(s, limit)


class Names:
    """techNames, unique in the whole form: fixed names of the library first, then slugs of labels."""

    def __init__(self) -> None:
        self._used: set[str] = set()

    def reserve(self, name: str) -> str:
        if name in self._used:
            raise ComposeError(f"the library uses the techName {name!r} twice")
        self._used.add(name)
        return name

    def unique(self, base: str, role_suffix: str = "") -> str:
        """`base`; on a collision the role suffix first, a number last (design 6.5.7)."""
        candidates = [base]
        if role_suffix and not base.endswith(f"_{role_suffix}"):
            candidates.append(f"{cut(base, TECHNAME_MAX - len(role_suffix) - 1)}_{role_suffix}"[:TECHNAME_MAX].strip("_"))
        for name in candidates:
            if name not in self._used:
                self._used.add(name)
                return name
        n = 2
        while True:
            tail = f"_{n}"
            name = f"{cut(base, TECHNAME_MAX - len(tail))}{tail}"
            if name not in self._used:
                self._used.add(name)
                return name
            n += 1


class Ids:
    """uuid5(namespace, "<form key>/<path>"); a second use of one path gets `#2` (design 6.5.6)."""

    def __init__(self, namespace: uuid.UUID, form_key: str) -> None:
        self._namespace, self._form_key = namespace, form_key
        self._seen: dict[str, int] = {}

    def of(self, *path: str) -> tuple[str, str]:
        """(id, the path it was made from)."""
        key = "/".join((self._form_key, *path))
        n = self._seen.get(key, 0) + 1
        self._seen[key] = n
        if n > 1:
            key = f"{key}#{n}"
        return str(uuid.uuid5(self._namespace, key)), key
