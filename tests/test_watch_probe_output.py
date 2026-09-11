"""Tests for the one-shot Lightroom Classic probe-output monitor."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.watch_probe_output import (
    DEFAULT_TIMEOUT_SECONDS,
    Config,
    alert_message,
    file_signature,
)


class ProbeOutputMonitorTests(unittest.TestCase):
    def test_default_lifetime_covers_a_full_day_of_human_interaction(self) -> None:
        self.assertEqual(DEFAULT_TIMEOUT_SECONDS, 24 * 60 * 60)

    def test_file_signature_distinguishes_absent_and_written_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "probe.json"
            self.assertIsNone(file_signature(output))

            output.write_text('{"schema":1}', encoding="utf-8")

            signature = file_signature(output)
            self.assertIsNotNone(signature)
            assert signature is not None
            self.assertEqual(signature[1], 12)

    def test_alert_names_path_without_copying_report_content(self) -> None:
        config = Config(
            output=Path(r"C:\Temp\FGA-probe.json"),
            output_label="FGA Lightroom probe",
            thread_id="11111111-1111-1111-1111-111111111111",
            status_path=Path(r"C:\Temp\FGA-probe-monitor-status.json"),
            target_path=Path(r"C:\Temp\FGA-probe-monitor-target.json"),
            lock_path=Path(r"C:\Temp\FGA-probe-monitor.lock"),
            quiet_seconds=0.75,
            timeout_seconds=3600,
        )

        message = alert_message(config, "2026-08-27T12:00:00-04:00")

        self.assertIn(str(config.output), message)
        self.assertIn("monitor did not read", message)
        self.assertNotIn("sourceRecords", message)


if __name__ == "__main__":
    unittest.main()
