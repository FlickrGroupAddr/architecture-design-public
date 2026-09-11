"""Regression tests for documentation drift reconciled by ticket #0029."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class DocumentationDriftTests(unittest.TestCase):
    def test_architecture_overview_date_is_reconciled(self) -> None:
        text = (REPOSITORY_ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
        self.assertIn("Last updated: 2026-09-11", "\n".join(text.splitlines()[:8]))

    def test_sandbox_git_example_suppresses_both_known_boundary_warnings(self) -> None:
        text = (REPOSITORY_ROOT / "docs" / "operations" / "development-environment.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("-c safe.directory=C:/Projects/FGA/architecture-design", text)
        self.assertIn("-c core.excludesFile=.git/info/exclude", text)

    def test_diagnostic_python_command_is_frozen(self) -> None:
        text = (
            REPOSITORY_ROOT / "lightroom" / "FGA Diagnostics.lrdevplugin" / "README.md"
        ).read_text(encoding="utf-8")
        self.assertNotIn("uv run python", text)
        self.assertIn("uv run --frozen python scripts/analyze_png_exports.py", text)

    def test_signing_research_defers_to_the_current_decision_and_contract(self) -> None:
        text = (REPOSITORY_ROOT / "docs" / "research" / "upload-signing-boundary.md").read_text(
            encoding="utf-8"
        )
        header = "\n".join(text.splitlines()[:16])
        self.assertIn("Status: Completed validation evidence", header)
        self.assertIn("Authority: Research evidence", header)
        self.assertNotIn("| Pairing code |", text)
        self.assertIn("historical alternatives, not preauthorized fallbacks", text)

    def test_question_register_separates_open_deferred_and_resolved_items(self) -> None:
        text = (REPOSITORY_ROOT / "docs" / "open-questions.md").read_text(encoding="utf-8")
        sections = re.split(r"^## ", text, flags=re.MULTILINE)
        by_heading = {section.splitlines()[0]: section for section in sections[1:]}
        self.assertEqual(
            set(re.findall(r"^### Q(\d{3})", by_heading["Open questions"], re.MULTILINE)),
            {"001", "003", "007", "018", "019"},
        )
        self.assertEqual(
            set(
                re.findall(
                    r"^### Q(\d{3})",
                    by_heading["Deferred scope-change questions"],
                    re.MULTILINE,
                )
            ),
            {"013", "014"},
        )
        self.assertEqual(
            set(re.findall(r"^### Q(\d{3})", by_heading["Resolved questions"], re.MULTILINE)),
            {
                "002",
                "004",
                "005",
                "006",
                "008",
                "009",
                "010",
                "011",
                "012",
                "015",
                "016",
                "017",
            },
        )
        for ticket in ("#0068", "#0069", "#0070", "#0071", "#0072"):
            self.assertIn(ticket, by_heading["Open questions"])

    def test_plugin_code_transfer_requires_canonical_clear_text_comparison(self) -> None:
        active_design_files = (
            "administrative-control-plane-contract.md",
            "architecture.md",
            "future-terry-faq.md",
            "plugin-service-contract.md",
            "private-install-credential-transfer.md",
            "zero-state-publish-flow.md",
            "decisions/0006-browser-free-private-installation.md",
            "decisions/0018-same-workstation-private-credential-transfer.md",
        )
        obsolete_phrases = (
            "password-style",
            "password field",
            "password control",
            "transient password",
            "renders a masked",
            "masking or visual style is an implementation choice",
        )

        for relative_path in active_design_files:
            text = (REPOSITORY_ROOT / "docs" / relative_path).read_text(encoding="utf-8")
            for phrase in obsolete_phrases:
                self.assertNotIn(phrase, text, relative_path)
            self.assertIn("clear-text", text, relative_path)
            self.assertIn("Crockford Base32", text, relative_path)

        transfer_contract = (
            REPOSITORY_ROOT / "docs" / "private-install-credential-transfer.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "^[0-9A-HJKMNP-TV-Z]{4}(?:-[0-9A-HJKMNP-TV-Z]{4}){11}-[0-9A-HJKMNP-TV-Z]{3}[0G]$",
            transfer_contract,
        )
        self.assertIn("exactly 32 random octets", transfer_contract)
        self.assertIn("simultaneously visible", transfer_contract)

    def test_zero_state_preserves_authoritative_plugin_code_list_before_create(self) -> None:
        text = (REPOSITORY_ROOT / "docs" / "zero-state-publish-flow.md").read_text(encoding="utf-8")
        list_position = text.index("GET /api/v001/plugin-codes")
        audit_position = text.index("list-read audit", list_position)
        create_position = text.index("POST /api/v001/plugin-codes", audit_position)
        self.assertLess(list_position, audit_position)
        self.assertLess(audit_position, create_position)
        self.assertIn("without exposing its value to JavaScript", text)


if __name__ == "__main__":
    unittest.main()
