"""The gate on synthetic forms: our forms pass, and each check has a fixture that fails exactly that check."""
from __future__ import annotations

import json

import pytest
from gate_helpers import field, fields, matter_field, mutate, reference_form, synthetic_form

from app.gate import NAMES, GateFailed, check, html_problems, load_journeys

SIDECAR_OK = {
    "ledger": {"blanks_found": 1, "became_field": 1, "merged": 0, "covered_by_standard": 0, "left_out": 0,
               "awaiting_decision": 0, "rows": []},   # the FIELD row is filled in by the test with a real id
    "coverage": {"runs_total": 3, "assigned": 2, "unassigned": ["Pole"], "silent_pages": []},
}
PAPER_VALUE = "ul. Przykładowa 12"


@pytest.fixture(scope="module")
def base() -> dict:
    return synthetic_form()


def sidecar_for(form: dict) -> dict:
    s = json.loads(json.dumps(SIDECAR_OK))
    s["ledger"]["rows"] = [{"candidate": "c1", "fate": "FIELD", "field": matter_field(form)["id"]}]
    return s


def failed_ids(form, **kw) -> set[str]:
    return {c.id for c in check(form, **kw).failed}


# -- what passes ------------------------------------------------------------------------------------------------

def test_synthetic_form_passes_all_twelve(base):
    r = check(base, sidecar=sidecar_for(base), fill_values=["Jan Testowy-Przykład"])
    assert [c.id for c in r.checks] == list(NAMES)
    assert {c.status for c in r.checks} == {"passed"}, r.to_dict()
    assert [(j.id, j.status) for j in r.journeys] == [(j["id"], "passed") for j in load_journeys()]


@pytest.mark.parametrize("name", ["brief_reference_01", "brief_reference_05"])
def test_our_reference_forms_pass_strict(name):
    r = check(reference_form(name))
    assert r.passed, [(c.id, c.findings[:2]) for c in r.failed]
    assert {j.status for j in r.journeys} == {"passed"}
    assert r.get("G7").detail["judged"] > 0 and r.get("G6").detail["evaluated"] > 0


def test_without_sidecar_and_values_two_checks_are_not_applicable(base):
    r = check(base)
    assert r.passed
    assert {c.id for c in r.checks if c.status == "not_applicable"} == {"G11", "G12"}
    assert all(c.reason for c in r.checks if c.status == "not_applicable")


# -- twelve negative controls: each fails exactly its own check --------------------------------------------------

def _g1(f):
    f["meta"] = {}


def _g2(f):
    f["tabs"][-1]["type"] = "MAIN"


def _g3(f):
    contact = field(f, "dane_do_kontaktu")["repeatingSectionGrid"]
    contact[-1]["field"]["techName"] = field(f, "twoje_dane")["repeatingSectionGrid"][0]["field"]["techName"]


def _g4(f):
    field(f, "plik_z_potwierdzeniem_przelewu")["id"] = field(f, "oplata_info_1")["id"]


def _g5(f):
    s = field(f, "oplata_info_1")["states"][0]
    s["query"] = s["query"].replace("tabs['Dane' in title]", "tabs['Dan' in title]")


def _g6(f):
    s = field(f, "plik_z_potwierdzeniem_przelewu")["states"][0]
    s["query"] = s["query"].replace('"Tak" in', '"Tak!" in')


def _g7(f):
    s = field(f, "oplata_info_1")["states"][0]
    s["query"] = f"$not({s['query']})"


def _g8(f):
    matter = f["tabs"][1]["questions"][0]["field"]
    matter["states"] = json.loads(json.dumps(field(f, "dane_podmiotu")["states"]))


def _g9(f):
    field(f, "wojewodztwo")["dictionaryName"] = "Miasta"


def _g10(f):
    block = f["tabs"][-1]["questions"][0]["field"]["repeatingSectionGrid"][0]["field"]
    block["description"] = block["description"].replace("<body>", '<body><a href="javascript:alert(1)">x</a>', 1)


def _g12(f):
    matter_field(f)["defaultValue"] = PAPER_VALUE


