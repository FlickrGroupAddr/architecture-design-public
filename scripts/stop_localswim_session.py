"""Stop both localswim monitors and services during a clean Codex session exit."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if __package__:
    from .start_localswim_session import BOARDS, SESSION_LIFECYCLE_LOCK, BoardConfig
    from .watch_localswim import acquire_lock, read_json, release_lock, write_atomic_json
else:
    from start_localswim_session import BOARDS, SESSION_LIFECYCLE_LOCK, BoardConfig
    from watch_localswim import acquire_lock, read_json, release_lock, write_atomic_json

if TYPE_CHECKING:
    from collections.abc import Sequence

HOOK_STATUS = Path(r"C:\Temp\FGA-localswim-session-end-hook-status.json")
MONITOR_STOP_TIMEOUT_SECONDS = 15.0
SERVICE_STOP_TIMEOUT_SECONDS = 145


def now() -> str:
    """Return one unambiguous local timestamp."""
    return datetime.now(tz=UTC).astimezone().isoformat()


def write_hook_status(
    state: str,
    *,
    detail: str | None = None,
    coordinator_pid: int | None = None,
) -> None:
    """Publish one sanitized SessionEnd result through an atomic handoff."""
    value: dict[str, object] = {
        "schema": 1,
        "state": state,
        "updatedAt": now(),
    }
    if detail:
        value["detail"] = detail[:500]
    if coordinator_pid is not None:
        value["coordinatorPid"] = coordinator_pid
    write_atomic_json(HOOK_STATUS, value)


def request_monitor_stop(config: BoardConfig) -> int | None:
    """Request a clean stop from one running monitor and return its exact PID."""
    lock = acquire_lock(config.monitor_lock)
    if lock is not None:
        release_lock(lock)
        return None

    status = read_json(config.monitor_status)
    pid = status.get("pid")
    if status.get("state") not in {"running", "stopping"} or not isinstance(pid, int) or pid <= 0:
        raise RuntimeError(f"{config.name} monitor has no valid running-process status")
    if os.path.normcase(str(status.get("board"))) != os.path.normcase(str(config.board)):
        raise RuntimeError(f"{config.name} monitor status names an unexpected board")

    target = read_json(config.monitor_target)
    thread_id = target.get("threadId")
    if target.get("schema") != 1 or not isinstance(thread_id, str):
        raise RuntimeError(f"{config.name} monitor target is invalid")
    write_atomic_json(
        config.monitor_target,
        {
            "schema": 1,
            "threadId": thread_id,
            "stopPid": pid,
            "updatedAt": now(),
        },
    )
    return pid


def cancel_monitor_stop(config: BoardConfig, pid: int | None) -> None:
    """Cancel this hook's stop request when the paired service refuses shutdown."""
    if pid is None:
        return
    target = read_json(config.monitor_target)
    if target.get("stopPid") != pid:
        return
    thread_id = target.get("threadId")
    if target.get("schema") != 1 or not isinstance(thread_id, str):
        raise RuntimeError(f"{config.name} monitor target is invalid")
    write_atomic_json(
        config.monitor_target,
        {"schema": 1, "threadId": thread_id, "updatedAt": now()},
    )


def wait_for_monitor_stop(config: BoardConfig) -> None:
    """Wait until one monitor releases its exclusive lifetime lock."""
    deadline = time.monotonic() + MONITOR_STOP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        lock = acquire_lock(config.monitor_lock)
        if lock is not None:
            release_lock(lock)
            return
        time.sleep(0.1)
    raise RuntimeError(f"{config.name} monitor did not stop cleanly")


def stop_service(config: BoardConfig, cli: str) -> None:
    """Ask one service to final-push and shut down through localswim-cli."""
    completed = subprocess.run(  # noqa: S603 -- resolved installed CLI and fixed arguments
        (cli, str(config.board), "board", "shutdown"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=SERVICE_STOP_TIMEOUT_SECONDS,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "no diagnostic output").strip()
        raise RuntimeError(f"{config.name} service shutdown failed: {detail[:300]}")


def run() -> int:
    """Stop monitors and services without terminating any process forcibly."""
    cli = shutil.which("localswim-cli")
    if cli is None:
        raise RuntimeError("localswim-cli is not on PATH")

    monitors: dict[str, int | None] = {}
    try:
        for config in BOARDS:
            monitors[config.name] = request_monitor_stop(config)
    except OSError, TypeError, ValueError, RuntimeError:
        for requested_config in BOARDS:
            if requested_config.name not in monitors:
                continue
            with suppress(OSError, TypeError, ValueError, RuntimeError):
                cancel_monitor_stop(requested_config, monitors[requested_config.name])
        raise
    failures: list[str] = []
    stopped: list[BoardConfig] = []
    for config in BOARDS:
        try:
            stop_service(config, cli)
        except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
            with suppress(OSError, TypeError, ValueError, RuntimeError):
                cancel_monitor_stop(config, monitors[config.name])
            failures.append(str(exc))
        else:
            stopped.append(config)

    for config in stopped:
        try:
            wait_for_monitor_stop(config)
        except RuntimeError as exc:
            failures.append(str(exc))
    if failures:
        raise RuntimeError("; ".join(failures))
    return 0


def main(_argv: Sequence[str] | None = None) -> int:
    """Run the detached shutdown coordinator with concise status output."""

    lifecycle_lock = acquire_lock(SESSION_LIFECYCLE_LOCK)
    if lifecycle_lock is None:
        print("A graceful localswim shutdown coordinator is already running.", flush=True)
        return 0
    try:
        with suppress(OSError):
            write_hook_status("stopping", coordinator_pid=os.getpid())
        try:
            result = run()
        except Exception as exc:  # noqa: BLE001 -- final coordinator boundary
            with suppress(OSError):
                write_hook_status("error", detail=str(exc), coordinator_pid=os.getpid())
            print(f"localswim shutdown coordinator failed: {exc}", file=sys.stderr, flush=True)
            return 1
        with suppress(OSError):
            write_hook_status("stopped", coordinator_pid=os.getpid())
        print("Stopped both localswim services and board monitors cleanly.", flush=True)
        return result
    finally:
        release_lock(lifecycle_lock)


if __name__ == "__main__":
    raise SystemExit(main())
