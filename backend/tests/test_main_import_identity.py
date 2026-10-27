"""Regression checks for the two supported import roots of the application."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "first_import,second_import",
    [
        ("app.main", "backend.app.main"),
        ("backend.app.main", "app.main"),
    ],
    ids=("app-first", "backend-app-first"),
)
def test_main_module_and_application_are_shared_across_import_roots(
    first_import: str, second_import: str
) -> None:
    check_imports = r'''
import importlib
import sys

first = importlib.import_module(sys.argv[1])
second = importlib.import_module(sys.argv[2])

assert sys.modules["app.main"] is sys.modules["backend.app.main"]
assert first is second
assert first.app is second.app
assert first.app.state is second.app.state
for name in (
    "bus",
    "simulations",
    "mongo_client",
    "telemetry_collection",
    "lock_demo_guard",
    "race_history_handlers",
    "require_runtime_lease",
):
    assert getattr(first, name) is getattr(second, name), name
assert first.app.state.runtime.bus is first.bus
'''
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        (str(REPOSITORY_ROOT), str(REPOSITORY_ROOT / "backend"))
    )
    # S603 is safe here: the interpreter and script are fixed, and import names
    # come only from the literal parameter pairs above.
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", check_imports, first_import, second_import],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, (
        f"import order {first_import!r} then {second_import!r} did not share main state\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
