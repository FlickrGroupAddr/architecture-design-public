"""Queue one next-turn Codex alert after a burst of localswim board writes.

The mature MIT-licensed ``watchfiles`` package supplies native Windows filesystem
notifications. This script never reads or logs board content. It records only file
signatures and timestamps beneath ``C:\\Temp``, coalesces related writes across a
quiet window, then queues a bounded ``localswim-cli`` activity query for the target
thread's next turn.
"""

from __future__ import annotations

import argparse
import json
import msvcrt
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

from watchfiles import watch

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import IO, Any

    from watchfiles import Change

MAX_PORT = 65535
MAX_SERVICE_MISSES = 5
DEFAULT_QUIET_SECONDS = 15.0
MAX_QUIET_SECONDS = 300.0


@dataclass(frozen=True)
class Config:
    """Validated monitor inputs."""

    board: Path
    board_label: str
    thread_id: str
    port: int
    status_path: Path
    target_path: Path
    lock_path: Path
    quiet_seconds: float


@dataclass(frozen=True)
class PendingAlert:
    """Sanitized metadata for board writes waiting on the quiet window."""

    activity_started_at: str
    first_observed_at: str
    last_observed_at: str
    last_write_monotonic: float
    write_count: int


@dataclass
class MonitorRuntime:
    """Mutable sanitized state for one running monitor."""

    last_signature: tuple[int, int]
    last_signature_at: str
    last_alert_at: str | None = None
    pending_alert: PendingAlert | None = None
    service_misses: int = 0
    stopping: bool = False


def note_board_write(
    pending: PendingAlert | None,
    *,
    activity_started_at: str,
    observed_at: str,
    observed_monotonic: float,
) -> PendingAlert:
    """Start or extend one trailing-edge debounce and activity-query window."""

    if pending is None:
        return PendingAlert(
            activity_started_at,
            observed_at,
            observed_at,
            observed_monotonic,
            1,
        )
    return PendingAlert(
        pending.activity_started_at,
        pending.first_observed_at,
        observed_at,
        observed_monotonic,
        pending.write_count + 1,
    )


def quiet_window_elapsed(
    pending: PendingAlert,
    *,
    current_monotonic: float,
    quiet_seconds: float,
) -> bool:
    """Report whether a pending burst has seen the configured quiet period."""

    return current_monotonic - pending.last_write_monotonic >= quiet_seconds


def now() -> str:
    """Return an unambiguous local timestamp."""

    return datetime.now(tz=UTC).astimezone().isoformat()


def activity_query_bound(stamp: str) -> str:
    """Return one monitor cursor at localswim's persisted event precision."""

    instant = datetime.fromisoformat(stamp)
    if instant.tzinfo is None:
        raise ValueError("an activity query bound needs a UTC offset")
    return instant.isoformat(timespec="microseconds")


