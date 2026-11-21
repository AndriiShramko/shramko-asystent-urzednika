"""Composer against the partner's two reference exports. The exports are local only: every test here is `sets`.

The library is compared section by section, ignoring ids and grid; HTML is compared by its visible text (D11: the
markup is ours) and conditions without white space. Every tolerated difference is named below with its reason,
and the test fails when one of them disappears as well as when a new one appears.
"""
from __future__ import annotations

import json

import pytest
from compose_helpers import REFERENCE, components, load_brief, norm_field, section_diff, sections

from app.compose import EXPORT_1, EXPORT_5, ComposeOptions, compose

pytestmark = pytest.mark.sets

PRESET = {"reference-01-numer-porzadkowy": EXPORT_1, "reference-05-nadplata-podatku": EXPORT_5}
OTHER_ADDRESS = "adres_zamieszkania_osoby_ktorej_jestes_pelnomocnikiem"
# (section, component or "", key): the exports set these on some addresses only; the library writes them one way.
SELECT_FLAGS_1 = {("adres_zamieszkania", "kraj", "multiLevelTree"), ("adres_zamieszkania", "kraj", "searchEnabled"),
                  ("adres_siedziby", "kraj_siedziba", "searchEnabled"), ("adres_siedziby", "wojewodztwo_siedziba", "multiLevelTree"),
                  ("adres_siedziby", "wojewodztwo_siedziba", "searchEnabled"), (OTHER_ADDRESS, "kraj_inna_osoba", "searchEnabled"),
                  (OTHER_ADDRESS, "wojewodztwo_inna_osoba", "multiLevelTree"), (OTHER_ADDRESS, "wojewodztwo_inna_osoba", "searchEnabled")}
SELECT_FLAGS_5 = {(OTHER_ADDRESS, "wojewodztwo_inna_osoba", "multiLevelTree"), (OTHER_ADDRESS, "wojewodztwo_inna_osoba", "searchEnabled")}
BOTH = {("adres_siedziby", "ulica_siedziba", "defaultValue"),            # the exports write defaultValue "" on this one field
        ("oplata_skarbowa_pelnomocnictwo_2", "", "title")}               # "pełnomonictwo": a typing slip we do not copy
TOLERATED = {
    "reference-01-numer-porzadkowy": SELECT_FLAGS_1 | BOTH,
    # export 5 leaves the option "Reprezentant" without a techName; ours has one
    "reference-05-nadplata-podatku": SELECT_FLAGS_5 | BOTH | {("podmiot_wniosku", "wybierz_jako_kto_wnioskujesz", "options")},
}
# Page titles of the matter that differ: the brief has no page title, the page takes the title of its first section.
PAGE_TITLES = {"reference-01-numer-porzadkowy": [("Informacje o budynku", "Lokalizacja budynku")], "reference-05-nadplata-podatku": []}


def _pair(set_id: str) -> tuple[dict, dict]:
    from eval.golden import expected_forms

    export = json.loads(expected_forms()[set_id].read_text(encoding="utf-8"))
    options = ComposeOptions(validators=False, statutory_representative=False, standard=PRESET[set_id])
    return export, compose(load_brief(REFERENCE[set_id]), options).form.to_partner()


def _standard_pages(doc: dict) -> set[str]:
    return {doc["tabs"][0]["title"], doc["tabs"][-2]["title"], doc["tabs"][-1]["title"]}


def _matter(doc: dict) -> list[tuple[str, str]]:
    return [(c["type"], c["title"]) for t in doc["tabs"][1:-2] for q in t["questions"] for c in components(q["field"])]


@pytest.mark.parametrize("set_id", REFERENCE)
def test_every_standard_section_of_the_export_is_rebuilt(set_id: str, capsys: pytest.CaptureFixture) -> None:
    export, ours = _pair(set_id)
    theirs, mine = sections(export, _standard_pages(export)), sections(ours, _standard_pages(ours))
    assert set(theirs) == set(mine)                                      # the same standard sections by techName
    assert [t for t in theirs] == [t for t in mine]                      # in the same order
    found = set().union(*(section_diff(theirs[name], mine[name]) for name in theirs))
    assert found == TOLERATED[set_id]
    parts = sum(len(components(s)) for s in theirs.values())
    with capsys.disabled():
        print(f"\n{set_id}: {len(theirs)} standard sections and {parts} components rebuilt, {len(found)} named tolerances")


@pytest.mark.parametrize("set_id", REFERENCE)
def test_same_pages_and_the_fields_of_the_matter(set_id: str, capsys: pytest.CaptureFixture) -> None:
    export, ours = _pair(set_id)
    assert [t["type"] for t in export["tabs"]] == [t["type"] for t in ours["tabs"]]
    titles = [(a["title"], b["title"]) for a, b in zip(export["tabs"], ours["tabs"], strict=True)]
    assert [pair for pair in titles if pair[0] != pair[1]] == PAGE_TITLES[set_id]
    assert len(export["flow"]["links"]) == len(ours["flow"]["links"]) == len(ours["tabs"]) - 1
    theirs, mine = _matter(export), _matter(ours)
    matched = [x for x in theirs if x in mine]
    missing, extra = [x for x in theirs if x not in mine], [x for x in mine if x not in theirs]
    a, b = sections(export), sections(ours)
    renamed = sorted((x["techName"], y["techName"]) for name in a.keys() & b.keys() if name not in sections(export, _standard_pages(export))
                     for x, y in zip(components(a[name]), components(b[name]), strict=False) if x["techName"] != y["techName"])
    with capsys.disabled():
        print(f"\n{set_id}: pages {[t['title'] for t in ours['tabs']]}")
        print(f"  matter components matched {len(matched)}: {[t for _, t in matched]}")
        print(f"  missing {missing}; extra {extra}; same field, other techName (export, ours): {renamed}")
    assert (missing, extra) == ([], [])
    # Conditions of the matter: the same text, white space aside (set 5 shows two fields by the chosen option).
    conditions = lambda doc: sorted(norm_field(c)["states"][0][1] for t in doc["tabs"][1:-2] for q in t["questions"]  # noqa: E731
                                    for c in components(q["field"]) if c.get("states"))
    assert conditions(export) == conditions(ours)


@pytest.mark.parametrize("set_id", REFERENCE)
def test_default_options_keep_the_exports_sections_and_list_what_is_ours(set_id: str, capsys: pytest.CaptureFixture) -> None:
    from eval.golden import expected_forms

    export = json.loads(expected_forms()[set_id].read_text(encoding="utf-8"))
    ours = compose(load_brief(REFERENCE[set_id])).form.to_partner()      # defaults: validators on, D16 on, our wording choices
    names = lambda doc: {c["techName"] for s in sections(doc).values() for c in [s, *components(s)]}  # noqa: E731
    missing, extra = sorted(names(export) - names(ours)), sorted(names(ours) - names(export))
    with capsys.disabled():
        print(f"\n{set_id} with default options: matched {len(names(export) & names(ours))}, missing {missing}, extra {extra}")
    assert {"wybierz_jako_kto_wnioskujesz_inna_osoba", "potwierdzenie_ze_jestes_przedstawicielem_ustawowym"} <= set(extra)   # D16
    assert len(missing) <= 9                                             # wording variants of export 1 and the matter's techNames
