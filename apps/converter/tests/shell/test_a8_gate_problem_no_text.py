"""AUDIT-8 VC-3 (06-F11): the 500 GATE_FAILED detail names the check, the rule and the place, never text taken from
the document (a page title, a label) and never the message of an exception inside a check."""
from __future__ import annotations

import copy

import factory as fx
from fastapi.testclient import TestClient

import app.gate as gate_mod
import app.gate.structure as structure
from app import pipeline
from app.config import Settings
from app.main import create_app

SENTINEL = "TRESCZFORMULARZA"   # stands for text of the document


def make() -> TestClient:
    env = {"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000"}
    return TestClient(create_app(Settings.from_env(env)))


def convert(client: TestClient):
    return client.post("/v1/forms/convert", files={"file": ("a.pdf", fx.pdf(), "application/pdf")})


def test_a_page_title_from_the_document_does_not_reach_the_500(monkeypatch):
    real = gate_mod.check

    def broken_check(form, *a, **kw):
        bad = copy.deepcopy(form)
        bad["tabs"][1]["title"] = f"{SENTINEL} pana O'Brien"   # an apostrophe makes repr use double quotes
        bad["tabs"][1]["id"] = bad["tabs"][0]["id"]            # G4: "id used twice: ... (page <title>)"
        return real(bad, *a, **kw)

    monkeypatch.setattr(gate_mod, "check", broken_check)
    r = convert(make())
    assert r.status_code == 500 and r.json()["code"] == "GATE_FAILED"
    assert SENTINEL not in r.text and "Brien" not in r.text, r.json()["detail"]
    assert "id used twice" in r.json()["detail"]


def test_the_message_of_a_crashed_check_does_not_reach_the_500(monkeypatch):
    def boom(*a, **kw):
        raise ValueError(f"{SENTINEL} nie pasuje")

    monkeypatch.setattr(gate_mod, "g4_ids", boom)
    r = convert(make())
    assert r.status_code == 500 and r.json()["code"] == "GATE_FAILED"
    assert SENTINEL not in r.text, r.json()["detail"]
    assert "ValueError" in r.json()["detail"]   # the type of the failure stays: it is ours and holds no text


def test_gate_problem_keeps_the_rule_and_the_place():
    failed = gate_mod.CheckResult("G2", "partner_rules", "failed",
                                  [gate_mod.Finding("/tabs/0", f"{SENTINEL}/sec_1: empty section")])
    detail = pipeline._gate_problem(failed).detail
    assert SENTINEL not in detail and "empty section" in detail and "/tabs/0" in detail


def test_a_title_with_a_colon_is_dropped_too():
    # Polish page titles often read "Część A: Dane ..." (review 45, VC-3)
    for msg in (f"Część A: {SENTINEL}/sec_1: empty section",
                f"Część A: {SENTINEL} pana O'Brien/sec_1: unknown initial data 'x/y: z'",
                f"sec_1: unknown initial data '{SENTINEL}'"):
        failed = gate_mod.CheckResult("G2", "partner_rules", "failed", [gate_mod.Finding("/tabs/1", msg)])
        detail = pipeline._gate_problem(failed).detail
        assert SENTINEL not in detail and "Część" not in detail and "Brien" not in detail and "/tabs/1" in detail, detail
    assert "unknown initial data" in detail
