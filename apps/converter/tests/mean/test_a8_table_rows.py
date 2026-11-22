"""A8 TT: negative controls for the table-of-equal-rows rule (design 6.4.3; review 20-F3). The positive case lives in
test_mean_core.py::test_equal_rows_become_one_repeating_section. Mutation probes M1 (`k >= 3` to `k >= 2`) and M2
(the same-section check removed) survived the existing mean tests; these two tests kill them.
"""
from __future__ import annotations

from test_mean_core import Paper


def test_two_equal_rows_stay_separate_fields():
    p = Paper()
    p.text("WNIOSEK O ZAJĘCIE PASA DROGOWEGO", bold=True)
    for _ in range(2):
        for label in ("długość", "szerokość", "razem"):
            p.blank(label, kind="blank_in_sentence", how="sentence")
    b = p.brief()
    assert not any(s.repeating for s in b.matter), [(s.repeating, [x.label for x in s.fields]) for s in b.matter]
    assert "TABLE_ROW" not in [d.why for d in b.dispositions]


def test_three_equal_rows_in_three_sections_are_not_one_table():
    """Imię / Nazwisko / Adres repeated for the applicant, the owner and the proxy are three parties, not a table."""
    p = Paper()
    p.text("WNIOSEK", bold=True)
    for party in ("Wnioskodawca", "Właściciel", "Pełnomocnik"):
        sid = p.heading(party)
        for label in ("Imię", "Nazwisko", "Adres"):
            p.blank(label, section=sid)
    b = p.brief()
    assert "TABLE_ROW" not in [d.why for d in b.dispositions], [d.why for d in b.dispositions]
    assert not any(s.repeating for s in b.matter)
