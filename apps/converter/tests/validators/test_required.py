"""REQUIRED of the paper's fields (D8; coi-json-format section 10 item 2; design 6.4.3).

Rule 1: an inferred REQUIRED yields to the paper's own optional or conditional words. Rule 2: the policy
("inferred", the default; "paper": no inferred REQUIRED at all). Synthetic briefs only.
"""
from __future__ import annotations

from typing import Any

import pytest

from app import lexicon
from app.compose import ComposeOptions, compose
from app.compose import required as rule
from app.model.brief import Brief

QUOTE = [{"page": 1, "quote": "tekst z papieru"}]


def _brief(sections: list[dict[str, Any]], **over: Any) -> Brief:
    base: dict[str, Any] = {
        "input": {"sha256": "a" * 64, "format": "pdf"},
        "title": {"status": "stated", "value": "Wniosek o przyznanie stypendium", "evidence": QUOTE},
        "addressee": {"status": "stated", "kind": "office", "name": "Urząd Gminy Przykładowo", "evidence": QUOTE},
        "applicants": {"status": "stated", "self": True, "evidence": QUOTE},
        "matter": sections,
        "declarations": {"consents": [], "clause": {"status": "not_found"}},
        "fee": {"status": "not_found"},
        "legal_basis": {"status": "not_found"},
    }
    base.update(over)
    return Brief.model_validate(base)


def _f(key: str, label: str, basis: str | None = "inferred", **more: Any) -> dict[str, Any]:
    need = {"required": True, "required_basis": basis} if basis else {}
    return {"key": key, "label": label, "type": "TEXT_FIELD", **need, **more}


def _sec(title: str, fields: list[dict[str, Any]], role: str = "matter/dane") -> dict[str, Any]:
    return {"title": title, "role": role, "fields": fields}


def _required(brief: Brief, options: ComposeOptions | None = None) -> tuple[dict[str, bool], list[str]]:
    """({brief key: REQUIRED written}, the details of the REQUIRED_INFERRED remarks of the composer)."""
    r = compose(brief, options)
    by_key = {r.brief_keys[f.id]: "REQUIRED" in f.validation for f in r.form.iter_fields() if f.id in r.brief_keys}
    return by_key, [x.detail for x in r.remarks if x.code == "REQUIRED_INFERRED"]


# -- rule 1: our inference yields to the paper's words ------------------------------------------------------------------

YIELDS = [
    _f("adres", "Adres do korespondencji", hint="jeśli różni się od adresu zameldowania"),
    _f("adres_2", "Adres do korespondencji", hint="jeżeli jest inny niż adres powyżej"),
    _f("pesel_dziecka", "Numer PESEL dziecka", hint="o ile został nadany"),
    _f("zrodlo", "Źródło spłaty", hint="w przypadku wniosku o rozłożenie na raty"),
    _f("telefon", "Telefon kontaktowy", hint="nieobowiązkowo"),
    _f("jakie", "Jeżeli tak, należy wskazać jakie"),
    _f("zrodlo_dochodu", "Jeśli tak, należy wskazać źródło dochodu"),
    _f("inne", "W przypadku zaznaczenia odpowiedzi „inne” podać jakie"),
    _f("uwagi", "Uwagi (opcjonalnie)"),
    _f("fax", "Faks - pole nieobowiązkowe"),
]
STAYS = [
    _f("cel", "Cel wydania zaświadczenia"),
    _f("osoba", "Imię i nazwisko osoby do kontaktu w przypadku awarii"),                   # mid-label: decides nothing
    _f("zgoda", "Imię i nazwisko – wnioskodawca, w przypadku innej osoby zgoda tej osoby"),
    _f("zarzad", "W zarządzie lub użytkowaniu", hint="należy podać jaki oraz dokładne dane"),
    _f("okres", "Okres", hint="od dnia do dnia"),
]


def test_an_inferred_required_yields_to_an_optional_or_conditional_mark_of_the_paper() -> None:
    got, remarks = _required(_brief([_sec("Dane sportowca", YIELDS + STAYS)]))
    assert got == {**{f["key"]: False for f in YIELDS}, **{f["key"]: True for f in STAYS}}
    assert len(remarks) == len(YIELDS) and all(f"field {f['key']}:" in d for f, d in zip(YIELDS, remarks, strict=True))
    assert "'jeśli' in the hint" in remarks[0] and "'o ile' in the hint" in remarks[2] and "'nieobowiązkow' in the hint" in remarks[4]
    assert "'jeżeli' at the start of the label" in remarks[5] and "'opcjonaln' in the label" in remarks[8]


def test_an_optional_word_in_the_title_of_the_section_covers_its_inferred_fields() -> None:
    brief = _brief([_sec("Dane do kontaktu (pola nieobowiązkowe)", [_f("telefon", "Telefon"), _f("email", "Adres e-mail"),
                                                                    _f("faks", "Faks", basis="paper")], "matter/kontakt"),
                    _sec("Dane dziecka w przypadku rodziny wielodzietnej", [_f("imie_dziecka", "Imię dziecka")], "matter/dziecko")])
    got, remarks = _required(brief)
    assert got == {"telefon": False, "email": False, "faks": True, "imie_dziecka": True}   # a conditional word in a title: no rule
    assert len(remarks) == 2 and all("in the section title" in d for d in remarks)
    emails = [f for f in compose(brief).form.iter_fields() if f.title == "Adres e-mail" and f.techName != "adres_e_mail"]
    assert [f.validation for f in emails] == [["EMAIL"]]                                   # optional, and still an e-mail


