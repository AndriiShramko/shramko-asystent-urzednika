"""A8 TT: seeded byte-flip fuzz over the synthetic forms (PDF, DOCX, XLSX built in code). A damaged upload must end
in a 200 form JSON or a problem JSON with a machine `code`: never a crash, never a plain-text 500, never a hang.

Fixed seed, so a failure names the exact case (format, round) and replays the same bytes. Marked slow (about a minute):
the fast gate leaves it out, `gate.sh full` (CI) runs it.
"""
from __future__ import annotations

import dataclasses
import random
import time

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

from test_a8_cross_format import docx_form, pdf_form, xlsx_form

pytestmark = pytest.mark.slow

SEED = 20261122
ROUNDS = 12            # per format
FLIPS = (1, 8, 64)     # bytes changed per round, cycled
PER_CASE_S = 10.0
SETTINGS = dataclasses.replace(
    Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000"}), job_timeout_s=30)
TYPES = {"pdf": "application/pdf",
         "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
         "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}


def mutants(data: bytes, rng: random.Random):
    for r in range(ROUNDS):
        b = bytearray(data)
        n = FLIPS[r % len(FLIPS)]
        for _ in range(n):
            i = rng.randrange(len(b))
            b[i] = rng.randrange(256)
        if r % 4 == 3:   # a cut tail as well: a truncated upload
            b = b[: rng.randrange(len(b) // 2, len(b))]
        yield r, bytes(b)


@pytest.mark.parametrize("ext,build", [("pdf", pdf_form), ("docx", docx_form), ("xlsx", xlsx_form)])
def test_byte_flips_never_crash_or_hang(ext, build):
    client = TestClient(create_app(SETTINGS), raise_server_exceptions=False)
    rng = random.Random(f"{SEED}-{ext}")
    seen = {}
    for r, data in mutants(build(), rng):
        t = time.monotonic()
        resp = client.post("/v1/forms/convert", files={"file": (f"fuzz.{ext}", data, TYPES[ext])})
        took = time.monotonic() - t
        case = (ext, r, resp.status_code)
        assert took < PER_CASE_S, ("hang", case, round(took, 1))
        ctype = resp.headers.get("content-type", "")
        if resp.status_code == 200:
            body = resp.json()
            assert set(body) >= {"title", "tabs", "flow"}, case
        else:
            assert ctype.startswith("application/problem+json"), (case, ctype, resp.text[:200])
            body = resp.json()
            assert body.get("code") and body.get("status") == resp.status_code, (case, body)
            assert resp.status_code != 500, ("our fault on a damaged upload", case, body)
            assert "Traceback" not in resp.text, case
        seen[resp.status_code] = seen.get(resp.status_code, 0) + 1
    assert seen, ext
