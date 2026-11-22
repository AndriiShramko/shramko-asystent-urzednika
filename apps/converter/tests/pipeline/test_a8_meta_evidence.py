"""A8 VB-4 (B16, WP-F14b): the sidecar says where each field of the matter stands on the paper.

The review page reads `meta.evidence[<form id>]` (apps/review-web/src/lib/model.ts:90) for the page and the quote of
a field; the pipeline wrote no `evidence`, so every field of the matter showed "no place on the paper found" although
the brief carries page, box and quote for each of them.
"""
from __future__ import annotations

import io

import pytest

from app.config import Settings
from app.model.sidecar import Sidecar
from app.pipeline import run

SETTINGS = Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false"})


def _pdf(lines: list[str]) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, invariant=1)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(120, 780, "Wniosek o wydanie zaswiadczenia")
    c.setFont("Helvetica", 10)
    y = 720
    for text in lines:
        c.drawString(56, y, text)
        y -= 28
    c.save()
    return buf.getvalue()


def _matter_ids(sidecar: dict) -> set[str]:
    return {fid for fid, origin in sidecar["meta"]["origins"].items()
            if origin == "paper" and fid in sidecar["meta"]["brief_keys"]}


def test_each_field_of_the_matter_has_its_place_on_the_paper() -> None:
    sc = run(_pdf(["Imie i nazwisko ........................................",
                   "Cel wydania zaswiadczenia ............................."]), "x.pdf", SETTINGS).sidecar
    assert sc["converter"]["pipeline"] == "brief"
    ids = _matter_ids(sc)
    assert ids, "the synthetic paper gave no field of the matter"
    evidence = sc["meta"].get("evidence", {})
    assert ids <= set(evidence), "fields of the matter without meta.evidence"
    for fid in ids:
        rec = evidence[fid][0]
        assert rec["page"] == 1 and rec["quote"]
    assert set(evidence) <= set(sc["meta"]["brief_keys"])   # never a standard field
    Sidecar.model_validate(sc)


def test_interim_path_writes_no_evidence() -> None:
    sc = run(_pdf([]), "x.pdf", SETTINGS).sidecar
    assert sc["converter"]["pipeline"] == "interim"
    assert "evidence" not in sc["meta"]


def test_judged_sets_have_evidence_for_every_matter_field() -> None:
    from tools.coi_paths import sets

    folders = list(sets("judged"))
    if not folders:
        pytest.skip("the judged sets are not on this machine")
    for folder in folders:
        pick = next((f for f in sorted(folder.iterdir()) if f.suffix.lower() == ".pdf"), None)
        if pick is None:
            continue
        sc = run(pick.read_bytes(), pick.name, SETTINGS).sidecar
        if sc["converter"]["pipeline"] != "brief":
            continue
        missing = _matter_ids(sc) - set(sc["meta"].get("evidence", {}))
        assert not missing, (folder.name, len(missing))
        Sidecar.model_validate(sc)
