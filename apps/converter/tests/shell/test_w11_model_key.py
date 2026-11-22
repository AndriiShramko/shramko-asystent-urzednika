"""Wave 11 KEY: the model settings of the review page (`app.vision.session`, routes /v1/model...).

A key never appears in an answer or a log line; the key of the environment is sent only to the address of the
environment; a wrong key, no credit, a limit, an unknown model, a dead address and a slow server each get their own
Polish sentence, and each says that conversion goes on without the model; with nothing configured /status and the
conversion output are what they were. The model server is a small local HTTP server of this file: no network
outside 127.0.0.1, every key is synthetic.
"""
from __future__ import annotations

import json
import logging
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import factory as fx
import jwt
import pytest
from fastapi.testclient import TestClient

from app import pipeline, vision
from app.config import Settings
from app.main import create_app
from app.vision import session

# Fake keys, built from parts so that the publishing check does not read them as real secrets.
ENV_KEY = "-".join(["FAKE", "ENV", "KEY", "do", "not", "show", "0123456789", "tailE"])   # 16+: a tail of four may be shown
PAGE_KEY = "-".join(["FAKE", "PAGE", "KEY", "do", "not", "show", "9876543210", "tailP"])
SHORT_KEY = "short-key"                                      # under 16: nothing of it is ever shown
VISION_VARS = ("VISION_MODE", "VISION_BASE_URL", "VISION_API_KEY", "VISION_API_KEY_FILE", "VISION_MODEL",
               "VISION_PAGE_CONFIG", "MODEL_STEP")


class FakeModelServer:
    """An OpenAI-compatible server that answers by the key it is given. It records every request it got."""

    def __init__(self) -> None:
        self.seen: list[dict] = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):   # silent
                pass

            def do_POST(self):   # noqa: N802
                body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
                key = (self.headers.get("Authorization") or "").removeprefix("Bearer ")
                try:
                    model = json.loads(body).get("model", "")
                except ValueError:
                    model = ""
                outer.seen.append({"path": self.path, "key": key, "model": model})
                status, payload = 200, {"choices": [{"finish_reason": "stop", "message": {"content": "OK"}}]}
                if not self.path.endswith("/v1/chat/completions"):
                    status, payload = 404, {"detail": "Not Found"}
                elif key == "wrong":
                    status, payload = 401, {"error": {"message": "Invalid API key"}}
                elif key == "empty-wallet":
                    status, payload = 402, {"error": {"message": "Insufficient credits"}}
                elif key == "too-many":
                    status, payload = 429, {"error": {"message": "Rate limit reached"}}
                elif key == "slow":
                    time.sleep(1.5)
                elif key == "html":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<html>hello</html>")
                    return
                elif model == "no-such-model":
                    status, payload = 404, {"error": {"message": "The model `no-such-model` does not exist"}}
                raw = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/v1"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture()
def server():
    s = FakeModelServer()
    yield s
    s.close()


@pytest.fixture()
def other():
    s = FakeModelServer()
    yield s
    s.close()


@pytest.fixture(autouse=True)
def _fresh(monkeypatch):
    for k in VISION_VARS:
        monkeypatch.delenv(k, raising=False)
    session.clear()
    session._OVERRIDE = None
    vision.CACHE._d.clear()
    vision.BREAKER._n, vision.BREAKER._until, vision.BREAKER._trial = 0, 0.0, False
    vision._set_state("OFF")
    yield
    session._OVERRIDE = None
    vision._set_state("OFF")


def make(**over) -> TestClient:
    env = {"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000", **over}
    return TestClient(create_app(Settings.from_env(env)))


def configured(monkeypatch, server, key: str = ENV_KEY, model: str = "open-lab/Open-Model-3B") -> None:
    monkeypatch.setenv("VISION_BASE_URL", server.url)
    monkeypatch.setenv("VISION_API_KEY", key)
    monkeypatch.setenv("VISION_MODEL", model)


