"""WP-F2b integration: the three readers through the service pipeline (format by content, interim brief, gate)."""
from __future__ import annotations

import pytest

from app import pipeline
from app.config import Settings
from app.readers import formats
from tools import coi_lint

from test_sheet_doc_readers import _doc, _form, _ods_form, _xlsx

SETTINGS = Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000"})


def test_the_three_formats_are_registered():
    assert {"xlsx", "ods", "doc"} <= set(formats())


@pytest.mark.parametrize("name,make,reader", [
    ("xlsx", lambda: _xlsx(_form), "xlsx"),
    ("ods", _ods_form, "ods"),
    ("doc", _doc, "doc.flow"),
])
def test_synthetic_file_goes_through_the_pipeline(name, make, reader):
    res = pipeline.run(make(), f"form.{name}", SETTINGS)
    assert res.sidecar["converter"]["reader"] == reader
    assert res.sidecar["counts"]["source_pages"] >= 1
    assert res.form["tabs"], name
    assert [m for k, m in coi_lint.check(res.form, "strict") if k == "ERROR"] == [], name


def test_a_renamed_doc_that_is_ole_goes_by_content():
    res = pipeline.run(_doc(), "scan.docx", SETTINGS)  # wrong suffix: the content decides
    assert res.sidecar["converter"]["reader"] == "doc.flow"


@pytest.mark.sets
@pytest.mark.slow
def test_every_set_file_of_the_new_formats_goes_through_the_pipeline_without_a_crash():
    from eval.golden import golden_inputs, judged_inputs

    from app.guard.problems import ProblemError

    files = [p for p in golden_inputs() + judged_inputs() if p.suffix.lower() in (".xlsx", ".ods", ".doc") and p.exists()]
    if not files:
        pytest.skip("task sets are not on this machine")
    for f in files:
        try:
            res = pipeline.run(f.read_bytes(), f.name, SETTINGS)
        except ProblemError:
            continue  # a stated refusal is allowed; a crash is not
        assert [m for k, m in coi_lint.check(res.form, "strict") if k == "ERROR"] == [], f.parent.name
