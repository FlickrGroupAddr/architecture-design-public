"""Regression tests for fail-closed localswim lifecycle-test isolation."""

from __future__ import annotations

import os
from pathlib import Path

from scripts import (
    start_localswim_session,
    stop_localswim_session,
    trigger_localswim_shutdown,
)
from tests.lifecycle_test_support import IsolatedLifecycleTestCase


class LifecycleTestIsolationTests(IsolatedLifecycleTestCase):
    """Keep production descriptors, endpoints, logs, and handoffs unreachable."""

    def test_every_mutable_lifecycle_path_is_test_owned(self) -> None:
        paths = [
            start_localswim_session.PROJECT_ROOT,
            start_localswim_session.STATE_STORE_ROOT,
            start_localswim_session.LOCALSWIM_SOURCE_ROOT,
            start_localswim_session.UV_CACHE,
            start_localswim_session.POWERSHELL,
            start_localswim_session.MONITOR_SCRIPT,
            start_localswim_session.HOOK_STATUS,
            start_localswim_session.SESSION_END_STATUS,
            start_localswim_session.SESSION_LIFECYCLE_LOCK,
            stop_localswim_session.HOOK_STATUS,
            stop_localswim_session.SESSION_LIFECYCLE_LOCK,
            trigger_localswim_shutdown.PROJECT_ROOT,
            trigger_localswim_shutdown.COORDINATOR,
            trigger_localswim_shutdown.UV_CACHE,
            trigger_localswim_shutdown.HOOK_STATUS,
            trigger_localswim_shutdown.COORDINATOR_STDOUT,
            trigger_localswim_shutdown.COORDINATOR_STDERR,
        ]
        for config in self.boards:
            paths.extend(
                (
                    config.board,
                    config.service_working_directory,
                    config.service_stdout,
                    config.service_stderr,
                    config.monitor_status,
                    config.monitor_target,
                    config.monitor_lock,
                    config.monitor_stdout,
                    config.monitor_stderr,
                )
            )
        for path in paths:
            self.assert_test_owned(path)

        self.assertEqual(Path(os.environ["TEMP"]), self.subprocess_temp_root)
        self.assertEqual(Path(os.environ["TMP"]), self.subprocess_temp_root)

    def test_hook_status_writes_are_redirected(self) -> None:
        start_localswim_session.write_hook_status("ok")
        stop_localswim_session.write_hook_status("stopping")
        trigger_localswim_shutdown.write_hook_status("launching")

        self.assertTrue(start_localswim_session.HOOK_STATUS.is_file())
        self.assertTrue(stop_localswim_session.HOOK_STATUS.is_file())
        self.assertEqual(
            stop_localswim_session.HOOK_STATUS,
            trigger_localswim_shutdown.HOOK_STATUS,
        )

    def test_unstubbed_shutdown_process_is_refused_before_descriptor_access(self) -> None:
        try:
            stop_localswim_session.stop_service(self.boards[0], "localswim-cli")
        except AssertionError as exc:
            self.assertIn("unstubbed child process", str(exc))
        else:
            self.fail("an unstubbed shutdown process was allowed")

    def test_unstubbed_loopback_request_is_refused(self) -> None:
        try:
            start_localswim_session.get_service_status(8793)
        except AssertionError as exc:
            self.assertIn("unstubbed loopback request", str(exc))
        else:
            self.fail("an unstubbed loopback request was allowed")


if __name__ == "__main__":
    raise SystemExit("run this test through unittest discovery")
