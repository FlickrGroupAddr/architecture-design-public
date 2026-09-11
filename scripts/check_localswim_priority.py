"""Refuse an FGA handoff while the localswim inception board has actionable work."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

if __package__:
    from .start_localswim_session import BOARDS
else:
    from start_localswim_session import BOARDS

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

ACTIONABLE_LANES = ("ready_for_work", "in_progress")
BLOCKED_EXIT = 1


@dataclass(frozen=True)
class InceptionWork:
    """Sanitized identity for the highest-priority actionable inception card."""

    ticket: int
    item_id: str
    state: str
    priority: str

    @classmethod
    def from_json(cls, value: object) -> InceptionWork:
        """Validate the small subset of one CLI item that the barrier may expose."""
        if not isinstance(value, dict):
            raise TypeError("localswim-cli returned a non-object card")
        item = cast("dict[str, object]", value)
        ticket = item.get("ticket")
        item_id = item.get("id")
        state = item.get("state")
        priority = item.get("priority")
        if not isinstance(ticket, int) or ticket < 1:
            raise TypeError("localswim-cli returned an invalid ticket number")
        if not isinstance(item_id, str) or not item_id:
            raise TypeError("localswim-cli returned an invalid card id")
        if not isinstance(state, str) or state not in ACTIONABLE_LANES:
            raise TypeError("localswim-cli returned an unexpected card state")
        if not isinstance(priority, str) or not priority:
            raise TypeError("localswim-cli returned an invalid card priority")
        return cls(ticket, item_id, state, priority)


def inception_board() -> Path:
    """Return the single configured inception-board path."""
    matches = [config.board for config in BOARDS if config.name == "localswim inception"]
    if len(matches) != 1:
        raise RuntimeError("exactly one localswim inception board must be configured")
    return matches[0]


def next_actionable(cli: str, board: Path) -> InceptionWork | None:
    """Query the authoritative board through the installed command-oriented CLI."""
    command = [cli, str(board), "card", "next", "1"]
    for lane in ACTIONABLE_LANES:
        command.extend(("--lane", lane))
    command.append("--json")
    completed = subprocess.run(  # noqa: S603 -- resolved executable and fixed arguments
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "no diagnostic output").strip()
        raise RuntimeError(f"localswim inception priority query failed: {detail[:300]}")
    report_value = cast("object", json.loads(completed.stdout))
    if not isinstance(report_value, dict):
        raise TypeError("localswim-cli returned an invalid prioritized-card report")
    report = cast("dict[str, object]", report_value)
    if not isinstance(report.get("items"), list):
        raise TypeError("localswim-cli returned an invalid prioritized-card report")
    items = cast("list[object]", report["items"])
    return InceptionWork.from_json(items[0]) if items else None


def run() -> int:
    """Return nonzero when inception work must run before any FGA task."""
    cli = shutil.which("localswim-cli")
    if cli is None:
        raise RuntimeError("localswim-cli is not on PATH")
    work = next_actionable(cli, inception_board())
    if work is None:
        print("localswim inception priority clear")
        return 0
    print(
        "localswim inception priority blocks FGA: "
        f"#{work.ticket:04d} {work.item_id} ({work.priority}, {work.state})"
    )
    return BLOCKED_EXIT


def main(_argv: Sequence[str] | None = None) -> int:
    """Run the priority barrier with a concise failure boundary."""
    try:
        return run()
    except (OSError, TypeError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"localswim inception priority check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
