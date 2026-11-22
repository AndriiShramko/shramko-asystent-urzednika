"""A8 VB-1 (analysis 13-F1): the sidecar the pipeline returns has a published contract and keeps it.

`contracts/coi/meta.schema.json` is the design 5.4 target (hashes, receipts, coverage, legal basis), which no run
writes yet. The sidecar of `/v1/convert` and of `results/*/meta.json` is a different document: `version`,
`converter`, `counts`, `warnings`, `checks`, `meta`. These tests hold that shape to `contracts/coi/sidecar.schema.json`
(written from `app.model.sidecar.Sidecar`) and every warning code the pipeline can emit to `WarningCode`.
"""
from __future__ import annotations

import io
import json
from pathlib import Path
from typing import get_args

import pytest
from jsonschema import Draft202012Validator

from app.config import Settings
from app.model.common import WarningCode
from app.pipeline import run

ROOT = Path(__file__).resolve().parents[4]
SCHEMA = ROOT / "contracts" / "coi" / "sidecar.schema.json"
SETTINGS = Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false"})

# Every code the pipeline itself writes (pipeline.py, interim.NOT_READ_WARNING), besides the codes of the steps.
PIPELINE_CODES = {"INPUT_NOTE", "LEDGER_NOT_CLOSED", "BRIEF_NOT_READ"} | {f"GATE_G{i}" for i in range(5, 13)}


def _validator() -> Draft202012Validator:
    assert SCHEMA.is_file(), "contracts/coi/sidecar.schema.json is missing: the returned sidecar has no contract"
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _errors(doc: dict) -> list[str]:
    return sorted(f"{'/'.join(map(str, e.path)) or '/'}: {e.message[:160]}" for e in _validator().iter_errors(doc))


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


def test_every_pipeline_warning_code_is_a_known_code() -> None:
    assert PIPELINE_CODES - set(get_args(WarningCode)) == set()


def test_schema_file_matches_the_model() -> None:
    from app.model.schemas import schema_for
    from app.model.common import canonical_json

    assert SCHEMA.read_bytes() == canonical_json(schema_for("sidecar"))


@pytest.mark.parametrize("lines", [
    [],   # nothing of the matter: the interim path
    ["Imie i nazwisko ........................................",
     "Adres zamieszkania ....................................",
     "Cel wydania zaswiadczenia ............................."],
], ids=["interim", "brief"])
def test_pipeline_sidecar_keeps_its_contract(lines: list[str]) -> None:
    result = run(_pdf(lines), "x.pdf", SETTINGS, notes=("Rozszerzenie pliku nie zgadza się z treścią.",))
    assert result.sidecar["converter"]["pipeline"] == ("brief" if lines else "interim")
    assert _errors(result.sidecar) == []
    from app.model.sidecar import Sidecar

    Sidecar.model_validate(result.sidecar)


def test_committed_results_keep_the_contract() -> None:
    metas = sorted((ROOT / "results").glob("*/meta.json"))
    assert metas
    bad = {m.parent.name: _errors(json.loads(m.read_text(encoding="utf-8")))[:3] for m in metas}
    assert {k: v for k, v in bad.items() if v} == {}


def test_judged_sets_keep_the_contract() -> None:
    from tools.coi_paths import sets

    folders = list(sets("judged"))
    if not folders:
        pytest.skip("the judged sets are not on this machine")
    for folder in folders:
        pick = next((f for f in sorted(folder.iterdir()) if f.suffix.lower() == ".pdf"), None)
        if pick is None:
            continue
        assert _errors(run(pick.read_bytes(), pick.name, SETTINGS).sidecar) == [], folder.name


def test_dictionary_keys_of_dx_are_part_of_the_contract() -> None:
    """A8 DX-1 and DX-2 write `meta.proposals` and `meta.dictionary_links` (`compose.dictionaries.sidecar_extras`);
    the contract admits them and holds the shape of a link row. No judged set is needed for this."""
    good = run(_pdf([]), "x.pdf", SETTINGS).sidecar
    link = {"field": "kraj", "label": "Kraj", "dictionary": "countries", "written": False, "why": "the paper names a country"}
    extras = {"proposals": {"dictionaries": [{"name": "rodzaj_pojazdu", "entries": ["osobowy", "ciezarowy"]}]},
              "dictionary_links": [link]}
    assert _errors(good | {"meta": good["meta"] | extras}) == []
    broken = {k: v for k, v in link.items() if k != "why"}
    assert _errors(good | {"meta": good["meta"] | {"dictionary_links": [broken]}})
    assert _errors(good | {"meta": good["meta"] | {"proposals": {"dictionaries": [{"entries": ["x"]}]}}})   # no name


def test_negative_controls_are_refused() -> None:
    result = run(_pdf([]), "x.pdf", SETTINGS)
    good = result.sidecar
    assert _errors(good | {"accuracy": 0.97})                                     # an extra top key
    assert _errors(good | {"warnings": [{"code": "MADE_UP", "detail": "x"}]})       # a code nobody declared
    assert _errors(good | {"checks": [{"id": "G1", "name": "schema", "status": "pass"}]})   # meta.schema's word
    del good["counts"]
    assert _errors(good)
