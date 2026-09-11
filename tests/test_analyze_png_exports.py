"""Tests for the Lightroom PNG matrix artifact analyzer."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from typing import cast

from scripts.analyze_png_exports import analyze_run_directory


class AnalyzePngExportsTests(unittest.TestCase):
    def test_analyze_without_exiftool_records_hash_and_size(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_directory = Path(temporary_directory)
            (run_directory / "manifest.json").write_text("{}\n", encoding="utf-8")
            image_directory = run_directory / "png-8-srgb"
            image_directory.mkdir()
            image_bytes = b"synthetic-test-image"
            (image_directory / "fixture.png").write_bytes(image_bytes)

            analysis = analyze_run_directory(run_directory, exiftool=None)

        self.assertEqual(analysis["imageCount"], 1)
        images = cast("list[dict[str, object]]", analysis["images"])
        self.assertEqual(images[0]["fileSizeBytes"], len(image_bytes))
        self.assertEqual(
            images[0]["SHA2-256"],
            hashlib.sha256(image_bytes).hexdigest(),
        )
        self.assertIsNone(images[0]["metadata"])


if __name__ == "__main__":
    unittest.main()
