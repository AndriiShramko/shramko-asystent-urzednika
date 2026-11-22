"""Audit 8 SL1: the service turns the accepted scan preparation steps on by default (the jury starts the image with no
flags); SCAN_PREP=off gives the image way of before. Readers called directly (ReadOptions()) still take no step."""
from __future__ import annotations

from app.config import SCAN_PREP_ACCEPTED, Settings, read_options
from app.readers._base import ReadOptions


def test_the_service_default_is_the_accepted_set():
    s = Settings.from_env({})
    assert s.scan_prep == "on"
    assert read_options(s).scan_prep == SCAN_PREP_ACCEPTED
    assert SCAN_PREP_ACCEPTED


def test_off_gives_no_step():
    assert read_options(Settings.from_env({"SCAN_PREP": "off"})).scan_prep == frozenset()


def test_readers_called_directly_take_no_step():
    assert ReadOptions().scan_prep == frozenset()
