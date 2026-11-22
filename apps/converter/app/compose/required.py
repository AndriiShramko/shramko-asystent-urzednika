"""REQUIRED of a field of the paper (D8; coi-json-format section 10 item 2; design 6.4.3 "Required or not").

The brief says for every field whether it is required and on what basis: "paper" (the paper marks it), "substance"
(the request cannot be read without it) or "inferred" (our rule: a blank the paper does not mark optional). The
composer writes REQUIRED from that, with two rules of its own:

1. Our inference yields to the paper. An inferred REQUIRED is not written when the paper's own words make the field
   optional or conditional: an optional word ("nieobowiązkowe", "opcjonalnie", "fakultatywnie") in the label, in the
   hint (the bracket or caption of the field) or in the title of its section; a conditional word ("jeśli", "jeżeli",
   "o ile", "w przypadku") in the hint, or at the start of the label ("Jeżeli tak, podać jakie"). A conditional
   word in the middle of a label decides nothing and changes nothing. What the paper marks required stays required.
2. The policy. "inferred" (the default, the behaviour of design 6.4.3): every other inferred REQUIRED is written
   and the sidecar flags it REQUIRED_INFERRED. "paper" (the reading of coi-json-format): no inferred REQUIRED is
   written at all; the composer says how many in one remark.

The words come from the lexicon `habits` (habits "optional" and "conditional").
"""
from __future__ import annotations

from app import lexicon
from app.model.brief import BriefField

POLICIES = ("inferred", "paper")
OPTIONAL = lexicon.regex("habits", habit="optional")
CONDITIONAL = lexicon.regex("habits", habit="conditional")
REQUIRED_WORD = lexicon.regex("habits", habit="required")

UNSTATED = "unstated"       # the reason of rule 2, counted and reported once


def paper_mark(label: str, hint: str | None, section_title: str) -> str | None:
    """The paper's words that make the field optional or conditional, with the place they stand in; None when none."""
    for place, text in (("hint", hint or ""), ("label", label), ("section title", section_title)):
        m = OPTIONAL.search(text)
        if m:
            return f"{m.group(0).casefold()!r} in the {place}"
    m = CONDITIONAL.search(hint or "")
    if m:
        return f"{m.group(0).casefold()!r} in the hint"
    m = CONDITIONAL.match(label.lstrip(" (/"))
    if m:
        return f"{m.group(0).casefold()!r} at the start of the label"
    return None


def written(f: BriefField, section_title: str, policy: str) -> tuple[bool, str | None]:
    """(REQUIRED is written, why not): the reason is None for a field the brief does not require."""
    if not f.required:
        return False, None
    if f.required_basis != "inferred":
        return True, None
    mark = paper_mark(f.label, f.hint, section_title)
    if mark:
        return False, f"the paper makes the field optional or conditional ({mark})"
    if policy == "paper":
        return False, UNSTATED
    return True, None
