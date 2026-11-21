"""D8: a field that states PESEL, NIP, REGON, a postal code, an e-mail, an ePUAP box, an e-Delivery address or the
number of an identity card names the partner's validator; nothing else does; `VALIDATORS=off` gives empty lists.

One test per validator on synthetic briefs (audit rule 10), the standard sections, the lexicon rows that type the
concept, one synthetic paper through the whole pipeline, and the cases where no validator may be written.

No identifier value appears here: the composer writes the *name* of a validator, the partner's system checks the
value. A test that ever needs a value builds it from a stem and a check digit computed in the test (conftest).
"""
from __future__ import annotations

import io
from typing import Any, get_args

import pytest

from app import lexicon
from app.compose import ComposeOptions, compose
from app.compose import validators as rule
from app.model.brief import Brief
from app.model.form import Validator

QUOTE = [{"page": 1, "quote": "tekst z papieru"}]
# validator -> (concept of the brief, labels of a paper that state it)
STATED = {
    "PESEL": ("pesel", ["PESEL", "Numer PESEL", "Nr PESEL dziecka"]),
    "NIP": ("nip", ["NIP", "Numer NIP płatnika"]),
    "REGON": ("regon", ["REGON", "Numer REGON"]),
    "ZIP_CODE": ("zip_code", ["Kod pocztowy"]),
    "EMAIL": ("email", ["Adres e-mail", "E-mail", "Adres poczty elektronicznej", "Email"]),
    "EPUAP": ("epuap", ["Skrzynka ePUAP - adres skrzynki", "Adres skrytki ePUAP"]),
    "ADE": ("ade", ["Adres do doręczeń elektronicznych", "e-Doręczenia - adres skrzynki", "Adres ADE", "Adres do e-Doreczen"]),
    "SERIAL_NUMBER_ID_CARD": ("id_card", ["Seria i numer dowodu osobistego", "Nr dowodu osobistego", "Dowód osobisty: seria i numer"]),
}


def _brief(fields: list[dict[str, Any]], **over: Any) -> Brief:
    base: dict[str, Any] = {
        "input": {"sha256": "a" * 64, "format": "pdf"},
        "title": {"status": "stated", "value": "Wniosek o wydanie zaświadczenia", "evidence": QUOTE},
        "addressee": {"status": "stated", "kind": "office", "name": "Urząd Gminy Przykładowo", "evidence": QUOTE},
        "applicants": {"status": "stated", "self": True, "evidence": QUOTE},
        "matter": [{"title": "Dane dziecka", "role": "matter/dane_dziecka", "fields": fields}],
        "declarations": {"consents": [], "clause": {"status": "not_found"}},
        "fee": {"status": "not_found"},
        "legal_basis": {"status": "not_found"},
    }
    base.update(over)
    return Brief.model_validate(base)


def _field(n: int, label: str, **more: Any) -> dict[str, Any]:
    return {"key": f"pole_{n}", "label": label, "type": "TEXT_FIELD", **more}


def _matter(brief: Brief, options: ComposeOptions | None = None) -> tuple[list[tuple[str, list[str]]], list[tuple[str, str]]]:
    """([(title, validation)] of the paper's fields in order, [(code, detail)] of the remarks)."""
    r = compose(brief, options)
    paper = [(f.title, list(f.validation)) for f in r.form.iter_fields() if r.origins[f.id] == "paper" and f.type != "SECTION"]
    return paper, [(x.code, x.detail) for x in r.remarks]


# -- one test per validator -----------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", STATED)
def test_a_field_whose_label_or_concept_states_the_value_names_its_validator(name: str) -> None:
    concept, labels = STATED[name]
    by_label, _ = _matter(_brief([_field(n, label) for n, label in enumerate(labels)]))
    assert by_label == [(label, [name]) for label in labels]                       # the label alone is enough
    by_concept, _ = _matter(_brief([_field(0, "Numer", concept=concept, required=True, required_basis="paper")]))
    assert by_concept == [("Numer", ["REQUIRED", name])]                           # so is the concept; REQUIRED comes first
    off, _ = _matter(_brief([_field(n, label, concept=concept) for n, label in enumerate(labels)]), ComposeOptions(validators=False))
    assert off == [(label, []) for label in labels]                                # D8: the switch gives the exports' empty lists


def test_required_is_written_for_a_required_field_and_for_no_other() -> None:
    fields = [_field(0, "Cel wydania zaświadczenia", required=True, required_basis="paper"), _field(1, "Uwagi"),
              {"key": "plec", "label": "Płeć", "type": "RADIO", "options": ["Kobieta", "Mężczyzna"], "required": True, "required_basis": "inferred"}]
    assert _matter(_brief(fields))[0] == [("Cel wydania zaświadczenia", ["REQUIRED"]), ("Uwagi", []), ("Płeć", ["REQUIRED"])]
    assert all(v == [] for _, v in _matter(_brief(fields), ComposeOptions(validators=False))[0])


