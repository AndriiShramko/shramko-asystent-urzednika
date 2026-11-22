"""A8 TT: determinism of the answer. Two runs of the same bytes, and the same bytes under another file name, must give
the same form bytes (the canonical JSON the service sends) and the same ids. The jury runs our image on new files and
may send one file twice or rename it; a different answer for the same bytes would be read as instability.

The file name may differ only in what the service is told about it; the bytes decide the result.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from app import pipeline
from app.config import Settings

from test_a8_cross_format import MAKERS

SETTINGS = Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000"})


def canonical(obj: dict) -> bytes:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def digest(ext: str, data: bytes, name: str) -> str:
    return hashlib.sha256(canonical(pipeline.run(data, name, SETTINGS).form)).hexdigest()


@pytest.mark.parametrize("ext", sorted(MAKERS))
def test_two_runs_of_the_same_bytes_give_the_same_form_bytes(ext):
    data = MAKERS[ext]()
    assert digest(ext, data, f"form.{ext}") == digest(ext, data, f"form.{ext}")


@pytest.mark.parametrize("ext", sorted(MAKERS))
def test_the_same_bytes_under_another_name_give_the_same_form_bytes(ext):
    data = MAKERS[ext]()
    first = digest(ext, data, f"form.{ext}")
    assert digest(ext, data, f"Wniosek_kopia (2).{ext}") == first
    assert digest(ext, data, f"ZZZ.{ext.upper()}") == first


@pytest.mark.parametrize("ext", sorted(MAKERS))
def test_rebuilt_bytes_of_the_same_form_give_the_same_form_bytes(ext):
    """The builders stamp a creation time into the file; the answer must not depend on such metadata."""
    a, b = MAKERS[ext](), MAKERS[ext]()
    assert digest(ext, a, f"a.{ext}") == digest(ext, b, f"b.{ext}")


def test_the_rest_answer_is_byte_equal_for_the_same_bytes_under_two_names():
    from fastapi.testclient import TestClient

    from app.main import create_app

    client = TestClient(create_app(SETTINGS))
    data = MAKERS["docx"]()
    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    r1 = client.post("/v1/forms/convert", files={"file": ("pierwszy.docx", data, mime)})
    r2 = client.post("/v1/forms/convert", files={"file": ("drugi plik.docx", data, mime)})
    assert r1.status_code == r2.status_code == 200, (r1.status_code, r1.text[:300])
    assert r1.content == r2.content
    assert r1.headers["X-Form-SHA256"] == r2.headers["X-Form-SHA256"]
    assert r1.headers["X-Input-SHA256"] == r2.headers["X-Input-SHA256"]
