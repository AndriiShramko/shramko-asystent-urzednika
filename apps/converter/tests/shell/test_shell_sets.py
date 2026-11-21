"""Integration with the partner's task sets (local only; skipped where they are absent): the guard must accept
every real file of the judged and reference sets under its own extension, and the shell must answer 200 with a
form that passes the linter. Nothing from the files is printed or copied; assertion messages carry set and suffix."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import factory as fx
from app.config import Settings
from app.guard import inspect_upload
from app.main import create_app
from tools import coi_lint
from tools.coi_paths import sets

pytestmark = pytest.mark.sets

SUFFIXES = {".pdf", ".doc", ".docx", ".ods", ".xlsx", ".jpg", ".jpeg", ".png"}


def _files():
    out = []
    for folder in sets("judged") + sets("reference"):
        for f in sorted(folder.iterdir()):
            if f.suffix.lower() in SUFFIXES and "wizualizacja" not in f.name and not f.stem.endswith("(1)"):
                out.append(pytest.param(f, id=f"{folder.name[:12]}{f.suffix.lower()}"))
    return out


SETTINGS = Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000"})


@pytest.mark.parametrize("path", _files())
def test_the_guard_accepts_every_real_file_by_its_own_extension(path):
    info = inspect_upload(path.name, path.read_bytes(), SETTINGS)
    assert info.name


def test_every_format_of_every_set_converts_to_a_form_that_passes_the_linter():
    client = TestClient(create_app(SETTINGS))
    done = 0
    for p in _files():
        f = p.values[0]
        body, ctype = fx.multipart([("file", f.name, f.read_bytes(), "application/octet-stream")])
        r = client.post("/v1/forms/convert", content=body, headers={"Content-Type": ctype})
        assert r.status_code == 200, f"{p.id}: {r.status_code} {r.json().get('code')}"
        errors = [m for k, m in coi_lint.lint(r.json()) if k == "ERROR"]
        assert not errors, f"{p.id}: {len(errors)} linter errors"
        done += 1
    assert done >= 50  # nine sets with eight formats each, less the files that are not forms
