"""Tests for the inception-before-FGA priority barrier."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.check_localswim_priority import (
    BLOCKED_EXIT,
    InceptionWork,
    next_actionable,
    run,
)


class PriorityQueryTests(unittest.TestCase):
    @patch("scripts.check_localswim_priority.subprocess.run")
    def test_query_uses_both_actionable_lanes(self, run_process: MagicMock) -> None:
        run_process.return_value = subprocess.CompletedProcess(
            [],
            0,
            json.dumps(
                {
                    "items": [
                        {
                            "ticket": 18,
                            "id": "priority-barrier",
                            "state": "in_progress",
                            "priority": "P2",
                            "subject": "private board prose is ignored",
                        }
                    ]
                }
            ),
            "",
        )

        work = next_actionable("localswim-cli", Path("board.json"))

        self.assertIsNotNone(work)
        assert work is not None
        self.assertEqual(work.ticket, 18)
        self.assertEqual(work.item_id, "priority-barrier")
        self.assertEqual(
            run_process.call_args.args[0],
            [
                "localswim-cli",
                "board.json",
                "card",
                "next",
                "1",
                "--lane",
                "ready_for_work",
                "--lane",
                "in_progress",
                "--json",
            ],
        )

    @patch("scripts.check_localswim_priority.subprocess.run")
    def test_query_returns_none_for_clear_board(self, run_process: MagicMock) -> None:
        run_process.return_value = subprocess.CompletedProcess([], 0, '{"items": []}', "")

        self.assertIsNone(next_actionable("localswim-cli", Path("board.json")))


class PriorityBarrierTests(unittest.TestCase):
    @patch("scripts.check_localswim_priority.next_actionable")
    @patch("scripts.check_localswim_priority.inception_board", return_value=Path("board.json"))
    @patch("scripts.check_localswim_priority.shutil.which", return_value="localswim-cli")
    def test_actionable_card_blocks_fga(
        self,
        which: MagicMock,
        board: MagicMock,
        next_card: MagicMock,
    ) -> None:
        next_card.return_value = InceptionWork(18, "priority-barrier", "in_progress", "P2")

        self.assertEqual(run(), BLOCKED_EXIT)
        which.assert_called_once_with("localswim-cli")
        board.assert_called_once_with()

    @patch("scripts.check_localswim_priority.next_actionable", return_value=None)
    @patch("scripts.check_localswim_priority.inception_board", return_value=Path("board.json"))
    @patch("scripts.check_localswim_priority.shutil.which", return_value="localswim-cli")
    def test_clear_board_allows_fga(
        self,
        which: MagicMock,
        board: MagicMock,
        next_card: MagicMock,
    ) -> None:
        self.assertEqual(run(), 0)
        which.assert_called_once_with("localswim-cli")
        board.assert_called_once_with()
        next_card.assert_called_once_with("localswim-cli", Path("board.json"))


if __name__ == "__main__":
    unittest.main()
