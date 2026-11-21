"""Readers: one file in, one page model out (design 5.1, 6.2).

    from app.readers import read_document, ReaderError
    model = read_document(data, "pdf")          # -> app.model.page.PageModel

One module per format lives in this package and registers itself on import:

    from app.readers import register, ReadResult
    @register("xlsx")
    def read(data: bytes, options: ReadOptions) -> ReadResult: ...

Every module of this package whose name does not start with "_" is imported on first use, so a new format is a
new file and no edit here. A reader raises ReaderError for a file it cannot follow (the service answers 422);
any other exception of a reader is turned into ReaderError("UNREADABLE") here, so no stack trace reaches a caller.

Hooks: a step that is not built yet is a named hook. "pdf.textless_page" is called for a PDF page with fewer than
`ocr_min_chars` characters: hook(data, page_index, page_number, ids, options) -> Page (origin "ocr"). With no
hook registered the page stays empty and the document carries an UNREADABLE_PART warning for it (WP-F2c adds it).
"""
from __future__ import annotations

import hashlib
import importlib
import pkgutil
from typing import Any, Callable, Mapping

from pydantic import ValidationError

from app.model.page import PageModel, Source

from ._base import Ids, ReaderError, ReadOptions, ReadResult

__all__ = ["read_document", "register", "register_hook", "hook", "formats", "ReaderError", "ReadOptions",
           "ReadResult", "Ids"]

# The page-model contract (app.model.common.Format) names the formats of the readers except the ones recorded here under
# the nearest kind (WP-F20e; `source.reader` tells them apart). WP-F20f added rtf, xls, txt and heic to the contract.
MODEL_FORMAT = {"tiff": "png", "bmp": "png", "gif": "png", "webp": "png", "odt": "docx"}

ReaderFn = Callable[[bytes, ReadOptions], ReadResult]

_READERS: dict[str, ReaderFn] = {}
_HOOKS: dict[str, Callable[..., Any]] = {}
_discovered = False


def register(fmt: str) -> Callable[[ReaderFn], ReaderFn]:
    """Decorator: the function reads one format (a value of app.model.common.Format)."""

    def deco(fn: ReaderFn) -> ReaderFn:
        if fmt in _READERS and _READERS[fmt] is not fn:
            raise RuntimeError(f"two readers registered for {fmt!r}")
        _READERS[fmt] = fn
        return fn

    return deco


def register_hook(name: str, fn: Callable[..., Any]) -> None:
    _HOOKS[name] = fn


def hook(name: str) -> Callable[..., Any] | None:
    _discover()
    return _HOOKS.get(name)


def _discover() -> None:
    global _discovered
    if _discovered:
        return
    _discovered = True
    for m in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        if not m.name.startswith("_"):
            importlib.import_module(f"{__name__}.{m.name}")


def formats() -> list[str]:
    """Formats that have a reader on this build."""
    _discover()
    return sorted(_READERS)


def read_document(data: bytes, fmt: str, options: ReadOptions | Mapping[str, Any] | None = None) -> PageModel:
    """Read one file of a known content kind into the page model. Raises ReaderError only."""
    _discover()
    fn = _READERS.get(fmt)
    if fn is None:
        raise ReaderError("UNSUPPORTED_FORMAT", f"no reader for the format {fmt!r} in this build")
    opts = ReadOptions.of(options)
    try:
        result = fn(data, opts)
        if len(result.pages) > opts.max_pages:
            raise ReaderError("TOO_LARGE", f"{len(result.pages)} pages, the limit is {opts.max_pages}")
        return PageModel(
            source=Source(sha256=hashlib.sha256(data).hexdigest(), format=MODEL_FORMAT.get(fmt, fmt), reader=result.reader,
                          pages=len(result.pages)),
            pages=result.pages,
            warnings=result.warnings,
        )
    except ReaderError:
        raise
    except MemoryError:
        raise ReaderError("TOO_LARGE", "the file needs more memory than the reader may use") from None
    except ValidationError as e:  # our own bug: a reader built a page model the contract refuses
        raise ReaderError("UNREADABLE", f"the {fmt} reader built an invalid page model ({e.error_count()} errors)") from e
    except Exception as e:  # noqa: BLE001 - a library's failure on a broken file is a 422, not a stack trace
        raise ReaderError("UNREADABLE", f"the {fmt} reader could not follow this file ({type(e).__name__})") from e