def convert(client: TestClient):
    return client.post("/v1/forms/convert?report=1", files={"file": ("a.docx", fx.docx(), "application/zip")})


# ---- nothing configured: as before --------------------------------------------------------------------------------

def test_nothing_configured_status_and_conversion_are_as_before():
    client = make()
    status = client.get("/status")
    assert set(status.json()) == {"service", "version", "engine", "auth", "formats", "limits"}
    assert status.json()["engine"] == "rules"
    first = convert(client)
    assert first.status_code == 200 and first.headers["X-Converter-Engine"] == "rules"
    assert client.get("/v1/model").json() == {"page_config": True, "state": "off", "source": "none"}
    # the routes of this module were asked, nothing was typed: the same bytes, the same /status
    again = convert(client)
    assert again.content.split(b"\r\n", 1)[1] == first.content.split(b"\r\n", 1)[1]
    assert again.headers["X-Form-SHA256"] == first.headers["X-Form-SHA256"]
    assert client.get("/status").content == status.content
    assert vision.VisionConfig.from_env().configured is False and pipeline.vision_on(Settings.from_env({})) is False


def test_a_check_with_nothing_configured_calls_nobody_and_says_so():
    r = make().post("/v1/model/check", json={})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False and body["code"] == "not_configured" and body["http"] is None
    assert "wpisz adres serwera modelu i klucz" in body["message"] and session.STILL_WORKS in body["message"]


def test_typed_settings_then_forgotten_leave_the_service_as_it_was(server):
    client = make()
    before_status, before = client.get("/status").content, convert(client)
    put = client.put("/v1/model/session", json={"base_url": server.url, "model": "m1", "key": PAGE_KEY})
    assert put.status_code == 200 and put.json()["model"]["source"] == "session"
    assert vision.VisionConfig.from_env().configured is True
    assert client.delete("/v1/model/session").json()["model"] == {"page_config": True, "state": "off", "source": "none"}
    assert vision.VisionConfig.from_env().configured is False
    assert client.get("/status").content == before_status
    assert convert(client).headers["X-Form-SHA256"] == before.headers["X-Form-SHA256"]


# ---- the state for the page ----------------------------------------------------------------------------------------

def test_a_key_of_the_environment_is_named_by_its_origin_and_its_last_four_characters(monkeypatch, server):
    configured(monkeypatch, server)
    body = make().get("/v1/model").json()
    assert body["state"] == "on" and body["source"] == "environment" and body["used"] is False
    assert body["model"] == "open-lab/Open-Model-3B" and body["host"] == "loopback" and body["address"] == server.url
    assert body["key"] == {"set": True, "origin": "environment-variable", "tail": ENV_KEY[-4:]}


def test_the_whole_key_is_shown_only_when_the_operator_allows_it(monkeypatch, server):
    configured(monkeypatch, server)
    monkeypatch.delenv("VISION_KEY_REVEAL", raising=False)
    assert "full" not in make().get("/v1/model").json()["key"]
    monkeypatch.setenv("VISION_KEY_REVEAL", "off")
    assert "full" not in make().get("/v1/model").json()["key"]
    monkeypatch.setenv("VISION_KEY_REVEAL", "on")
    assert make().get("/v1/model").json()["key"]["full"] == ENV_KEY


def test_with_tokens_on_and_reveal_on_a_stranger_still_gets_no_key(monkeypatch, server, tmp_path):
    configured(monkeypatch, server)
    monkeypatch.setenv("VISION_KEY_REVEAL", "on")
    assert session.public_state(authorized=False)["key"] == {"set": True, "origin": "environment-variable"}
    assert session.public_state(authorized=True)["key"]["full"] == ENV_KEY


def test_a_short_key_shows_no_tail(monkeypatch, server):
    configured(monkeypatch, server, key=SHORT_KEY)
    assert make().get("/v1/model").json()["key"] == {"set": True, "origin": "environment-variable"}


