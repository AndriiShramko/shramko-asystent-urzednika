"""AUDIT-8 VA-2 (23-F3, 23-F4): one or several options. A group whose paper does not say "several" is one choice
(RADIO): the partner's exports hold no CHECKBOX group. The instruction line above the group counts as its wording,
and the "several" wording wins over the length of the list. Synthetic papers."""
from __future__ import annotations

from app.find import find
from app.mean import understand
from tests.find.find_builders import Native, model

OPTIONS = ["pierwsza deklaracja", "nowa deklaracja", "ustanie obowiazku", "korekta deklaracji"]
MANY = ["boks", "judo", "karate", "kolarstwo", "plywanie", "szachy", "tenis", "zeglarstwo"]


def _group(options: list[str], question: str = "Okolicznosci zlozenia", instruction: str | None = None) -> Native:
    n = Native()
    n.text(70, 60, "DEKLARACJA O WYSOKOSCI OPLATY", 300, bold=True)
    n.text(50, 100, "B. OKOLICZNOSCI", 200, bold=True)
    y = 120
    if instruction:
        n.text(50, y, instruction, 300)
        y += 16
    n.text(50, y, question, 200)
    for opt in options:
        y += 16
        n.text(60, y, "□", 8)
        n.text(75, y, opt, 200)
    return n


def _choices(n: Native) -> list[tuple[str, int]]:
    m = model(n.page())
    b = understand(m, find(m))
    return [(f.type, len(f.options or [])) for s in b.matter for f in s.fields if f.type in ("RADIO", "CHECKBOX", "SELECT")]


def test_a_group_the_paper_does_not_call_multiple_is_one_choice() -> None:
    assert _choices(_group(OPTIONS)) == [("RADIO", 4)]


def test_an_instruction_line_that_allows_several_makes_a_checkbox_group() -> None:
    assert _choices(_group(OPTIONS, instruction="(można zaznaczyć kilka odpowiedzi)")) == [("CHECKBOX", 4)]


def test_the_several_wording_wins_over_a_long_list() -> None:
    assert _choices(_group(MANY, question="Dyscypliny (zaznacz wszystkie uprawiane)")) == [("CHECKBOX", 8)]


def test_a_long_list_without_the_several_wording_stays_a_select() -> None:
    assert _choices(_group(MANY, question="Dyscyplina")) == [("SELECT", 8)]
