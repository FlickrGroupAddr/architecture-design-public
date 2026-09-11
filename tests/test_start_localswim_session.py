"""Tests for the localswim SessionStart launcher."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.start_localswim_session import (
    DesktopRect,
    WindowPlacement,
    chrome_board_arguments,
    compensate_window_frame,
    interpret_service_status,
    launch_hidden,
    resolve_thread_id,
    session_start_source,
    should_open_board_browsers,
    split_work_area,
    wait_for_lifecycle_lock,
)
from tests.lifecycle_test_support import IsolatedLifecycleTestCase

THREAD_ID = "28a44ccc-02a3-4fe7-84a8-8ef6c416d4ce"
SECOND_THREAD_ID = "5692ff46-a53c-4418-9536-b3d664b80870"


class ResolveThreadIdTests(IsolatedLifecycleTestCase):
    """Validate hook and environment thread selection."""

    def test_explicit_thread_takes_precedence(self) -> None:
        hook_input = json.dumps({"session_id": SECOND_THREAD_ID})
        actual = resolve_thread_id(THREAD_ID, hook_input, {"CODEX_THREAD_ID": SECOND_THREAD_ID})
        self.assertEqual(actual, THREAD_ID)

    def test_hook_session_id_precedes_inherited_environment(self) -> None:
        hook_input = json.dumps({"session_id": SECOND_THREAD_ID})
        actual = resolve_thread_id(None, hook_input, {"CODEX_THREAD_ID": THREAD_ID})
        self.assertEqual(actual, SECOND_THREAD_ID)

    def test_hook_session_id_is_used_without_environment(self) -> None:
        hook_input = json.dumps({"session_id": THREAD_ID})
        self.assertEqual(resolve_thread_id(None, hook_input, {}), THREAD_ID)

    def test_environment_thread_is_the_manual_fallback(self) -> None:
        self.assertEqual(resolve_thread_id(None, "", {"CODEX_THREAD_ID": THREAD_ID}), THREAD_ID)

    def test_missing_uuid_is_rejected(self) -> None:
        try:
            resolve_thread_id(None, json.dumps({"session_id": "thr_invalid"}), {})
        except ValueError as exc:
            self.assertIn("no usable UUID", str(exc))
        else:
            self.fail("invalid thread ID was accepted")


class SessionStartSourceTests(IsolatedLifecycleTestCase):
    """Limit visible browser windows to Codex process launches."""

    def test_startup_source_is_returned(self) -> None:
        self.assertEqual(session_start_source(json.dumps({"source": "startup"})), "startup")

    def test_startup_and_resume_open_board_browsers(self) -> None:
        self.assertTrue(should_open_board_browsers("startup"))
        self.assertTrue(should_open_board_browsers("resume"))

    def test_clear_compact_and_manual_runs_do_not_open_board_browsers(self) -> None:
        self.assertFalse(should_open_board_browsers("clear"))
        self.assertFalse(should_open_board_browsers("compact"))
        self.assertFalse(should_open_board_browsers(None))

    def test_manual_invocation_has_no_source(self) -> None:
        self.assertIsNone(session_start_source(""))

    def test_chrome_arguments_request_a_new_board_window(self) -> None:
        self.assertEqual(
            chrome_board_arguments(8793),
            ("--new-window", "http://127.0.0.1:8793/"),
        )

    def test_monitor_work_area_is_split_left_then_right(self) -> None:
        self.assertEqual(
            split_work_area(DesktopRect(1440, 233, 5280, 2393)),
            (
                WindowPlacement(1440, 233, 1920, 2160),
                WindowPlacement(3360, 233, 1920, 2160),
            ),
        )

    def test_odd_monitor_width_assigns_extra_pixel_to_right_window(self) -> None:
        self.assertEqual(
            split_work_area(DesktopRect(0, 0, 5, 3)),
            (WindowPlacement(0, 0, 2, 3), WindowPlacement(2, 0, 3, 3)),
        )

    def test_invalid_monitor_work_area_is_rejected(self) -> None:
        try:
            split_work_area(DesktopRect(0, 0, 0, 3))
        except ValueError as exc:
            self.assertIn("positive width and height", str(exc))
        else:
            self.fail("invalid monitor work area was accepted")

    def test_invisible_chrome_frame_is_compensated(self) -> None:
        self.assertEqual(
            compensate_window_frame(
                WindowPlacement(1440, 233, 1920, 2160),
                DesktopRect(1440, 233, 3360, 2393),
                DesktopRect(1449, 233, 3351, 2384),
            ),
            WindowPlacement(1431, 233, 1938, 2169),
        )


class ServiceStatusTests(IsolatedLifecycleTestCase):
    """Validate the required localswim status fields."""

    def test_ok_autopush_status_is_healthy(self) -> None:
        status = interpret_service_status({"ok": True, "push": {"state": "ok"}})
        self.assertTrue(status.reachable)
        self.assertTrue(status.healthy)
        self.assertEqual(status.push_state, "ok")

    def test_missing_push_state_is_not_healthy(self) -> None:
        status = interpret_service_status({"ok": True, "push": {}})
        self.assertTrue(status.reachable)
        self.assertFalse(status.healthy)
        self.assertIsNone(status.push_state)


class HiddenLaunchTests(IsolatedLifecycleTestCase):
    """Keep detached children from holding the launcher open through captured pipes."""

    @patch("scripts.start_localswim_session.subprocess.Popen")
    def test_success_waits_for_powershell_without_reading_inherited_pipes(
        self,
        popen: MagicMock,
    ) -> None:
        process = popen.return_value
        process.wait.return_value = 0

        launch_hidden(
            Path("child.exe"),
            ("argument",),
            Path("working"),
            Path("stdout.log"),
            Path("stderr.log"),
        )

        process.wait.assert_called_once_with(timeout=30)
        process.communicate.assert_not_called()
        call = popen.call_args
        self.assertIs(call.kwargs["stdin"], subprocess.DEVNULL)
        self.assertIs(call.kwargs["stdout"], subprocess.PIPE)
        self.assertIs(call.kwargs["stderr"], subprocess.PIPE)


class LifecycleLockTests(IsolatedLifecycleTestCase):
    """Serialize startup behind an in-flight detached shutdown."""

    @patch("scripts.start_localswim_session.time.sleep")
    @patch("scripts.start_localswim_session.acquire_lock")
    @patch("scripts.start_localswim_session.shutdown_is_pending", return_value=False)
    def test_startup_waits_until_lifecycle_lock_is_available(
        self,
        shutdown_is_pending: MagicMock,
        acquire_lock: MagicMock,
        sleep: MagicMock,
    ) -> None:
        expected_lock = MagicMock()
        acquire_lock.side_effect = (None, expected_lock)

        self.assertIs(wait_for_lifecycle_lock(), expected_lock)

        self.assertEqual(acquire_lock.call_count, 2)
        self.assertEqual(shutdown_is_pending.call_count, 3)
        sleep.assert_called_once_with(0.1)

    @patch("scripts.start_localswim_session.time.sleep")
    @patch("scripts.start_localswim_session.release_lock")
    @patch("scripts.start_localswim_session.acquire_lock")
    @patch("scripts.start_localswim_session.shutdown_is_pending")
    def test_startup_rechecks_pending_status_after_acquiring_lock(
        self,
        shutdown_is_pending: MagicMock,
        acquire_lock: MagicMock,
        release_lock: MagicMock,
        sleep: MagicMock,
    ) -> None:
        first_lock = MagicMock()
        expected_lock = MagicMock()
        shutdown_is_pending.side_effect = (False, True, False, False)
        acquire_lock.side_effect = (first_lock, expected_lock)

        self.assertIs(wait_for_lifecycle_lock(), expected_lock)

        release_lock.assert_called_once_with(first_lock)
        sleep.assert_called_once_with(0.1)


if __name__ == "__main__":
    unittest.main()
