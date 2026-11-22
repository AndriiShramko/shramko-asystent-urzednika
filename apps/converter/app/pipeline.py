"""The ONE seam between the service shell and the reading pipeline.

`run(data, filename, settings)` takes the bytes of a file the guard has already accepted and returns the form (the
partner's object, decision D1) and the sidecar (decision D2). The steps: the format from the guard's proof of
content, `read_document`, `app.find` and `app.mean` (the brief; `app.interim` only when the finder yields no candidate), `compose`. A failure is
a `ProblemError` of design section 3, which the HTTP shell and the command line already turn into an answer: no stack
trace, no content of the file. No endpoint, no command and no test of the shell reaches past this function.
"""
from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass

from app import __version__, gate, interim
from app.find import find
from app.mean import understand
from app.model.ledger import LedgerError, assemble_ledger
from app.compose import ComposeError, compose, dictionaries
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
    if exc.code == "NO_DECODER":   # a laptop install without heif-dec; the user is never asked to re-save the file
        return ProblemError("UNREADABLE", "Ta instalacja nie ma dekodera HEIC.")
    if exc.code == "ENCRYPTED" and "PDF" in exc.reason:
        return ProblemError("UNREADABLE", "Plik PDF jest chroniony hasłem otwarcia; usługa nie zna hasła.")
    if exc.code == "ENCRYPTED":
        return ProblemError("UNREADABLE", "Plik jest zaszyfrowany lub chroniony hasłem; nie można go odczytać.")
    if exc.code == "UNSUPPORTED_FORMAT":
        return ProblemError("EXTENSION", "Ta wersja usługi nie ma czytnika tego formatu.")
    return ProblemError("UNREADABLE", "Nie udało się odczytać pliku: jest uszkodzony lub nie ma tekstu do odczytu.")


def _count_fields(form: dict) -> int:
    return sum(len(q["field"]["repeatingSectionGrid"]) for t in form["tabs"] for q in t["questions"])


_NO_QUOTES = re.compile(r"'[^']*'|\"[^\"]*\"")   # a message may quote a value of the form; the place is enough
_EXC_TEXT = re.compile(r"\b([A-Z]\w*(?:Error|Exception|Warning)|KeyError|StopIteration)\b: .*")   # a crash: its type only
# coi_lint's "page title/techName: rule" (greedy to the last "/techName: ", so a title holding a colon goes too; when a
# quoted value holds "a/b: " more of the rule goes, never text of the document) or "techName: rule"
_PLACE_HEAD = re.compile(r"^(?:.*/[^/:\s]*|[A-Za-z0-9_]+): ")


def _safe_message(message: str) -> str:
    """A finding without text of the document: no exception message, no place head (titles), no quoted value.
    The rule stays, and the place is the JSON pointer next to it (audit-8 VC-3, 06-F11)."""
    m = _EXC_TEXT.sub(lambda x: x.group(1), message)
    m = _PLACE_HEAD.sub("", m)
    return _NO_QUOTES.sub("'...'", m)


def _gate_problem(failed: gate.CheckResult) -> ProblemError:
    """500 GATE_FAILED: the id and name of the check and its first findings (a place and a rule, 1000 characters at most)."""
    shown = "; ".join(f"{_safe_message(f.message)} at {f.path or '/'}" for f in failed.findings[:5])
    more = f" (+{len(failed.findings) - 5} more)" if len(failed.findings) > 5 else ""
    return ProblemError("GATE_FAILED", f"Bramka {failed.id} {failed.name} odrzuciła wynik: {shown}{more}"[:1000])


BLOCKING_CHECKS = frozenset({"G1", "G2", "G3", "G4"})   # D19: schema, partner rules, grid, ids and links


def _gate_warning(check: gate.CheckResult) -> dict:
    """A failed non-blocking check as a warning: the code of the check, the places (no values), Polish and short."""
    places = ", ".join(dict.fromkeys(f.path or "/" for f in check.findings[:3]))
    more = f" (łącznie {len(check.findings)})" if len(check.findings) > 3 else ""
    return {"code": f"GATE_{check.id}",
            "detail": f"Kontrola {check.id} ({check.name}) zgłosiła uwagi w miejscach: {places}{more}."[:300]}