def test_what_the_paper_marks_required_stays_required_whatever_the_words() -> None:
    fields = [_f("nip", "NIP", basis="paper", hint="jeśli dotyczy"), _f("rodzaj", "Jeśli tak, wybierz rodzaj", basis="substance"),
              {"key": "forma", "label": "Wynajęcie lub użyczenie", "type": "RADIO", "options": ["Wynajęcie", "Użyczenie"],
               "required": True, "required_basis": "paper", "hint": "w przypadku wątpliwości zapytaj"}]
    for policy in rule.POLICIES:
        got, remarks = _required(_brief([_sec("Dane", fields)]), ComposeOptions(required_policy=policy))
        assert got == {"nip": True, "rodzaj": True, "forma": True} and remarks == []


def test_a_field_the_brief_does_not_require_never_gets_required() -> None:
    got, remarks = _required(_brief([_sec("Dane", [_f("uwagi", "Uwagi", basis=None), _f("inne", "Inne", basis=None, hint="jeśli dotyczy")])]))
    assert got == {"uwagi": False, "inne": False} and remarks == []


# -- rule 2: the policy ---------------------------------------------------------------------------------------------------

def _mixed() -> Brief:
    fields = [_f("cel", "Cel wydania zaświadczenia"), _f("okres", "Okres"), _f("nip", "NIP", basis="paper"),
              _f("rodzaj", "Rodzaj wniosku", basis="substance"), _f("adres", "Adres do korespondencji", hint="jeśli jest inny")]
    attachments = [{"label": "Mapa z zaznaczonym terenem", "required": True, "key": "mapa", "evidence": QUOTE},
                   {"label": "Opinia klubu", "required": False, "key": "opinia", "evidence": QUOTE}]
    return _brief([_sec("Dane", fields)], attachments=attachments)


def test_the_default_policy_keeps_every_other_inferred_required() -> None:
    assert ComposeOptions().required_policy == "inferred"
    got, remarks = _required(_mixed())
    assert got == {"cel": True, "okres": True, "nip": True, "rodzaj": True, "adres": False, "mapa": True, "opinia": False}
    assert len(remarks) == 1 and "field adres:" in remarks[0]


def test_the_paper_policy_writes_no_inferred_required_and_says_how_many() -> None:
    got, remarks = _required(_mixed(), ComposeOptions(required_policy="paper"))
    assert got == {"cel": False, "okres": False, "nip": True, "rodzaj": True, "adres": False, "mapa": True, "opinia": False}
    assert len(remarks) == 2 and "field adres:" in remarks[0]
    assert remarks[1].startswith("2 fields are required only by our rule") and "cel, okres" in remarks[1]


def test_an_unknown_policy_is_refused() -> None:
    from app.compose import ComposeError

    with pytest.raises(ComposeError):
        compose(_mixed(), ComposeOptions(required_policy="always"))


def test_validators_off_and_two_runs() -> None:
    off = compose(_mixed(), ComposeOptions(validators=False))
    assert all(f.validation == [] for f in off.form.iter_fields())
    for policy in rule.POLICIES:
        o = ComposeOptions(required_policy=policy)
        assert compose(_mixed(), o).form.to_json_bytes() == compose(_mixed(), o).form.to_json_bytes()
    assert compose(_mixed()).form.to_json_bytes() != compose(_mixed(), ComposeOptions(required_policy="paper")).form.to_json_bytes()


# -- the words --------------------------------------------------------------------------------------------------------------

def test_the_words_come_from_the_lexicon_and_the_understanding_step_reads_the_same_optional_words_as_before() -> None:
    habits = {}
    for row in lexicon.rows("habits"):
        habits.setdefault(row["habit"], []).append(row["pattern"])
    assert habits["optional"] == ["nieobowiązkow|opcjonaln|fakultatywn"]       # app.mean reads this row: not changed here
    assert len(habits["conditional"]) == 1
    for text in ("jeśli dotyczy", "Jeżeli tak", "o ile został nadany", "w przypadku braku", "jesli dotyczy", "JEŻELI"):
        assert rule.CONDITIONAL.search(text), text
    for text in ("przypadkowo", "ile osób", "Jeślin", "w przypadkach"):
        assert not rule.CONDITIONAL.search(text), text


@pytest.mark.parametrize(("label", "hint", "title", "mark"), [
    ("Adres", "jeśli inny", "Dane", "'jeśli' in the hint"),
    ("Adres", None, "Dane", None),
    ("(jeżeli dotyczy) Adres", None, "Dane", "'jeżeli' at the start of the label"),
    ("Adres w przypadku zmiany", None, "Dane w przypadku zmiany", None),
    ("Adres", None, "Dane fakultatywne", "'fakultatywn' in the section title"),
])
def test_paper_mark(label: str, hint: str | None, title: str, mark: str | None) -> None:
    assert rule.paper_mark(label, hint, title) == mark
