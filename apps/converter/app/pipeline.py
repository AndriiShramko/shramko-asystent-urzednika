"""The ONE seam between the service shell and the reading pipeline.

`run(data, filename, settings)` takes the bytes of a file the guard has already accepted and returns the form (the
partner's object, decision D1) and the sidecar (decision D2). Work package WP-F1 ships a stub: a fixed, valid form
built in code, so the shell, the tests and the image can be proved before any reader exists. Later packages replace
the body of `run` and nothing else: no endpoint, no command and no test of the shell may reach past this function.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from app import __version__
from app.config import Settings

# Namespace of the ids (decision D10). An office may set its own through ID_NAMESPACE.
DEFAULT_NAMESPACE = uuid.UUID("6f1c0a52-3b7e-5d2a-9c41-0d8e7a1b2c3d")


@dataclass(frozen=True)
class PipelineResult:
    form: dict
    sidecar: dict


def _id(ns: uuid.UUID, *parts: str) -> str:
    return str(uuid.uuid5(ns, "/".join(parts)))


def _field(ns: uuid.UUID, scope: str, y: int, tech: str, title: str, ftype: str, description: str = "") -> dict:
    return {
        "x": 0, "y": y, "rows": 1, "cols": 3,
        "field": {
            "id": _id(ns, scope, tech), "type": ftype, "techName": tech, "title": title,
            "description": description, "tooltipMessage": "", "questionOrder": y,
            "options": [], "validation": ["REQUIRED"] if ftype != "TEXT_BLOCK" else [], "readOnly": False,
            "repeatingSectionGrid": [], "states": [],
        },
    }


def _section(ns: uuid.UUID, page: str, y: int, tech: str, title: str, inner: list[dict]) -> dict:
    q = _field(ns, page, y, tech, title, "SECTION", "<html><head></head><body></body></html>")
    q["rows"] = len(inner) + 1
    q["field"]["validation"] = []
    q["field"]["repeatingSectionGrid"] = inner
    return q


def stub_form(settings: Settings) -> dict:
    """A fixed, valid form: a page with one section of two fields, and the closing page with one text block."""
    ns = uuid.UUID(settings.id_namespace) if settings.id_namespace else DEFAULT_NAMESPACE
    key = settings.form_key or "formularz-probny"
    main_id, finish_id = _id(ns, key, "page", "main"), _id(ns, key, "page", "finish")
    data = _section(ns, main_id, 0, "dane_wnioskodawcy", "Dane wnioskodawcy", [
        _field(ns, main_id, 0, "imie", "Imię", "TEXT_FIELD"),
        _field(ns, main_id, 1, "nazwisko", "Nazwisko", "TEXT_FIELD"),
    ])
    done = _section(ns, finish_id, 0, "zakonczenie", "Zakończenie", [
        _field(ns, finish_id, 0, "informacja_koncowa", "Informacja", "TEXT_BLOCK",
               "<html><head></head><body><p>Wniosek został przygotowany do wysłania.</p></body></html>"),
    ])
    return {
        "title": "Formularz próbny",
        "tabs": [
            {"id": main_id, "title": "Dane", "type": "MAIN", "questions": [data]},
            {"id": finish_id, "title": "Zakończenie", "type": "FINISH", "questions": [done]},
        ],
        "flow": {"links": [{"id": _id(ns, key, "link", "main-finish"), "source": main_id, "target": finish_id}]},
    }


def run(data: bytes, filename: str, settings: Settings) -> PipelineResult:
    """Stub body. `data` and `filename` are not read yet; the real pipeline reads the document here."""
    form = stub_form(settings)
    fields = sum(len(q["field"]["repeatingSectionGrid"]) for t in form["tabs"] for q in t["questions"])
    sidecar = {
        "version": 1,
        "converter": {"version": __version__, "pipeline": "stub"},
        "counts": {"pages": len(form["tabs"]), "fields": fields},
        "warnings": [{"code": "PIPELINE_STUB", "detail": "Czytnik formularzy nie jest jeszcze podłączony: to formularz stały."}],
        "meta": {},
    }
    return PipelineResult(form=form, sidecar=sidecar)