CONTROLS = {"G1": _g1, "G2": _g2, "G3": _g3, "G4": _g4, "G5": _g5, "G6": _g6, "G7": _g7, "G8": _g8, "G9": _g9,
            "G10": _g10, "G12": _g12}


@pytest.mark.parametrize("cid", list(CONTROLS))
def test_fixture_fails_exactly_its_check(base, cid):
    broken = mutate(base, CONTROLS[cid])
    assert failed_ids(broken, sidecar=sidecar_for(base), fill_values=[PAPER_VALUE]) == {cid}


def test_fixture_g11_ledger_that_does_not_close(base):
    s = sidecar_for(base)
    s["ledger"]["blanks_found"] = 2
    assert failed_ids(base, sidecar=s, fill_values=[PAPER_VALUE]) == {"G11"}


def test_g11_unassigned_long_run_and_unknown_field(base):
    s = sidecar_for(base)
    s["coverage"] = {"runs_total": 1, "assigned": 0, "unassigned": ["jeden dwa trzy cztery"], "silent_pages": []}
    s["ledger"]["rows"][0]["field"] = "00000000-0000-4000-8000-000000000000"
    msgs = [f.message for f in check(base, sidecar=s).get("G11").findings]
    assert any("4 words" in m for m in msgs) and any("not in the form" in m for m in msgs)


def test_every_check_has_a_negative_control():
    assert set(CONTROLS) | {"G11"} == set(NAMES)


def test_g12_finding_names_the_place_not_the_value(base):
    r = check(mutate(base, _g12), fill_values=[PAPER_VALUE]).get("G12")
    assert r.findings and all(PAPER_VALUE.casefold() not in f.message.casefold() for f in r.findings)
    assert r.findings[0].path.endswith("/defaultValue")


# -- details of single checks -----------------------------------------------------------------------------------

def test_findings_carry_the_path_inside_the_form(base):
    r = check(mutate(base, _g6))
    f = r.get("G6").findings[0]
    assert f.path.startswith("/tabs/0/questions/") and f.path.endswith("/states/0/query")
    assert "'Tak!' is not an option" in f.message


def test_g6_known_limit_a_valid_but_wrong_option_passes(base):
    """Recorded limit: G6 knows the options of a field, not the intent. A condition naming "Nie" where "Tak" was
    meant passes G6; intent is judged only by the journeys, and no journey answers the stamp-duty question."""
    def swap(f):
        s = field(f, "plik_z_potwierdzeniem_przelewu")["states"][0]
        s["query"] = s["query"].replace('"Tak" in', '"Nie" in')
    assert "G6" not in failed_ids(mutate(base, swap))


def test_g6_condition_always_true(base):
    def always(f):
        s = field(f, "oplata_info_1")["states"][0]
        s["query"] = f"({s['query']}) or true"
    msgs = [x.message for x in check(mutate(base, always)).get("G6").findings]
    assert any("always true" in m for m in msgs)


def test_g5_unparsable_condition_does_not_crash(base):
    def broken(f):
        field(f, "oplata_info_1")["states"][0]["query"] = '("Tak" in '
    r = check(mutate(base, broken))
    assert {c.id for c in r.failed} == {"G5"}
    assert "does not parse" in r.get("G5").findings[0].message


def test_g7_counts_what_a_default_decides(base):
    d = check(base).get("G7").detail
    assert d["judged"] > 0 and d["decided_by_default"] > 0


def test_g8_names_the_page_that_can_become_empty(base):
    r = check(mutate(base, _g8), journeys=False)
    assert r.get("G8").findings[0].path == "/tabs/1" and r.journeys == []


@pytest.mark.parametrize("profile", ["strict", "tolerant"])
@pytest.mark.parametrize("bad", [
    '<html><head></head><body><a href="javascript:alert(1)">x</a></body></html>',
    '<html><head></head><body><a href=" JaVaScRiPt:alert(1)">x</a></body></html>',
    '<html><head></head><body><script>alert(1)</script></body></html>',
    '<html><head></head><body><p onclick="alert(1)">x</p></body></html>',
    '<html><head></head><body><a href="data:text/html;base64,PHNjcmlwdD4=">x</a></body></html>',
    '<html><head></head><body><iframe src="https://example.invalid"></iframe></body></html>',
    '<html><head></head><body><span style="width: expression(alert(1))">x</span></body></html>',
])
def test_html_allow_list_refuses_script(profile, bad):
    assert html_problems(bad, profile)


