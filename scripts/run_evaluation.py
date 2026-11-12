import argparse
import json
import socket
import sys
import unittest
import pytest
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

try:
    from scripts.evaluation_scenarios import SCENARIOS
except ModuleNotFoundError:
    from evaluation_scenarios import SCENARIOS

@contextmanager
def block_network():
    with patch(
        "socket.socket.connect",
        side_effect=OSError("Network access is disabled during evaluation."),
    ):
        yield

class RecordingResult(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.outcomes = {}

    def startTest(self, test):
        super().startTest(test)
        self.outcomes[test.id()] = {
            "status": "running",
            "reason": "",
        }

    def addSuccess(self, test):
        super().addSuccess(test)
        self.outcomes[test.id()] = {
            "status": "passed",
            "reason": "",
        }

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.outcomes[test.id()] = {
            "status": "failed",
            "reason": self._reason(err),
        }

    def addError(self, test, err):
        super().addError(test, err)
        self.outcomes[test.id()] = {
            "status": "error",
            "reason": self._reason(err),
        }

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.outcomes[test.id()] = {
            "status": "skipped",
            "reason": reason,
        }

    @staticmethod
    def _reason(err):
        if isinstance(err, tuple):
            return str(err[1]).splitlines()[0]

        return str(err).splitlines()[0]        

def load_tests(test_ids):
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    errors = {}

    for test_id in test_ids:
        try:
            loaded = loader.loadTestsFromName(test_id)

            if loader.errors:
                errors[test_id] = loader.errors[-1]
                loader.errors.clear()
                continue

            if loaded.countTestCases() == 0:
                errors[test_id] = "No tests were found."
                continue

            suite.addTests(loaded)

        except Exception as exc:
            errors[test_id] = str(exc)

    return suite, errors 

class EvaluationPlugin:
    def __init__(self):
        self.outcomes = {}

    def pytest_runtest_logreport(self, report):
        if report.when != "call":
            if report.failed:
                self.outcomes[report.nodeid] = {
                    "status": "error",
                    "reason": report.longreprtext.splitlines()[0],
                }
            return

        if report.passed:
            status = "passed"
            reason = ""
        elif report.failed:
            status = "failed"
            reason = str(report.longrepr).splitlines()[0]
        else:
            status = "skipped"
            reason = str(report.longrepr)

        self.outcomes[report.nodeid] = {
            "status": status,
            "reason": reason,
        }

def to_pytest_nodeid(test_id):
    parts = test_id.split(".")

    module_path = f"{parts[0]}/{parts[1]}.py"
    test_path = "::".join(parts[2:])

    return f"{module_path}::{test_path}"

def evaluate():
    plugin = EvaluationPlugin()

    all_test_ids = sorted({
        test_id
        for scenario in SCENARIOS
        for test_id in scenario.tests
    })

    test_paths = [
    to_pytest_nodeid(test_id)
    for test_id in all_test_ids
]

    with block_network():
        exit_code = pytest.main(
            ["-q", *test_paths],
            plugins=[plugin],
        )

    scenario_results = []

    for scenario in SCENARIOS:
        results = []

        for test_id in scenario.tests:
            nodeid = to_pytest_nodeid(test_id)
            result = plugin.outcomes.get(nodeid)

            if result is None:
                result = {
                    "status": "not_found",
                    "reason": "Test was not collected or executed.",
                }

            results.append({
                "test_id": test_id,
                **result,
            })

        passed = all(
            result["status"] == "passed"
            for result in results
        )

        scenario_results.append({
            "number": scenario.number,
            "name": scenario.name,
            "category": scenario.category,
            "checks": scenario.checks,
            "passed": passed,
            "tests_passed": sum(
                result["status"] == "passed"
                for result in results
            ),
            "total_tests": len(results),
            "failures": [
                result
                for result in results
                if result["status"] != "passed"
            ],
        })

    total = len(scenario_results)
    passed_count = sum(item["passed"] for item in scenario_results)

    return {
        "scenarios": scenario_results,
        "total_scenarios": total,
        "passed_scenarios": passed_count,
        "failed_scenarios": total - passed_count,
        "pass_percentage": (
            round(passed_count / total * 100, 2)
            if total else 0
        ),
        "exit_code": exit_code,
    }           

def short(test_id):
    return test_id.split(".")[-1]


def print_report(report):
    print("\n" + "=" * 65)
    print("             MINI CLASSBUILD EVALUATION")
    print("=" * 65)

    current_category = None

    for scenario in report["scenarios"]:
        if scenario["category"] != current_category:
            current_category = scenario["category"]
            print(f"\n[{current_category.upper()}]")

        status = "PASS" if scenario["passed"] else "FAIL"

        print(
            f'{scenario["number"]:02d}. {scenario["name"]}: '
            f'{status} '
            f'({scenario["tests_passed"]}/{scenario["total_tests"]})'
        )

        for failure in scenario["failures"]:
            print(f'    - {short(failure["test_id"])}')
            print(f'      {failure["status"]}: {failure["reason"]}')

    print("\n" + "-" * 65)
    print(f'Total scenarios: {report["total_scenarios"]}')
    print(f'Passed: {report["passed_scenarios"]}')
    print(f'Failed: {report["failed_scenarios"]}')
    print(f'Pass percentage: {report["pass_percentage"]}%')
    print("=" * 65)

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run Mini ClassBuild offline evaluation."
    )

    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Print results without saving JSON reports.",
    )

    parser.add_argument(
        "--output-dir",
        default="evaluation_results",
        help="Directory for JSON evaluation reports.",
    )

    args = parser.parse_args(argv)

    report = evaluate()
    print_report(report)

    if not args.no_json:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        report_path = output_dir / f"evaluation-{timestamp}.json"
        latest_path = output_dir / "latest.json"

        report_path.write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )

        latest_path.write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )

        print(f"\nJSON report saved to: {report_path}")

    return 0 if report["failed_scenarios"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())    