"""A8 TT: the body cap of the BodyLimit middleware is the documented one (max_upload_bytes * factor + FRAMING_SLACK).

Mutation probe M7 (the cap multiplied by 8) survived all of tests/shell: the existing 413 tests send a real file part,
so the guard refuses it with the same 413 TOO_LARGE even when the middleware lets the whole body in (read into memory).
Here the body is junk that is not multipart: the middleware alone answers 413; a body it lets through ends as 400.
"""
from __future__ import annotations

import dataclasses

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import BATCH_MAX_FACTOR, FRAMING_SLACK, create_app

MB = 1 << 20
S = dataclasses.replace(Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000"}),
                        max_upload_bytes=2 * MB)


def post(path: str, size: int):
    c = TestClient(create_app(S), raise_server_exceptions=False)
    return c.post(path, content=b"j" * size, headers={"Content-Type": "text/plain"})


def test_single_file_cap_is_the_limit_plus_the_framing_slack():
    cap = S.max_upload_bytes + FRAMING_SLACK
    assert post("/v1/forms/convert", cap).status_code == 400            # inside the cap: refused later, as not multipart
    r = post("/v1/forms/convert", cap + 1)
    assert r.status_code == 413 and r.json()["code"] == "TOO_LARGE", r.text[:200]


def test_batch_cap_is_the_factor_times_the_limit_plus_the_framing_slack():
    cap = S.max_upload_bytes * BATCH_MAX_FACTOR + FRAMING_SLACK
    r = post("/v1/batches", cap + 1)
    assert r.status_code == 413 and r.json()["code"] == "TOO_LARGE", r.text[:200]
