"""OCR behind one interface (design 6.2.2, 9.3): Tesseract as a program in a subprocess, word boxes and confidence
from its TSV output. A second engine, or a fake one in tests, is anything with `read(png, lang, timeout)`.

The product never calls out of the container: the program is local, runs with a timeout, and gets a temporary file.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class OcrError(Exception):
    """The engine could not read this strip: the page is then reported as "not read", never a crash."""


@dataclass(frozen=True)
class Word:
    text: str
    x0: int
    y0: int
    x1: int
    y1: int
    conf: float  # 0..1
    line: tuple[int, int, int] = (0, 0, 0)  # block, paragraph, line numbers of the engine


class OcrEngine(Protocol):
    name: str

    def read(self, png: bytes, lang: str, timeout: float) -> list[Word]: ...


def parse_tsv(tsv: str) -> list[Word]:
    """Tesseract's TSV: level, page, block, par, line, word, left, top, width, height, conf, text. Only level 5
    (words) with a non-blank text and a confidence of 0 or more are kept."""
    words: list[Word] = []
    for raw in tsv.splitlines()[1:]:
        cols = raw.rstrip("\r\n").split("\t", 11)
        if len(cols) < 12 or cols[0] != "5":
            continue
        text = cols[11].strip()
        try:
            left, top, width, height = (int(c) for c in cols[6:10])
            conf = float(cols[10])
            line = (int(cols[2]), int(cols[3]), int(cols[4]))
        except ValueError:
            continue
        if not text or conf < 0 or width <= 0 or height <= 0:
            continue
        words.append(Word(text, left, top, left + width, top + height, min(1.0, conf / 100.0), line))
    return words


class TesseractEngine:
    name = "tesseract"

    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or shutil.which("tesseract")

    def available(self) -> bool:
        return self.executable is not None

    def read(self, png: bytes, lang: str, timeout: float) -> list[Word]:
        if not self.executable:
            raise OcrError("the OCR program is not installed")
        env = dict(os.environ, OMP_THREAD_LIMIT="1")
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "strip.png"
            src.write_bytes(png)
            try:
                done = subprocess.run(  # noqa: S603 - fixed argument list, no shell
                    [self.executable, str(src), "stdout", "-l", lang, "--psm", "3", "tsv"],
                    capture_output=True, timeout=timeout, env=env, check=False,
                )
            except subprocess.TimeoutExpired:
                raise OcrError(f"the OCR program did not finish in {timeout:g} s") from None
            except OSError as e:
                raise OcrError(f"the OCR program could not be started ({type(e).__name__})") from None
        if done.returncode != 0:
            raise OcrError(f"the OCR program stopped with code {done.returncode}")
        return parse_tsv(done.stdout.decode("utf-8", errors="replace"))


_override: OcrEngine | None = None
_disabled = False


def set_engine(engine: OcrEngine | None, *, disabled: bool = False) -> None:
    """Tests and the second engine: install an engine instead of Tesseract; `disabled=True` means none at all."""
    global _override, _disabled
    _override, _disabled = engine, disabled


def get_engine() -> OcrEngine | None:
    if _override is not None:
        return _override
    if _disabled:
        return None
    eng = TesseractEngine()
    return eng if eng.available() else None
