"""Fail-closed isolation for localswim lifecycle tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import (
    start_localswim_session,
    stop_localswim_session,
    trigger_localswim_shutdown,
)
from scripts.start_localswim_session import BoardConfig


def _board_config(
    *,
    name: str,
    board: Path,
    working_directory: Path,
    runtime_root: Path,
) -> BoardConfig:
    """Build one board whose mutable boundaries are test-owned."""

    stem = name.replace(" ", "-").lower()
    return BoardConfig(
        name,
        board,
        f"{name} test board",
        working_directory,
        runtime_root / f"{stem}-service.out.log",
        runtime_root / f"{stem}-service.err.log",
        runtime_root / f"{stem}-monitor-status.json",
        runtime_root / f"{stem}-monitor-target.json",
        runtime_root / f"{stem}-monitor.lock",
        runtime_root / f"{stem}-monitor.out.log",
        runtime_root / f"{stem}-monitor.err.log",
    )


class IsolatedLifecycleTestCase(unittest.TestCase):
    """Redirect lifecycle state and reject unstubbed external operations."""

    def setUp(self) -> None:
        """Create and install one unique lifecycle boundary for each test."""

        super().setUp()
        temporary_directory = tempfile.TemporaryDirectory(prefix="fga-lifecycle-test-")
        self.addCleanup(temporary_directory.cleanup)
        self.test_root = Path(temporary_directory.name)
        self.project_root = self.test_root / "project"
        self.state_store_root = self.test_root / "state-store"
        self.localswim_source_root = self.test_root / "localswim-source"
        self.runtime_root = self.test_root / "runtime"
        self.subprocess_temp_root = self.test_root / "subprocess-temp"
        for path in (
            self.project_root,
            self.state_store_root,
            self.localswim_source_root,
            self.runtime_root,
            self.subprocess_temp_root,
        ):
            path.mkdir(parents=True)
        (self.test_root / "pwsh.exe").touch()

        fga_board = self.state_store_root / "flickgroupaddr" / "fga-localswim.json"
        inception_board = self.state_store_root / "localswim" / "localswim.json"
        for board, port in ((fga_board, 48793), (inception_board, 48794)):
            board.parent.mkdir(parents=True)
            board.write_text(f'{{"port":{port}}}', encoding="utf-8")

        self.boards = (
            _board_config(
                name="FGA",
                board=fga_board,
                working_directory=self.project_root,
                runtime_root=self.runtime_root,
            ),
            _board_config(
                name="localswim inception",
                board=inception_board,
                working_directory=self.localswim_source_root,
                runtime_root=self.runtime_root,
            ),
        )
        hook_status = self.runtime_root / "session-start-status.json"
        session_end_status = self.runtime_root / "session-end-status.json"
        lifecycle_lock = self.runtime_root / "session-lifecycle.lock"
        uv_cache = self.runtime_root / "uv-cache"

        replacements = (
            patch.object(start_localswim_session, "PROJECT_ROOT", self.project_root),
            patch.object(
                start_localswim_session,
                "STATE_STORE_ROOT",
                self.state_store_root,
            ),
            patch.object(
                start_localswim_session,
                "LOCALSWIM_SOURCE_ROOT",
                self.localswim_source_root,
            ),
            patch.object(start_localswim_session, "UV_CACHE", uv_cache),
            patch.object(
                start_localswim_session,
                "POWERSHELL",
                self.test_root / "pwsh.exe",
            ),
            patch.object(
                start_localswim_session,
                "MONITOR_SCRIPT",
                self.project_root / "scripts" / "watch_localswim.py",
            ),
            patch.object(start_localswim_session, "HOOK_STATUS", hook_status),
            patch.object(
                start_localswim_session,
                "SESSION_END_STATUS",
                session_end_status,
            ),
            patch.object(
                start_localswim_session,
                "SESSION_LIFECYCLE_LOCK",
                lifecycle_lock,
            ),
            patch.object(start_localswim_session, "BOARDS", self.boards),
            patch.object(stop_localswim_session, "BOARDS", self.boards),
            patch.object(stop_localswim_session, "HOOK_STATUS", session_end_status),
            patch.object(
                stop_localswim_session,
                "SESSION_LIFECYCLE_LOCK",
                lifecycle_lock,
            ),
            patch.object(trigger_localswim_shutdown, "PROJECT_ROOT", self.project_root),
            patch.object(
                trigger_localswim_shutdown,
                "COORDINATOR",
                self.project_root / "scripts" / "stop_localswim_session.py",
            ),
            patch.object(trigger_localswim_shutdown, "UV_CACHE", uv_cache),
            patch.object(trigger_localswim_shutdown, "HOOK_STATUS", session_end_status),
            patch.object(
                trigger_localswim_shutdown,
                "COORDINATOR_STDOUT",
                self.runtime_root / "coordinator.out.log",
            ),
            patch.object(
                trigger_localswim_shutdown,
                "COORDINATOR_STDERR",
                self.runtime_root / "coordinator.err.log",
            ),
            patch.dict(
                os.environ,
                {
                    "TEMP": str(self.subprocess_temp_root),
                    "TMP": str(self.subprocess_temp_root),
                },
            ),
            patch(
                "subprocess.Popen",
                side_effect=AssertionError("lifecycle test attempted an unstubbed child process"),
            ),
            patch(
                "subprocess.run",
                side_effect=AssertionError("lifecycle test attempted an unstubbed child process"),
            ),
            patch(
                "urllib.request.urlopen",
                side_effect=AssertionError(
                    "lifecycle test attempted an unstubbed loopback request"
                ),
            ),
        )
        for replacement in replacements:
            replacement.start()
            self.addCleanup(replacement.stop)

    def assert_test_owned(self, path: Path) -> None:
        """Assert that one path stays beneath this test's temporary root."""

        self.assertTrue(
            path.resolve().is_relative_to(self.test_root.resolve()),
            f"lifecycle test path escaped its temporary root: {path}",
        )
