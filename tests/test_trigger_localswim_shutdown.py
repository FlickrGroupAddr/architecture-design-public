"""Tests for the bounded SessionEnd shutdown trigger."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts import trigger_localswim_shutdown
from tests.lifecycle_test_support import IsolatedLifecycleTestCase


class CoordinatorLaunchTests(IsolatedLifecycleTestCase):
    """Keep the SessionEnd hook fast and independent of coordinator completion."""

    @patch("scripts.trigger_localswim_shutdown.subprocess.Popen")
    def test_launch_uses_detached_hidden_uv_process(self, popen: MagicMock) -> None:
        popen.return_value.pid = 4321
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            uv = root / "uv.exe"
            coordinator = root / "stop.py"
            uv.touch()
            coordinator.touch()
            with (
                patch.object(trigger_localswim_shutdown.os, "name", "nt"),
                patch.object(trigger_localswim_shutdown, "PROJECT_ROOT", root),
                patch.object(trigger_localswim_shutdown, "COORDINATOR", coordinator),
                patch.object(
                    trigger_localswim_shutdown,
                    "COORDINATOR_STDOUT",
                    root / "coordinator.out.log",
                ),
                patch.object(
                    trigger_localswim_shutdown,
                    "COORDINATOR_STDERR",
                    root / "coordinator.err.log",
                ),
            ):
                pid = trigger_localswim_shutdown.launch_coordinator(
                    environment={},
                    uv_command=str(uv),
                )

        self.assertEqual(pid, 4321)
        launch = popen.call_args
        self.assertEqual(
            launch.args[0],
            (
                str(uv.resolve()),
                "run",
                "--project",
                str(root),
                "--frozen",
                "python",
                str(coordinator),
            ),
        )
        self.assertEqual(launch.kwargs["cwd"], root)
        self.assertIs(launch.kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual(
            launch.kwargs["creationflags"],
            trigger_localswim_shutdown.DETACHED_PROCESS
            | trigger_localswim_shutdown.CREATE_NEW_PROCESS_GROUP
            | trigger_localswim_shutdown.CREATE_NO_WINDOW,
        )
        self.assertTrue(launch.kwargs["close_fds"])
        self.assertEqual(launch.kwargs["env"]["PYTHONIOENCODING"], "utf-8")
        self.assertEqual(
            launch.kwargs["env"]["UV_CACHE_DIR"],
            str(trigger_localswim_shutdown.UV_CACHE),
        )

    @patch("scripts.trigger_localswim_shutdown.write_hook_status")
    @patch("scripts.trigger_localswim_shutdown.launch_coordinator", return_value=4321)
    def test_main_records_launch_before_starting_coordinator(
        self,
        launch_coordinator: MagicMock,
        write_hook_status: MagicMock,
    ) -> None:
        self.assertEqual(trigger_localswim_shutdown.main(), 0)

        write_hook_status.assert_called_once_with("launching")
        launch_coordinator.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