def test_a_key_file_is_named_as_a_file_never_by_its_path(monkeypatch, server, tmp_path):
    f = tmp_path / "secret-folder" / "model.key"
    f.parent.mkdir()
    f.write_text(ENV_KEY, encoding="utf-8")
    monkeypatch.setenv("VISION_BASE_URL", server.url)
    monkeypatch.setenv("VISION_API_KEY_FILE", str(f))
    r = make().get("/v1/model")
    assert r.json()["key"]["origin"] == "environment-file" and "secret-folder" not in r.text


def test_with_tokens_on_a_stranger_sees_the_state_but_no_address_and_no_tail(monkeypatch, server, tmp_path):
    configured(monkeypatch, server)
    secret = tmp_path / "secret.key"
    secret.write_bytes(fx.SECRET + b"\n")
    client = make(AUTH_MODE="jwt", JWT_SECRET_FILE=str(secret))
    stranger = client.get("/v1/model").json()
    assert stranger["state"] == "on" and "address" not in stranger and "tail" not in stranger["key"]
    bearer = {"Authorization": "Bearer " + jwt.encode(fx.claims(), fx.SECRET, algorithm="HS256")}
    assert client.get("/v1/model", headers=bearer).json()["key"]["tail"] == ENV_KEY[-4:]
    for call in (lambda: client.put("/v1/model/session", json={"model": "m2"}),
                 lambda: client.delete("/v1/model/session"), lambda: client.post("/v1/model/check", json={})):
        assert call().status_code == 401
    assert server.seen == [] and session.active() is False


# ---- the key never leaves -----------------------------------------------------------------------------------------

def test_no_key_in_any_answer_or_log_line(monkeypatch, server, other, caplog):
    configured(monkeypatch, server)
    answers = []
    with caplog.at_level(logging.DEBUG), make() as client:
        answers += [client.get("/v1/model"), client.get("/status"), client.post("/v1/model/check", json={})]
        answers += [client.put("/v1/model/session", json={"base_url": other.url, "model": "m2", "key": PAGE_KEY})]
        answers += [client.get("/v1/model"), client.get("/status"), client.post("/v1/model/check", json={})]
        answers += [client.post("/v1/model/check", json={"key": "wrong"}), client.post("/v1/model/check", json={"key": PAGE_KEY})]
        answers += [client.put("/v1/model/session", json={"base_url": "ftp://x", "key": PAGE_KEY}), convert(client)]
        answers += [client.put("/v1/model/session", content=b"{not json " + PAGE_KEY.encode())]
        answers += [client.delete("/v1/model/session"), client.get("/v1/model")]
    assert [a.status_code for a in answers] == [200, 200, 200, 200, 200, 200, 200, 200, 200, 400, 200, 400, 200, 200]
    everything = "\n".join(a.text + "\n" + json.dumps(dict(a.headers)) for a in answers) + "\n" + caplog.text
    for secret in (ENV_KEY, PAGE_KEY, ENV_KEY[:-4], PAGE_KEY[:-4]):
        assert secret not in everything
    assert "stage=model-config result=set source=session host=loopback" in caplog.text
    assert "stage=model-check result=ok host=loopback" in caplog.text
    assert other.url not in caplog.text and server.url not in caplog.text
    # the servers got the keys they were meant to get, and nothing else
    assert {s["key"] for s in server.seen} == {ENV_KEY}
    assert {s["key"] for s in other.seen} == {PAGE_KEY, "wrong"}


