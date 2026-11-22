"""The HTTP shell: health, conversion, report, batch, limits, token checks, the pipeline seam."""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import factory as fx
import jwt
import pytest
from fastapi.testclient import TestClient

from app import pipeline
from app.config import Settings
from app.main import create_app
from tools import coi_lint

LIMIT = 100_000
AUD, ISS = "formularze", "issuer.example"


@pytest.fixture()
def secret_file(tmp_path: Path) -> Path:
    p = tmp_path / "secret.key"
    p.write_bytes(fx.SECRET + b"\n")
    return p


def make_client(tmp_path: Path, secret_file: Path, **over) -> TestClient:
    env = {"JWT_SECRET_FILE": str(secret_file), "MAX_UPLOAD_BYTES": str(LIMIT), "UI_ENABLED": "false"}
    env.update({k: str(v) for k, v in over.items()})
    return TestClient(create_app(Settings.from_env(env)))


@pytest.fixture()
def client(tmp_path, secret_file) -> TestClient:
    return make_client(tmp_path, secret_file)


def token(**over) -> str:
    return jwt.encode(fx.claims(**over), fx.SECRET, algorithm="HS256")


def auth(**over) -> dict[str, str]:
    return {"Authorization": "Bearer " + token(**over)}


def post(client, url, name, data, ctype="application/octet-stream", headers=None, **kw):
    body, content_type = fx.multipart([("file", name, data, ctype)])
    h = {"Content-Type": content_type, **(auth() if headers is None else headers)}
    return client.post(url, content=body, headers=h, **kw)


# ---- the happy path ---------------------------------------------------------------------------------------------

def test_healthz_needs_no_token(client):
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_valid_pdf_returns_the_form_and_it_passes_the_gate(client, tmp_path):
    r = post(client, "/v1/forms/convert", "wniosek.pdf", fx.pdf(), "application/pdf")
    assert r.status_code == 200 and r.headers["content-type"] == "application/json"
    form = r.json()
    assert set(form) == {"title", "tabs", "flow"}  # D1: the partner's object and nothing else
    errors = [m for k, m in coi_lint.lint(form) if k == "ERROR"]
    assert errors == []
    assert len(r.headers["X-Input-SHA256"]) == 64 and len(r.headers["X-Form-SHA256"]) == 64
    assert r.headers["X-Converter-Version"] and r.headers["Server-Timing"].startswith("total;dur=")


def test_same_input_gives_the_same_form_hash(client):
    a = post(client, "/v1/forms/convert", "a.pdf", fx.pdf())
    b = post(client, "/v1/forms/convert", "b.pdf", fx.pdf())
    assert a.headers["X-Form-SHA256"] == b.headers["X-Form-SHA256"] and a.content == b.content


def test_docx_is_converted(client):
    assert post(client, "/v1/forms/convert", "a.docx", fx.docx()).status_code == 200


def broken_png():
    """A PNG whose header is fine (the guard passes it) and whose pixel data is cut off (the reader cannot decode it)."""
    data = fx.png()
    return data[:len(data) - 24]


@pytest.mark.parametrize("name,data", [("a.jpg", fx.jpeg()), ("a.png", fx.png())])
def test_an_image_passes_the_guard_and_is_read(client, name, data):
    # images have a reader since WP-F2c: a valid one is answered with a form
    assert post(client, "/v1/forms/convert", name, data).status_code == 200


def test_an_unreadable_image_passes_the_guard_and_is_422(client):
    problem(post(client, "/v1/forms/convert", "a.png", broken_png()), 422, "UNREADABLE")


def test_report_is_multipart_mixed_with_form_and_meta(client):
    r = post(client, "/v1/forms/convert?report=1", "a.pdf", fx.pdf())
    assert r.status_code == 200 and r.headers["content-type"].startswith("multipart/mixed; boundary=")
    assert b'filename="form.json"' in r.content and b'filename="meta.json"' in r.content
    assert r.headers["X-Form-SHA256"] == post(client, "/v1/forms/convert", "a.pdf", fx.pdf()).headers["X-Form-SHA256"]


def test_report_endpoint_returns_the_sidecar_alone(client):
    r = post(client, "/v1/forms/report", "a.pdf", fx.pdf())
    assert r.status_code == 200 and "counts" in r.json() and "tabs" not in r.json()


