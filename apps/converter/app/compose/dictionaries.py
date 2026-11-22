"""Dictionaries and the fields of the paper (task card points I and II; partner's "Słowniki").

`proposals(brief, ids)`: point II, "Zaproponowanie nowego słownika". A closed list of options printed on the paper
that looks like reference data is proposed as a NEW dictionary: the same list on two or more choice fields (three
options at least), or one list of six or more short options. The name comes from the group's own label, the entries
are the options exactly as printed, `fields` are the form ids that would take it, `evidence` the quotes. A proposal
never enters the form: gate G9 admits only the partner's dictionary names there (D9), so it lives in the sidecar,
`meta.proposals.dictionaries`, in the contract's own slot (`ProposedDictionary`).

`sidecar_extras(brief, brief_keys)`: what this module adds to the sidecar's `meta`; empty for a form without such a
list, so the sidecar of that form is written byte for byte as before. The rule reads the brief only: nothing in it
names a form, an office or a set.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.model.brief import Brief, BriefField
from app.model.common import Evidence
from app.model.meta import Proposals, ProposedDictionary

from .library import KRAJE, TERYT_4G

CHOICE = ("RADIO", "CHECKBOX", "SELECT")
MIN_SHARED = 3          # options of a list that two or more fields share
MIN_SINGLE = 6          # options of one list that stands alone
SHORT_WORDS, SHORT_CHARS = 6, 60   # a "short" option: a name of a thing, not a sentence
NAME_CHARS = 60
_WORD = re.compile(r"[^\W\d_]{3,}")                    # a word of three letters or more
_YES_NO = frozenset({"tak", "nie", "nie dotyczy", "nie wiem"})
_NUMBERING = re.compile(r"^\s*(?:\d+(?:\.\d+)*|[IVXLC]+|[a-z])[.)]\s+", re.IGNORECASE)
_BRACKETS = re.compile(r"\s*[(\[][^)\]]*[)\]]")


def _norm(text: str) -> str:
    return " ".join(text.casefold().split())


def _short(option: str) -> bool:
    return len(option) <= SHORT_CHARS and len(option.split()) <= SHORT_WORDS


def dictionary_name(label: str) -> str:
    """The group's own label without its numbering, hints in brackets and closing colon; 60 characters at most."""
    name = _BRACKETS.sub("", _NUMBERING.sub("", label)).strip(" \t:;*.-–")
    name = " ".join(name.split())
    if len(name) > NAME_CHARS:
        name = name[:NAME_CHARS].rsplit(" ", 1)[0]
    return (name[:1].upper() + name[1:]) if name else "Słownik"


def _groups(brief: Brief) -> list[list[BriefField]]:
    """Choice fields with readable options, grouped by their list of options (case and spaces aside), in paper order."""
    groups: dict[tuple[str, ...], list[BriefField]] = {}
    for m in brief.matter:
        for f in m.fields:
            if f.type in CHOICE and f.options and all(_WORD.search(o) for o in f.options):
                groups.setdefault(tuple(_norm(o) for o in f.options), []).append(f)
    return list(groups.values())


def _is_reference_data(fields: list[BriefField]) -> str | None:
    """Why the list is proposed (Polish, for the sidecar), or None."""
    options = fields[0].options
    if {_norm(o) for o in options} <= _YES_NO:
        return None
    n = len(options)
    if len(fields) >= 2 and n >= MIN_SHARED:
        return f"Ta sama zamknięta lista {n} pozycji występuje w {len(fields)} polach formularza."
    if n >= MIN_SINGLE and all(_short(o) for o in options):
        return f"Zamknięta lista {n} krótkich pozycji wydrukowana na formularzu (dane referencyjne)."
    return None


def proposals(brief: Brief, ids: dict[str, str]) -> list[ProposedDictionary]:
    """`ids`: brief key -> form id (the inverse of `ComposeResult.brief_keys`)."""
    out: list[ProposedDictionary] = []
    seen: set[str] = set()
    for fields in _groups(brief):
        why = _is_reference_data(fields)
        if why is None:
            continue
        name = base = dictionary_name(fields[0].label)
        n = 2
        while name in seen:
            name, n = f"{base} ({n})", n + 1
        seen.add(name)
        fids = [ids[f.key] for f in fields if f.key in ids]
        evidence = [Evidence(page=e.page, quote=e.quote) for f in fields for e in f.evidence[:1] if e.quote]
        pages = sorted({e.page for f in fields for e in f.evidence if e.page is not None})
        labels = ", ".join(f"„{f.label.strip()}”" for f in fields[:3])
        use = (f"Pole {labels} brałoby pozycje z tego słownika zamiast z listy opcji wpisanej w formularz; "
               f"struktura: jedna pozycja = nazwa wyświetlana (jak na papierze) i kod techniczny.")
        out.append(ProposedDictionary(name=name, entries=list(fields[0].options), pages=pages,
                                      field=fids[0] if fids else None, fields=fids, why=why, use=use, evidence=evidence))
    return out


