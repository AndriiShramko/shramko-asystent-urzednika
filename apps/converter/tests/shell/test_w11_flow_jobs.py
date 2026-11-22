"""Wave 11, lane FLOW: jobs (`/v1/jobs`), the bounded queue and progress by real stages.

What is fixed here: a job answers the bytes of `/v1/forms/convert`; the finished parts of a job move only when the
conversion reports work (never with the clock); the queue runs CONCURRENCY jobs, tells each waiting job its place
and refuses with 429 QUEUE_FULL when it has no room; one failed job does not stop the others; a file the guard
refuses is refused at once and never waits.
"""
from __future__ import annotations

import threading
import time

import factory as fx
from fastapi.testclient import TestClient

from app import jobs, pipeline, progress
from app.config import Settings
from app.guard import ProblemError
from app.main import create_app

OPEN = {"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000"}
FORM = {"title": "Z", "tabs": [], "flow": {"links": []}}


def client(**over) -> TestClient:
    return TestClient(create_app(Settings.from_env({**OPEN, **{k: str(v) for k, v in over.items()}})))


def post(c: TestClient, url: str, name: str, data: bytes):
    body, ctype = fx.multipart([("file", name, data, "application/octet-stream")])
    return c.post(url, content=body, headers={"Content-Type": ctype})


def wait_state(c: TestClient, job_id: str, *states: str, seconds: float = 20.0) -> dict:
    end = time.monotonic() + seconds
    body: dict = {}
    while time.monotonic() < end:
        body = c.get(f"/v1/jobs/{job_id}").json()
        if body.get("state") in states:
            return body
        time.sleep(0.02)
    raise AssertionError(f"job never reached {states}: {body}")


def ok_result() -> pipeline.PipelineResult:
    return pipeline.PipelineResult(form=dict(FORM), sidecar={"counts": {}, "warnings": []})


# ---- the tracker alone ---------------------------------------------------------------------------------------------


def test_calls_without_a_tracker_do_nothing():
    progress.phase("reading")
    progress.pages(3)
    progress.page(2, "ocr")   # no tracker bound: no error, nothing kept


def test_parts_count_finished_work_and_never_go_back():
    t = progress.Tracker()
    assert t.snapshot()["units"] == {"done": 0.0, "total": 100}
    t.phase("reading")
    assert t.snapshot()["units"]["done"] == 4.0           # received 2 + recognised 2 are behind
    t.pages(4)
    t.page(1, "ocr")
    first = t.snapshot()["units"]["done"]
    t.page(3, "ocr")
    assert t.snapshot()["stage"] == {"name": "reading", "step": "ocr", "page": 3, "pages": 4}
    assert t.snapshot()["units"]["done"] == round(4 + 70 * (2 + progress.PAGE_STEPS["ocr"]) / 4, 1) > first
    t.phase("checks")
    high = t.snapshot()["units"]["done"]
    assert high == 94.0
    t.phase("meaning")                                     # the model path composes twice: the text goes back,
    assert t.snapshot()["stage"]["name"] == "meaning"      # the count does not
    assert t.snapshot()["units"]["done"] == high
    t.finish()
    assert t.snapshot()["units"]["done"] == 100.0


def test_the_plan_with_a_model_also_sums_to_one_hundred():
    assert sum(w for _, w in progress.PHASES) == progress.TOTAL == sum(w for _, w in progress.PHASES_MODEL)


# ---- one job -------------------------------------------------------------------------------------------------------


def test_a_job_answers_the_bytes_of_convert():
    data = fx.pdf()
    with client() as c:
        direct = post(c, "/v1/forms/convert?report=1", "a.pdf", data)
        assert direct.status_code == 200
        taken = post(c, "/v1/jobs", "a.pdf", data)
        assert taken.status_code == 202 and taken.headers["Location"] == f"/v1/jobs/{taken.json()['id']}"
        job = taken.json()["id"]
        done = wait_state(c, job, "done")
        assert done["units"] == {"done": 100.0, "total": 100}
        result = c.get(f"/v1/jobs/{job}/result")
        assert result.status_code == 200
        assert result.content == direct.content
        assert result.headers["content-type"] == direct.headers["content-type"]
        for name in ("X-Form-SHA256", "X-Input-SHA256", "X-Converter-Engine"):
            assert result.headers[name] == direct.headers[name]
        alone = c.get(f"/v1/jobs/{job}/result?report=0")
        assert alone.content == post(c, "/v1/forms/convert", "a.pdf", data).content