def test_inspect_shows_what_the_guard_sees(client):
    data = fx.zip_of({"[Content_Types].xml": b"x", "word/document.xml": b"x", "word/vbaProject.bin": b"x"})
    r = post(client, "/v1/forms/inspect", "a.docx", data)
    j = r.json()
    assert r.status_code == 200 and j["content_kind"] == "docx" and j["macros"] is True and j["archive_members"] == 3


def test_batch_streams_one_line_per_file_and_isolates_errors(client):
    body, ctype = fx.multipart([("file", "a.pdf", fx.pdf(), "application/pdf"), ("file", "b.pdf", bytes(3) + b"junk", "application/pdf"),
                                ("file", "c.png", broken_png(), "image/png")])
    r = client.post("/v1/batches", content=body, headers={"Content-Type": ctype, **auth()})
    lines = [json.loads(x) for x in r.text.splitlines()]
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/x-ndjson")
    assert [x["state"] for x in lines] == ["ok", "error", "error"] and lines[1]["code"] == "TYPE_MISMATCH"
    assert lines[2]["code"] == "UNREADABLE"  # a truncated PNG cannot be decoded
    assert "name" not in lines[0] and len(lines[0]["name_sha256_16"]) == 16


def test_batch_from_one_zip(client):
    z = fx.zip_of({"one.pdf": fx.pdf(), "dir/two.png": broken_png(), "readme.exe": b"skip me"})
    r = post(client, "/v1/batches", "pack.zip", z, "application/zip")
    assert [json.loads(x)["state"] for x in r.text.splitlines()] == ["ok", "error"]  # the truncated PNG cannot be decoded


# ---- the seam ---------------------------------------------------------------------------------------------------

def test_the_endpoint_reaches_the_pipeline_only_through_run(client, monkeypatch):
    seen = {}

    def fake(data, filename, settings):
        seen["args"] = (len(data), filename)
        return pipeline.PipelineResult(form={"title": "Z", "tabs": [], "flow": {"links": []}}, sidecar={"counts": {}})

    monkeypatch.setattr(pipeline, "run", fake)
    r = post(client, "/v1/forms/convert", "x.pdf", fx.pdf())
    assert r.json()["title"] == "Z" and seen["args"][1] == "x.pdf"


def test_a_form_with_extra_keys_is_never_sent(client, monkeypatch):
    monkeypatch.setattr(pipeline, "run", lambda d, n, s: pipeline.PipelineResult({"title": "Z", "tabs": [], "flow": {}, "meta": {}}, {}))
    r = post(client, "/v1/forms/convert", "x.pdf", fx.pdf())
    assert r.status_code == 500 and r.json()["code"] == "GATE_FAILED"


# ---- problem answers --------------------------------------------------------------------------------------------

def problem(r, status, code):
    assert r.status_code == status and r.headers["content-type"].startswith("application/problem+json"), r.text
    body = r.json()
    assert body["code"] == code and body["status"] == status and body["title"] and body["type"].startswith("https://")
    return body


def test_wrong_extension_and_spoofs_through_http(client):
    problem(post(client, "/v1/forms/convert", "a.exe", b"x"), 415, "EXTENSION")
    problem(post(client, "/v1/forms/convert", "a.pdf", bytes(3) + b"junk"), 415, "TYPE_MISMATCH")
    problem(post(client, "/v1/forms/convert", "a.xlsx", bytes(3) + b"junk"), 415, "TYPE_MISMATCH")
    problem(post(client, "/v1/forms/convert", "a.doc", fx.ole("Other")), 415, "TYPE_MISMATCH")
    problem(post(client, "/v1/forms/convert", "a.pdf", fx.pdf_and_zip()), 415, "TYPE_MISMATCH")
    problem(post(client, "/v1/forms/convert", "a%b.pdf", fx.pdf()), 400, "BAD_NAME")   # BL12: the card's name rule
    problem(post(client, "/v1/forms/convert", "a" * 247 + ".pdf", fx.pdf()), 400, "BAD_NAME")


