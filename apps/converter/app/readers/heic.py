"""HEIC and HEIF reader (WP-F20f, D24): the unmodified decoder program `heif-dec` of libheif as a child process, then
its PNG goes through the image reader with the same limits.

    photo.heic -> heif-dec (no shell, 30 s, its own temporary folder, 0700) -> PNG -> image reader (OCR, lines, boxes)

Where the program is absent (a laptop install) the reader refuses plainly with the code NO_DECODER: the pipeline says
"Ta instalacja nie ma dekodera HEIC." and never asks the user to re-save the file. The decoder is a separate program on
purpose: its licence (LGPL libheif, LGPL libde265) is then not linked into our code, and a crash of it ends only the child.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import register
from . import image
from ._base import ReaderError, ReadOptions, ReadResult

TIMEOUT_S = 30.0
MAX_PNG_BYTES = 400 << 20     # what the decoder may write; a larger file is refused before it is read
_KEEP_ENV = ("PATH", "LD_LIBRARY_PATH", "LIBHEIF_PLUGIN_PATH", "LANG", "LC_ALL", "SYSTEMROOT")


def find_decoder() -> str | None:
    return shutil.which("heif-dec")


def available() -> bool:
    return find_decoder() is not None


def _png_of(data: bytes, exe: str, timeout: float = TIMEOUT_S) -> bytes:
    env = {k: os.environ[k] for k in _KEEP_ENV if k in os.environ}
    with tempfile.TemporaryDirectory(prefix="heic-") as tmp:   # mkdtemp: mode 0700, ours alone
        folder = Path(tmp)
        src, dst = folder / "in.heic", folder / "out.png"
        src.write_bytes(data)
        try:
            done = subprocess.run(  # noqa: S603 - fixed argument list, no shell, the name of the file is ours
                [exe, str(src), str(dst)], capture_output=True, timeout=timeout, env=env, cwd=tmp, check=False,
            )
        except subprocess.TimeoutExpired:
            raise ReaderError("UNREADABLE", f"the HEIC decoder did not finish in {timeout:g} s") from None
        except OSError as e:
            raise ReaderError("NO_DECODER", f"the HEIC decoder could not be started ({type(e).__name__})") from None
        if done.returncode != 0:
            raise ReaderError("UNREADABLE", f"the HEIC decoder stopped with code {done.returncode}")
        out = dst if dst.is_file() else next(iter(sorted(folder.glob("out*.png"))), None)   # several images: the first
        if out is None:
            raise ReaderError("UNREADABLE", "the HEIC decoder wrote no image")
        if out.stat().st_size > MAX_PNG_BYTES:
            raise ReaderError("TOO_LARGE", "the decoded image is larger than the reader may open")
        return out.read_bytes()


@register("heic")
def read_heic(data: bytes, options: ReadOptions) -> ReadResult:
    exe = find_decoder()
    if exe is None:
        raise ReaderError("NO_DECODER", "heif-dec is not installed")
    result = image.read_png(_png_of(data, exe), options)
    return ReadResult(reader="heic." + result.reader.replace(".", "_"), pages=result.pages, warnings=result.warnings)
