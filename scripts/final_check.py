
import compileall
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent


def main():
    print("\n" + "=" * 55)
    print("MINI CLASSBUILD - FINAL VERIFICATION")
    print("=" * 55)

    # Ensure the project root is importable.
    sys.path.insert(0, str(ROOT))

    # 1. Compile project files.
    print("\n[1/2] Checking Python syntax...")

    folders = [
        ROOT / "classbuild",
        ROOT / "scripts",
        ROOT / "tests",
    ]

    syntax_ok = all(
        compileall.compile_dir(
            str(folder),
            quiet=1,
            force=True,
        )
        for folder in folders
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

    if syntax_ok:
        print("PASS: Python syntax check")
    else:
        print("FAIL: Python syntax check")
        return 1

    # 2. Run the complete test suite.
    print("\n[2/2] Running automated tests...")

    exit_code = pytest.main(
        ["-q", str(ROOT / "tests")]
    )

    if exit_code == pytest.ExitCode.OK:
        print("\nPASS: All automated tests")
        print("\nFINAL RESULT: SUCCESS")
        return 0

    print("\nFAIL: Automated tests")
    print("\nFINAL RESULT: FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