def write_atomic_json(path: Path, value: dict[str, object]) -> None:
    """Replace one transient status document without exposing a partial write."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, separators=(",", ":")), encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path) -> dict[str, Any]:
    """Read one monitor-owned transient document."""

    value = cast("object", json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(value, dict):
        raise TypeError(f"expected a JSON object in {path}")
    return cast("dict[str, Any]", value)


def stop_requested(path: Path, pid: int) -> bool:
    """Return whether the monitor target asks this exact process to stop."""
    try:
        target = read_json(path)
    except OSError, TypeError, ValueError:
        return False
    return target.get("schema") == 1 and target.get("stopPid") == pid


def board_signature(path: Path) -> tuple[int, int]:
    """Wait briefly for an atomically replaced board path, then stat it."""

    for _attempt in range(20):
        try:
            stat = path.stat()
        except FileNotFoundError:
            time.sleep(0.025)
        else:
            return stat.st_mtime_ns, stat.st_size
    raise RuntimeError(f"board did not become readable after a filesystem event: {path}")


def acquire_lock(path: Path) -> IO[bytes] | None:
    """Own one byte of a Windows lock file, or report an existing monitor."""

    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    if handle.seek(0, os.SEEK_END) == 0:
        handle.write(b"0")
        handle.flush()
    handle.seek(0)
    try:
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        handle.close()
        return None
    return handle


def release_lock(handle: IO[bytes]) -> None:
    """Release the byte-range lock held for the monitor lifetime."""

    handle.seek(0)
    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    handle.close()


def service_is_healthy(port: int) -> bool:
    """Check the loopback service without reading private board content."""

    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/v001/status", timeout=1
        ) as response:
            status = cast("object", json.load(response))
    except OSError, TimeoutError, ValueError:
        return False
    return isinstance(status, dict) and cast("dict[str, object]", status).get("ok") is True


def handle_idle_cycle(
    config: Config,
    codex: str,
    runtime: MonitorRuntime,
    publish_status: Callable[[str], None],
) -> None:
    """Update health and flush any alert whose quiet window has elapsed."""
    if service_is_healthy(config.port):
        runtime.service_misses = 0
    else:
        runtime.service_misses += 1
    if runtime.pending_alert is not None and quiet_window_elapsed(
        runtime.pending_alert,
        current_monotonic=time.monotonic(),
        quiet_seconds=config.quiet_seconds,
    ):
        runtime.last_alert_at = flush_pending_alert(config, codex, runtime.pending_alert)
        runtime.pending_alert = None
        publish_status("running")
    if runtime.service_misses >= MAX_SERVICE_MISSES and runtime.pending_alert is None:
        message = "localswim was unavailable for five consecutive checks"
        raise RuntimeError(message)


def queue_alert(config: Config, codex: str, pending: PendingAlert) -> None:
    """Queue a sanitized next-turn alert to the registered Codex thread."""

    target = read_json(config.target_path)
    if target.get("schema") != 1 or not isinstance(target.get("threadId"), str):
        raise ValueError("the monitor target file is invalid")
    try:
        thread_id = str(uuid.UUID(target["threadId"]))
    except ValueError as exc:
        raise ValueError("the monitor target thread ID is invalid") from exc

    write_summary = (
        "1 board write was observed"
        if pending.write_count == 1
        else f"{pending.write_count} board writes were coalesced"
    )
    activity_start = activity_query_bound(pending.activity_started_at)
    activity_end = activity_query_bound(pending.last_observed_at)
    message = (
        f"{config.board_label} next-turn board-write alert. {write_summary} after a "
        f"{config.quiet_seconds:g}-second quiet window. This notification was queued "
        "for the next Codex turn; it does not acknowledge delivery to the turn that "
        "was active when the write occurred. Inspect the persistent board "
        "through localswim-cli for new cards, comments, assignments, relationships, "
        "or moves. Do not edit the JSON directly. Use activity between "
        f"{activity_start} {activity_end}; those bounds enclose the change interval "
        "at the board event log's precision. "
        f"First observed at {pending.first_observed_at}; last observed at "
        f"{pending.last_observed_at}."
    )
    completed = subprocess.run(  # noqa: S603 -- resolved executable, fixed arguments
        [codex, "queue", "--thread", thread_id, "--message", message],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "no diagnostic output").splitlines()[0]
        raise RuntimeError(f"codex queue failed: {detail[:300]}")


def flush_pending_alert(config: Config, codex: str, pending: PendingAlert) -> str:
    """Queue one completed burst and return its queue timestamp."""

    queue_alert(config, codex, pending)
    alerted_at = now()
    print(
        f"Queued one next-turn alert for {pending.write_count} board write(s) ending at "
        f"{pending.last_observed_at}.",
        flush=True,
    )
    return alerted_at


def parse_args(argv: Sequence[str] | None = None) -> Config:
    """Parse and validate process inputs."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board-path", required=True, type=Path)
    parser.add_argument(
        "--board-label",
        default="FGA localswim",
        help="sanitized board name used in queued alerts",
    )
    parser.add_argument("--thread-id", required=True)
    parser.add_argument("--port", type=int, default=8793)
    parser.add_argument(
        "--status-path",
        type=Path,
        default=Path(r"C:\Temp\FGA-localswim-monitor-status.json"),
    )
    parser.add_argument(
        "--target-path",
        type=Path,
        default=Path(r"C:\Temp\FGA-localswim-monitor-target.json"),
    )
    parser.add_argument(
        "--lock-path",
        type=Path,
        default=Path(r"C:\Temp\FGA-localswim-monitor.lock"),
    )
    parser.add_argument(
        "--quiet-seconds",
        type=float,
        default=DEFAULT_QUIET_SECONDS,
        help="seconds without another board write before one coalesced alert",
    )
    args = parser.parse_args(argv)
    board = args.board_path.resolve(strict=True)
    board_label = args.board_label.strip()
    if not board_label:
        parser.error("--board-label must not be empty")
    thread_id = str(uuid.UUID(args.thread_id))
    if not 1 <= args.port <= MAX_PORT:
        parser.error(f"--port must be between 1 and {MAX_PORT}")
    if not 0 < args.quiet_seconds <= MAX_QUIET_SECONDS:
        parser.error(f"--quiet-seconds must be greater than 0 and at most {MAX_QUIET_SECONDS:g}")
    return Config(
        board,
        board_label,
        thread_id,
        args.port,
        args.status_path,
        args.target_path,
        args.lock_path,
        args.quiet_seconds,
    )


