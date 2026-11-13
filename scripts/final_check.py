
import compileall
import importlib.metadata
import importlib.util
import os
import re
import subprocess
import sys

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MIN_PYTHON = (3, 11)
COMMAND_TIMEOUT = 600

IMPORT_NAMES = {
    "python-dotenv": "dotenv",
    "sentence-transformers": "sentence_transformers",
}


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str = ""


@dataclass
class Requirement:
    name: str
    import_name: str
    operator: str = ""
    version: str = ""


def parse_requirements(path):
    """Read package requirements using the standard library."""
    requirements = []

    if not path.exists():
        return requirements

    pattern = re.compile(
        r"^\s*([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?"
        r"\s*(>=|==|~=|>|<=|<|!=)?\s*"
        r"([A-Za-z0-9.*+!-]+)?"
    )

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()

        if not line or line.startswith(("-", "git+", "http")):
            continue

        # Environment markers are not needed for this project's checks.
        line = line.split(";", 1)[0].strip()

        match = pattern.match(line)
        if not match:
            continue

        name, operator, version = match.groups()
        normalized_name = name.lower().replace("_", "-")

        import_name = IMPORT_NAMES.get(
            normalized_name,
            name.replace("-", "_"),
        )

        requirements.append(
            Requirement(
                name=normalized_name,
                import_name=import_name,
                operator=operator or "",
                version=version or "",
            )
        )

    return requirements


def version_tuple(version):
    """Convert a version string into numeric parts."""
    numbers = re.findall(r"\d+", version)
    return tuple(int(number) for number in numbers)


def version_satisfies(installed, operator, required):
    if not operator or not required:
        return True

    current = version_tuple(installed)
    target = version_tuple(required)

    if not current or not target:
        return False

    length = max(len(current), len(target))
    current += (0,) * (length - len(current))
    target += (0,) * (length - len(target))

    if operator in (">=", "~="):
        return current >= target
    if operator == ">":
        return current > target
    if operator == "<=":
        return current <= target
    if operator == "<":
        return current < target
    if operator == "==":
        return current == target
    if operator == "!=":
        return current != target

    return True


def check_python_version():
    current = sys.version_info[:2]

    if current >= MIN_PYTHON:
        return CheckResult(
            "Python version",
            True,
            f"Python {sys.version.split()[0]}",
        )

    return CheckResult(
        "Python version",
        False,
        "Python 3.11 or newer is required.",
    )


def check_dependencies():
    requirements_file = ROOT / "requirements.txt"

    if not requirements_file.exists():
        return [
            CheckResult(
                "Dependencies",
                False,
                "requirements.txt was not found.",
            )
        ]

    requirements = parse_requirements(requirements_file)

    if not requirements:
        return [
            CheckResult(
                "Dependencies",
                False,
                "No valid requirements were found.",
            )
        ]

    results = []

    for requirement in requirements:
        try:
            installed_version = importlib.metadata.version(
                requirement.name
            )
        except importlib.metadata.PackageNotFoundError:
            results.append(
                CheckResult(
                    f"Dependency: {requirement.name}",
                    False,
                    "Package is not installed.",
                )
            )
            continue

        try:
            importable = (
                importlib.util.find_spec(requirement.import_name)
                is not None
            )
        except (ImportError, ModuleNotFoundError, ValueError):
            importable = False

        version_ok = version_satisfies(
            installed_version,
            requirement.operator,
            requirement.version,
        )

        passed = importable and version_ok

        details = f"Installed version: {installed_version}"

        if not importable:
            details += "; module is not importable."

        if not version_ok:
            details += (
                f"; required version: "
                f"{requirement.operator}{requirement.version}"
            )

        results.append(
            CheckResult(
                f"Dependency: {requirement.name}",
                passed,
                details,
            )
        )

    return results


def child_environment():
    """Create an offline environment without API secrets."""
    environment = os.environ.copy()

    environment.pop("GROQ_API_KEY", None)

    environment["HF_HUB_OFFLINE"] = "1"
    environment["TRANSFORMERS_OFFLINE"] = "1"

    return environment


def run_command(name, command):
    """Run a verification command with a timeout."""
    print(f"\nRunning: {name}")
    print("$", " ".join(str(part) for part in command))

    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=child_environment(),
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
            check=False,
        )

        if result.stdout:
            print(result.stdout.strip())

        if result.stderr:
            print(result.stderr.strip())

        if result.returncode == 0:
            return CheckResult(name, True, "Command completed.")

        return CheckResult(
            name,
            False,
            f"Command exited with code {result.returncode}.",
        )

    except subprocess.TimeoutExpired:
        return CheckResult(
            name,
            False,
            f"Command timed out after {COMMAND_TIMEOUT} seconds.",
        )

    except OSError as error:
        return CheckResult(
            name,
            False,
            str(error),
        )


def check_syntax():
    folders = [
        ROOT / "classbuild",
        ROOT / "scripts",
        ROOT / "tests",
    ]

    syntax_ok = True

    for folder in folders:
        if folder.exists():
            syntax_ok = (
                compileall.compile_dir(
                    str(folder),
                    quiet=1,
                    force=True,
                )
                and syntax_ok
            )

    app_file = ROOT / "app.py"

    if app_file.exists():
        syntax_ok = (
            compileall.compile_file(
                str(app_file),
                quiet=1,
                force=True,
            )
            and syntax_ok
        )

    return CheckResult(
        "Python syntax",
        syntax_ok,
        "Project files compiled successfully."
        if syntax_ok
        else "One or more Python files contain syntax errors.",
    )


def main():
    print("\n" + "=" * 60)
    print("MINI CLASSBUILD - FINAL VERIFICATION")
    print("=" * 60)

    results = []

    # 1. Python version
    print("\n[1] Checking Python version...")
    results.append(check_python_version())

    # 2. Dependencies
    print("\n[2] Checking dependencies...")
    dependency_results = check_dependencies()
    results.extend(dependency_results)

    # 3. Syntax
    print("\n[3] Checking Python syntax...")
    results.append(check_syntax())

    # 4. Complete unit test suite
    print("\n[4] Running unit tests...")
    results.append(
        run_command(
            "Unit tests",
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "tests",
            ],
        )
    )

    # 5. Offline evaluation scenarios
    print("\n[5] Running evaluation scenarios...")
    results.append(
        run_command(
            "Evaluation scenarios",
            [
                sys.executable,
                "scripts/run_evaluation.py",
                "--no-json",
            ],
        )
    )

    # 6. End-to-end tests
    print("\n[6] Running end-to-end tests...")
    results.append(
        run_command(
            "End-to-end tests",
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "tests/test_end_to_end.py",
            ],
        )
    )

    # Final report
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status}: {result.name}")

        if result.details:
            print(f"      {result.details}")

    passed_count = sum(result.passed for result in results)
    failed_count = len(results) - passed_count

    print("\n" + "-" * 60)
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")

    if failed_count == 0:
        print("\nFINAL RESULT: SUCCESS")
        return 0

    print("\nFINAL RESULT: FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
