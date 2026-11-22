"""Repo rules for the weak page reader (wave 10, ML1R): the product never reads the organizers' gateway key and
never names that gateway; the key comes only from VISION_API_KEY_FILE or VISION_API_KEY; the engine tokens of the
step are exactly the ones the review page understands. No network, no key."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from app import engine, vision

APP = Path(__file__).resolve().parents[2] / "app"
REVIEW_API = Path(__file__).resolve().parents[4] / "apps" / "review-web" / "src" / "lib" / "api.ts"
GATEWAY_KEY = "EDEN" + "AI_API_KEY"   # built here so this file is not itself a hit of the grep below


def _product_sources():
    return [p for p in APP.rglob("*.py") if "__pycache__" not in p.parts]


def test_product_package_never_names_the_gateway_key():
    """AGENTS.md hard rule 2: only tools/eden/eden.py may read that variable; the product package never names it."""
    hits = [str(p.relative_to(APP)) for p in _product_sources() if GATEWAY_KEY in p.read_text(encoding="utf-8")]
    assert hits == []


def test_product_package_never_names_a_gateway_host_or_route():
    """VISION_BASE_URL is the operator's own server: no gateway host or gateway route id appears in the product."""
    pat = re.compile(r"edenai|api\.eden|amazon/qwen", re.IGNORECASE)
    hits = [str(p.relative_to(APP)) for p in _product_sources() if pat.search(p.read_text(encoding="utf-8"))]
    assert hits == []


def test_key_comes_only_from_the_vision_variables(tmp_path):
    only_gateway = {"VISION_BASE_URL": "http://model.invalid/v1", GATEWAY_KEY: "test-not-a-key"}
    assert vision.VisionConfig.from_env(only_gateway).configured is False
    keyfile = tmp_path / "k"
    keyfile.write_text("test-not-a-key-file", encoding="utf-8")
    by_file = vision.VisionConfig.from_env({"VISION_BASE_URL": "http://model.invalid/v1",
                                            "VISION_API_KEY_FILE": str(keyfile)})
    assert by_file.configured is True and "test-not-a-key-file" not in repr(by_file)
    by_var = vision.VisionConfig.from_env({"VISION_BASE_URL": "http://model.invalid/v1", "VISION_API_KEY": "t"})
    assert by_var.configured is True


def test_nothing_configured_has_no_endpoint_and_is_off():
    cfg = vision.VisionConfig.from_env({})
    assert cfg.configured is False and cfg.base_url == "" and vision.status(cfg) == {"state": "OFF"}


def test_engine_tokens_are_the_ones_the_review_page_reads():
    tokens = {"rules", "rules+model", "rules-fallback"}
    assert set(engine.ENGINES) == tokens
    assert engine.engine_of({"warnings": [{"code": "MODEL_USED"}]}) == "rules+model"
    assert engine.engine_of({"warnings": [{"code": "MODEL_FALLBACK"}, {"code": "MODEL_USED"}]}) == "rules-fallback"
    assert engine.engine_of({"warnings": []}) == "rules"
    if not REVIEW_API.exists():
        pytest.skip("review page sources not in this tree")
    m = re.search(r"const ENGINES[^=]*=\s*\[([^\]]*)\]", REVIEW_API.read_text(encoding="utf-8"))
    assert m, "the page's ENGINES list moved"
    assert set(re.findall(r"'([^']+)'", m.group(1))) == tokens
