"""AUDIT-8 VA-6 (01-review-finder F1): the reading order of the finder output must not rebuild a set of all run ids
for every run (quadratic: 8000 runs took 5.5 s, 0.25 s after the fix). Deterministic: counts the sets the output
step builds instead of timing it."""
from __future__ import annotations

import builtins

import app.find._core as core
from app.find import find
from tests.find.find_builders import Native, model


def _page(n_words: int) -> Native:
    p = Native()
    for i in range(n_words):
        row, col = divmod(i, 10)
        p.text(40 + col * 50, 40 + row * 11, f"slowo{i % 97}", 40)
    return p


def test_the_order_step_builds_a_bounded_number_of_sets(monkeypatch) -> None:
    calls = {"n": 0}
    real = builtins.set

    def counting(*a):
        # only the sets built from a long list of ids (the whole order so far); small sets elsewhere are not counted
        if a and isinstance(a[0], list) and len(a[0]) >= 100:
            calls["n"] += 1
        return real(*a)

    m = model(_page(600).page())
    monkeypatch.setattr(core, "set", counting, raising=False)
    find(m)
    # the step that appends runs missing from the order used to build one such set per run (600 here)
    assert calls["n"] < 10


def test_every_run_is_in_the_order_once() -> None:
    f = find(model(_page(120).page()))
    assert len(f.order) == len(set(f.order)) == 120
