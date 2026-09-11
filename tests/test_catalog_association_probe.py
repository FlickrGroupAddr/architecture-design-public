"""Conformance tests for the ticket #0067 Lightroom catalog-association probe."""

from __future__ import annotations

import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPOSITORY_ROOT / "lightroom" / "FGA Diagnostics.lrdevplugin"
INFO = PLUGIN_ROOT / "Info.lua"
PROBE = PLUGIN_ROOT / "CatalogAssociationProbe.lua"
PROVIDER = PLUGIN_ROOT / "CatalogAssociationPublishServiceProvider.lua"


class CatalogAssociationProbeTests(unittest.TestCase):
    def test_info_exposes_the_probe_provider_and_four_explicit_phases(self) -> None:
        text = INFO.read_text(encoding="utf-8")
        self.assertIn('file = "CatalogAssociationPublishServiceProvider.lua"', text)
        for filename in (
            "RunPrepareCatalogAssociationProbe.lua",
            "RunCreateCatalogAssociationProbe.lua",
            "RunInspectCatalogAssociationProbe.lua",
            "RunRemoveCatalogAssociationProbe.lua",
        ):
            self.assertIn(f'file = "{filename}"', text)

    def test_provider_has_no_network_or_process_boundary(self) -> None:
        text = PROVIDER.read_text(encoding="utf-8")
        for prohibited in (
            'import("LrHttp")',
            'import("LrSocket")',
            'import("LrShell")',
            "LrTasks.execute",
            "FlickrAPI.",
            ":uploadPhoto(",
            ":postMultipart(",
        ):
            self.assertNotIn(prohibited, text)

    def test_provider_blocks_render_and_acknowledges_only_local_removal(self) -> None:
        text = PROVIDER.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        self.assertIn("rendition:skipRender()", text)
        self.assertIn("rendition:uploadFailed(", text)
        self.assertNotIn("rendition:waitForRender()", text)
        self.assertNotIn("recordPublishedPhotoId", text)
        self.assertIn('return "ignore"', text)
        self.assertIn("deletedCallback(photoId)", text)
        self.assertIn("deletePhotosFromPublishedCollection", normalized)

    def test_probe_uses_the_documented_provider_scoped_association(self) -> None:
        text = PROBE.read_text(encoding="utf-8")

        self.assertIn('ADOBE_FLICKR_PLUGIN_ID = "com.adobe.lightroom.export.flickr"', text)
        self.assertIn('FIXTURE_FILENAME = "catalog-association-0067.png"', text)
        self.assertIn("LrDigest.SHA256.digest(payload)", text)
        self.assertIn("EXPECTED_FIXTURE_SHA2_256", text)
        self.assertIn("associationCollection:addPhotoByRemoteId(", text)
        self.assertIn("if before ~= after then", text)
        self.assertIn("association.collection:removePhotos({ photo })", text)

    def test_probe_writes_sanitized_json_to_the_known_handoff_path(self) -> None:
        text = PROBE.read_text(encoding="utf-8")

        self.assertIn('REPORT_PATH = "C:\\\\Temp\\\\FGA-catalog-association-0067.json"', text)
        self.assertIn('probe = "catalog-only-existing-photo-association"', text)
        self.assertIn("sourceRecords = recordsData(sources)", text)
        self.assertIn("associationRecords = recordsData(associations)", text)
        self.assertIn("callbackAudit = auditData()", text)
        self.assertIn("publishServices = publishServiceInventory(catalog)", text)
        self.assertIn("fixtureSha2_256 = photoFixtureDigest(photo)", text)
        for secret_marker in (
            "auth_token",
            "authorizationHeader",
            "oauth_token",
            "oauth_token_secret",
        ):
            self.assertNotIn(secret_marker, text)

    def test_probe_uses_lightroom_yield_safe_protected_calls(self) -> None:
        probe = PROBE.read_text(encoding="utf-8")
        provider = PROVIDER.read_text(encoding="utf-8")

        self.assertIn("LrTasks.pcall(action)", probe)
        self.assertIn("LrTasks.pcall(\n            CatalogAssociationProbe.writeReport", probe)
        self.assertIn("LrTasks.pcall(CatalogAssociationProbe.writeReport, phase)", provider)
        self.assertNotIn("= pcall(", probe)
        self.assertNotIn("= pcall(", provider)

    def test_success_report_precedes_the_completion_dialog(self) -> None:
        text = PROBE.read_text(encoding="utf-8")
        helper = text[
            text.index("local function reportThenShow") : text.index(
                "function CatalogAssociationProbe.run"
            )
        ]

        self.assertLess(
            helper.index("CatalogAssociationProbe.writeReport(phase)"),
            helper.index("LrDialogs.message(title, message"),
        )
        self.assertIn("local succeeded, result, reportWritten = LrTasks.pcall(action)", text)


if __name__ == "__main__":
    unittest.main()
