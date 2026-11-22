"""AUDIT-8 VF-4: the mentor answers (docs/05-hackathon/mentor-questions/answers-v2.md) may state as settled only
what the code and the image do today. Each test reads the code or the Dockerfile and fails while the document says
more than they do. No run of the service is needed."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DOC = ROOT / "docs" / "05-hackathon" / "mentor-questions" / "answers-v2.md"
APP = ROOT / "apps" / "converter" / "app"
DOCKERFILE = ROOT / "apps" / "converter" / "Dockerfile"


def _row(key: str) -> str:
    for line in DOC.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"| {key} |"):
            return line
    raise AssertionError(f"row {key} not found in {DOC.name}")


def _routes() -> str:
    return (APP / "main.py").read_text(encoding="utf-8")


def _emits_filled_form() -> bool:
    """True when some module other than the declaration list raises the FILLED_FORM warning."""
    for path in APP.rglob("*.py"):
        if path.name == "common.py" and path.parent.name == "model":
            continue
        if "FILLED_FORM" in path.read_text(encoding="utf-8"):
            return True
    return False


def test_b19_names_no_selftest_route_that_the_service_lacks():
    row = _row("B19")
    if "/selftest" in row:
        assert re.search(r"[\"']/v1/selftest[\"']|[\"']/selftest[\"']", _routes()), \
            "B19 promises /selftest, main.py has no such route"


def test_b20_filled_form_handling_is_not_stated_as_done_while_nothing_emits_it():
    row = _row("B20")
    if not _emits_filled_form():
        assert "redact mode" not in row or "not built" in row.lower(), \
            "B20 states a redact mode for filled forms, but FILLED_FORM is only declared (model/common.py)"


def test_t10_libreoffice_in_plus_image_only_if_the_dockerfile_installs_it():
    row = _row("T10")
    docker = DOCKERFILE.read_text(encoding="utf-8").lower()
    if "libreoffice" not in docker and "soffice" not in docker:
        assert not re.search(r"LibreOffice \(MPL-2\.0\) is only an optional switch in the `plus` image", row), \
            "T10 says the plus image has LibreOffice, the Dockerfile installs none"
    assert (APP / "readers" / "doc.py").exists()
    assert "reader is not built yet" not in row, "T10 says the DOC reader is not built, app/readers/doc.py exists"


def test_proposals_9_and_11_are_marked_when_not_built():
    p9, p11 = _row("9"), _row("11")
    if not _emits_filled_form():
        assert "not built" in p9, "proposal 9 (filled-form alarm) reads as done, nothing emits FILLED_FORM"
    if "/selftest" in p11 and "selftest" not in _routes():
        assert "not built" in p11, "proposal 11 names /selftest as a proof, main.py has no such route"
    cli = (APP / "cli.py").read_text(encoding="utf-8") if (APP / "cli.py").exists() else ""
    if "diff" not in _routes() and "diff" not in cli:
        assert "not built" in _row("10"), "proposal 10 (comparison of versions) reads as done, no route or command"


def test_table_rows_keep_their_column_count():
    """A literal | inside a cell would split it; the edited rows keep the width of their table."""
    assert _row("B20").count("|") == _row("B19").count("|")
    assert _row("T10").count("|") == _row("B19").count("|")
