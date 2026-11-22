"""Audit 8 SL1: the SCAN_PREP switch of the image path. Default off: the readers get no scan preparation step, so the
image path is the one of before; a comma list names single steps; anything else stops the start."""
from __future__ import annotations

import pytest

from app.config import SCAN_PREP_ACCEPTED, SCAN_PREP_TOKENS, ConfigError, Settings, read_options
from app.readers._base import ReadOptions


def test_default_is_off_and_gives_no_step():
    assert ReadOptions().scan_prep == frozenset()
    s = Settings.from_env({})
    assert s.scan_prep == "off"
    assert read_options(s).scan_prep == frozenset()


def test_on_is_the_accepted_set():
    assert SCAN_PREP_ACCEPTED <= SCAN_PREP_TOKENS
    assert read_options(Settings.from_env({"SCAN_PREP": "on"})).scan_prep == SCAN_PREP_ACCEPTED


def test_a_comma_list_names_steps():
    s = Settings.from_env({"SCAN_PREP": "glyph, leader,thick"})
    assert read_options(s).scan_prep == frozenset({"glyph", "leader", "thick"})


@pytest.mark.parametrize("raw", ["yes", "glyph,blur", "ON"])
def test_an_unknown_value_stops_the_start(raw):
    with pytest.raises(ConfigError) as e:
        Settings.from_env({"SCAN_PREP": raw})
    assert any("SCAN_PREP" in p for p in e.value.problems)
