"""Run the complete FGA Python quality gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent


def run_check(label: str, arguments: list[str]) -> None:
    """Run one fixed project check and stop on failure."""

    print(label, flush=True)
    completed = subprocess.run(  # noqa: S603 - fixed local project tools only
        [sys.executable, *arguments],
        cwd=REPOSITORY_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        message = f"{label} failed with exit code {completed.returncode}."
        raise RuntimeError(message)


def main() -> None:
    """Run formatting, linting, typing, and tests in order."""

    run_check("Ruff format", ["-m", "ruff", "format", "--check", "scripts", "tests"])
    run_check("Ruff lint", ["-m", "ruff", "check", "scripts", "tests"])
    run_check("Pyright", ["-m", "pyright", "scripts", "tests"])
    run_check(
        "Unit tests",
        ["-m", "unittest", "discover", "-s", "tests", "-v"],
    )


if __name__ == "__main__":
    main()
