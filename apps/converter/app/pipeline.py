"""The ONE seam between the service shell and the reading pipeline.

`run(data, filename, settings)` takes the bytes of a file the guard has already accepted and returns the form (the
partner's object, decision D1) and the sidecar (decision D2). The steps: the format from the guard's proof of
content, `read_document`, `app.interim.brief_from_pages` (a stand-in until WP-F3 and WP-F4), `compose`. A failure is
a `ProblemError` of design section 3, which the HTTP shell and the command line already turn into an answer: no stack
trace, no content of the file. No endpoint, no command and no test of the shell reaches past this function.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app import __version__, gate, interim
from app.compose import ComposeError, compose
from app.config import Settings, compose_options, read_options
from app.guard import ProblemError
from app.guard.checks import KIND_LABEL, sniff_kinds
from app.readers import ReaderError, formats, read_document


@dataclass(frozen=True)
class PipelineResult:
    form: dict
    sidecar: dict


def _format_of(data: bytes, settings: Settings) -> str:
    """The content kind the guard proves (a `.doc` that holds a DOCX is a DOCX)."""
    kinds = sniff_kinds(data, settings)
    if len(kinds) != 1:
        raise ProblemError("UNREADABLE", "Nie udało się ustalić jednego formatu pliku.")
    return next(iter(kinds))


def _problem_of(exc: ReaderError) -> ProblemError:
    if exc.code == "TOO_LARGE":
        return ProblemError("TOO_LARGE", "Dokument jest większy, niż pozwala ta instalacja (strony lub pamięć).")
    if exc.code == "ENCRYPTED":
        return ProblemError("UNREADABLE", "Plik jest zaszyfrowany lub chroniony hasłem; nie można go odczytać.")
    if exc.code == "UNSUPPORTED_FORMAT":
        return ProblemError("EXTENSION", "Ta wersja usługi nie ma czytnika tego formatu.")
    return ProblemError("UNREADABLE", "Nie udało się odczytać pliku: jest uszkodzony lub nie ma tekstu do odczytu.")


def _count_fields(form: dict) -> int:
    return sum(len(q["field"]["repeatingSectionGrid"]) for t in form["tabs"] for q in t["questions"])


_NO_QUOTES = re.compile(r"'[^']*'")   # a message may quote a value of the form; the place is enough


def _gate_problem(failed: gate.CheckResult) -> ProblemError:
    """500 GATE_FAILED: the id and name of the check and its first findings (a place and a rule, 1000 characters at most)."""
    shown = "; ".join(f"{_NO_QUOTES.sub(chr(39) + '...' + chr(39), f.message)} at {f.path or '/'}" for f in failed.findings[:5])
    more = f" (+{len(failed.findings) - 5} more)" if len(failed.findings) > 5 else ""
    return ProblemError("GATE_FAILED", f"Bramka {failed.id} {failed.name} odrzuciła wynik: {shown}{more}"[:1000])


def _checks_of(report: gate.GateReport) -> list[dict]:
    return [{"id": c.id, "name": c.name, "status": c.status, **({"reason": c.reason} if c.reason else {})}
            for c in report.checks]


def run(data: bytes, filename: str, settings: Settings) -> PipelineResult:
    """`filename` is not used: the format comes from the content, and a name must never reach a log."""
    fmt = _format_of(data, settings)
    if fmt not in formats():
        label = KIND_LABEL.get(fmt, fmt)
        raise ProblemError("UNREADABLE", f"Ta wersja usługi nie potrafi jeszcze czytać tego formatu ({label}).")
    try:
        model = read_document(data, fmt, read_options(settings))
    except ReaderError as exc:
        raise _problem_of(exc) from None
    brief = interim.brief_from_pages(model)
    try:
        composed = compose(brief, compose_options(settings))
    except ComposeError as exc:
        raise ProblemError("GATE_FAILED", f"Kompozytor odrzucił wynik ({type(exc).__name__}).") from None
    form = json.loads(composed.form.to_json_bytes())
    report = gate.check(form)
    if not report.passed:
        raise _gate_problem(report.failed[0])
    warnings = [w.model_dump(mode="json", exclude_none=True) for w in model.warnings]
    warnings.append(dict(interim.NOT_READ_WARNING))
    warnings += [{"code": r.code, "detail": r.detail, **({"field": r.field} if r.field else {})} for r in composed.remarks]
    sidecar = {
        "version": 1,
        "converter": {"version": __version__, "pipeline": "interim", "reader": model.source.reader},
        "counts": {"pages": len(form["tabs"]), "fields": _count_fields(form), "source_pages": model.source.pages},
        "warnings": warnings,
        "checks": _checks_of(report),
        "meta": {"origins": composed.origins, "brief_keys": composed.brief_keys},
    }
    return PipelineResult(form=form, sidecar=sidecar)