def test_the_table_is_the_partners_list_and_nothing_else() -> None:
    assert set(rule.PARTNER) == set(get_args(Validator)) and len(rule.PARTNER) == 9
    assert set(rule.CONCEPT_VALIDATORS.values()) == set(rule.PARTNER) - {"REQUIRED"} == set(STATED)
    everything = [_field(n, label, required=True, required_basis="paper") for n, label in enumerate(x for _, ls in STATED.values() for x in ls)]
    r = compose(_brief(everything, applicants={"status": "stated", "self": True, "other_person": True, "entity": True, "evidence": QUOTE},
                       applicant_extras=[{"concept": "pesel", "party": "self"}, {"concept": "regon", "party": "entity"}]))
    used = {v for f in r.form.iter_fields() for v in f.validation}
    assert used == set(rule.PARTNER)                                               # all nine can be written, none outside the list


# -- the standard sections --------------------------------------------------------------------------------------------

FOREIGN_CODES = {"kod_pocztowy_zagranica", "kod_pocztowy_siedziba_zagranica", "kod_pocztowy_inna_osoba_zagranica"}


def _full() -> Brief:
    extras = [{"concept": "pesel", "party": "self"}, {"concept": "pesel", "party": "other_person"},
              {"concept": "regon", "party": "entity"}, {"concept": "krs", "party": "entity"}]
    return _brief([_field(0, "Cel")], applicant_extras=extras,
                  applicants={"status": "stated", "self": True, "other_person": True, "entity": True, "evidence": QUOTE})


def test_every_standard_field_that_states_a_value_names_its_validator() -> None:
    r = compose(_full())
    standard = {f.techName: f for f in r.form.iter_fields() if r.origins[f.id] == "standard" and f.type == "TEXT_FIELD"}
    got = {name: [v for v in f.validation if v != "REQUIRED"] for name, f in standard.items()}
    want = {name: [v] if (v := rule.identifier("TEXT_FIELD", None, f.title)[0]) and name not in FOREIGN_CODES else []
            for name, f in standard.items()}
    assert got == want
    # the finding of the audit (sets 03 and 08): the PESEL of "Twoje dane", read-only from the register
    assert got["numer_pesel"] == ["PESEL"] and standard["numer_pesel"].readOnly and standard["numer_pesel"].defaultValue == "PESEL.pesel"
    assert got["numer_pesel_inna_osoba"] == ["PESEL"] and got["nip"] == ["NIP"] and got["regon"] == ["REGON"]
    assert got["adres_e_mail"] == ["EMAIL"] and got["numer_krs"] == [] and got["numer_telefonu"] == []
    assert [got[n] for n in ("kod_pocztowy", "kod_pocztowy_siedziba", "kod_pocztowy_inna_osoba")] == [["ZIP_CODE"]] * 3
    assert all(got[n] == [] for n in FOREIGN_CODES)                                # a Polish code rule would refuse a foreign code


def test_validators_off_empties_the_standard_sections_too() -> None:
    assert all(f.validation == [] for f in compose(_full(), ComposeOptions(validators=False)).form.iter_fields())


def test_the_service_switch_reaches_the_composer() -> None:
    from app.config import Settings, compose_options

    assert compose_options(Settings.from_env({"AUTH_MODE": "off"})).validators is True
    assert compose_options(Settings.from_env({"AUTH_MODE": "off", "VALIDATORS": "off"})).validators is False


# -- where no validator may be written --------------------------------------------------------------------------------

TWO_KINDS = ["NIP / PESEL", "PESEL lub data urodzenia", "Telefon, e-mail", "Kod pocztowy, miejscowość", "Kod pocztowy i poczta",
             "Seria i numer dowodu osobistego lub paszportu", "Adres skrytki ePUAP lub adres do doręczeń elektronicznych",
             "NIP, REGON", "Numer rachunku bankowego i NIP"]
NO_SUCH_VALUE = ["Adres do doręczeń", "Adres do korespondencji", "Organ wydający dowód osobisty", "Imię i nazwisko",
                 "Numer telefonu", "Numer KRS", "Poczta", "Nazwa banku"]


