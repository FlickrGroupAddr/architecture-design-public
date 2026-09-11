"""Tests for debounced localswim board-write alerts."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.watch_localswim import (
    Config,
    PendingAlert,
    activity_query_bound,
    monitor,
    note_board_write,
    queue_alert,
    quiet_window_elapsed,
    stop_requested,
)


class WatchLocalswimTests(unittest.TestCase):
    def test_stop_request_targets_one_exact_monitor_process(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = Path(temporary_directory) / "target.json"
            target.write_text(
                json.dumps({"schema": 1, "threadId": str(uuid.uuid4()), "stopPid": 1234}),
                encoding="utf-8",
            )

            self.assertTrue(stop_requested(target, 1234))
            self.assertFalse(stop_requested(target, 5678))

    def test_missing_or_malformed_stop_request_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = Path(temporary_directory) / "target.json"
            self.assertFalse(stop_requested(target, 1234))
            target.write_text("not JSON", encoding="utf-8")
            self.assertFalse(stop_requested(target, 1234))

    @patch("scripts.watch_localswim.os.getpid", return_value=1234)
    @patch("scripts.watch_localswim.service_is_healthy", side_effect=(True, False))
    @patch("scripts.watch_localswim.shutil.which", return_value="codex")
    @patch("scripts.watch_localswim.watch")
    def test_monitor_waits_for_service_then_stops_cleanly(
        self,
        watch: MagicMock,
        which: MagicMock,
        service_is_healthy: MagicMock,
        getpid: MagicMock,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            board = root / "board.json"
            board.write_text("{}", encoding="utf-8")
            thread_id = str(uuid.uuid4())
            config = Config(
                board=board,
                board_label="test board",
                thread_id=thread_id,
                port=8793,
                status_path=root / "status.json",
                target_path=root / "target.json",
                lock_path=root / "monitor.lock",
                quiet_seconds=15.0,
            )

            def changes(*_args: object, **_kwargs: object) -> list[set[object]]:
                config.target_path.write_text(
                    json.dumps({"schema": 1, "threadId": thread_id, "stopPid": 1234}),
                    encoding="utf-8",
                )
                return [set(), set()]

            watch.side_effect = changes

            self.assertEqual(monitor(config), 0)
            status = json.loads(config.status_path.read_text(encoding="utf-8"))

        which.assert_called_once_with("codex")
        self.assertEqual(service_is_healthy.call_count, 2)
        self.assertGreaterEqual(getpid.call_count, 1)
        self.assertEqual(status["state"], "stopped")

    def test_note_board_write_extends_one_trailing_edge_window(self) -> None:
        pending = note_board_write(
            None,
            activity_started_at="2026-08-22T12:34:40.987654-04:00",
            observed_at="2026-08-22T12:34:42.123456-04:00",
            observed_monotonic=100.0,
        )
        pending = note_board_write(
            pending,
            activity_started_at="2026-08-22T12:34:42.123456-04:00",
            observed_at="2026-08-22T12:34:52.654321-04:00",
            observed_monotonic=110.0,
        )

        self.assertEqual(pending.activity_started_at, "2026-08-22T12:34:40.987654-04:00")
        self.assertEqual(pending.first_observed_at, "2026-08-22T12:34:42.123456-04:00")
        self.assertEqual(pending.last_observed_at, "2026-08-22T12:34:52.654321-04:00")
        self.assertEqual(pending.last_write_monotonic, 110.0)
        self.assertEqual(pending.write_count, 2)
        self.assertFalse(
            quiet_window_elapsed(
                pending,
                current_monotonic=124.999,
                quiet_seconds=15.0,
            )
        )
        self.assertTrue(
            quiet_window_elapsed(
                pending,
                current_monotonic=125.0,
                quiet_seconds=15.0,
            )
        )

    def test_activity_query_bound_matches_board_event_precision(self) -> None:
        self.assertEqual(
            activity_query_bound("2026-08-24T11:27:37.846721-04:00"),
            "2026-08-24T11:27:37.846721-04:00",
        )

    def test_queue_alert_reports_one_coalesced_burst(self) -> None:
        thread_id = str(uuid.uuid4())
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target_path = root / "target.json"
            target_path.write_text(
                json.dumps({"schema": 1, "threadId": thread_id}),
                encoding="utf-8",
            )
            config = Config(
                board=root / "board.json",
                board_label="localswim inception",
                thread_id=thread_id,
                port=8793,
                status_path=root / "status.json",
                target_path=target_path,
                lock_path=root / "monitor.lock",
                quiet_seconds=15.0,
            )
            pending = PendingAlert(
                activity_started_at="2026-08-22T12:34:40.987654-04:00",
                first_observed_at="2026-08-22T12:34:42.123456-04:00",
                last_observed_at="2026-08-22T12:35:01.654321-04:00",
                last_write_monotonic=119.0,
                write_count=4,
            )

            with patch("scripts.watch_localswim.subprocess.run") as run:
                run.return_value = subprocess.CompletedProcess([], 0, "", "")
                queue_alert(config, "codex", pending)

        command = run.call_args.args[0]
        message = command[command.index("--message") + 1]
        self.assertIn("4 board writes were coalesced", message)
        self.assertIn("localswim inception next-turn board-write alert", message)
        self.assertIn("15-second quiet window", message)
        self.assertIn("queued for the next Codex turn", message)
        self.assertIn("does not acknowledge delivery", message)
        self.assertIn(pending.first_observed_at, message)
        self.assertIn(pending.last_observed_at, message)
        self.assertIn("localswim-cli", message)
        self.assertIn(
            "activity between 2026-08-22T12:34:40.987654-04:00 2026-08-22T12:35:01.654321-04:00",
            message,
        )


if __name__ == "__main__":
    unittest.main()