def test_the_key_of_the_environment_is_never_sent_to_another_address(monkeypatch, server, other):
    configured(monkeypatch, server)
    client = make()
    check = client.post("/v1/model/check", json={"base_url": other.url})
    assert check.json()["code"] == "key_needed" and "wpisz też klucz" in check.json()["message"]
    put = client.put("/v1/model/session", json={"base_url": other.url, "model": "m2"})
    assert put.status_code == 400 and put.json()["code"] == "key_needed"
    assert other.seen == [] and session.active() is False
    # the same address with another model name: the key of the environment may be used
    assert client.put("/v1/model/session", json={"model": "m2"}).json()["model"]["model"] == "m2"
    assert client.post("/v1/model/check", json={}).json()["ok"] is True
    assert server.seen[-1] == {"path": "/v1/chat/completions", "key": ENV_KEY, "model": "m2"} and other.seen == []


def test_a_key_typed_for_one_address_is_not_reused_for_another(server, other):
    client = make()
    assert client.put("/v1/model/session", json={"base_url": server.url, "model": "m1", "key": PAGE_KEY}).status_code == 200
    assert client.post("/v1/model/check", json={"base_url": other.url, "model": "m1"}).json()["code"] == "key_needed"
    assert other.seen == []


# ---- what is wrong, in Polish ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("typed, code, http, words", [
    ({"key": "wrong"}, "bad_key", 401, "odrzucił klucz"),
    ({"key": "empty-wallet"}, "no_credit", 402, "skończyły się środki"),
    ({"key": "too-many"}, "rate_limit", 429, "limit zapytań"),
    ({"model": "no-such-model"}, "model_not_found", 404, "nie zna modelu"),
    ({"key": "html"}, "not_api", 200, "nie odpowiada API zgodne z OpenAI"),
])
def test_each_failure_has_its_own_polish_sentence_and_says_conversion_goes_on(monkeypatch, server, typed, code, http, words):
    configured(monkeypatch, server)
    body = make().post("/v1/model/check", json=typed).json()
    assert (body["ok"], body["code"], body["http"]) == (False, code, http)
    assert words in body["message"] and body["message"].endswith(session.STILL_WORKS)


def test_a_wrong_address_on_a_living_server_is_not_an_api(monkeypatch, server):
    configured(monkeypatch, server)
    body = make().post("/v1/model/check", json={"base_url": server.url + "/wrong", "key": PAGE_KEY}).json()
    assert body["code"] == "not_api" and body["http"] == 404


def test_a_dead_address_is_unreachable(monkeypatch):
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()   # nobody listens there now
    body = make().post("/v1/model/check", json={"base_url": f"http://127.0.0.1:{port}/v1", "key": PAGE_KEY}).json()
    assert body["code"] == "unreachable" and "Nie udało się połączyć" in body["message"]
    assert body["message"].endswith(session.STILL_WORKS)


def test_a_slow_server_is_a_timeout(monkeypatch, server):
    monkeypatch.setattr(session, "CHECK_READ_S", 0.3)
    body = make().post("/v1/model/check", json={"base_url": server.url, "key": "slow"}).json()
    assert body["code"] == "timeout" and "nie odpowiedział na czas" in body["message"]


@pytest.mark.parametrize("typed, code", [
    ({"base_url": "ftp://files.example.test/v1", "key": PAGE_KEY}, "bad_url"),
    ({"base_url": "https://user:pass@models.example.test/v1", "key": PAGE_KEY}, "bad_url"),
    ({"base_url": "https://models.example.test/v1", "key": "two words"}, "bad_key_form"),
    ({"base_url": "https://models.example.test/v1", "key": PAGE_KEY, "model": "bad name!"}, "bad_model"),
    ({"base_url": "https://models.example.test/v1", "key": 5}, "bad_request"),
])
def test_bad_input_is_refused_before_any_call(typed, code):
    client = make()
    assert client.post("/v1/model/check", json=typed).json()["code"] == code
    assert client.put("/v1/model/session", json=typed).status_code == 400 and session.active() is False


