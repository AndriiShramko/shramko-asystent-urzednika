"""HTML of descriptions, text blocks and consents (D11): built from these templates only.

Text from the paper enters as a plain `str` and is escaped; a fragment made here is a `Markup`. The finished body
passes the allow-list (`p`, `br`, `strong`, `em`, `ul`, `ol`, `li`, `a` with an https target) before it is wrapped
in the document shell of the partner's exports.
"""
from __future__ import annotations

from html import escape

import nh3

from app.model.form import EMPTY_HTML

ALLOWED_TAGS = {"p", "br", "strong", "em", "ul", "ol", "li", "a"}
ALLOWED_ATTRIBUTES = {"a": {"href"}}
ALLOWED_SCHEMES = {"https"}
_OPEN, _CLOSE = "<html><head></head><body>", "</body></html>"


class Markup(str):
    """A fragment built by this module: already escaped."""


def _inline(parts: tuple[object, ...]) -> str:
    return "".join(x if isinstance(x, Markup) else escape(str(x), quote=True) for x in parts)


def p(*parts: object) -> Markup:
    return Markup(f"<p>{_inline(parts)}</p>")


def strong(*parts: object) -> Markup:
    return Markup(f"<strong>{_inline(parts)}</strong>")


def link(href: str, text: str) -> Markup:
    """A link only to an https address; anything else stays the plain text."""
    if not href.startswith("https://"):
        return Markup(escape(text, quote=True))
    return Markup(f'<a href="{escape(href, quote=True)}">{escape(text, quote=True)}</a>')


def clean(body: str) -> str:
    return nh3.clean(body, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, url_schemes=ALLOWED_SCHEMES)


def doc(*blocks: Markup) -> str:
    """The document of a description: our blocks, sanitised, in the shell of the exports."""
    if not blocks:
        return EMPTY_HTML
    if not all(isinstance(b, Markup) for b in blocks):
        raise TypeError("doc() takes fragments built by p(), strong(), link(): never raw text")
    return f"{_OPEN}{clean(''.join(blocks))}{_CLOSE}"


def body_of(html: str) -> str | None:
    """The body of a document written by doc(); None when the string is not in our shell."""
    if html.startswith(_OPEN) and html.endswith(_CLOSE):
        return html[len(_OPEN): len(html) - len(_CLOSE)]
    return None


def is_ours(html: str) -> bool:
    """True when the string is empty or a document whose body passes the allow-list unchanged (for the gate)."""
    if html == "":
        return True
    body = body_of(html)
    return body is not None and clean(body) == body
