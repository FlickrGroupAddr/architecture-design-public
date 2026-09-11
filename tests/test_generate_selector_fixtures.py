"""Tests for deterministic existing-photo selector fixtures."""

from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from scripts.generate_selector_fixtures import (
    FIXTURES,
    HEIGHT,
    WIDTH,
    check_fixtures,
    fixture_bytes,
    write_fixtures,
)


class SelectorFixtureTests(unittest.TestCase):
    def test_generated_fixtures_are_distinct_8_bit_rgb_pngs(self) -> None:
        payloads = [fixture_bytes(spec) for spec in FIXTURES]

        self.assertEqual(len(payloads), len(set(payloads)))
        for data in payloads:
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            width, height, bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
            self.assertEqual((width, height), (WIDTH, HEIGHT))
            self.assertEqual(bit_depth, 8)
            self.assertEqual(color_type, 2)

    def test_written_fixture_set_matches_generator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_directory = Path(directory)
            write_fixtures(output_directory)

            self.assertEqual(check_fixtures(output_directory), [])

            first = output_directory / FIXTURES[0].filename
            first.write_bytes(b"stale")
            self.assertEqual(check_fixtures(output_directory), [FIXTURES[0].filename])


if __name__ == "__main__":
    unittest.main()