def test_a_failure_of_the_step_is_shown_as_a_fallback_with_its_meaning(monkeypatch, server):
    configured(monkeypatch, server)
    client = make()
    vision._set_state("FALLBACK", "http_401", "open-lab/Open-Model-3B")
    body = client.get("/v1/model").json()
    assert (body["state"], body["reason"], body["problem"]) == ("fallback", "http_401", "bad_key")
    # the same settings answer a check again: the fallback is over
    assert client.post("/v1/model/check", json={}).json()["ok"] is True
    assert client.get("/v1/model").json()["state"] == "on"


def test_a_failed_check_of_the_settings_in_use_is_shown_at_once_and_a_check_of_typed_ones_is_not(monkeypatch, server):
    configured(monkeypatch, server, key="empty-wallet")
    client = make()
    assert client.get("/v1/model").json()["state"] == "on"
    assert client.post("/v1/model/check", json={"key": "wrong"}).json()["code"] == "bad_key"   # typed, not in use
    assert client.get("/v1/model").json()["state"] == "on"
    assert client.post("/v1/model/check", json={}).json()["code"] == "no_credit"               # the settings in use
    body = client.get("/v1/model").json()
    assert (body["state"], body["reason"], body["problem"]) == ("fallback", "check_no_credit", "no_credit")
    assert client.get("/status").json()["vision"]["state"] == "FALLBACK"
    assert convert(client).status_code == 200   # and conversion goes on


@pytest.mark.parametrize("reason, code", [
    ("check_rate_limit", "rate_limit"), ("check_unknown", "server_error"),
    ("http_401", "bad_key"), ("http_403", "bad_key"), ("http_402", "no_credit"), ("http_429", "rate_limit"),
    ("http_404", "model_not_found"), ("connect", "unreachable"), ("network", "unreachable"), ("timeout", "timeout"),
    ("deadline", "timeout"), ("not_json", "not_api"), ("http_500", "server_error"), ("breaker_open", "server_error"),
    ("bad_answer", "server_error"), ("", "server_error"),
])
def test_every_reason_of_the_step_maps_to_a_sentence(reason, code):
    assert session.problem_of(reason) == code and session.message(code).endswith(session.STILL_WORKS)


# ---- the operator's switches ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("switch", [{"MODEL_STEP": "off"}, {"VISION_MODE": "off"}])
def test_a_step_switched_off_by_the_operator_cannot_be_switched_on_from_the_page(monkeypatch, server, switch):
    configured(monkeypatch, server)
    for k, v in switch.items():
        monkeypatch.setenv(k, v)
    client = make()
    assert client.get("/v1/model").json() == {"page_config": False, "state": "disabled", "source": "none"}
    put = client.put("/v1/model/session", json={"base_url": server.url, "model": "m1", "key": PAGE_KEY})
    assert put.status_code == 403 and put.json()["code"] == "disabled"
    assert client.post("/v1/model/check", json={}).status_code == 403
    assert vision.VisionConfig.from_env().configured is False and server.seen == []


def test_page_changes_can_be_forbidden(monkeypatch, server):
    configured(monkeypatch, server)
    monkeypatch.setenv("VISION_PAGE_CONFIG", "off")
    client = make()
    assert client.get("/v1/model").json()["page_config"] is False
    put = client.put("/v1/model/session", json={"model": "m2"})
    assert put.status_code == 403 and put.json()["code"] == "locked" and "wyłączył zmianę" in put.json()["message"]
    assert client.delete("/v1/model/session").status_code == 403
    assert client.post("/v1/model/check", json={"key": PAGE_KEY}).status_code == 403
    assert client.post("/v1/model/check", json={}).json()["ok"] is True   # checking the server's own settings is allowed
    assert session.active() is False


def test_an_oversized_body_is_refused(server):
    r = make().put("/v1/model/session", content=json.dumps({"key": "k" * 9000}).encode())
    assert r.status_code == 400 and r.json()["code"] == "bad_request"


def test_the_routes_are_in_the_openapi():
    paths = make().get("/openapi.json").json()["paths"]
    assert {"/v1/model", "/v1/model/session", "/v1/model/check"} <= set(paths)
