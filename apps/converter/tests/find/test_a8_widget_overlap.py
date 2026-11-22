"""AUDIT-8 VA-7 (01-review-finder F3): a fillable widget lying over a place the paper draws (a box, a dotted line)
gave two fields, one of them labelled with the widget's technical name ("Text1"). Synthetic pages; negative cases:
a widget on bare paper stays, widgets inside a larger drawn cell stay."""
from __future__ import annotations

from app.find import find
from app.mean import understand
from app.model.page import Widget
from tests.find.find_builders import DOTS, Native, model


def _fields(n: Native, *widgets: Widget) -> list[str]:
    pg = n.page().model_copy(update={"widgets": list(widgets)})
    m = model(pg)
    b = understand(m, find(m))
    return [f.label for s in b.matter for f in s.fields]


def _paper() -> Native:
    n = Native()
    n.text(70, 60, "WNIOSEK O WYDANIE ZASWIADCZENIA", 300, bold=True)
    n.text(50, 100, "Nazwa ogrodu", 80)
    return n


def test_a_widget_over_a_drawn_box_is_one_field_with_the_paper_label() -> None:
    n = _paper()
    n.rect(140, 98, 200, 14)
    assert _fields(n, Widget(id="p1w1", kind="text", name="Text1", box=(140, 98, 340, 112))) == ["Nazwa ogrodu"]


def test_a_widget_over_a_dotted_line_is_one_field_with_the_paper_label() -> None:
    n = _paper()
    n.text(140, 100, DOTS, 200)
    assert _fields(n, Widget(id="p1w1", kind="text", name="Text1", box=(140, 98, 340, 112))) == ["Nazwa ogrodu"]


def test_a_widget_on_bare_paper_stays_a_field() -> None:
    # negative case: nothing drawn under the widget
    n = _paper()
    assert len(_fields(n, Widget(id="p1w1", kind="text", name="Nazwa ogrodu", box=(140, 98, 340, 112)))) == 1


def test_two_widgets_inside_one_larger_drawn_cell_both_stay() -> None:
    # negative case: the drawn cell is not covered by either widget, so neither widget is a duplicate of it
    n = _paper()
    n.rect(140, 96, 400, 40)
    labels = _fields(n, Widget(id="p1w1", kind="text", name="Imie", box=(142, 98, 300, 112)),
                     Widget(id="p1w2", kind="text", name="Nazwisko", box=(142, 118, 300, 132)))
    assert "Imie" in labels and "Nazwisko" in labels
