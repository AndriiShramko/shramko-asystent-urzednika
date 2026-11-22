"""Progress of one conversion, told by the code that does the work (wave 11, lane FLOW).

    from app import progress
    progress.phase("reading")          # a phase of the conversion begins (the earlier ones are complete)
    progress.pages(7)                  # the reader knows how many pages it will read
    progress.page(3, "ocr")            # page 3: its OCR begins (the pages before it are complete)

Every call is a fact: a piece of work has begun, so the pieces before it are finished. Nothing here measures time
and nothing moves by itself; with no tracker bound (the command line, the synchronous endpoints, the tests) every
call returns at once. A call never raises and never changes what the conversion returns.

The bar. The conversion is a fixed row of phases; each phase owns a share of 100 parts (`PHASES`). The shares are
constants taken from measured runs (reading a scan is nearly all of the time: see `PAGE_STEPS`), but a part is
counted only when the work behind it is reported: `done = shares of finished phases + share of the current phase
x finished pages / pages`. A phase with no pages (a DOCX, a sheet) is one piece: its share is added when it ends.
"""
from __future__ import annotations

import contextvars
import threading
import time
from typing import Any

# phase -> parts of 100. "model" exists only when the open model is configured (its share comes out of reading).
PHASES: tuple[tuple[str, int], ...] = (
    ("received", 2), ("recognised", 2), ("reading", 70), ("fields", 8), ("meaning", 8), ("form", 4), ("checks", 4),
    ("export", 2))
PHASES_MODEL: tuple[tuple[str, int], ...] = (
    ("received", 2), ("recognised", 2), ("reading", 58), ("fields", 8), ("meaning", 8), ("form", 4), ("checks", 4),
    ("model", 12), ("export", 2))
TOTAL = 100

# The steps of one page and the part of the page that is finished when the step BEGINS. Measured on the task scans
# (2 CPU): the OCR program is about nine tenths of a scanned page, finding lines and boxes most of the rest.
PAGE_STEPS: dict[str, float] = {"native": 0.0, "render": 0.0, "prepare": 0.0, "ocr": 0.05, "shapes": 0.9}

_current: contextvars.ContextVar["Tracker | None"] = contextvars.ContextVar("progress_tracker", default=None)


class Tracker:
    """What one job has reported so far. Written by the job's thread, read by the status endpoint."""

    def __init__(self, model: bool = False) -> None:
        self._plan = PHASES_MODEL if model else PHASES
        self._names = [n for n, _ in self._plan]
        self._lock = threading.Lock()
        self._phase = 0            # index into the plan
        self._step = ""
        self._page = 0
        self._pages = 0
        self._done = 0.0           # parts finished; never goes down
        self._since = time.monotonic()
        self._reports = 0

    # ---- written by the job -----------------------------------------------------------------------------------

    def _touch(self) -> None:
        self._since = time.monotonic()
        self._reports += 1

    def _parts(self) -> float:
        before = float(sum(w for _, w in self._plan[: self._phase]))
        share = self._plan[self._phase][1]
        if self._pages > 0 and self._page > 0:
            in_page = PAGE_STEPS.get(self._step, 0.0)
            before += share * min(1.0, (self._page - 1 + in_page) / self._pages)
        return before

    def phase(self, name: str) -> None:
        with self._lock:
            if name not in self._names:
                return
            index = self._names.index(name)
            if index != self._phase or self._step:
                self._touch()
            # A later pass may name an earlier phase again (the model path composes twice): the text follows the
            # work, the count of finished parts never goes back.
            self._phase, self._step, self._page, self._pages = index, "", 0, 0
            self._done = max(self._done, self._parts())

    def pages(self, total: int) -> None:
        with self._lock:
            self._pages = max(0, int(total))

    def page(self, number: int, step: str) -> None:
        with self._lock:
            if (number, step) != (self._page, self._step):
                self._touch()
            self._page, self._step = max(0, int(number)), step
            self._done = max(self._done, self._parts())

    def finish(self) -> None:
        with self._lock:
            self._phase, self._step = len(self._plan) - 1, ""
            self._done = float(TOTAL)
            self._touch()

    # ---- read by the status endpoint --------------------------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            stage: dict[str, Any] = {"name": self._names[self._phase]}
            if self._step:
                stage["step"] = self._step
            if self._page:
                stage["page"] = self._page
            if self._pages:
                stage["pages"] = self._pages
            return {"stage": stage, "units": {"done": round(self._done, 1), "total": TOTAL},
                    "stage_s": round(time.monotonic() - self._since, 1), "reports": self._reports}


def bind(tracker: Tracker | None) -> contextvars.Token:
    """Make `tracker` the one the calls below write to, in this context (and in threads started with a copy of it)."""
    return _current.set(tracker)


def unbind(token: contextvars.Token) -> None:
    _current.reset(token)


def phase(name: str) -> None:
    t = _current.get()
    if t is not None:
        t.phase(name)


def pages(total: int) -> None:
    t = _current.get()
    if t is not None:
        t.pages(total)


def page(number: int, step: str) -> None:
    t = _current.get()
    if t is not None:
        t.page(number, step)
