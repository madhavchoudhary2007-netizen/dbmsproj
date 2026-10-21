"""Synthetic coverage for the backend JUnit summary gate."""

# ruff: noqa: S101
import xml.etree.ElementTree as ET

import pytest
from junit_gate import main, summarize


def report(tmp_path, contents):
    path = tmp_path / "report.xml"
    path.write_text(contents, encoding="utf-8")
    return path


def test_strict_xfails_are_reported_and_allowed(tmp_path, capsys):
    path = report(
        tmp_path,
        '<testsuite tests="2" failures="0" errors="0" skipped="1">'
        '<testcase name="ok"/><testcase name="xfail">'
        '<skipped type="pytest.xfail" message="G11"/></testcase></testsuite>',
    )
    assert summarize(path) == {
        "passed": 1, "failed": 0, "errors": 0, "skipped": 0, "xfails": 1
    }
    assert main(str(path), 0) == 0
    assert "0 skipped, 1 xfailed" in capsys.readouterr().out
    assert main(str(path), 1) == 1


def test_real_skip_is_rejected(tmp_path):
    path = report(
        tmp_path,
        '<testsuite tests="1" skipped="1"><testcase name="skip">'
        '<skipped message="not run"/></testcase></testsuite>',
    )
    assert summarize(path)["skipped"] == 1
    assert main(str(path), 0) == 1


def test_test_failure_is_rejected(tmp_path):
    path = report(
        tmp_path,
        '<testsuite tests="1" failures="1"><testcase name="bad">'
        '<failure message="assertion"/></testcase></testsuite>',
    )
    assert summarize(path)["failed"] == 1
    assert main(str(path), 0) == 1


@pytest.mark.parametrize("contents", [None, "<testsuite>"])
def test_missing_or_malformed_report_is_rejected(tmp_path, contents):
    path = tmp_path / "report.xml" if contents is None else report(tmp_path, contents)
    with pytest.raises((OSError, ValueError, ET.ParseError)):
        summarize(path)
    assert main(str(path), 0) == 1
