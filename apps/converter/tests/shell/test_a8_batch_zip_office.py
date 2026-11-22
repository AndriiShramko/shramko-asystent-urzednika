"""AUDIT-8 VC-1 (06-F1): a batch ZIP that holds Office files (themselves ZIP packages) is read member by member,
not refused whole as "an archive inside an archive". A real archive inside the batch ZIP stays refused."""
from __future__ import annotations

import json

import factory as fx
from fastapi.testclient import TestClient

from app.config import Settings
from app.guard import ProblemError
from app.guard.checks import check_archive
from app.main import create_app


def make() -> TestClient:
    env = {"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000"}
    return TestClient(create_app(Settings.from_env(env)))


def batch(client: TestClient, data: bytes):
    return client.post("/v1/batches", files={"file": ("pack.zip", data, "application/zip")})


def test_batch_zip_with_docx_xlsx_ods_is_read_member_by_member():
    z = fx.zip_of({"one.pdf": fx.pdf(), "two.docx": fx.docx(), "three.xlsx": fx.xlsx(), "four.ods": fx.ods()})
    r = batch(make(), z)
    assert r.status_code == 200, r.text
    lines = [json.loads(x) for x in r.text.splitlines()]
    assert len(lines) == 4
    assert [x["state"] for x in lines[:3]] == ["ok", "ok", "ok"], [(x["state"], x.get("code")) for x in lines]
    # the factory's ODS is a stub with no table: it passes the guard and the reader says it has nothing to read
    assert lines[3].get("code") != "ARCHIVE_LIMIT"


def test_batch_zip_with_a_zip_inside_is_still_refused():
    z = fx.zip_of({"one.pdf": fx.pdf(), "inner.zip": fx.zip_of({"x.pdf": fx.pdf()})})
    r = batch(make(), z)
    assert r.status_code == 413 and r.json()["code"] == "ARCHIVE_LIMIT"


def test_zip_renamed_docx_inside_the_batch_is_an_error_line_not_a_pass():
    z = fx.zip_of({"one.pdf": fx.pdf(), "fake.docx": fx.zip_of({"x.pdf": fx.pdf()})})
    r = batch(make(), z)
    lines = [json.loads(x) for x in r.text.splitlines()]
    assert r.status_code == 200 and [x["state"] for x in lines] == ["ok", "error"]
    assert lines[1]["code"] == "TYPE_MISMATCH"


def test_single_upload_guard_keeps_refusing_nested_archives():
    s = Settings(auth_mode="off")
    try:
        check_archive(fx.zip_of({"two.docx": fx.docx()}), s)
    except ProblemError as exc:
        assert exc.code == "ARCHIVE_LIMIT"
    else:
        raise AssertionError("a ZIP holding a ZIP must stay refused outside the batch path")
