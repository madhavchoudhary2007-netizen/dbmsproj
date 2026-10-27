import os
import subprocess
import sys


def configured_seed_flag(*, app_env: str, seed_demo_data: str | None = None) -> bool:
    env = {
        "PATH": os.environ["PATH"],
        "JWT_SECRET": "synthetic-test-secret-that-is-long-enough-for-validation",
        "APP_ENV": app_env,
    }
    if seed_demo_data is not None:
        env["SEED_DEMO_DATA"] = seed_demo_data

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import runpy; print(runpy.run_path('backend/app/config.py')['SEED_DEMO_DATA'])",
        ],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )
    return result.stdout.strip() == "True"


def test_local_defaults_to_demo_seeding() -> None:
    assert configured_seed_flag(app_env="local") is True


def test_local_can_disable_demo_seeding() -> None:
    assert configured_seed_flag(app_env="local", seed_demo_data="0") is False


def test_production_defaults_to_no_demo_seeding() -> None:
    assert configured_seed_flag(app_env="production") is False


def test_demo_seeding_can_be_explicitly_enabled() -> None:
    assert configured_seed_flag(app_env="production", seed_demo_data="1") is True
