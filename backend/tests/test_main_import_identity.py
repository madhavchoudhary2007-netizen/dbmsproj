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
from typing import get_type_hints

first = importlib.import_module(sys.argv[1])
second = importlib.import_module(sys.argv[2])

assert sys.modules["app.main"] is sys.modules["backend.app.main"]
assert first is second
assert first.app is second.app
assert first.app.state is second.app.state

app_package = importlib.import_module("app")
backend_package = importlib.import_module("backend")
backend_app_package = importlib.import_module("backend.app")
app_api_package = importlib.import_module("app.api")
backend_api_package = importlib.import_module("backend.app.api")
showcase_app = importlib.import_module("app.api.dbms_showcase")
showcase_backend = importlib.import_module("backend.app.api.dbms_showcase")
laps_app = importlib.import_module("app.api.laps")
laps_backend = importlib.import_module("backend.app.api.laps")

assert backend_package.app is app_package
assert app_package.main is first
assert backend_app_package.main is first
assert sys.modules["app.api.dbms_showcase"] is sys.modules["backend.app.api.dbms_showcase"]
assert showcase_app is showcase_backend
assert app_package.api is app_api_package
assert backend_app_package.api is backend_api_package
assert app_api_package.dbms_showcase is showcase_app
assert backend_api_package.dbms_showcase is showcase_app
assert sys.modules["app.api.laps"] is sys.modules["backend.app.api.laps"]
assert laps_app is laps_backend
assert app_api_package.laps is laps_app
assert backend_api_package.laps is laps_app

def telemetry_dependency(module):
    annotation = get_type_hints(module.get_analytics_gaps, include_extras=True)["telemetry"]
    return next(item for item in annotation.__metadata__ if hasattr(item, "dependency"))

app_telemetry_dependency = telemetry_dependency(showcase_app)
backend_telemetry_dependency = telemetry_dependency(showcase_backend)
assert app_telemetry_dependency.dependency is backend_telemetry_dependency.dependency
assert app_telemetry_dependency.dependency is laps_app.get_race_telemetry

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
