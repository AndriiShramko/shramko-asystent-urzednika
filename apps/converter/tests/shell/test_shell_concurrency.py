"""Integration: when every CONCURRENCY slot is busy, the next request gets 429 BUSY at once (no queue)."""
from __future__ import annotations

import threading

import factory as fx
from test_shell_http import make_client, post, secret_file  # noqa: F401  (fixture re-used)

from app import pipeline


def test_busy_answer_when_all_slots_are_taken(tmp_path, secret_file, monkeypatch):  # noqa: F811
    entered, release = threading.Event(), threading.Event()
    form = {"title": "Z", "tabs": [], "flow": {"links": []}}

    def slow(data, filename, settings):
        entered.set()
        assert release.wait(10), "the test never released the first request"
        return pipeline.PipelineResult(form=form, sidecar={"counts": {}})

    monkeypatch.setattr(pipeline, "run", slow)
    first: dict = {}
    with make_client(tmp_path, secret_file, CONCURRENCY=1) as client:  # one event loop shared by both requests
        t = threading.Thread(target=lambda: first.update(r=post(client, "/v1/forms/convert", "a.pdf", fx.pdf())))
        t.start()
        try:
            assert entered.wait(10), "the first request never reached the pipeline"
            second = post(client, "/v1/forms/convert", "b.pdf", fx.pdf())
            assert second.status_code == 429
            assert second.json()["code"] == "BUSY"
            assert second.headers["Retry-After"] == "5"
        finally:
            release.set()
            t.join(10)
        assert first["r"].status_code == 200  # the first request was not harmed by the refusal
        again = post(client, "/v1/forms/convert", "c.pdf", fx.pdf())
        assert again.status_code == 200  # the slot is free again
