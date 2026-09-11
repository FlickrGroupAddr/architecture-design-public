"""Tests for the localswim SessionEnd shutdown orchestrator."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from scripts.start_localswim_session import BoardConfig
from scripts.stop_localswim_session import (
    cancel_monitor_stop,
    main,
    request_monitor_stop,
    run,
    stop_service,
)
from tests.lifecycle_test_support import IsolatedLifecycleTestCase


def board_config(root: Path) -> BoardConfig:
    """Build one isolated board configuration."""
    return BoardConfig(
        "test",
        root / "board.json",
        "test board",
        root,
        root / "service.out.log",
        root / "service.err.log",
        root / "monitor-status.json",
        root / "monitor-target.json",
        root / "monitor.lock",
        root / "monitor.out.log",
        root / "monitor.err.log",
    )


class MonitorStopTests(IsolatedLifecycleTestCase):
    @patch("scripts.stop_localswim_session.acquire_lock", return_value=None)
    def test_stop_request_targets_status_pid(self, acquire_lock: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config = board_config(Path(temporary_directory))
            config.monitor_status.write_text(
                json.dumps(
                    {
                        "state": "running",
                        "pid": 1234,
                        "board": str(config.board),
                    }
                ),
                encoding="utf-8",
            )
            config.monitor_target.write_text(
                json.dumps({"schema": 1, "threadId": "thread-id"}),
                encoding="utf-8",
            )

            self.assertEqual(request_monitor_stop(config), 1234)
            target = json.loads(config.monitor_target.read_text(encoding="utf-8"))

        acquire_lock.assert_called_once_with(config.monitor_lock)
        self.assertEqual(target["schema"], 1)
        self.assertEqual(target["threadId"], "thread-id")
        self.assertEqual(target["stopPid"], 1234)

    def test_cancel_removes_only_matching_stop_request(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config = board_config(Path(temporary_directory))
            config.monitor_target.write_text(
                json.dumps({"schema": 1, "threadId": "thread-id", "stopPid": 1234}),
                encoding="utf-8",
            )

            cancel_monitor_stop(config, 1234)
            target = json.loads(config.monitor_target.read_text(encoding="utf-8"))

        self.assertEqual(target["schema"], 1)
        self.assertEqual(target["threadId"], "thread-id")
        self.assertNotIn("stopPid", target)


class ServiceStopTests(IsolatedLifecycleTestCase):
    @patch("scripts.stop_localswim_session.subprocess.run")
    def test_stop_uses_click_command_tree(self, run_process: MagicMock) -> None:
        run_process.return_value.returncode = 0
        config = board_config(self.test_root / "service-stop")

        stop_service(config, "localswim-cli")

        self.assertEqual(
            run_process.call_args.args[0],
            ("localswim-cli", str(config.board), "board", "shutdown"),
        )


class ShutdownRunTests(IsolatedLifecycleTestCase):
    @patch("scripts.stop_localswim_session.cancel_monitor_stop")
    @patch("scripts.stop_localswim_session.stop_service")
    @patch(
        "scripts.stop_localswim_session.request_monitor_stop",
        side_effect=(101, RuntimeError("bad monitor status")),
    )
    @patch("scripts.stop_localswim_session.shutil.which", return_value="localswim-cli")
    def test_run_cancels_earlier_request_when_later_monitor_is_invalid(
        self,
        which: MagicMock,
        request_stop: MagicMock,
        stop_service: MagicMock,
        cancel_monitor_stop: MagicMock,
    ) -> None:
        try:
            run()
        except RuntimeError as exc:
            self.assertIn("bad monitor status", str(exc))
        else:
            self.fail("invalid monitor status was not reported")

        which.assert_called_once_with("localswim-cli")
        self.assertEqual(request_stop.call_count, 2)
        stop_service.assert_not_called()
        cancel_monitor_stop.assert_called_once_with(self.boards[0], 101)

    @patch("scripts.stop_localswim_session.wait_for_monitor_stop")
    @patch("scripts.stop_localswim_session.stop_service")
    @patch("scripts.stop_localswim_session.request_monitor_stop", side_effect=(101, 202))
    @patch("scripts.stop_localswim_session.shutil.which", return_value="localswim-cli")
    def test_run_stops_both_services_then_waits_for_monitors(
        self,
        which: MagicMock,
        request_stop: MagicMock,
        stop_service: MagicMock,
        wait_for_monitor_stop: MagicMock,
    ) -> None:
        self.assertEqual(run(), 0)

        which.assert_called_once_with("localswim-cli")
        self.assertEqual(request_stop.call_count, 2)
        self.assertEqual(stop_service.call_count, 2)
        self.assertEqual(
            wait_for_monitor_stop.call_args_list,
            [call(config) for config in self.boards],
        )

    @patch("scripts.stop_localswim_session.cancel_monitor_stop")
    @patch("scripts.stop_localswim_session.wait_for_monitor_stop")
    @patch(
        "scripts.stop_localswim_session.stop_service",
        side_effect=(RuntimeError("push failed"), None),
    )
    @patch("scripts.stop_localswim_session.request_monitor_stop", side_effect=(101, 202))
    @patch("scripts.stop_localswim_session.shutil.which", return_value="localswim-cli")
    def test_run_cancels_monitor_when_service_refuses_shutdown(
        self,
        which: MagicMock,
        request_stop: MagicMock,
        stop_service: MagicMock,
        wait_for_monitor_stop: MagicMock,
        cancel_monitor_stop: MagicMock,
    ) -> None:
        try:
            run()
        except RuntimeError as exc:
            self.assertIn("push failed", str(exc))
        else:
            self.fail("shutdown failure was not reported")

        which.assert_called_once_with("localswim-cli")
        self.assertEqual(request_stop.call_count, 2)
        self.assertEqual(stop_service.call_count, 2)
        cancel_monitor_stop.assert_called_once_with(self.boards[0], 101)
        wait_for_monitor_stop.assert_called_once_with(self.boards[1])


class CoordinatorTests(IsolatedLifecycleTestCase):
    """Own the cross-session lifecycle lock for the full graceful shutdown."""

    @patch("scripts.stop_localswim_session.release_lock")
    @patch("scripts.stop_localswim_session.write_hook_status")
    @patch("scripts.stop_localswim_session.run", return_value=0)
    @patch("scripts.stop_localswim_session.acquire_lock")
    @patch("scripts.stop_localswim_session.os.getpid", return_value=4321)
    def test_coordinator_records_completion_and_releases_lock(
        self,
        getpid: MagicMock,
        acquire_lock: MagicMock,
        run_shutdown: MagicMock,
        write_hook_status: MagicMock,
        release_lock: MagicMock,
    ) -> None:
        lock = MagicMock()
        acquire_lock.return_value = lock

        self.assertEqual(main(), 0)

        getpid.assert_called()
        run_shutdown.assert_called_once_with()
        self.assertEqual(
            write_hook_status.call_args_list,
            [
                call("stopping", coordinator_pid=4321),
                call("stopped", coordinator_pid=4321),
            ],
        )
        release_lock.assert_called_once_with(lock)

    @patch("scripts.stop_localswim_session.release_lock")
    @patch("scripts.stop_localswim_session.run")
    @patch("scripts.stop_localswim_session.acquire_lock", return_value=None)
    def test_duplicate_coordinator_does_not_queue_another_shutdown(
        self,
        acquire_lock: MagicMock,
        run_shutdown: MagicMock,
        release_lock: MagicMock,
    ) -> None:
        self.assertEqual(main(), 0)

        acquire_lock.assert_called_once()
        run_shutdown.assert_not_called()
        release_lock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