def monitor(config: Config) -> int:
    """Retarget an existing watcher or monitor until localswim stops."""

    write_atomic_json(
        config.target_path,
        {"schema": 1, "threadId": config.thread_id, "updatedAt": now()},
    )
    lock = acquire_lock(config.lock_path)
    if lock is None:
        print(f"Retargeted the existing {config.board_label} monitor.", flush=True)
        return 0

    codex = shutil.which("codex")
    if codex is None:
        release_lock(lock)
        raise RuntimeError("codex executable is not on PATH")

    started_at = now()
    runtime = MonitorRuntime(board_signature(config.board), started_at)

    def status(state: str, **extra: object) -> None:
        write_atomic_json(
            config.status_path,
            {
                "schema": 1,
                "state": state,
                "pid": os.getpid(),
                "board": str(config.board),
                "startedAt": started_at,
                "lastSignature": list(runtime.last_signature),
                "lastSignatureAt": runtime.last_signature_at,
                "lastAlertAt": runtime.last_alert_at,
                "quietSeconds": config.quiet_seconds,
                "pendingWriteCount": (
                    0 if runtime.pending_alert is None else runtime.pending_alert.write_count
                ),
                "pendingFirstObservedAt": (
                    None
                    if runtime.pending_alert is None
                    else runtime.pending_alert.first_observed_at
                ),
                "pendingActivityStartedAt": (
                    None
                    if runtime.pending_alert is None
                    else runtime.pending_alert.activity_started_at
                ),
                "pendingLastObservedAt": (
                    None
                    if runtime.pending_alert is None
                    else runtime.pending_alert.last_observed_at
                ),
                **extra,
            },
        )

    def only_board(_change: Change, changed_path: str) -> bool:
        return os.path.normcase(str(Path(changed_path).resolve())) == os.path.normcase(
            str(config.board)
        )

    try:
        status("running")
        print(f"Watching {config.board} for Codex thread alerts.", flush=True)
        for changes in watch(
            config.board.parent,
            watch_filter=only_board,
            debounce=100,
            step=20,
            recursive=False,
            rust_timeout=1000,
            yield_on_timeout=True,
        ):
            if stop_requested(config.target_path, os.getpid()):
                if service_is_healthy(config.port):
                    if not runtime.stopping:
                        status("stopping")
                    runtime.stopping = True
                    continue
                status("stopped")
                print(f"Stopped the {config.board_label} monitor cleanly.", flush=True)
                return 0
            if runtime.stopping:
                runtime.stopping = False
                status("running")
            if not changes:
                handle_idle_cycle(config, codex, runtime, status)
                continue

            time.sleep(0.05)
            signature = board_signature(config.board)
            if signature == runtime.last_signature:
                continue
            runtime.last_signature = signature
            observed_at = now()
            runtime.pending_alert = note_board_write(
                runtime.pending_alert,
                activity_started_at=runtime.last_signature_at,
                observed_at=observed_at,
                observed_monotonic=time.monotonic(),
            )
            runtime.last_signature_at = observed_at
            status("running")
            print(
                f"Debouncing board write {runtime.pending_alert.write_count} at {observed_at}.",
                flush=True,
            )
    except Exception as exc:
        status("failed", detail=str(exc))
        raise
    finally:
        release_lock(lock)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the monitor with a concise failure on stderr."""

    try:
        return monitor(parse_args(argv))
    except Exception as exc:  # noqa: BLE001 -- final CLI boundary reports all monitor failures
        print(f"localswim monitor failed: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