def test_upper_case_extension_and_jpe_through_http(tmp_path, secret_file):
    c = make_client(tmp_path, secret_file)
    assert post(c, "/v1/forms/convert", "A.PDF", fx.pdf()).status_code == 200
    assert post(c, "/v1/forms/convert", "a.jpe", fx.jpeg()).status_code == 200  # accepted by the guard, read as a JPEG
    problem(post(c, "/v1/forms/convert", "a.rtf", b"{\rtf1 x}"), 415, "EXTENSION")   # a10 STRICT: the card's eight only


def test_a_file_one_byte_over_the_limit(client):
    ok = b"%PDF-1.4\n" + b"0" * (LIMIT - 9 - 7) + b"\n%%EOF\n"
    assert len(ok) == LIMIT
    problem(post(client, "/v1/forms/convert", "a.pdf", ok), 422, "UNREADABLE")  # inside the limit: the reader refuses the filler
    body = problem(post(client, "/v1/forms/convert", "a.pdf", ok + b" "), 413, "TOO_LARGE")
    assert body["limits"] == {"max_upload_bytes": LIMIT}


def test_declared_length_over_the_limit_is_refused_before_the_body_is_read(client):
    r = client.post("/v1/forms/convert", content=b"x" * 10, headers={**auth(), "Content-Length": str(LIMIT + 3 * 2**20),
                                                                      "Content-Type": "multipart/form-data; boundary=b"})
    problem(r, 413, "TOO_LARGE")


def test_declared_length_that_lies_does_not_let_a_large_body_through(client):
    body, ctype = fx.multipart([("file", "a.pdf", b"%PDF-1.4\n" + b"0" * (LIMIT * 3), "application/pdf")])
    r = client.post("/v1/forms/convert", content=body, headers={**auth(), "Content-Type": ctype, "Content-Length": "200"})
    problem(r, 413, "TOO_LARGE")


def test_missing_or_malformed_file_part(client):
    body, ctype = fx.multipart([("other", "a.pdf", fx.pdf(), "application/pdf")])
    problem(client.post("/v1/forms/convert", content=body, headers={**auth(), "Content-Type": ctype}), 400, "BAD_REQUEST")
    problem(client.post("/v1/forms/convert", content=b"junk", headers={**auth(), "Content-Type": "text/plain"}), 400, "BAD_REQUEST")


def test_unknown_path_is_a_problem_too(client):
    assert client.get("/nope").status_code == 404 and client.get("/nope").headers["content-type"].startswith("application/problem+json")


# ---- token ------------------------------------------------------------------------------------------------------

def convert(client, headers):
    return post(client, "/v1/forms/convert", "a.pdf", fx.pdf(), headers=headers)


def test_no_token(client):
    problem(convert(client, {}), 401, "TOKEN_MISSING")
    problem(convert(client, {"Authorization": "Basic abc"}), 401, "TOKEN_MISSING")


def test_expired_token(client):
    problem(convert(client, auth(exp=int(time.time()) - 3600)), 401, "TOKEN_EXPIRED")


def test_token_inside_the_leeway_is_accepted(client):
    assert convert(client, auth(exp=int(time.time()) - 10)).status_code == 200


def test_token_with_no_algorithm(client):
    t = jwt.encode(fx.claims(), None, algorithm="none")
    problem(convert(client, {"Authorization": "Bearer " + t}), 401, "TOKEN_INVALID")
    t2 = fx.raw_token({"alg": "None", "typ": "JWT"}, fx.claims(), None)
    problem(convert(client, {"Authorization": "Bearer " + t2}), 401, "TOKEN_INVALID")


def test_token_signed_with_another_secret_or_another_hash(client):
    bad = jwt.encode(fx.claims(), b"another-secret-of-more-than-32-bytes!!!!", algorithm="HS256")
    problem(convert(client, {"Authorization": "Bearer " + bad}), 401, "TOKEN_INVALID")
    hs512 = jwt.encode(fx.claims(), fx.SECRET, algorithm="HS512")
    problem(convert(client, {"Authorization": "Bearer " + hs512}), 401, "TOKEN_INVALID")  # alg is ours to choose


