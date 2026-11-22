"""AUDIT-8 VF-5: docs/02-architecture/converter-design.md may list a route or a setting as working only when the code
has it. A route row whose path main.py does not serve, and a setting row whose value nothing reads, must say so
("not built" / "no effect"). Reads code only; no run of the service."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DOC = ROOT / "docs" / "02-architecture" / "converter-design.md"
APP = ROOT / "apps" / "converter" / "app"
DOCKERFILE = ROOT / "apps" / "converter" / "Dockerfile"


def _lines() -> list[str]:
    return DOC.read_text(encoding="utf-8").splitlines()


def _served() -> str:
    return (APP / "main.py").read_text(encoding="utf-8")


def _settings_fields() -> set[str]:
    from app.config import Settings

    return set(Settings.__dataclass_fields__) if hasattr(Settings, "__dataclass_fields__") else \
        {k for k in vars(Settings).get("__annotations__", {})}


def _is_read(name: str) -> bool:
    """A setting is read when some module other than config.py names it, or config.py hands `s.<name>` on."""
    for path in APP.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if path.name == "config.py" and path.parent == APP:
            if re.search(rf"\bs\.{name}\b", text):
                return True
        elif re.search(rf"\b{name}\b", text):
            return True
    return False


def test_route_rows_name_only_served_paths_or_say_not_built():
    served = _served()
    bad = []
    for line in _lines():
        m = re.match(r"\| `(?:GET|POST) (/[^` ?]*)", line)
        if not m:
            continue
        for path in re.findall(r"(/[a-z0-9/_*.{}-]+)", line.split("|")[1]):
            if path.endswith("/*") or path in ("/ui/",):
                continue
            if path == "/openapi.json" and "openapi_url" not in served:   # FastAPI serves it by default
                continue
            if f'"{path}"' not in served and "not built" not in line:
                bad.append(path)
    assert not bad, f"converter-design.md lists routes main.py does not serve: {sorted(set(bad))}"


def test_setting_rows_whose_value_nothing_reads_say_no_effect():
    fields = _settings_fields()
    bad = []
    for line in _lines():
        m = re.match(r"\| `([A-Z][A-Z0-9_]+)`", line)
        if not m:
            continue
        name = m.group(1).lower()
        if name == "model_step":   # one allowed value, "off"; the row only says that nothing is loaded
            continue
        if name in fields and not _is_read(name) and "no effect" not in line:
            bad.append(m.group(1))
    assert not bad, f"converter-design.md describes settings nothing reads: {bad}"


def test_libreoffice_value_is_marked_while_no_image_has_it():
    docker = DOCKERFILE.read_text(encoding="utf-8").lower()
    if "libreoffice" in docker or "soffice" in docker:
        return
    for line in _lines():
        if line.startswith("| `DOC_READER`"):
            assert "no effect" in line, "DOC_READER row offers libreoffice, no image installs it"