def test_parts_move_with_reported_work_and_not_with_the_clock(monkeypatch):
    at_ocr, go_on = threading.Event(), threading.Event()

    def staged(data, filename, settings):
        progress.phase("reading")
        progress.pages(4)
        progress.page(3, "ocr")
        at_ocr.set()
        assert go_on.wait(10)
        progress.phase("checks")
        return ok_result()

    monkeypatch.setattr(pipeline, "run", staged)   # called in the job thread: the tracker must reach it there
    with client() as c:
        job = post(c, "/v1/jobs", "a.pdf", fx.pdf()).json()["id"]
        try:
            assert at_ocr.wait(10)
            one = wait_state(c, job, "running")
            assert one["stage"] == {"name": "reading", "step": "ocr", "page": 3, "pages": 4}
            assert one["units"] == {"done": round(4 + 70 * 2.05 / 4, 1), "total": 100}
            time.sleep(0.3)
            two = c.get(f"/v1/jobs/{job}").json()
            assert two["units"] == one["units"]            # nothing was reported: nothing moved
            assert two["stage_s"] > one["stage_s"]         # the sign of life: time since the last report
            not_yet = c.get(f"/v1/jobs/{job}/result")
            assert not_yet.status_code == 202 and not_yet.json()["state"] == "running"
        finally:
            go_on.set()
        assert wait_state(c, job, "done")["units"]["done"] == 100.0


# ---- many jobs -----------------------------------------------------------------------------------------------------


def test_the_queue_runs_one_at_a_time_tells_places_and_refuses_when_full(monkeypatch):
    release = threading.Event()
    running = threading.Semaphore(0)
    most = {"now": 0, "max": 0}
    lock = threading.Lock()

    def slow(data, filename, settings):
        with lock:
            most["now"] += 1
            most["max"] = max(most["max"], most["now"])
        running.release()
        assert release.wait(10)
        with lock:
            most["now"] -= 1
        return ok_result()

    monkeypatch.setattr(pipeline, "run", slow)
    with client(CONCURRENCY=1) as c:
        c.app.state.jobs.limits = jobs.QueueLimits(waiting=2, waiting_bytes=10**9)
        ids = [post(c, "/v1/jobs", f"{i}.pdf", fx.pdf()).json()["id"] for i in range(3)]
        try:
            assert running.acquire(timeout=10)
            assert wait_state(c, ids[0], "running")["queue"] == {"running": 1, "waiting": 2, "waiting_max": 2}
            assert [c.get(f"/v1/jobs/{i}").json().get("position") for i in ids] == [None, 1, 2]
            full = post(c, "/v1/jobs", "x.pdf", fx.pdf())
            assert full.status_code == 429 and full.json()["code"] == "QUEUE_FULL"
            assert full.headers["Retry-After"] == "10" and full.json()["limits"]["waiting_max"] == 2
            busy = post(c, "/v1/forms/convert", "y.pdf", fx.pdf())   # the synchronous way keeps its own answer
            assert busy.status_code == 429 and busy.json()["code"] == "BUSY"
            assert c.get("/v1/jobs").json()["waiting"] == 2
        finally:
            release.set()
        for i in ids:
            assert wait_state(c, i, "done")["state"] == "done"
        assert most["max"] == 1   # never more at once than CONCURRENCY


