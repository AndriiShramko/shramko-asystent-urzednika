"""The cold start of the readers registry (WP-F-svc, R1): several first callers at once all see the full list.

Before the fix `_discover` set its flag before the imports and had no lock, so the second of two simultaneous first
requests saw a half-filled registry and answered a false 422 ("this version cannot read PDF yet").
"""
from __future__ import annotations

import importlib
import io
import sys
import threading
import time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import readers
from app.config import Settings
from app.main import create_app

THREADS = 8


def reset_registry(monkeypatch, fail_first: bool = False) -> list[str]:
    """Put the registry back into the state of a process that has converted nothing: no reader, no hook, the reader
    modules not imported. Every import then takes a little time, as it does in a cold container. Returns the full
    list of formats; monkeypatch restores the real modules and the real registry after the test."""
    full = readers.formats()
    prefix = readers.__name__ + "."
    for name, mod in list(sys.modules.items()):
        short = name[len(prefix):]
        if name.startswith(prefix) and "." not in short and not short.startswith("_"):
            monkeypatch.setattr(readers, short, mod, raising=False)   # the attribute of the package comes back too
            monkeypatch.delitem(sys.modules, name)
    monkeypatch.setattr(readers, "_READERS", {})
    monkeypatch.setattr(readers, "_HOOKS", {})
    monkeypatch.setattr(readers, "_discovered", False)
    state = {"fail": fail_first}

    def slow_import(name: str):
        if state["fail"]:
            state["fail"] = False
            raise ImportError("synthetic failure of the first import")
        time.sleep(0.02)
        return importlib.import_module(name)

    monkeypatch.setattr(readers, "importlib", SimpleNamespace(import_module=slow_import))
    return full


def test_simultaneous_first_callers_all_see_the_full_registry(monkeypatch):
    full = reset_registry(monkeypatch)
    assert {"pdf", "docx", "png"} <= set(full)
    start = threading.Barrier(THREADS)
    seen: list[tuple[bool, list[str]]] = []

    def first_call() -> None:
        start.wait(10)
        found = readers.hook("pdf.textless_page") is not None
        seen.append((found, readers.formats()))

    threads = [threading.Thread(target=first_call) for _ in range(THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    assert len(seen) == THREADS
    assert all(found for found, _ in seen), "a caller did not find the hook: the registry was seen half filled"
    assert all(fmts == full for _, fmts in seen)


def test_a_failed_import_is_tried_again_not_left_half_done(monkeypatch):
    full = reset_registry(monkeypatch, fail_first=True)
    with pytest.raises(ImportError):
        readers.formats()
    assert readers._discovered is False
    assert readers.formats() == full


def _pdf() -> bytes:
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 750, "Wniosek probny")
    c.drawString(72, 700, "Imie: ........................")
    c.save()
    return buf.getvalue()


def test_create_app_warms_the_registry(monkeypatch):
    full = reset_registry(monkeypatch)
    assert readers._discovered is False
    create_app(Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false"}))
    assert readers._discovered is True and sorted(readers._READERS) == full


def test_two_simultaneous_first_requests_both_convert_with_equal_bytes(monkeypatch):
    app = create_app(Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000"}))
    reset_registry(monkeypatch)   # as if nothing had warmed it: the lock alone must hold
    data = _pdf()
    start = threading.Barrier(2)
    answers: list = []
    with TestClient(app) as client:   # one event loop shared by both requests

        def send() -> None:
            start.wait(10)
            answers.append(client.post("/v1/forms/convert", files={"file": ("a.pdf", data, "application/pdf")}))

        threads = [threading.Thread(target=send) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(60)
    assert [r.status_code for r in answers] == [200, 200]
    assert answers[0].content == answers[1].content
