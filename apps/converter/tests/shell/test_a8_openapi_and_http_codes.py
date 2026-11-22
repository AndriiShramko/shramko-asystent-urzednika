"""AUDIT-8 VC-6 (06-F6, 06-F7): a 404 or 405 is a problem answer with a `code` like every other error (405 keeps its
Allow header), and /openapi.json declares the multipart body of the upload routes, so a generated client can call them."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def make() -> TestClient:
    env = {"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000"}
    return TestClient(create_app(Settings.from_env(env)))


def test_404_and_405_carry_a_code():
    c = make()
    r = c.get("/v1/no-such-route")
    assert r.status_code == 404 and r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["code"] == "NOT_FOUND"
    r = c.get("/v1/forms/convert")
    assert r.status_code == 405 and r.json()["code"] == "METHOD_NOT_ALLOWED"
    assert "POST" in r.headers.get("allow", "")


def test_openapi_declares_the_upload_body():
    paths = make().get("/openapi.json").json()["paths"]
    for route in ("/v1/forms/convert", "/v1/forms/report", "/v1/forms/inspect", "/v1/batches"):
        body = paths[route]["post"].get("requestBody")
        assert body and body.get("required") is True, route
        schema = body["content"]["multipart/form-data"]["schema"]
        assert "file" in schema["properties"] and schema["required"] == ["file"], route
    many = paths["/v1/batches"]["post"]["requestBody"]["content"]["multipart/form-data"]["schema"]["properties"]["file"]
    assert many["type"] == "array"
