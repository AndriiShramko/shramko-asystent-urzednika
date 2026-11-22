"""AUDIT-8 VA-3 (02-F5): on a composite paper a heading of the paper that reads like the selector ("Rodzaj
wniosku") must not take the selector's place. Synthetic paper built like test_mean_core's composite case."""
from __future__ import annotations

from tests.mean.test_mean_core import Paper, fields


def _composite(own_heading: str, before: bool) -> Paper:
    p = Paper()
    if before:
        s = p.heading(own_heading, number="1")
        p.blank("Opis sprawy", section=s)
    for n, what in enumerate(("stypendium sportowe", "nagrodę sportową", "wyróżnienie dla trenera")):
        if n:
            p.new_page()
        p.text(f"WNIOSEK O {what.upper()}", bold=True)
        s = p.heading("Dane sportowca", number="2")
        p.blank("Dyscyplina", section=s)
        t = p.heading("Osiągnięcia", number="3")
        p.blank(f"Opis osiągnięć na {what}", section=t, kind="line_block", lines=2)
    return p


def test_a_paper_heading_rodzaj_wniosku_keeps_the_selector_and_its_own_field() -> None:
    b = _composite("Rodzaj wniosku", before=True).brief()
    f = fields(b)
    assert "rodzaj_wniosku" in f and f["rodzaj_wniosku"].type == "RADIO" and len(f["rodzaj_wniosku"].options) == 3
    assert any(x.label == "Opis sprawy" for x in f.values())
    assert not [w for w in b.warnings if w.code == "UNREADABLE_PART"]


def test_another_heading_before_the_variants_changes_nothing() -> None:
    b = _composite("Informacje wstepne", before=True).brief()
    f = fields(b)
    assert f["rodzaj_wniosku"].type == "RADIO" and any(x.label == "Opis sprawy" for x in f.values())
