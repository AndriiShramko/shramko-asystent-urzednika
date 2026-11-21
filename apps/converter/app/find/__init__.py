"""Finder: from the page model to candidates (design 5.2, 6.3). One entry:

    from app.find import find
    out = find(page_model)                 # -> app.model.candidate.FinderOutput

The finder reads only the page model. It names every place to fill (leader, line block, comb, box, choice group,
cell, widget, blank inside a sentence, signature, office use), the label it found for it and how, the section it
stands in, and the role of every other run. What it cannot decide is a warning with the page and the place
(LABEL_NOT_FOUND, AMBIGUOUS_GROUP, LOW_CONFIDENCE, NOT_A_FORM): never a guess, never an exception.

Options (a mapping or FindOptions): `min_leader` (default 8), `strict` (tests: let a rule's exception through).
"""
from __future__ import annotations

from typing import Any, Mapping

from app.model.candidate import FinderOutput
from app.model.common import InputRef, Warning
from app.model.page import PageModel

from ._core import FindOptions, run

__all__ = ["find", "FindOptions"]


def find(page_model: PageModel, options: FindOptions | Mapping[str, Any] | None = None) -> FinderOutput:
    """Candidates, sections, reading order and roles of one document. Never raises unless `strict` is set."""
    o = FindOptions.of(options)
    if o.strict:
        return run(page_model, o)
    try:
        return run(page_model, o)
    except Exception as e:  # noqa: BLE001 - a rule that fails on an unseen paper is an honest gap, not a 500
        runs = [r.id for p in page_model.pages for r in p.runs]
        return FinderOutput(
            input=InputRef(sha256=page_model.source.sha256, format=page_model.source.format),
            order=runs, roles={r: "body" for r in runs},
            warnings=[Warning(code="UNREADABLE_PART",
                              detail=f"the finder could not follow this document ({type(e).__name__}); no place was read")],
        )
