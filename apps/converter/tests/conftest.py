"""Shared test configuration of the converter. Lead-owned: a package adds fixtures in its own tests folder.

Markers decide what cannot run on a machine; such a test is reported as skipped with its reason, never as
passed (track rule 3 in docs/03-plan/work-packages/WP-F-forms-to-json.md):

    linux      needs Linux                          -> runs in the image workflow
    container  runs only inside the image           -> IN_CONTAINER=1
    tesseract  needs the Tesseract program          -> runs in the image workflow
    sets       needs the partner's task sets        -> they are local only and never in git, so CI skips these;
                                                       every module therefore also has tests on synthetic
                                                       fixtures built from code
    slow       longer than about five seconds       -> left out of `bash tools/gate.sh fast`

Synthetic values only. A test never holds a literal identifier with a valid check digit (PESEL, NIP, REGON,
identity card, account): the publishing check of the repository refuses them. Build one from a stem and a
check digit computed in the test.
"""
from __future__ import annotations

import os
import shutil
import sys

import pytest


def _sets_present() -> bool:
    try:
        from tools.coi_paths import sets

        return len(sets("reference")) >= 2 and len(sets("judged")) >= 7
    except Exception:  # noqa: BLE001 - any failure means "not here"
        return False


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    reasons: dict[str, str] = {}
    if not sys.platform.startswith("linux"):
        reasons["linux"] = "needs Linux; runs in the image workflow"
    if os.environ.get("IN_CONTAINER") != "1":
        reasons["container"] = "runs only inside the image (IN_CONTAINER=1)"
    if shutil.which("tesseract") is None:
        reasons["tesseract"] = "Tesseract is not installed here; runs in the image workflow"
    if not _sets_present():
        reasons["sets"] = "the partner's task sets are not on this machine (local only, never in git)"
    for item in items:
        for name, why in reasons.items():
            if name in item.keywords:
                item.add_marker(pytest.mark.skip(reason=why))