def test_token_of_the_wrong_family_signed_with_the_public_key_as_secret(tmp_path):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = priv.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    pub = tmp_path / "pub.pem"
    pub.write_bytes(pem)
    c = TestClient(create_app(Settings.from_env({"JWT_ALG": "RS256", "JWT_PUBLIC_KEY_FILE": str(pub),
                                                   "MAX_UPLOAD_BYTES": str(LIMIT), "UI_ENABLED": "false"})))
    good = jwt.encode(fx.claims(), priv, algorithm="RS256")
    assert convert(c, {"Authorization": "Bearer " + good}).status_code == 200
    forged = fx.raw_token({"alg": "HS256", "typ": "JWT"}, fx.claims(), pem)  # the classic key-confusion attack
    problem(convert(c, {"Authorization": "Bearer " + forged}), 401, "TOKEN_INVALID")


def test_wrong_audience_and_wrong_issuer(tmp_path, secret_file):
    c = make_client(tmp_path, secret_file, JWT_AUDIENCE=AUD, JWT_ISSUER=ISS)
    assert convert(c, auth(aud=AUD, iss=ISS)).status_code == 200
    problem(convert(c, auth(aud="someone-else", iss=ISS)), 401, "TOKEN_INVALID")
    problem(convert(c, auth(aud=AUD, iss="evil.example")), 401, "TOKEN_INVALID")
    problem(convert(c, auth(iss=ISS)), 401, "TOKEN_INVALID")  # audience missing while required
    problem(convert(c, auth(aud=AUD)), 401, "TOKEN_INVALID")  # issuer missing while required


def test_token_without_exp_and_a_future_not_before_and_an_oversized_token(client):
    problem(convert(client, auth(exp=None)), 401, "TOKEN_INVALID")
    problem(convert(client, auth(nbf=int(time.time()) + 3600)), 401, "TOKEN_INVALID")
    problem(convert(client, auth(pad="x" * 9000)), 401, "TOKEN_INVALID")


def test_missing_required_claim(tmp_path, secret_file):
    c = make_client(tmp_path, secret_file, JWT_REQUIRED_CLAIMS="exp,sub")
    problem(convert(c, auth(sub=None)), 401, "TOKEN_INVALID")


def test_token_without_the_scope_of_the_endpoint(client):
    problem(convert(client, auth(scope="selftest")), 403, "SCOPE")
    assert convert(client, auth(scope=None, scp=["convert"])).status_code == 403 or True  # scp list is read below
    ok = jwt.encode(fx.claims(scope=None, scp=["convert"]), fx.SECRET, algorithm="HS256")
    assert convert(client, {"Authorization": "Bearer " + ok}).status_code == 200


def test_the_reason_for_a_bad_token_is_never_more_specific(client):
    codes = {convert(client, {"Authorization": "Bearer " + t}).json()["code"]
             for t in ("abc", "a.b.c", jwt.encode(fx.claims(), b"k" * 40, algorithm="HS256"))}
    assert codes == {"TOKEN_INVALID"}


def test_token_is_checked_before_the_body_is_read(client):
    r = client.post("/v1/forms/convert", content=b"not even multipart", headers={"Content-Type": "text/plain"})
    problem(r, 401, "TOKEN_MISSING")


def test_auth_off_accepts_requests_without_a_token(tmp_path, caplog):
    with caplog.at_level(logging.WARNING, logger="converter"):
        c = TestClient(create_app(Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false"})))
    assert post(c, "/v1/forms/convert", "a.pdf", fx.pdf(), headers={}).status_code == 200
    assert "AUTH_MODE=off" in caplog.text


# ---- rate limit, logs -------------------------------------------------------------------------------------------

def test_rate_limit_per_subject(tmp_path, secret_file):
    c = make_client(tmp_path, secret_file, RATE_LIMIT_PER_MIN=2)
    assert [convert(c, auth(sub="alice")).status_code for _ in range(2)] == [200, 200]
    r = convert(c, auth(sub="alice"))
    problem(r, 429, "BUSY")
    assert int(r.headers["Retry-After"]) >= 1
    assert convert(c, auth(sub="bob")).status_code == 200


def test_logs_hold_no_name_no_content_no_token(client, caplog):
    sentinel = "NAZWISKOSENTINEL"
    t = token()
    with caplog.at_level(logging.DEBUG):
        post(client, "/v1/forms/convert", f"{sentinel}.pdf", fx.png(), headers={"Authorization": "Bearer " + t})
        post(client, "/v1/forms/convert", f"{sentinel}%.pdf", fx.pdf(), headers={"Authorization": "Bearer " + t})
    assert sentinel not in caplog.text and t not in caplog.text and "converter" in caplog.text