_abandoned: list[threading.Thread] = []   # jobs whose caller got 504 and which are still running
_abandoned_lock = threading.Lock()


def run_limited(data: bytes, filename: str, settings: Settings, notes: tuple[str, ...] = ()) -> PipelineResult:
    """`run` under `settings.job_timeout_s`: the job runs in a daemon thread and the caller stops waiting when the
    time is up (504 TIMEOUT). A thread cannot be killed, so the abandoned job ends by itself; the normal path is
    unchanged, so the bytes are too. Abandoned jobs still use a processor, so they count against the slots: while
    `settings.concurrency` or more of them are alive no new job starts (429 BUSY) and the pile cannot grow."""
    with _abandoned_lock:
        _abandoned[:] = [t for t in _abandoned if t.is_alive()]
        if len(_abandoned) >= settings.concurrency:
            raise ProblemError("BUSY", "Poprzednie zadania przekroczyły limit czasu i jeszcze się kończą.",
                               headers={"Retry-After": "30"})
    box: dict = {}
    args = (data, filename, settings, notes) if notes else (data, filename, settings)

    def work() -> None:
        try:
            box["result"] = run(*args)
        except BaseException as exc:   # handed to the caller, which re-raises it
            box["error"] = exc

    th = threading.Thread(target=work, name="convert-job", daemon=True)
    th.start()
    th.join(settings.job_timeout_s)
    if th.is_alive():
        with _abandoned_lock:
            _abandoned.append(th)
        raise ProblemError("TIMEOUT", f"Przetwarzanie pliku trwało dłużej niż {settings.job_timeout_s} s; wynik nie zostanie zwrócony, a zadanie kończy się w tle.")
    if "error" in box:
        raise box["error"]
    return box["result"]


def _checks_of(report: gate.GateReport) -> list[dict]:
    return [{"id": c.id, "name": c.name, "status": c.status, **({"reason": c.reason} if c.reason else {})}
            for c in report.checks]


_EVIDENCE_KEYS = ("page", "box", "anchor", "quote", "candidate", "runs")


def _field_evidence(brief, brief_keys: dict[str, str]) -> dict[str, list[dict]]:
    """A8 VB-4: form id -> where the field of the matter stands on the paper, in the shape of meta FieldEvidence.

    Only the keys FieldEvidence knows are kept (no `spans`), and a record that locates nothing (no quote, box or
    anchor) is left out, so the sidecar keeps its contract (sidecar.schema.json).
    """
    by_key = {f.key: f.evidence for s in brief.matter for f in s.fields if f.key}
    by_key.update({a.key: a.evidence for a in brief.attachments if a.key and a.key not in by_key})
    out: dict[str, list[dict]] = {}
    for fid, key in brief_keys.items():
        recs = []
        for e in by_key.get(key) or ():
            d = {k: v for k, v in e.model_dump(mode="json", exclude_none=True).items() if k in _EVIDENCE_KEYS and v != []}
            if "quote" in d or "box" in d or "anchor" in d:
                recs.append(d)
        if recs:
            out[fid] = recs
    return out


def _form_ids(form: dict, brief, brief_keys: dict[str, str]) -> dict[str, str]:
    """Brief key -> form id: the inverse of `ComposeResult.brief_keys`. The composer does not carry the key of an
    attachment (request to lead), so an upload is found by its title among the uploaders of the form."""
    ids = {key: fid for fid, key in brief_keys.items()}
    uploads: dict[str, str] = {}
    for tab in form["tabs"]:
        for q in tab["questions"]:
            for cell in q["field"]["repeatingSectionGrid"]:
                if cell["field"]["type"] == "FILE_UPLOADER":
                    uploads.setdefault(cell["field"]["title"], cell["field"]["id"])
    for a in brief.attachments:
        if a.key and a.key not in ids and a.label in uploads:
            ids[a.key] = uploads[a.label]
    return ids


