"""Structural checks for the disposable first-publish storyboard."""

from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
STORYBOARD_ROOT = REPOSITORY_ROOT / "prototypes" / "first-publish-storyboard"
FAKE_PLUGIN_CODE = "2345-6789-ABCD-EFGH-JKMN-PQRS-TVWX-YZ23-4567-89AB-CDEF-GHJK-MNP0"
PLUGIN_CODE_PATTERN = re.compile(
    r"^[0-9A-HJKMNP-TV-Z]{4}"
    r"(?:-[0-9A-HJKMNP-TV-Z]{4}){11}"
    r"-[0-9A-HJKMNP-TV-Z]{3}[0G]$"
)


class StoryboardParser(HTMLParser):
    """Collect scene IDs and external resource references from the prototype."""

    def __init__(self) -> None:
        super().__init__()
        self.scene_ids: list[str] = []
        self.resource_references: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = dict(attrs)
        scene_id = attributes.get("data-scene")
        if scene_id is not None:
            self.scene_ids.append(scene_id)
        reference = attributes.get("src") or attributes.get("href")
        if tag in {"link", "script", "img"} and reference is not None:
            self.resource_references.append(reference)


class FirstPublishStoryboardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = (STORYBOARD_ROOT / "index.html").read_text(encoding="utf-8")
        self.readme = (STORYBOARD_ROOT / "README.md").read_text(encoding="utf-8")
        self.styles = (STORYBOARD_ROOT / "styles.css").read_text(encoding="utf-8")
        self.parser = StoryboardParser()
        self.parser.feed(self.html)

    def test_storyboard_has_the_deliberate_end_to_end_scene_order(self) -> None:
        self.assertEqual(
            self.parser.scene_ids,
            [
                "choose",
                "sign-in",
                "authorize",
                "plugin-code",
                "configure",
                "select-groups",
                "publish",
                "upload",
                "accepted",
                "partial",
                "safe-retry",
                "recover",
            ],
        )

    def test_storyboard_has_no_external_runtime_dependency(self) -> None:
        for reference in self.parser.resource_references:
            self.assertNotRegex(reference, r"^(?:https?:)?//", reference)
            self.assertTrue((STORYBOARD_ROOT / reference).is_file(), reference)

    def test_group_recovery_exposes_no_write_retry_control(self) -> None:
        button_text = " ".join(
            " ".join(re.sub(r"<[^>]+>", " ", match).split())
            for match in re.findall(r"<button\b[^>]*>.*?</button>", self.html, re.DOTALL)
        ).casefold()
        for forbidden_action in (
            "retry now",
            "send anyway",
            "force resubmit",
            "clear block",
            "reopen",
        ):
            self.assertNotIn(forbidden_action, button_text)

        self.assertIn("Refresh status", self.html)
        self.assertIn("Inspect Flickr", self.html)
        self.assertIn("will not submit this exact pair again", self.html)

    def test_scene_ten_separates_group_status_and_change_time(self) -> None:
        scene = re.search(
            r'<section class="scene" data-scene="partial".*?</section>',
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(scene)
        scene_html = scene.group(0) if scene is not None else ""

        for heading in (
            "Flickr group",
            "Last status change",
            "Date/time of last status change",
        ):
            self.assertIn(f'<span role="columnheader">{heading}</span>', scene_html)
        self.assertEqual(scene_html.count('class="status-row" role="row"'), 3)
        self.assertEqual(scene_html.count('<time role="cell" datetime="'), 3)
        self.assertEqual(scene_html.count("<strong>Terminal.</strong>"), 2)
        self.assertIn(">2026-09-02 9:13am EDT</time>", scene_html)
        self.assertEqual(scene_html.count(">2026-09-02 9:14am EDT</time>"), 2)
        self.assertIn("after 2026-09-02 9:15am EDT.", scene_html)
        self.assertNotIn("Sep 2, 2026", scene_html)
        self.assertNotIn("9:13 AM", scene_html)
        self.assertIn(
            "grid-template-columns: minmax(120px, 0.7fr) "
            "minmax(220px, 1.4fr) minmax(160px, 0.8fr);",
            self.styles,
        )

    def test_album_and_group_follow_up_do_not_gain_false_ordering(self) -> None:
        self.assertNotIn("Remote photo bound and Album attached", self.html)
        self.assertIn("Album attachment pending", self.html)
        self.assertIn("progresses\n            independently of group-intent handoff", self.html)

    def test_new_photo_selector_does_not_invent_flickr_membership(self) -> None:
        self.assertNotIn("Already in Flickr", self.html)
        self.assertIn("New photo · no Flickr identity exists yet", self.html)

    def test_image_format_is_fixed_to_current_supported_output(self) -> None:
        self.assertRegex(
            self.html,
            r'<select aria-label="Image format" disabled>\s*'
            r"<option>PNG - 8-bit - sRGB</option>\s*</select>",
        )

    def test_plugin_code_is_clear_and_visually_comparable_before_storage(self) -> None:
        self.assertRegex(FAKE_PLUGIN_CODE, PLUGIN_CODE_PATTERN)
        self.assertEqual(self.html.count(FAKE_PLUGIN_CODE), 2)
        self.assertEqual(self.html.count('class="plugin-code-value"'), 2)
        self.assertIn('<textarea\n                  class="plugin-code-value"', self.html)
        self.assertIn('wrap="soft"', self.html)
        self.assertNotIn("FAKE-CODE", self.html)
        self.assertNotIn("••", self.html)
        self.assertIn("Ready to compare and store", self.html)
        self.assertIn("Store and verify", self.html)
        self.assertIn(
            "grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);",
            self.styles,
        )
        self.assertIn("font-variant-numeric: tabular-nums slashed-zero;", self.styles)
        self.assertIn('font-feature-settings: "zero" 1;', self.styles)

    def test_findings_route_the_known_interaction_gap(self) -> None:
        self.assertIn("## Walkthrough findings", self.readme)
        self.assertIn("## Contract-gap disposition", self.readme)
        self.assertIn("ticket #0068", self.readme)
        self.assertIn("no new architecture contract gap", self.readme)
        self.assertIn("User-visible datetimes use `YYYY-MM-DD h:mmam/pm TZ`", self.readme)


if __name__ == "__main__":
    unittest.main()
