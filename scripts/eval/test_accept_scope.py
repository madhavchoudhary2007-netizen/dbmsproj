import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
ACCEPT = ROOT / "scripts/agent/accept.sh"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, text=True, capture_output=True
    ).stdout.strip()


@pytest.fixture
def fixture_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "qa@example.invalid")
    git(repo, "config", "user.name", "Acceptance QA")
    (repo / "scripts/agent").mkdir(parents=True)
    shutil.copy2(ACCEPT, repo / "scripts/agent/accept.sh")
    (repo / "scripts/agent/accept.sh").chmod(0o755)
    git(repo, "add", "scripts/agent/accept.sh")
    git(repo, "commit", "-qm", "fixture harness")
    (repo / ".agent/results").mkdir(parents=True)
    (repo / ".agent/packets").mkdir(parents=True)
    (repo / ".agent/envelope.schema.json").write_text("{}\n")
    # The fixture's local validator stub keeps acceptance offline.
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "npx"
    stub.write_text("#!/bin/sh\nexit 0\n")
    stub.chmod(0o755)
    yield repo, bin_dir


def configure_task(
    repo: Path,
    *,
    status: str = "PASSED",
    command: str = "true",
    approved_command: str = "true",
    targets: str | None = "src/target.txt",
    files_modified: list[dict] | None = None,
) -> None:
    (repo / ".agent/packets/T-44615.md").write_text(
        f"# fixture\n\n## Approved Verify\n```sh\n{approved_command}\n```\n"
    )
    target_entry = "" if targets is None else f"- target_files: {targets}\n"
    (repo / ".agent/NEXT_STATE.md").write_text(f"### T-44615 task\n{target_entry}")
    envelope = {
        "task_id": "T-44615",
        "status": status,
        "files_modified": files_modified or [],
        "diff_summary": "fixture change",
        "verification": {
            "command": command,
            "exit_code": 0,
            "tests_passed": 1,
            "tests_failed": 0,
            "duration_ms": 1,
        },
        "unresolved_blockers": [],
    }
    (repo / ".agent/results/T-44615.json").write_text(json.dumps(envelope))


def accept(repo: Path, bin_dir: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    return subprocess.run(
        ["bash", "scripts/agent/accept.sh", "T-44615"],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
        timeout=10,
    )


def test_passed_commits_only_targets_and_preserves_other_work(fixture_repo):
    repo, bin_dir = fixture_repo
    configure_task(repo)
    (repo / "src").mkdir()
    (repo / "src/target.txt").write_text("approved\n")
    (repo / "src/unrelated.txt").write_text("unstaged original\n")
    (repo / "src/prestaged.txt").write_text("pre-staged original\n")
    git(repo, "add", "src/prestaged.txt")
    git(repo, "commit", "-qm", "baseline")
    # Restore the unrelated staged change after baseline, then add target and unrelated work.
    (repo / "src/prestaged.txt").write_text("pre-staged edit\n")
    git(repo, "add", "src/prestaged.txt")
    (repo / "src/target.txt").write_text("approved edit\n")
    (repo / "src/unrelated.txt").write_text("unstaged original\n")
    (repo / "src/untracked.txt").write_text("untracked original\n")
    (repo / ".agent/notes.txt").write_text("metadata original\n")

    result = accept(repo, bin_dir)

    assert result.returncode == 0, result.stderr + result.stdout
    committed = set(git(repo, "show", "--pretty=", "--name-only", "HEAD").splitlines())
    assert committed == {"src/target.txt"}
    assert git(repo, "show", "HEAD:src/prestaged.txt") == "pre-staged original"
    assert git(repo, "show", ":src/prestaged.txt") == "pre-staged edit"
    assert (repo / "src/unrelated.txt").read_text() == "unstaged original\n"
    assert (repo / "src/untracked.txt").read_text() == "untracked original\n"
    assert (repo / ".agent/notes.txt").read_text() == "metadata original\n"


@pytest.mark.parametrize(
    ("status", "command", "approved_command"),
    [
        ("FAILED", "touch failed-envelope-ran", "true"),
        ("PASSED", "touch mismatched-verify-ran", "true"),
    ],
)
def test_rejects_failed_or_mismatched_verify_before_command(
    fixture_repo, status, command, approved_command
):
    repo, bin_dir = fixture_repo
    configure_task(
        repo,
        status=status,
        command=command,
        approved_command=approved_command,
    )

    result = accept(repo, bin_dir)

    assert result.returncode != 0
    assert not (repo / "failed-envelope-ran").exists()
    assert not (repo / "mismatched-verify-ran").exists()


def test_reruns_approved_verify_once_and_requires_success(fixture_repo):
    repo, bin_dir = fixture_repo
    command = "printf 'run\\n' >> src/target.txt"
    configure_task(repo, command=command, approved_command=command)
    (repo / "src").mkdir()
    (repo / "src/target.txt").write_text("candidate\n")

    result = accept(repo, bin_dir)

    assert result.returncode == 0, result.stderr + result.stdout
    assert (repo / "src/target.txt").read_text() == "candidate\nrun\n"


def test_rejects_a_failing_approved_verify(fixture_repo):
    repo, bin_dir = fixture_repo
    head_before = git(repo, "rev-parse", "HEAD")
    configure_task(repo, command="false", approved_command="false")
    (repo / "src").mkdir()
    (repo / "src/target.txt").write_text("candidate\n")

    result = accept(repo, bin_dir)

    assert result.returncode != 0
    assert git(repo, "rev-parse", "HEAD") == head_before


def test_allows_listed_agent_target_and_preserves_other_agent_files(fixture_repo):
    repo, bin_dir = fixture_repo
    configure_task(repo, targets=".agent/target.txt")
    (repo / ".agent/target.txt").write_text("original target\n")
    (repo / ".agent/notes.txt").write_text("unrelated metadata\n")
    git(repo, "add", ".agent")
    git(repo, "commit", "-qm", "fixture metadata")
    (repo / ".agent/target.txt").write_text("approved edit\n")

    result = accept(repo, bin_dir)

    assert result.returncode == 0, result.stderr + result.stdout
    committed = set(git(repo, "show", "--pretty=", "--name-only", "HEAD").splitlines())
    assert committed == {".agent/target.txt"}
    assert (repo / ".agent/notes.txt").read_text() == "unrelated metadata\n"
    assert git(repo, "show", "HEAD:.agent/notes.txt") == "unrelated metadata"


def test_rejects_files_modified_entries_outside_approved_targets(fixture_repo):
    repo, bin_dir = fixture_repo
    head_before = git(repo, "rev-parse", "HEAD")
    configure_task(
        repo,
        files_modified=[
            {"path": "src/unapproved.txt", "lines_added": 1, "lines_removed": 0},
            {"path": ".agent/unapproved.txt", "lines_added": 1, "lines_removed": 0},
        ],
    )
    (repo / "src").mkdir()
    (repo / "src/target.txt").write_text("approved candidate\n")

    result = accept(repo, bin_dir)

    assert result.returncode != 0
    assert git(repo, "rev-parse", "HEAD") == head_before


@pytest.mark.parametrize(
    "targets",
    [None, "", "../outside.txt"],
)
def test_rejects_empty_unsafe_or_out_of_scope_target_lists(
    fixture_repo, targets
):
    repo, bin_dir = fixture_repo
    head_before = git(repo, "rev-parse", "HEAD")
    configure_task(repo, targets=targets)
    (repo / "src").mkdir()
    (repo / "src/target.txt").write_text("candidate\n")

    result = accept(repo, bin_dir)

    assert result.returncode != 0
    assert git(repo, "rev-parse", "HEAD") == head_before