def test_html_tolerant_accepts_what_the_exports_hold():
    ok = ('<html><head></head><body><p><span style="color: rgb(0,0,0)">Tekst</span> '
          '<a href="https://www.gov.pl/" target="_blank" rel="noopener" aria-label="x" title="x">link</a>'
          '<img src="data:image/png;base64,iVBORw0KGgo=" width="10" height="10" alt=""></p></body></html>')
    assert html_problems(ok, "tolerant") == []
    assert html_problems(ok, "strict")


def test_not_an_object_and_broken_structure_never_crash():
    r = check(["not", "a", "form"])
    assert not r.passed and r.get("G1").findings
    r = check({"title": "Wniosek", "tabs": "x", "flow": 3})
    assert not r.passed and "G1" in {c.id for c in r.failed}


def test_raise_for_failure_names_the_check(base):
    with pytest.raises(GateFailed) as e:
        check(mutate(base, _g9)).raise_for_failure()
    assert e.value.check.id == "G9" and "dictionaries" in str(e.value)
    check(base).raise_for_failure()


def test_build_without_the_rules_checker_fails_closed(base, monkeypatch):
    """The image must carry tools/coi_lint.py and the schema files: without them G1 and G2 fail, nothing passes."""
    from app.gate import structure
    monkeypatch.setattr(structure, "coi_lint", None)
    structure._validator.cache_clear()
    try:
        r = check(base)
        assert {"G1", "G2"} <= {c.id for c in r.failed}
        assert "not in this build" in r.get("G2").findings[0].message
    finally:
        structure._validator.cache_clear()


def test_unknown_profile_is_refused(base):
    with pytest.raises(ValueError):
        check(base, profile="lenient")


# -- journeys ---------------------------------------------------------------------------------------------------

def test_seven_journeys_as_shared_data():
    js = load_journeys()
    assert len(js) == 7 and len({j["id"] for j in js}) == 7
    assert any(j["id"].startswith("J7") and any("Przedstawiciel ustawowy" == a["value"] for a in j["answers"]) for j in js)
    for j in js:
        assert j["answers"] and all({"field", "value", "required"} <= a.keys() for a in j["answers"])
        assert set(j["expect_visible"]).isdisjoint(j["expect_hidden"])


def test_journey_the_form_cannot_take_is_not_applicable_never_passed():
    only_self = synthetic_form(applicants={"status": "stated", "self": True, "evidence": [{"quote": "x"}]})
    r = check(only_self)
    status = {j.id: j.status for j in r.journeys}
    assert r.passed
    assert status["J5_address_poland"] == status["J6_address_abroad"] == "passed"
    assert {s for k, s in status.items() if k[:2] in ("J1", "J2", "J3", "J4", "J7")} == {"not_applicable"}
    assert all(j.reason for j in r.journeys if j.status == "not_applicable")


def test_journey_that_shows_the_wrong_section_fails_g8(base):
    def leak(f):   # the power of attorney shown to the entity's representative too
        s = field(f, "pelnomocnictwo")["states"][0]
        s["query"] = s["query"].replace('"Pełnomocnik" in', '"Reprezentant" in')
    r = check(mutate(base, leak))
    assert "G8" in {c.id for c in r.failed}
    j3 = next(j for j in r.journeys if j.id.startswith("J3"))
    assert j3.status == "failed" and "pelnomocnictwo" in j3.findings[0].message


def test_all_paths_of_a_journey_are_visible_names(base):
    r = check(base)
    j6 = next(j for j in r.journeys if j.id.startswith("J6"))
    assert {"ulica_zagranica", "adres_zamieszkania"} <= set(j6.visible) and "ulica" not in j6.visible
    assert {t["techName"] for t in fields(base)} >= set(j6.visible)
