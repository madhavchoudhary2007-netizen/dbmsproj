#!/usr/bin/env python3
"""Summarize JUnit XML and allow strict pytest xfails but reject real skips."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def summarize(path: str | Path) -> dict[str, int]:
    root = ET.parse(path).getroot()  # noqa: S314 - report is produced by local pytest
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    cases = list(root.iter("testcase"))
    if not suites or not cases or root.tag not in {"testsuite", "testsuites"}:
        raise ValueError("JUnit report has no test suites or cases")
    reported_tests = sum(int(suite.get("tests", "0")) for suite in suites)
    if reported_tests != len(cases):
        raise ValueError("JUnit suite test count does not match its test cases")

    totals = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "xfails": 0}
    for case in cases:
        if case.find("error") is not None:
            totals["errors"] += 1
        elif case.find("failure") is not None:
            totals["failed"] += 1
        elif (skipped := case.find("skipped")) is not None:
            key = "xfails" if skipped.get("type") == "pytest.xfail" else "skipped"
            totals[key] += 1
        else:
            totals["passed"] += 1
    return totals


def main(path: str, pytest_status: int) -> int:
    try:
        totals = summarize(path)
    except (OSError, ET.ParseError, ValueError) as error:
        print(f"FAIL: backend tests did not produce a readable report ({error})")
        return 1
    failed = totals["failed"] + totals["errors"]
    print(
        f"Backend tests: {totals['passed']} passed, {failed} failed, "
        f"{totals['skipped']} skipped, {totals['xfails']} xfailed"
    )
    return int(pytest_status != 0 or failed != 0 or totals["skipped"] != 0)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: junit_gate.py REPORT PYTEST_EXIT_STATUS")
    raise SystemExit(main(sys.argv[1], int(sys.argv[2])))
