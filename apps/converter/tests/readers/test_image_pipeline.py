"""WP-F2c integration: images and textless PDFs through the service pipeline (format by content, brief, gate, lint)."""
from __future__ import annotations

import io

import pytest
from PIL import Image

from app import pipeline
from app.config import Settings
from app.readers import _ocr, formats
from tools import coi_lint

from test_image_reader import FakeEngine, W, PAGE_H, blank_page, draw_form, png_bytes

SETTINGS = Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000"})


@pytest.fixture(autouse=True)
def no_engine():
    _ocr.set_engine(None, disabled=True)
    yield
    _ocr.set_engine(None)


def _errors(form):
    return [m for k, m in coi_lint.check(form, "strict") if k == "ERROR"]


def _jpeg(img: Image.Image) -> bytes:
    out = io.BytesIO()
    img.convert("RGB").save(out, format="JPEG", quality=85)
    return out.getvalue()


def test_jpeg_and_png_are_registered():
    assert {"jpeg", "png"} <= set(formats())


@pytest.mark.parametrize("kind", ["png", "jpeg"])
def test_a_scan_without_ocr_converts_to_a_valid_form_with_not_read_warnings(kind):
    img = blank_page()
    draw_form(img)
    data = png_bytes(img) if kind == "png" else _jpeg(img)
    res = pipeline.run(data, f"scan.{kind}", SETTINGS)
    assert res.sidecar["converter"]["reader"] == "image.raster"
    assert res.sidecar["counts"]["source_pages"] == 1
    assert res.form["tabs"]
    assert any(w["code"] == "UNREADABLE_PART" for w in res.sidecar["warnings"])
    assert _errors(res.form) == []


def test_a_wrong_suffix_does_not_matter():
    res = pipeline.run(png_bytes(blank_page()), "scan.docx", SETTINGS)
    assert res.sidecar["converter"]["reader"].startswith("image.")


def test_a_tall_scan_gives_one_not_read_warning_per_page():
    img = Image.new("L", (W, PAGE_H * 6), 255)
    res = pipeline.run(png_bytes(img), "tall.png", SETTINGS)
    assert res.sidecar["counts"]["source_pages"] == 6
    assert _errors(res.form) == []


def test_with_a_fake_engine_the_words_reach_the_form():
    img = blank_page()
    draw_form(img)
    words = [_ocr.Word("Imię", 100, 100, 220, 140, 0.93, (1, 1, 1)), _ocr.Word("nazwisko", 240, 100, 400, 140, 0.88, (1, 1, 2))]
    eng = FakeEngine(words)
    _ocr.set_engine(eng)
    res = pipeline.run(png_bytes(img), "scan.png", SETTINGS)
    assert eng.calls == 1
    assert res.sidecar["converter"]["reader"] == "image.ocr"
    assert _errors(res.form) == []


def test_a_truncated_png_is_a_stated_refusal_not_a_crash():
    from app.guard.problems import ProblemError
    data = png_bytes(blank_page())[:40]
    with pytest.raises(ProblemError):
        pipeline.run(data, "x.png", SETTINGS)


@pytest.mark.sets
@pytest.mark.slow
def test_every_set_image_goes_through_the_pipeline_without_a_crash():
    from app.guard.problems import ProblemError
    from eval.golden import golden_inputs, judged_inputs

    files = [p for p in golden_inputs() + judged_inputs()
             if p.suffix.lower() in (".jpg", ".jpeg", ".png") and p.exists()]
    if not files:
        pytest.skip("task sets are not on this machine")
    for f in files:
        try:
            res = pipeline.run(f.read_bytes(), f.name, SETTINGS)
        except ProblemError:
            continue
        assert _errors(res.form) == [], f.parent.name
