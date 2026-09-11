"""Tests for the disposable Flickr replacement probe's local logic."""

from __future__ import annotations

import struct
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from scripts.flickr_replacement_probe import (
    PNG_HEIGHT,
    PNG_WIDTH,
    ImageSpec,
    Observation,
    generate_png,
    hash_file,
    preservation_checks,
)


class SyntheticPngTests(unittest.TestCase):
    def test_generated_images_are_distinct_8_bit_rgb_pngs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.png"
            replacement = root / "replacement.png"
            generate_png(baseline, ImageSpec("a", (1, 2, 3), (4, 5, 6), (7, 8, 9)))
            generate_png(replacement, ImageSpec("b", (9, 8, 7), (6, 5, 4), (3, 2, 1)))

            self.assertNotEqual(hash_file(baseline), hash_file(replacement))
            data = baseline.read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            width, height, bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
            self.assertEqual((width, height), (PNG_WIDTH, PNG_HEIGHT))
            self.assertEqual(bit_depth, 8)
            self.assertEqual(color_type, 2)


class PreservationChecksTests(unittest.TestCase):
    def test_expected_stable_observation_passes(self) -> None:
        before = Observation(
            photo_id="photo",
            owner_nsid="owner",
            photo_page_url="https://example.test/photo",
            title="title",
            description="description",
            is_public=True,
            views=3,
            favorite_count=0,
            comment_count=1,
            comment_ids_sha2_256="comments",
            tag_count=2,
            tag_values_sha2_256="tags",
            album_context_count=1,
            album_context_ids_sha2_256="albums",
            group_context_count=0,
            group_context_ids_sha2_256="groups",
            original_format="png",
            original_width=PNG_WIDTH,
            original_height=PNG_HEIGHT,
            original_bytes=100,
            original_sha2_256="before",
        )
        after = replace(
            before,
            views=4,
            original_bytes=120,
            original_sha2_256="replacement",
        )

        checks = preservation_checks(before, after, "photo", "replacement")

        self.assertTrue(all(checks.values()))

    def test_changed_album_context_is_not_preserved(self) -> None:
        before = Observation(
            photo_id="photo",
            owner_nsid="owner",
            photo_page_url="https://example.test/photo",
            title="title",
            description="description",
            is_public=True,
            views=0,
            favorite_count=0,
            comment_count=0,
            comment_ids_sha2_256="comments",
            tag_count=0,
            tag_values_sha2_256="tags",
            album_context_count=1,
            album_context_ids_sha2_256="before-albums",
            group_context_count=0,
            group_context_ids_sha2_256="groups",
            original_format="png",
            original_width=PNG_WIDTH,
            original_height=PNG_HEIGHT,
            original_bytes=100,
            original_sha2_256="before",
        )
        after = replace(
            before,
            album_context_ids_sha2_256="after-albums",
            original_sha2_256="replacement",
        )

        checks = preservation_checks(before, after, "photo", "replacement")

        self.assertFalse(checks["albumContextSetStable"])


if __name__ == "__main__":
    unittest.main()
