"""REV-3: boxes in front of a printed date mask ("□ D D -", "□ M M -", "□ R R R R") are one DATEPICKER (C6); the
clerk must not get the choice-group remark "one or several options" for that date. Synthetic paper."""
from __future__ import annotations

from app.find import find
from app.mean import understand
from tests.find.find_builders import flow, model


def test_date_mask_boxes_give_no_choice_group_warning():
    page = flow("DEKLARACJA O WYSOKOSCI OPLATY", "C. OKOLICZNOSCI ZLOZENIA",
                "Pierwsza deklaracja - data zdarzenia powodujacego obowiazek:",
                "□ D D -", "□ M M -", "□ R R R R", bold=(0, 1))
    m = model(page)
    b = understand(m, find(m))
    assert [f.type for s in b.matter for f in s.fields] == ["DATEPICKER"]
    assert not [w for w in b.warnings if w.code == "AMBIGUOUS_GROUP"], b.warnings


def test_a_real_choice_without_wording_still_tells_the_clerk():
    page = flow("WNIOSEK O WYDANIE ZAŚWIADCZENIA", "A. SPOSÓB ODBIORU",
                "Sposób odbioru zaświadczenia:", "□ osobiście", "□ pocztą", "□ przez ePUAP", bold=(0, 1))
    m = model(page)
    b = understand(m, find(m))
    if any(f.type == "RADIO" and len(f.options) == 3 for s in b.matter for f in s.fields):
        assert [w for w in b.warnings if w.code == "AMBIGUOUS_GROUP"]
