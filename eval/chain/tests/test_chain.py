"""Tests of the check chain on synthetic fixtures: each outcome class, the compare step, the sample, the image mode."""
from __future__ import annotations

import json
import struct
import subprocess
from pathlib import Path

import pytest

from eval.chain import __main__ as chain_main
from eval.chain import corpora, hostile, report, runner, worker


def _item(path: Path, corpus: str = "sets") -> corpora.Item:
    return corpora.Item(corpus, "k" + path.stem[:8], path, path.name, corpora.fmt_of(path.name))


@pytest.fixture()
def good_pdf(tmp_path) -> Path:
    canvas = pytest.importorskip("reportlab.pdfgen.canvas")
    p = tmp_path / "blank.pdf"
    c = canvas.Canvas(str(p))
    c.drawString(72, 780, "Wniosek o wydanie zaswiadczenia")
    c.drawString(72, 740, "Imie i nazwisko: ..............................")
    c.drawString(72, 700, "Adres: ..............................")
    c.save()
    return p


def _row(corpus="sets", key="a", outcome="converted", gate="passed", lint=0, fields=10, fmt="pdf", **kw):
    return {"corpus": corpus, "key": key, "format": fmt, "outcome": outcome, "gate": gate, "lint_errors": lint,
            "fields": fields, "fields_matter": 0, "no_label": 0, "warnings": {}, "error": kw.get("error", ""), "seconds": 0.1}


# --- outcome classes -------------------------------------------------------------------------------------------

def test_converted(good_pdf):
    rec = runner.run_native(_item(good_pdf))
    assert rec["outcome"] == "converted" and rec["gate"] == "passed" and rec["lint_errors"] == 0 and rec["fields"] > 0


def test_refused_with_polish_reason(tmp_path):
    p = tmp_path / "text.pdf"
    p.write_bytes(b"plain text, not a pdf\n" * 10)
    rec = runner.run_native(_item(p))
    assert rec["outcome"] == "refused" and rec["error"] == ""


def test_refusal_without_polish_reason_is_failed(tmp_path, monkeypatch):
    from app import guard

    def refuse(*a, **k):
        raise guard.ProblemError("UNREADABLE", "")
    monkeypatch.setattr(guard, "inspect_upload", refuse)
    p = tmp_path / "x.pdf"
    p.write_bytes(b"%PDF-1.4")
    rec = worker.classify(p, "x.pdf")
    assert rec["outcome"] == "failed" and rec["error"].startswith("RefusalWithoutPolishReason")


def test_gate_failure_is_failed(tmp_path, monkeypatch, good_pdf):
    from app import guard, pipeline

    def broken(*a, **k):
        raise guard.ProblemError("GATE_FAILED", "Bramka G1 schema odrzuciła wynik")
    monkeypatch.setattr(pipeline, "run", broken)
    rec = worker.classify(good_pdf, good_pdf.name)
    assert rec["outcome"] == "failed" and rec["gate"] == "failed"


def test_forced_exception_is_failed_and_exit_nonzero(good_pdf, monkeypatch, tmp_path, capsys):
    """Negative control: a fixture forced to raise inside the pipeline is `failed` and the chain exits non-zero."""
    monkeypatch.setenv("CHAIN_FAULT", "raise")
    rec = runner.run_native(_item(good_pdf))
    assert rec["outcome"] == "failed" and rec["error"] == "RuntimeError"
    monkeypatch.setattr(chain_main, "collect", lambda names, archive: [_item(good_pdf)])
    monkeypatch.setattr(report, "LAST_RUN", tmp_path / "l.jsonl")
    monkeypatch.setattr(report, "SUMMARY", tmp_path / "s.json")
    assert chain_main.main(["--corpus", "sets"]) == 1
    assert "FAILED" in capsys.readouterr().out


def test_timeout_is_failed(good_pdf):
    rec = runner.run_native(_item(good_pdf), timeout=0.05)
    assert rec["outcome"] == "failed" and rec["error"] == "Timeout"


