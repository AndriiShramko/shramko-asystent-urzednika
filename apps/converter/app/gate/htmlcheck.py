"""G10: every HTML string passes an allow-list; no script target; the title within its cap (D11).

HTML strings are the values of the keys in HTML_KEYS anywhere in the form. Two allow-lists:
  strict   what our templates write (app.compose.html): the document shell of the exports around p, br, strong,
           em, ul, ol, li and a with an https target (and the rel that nh3 adds); the body must come out of the
           sanitiser of app.compose.html unchanged.
  tolerant what the partner's two exports contain (measured 21 November): adds span, img, pre and the attributes
           style, target, rel, aria-label, title, alt, width, height, data-language; img may carry a data:image
           picture. A tag that nh3 would remove still fails.
Both: no javascript:, vbscript: or (outside a picture) data: target, no event attribute, no CSS expression.
Plain-text keys (titles, option names) are not HTML and are not judged here.
"""
from __future__ import annotations

import re
from collections import Counter
from html.parser import HTMLParser

import nh3

from app.compose.html import ALLOWED_TAGS, clean
from app.gate.report import CheckResult, Finding
from app.gate.walk import strings

HTML_KEYS = frozenset({"description", "tooltipMessage"})
TITLE_MAX = 255
SHELL = ("<html><head></head><body>", "</body></html>")
DOCUMENT_TAGS = {"html", "head", "body"}
TAGS = {
    "strict": set(ALLOWED_TAGS),
    "tolerant": {"p", "br", "strong", "em", "ul", "ol", "li", "a", "span", "img", "pre", "b", "i", "u"},
}
ATTRS = {
    "strict": {"a": {"href", "rel"}},           # rel: the "noopener noreferrer" that nh3 adds to every link
    "tolerant": {"a": {"href", "target", "rel", "aria-label", "title", "style"}, "img": {"src", "alt", "width", "height"},
                 "span": {"style"}, "strong": {"style"}, "p": {"style"}, "pre": {"data-language"}},
}
PICTURE = re.compile(r"^data:image/(png|jpeg|gif|webp);base64,[A-Za-z0-9+/=\s]*$")
BAD_SCHEME = re.compile(r"^(javascript|vbscript|data|file):", re.I)
BAD_TEXT = re.compile(r"javascript:|vbscript:|expression\s*\(", re.I)
BODY = re.compile(r"<body[^>]*>(.*)</body>", re.I | re.S)


class _Walk(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, list[tuple[str, str]]]] = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, [(a, v or "") for a, v in attrs]))

    handle_startendtag = handle_starttag


def _tags(markup: str) -> list[tuple[str, list[tuple[str, str]]]]:
    w = _Walk()
    w.feed(markup)
    w.close()
    return w.tags


def _clean(body: str, profile: str) -> str:
    if profile == "strict":
        return clean(body)      # the very sanitiser of our templates: one allow-list, not two
    return nh3.clean(body, tags=TAGS[profile], attributes=ATTRS[profile], url_schemes={"https", "http", "mailto", "data"},
                     link_rel=None)


def html_problems(markup: str, profile: str) -> list[str]:
    """What is wrong with one HTML string under the profile; [] when it passes."""
    if markup == "":
        return []
    out: list[str] = []
    for tag, attrs in _tags(markup):
        if tag in DOCUMENT_TAGS:
            continue
        if tag not in TAGS[profile]:
            out.append(f"tag <{tag}> is not on the allow-list")
            continue
        for a, v in attrs:
            if a not in ATTRS[profile].get(tag, set()):
                out.append(f"attribute {a!r} on <{tag}> is not on the allow-list")
                continue
            compact = re.sub(r"\s+", "", v)
            if a in ("href", "src"):
                if tag == "img" and a == "src" and PICTURE.match(v.strip()):
                    pass
                elif BAD_SCHEME.match(compact):
                    out.append(f"{a} of <{tag}> has a forbidden target {compact[:24]!r}")
                elif profile == "strict" and not v.startswith("https://"):
                    out.append(f"{a} of <{tag}> is not an https address")
            elif BAD_TEXT.search(compact):
                out.append(f"attribute {a!r} on <{tag}> holds script")
    if profile == "strict":
        if not (markup.startswith(SHELL[0]) and markup.endswith(SHELL[1])):
            out.append("the HTML is not in the document shell <html><head></head><body>...</body></html>")
        else:
            body = markup[len(SHELL[0]): len(markup) - len(SHELL[1])]
            if _clean(body, profile) != body:
                out.append("the sanitiser (nh3) would change this HTML")
    else:
        m = BODY.search(markup)
        body = m.group(1) if m else markup
        lost = Counter(t for t, _ in _tags(body)) - Counter(t for t, _ in _tags(_clean(body, profile)))
        if lost:
            out.append(f"the sanitiser (nh3) removes {', '.join(f'<{t}>' for t in sorted(lost))}")
    return list(dict.fromkeys(out))


def g10_html(form: dict, profile: str, routed: dict[str, list[Finding]]) -> CheckResult:
    r = CheckResult("G10", "html", findings=list(routed.get("G10", [])))
    title = form.get("title")
    if isinstance(title, str) and len(title) > TITLE_MAX and not r.findings:
        r.findings.append(Finding("/title", f"title has {len(title)} characters, at most {TITLE_MAX}"))
    judged = 0
    for path, key, value in strings(form):
        if key in HTML_KEYS:
            judged += 1
            r.findings += [Finding(path, p) for p in html_problems(value, profile)]
    r.detail["html_strings"] = judged
    return r