# -- point I on the fields of the paper (A8 DX-2) ------------------------------------------------------------------
# The partner's dictionaries ("Słowniki"): Kraje for a country; Województwo, Powiat, Gmina, Miejscowość, which the
# exports carry as one multi-level TERYT dictionary (the library's TERYT_4G_DOWODOWY); Numery kierunkowe for a phone,
# whose technical name no export shows, so it is named in the sidecar only (gate G9 admits known names, D9). A link
# needs the whole label: a country word first and three words at most, a territorial word alone, no word of a
# place-and-date line. A dictionary is bound only to a drop-down list (SELECT), so a linked text field becomes one.
PREFIXES = "Numery kierunkowe"
_COUNTRY = frozenset({"kraj", "państwo", "obywatelstwo"})
_TERRITORY = frozenset({"województwo", "powiat", "gmina"})
_LOCALITY = "miejscowość"
_PHONE = frozenset({"telefon", "telefonu", "tel"})
_NEVER = frozenset({"data", "dnia", "podpis", "nazwa", "kod", "numer", "nr", "ulica", "adres"})
_TOKENS = re.compile(r"[^\W\d_]+")


@dataclass(frozen=True)
class Link:
    dictionary: str
    written: bool                  # False: named in the sidecar only, the form is not changed
    multi_level: bool | None
    why: str


def link_of(f: BriefField) -> Link | None:
    """The partner's dictionary a field of the paper takes by its label, or None (a wrong link is worse than none)."""
    words = _TOKENS.findall(f.label.casefold())
    if not words or f.options or f.type != "TEXT_FIELD":
        return None
    label = f.label.strip()
    if f.concept is None and not (_NEVER & set(words)):
        if words[0] in _COUNTRY and len(words) <= 3:
            return Link(KRAJE, True, False, f"Etykieta „{label}” wskazuje kraj: słownik partnera {KRAJE} (lista "
                                            "rozwijana) zamiast wpisywania nazwy państwa tekstem.")
        if words == [_LOCALITY]:
            # The partner's reference export 01 keeps the matter's "Miejscowość" a TEXT_FIELD without a dictionary:
            # the form follows the partner, the sidecar names the dictionary that would fit.
            return Link(TERYT_4G, False, None, f"Etykieta „{label}”: pasuje słownik partnera Miejscowość ({TERYT_4G}). "
                                               "Nie zapisano go w formularzu: wzorcowy eksport partnera zostawia "
                                               "„Miejscowość” w sprawie jako pole tekstowe.")
        if len(words) == 1 and words[0] in _TERRITORY:
            return Link(TERYT_4G, True, True, f"Etykieta „{label}” to jednostka podziału terytorialnego: słownik "
                                              f"{TERYT_4G}, ten sam co w adresach sekcji standardowych partnera.")
    if len(words) <= 6 and (f.concept == "phone" or _PHONE & set(words)):
        return Link(PREFIXES, False, None, f"Pole telefonu „{label}”: pasuje słownik partnera {PREFIXES} (wybór prefiksu "
                                           "kraju). Nie zapisano go w formularzu: eksporty partnera nie pokazują jego "
                                           "nazwy technicznej (bramka G9).")
    return None


def links(brief: Brief, ids: dict[str, str]) -> list[dict]:
    """One sidecar row per linked field of the paper: form id, label, dictionary, written or not, and why."""
    out: list[dict] = []
    for m in brief.matter:
        for f in m.fields:
            link = link_of(f)
            if link is not None and f.key in ids:
                out.append({"field": ids[f.key], "label": f.label.strip(), "dictionary": link.dictionary,
                            "written": link.written, "why": link.why})
    return out


def sidecar_extras(brief: Brief, brief_keys: dict[str, str]) -> dict:
    """The keys this module adds to the sidecar's `meta` (none when there is nothing to say)."""
    ids = {key: fid for fid, key in brief_keys.items()}
    extras: dict = {}
    found = proposals(brief, ids)
    if found:
        extras["proposals"] = Proposals(dictionaries=found).model_dump(mode="json", exclude_none=True, exclude_defaults=True)
    linked = links(brief, ids)
    if linked:
        extras["dictionary_links"] = linked
    return extras