def test_worker_crash_is_failed(tmp_path):
    p = tmp_path / "x.pdf"
    p.write_bytes(b"x")
    rec = runner.run_native(_item(p), env={"PYTHONPATH": str(tmp_path)})  # the code is not importable: no JSON line
    assert rec["outcome"] == "failed" and rec["error"].startswith("WorkerCrash")


# --- compare ---------------------------------------------------------------------------------------------------

def test_compare_same_run_is_clean():
    rows = [_row(key="a"), _row(key="b", corpus="hostile", outcome="refused", fields=0)]
    bad, good, _, fatal = report.compare(rows, report.to_baseline(rows))
    assert bad == [] and good == [] and fatal == []


def test_compare_flags_regressions():
    base = report.to_baseline([_row(key="a", fields=10), _row(key="b", fields=10), _row(key="c")])
    worse, _, _, fatal = report.compare([_row(key="a", fields=7), _row(key="b", outcome="failed", error="X"),
                                         _row(key="c", gate="failed")], base)
    assert len(worse) == 3 and len(fatal) == 3


def test_baseline_with_one_more_field_reports_worse_but_not_fatal():
    """Negative control: the baseline says 11 fields, the run finds 10 (a fall of under 20 %): listed as worse,
    not fatal; a fall of over 20 % on a file of the sets is fatal."""
    rows = [_row(key="a", fields=10)]
    base = report.to_baseline(rows)
    base["files"]["sets:a"]["fields"] = 11
    worse, good, notes, fatal = report.compare(rows, base)
    assert any("fields 11 -> 10" in w for w in worse) and fatal == []
    base["files"]["sets:a"]["fields"] = 13
    worse, _, _, fatal = report.compare(rows, base)
    assert any("fall over 20 %" in w for w in fatal)


def test_compare_fall_on_unseen_is_worse_not_fatal():
    rows = [_row(corpus="unseen", key="a", fields=2)]
    base = report.to_baseline([_row(corpus="unseen", key="a", fields=10)])
    worse, _, _, fatal = report.compare(rows, base)
    assert len(worse) == 1 and fatal == []


def test_compare_converted_to_refused_is_fatal_on_any_file():
    rows = [_row(corpus="unseen", key="a", outcome="refused", fields=0)]
    base = report.to_baseline([_row(corpus="unseen", key="a", fields=9)])
    worse, _, _, fatal = report.compare(rows, base)
    assert len(fatal) == 1 and any("converted, now refused" in w for w in worse)


def test_compare_lint_increase_is_worse_not_fatal():
    base = report.to_baseline([_row(key="a")])
    worse, _, _, fatal = report.compare([_row(key="a", lint=2)], base)
    assert len(worse) == 1 and fatal == []


def test_exit_code_follows_fatal_list(tmp_path, monkeypatch):
    import json
    from eval.chain import __main__ as cli
    rows = [_row(key="a", fields=10)]
    bl = report.to_baseline(rows)
    bl["files"]["sets:a"]["fields"] = 11
    f = tmp_path / "baseline.json"
    f.write_text(json.dumps(bl), encoding="utf-8")
    monkeypatch.setattr(report, "BASELINE", f)
    assert cli._exit_for(rows) == 0
    bl["files"]["sets:a"]["fields"] = 20
    f.write_text(json.dumps(bl), encoding="utf-8")
    assert cli._exit_for(rows) == 1


def test_compare_improvement_and_new_failure():
    base = report.to_baseline([_row(key="a", fields=5), _row(key="b", outcome="failed", error="X")])
    bad, good, _, _ = report.compare([_row(key="a", fields=9), _row(key="b"), _row(key="new", outcome="failed", error="Y")], base)
    assert len(good) == 2 and len(bad) == 1


def test_summary_totals_per_corpus_and_format():
    rows = [_row(key="a"), _row(key="b", fmt="docx", outcome="refused"), _row(corpus="hostile", key="c", outcome="failed", error="E")]
    s = report.summarize(rows)
    assert s["total"]["files"] == 3 and s["total"]["failed"] == 1
    assert s["corpora"]["sets"]["formats"]["docx"]["refused"] == 1
    assert "name" not in json.dumps(s)


# --- corpora ---------------------------------------------------------------------------------------------------

