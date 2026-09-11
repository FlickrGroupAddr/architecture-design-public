"""Tests for the architecture-document authority index."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from defusedxml import ElementTree

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DECISION_DIRECTORY = REPOSITORY_ROOT / "docs" / "decisions"
INDEX_ROW = re.compile(
    r"^\| \[(?P<number>\d{4})\]\((?P<file>\d{4}-[^)]+\.md)\) "
    r"\| (?P<status>Accepted|Proposed|Superseded|Rejected) \|",
    re.MULTILINE,
)
ADR_STATUS = re.compile(
    r"^Status: (?P<status>Accepted|Proposed|Superseded|Rejected)\b",
    re.MULTILINE,
)


class DocumentationAuthorityTests(unittest.TestCase):
    def test_adr_index_matches_every_header(self) -> None:
        index_text = (DECISION_DIRECTORY / "README.md").read_text(encoding="utf-8")
        indexed = {
            match.group("file"): (match.group("number"), match.group("status"))
            for match in INDEX_ROW.finditer(index_text)
        }
        adr_files = {path.name for path in DECISION_DIRECTORY.glob("[0-9][0-9][0-9][0-9]-*.md")}

        self.assertEqual(set(indexed), adr_files)
        for filename, (number, indexed_status) in indexed.items():
            self.assertEqual(number, filename[:4])
            text = (DECISION_DIRECTORY / filename).read_text(encoding="utf-8")
            header = ADR_STATUS.search(text)
            self.assertIsNotNone(header, filename)
            assert header is not None
            self.assertEqual(indexed_status, header.group("status"), filename)

    def test_repository_links_the_authority_entry_point(self) -> None:
        root_readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(
            "[Architecture documentation authority](docs/README.md)",
            root_readme,
        )

    def test_ambiguous_derived_documents_declare_their_role(self) -> None:
        required_markers = {
            "architecture.md": "Authority: Derived overview",
            "future-terry-faq.md": "Authority: Derived explanation",
            "open-questions.md": "Authority: Non-normative decision inventory",
            "plugin-service-contract.md": "Authority: Accepted normative contract",
            "vision-and-scope.md": "Authority: Derived scope synthesis",
            "zero-state-publish-flow.md": "Authority: Mixed-status normative contract",
        }

        for filename, marker in required_markers.items():
            text = (REPOSITORY_ROOT / "docs" / filename).read_text(encoding="utf-8")
            self.assertIn(marker, "\n".join(text.splitlines()[:12]), filename)

        for filename in (
            "photo-group-add-state-machine.puml",
            "zero-state-publish-flow.puml",
        ):
            text = (REPOSITORY_ROOT / "docs" / "diagrams" / filename).read_text(encoding="utf-8")
            self.assertIn("Authority: Derived visual", "\n".join(text.splitlines()[:12]))

    def test_system_architecture_drawio_is_reviewable_and_complete(self) -> None:
        path = REPOSITORY_ROOT / "docs" / "diagrams" / "system-architecture.drawio"
        tree = ElementTree.parse(path)
        root = tree.getroot()
        self.assertIsNotNone(root)
        assert root is not None

        self.assertEqual(root.tag, "mxfile")
        self.assertEqual(root.attrib.get("compressed"), "false")
        diagrams = root.findall("diagram")
        self.assertEqual(
            [diagram.attrib.get("name") for diagram in diagrams],
            ["System architecture", "Fail-polite group add"],
        )

        labels = {
            cell.attrib.get("value", "")
            for diagram in diagrams
            for cell in diagram.findall("./mxGraphModel/root/mxCell")
        }
        required_fragments = (
            "Authority: Derived visual",
            "FGA LrC plug-in",
            "FGA API backend",
            "FGA group-submission worker",
            "FGA database",
            "FGA managed secret store",
            "service-signed direct upload",
            "flickr.photos.getAllContexts",
            "flickr.groups.getInfo",
            "flickr.groups.pools.add",
            "dispatch_started",
            "permanent exact-pair block",
            "FGA components expose no force-resubmit path",
        )
        combined_labels = "\n".join(labels)
        for fragment in required_fragments:
            self.assertIn(fragment, combined_labels)

        for diagram in diagrams:
            model = diagram.find("mxGraphModel")
            self.assertIsNotNone(model, diagram.attrib.get("name"))
            assert model is not None
            self.assertEqual(model.attrib.get("pageWidth"), "1600")
            self.assertEqual(model.attrib.get("pageHeight"), "1000")

        for diagram in diagrams:
            cells = diagram.findall("./mxGraphModel/root/mxCell")
            cell_ids = {cell.attrib["id"] for cell in cells}
            self.assertEqual(len(cell_ids), len(cells), diagram.attrib.get("name"))
            for cell in cells:
                if cell.attrib.get("edge") != "1":
                    continue
                self.assertIn(cell.attrib["source"], cell_ids, cell.attrib["id"])
                self.assertIn(cell.attrib["target"], cell_ids, cell.attrib["id"])

    def test_clean_room_authentication_tabs_are_scoped_interaction_authority(self) -> None:
        authority_text = (REPOSITORY_ROOT / "docs" / "README.md").read_text(encoding="utf-8")
        diagram_notes = (REPOSITORY_ROOT / "docs" / "diagrams" / "README.md").read_text(
            encoding="utf-8"
        )
        decision = (
            DECISION_DIRECTORY
            / "0041-use-clean-room-authentication-tabs-as-interaction-authority.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Status: Accepted", decision.partition("## Context")[0])
        self.assertIn("interaction map", authority_text)
        self.assertIn("all three tabs", authority_text)
        self.assertIn("Authority: Mixed", "\n".join(diagram_notes.splitlines()[:10]))
        self.assertIn("ADR 0041", diagram_notes)
        self.assertIn("all three tabs", diagram_notes)
        self.assertIn("necessary but not sufficient", decision.casefold())

        path = REPOSITORY_ROOT / "docs" / "diagrams" / "clean-room-authentication-legal.drawio"
        root = ElementTree.parse(path).getroot()
        assert root is not None
        diagrams = root.findall("diagram")
        self.assertEqual(
            [diagram.attrib.get("name") for diagram in diagrams],
            [
                "1 · Browser Session",
                "2 · Plugin Code Generation",
                "3 · Publish PNG + Groups",
            ],
        )
        for diagram in diagrams:
            values = "\n".join(cell.attrib.get("value", "") for cell in diagram.iter("mxCell"))
            self.assertIn("Authority: Normative happy-path interaction map", values)
            self.assertNotIn("Authority: Derived conceptual visual", values)
            self.assertNotIn("Draft:", values)


if __name__ == "__main__":
    unittest.main()
