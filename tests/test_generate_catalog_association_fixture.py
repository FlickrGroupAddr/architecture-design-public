"""Tests for the deterministic ticket #0067 synthetic PNG fixture."""

from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from scripts.generate_catalog_association_fixture import (
    expected_bytes,
    fixture_matches,
    sha2_256,
    write_fixture,
)
from scripts.generate_selector_fixtures import HEIGHT, WIDTH


class CatalogAssociationFixtureTests(unittest.TestCase):
    def test_fixture_is_deterministic_8_bit_rgb_png(self) -> None:
        data = expected_bytes()

        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        width, height, bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
        self.assertEqual((width, height), (WIDTH, HEIGHT))
        self.assertEqual(bit_depth, 8)
        self.assertEqual(color_type, 2)
        self.assertEqual(
            sha2_256(data),
            "a64d5bfa01b27dcb6772b388baaef4e9e6289886bd40f2a8e26c573f65014968",
        )

    def test_written_fixture_matches_generator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "catalog-association-0067.png"
            write_fixture(output_path)

            self.assertTrue(fixture_matches(output_path))

            output_path.write_bytes(b"stale")
            self.assertFalse(fixture_matches(output_path))


if __name__ == "__main__":
    unittest.main()