def run(data: bytes, filename: str, settings: Settings, notes: tuple[str, ...] = ()) -> PipelineResult:
    """`filename` is not used: the format comes from the content, and a name must never reach a log.
    `notes` are the Polish sentences of the guard (`UploadInfo.warnings`: the extension disagreed with the content, a
    file name was cleaned); they travel into the warnings of the sidecar as they are."""
    fmt = _format_of(data, settings)
    if fmt not in formats():
        if fmt == "heic":   # the reader comes with WP-F20f stage 1b; the user is never asked to re-save the file
            raise ProblemError("UNREADABLE", "Ta instalacja nie ma dekodera HEIC.")
        label = KIND_LABEL.get(fmt, fmt)
        raise ProblemError("UNREADABLE", f"Ta wersja usługi nie potrafi jeszcze czytać tego formatu ({label}).")
    try:
        model = read_document(data, fmt, read_options(settings))
    except ReaderError as exc:
        raise _problem_of(exc) from None
    finder = find(model)
    rules = _finish(model, finder, settings, notes)
    if not vision_on(settings):
        return rules
    return _with_vision(model, finder, settings, notes, rules)


def vision_on(settings: Settings | None = None) -> bool:
    """The weak page reader is configured (VISION_MODE auto with a URL and a key, MODEL_STEP not off). Nothing
    configured: the model path never runs and the output is byte-identical to the rules."""
    from app.vision import VisionConfig

    if settings is not None and getattr(settings, "model_step", "auto") == "off":
        return False
    return VisionConfig.from_env().configured


def _with_vision(model, finder, settings: Settings, notes: tuple[str, ...], rules: PipelineResult,
                 cfg=None, post=None) -> PipelineResult:
    """ORDER M2 P1: weak OCR pages -> the model names label, option and heading lines by number -> synthetic
    marks -> the same finder, brief, composer and gate. All or nothing: any failure returns the rules' result with
    one FALLBACK warning in the sidecar; the form bytes are the rules' bytes."""
    from app import vision
    from app.vision import merge as vmerge

    cfg = cfg or vision.VisionConfig.from_env()
    # the model can never cause a 504: its whole budget stays well inside the job's time limit
    budget = min(cfg.deadline_s, max(5.0, settings.job_timeout_s / 2))
    if budget < cfg.deadline_s:
        from dataclasses import replace

        cfg = replace(cfg, deadline_s=budget)
    try:
        pages = vmerge.weak_pages(model, finder, cfg.max_pages, cfg.trigger)
        if not pages:
            vision._set_state("ON", "", cfg.model)
            return rules
        by_no = {p.number: p for p in model.pages}
        jobs = {n: vmerge.numbered(by_no[n]) for n in pages}
        jobs = {n: ls for n, ls in jobs.items() if 0 < len(ls) <= vision.MAX_LINES}
        if not jobs:
            vision._set_state("ON", "", cfg.model)
            return rules
        answers = vision.ask_pages(cfg, jobs, post=post)
        merged, added = vmerge.merge(model, answers)
        if not added:
            vision._set_state("ON", "", cfg.model)
            return _note(rules, "MODEL_USED", f"model {cfg.model}: pages {sorted(jobs)}, nothing added", cfg, sorted(jobs), 0)
        finder2 = find(merged)
        if len(finder2.candidates) < len(finder.candidates):
            raise vision.VisionError("fewer_places")
        result = _finish(merged, finder2, settings, notes)
    except Exception as exc:   # noqa: BLE001 - the model path never fails a request
        reason = getattr(exc, "reason", None) or ("gate" if isinstance(exc, ProblemError) else type(exc).__name__)
        vision._set_state("FALLBACK", reason, cfg.model)
        return _note(rules, "MODEL_FALLBACK", f"model step skipped ({reason}); the result comes from the rules", cfg, [], 0,
                     state="FALLBACK", reason=reason)
    vision._set_state("ON", "", cfg.model)
    return _note(result, "MODEL_USED",
                 f"model {cfg.model} read {len(jobs)} weak page(s) and marked {added} line(s); fields added there come "
                 "from the open model and should be checked", cfg, sorted(jobs), added)


