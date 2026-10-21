"""Runtime dependency regression checks for the security review."""

import re
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


@pytest.mark.xfail(strict=True, reason="F-E01")
def test_runtime_dependencies_exclude_python_jose():
    requirements_path = Path(__file__).resolve().parents[1] / "requirements.txt"
    requirements = requirements_path.read_text(encoding="utf-8")
    names = {
        canonicalize_name(Requirement(re.split(r"\s+#", line, maxsplit=1)[0]).name)
        for raw_line in requirements.splitlines()
        if (line := raw_line.strip()) and not line.startswith("#")
    }
    assert "python-jose" not in names