def test_a_label_that_names_two_kinds_of_value_gets_none_and_a_remark() -> None:
    got, remarks = _matter(_brief([_field(n, label, required=True, required_basis="paper") for n, label in enumerate(TWO_KINDS)]))
    assert got == [(label, ["REQUIRED"]) for label in TWO_KINDS]
    low = [d for code, d in remarks if code == "LOW_CONFIDENCE"]
    assert len(low) == len(TWO_KINDS) and all(f"field pole_{n}:" in d and "more than one kind" in d for n, d in enumerate(low))
    # the concept of the brief does not overrule the label: the understanding step takes the first pattern that matches
    got, remarks = _matter(_brief([_field(0, "NIP / PESEL", concept="pesel")]))
    assert got == [("NIP / PESEL", [])] and [c for c, _ in remarks if c == "LOW_CONFIDENCE"] == ["LOW_CONFIDENCE"]


def test_a_label_that_states_no_such_value_gets_none_and_no_remark() -> None:
    got, remarks = _matter(_brief([_field(n, label) for n, label in enumerate(NO_SUCH_VALUE)]))
    assert got == [(label, []) for label in NO_SUCH_VALUE]
    assert "LOW_CONFIDENCE" not in {c for c, _ in remarks}


def test_only_a_typed_text_field_takes_a_validator_of_a_value() -> None:
    fields = [{"key": "brak_pesel", "label": "Nie posiadam numeru PESEL", "type": "CHECKBOX"},
              {"key": "data", "label": "Data wydania dowodu osobistego", "type": "DATEPICKER", "concept": "date"},
              {"key": "skan", "label": "Skan dowodu osobistego: seria i numer", "type": "FILE_UPLOADER"},
              {"key": "kontakt", "label": "Preferowany kontakt: e-mail", "type": "RADIO", "options": ["Tak", "Nie"]},
              {"key": "opis", "label": "Opis: NIP kontrahentów", "type": "TEXTAREA", "concept": "nip"}]
    got, remarks = _matter(_brief(fields))
    assert [v for _, v in got] == [[]] * 5 and "LOW_CONFIDENCE" not in {c for c, _ in remarks}


# -- the lexicon rows that type the concept (the understanding step takes the first row that matches) -------------------

def _typed(label: str) -> tuple[str | None, str | None]:
    low = label.casefold()
    row = next((row for rx, row in lexicon.compiled("concepts") if rx.search(low)), None)
    return (row["type"], row.get("concept")) if row else (None, None)


@pytest.mark.parametrize("name", STATED)
def test_the_lexicon_types_every_such_label_as_a_text_field_with_the_concept(name: str) -> None:
    concept, labels = STATED[name]
    assert [_typed(label) for label in labels] == [("TEXT_FIELD", concept)] * len(labels)


def test_the_new_lexicon_rows_do_not_take_dates_or_postal_addresses() -> None:
    assert _typed("Data wydania dowodu osobistego") == ("DATEPICKER", "date")
    assert _typed("Organ wydający dowód osobisty") == (None, None)
    assert _typed("Adres do doręczeń") == (None, None)                              # a postal address, not e-Doręczenia
    assert _typed("Adres do korespondencji") == (None, None)


# -- one synthetic paper through the whole service pipeline -------------------------------------------------------------

def _paper() -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, invariant=1)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(120, 780, "WNIOSEK O WYDANIE KARTY MIESZKANCA")
    c.setFont("Helvetica", 11)
    y = 720
    for label in ("Cel wydania karty", "Skrzynka ePUAP", "Adres do e-Doreczen", "Seria i numer dowodu osobistego", "PESEL"):
        c.drawString(56, y, label + " ")
        c.drawString(56 + c.stringWidth(label + " ", "Helvetica", 11), y, "." * 60)
        y -= 28
    c.save()
    return buf.getvalue()


@pytest.mark.parametrize("switch", ["on", "off"])
def test_a_synthetic_paper_gets_the_validators_through_the_pipeline(switch: str) -> None:
    from app import pipeline
    from app.config import Settings
    from tools import coi_lint

    r = pipeline.run(_paper(), "a.pdf", Settings.from_env({"AUTH_MODE": "off", "VALIDATORS": switch}))
    assert [m for k, m in coi_lint.check(r.form, "strict") if k == "ERROR"] == []
    fields = [c["field"] for t in r.form["tabs"] for q in t["questions"] for c in q["field"]["repeatingSectionGrid"]]
    named = {f["title"]: [v for v in f["validation"] if v != "REQUIRED"] for f in fields}
    want = {"Skrzynka ePUAP": ["EPUAP"], "Adres do e-Doreczen": ["ADE"], "Seria i numer dowodu osobistego": ["SERIAL_NUMBER_ID_CARD"],
            "PESEL": ["PESEL"], "Kod pocztowy": ["ZIP_CODE"], "Adres e-mail": ["EMAIL"], "Cel wydania karty": []}
    if switch == "off":
        assert all(f["validation"] == [] for f in fields) and set(want) <= set(named)
    else:
        assert {title: named.get(title) for title in want} == want
