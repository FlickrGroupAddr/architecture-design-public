"""Start the graceful localswim shutdown coordinator and return promptly.

Codex permits a SessionEnd hook to run for at most three seconds. This small
launcher therefore creates an independent hidden process; the coordinator owns
the slower final-push and graceful-stop protocol after this hook returns.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COORDINATOR = PROJECT_ROOT / "scripts" / "stop_localswim_session.py"
UV_CACHE = Path(r"C:\Temp\localswim-uv-cache")
HOOK_STATUS = Path(r"C:\Temp\FGA-localswim-session-end-hook-status.json")
COORDINATOR_STDOUT = Path(r"C:\Temp\FGA-localswim-session-end.out.log")
COORDINATOR_STDERR = Path(r"C:\Temp\FGA-localswim-session-end.err.log")

# Win32 creation flags keep the coordinator independent and prevent a console window.
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000


def now() -> str:
    """Return one unambiguous local timestamp."""

    return datetime.now(tz=UTC).astimezone().isoformat()


def write_hook_status(state: str, *, detail: str | None = None) -> None:
    """Publish one sanitized trigger result without exposing a partial write."""

    value: dict[str, object] = {"schema": 1, "state": state, "updatedAt": now()}
    if detail:
        value["detail"] = detail[:500]
    HOOK_STATUS.parent.mkdir(parents=True, exist_ok=True)
    temporary = HOOK_STATUS.with_name(f"{HOOK_STATUS.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, separators=(",", ":")), encoding="utf-8")
    temporary.replace(HOOK_STATUS)


def coordinator_command(uv: Path) -> tuple[str, ...]:
    """Return the frozen uv command for the independent coordinator."""

    return (
        str(uv),
        "run",
        "--project",
        str(PROJECT_ROOT),
        "--frozen",
        "python",
        str(COORDINATOR),
    )


def launch_coordinator(
    *,
    environment: Mapping[str, str] | None = None,
    uv_command: str | None = None,
) -> int:
    """Launch the hidden coordinator and return its process identifier."""

    if os.name != "nt":
        raise RuntimeError("the SessionEnd shutdown launcher requires Windows")
    resolved_uv = uv_command or shutil.which("uv")
    if resolved_uv is None:
        raise RuntimeError("uv is not on PATH")
    uv = Path(resolved_uv).resolve(strict=True)
    COORDINATOR.resolve(strict=True)
    child_environment = dict(os.environ if environment is None else environment)
    child_environment.update(
        {
            "PYTHONIOENCODING": "utf-8",
            "UV_CACHE_DIR": str(UV_CACHE),
        }
    )
    COORDINATOR_STDOUT.parent.mkdir(parents=True, exist_ok=True)
    with (
        COORDINATOR_STDOUT.open("ab") as stdout,
        COORDINATOR_STDERR.open("ab") as stderr,
    ):
        process = subprocess.Popen(  # noqa: S603 -- resolved uv and fixed arguments
            coordinator_command(uv),
            cwd=PROJECT_ROOT,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            env=child_environment,
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
            close_fds=True,
        )
    return process.pid


def main(_argv: Sequence[str] | None = None) -> int:
    """Launch the coordinator within the SessionEnd deadline."""

    with suppress(OSError):
        write_hook_status("launching")
    try:
        pid = launch_coordinator()
    except Exception as exc:  # noqa: BLE001 -- final hook boundary
        with suppress(OSError):
            write_hook_status("error", detail=str(exc))
        print(f"localswim SessionEnd trigger failed: {exc}", file=sys.stderr, flush=True)
        return 1
    print(f"Started detached graceful localswim shutdown coordinator (PID {pid}).", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
