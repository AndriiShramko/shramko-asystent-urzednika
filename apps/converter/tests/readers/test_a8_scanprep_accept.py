"""Audit 8 SL1: the scan lab accepted six scan preparation steps (paired run on 145 lab files, image sl1:s5, all seven
steps against off: recall per file +13.0 points, bootstrap 95 % [+9.5, +16.8]; blank output -21.7 points; white,
prose and noise controls 0 paper fields; orient alone +0.4 points [-1.2, +2.5], so it is left out). SCAN_PREP=on
turns the accepted steps on; with no SCAN_PREP the image path stays the one of before."""
from __future__ import annotations

from app.config import SCAN_PREP_ACCEPTED, SCAN_PREP_TOKENS, Settings, read_options

ACCEPTED = frozenset({"scale", "glyph", "leader", "thick", "deskew", "rules"})


def test_the_lab_accepted_steps_are_named():
    assert SCAN_PREP_ACCEPTED == ACCEPTED
    assert SCAN_PREP_ACCEPTED <= SCAN_PREP_TOKENS


def test_on_turns_the_accepted_steps_on():
    assert read_options(Settings.from_env({"SCAN_PREP": "on"})).scan_prep == ACCEPTED


def test_unset_still_gives_no_step():
    assert read_options(Settings.from_env({})).scan_prep == frozenset()


def test_orient_is_not_accepted():
    assert "orient" not in SCAN_PREP_ACCEPTED
