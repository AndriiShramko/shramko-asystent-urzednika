"""A8 DX-2: task card point I on the fields of the paper itself. A field whose whole label names a country or a unit
of the territorial division takes the partner's dictionary (Kraje; the TERYT dictionary the library uses) as a SELECT;
a phone field gets the partner's "Numery kierunkowe" in the sidecar only (its export name is unknown, gate G9, D9).
A wrong link is worse than none: whole words only, and the reason goes into the sidecar. Synthetic briefs only."""
from __future__ import annotations

import json

from compose_helpers import brief

from app import gate
from app.compose import compose
from app.compose.dictionaries import link_of, sidecar_extras
from app.gate import KNOWN_DICTIONARIES
from app.model.brief import BriefField


def _form(*fields: dict) -> tuple[dict, dict, dict]:
    b = brief(matter=[{"title": "Adres nieruchomości", "role": "matter/adres", "fields": list(fields)}])
    c = compose(b)
    form = json.loads(c.form.to_json_bytes())
    by_title = {}
    for t in form["tabs"]:
        for q in t["questions"]:
            for cell in q["field"]["repeatingSectionGrid"]:
                if c.origins.get(cell["field"]["id"]) == "paper":
                    by_title[cell["field"]["title"]] = cell["field"]
    return form, by_title, sidecar_extras(b, c.brief_keys)


def _f(key: str, label: str, type_: str = "TEXT_FIELD", **kw) -> dict:
    return {"key": key, "label": label, "type": type_, **kw}


def test_country_labels_take_kraje_as_a_select() -> None:
    form, f, extras = _form(_f("kraj_urodzenia", "Kraj urodzenia"), _f("obywatelstwo", "Obywatelstwo:"))
    for title in ("Kraj urodzenia", "Obywatelstwo:"):
        assert f[title]["type"] == "SELECT" and f[title]["dictionaryName"] == "Kraje" and not f[title]["options"]
    assert not [c for c in gate.check(form).failed if c.id == "G9"]
    links = {x["dictionary"] for x in extras["dictionary_links"]}
    assert links == {"Kraje"} and all(x["written"] and x["why"] for x in extras["dictionary_links"])


def test_territorial_labels_take_the_teryt_dictionary_of_the_library() -> None:
    _, f, extras = _form(_f("wojewodztwo", "Województwo"), _f("powiat", "Powiat"), _f("gmina", "Gmina"), _f("miejscowosc", "Miejscowość"))
    for title in ("Województwo", "Powiat", "Gmina"):
        assert f[title]["type"] == "SELECT" and f[title]["dictionaryName"] == "TERYT_4G_DOWODOWY"
        assert f[title]["multiLevelTree"] is True
    # the partner's reference export 01 keeps the matter's "Miejscowość" a text field: the form follows it, the
    # sidecar names the fitting dictionary
    assert f["Miejscowość"]["type"] == "TEXT_FIELD" and not f["Miejscowość"].get("dictionaryName")
    row = [x for x in extras["dictionary_links"] if x["label"] == "Miejscowość"]
    assert len(row) == 1 and row[0]["written"] is False


def test_no_link_without_a_whole_word_match_or_on_a_printed_list() -> None:
    _, f, extras = _form(_f("miejscowosc_data", "Miejscowość i data"), _f("nazwa_gminy", "Nazwa gminy"),
                         _f("krajowy", "Krajowy numer rejestru"), _f("urodzenia", "Miejscowość urodzenia"),
                         _f("kraj_lista", "Kraj", "RADIO", options=["Polska", "Inny"]),
                         _f("gmina_opis", "Gmina, w której położona jest nieruchomość objęta wnioskiem"))
    assert all(not x.get("dictionaryName") for x in f.values())
    assert f["Miejscowość i data"]["type"] == "TEXT_FIELD" and f["Kraj"]["type"] == "RADIO"
    assert "dictionary_links" not in extras


def test_phone_gets_the_prefix_dictionary_in_the_sidecar_only() -> None:
    _, f, extras = _form(_f("telefon", "Nr tel./fax"), _f("telefon_2", "Telefon", concept="phone"))
    assert f["Telefon"]["type"] == "TEXT_FIELD" and not f["Telefon"].get("dictionaryName")
    notes = extras["dictionary_links"]
    assert [x["dictionary"] for x in notes] == ["Numery kierunkowe", "Numery kierunkowe"]
    assert not any(x["written"] for x in notes)
    assert "Numery kierunkowe" not in KNOWN_DICTIONARIES     # the form never gets a name the gate does not know


def test_every_written_link_is_a_known_partner_dictionary() -> None:
    for label in ("Kraj", "Państwo", "Kraj zamieszkania", "Województwo", "Gmina", "Powiat"):
        link = link_of(BriefField(key="x", label=label, type="TEXT_FIELD"))
        assert link is not None and link.written and link.dictionary in KNOWN_DICTIONARIES, label


def test_a_form_without_such_labels_is_unchanged() -> None:
    b = brief()
    assert "dictionary_links" not in sidecar_extras(b, compose(b).brief_keys)
