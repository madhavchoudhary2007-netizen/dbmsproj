import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WEIGHTS = {
    "functional": {f"F-{i}": w for i, w in enumerate((3, 2, 4, 6, 3, 2, 2, 2, 1), 1)},
    "aesthetic": {f"A-{i}": w for i, w in enumerate((2, 2, 2, 2, 3, 2, 2), 1)},
    "performance": {f"P-{i}": w for i, w in enumerate((3, 3, 2, 3, 2, 2), 1)},
    "edge": {f"E-{i}": w for i, w in enumerate((3, 4, 2, 2, 2), 1)},
}


def setup_case(tmp_path, mutate=None):
    (tmp_path / "scripts/eval").mkdir(parents=True)
    shutil.copy(ROOT / "scripts/eval/score.sh", tmp_path / "scripts/eval/score.sh")
    target = tmp_path / ".agent/eval"
    target.mkdir(parents=True)
    for dim, weights in WEIGHTS.items():
        checks = [
            dict(id=key, weight=weight, passed=True, detail="fixture passed")
            for key, weight in weights.items()
        ]
        if mutate and dim == "functional":
            mutate(checks)
        (target / f"{dim}.json").write_text(json.dumps({"checks": checks}))
    return subprocess.run(
        ["/bin/bash", "scripts/eval/score.sh"], cwd=tmp_path, text=True, capture_output=True
    )


def score(result):
    return json.loads(result.stdout)


def test_complete_evidence_scores_100_and_exits_zero(tmp_path):
    result = setup_case(tmp_path)
    assert result.returncode == 0
    assert score(result)["aggregate"] == 100
    assert score(result)["presentable"] is True


def test_f2_blocks_delivery_above_95(tmp_path):
    result = setup_case(tmp_path, lambda checks: checks[1].update(passed=False))
    assert result.returncode != 0
    output = score(result)
    assert output["aggregate"] > 95
    assert "F-2" in output["failed_gates"]
    assert output["presentable"] is False


def test_null_f9_counts_failed_and_blocks_delivery(tmp_path):
    result = setup_case(
        tmp_path, lambda checks: checks[8].update(passed=None, detail="NOT_RUN: audit tool")
    )
    assert result.returncode != 0
    output = score(result)
    assert output["functional"] == 96
    assert output["not_run"] == ["F-9"]
    assert output["presentable"] is False


def test_new_functional_checks_use_total_weight_25(tmp_path):
    result = setup_case(tmp_path, lambda checks: checks[6].update(passed=False))
    assert score(result)["functional"] == 92


@pytest.mark.parametrize(
    "change",
    [
        lambda checks: checks.pop(1),
        lambda checks: checks.append(checks[0].copy()),
        lambda checks: checks[0].update(weight=99),
        lambda checks: checks[0].update(id="F-999", weight=None),
    ],
)
def test_missing_duplicate_or_reweighted_evidence_is_rejected(tmp_path, change):
    result = setup_case(tmp_path, change)
    assert result.returncode != 0
    assert "invalid functional.json" in result.stderr
