"""D19: only G1 to G4 stop a form (500); G5 to G12 are warnings of a 200; the warnings header; the job time limit."""
from __future__ import annotations

import threading
import time

import factory as fx
import pytest
from fastapi.testclient import TestClient

from app import gate, pipeline
from app.config import Settings
from app.main import create_app


def make(**over) -> TestClient:
    env = {"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000", **over}
    return TestClient(create_app(Settings.from_env(env)))


def post(client: TestClient, path: str = "/v1/forms/convert"):
    return client.post(path, files={"file": ("a.pdf", fx.pdf(), "application/pdf")})


def fail_checks(monkeypatch, *ids: str) -> None:
    real = gate.check

    def check(form, *a, **kw):
        report = real(form, *a, **kw)
        for c in report.checks:
            if c.id in ids:
                c.status = "failed"
                c.findings = [gate.Finding("/tabs/0", "it says 'secret-value' here")]
        return report

    monkeypatch.setattr(pipeline.gate, "check", check)


def test_a_failed_non_blocking_check_is_a_warning_of_a_200(monkeypatch):
    fail_checks(monkeypatch, "G8")
    r = post(make())
    assert r.status_code == 200 and set(r.json()) == {"title", "tabs", "flow"}
    assert r.headers["X-Converter-Warnings"].split("; ")[0].isdigit()
    assert "GATE_G8" in r.headers["X-Converter-Warnings"]
    side = post(make(), "/v1/forms/report").json()
    w = [x for x in side["warnings"] if x["code"] == "GATE_G8"]
    assert len(w) == 1 and "G8" in w[0]["detail"] and "/tabs/0" in w[0]["detail"] and "secret-value" not in w[0]["detail"]


@pytest.mark.parametrize("blocking", ["G1", "G2", "G3", "G4"])
def test_a_failed_blocking_check_stays_500(monkeypatch, blocking):
    fail_checks(monkeypatch, blocking, "G8")
    r = post(make())
    assert r.status_code == 500 and r.json()["code"] == "GATE_FAILED" and blocking in r.json()["detail"]
    assert "X-Converter-Warnings" not in r.headers


def test_no_warning_no_header():
    r = post(make())
    assert r.status_code == 200
    n = len(post(make(), "/v1/forms/report").json()["warnings"])
    assert ("X-Converter-Warnings" in r.headers) == (n > 0)


def test_the_header_is_ascii_deduplicated_and_capped(monkeypatch):
    many = [{"code": f"CODE_{i}", "detail": "x"} for i in range(80)] + [{"code": "ŻÓŁW_é", "detail": "x"}] * 3
    result = pipeline.PipelineResult(form={"title": "Z", "tabs": [], "flow": {"links": []}}, sidecar={"warnings": many})
    monkeypatch.setattr(pipeline, "run", lambda d, n, s: result)
    r = post(make())
    h = r.headers["X-Converter-Warnings"]
    assert h.startswith("83; CODE_0, CODE_1") and h.isascii() and len(h) <= 210 and h.endswith("...")
    assert h.count("CODE_0,") == 1


JOB_S = 30   # how long a held job would run if nothing stopped the wait


def hold_jobs(monkeypatch) -> threading.Event:
    """Every job blocks until the event is set (or JOB_S seconds): a document that takes far longer than the limit."""
    release = threading.Event()
    monkeypatch.setattr(pipeline, "run", lambda d, n, s: release.wait(JOB_S))
    return release


def let_go(release: threading.Event) -> None:
    """End the held jobs and wait for their threads, so no abandoned job leaks into the next test."""
    release.set()
    for t in list(pipeline._abandoned):
        t.join(10)


def test_the_job_time_limit_answers_504_timeout(monkeypatch):
    release = hold_jobs(monkeypatch)
    try:
        started = time.perf_counter()
        r = post(make(JOB_TIMEOUT_S="1"))
        took = time.perf_counter() - started
        assert r.status_code == 504 and r.json()["code"] == "TIMEOUT" and "1 s" in r.json()["detail"]
        # the answer comes at the limit and not when the job ends: 1 s against 30 s, so a slow runner cannot blur it
        assert 0.9 <= took < JOB_S / 2
    finally:
        let_go(release)


def test_abandoned_jobs_count_against_the_slots(monkeypatch):
    release = hold_jobs(monkeypatch)
    client = make(JOB_TIMEOUT_S="1", CONCURRENCY="2")
    try:
        assert post(client).status_code == 504
        assert post(client).status_code == 504            # one abandoned job is fewer than the two slots
        started = time.perf_counter()
        r = post(client)                                  # two abandoned jobs: no third one is started
        assert r.status_code == 429 and r.json()["code"] == "BUSY" and r.headers["Retry-After"] == "30"
        assert r.headers["content-type"] == "application/problem+json"
        assert time.perf_counter() - started < 0.9        # refused at once, not after another time limit
        assert sum(t.is_alive() for t in pipeline._abandoned) == 2
    finally:
        let_go(release)
    done = pipeline.PipelineResult(form={"title": "Z", "tabs": [], "flow": {"links": []}}, sidecar={"warnings": []})
    monkeypatch.setattr(pipeline, "run", lambda d, n, s: done)
    assert post(client).status_code == 200                # the abandoned jobs ended: the slots are back


def test_a_job_inside_the_limit_is_unchanged():
    a = post(make(JOB_TIMEOUT_S="60")).content
    b = post(make(JOB_TIMEOUT_S="120")).content
    assert a == b
