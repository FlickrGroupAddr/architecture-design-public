"""Queue one Codex alert when a Lightroom Classic probe replaces its JSON output."""

from __future__ import annotations

import argparse
import json
import msvcrt
import os
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

from watchfiles import watch

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import IO, Any

DEFAULT_QUIET_SECONDS = 0.75
DEFAULT_TIMEOUT_SECONDS = 86400.0
MAX_QUIET_SECONDS = 30.0
MAX_TIMEOUT_SECONDS = 86400.0


@dataclass(frozen=True)
class Config:
    """Validated one-shot monitor inputs."""

    output: Path
    output_label: str
    thread_id: str
    status_path: Path
    target_path: Path
    lock_path: Path
    quiet_seconds: float
    timeout_seconds: float


def now() -> str:
    """Return an unambiguous local timestamp."""

    return datetime.now(tz=UTC).astimezone().isoformat()


def write_atomic_json(path: Path, value: dict[str, object]) -> None:
    """Replace one transient control document without exposing a partial write."""

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


def file_signature(path: Path) -> tuple[int, int] | None:
    """Return a content-change signature without reading the probe output."""

    try:
        stat = path.stat()
    except FileNotFoundError:
        return None
    return stat.st_mtime_ns, stat.st_size


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


def alert_message(config: Config, observed_at: str) -> str:
    """Build a sanitized next-turn alert that never includes report content."""

    return (
        f"{config.output_label} output alert. A complete probe report was written to "
        f"{config.output} at {observed_at}. This one-shot notification was queued for "
        "the next Codex turn. Read and analyze the JSON document before asking Terry "
        "to perform another visible Lightroom Classic step. The monitor did not read "
        "or copy report content and has exited."
    )


def queue_alert(config: Config, observed_at: str) -> None:
    """Queue one sanitized alert to the latest registered thread."""

    target = read_json(config.target_path)
    if target.get("schema") != 1 or not isinstance(target.get("threadId"), str):
        raise ValueError("the probe monitor target file is invalid")
    try:
        thread_id = str(uuid.UUID(target["threadId"]))
    except ValueError as exc:
        raise ValueError("the probe monitor target thread ID is invalid") from exc

    codex = shutil.which("codex")
    if codex is None:
        raise RuntimeError("codex executable is not on PATH")
    completed = subprocess.run(  # noqa: S603 -- resolved executable, fixed arguments
        [codex, "queue", "--thread", thread_id, "--message", alert_message(config, observed_at)],
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


def parse_args(argv: Sequence[str] | None = None) -> Config:
    """Parse and validate monitor inputs."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-path", required=True, type=Path)
    parser.add_argument("--output-label", required=True)
    parser.add_argument("--thread-id", required=True)
    parser.add_argument("--status-path", required=True, type=Path)
    parser.add_argument("--target-path", required=True, type=Path)
    parser.add_argument("--lock-path", required=True, type=Path)
    parser.add_argument("--quiet-seconds", type=float, default=DEFAULT_QUIET_SECONDS)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args(argv)

    output_label = args.output_label.strip()
    if not output_label:
        parser.error("--output-label must not be empty")
    thread_id = str(uuid.UUID(args.thread_id))
    if not 0 < args.quiet_seconds <= MAX_QUIET_SECONDS:
        parser.error(f"--quiet-seconds must be greater than 0 and at most {MAX_QUIET_SECONDS:g}")
    if not 0 < args.timeout_seconds <= MAX_TIMEOUT_SECONDS:
        parser.error(
            f"--timeout-seconds must be greater than 0 and at most {MAX_TIMEOUT_SECONDS:g}"
        )
    return Config(
        args.output_path.resolve(strict=False),
        output_label,
        thread_id,
        args.status_path,
        args.target_path,
        args.lock_path,
        args.quiet_seconds,
        args.timeout_seconds,
    )


def monitor(config: Config) -> int:
    """Retarget an existing watcher or wait for one complete replacement."""

    write_atomic_json(
        config.target_path,
        {"schema": 1, "threadId": config.thread_id, "updatedAt": now()},
    )
    lock = acquire_lock(config.lock_path)
    if lock is None:
        print(f"Retargeted the existing {config.output_label} monitor.", flush=True)
        return 0

    started_at = now()
    started_monotonic = time.monotonic()
    baseline = file_signature(config.output)

    def status(state: str, **extra: object) -> None:
        write_atomic_json(
            config.status_path,
            {
                "schema": 1,
                "state": state,
                "pid": os.getpid(),
                "output": str(config.output),
                "startedAt": started_at,
                "baselineSignature": list(baseline) if baseline else None,
                "timeoutSeconds": config.timeout_seconds,
                **extra,
            },
        )

    try:
        config.output.parent.mkdir(parents=True, exist_ok=True)
        status("waiting")
        for changes in watch(
            config.output.parent,
            debounce=max(100, round(config.quiet_seconds * 1000)),
            step=50,
            recursive=False,
            rust_timeout=1000,
            yield_on_timeout=True,
        ):
            if time.monotonic() - started_monotonic >= config.timeout_seconds:
                status("expired", expiredAt=now())
                return 2
            if not any(
                os.path.normcase(str(Path(changed_path).resolve()))
                == os.path.normcase(str(config.output))
                for _change, changed_path in changes
            ):
                continue

            time.sleep(config.quiet_seconds)
            signature = file_signature(config.output)
            if signature is None or signature == baseline:
                continue
            observed_at = now()
            queue_alert(config, observed_at)
            status("alerted", observedAt=observed_at, observedSignature=list(signature))
            return 0
    except Exception as exc:
        status("failed", detail=str(exc))
        raise
    finally:
        release_lock(lock)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the one-shot watcher with a concise failure on stderr."""

    try:
        return monitor(parse_args(argv))
    except Exception as exc:  # noqa: BLE001 -- final CLI boundary reports monitor failures
        print(f"probe output monitor failed: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
