"""WP-F-svc: every error is a problem answer (R3), the status page (J3), waiting for a free slot (item 8)."""
from __future__ import annotations

import json
import logging

import factory as fx
from fastapi.testclient import TestClient

from app import pipeline
from app.config import Settings
from app.main import create_app

SENTINEL = "TRESCZFORMULARZA"   # stands for text of the file inside the message of an exception


def make(**over) -> TestClient:
    env = {"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000", **over}
    return TestClient(create_app(Settings.from_env(env)))   # raise_server_exceptions stays on: nothing may reach the server


def post(client: TestClient, path: str = "/v1/forms/convert"):
    return client.post(path, files={"file": ("a.pdf", fx.pdf(), "application/pdf")})


def crash(monkeypatch, on_calls: set[int] | None = None) -> None:
    """`pipeline.run` raises an exception nobody expects, on every call or only on the numbered ones (from 1)."""
    real, count = pipeline.run, {"n": 0}

    def run(data, filename, settings, *a, **kw):
        count["n"] += 1
        if on_calls is None or count["n"] in on_calls:
            raise KeyError(SENTINEL)
        return real(data, filename, settings, *a, **kw)

    monkeypatch.setattr(pipeline, "run", run)


# ---- R3: the catch-all ------------------------------------------------------------------------------------------

def test_an_unexpected_exception_is_a_problem_answer_and_a_content_free_log_line(monkeypatch, caplog):
    crash(monkeypatch)
    client = make()
    with caplog.at_level(logging.DEBUG):
        r = post(client)
    assert r.status_code == 500 and r.headers["content-type"] == "application/problem+json"
    body = r.json()
    assert body["code"] == "GATE_FAILED" and body["status"] == 500 and body["detail"] == "Błąd wewnętrzny usługi."
    assert SENTINEL not in r.text and SENTINEL not in caplog.text
    assert "stage=internal result=KeyError" in caplog.text
    assert post(client, "/v1/forms/report").status_code == 500   # the same on the other conversion endpoint
    assert client.get("/healthz").status_code == 200             # and the service lives on


def test_after_an_unexpected_exception_the_slot_is_free_again(monkeypatch):
    crash(monkeypatch, on_calls={1})
    client = make(CONCURRENCY="1")
    assert [post(client).status_code for _ in range(3)] == [500, 200, 200]


def test_a_request_validation_error_is_a_problem_400(monkeypatch):
    r = make().post("/v1/forms/convert?report=true", files={"file": ("a.pdf", fx.pdf(), "application/pdf")})
    assert r.status_code == 400 and r.headers["content-type"] == "application/problem+json"
    body = r.json()
    assert body["code"] == "BAD_REQUEST" and "report" in body["detail"] and "true" not in body["detail"]
    assert "detail" in body and not isinstance(body["detail"], list)   # not FastAPI's own list of errors


def test_an_unexpected_exception_does_not_cut_the_batch_stream(monkeypatch, caplog):
    crash(monkeypatch, on_calls={2})
    files = [("file", (f"{n}.pdf", fx.pdf(), "application/pdf")) for n in "abc"]
    with caplog.at_level(logging.DEBUG):
        r = make().post("/v1/batches", files=files)
    lines = [json.loads(x) for x in r.text.splitlines()]
    assert r.status_code == 200 and [x["state"] for x in lines] == ["ok", "error", "ok"]
    assert (lines[1]["code"], lines[1]["status"], lines[1]["form"]) == ("GATE_FAILED", 500, None)
    assert lines[0]["form"] == lines[2]["form"] and set(lines[0]["form"]) == {"title", "tabs", "flow"}
    assert SENTINEL not in r.text and SENTINEL not in caplog.text and "result=KeyError" in caplog.text
