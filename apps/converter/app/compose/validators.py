"""Validators of the partner's list (D8): which one a field of the paper gets, and why one is withheld.

A field gets the validator of the kind of value it asks for. The kind comes from the concept of the brief and from
the label, read with the rows of the lexicon `concepts`: one table of patterns for the understanding step and for
the composer. The rule is narrow on purpose, because a validator on the wrong field refuses honest answers:

- only a typed text field takes one (never a date, a choice, an upload, a long text);
- a label that names two kinds of value ("NIP / PESEL", "telefon, e-mail", "kod pocztowy i miejscowość", "seria
  i numer dowodu osobistego lub paszportu") takes none: the validator of one kind would refuse the other. The
  composer says so in a remark; it never picks one.
"""
from __future__ import annotations

import re

from app import lexicon

PARTNER = ("REQUIRED", "EMAIL", "PESEL", "NIP", "REGON", "ZIP_CODE", "EPUAP", "ADE", "SERIAL_NUMBER_ID_CARD")
# Concept of a brief field -> the partner's validator.
CONCEPT_VALIDATORS = {"pesel": "PESEL", "nip": "NIP", "regon": "REGON", "zip_code": "ZIP_CODE", "email": "EMAIL",
                      "epuap": "EPUAP", "ade": "ADE", "id_card": "SERIAL_NUMBER_ID_CARD"}
TYPES = ("TEXT_FIELD",)
# Kinds of value that exclude each other inside one field: the eight above and the other numbers and contacts the
# lexicon knows. Two of them in one label: either of them, or both, is asked.
_KINDS = (*CONCEPT_VALIDATORS, "phone", "nrb", "krs", "date")
# Words of a second value the lexicon has no concept for: another document beside the identity card, the town
# beside the postal code.
_SECOND_VALUE = re.compile(r"paszport|dokument\w* (to[żz]samo[śs]ci|podr[óo][żz]y)|praw\w* jazdy|miejscowo[śs][ćc]|\bpoczta\b", re.IGNORECASE)


def kinds(label: str) -> tuple[str, ...]:
    """Kinds of value the label names, in the order of the lexicon, each once."""
    low = label.casefold()
    out: list[str] = []
    for rx, row in lexicon.compiled("concepts"):
        kind = row.get("concept")
        if kind in _KINDS and kind not in out and rx.search(low):
            out.append(kind)
    return tuple(out)


def identifier(type_: str, concept: str | None, label: str) -> tuple[str | None, str | None]:
    """(validator, None), (None, why none is written), or (None, None) when the field states no such value."""
    found = list(kinds(label))
    if concept in _KINDS and concept not in found:
        found.insert(0, concept)       # the understanding step may have reworded the label
    wanted = [k for k in found if k in CONCEPT_VALIDATORS]
    if not wanted:
        return None, None
    if type_ not in TYPES:
        return None, None              # the type already says it is not a typed number or address
    second = _SECOND_VALUE.search(label)
    if len(found) > 1 or second:
        named = ", ".join([*found, *([second.group(0).casefold()] if second else [])])
        return None, f"the label names more than one kind of value ({named}): the validator of one would refuse the other"
    return CONCEPT_VALIDATORS[wanted[0]], None
