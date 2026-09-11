"""Contract checks for the accepted Lightroom group-selection interaction."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import cast

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ADR_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "decisions"
    / "0045-use-a-library-modal-and-photo-metadata-for-group-selection.md"
)


class GroupSelectionInteractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adr = ADR_PATH.read_text(encoding="utf-8")
        self.adr_flat = " ".join(self.adr.split())
        self.architecture = (REPOSITORY_ROOT / "docs" / "architecture.md").read_text(
            encoding="utf-8"
        )
        self.contract = (REPOSITORY_ROOT / "docs" / "plugin-service-contract.md").read_text(
            encoding="utf-8"
        )
        self.flow = (REPOSITORY_ROOT / "docs" / "zero-state-publish-flow.md").read_text(
            encoding="utf-8"
        )
        self.questions = (REPOSITORY_ROOT / "docs" / "open-questions.md").read_text(
            encoding="utf-8"
        )
        self.research = (REPOSITORY_ROOT / "docs" / "research" / "lightroom-classic.md").read_text(
            encoding="utf-8"
        )

    def test_adr_selects_only_documented_sdk_surfaces(self) -> None:
        self.assertIn("Status: Accepted by Terry on 2026-09-04", self.adr)
        for sdk_name in (
            "LrLibraryMenuItems",
            "LrCatalog:getTargetPhotos()",
            "LrCatalog:getActiveSources()",
            "LrPhoto:getContainedPublishedCollections()",
            "LrDialogs.presentModalDialog",
            "LrMetadataProvider",
            "LrPhoto:getPropertyForPlugin()",
            "LrPhoto:setPropertyForPlugin()",
            "LrCatalog:withPrivateWriteAccessDo()",
            "exportContext.publishService",
            "exportContext.publishedCollection",
        ):
            self.assertIn(sdk_name, self.adr)

        self.assertIn(
            "Library > Plug-in Extras > FlickrGroupAddr: Choose Group Additions…",
            self.adr,
        )
        self.assertIn("exactly one photo", self.adr)
        self.assertIn("exactly one `LrPublishedCollection`", self.adr_flat)
        self.assertIn("opens no selector and no serial dialogs", self.adr_flat)
        self.assertNotIn("LrUUID", self.adr)

    def test_private_photo_record_is_versioned_scoped_and_bounded(self) -> None:
        example_match = re.search(r"```json\n(.*?)\n```", self.adr, re.DOTALL)
        self.assertIsNotNone(example_match)
        example_text = example_match.group(1) if example_match is not None else "{}"
        example = cast("dict[str, object]", json.loads(example_text))
        self.assertEqual(example["schemaVersion"], 1)

        entries = cast("list[dict[str, object]]", example["entries"])
        self.assertEqual(len(entries), 1)
        self.assertEqual(
            set(entries[0]),
            {
                "publishServiceLocalId",
                "publishedCollectionLocalId",
                "photoUuid",
                "selectionRevision",
                "choice",
                "flickrGroupIds",
            },
        )
        self.assertIn("private, untitled string field", self.adr)
        self.assertIn("one through 60 unique exact group IDs", self.adr)
        self.assertRegex(
            self.adr,
            r"current revision still\s+equals the snapshotted revision",
        )
        self.assertIn("no network request and opens no dialog", self.adr_flat)
        self.assertIn("fails closed", self.adr_flat)

    def test_ui_preserves_zero_group_and_moderator_safety_boundaries(self) -> None:
        for phrase in (
            "No group additions",
            "Not yet published by this FGA collection",
            "Currently in Flickr groups",
            "permanent submission block never has a checkbox",
            "deselection never means removal, cancellation, retry, or resubmission",
            "sends no empty batch",
        ):
            self.assertIn(phrase, self.adr_flat)

    def test_derived_documents_route_to_the_accepted_decision(self) -> None:
        for document in (
            self.architecture,
            self.contract,
            self.flow,
            self.questions,
        ):
            self.assertIn("ADR 0045", document)

        self.assertIn("Terry accepted this implementation mapping", self.flow)
        self.assertIn("Resolved on 2026-09-04", self.questions)
        self.assertIn("## Accepted local group-selection interaction", self.contract)
        self.assertNotIn(
            "The FGA LrC plug-in UI and local storage mechanism used for per-photo group\n"
            "  selection.",
            self.contract,
        )

    def test_research_records_local_sdk_provenance(self) -> None:
        self.assertIn("group-selection API review: 2026-09-04", self.research)
        for reference in (
            "Sample Plugins/custommetadatasample.lrdevplugin/CustomMetadataDefinition.lua",
            "API Reference/modules/LrCatalog.html",
            "API Reference/modules/LrDialogs.html",
            "API Reference/modules/LrExportContext.html",
        ):
            self.assertIn(reference, self.research)


if __name__ == "__main__":
    unittest.main()