def test_sample_tops_up_to_the_minimum(tmp_path, monkeypatch):
    for fmt in ("pdf", "docx"):
        for i in range(60):
            (tmp_path / f"n{i}.{fmt}").write_bytes(f"{fmt}-{i}".encode() * 3)
    (tmp_path / "x.rtf").write_bytes(b"rtf")
    s = corpora.build_sample(tmp_path, seed=3)
    assert s["total"] == corpora.MIN_TOTAL and sum(f["format"] == "rtf" for f in s["files"]) == 1


def test_sample_is_seeded_capped_and_hashes_names(tmp_path, monkeypatch):
    monkeypatch.setattr(corpora, "MIN_TOTAL", 0)
    for fmt in ("pdf", "png", "xlsx"):
        for i in range(20):
            (tmp_path / f"secret-name-{i}.{fmt}").write_bytes(f"{fmt}-{i}".encode() * 3)
    a = corpora.build_sample(tmp_path, seed=1)
    b = corpora.build_sample(tmp_path, seed=1)
    c = corpora.build_sample(tmp_path, seed=2)
    assert a == b and a != c
    assert a["total"] == 45 and all(sum(f["format"] == fm for f in a["files"]) == 15 for fm in ("pdf", "png", "xlsx"))
    assert "secret-name" not in json.dumps(a)
    spec = tmp_path / "sample.json"
    spec.write_text(json.dumps(a), encoding="utf-8")
    items = corpora.unseen_items(tmp_path, spec)
    assert len(items) == 45 and all("secret" not in i.name for i in items)
    (tmp_path / "secret-name-0.pdf").unlink()
    (tmp_path / "secret-name-1.pdf").unlink()
    with pytest.raises(FileNotFoundError):
        corpora.unseen_items(tmp_path, spec)


def test_hostile_corpus_is_built_and_every_file_is_handled(tmp_path):
    files = hostile.build(tmp_path)
    assert len(files) == 7
    head = files["huge-header.png"].read_bytes()
    assert struct.unpack(">II", head[16:24]) == (100_000, 100_000) and len(head) < 200
    assert files["zip-bomb.docx"].stat().st_size < 5_000_000
    for name in ("text-named-pdf.pdf", "empty.pdf", "pixel.png", "huge-header.png"):
        assert runner.run_native(_item(files[name], "hostile"))["outcome"] in ("refused", "converted"), name


# --- image mode (docker mocked) ----------------------------------------------------------------------------------

def _completed(code, out="", err=""):
    return subprocess.CompletedProcess([], code, out, err)


def test_image_command_has_no_network_and_read_only(tmp_path):
    p = tmp_path / "a.pdf"
    p.write_bytes(b"x")
    cmd = runner.docker_command("img:1", _item(p))
    assert cmd[:2] == ["docker", "run"] and "--network" in cmd and cmd[cmd.index("--network") + 1] == "none"
    assert "--read-only" in cmd and cmd[-5:-1] == ["python", "-m", "converter", "convert"]


def test_image_outcomes(tmp_path):
    p = tmp_path / "a.pdf"
    p.write_bytes(b"x")
    it = _item(p)
    refusal = json.dumps({"code": "UNREADABLE", "detail": "Plik jest uszkodzony."})
    assert runner.run_image(it, "i", runner=lambda *a, **k: _completed(2, err=refusal))["outcome"] == "refused"
    nodetail = json.dumps({"code": "UNREADABLE"})
    assert runner.run_image(it, "i", runner=lambda *a, **k: _completed(2, err=nodetail))["outcome"] == "failed"
    gate = json.dumps({"code": "GATE_FAILED", "detail": "Bramka"})
    assert runner.run_image(it, "i", runner=lambda *a, **k: _completed(2, err=gate))["gate"] == "failed"
    assert runner.run_image(it, "i", runner=lambda *a, **k: _completed(137))["error"] == "ContainerExit137"
    assert runner.run_image(it, "i", runner=lambda *a, **k: _completed(0, out="not json"))["error"] == "BadOutput"

    def slow(*a, **k):
        raise subprocess.TimeoutExpired("docker", 1)
    assert runner.run_image(it, "i", runner=slow)["error"] == "Timeout"