def test_the_cap_of_waiting_bytes_refuses_too(monkeypatch):
    release = threading.Event()
    monkeypatch.setattr(pipeline, "run", lambda d, f, s: (release.wait(10), ok_result())[1])
    data = fx.pdf()
    with client(CONCURRENCY=1) as c:
        c.app.state.jobs.limits = jobs.QueueLimits(waiting=20, waiting_bytes=len(data) + 10)
        try:
            first = post(c, "/v1/jobs", "a.pdf", data).json()["id"]
            wait_state(c, first, "running")
            assert post(c, "/v1/jobs", "b.pdf", data).status_code == 202   # one file fits in the waiting room
            assert post(c, "/v1/jobs", "c.pdf", data).json()["code"] == "QUEUE_FULL"
        finally:
            release.set()


def test_one_failed_job_does_not_stop_the_others(monkeypatch):
    calls = {"n": 0}

    def first_fails(data, filename, settings):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ProblemError("UNREADABLE", "Nie udało się odczytać pliku: jest uszkodzony lub nie ma tekstu do odczytu.")
        if calls["n"] == 2:
            raise RuntimeError("text of the file that must never be shown")
        return ok_result()

    monkeypatch.setattr(pipeline, "run", first_fails)
    with client(CONCURRENCY=1) as c:
        ids = [post(c, "/v1/jobs", f"{i}.pdf", fx.pdf()).json()["id"] for i in range(3)]
        bad = wait_state(c, ids[0], "error")
        assert bad["error"]["code"] == "UNREADABLE" and bad["error"]["status"] == 422
        answer = c.get(f"/v1/jobs/{ids[0]}/result")
        assert answer.status_code == 422 and answer.json()["code"] == "UNREADABLE"
        crashed = wait_state(c, ids[1], "error")
        assert crashed["error"]["code"] == "GATE_FAILED" and "must never" not in str(crashed)
        assert wait_state(c, ids[2], "done")["state"] == "done"
        assert c.get(f"/v1/jobs/{ids[2]}/result").status_code == 200


def test_a_refused_file_is_refused_at_once_and_never_waits():
    with client() as c:
        wrong = post(c, "/v1/jobs", "a.exe", b"MZ" + b"\x00" * 64)
        assert wrong.status_code == 415 and wrong.json()["code"] in ("EXTENSION", "TYPE_MISMATCH")
        empty = post(c, "/v1/jobs", "a.pdf", b"")
        assert empty.status_code in (400, 415, 422)
        assert c.get("/v1/jobs").json() == {"running": 0, "waiting": 0, "waiting_max": 20, "concurrency": 2,
                                            "job_timeout_s": 600, "waiting_bytes_max": 5 * 20971520}
    with client(MAX_UPLOAD_BYTES=1024) as c:
        over = post(c, "/v1/jobs", "a.pdf", b"%PDF-1.4\n" + b"0" * (3 << 20))
        assert over.status_code == 413 and over.json()["code"] == "TOO_LARGE"


def test_a_waiting_job_can_be_given_up_and_an_unknown_one_is_404(monkeypatch):
    release = threading.Event()
    seen: list[int] = []

    def slow(data, filename, settings):
        seen.append(len(data))
        assert release.wait(10)
        return ok_result()

    monkeypatch.setattr(pipeline, "run", slow)
    with client(CONCURRENCY=1) as c:
        try:
            first = post(c, "/v1/jobs", "a.pdf", fx.pdf()).json()["id"]
            second = post(c, "/v1/jobs", "b.pdf", fx.pdf()).json()["id"]
            wait_state(c, first, "running")
            gone = c.delete(f"/v1/jobs/{second}")
            assert gone.status_code == 200 and gone.json()["state"] == "cancelled"
            assert c.get(f"/v1/jobs/{second}").status_code == 404
            assert c.get("/v1/jobs").json()["waiting"] == 0
        finally:
            release.set()
        wait_state(c, first, "done")
        time.sleep(0.2)
        assert len(seen) == 1   # the job that was given up never started
        missing = c.get("/v1/jobs/" + "0" * 32)
        assert missing.status_code == 404 and missing.json()["code"] == "NOT_FOUND"
