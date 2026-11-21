"""The skeleton holds: the package imports, the version is set, the task-set tool is reachable from tests."""
import re


def test_package_imports_and_has_a_version() -> None:
    import app

    assert re.fullmatch(r"\d+\.\d+\.\d+", app.__version__)


def test_task_set_tool_is_importable() -> None:
    from tools.coi_paths import coi_dir

    assert coi_dir().name == "coi"