def _note(res: PipelineResult, code: str, detail: str, cfg, pages: list[int], added: int, state: str = "ON",
          reason: str = "") -> PipelineResult:
    from app.vision import PROMPT_VERSION, prompt_hash

    side = dict(res.sidecar)
    side["warnings"] = [*side["warnings"], {"code": code, "detail": detail[:300]}]
    meta = dict(side["meta"])
    meta["vision"] = {"state": state, "model": cfg.model, "pages": pages, "added": added,
                      "prompt": f"{PROMPT_VERSION}:{prompt_hash(cfg.model)}", **({"reason": reason} if reason else {})}
    side["meta"] = meta
    return PipelineResult(form=res.form, sidecar=side)


def _finish(model, finder, settings: Settings, notes: tuple[str, ...] = ()) -> PipelineResult:
    """Finder output -> brief -> form -> gate -> sidecar (the rules' path after reading)."""
    fallback = not finder.candidates
    if fallback:
        brief = interim.brief_from_pages(model)
    else:
        brief = understand(model, finder)
    try:
        composed = compose(brief, compose_options(settings))
    except ComposeError as exc:
        raise ProblemError("GATE_FAILED", f"Kompozytor odrzucił wynik ({type(exc).__name__}).") from None
    form = json.loads(composed.form.to_json_bytes())
    report = gate.check(form)
    blocking = [c for c in report.failed if c.id in BLOCKING_CHECKS]
    if blocking:   # D19: only G1 to G4 are our fault (500); a failed G5 to G12 is a warning of a 200
        raise _gate_problem(blocking[0])
    warnings = [{"code": "INPUT_NOTE", "detail": n} for n in notes]
    warnings += [_gate_warning(c) for c in report.failed]
    warnings += [w.model_dump(mode="json", exclude_none=True) for w in model.warnings]
    if fallback:
        warnings.append(dict(interim.NOT_READ_WARNING))
    else:
        # A REQUIRED the composer did not write must not keep the brief's "marked required by our rule" warning.
        dropped = set(composed.required_dropped)
        warnings += [w.model_dump(mode="json", exclude_none=True) for w in (*finder.warnings, *brief.warnings)
                     if not (w.code == "REQUIRED_INFERRED" and w.field in dropped)]
    warnings += [{"code": r.code, "detail": r.detail, **({"field": r.field} if r.field else {})} for r in composed.remarks]
    meta: dict = {"origins": composed.origins, "brief_keys": composed.brief_keys}
    # A8 VB-4 (B16): where each field of the matter stands on the paper (page, box, quote), keyed by form id, as
    # meta.schema.json `evidence` 1.1 has it; the review page shows the snippet from here.
    try:   # evidence is a courtesy of the review page: a slip here must never cost the form
        evidence = _field_evidence(brief, composed.brief_keys)
    except Exception:  # noqa: BLE001
        evidence = {}
    if evidence:
        meta["evidence"] = evidence
    if not fallback:
        try:
            ledger = assemble_ledger(finder, brief.dispositions, _form_ids(form, brief, composed.brief_keys))
            meta["ledger"] = ledger.model_dump(mode="json", exclude_none=True)
        except LedgerError:
            warnings.append({"code": "LEDGER_NOT_CLOSED", "detail": "the account of the blanks could not be closed"})
    meta.update(dictionaries.sidecar_extras(brief, composed.brief_keys))   # A8 DX: points I and II; empty = no key
    sidecar = {
        "version": 1,
        "converter": {"version": __version__, "pipeline": "interim" if fallback else "brief", "reader": model.source.reader},
        "counts": {"pages": len(form["tabs"]), "fields": _count_fields(form), "source_pages": model.source.pages},
        "warnings": warnings,
        "checks": _checks_of(report),
        "meta": meta,
    }
    return PipelineResult(form=form, sidecar=sidecar)
