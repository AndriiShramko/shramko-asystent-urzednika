"""WP-F3b, understanding second pass: an explicit exclusion prunes the proxy route (D20, audit T4), and the
field tests of audit T1 on papers built from code."""
from __future__ import annotations

from app.find import find
from app.mean import understand
from tests.find.find_builders import DOTS, Native, model
from tests.mean.test_mean_core import Paper


def _paper(extra: str | None) -> Paper:
    p = Paper()
    p.text("WNIOSEK O WPIS", bold=True)
    s = p.heading("Dane wnioskodawcy", number="1")
    p.blank("Imię i nazwisko", kind="cell", section=s)
    p.blank("Dane pełnomocnika", kind="cell", section=s)
    p.blank("Nazwa sali")
    if extra:
        p.text(extra)
    return p


def test_a_paper_that_says_it_is_filed_only_in_person_loses_the_proxy_route_and_keeps_the_quote() -> None:
    b = _paper("Wniosek składa się wyłącznie osobiście.").brief()
    a = b.applicants
    assert a.other_person is False and a.entity is False and a.capacities == []
    assert any("wyłącznie osobiście" in (e.quote or "") for e in a.evidence)
    assert any(d.reason == "PAPER_INSTRUCTION" and "osobiście" in d.what for d in b.dropped)


def test_in_person_only_removes_the_proxy_and_keeps_the_company_and_the_representative() -> None:
    def run(extra: str | None):
        p = Paper()
        p.text("WNIOSEK O WPIS", bold=True)
        s = p.heading("Dane podmiotu")
        p.blank("Nazwa firmy", kind="cell", section=s)
        p.blank("NIP", kind="cell", section=s)
        if extra:
            p.text(extra)
        return p.brief().applicants
    before, after = run(None), run("Wniosek składa się wyłącznie osobiście.")
    assert before.entity is True and "pelnomocnik" in before.capacities
    assert after.other_person is False and after.entity is True and after.self_ == before.self_
    assert "pelnomocnik" not in after.capacities and "reprezentant" in after.capacities


def test_without_the_exclusion_the_proxy_route_stays() -> None:
    a = _paper(None).brief().applicants
    assert a.other_person is True and "pelnomocnik" in a.capacities


# -- audit T1: two reservation papers that differ in one label give two different fields; a sale notice ----------

def _brief(title: str, labels: tuple[str, ...]):
    n = Native()
    n.text(70, 80, title, 300, bold=True)
    for i, label in enumerate(labels):
        n.text(70, 120 + 60 * i, label, 100)
        n.text(180, 120 + 60 * i, DOTS, 200)
    m = model(n.page())
    return understand(m, find(m))


def _fields(b) -> dict:
    return {f.label: f for s in b.matter for f in s.fields}


def test_numer_sali_and_liczba_uczestnikow_are_a_room_field_and_a_number() -> None:
    room = _fields(_brief("WNIOSEK O REZERWACJĘ", ("Numer sali", "Data rezerwacji")))
    count = _fields(_brief("WNIOSEK O REZERWACJĘ", ("Liczba uczestników", "Data rezerwacji")))
    assert room["Numer sali"].type == "TEXT_FIELD" and room["Numer sali"].concept is None
    assert count["Liczba uczestników"].type == "NUMBER" and count["Liczba uczestników"].concept == "count"
    assert room["Data rezerwacji"].type == count["Data rezerwacji"].type == "DATEPICKER"


def test_sale_notice_keeps_buyer_pesel_vin_and_date_of_sale_in_the_matter() -> None:
    b = _brief("ZAWIADOMIENIE O ZBYCIU POJAZDU", ("PESEL nabywcy", "Numer VIN", "Data zbycia"))
    got = _fields(b)
    assert set(got) == {"PESEL nabywcy", "Numer VIN", "Data zbycia"}
    assert got["PESEL nabywcy"].concept == "pesel" and got["Data zbycia"].type == "DATEPICKER"
    assert b.title.value == "Zawiadomienie o zbyciu pojazdu"


def test_a_name_asked_of_a_candidate_under_the_applicant_heading_is_a_field_of_the_matter() -> None:
    p = Paper()
    p.text("WNIOSEK O NAGRODĘ", bold=True)
    s = p.heading("Wnioskodawca", number="1")
    p.blank("Imię i nazwisko", kind="cell", section=s)
    p.blank("Imię i nazwisko kandydata", kind="cell", section=s)
    got = {f.label for sec in p.brief().matter for f in sec.fields}
    assert "Imię i nazwisko kandydata" in got and "Imię i nazwisko" not in got
