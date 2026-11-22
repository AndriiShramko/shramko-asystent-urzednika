"""REV-1: on a composite paper (variants) the twin sections are written once (_composite); a show condition read from a
note (C2) that names the choice of a deleted twin must name the kept twin, or the brief does not validate and the
whole form loses every field. Synthetic paper built like test_mean_core's composite case."""
from __future__ import annotations

from tests.mean.test_mean_core import Paper, fields


def _paper() -> Paper:
    p = Paper()
    for n, what in enumerate(("zezwolenie na utrzymanie psa", "zmianę zezwolenia na utrzymanie psa")):
        if n:
            p.new_page()
        p.text(f"WNIOSEK O {what.upper()}", bold=True)
        s = p.heading("Dane psa", number="1")
        p.group("Czy pies był szczepiony?", ["Tak", "Nie"], section=s)
        t = p.heading(f"Szczepienie {n + 1}", number="2")   # differs per variant: not a twin
        p.text("Jeżeli tak, podaj:", role="instruction")
        p.blank(f"Data szczepienia psa {n + 1}", section=t)
    return p


def test_condition_on_a_deleted_twin_names_the_kept_twin() -> None:
    b = _paper().brief()   # strict: raises if a condition names a field that is not in the brief
    f = fields(b)
    choice = [k for k, x in f.items() if x.type == "RADIO" and x.options == ["Tak", "Nie"]]
    assert len(choice) == 1, f.keys()
    dated = [x for x in f.values() if x.label.startswith("Data szczepienia psa")]
    assert len(dated) == 2 and all(x.show_if is not None and x.show_if.field == choice[0] for x in dated)
