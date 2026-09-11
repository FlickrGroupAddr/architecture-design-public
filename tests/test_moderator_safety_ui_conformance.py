"""Tests for the proposed moderator-safety UI conformance contract."""

from __future__ import annotations

import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONTRACT = REPOSITORY_ROOT / "docs" / "moderator-safety-ui-conformance.md"


class ModeratorSafetyUiConformanceTests(unittest.TestCase):
    def test_selector_uses_complete_server_projections_and_fails_closed(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        for marker in (
            "complete current writable-group snapshot",
            "one new complete binding-scoped Flickr membership observation",
            "complete retained `history` view",
            "joins each status intent to the authoritative exact-pair block row",
            "There is no default-to-eligible branch",
            "enables no group-add confirmation",
        ):
            self.assertIn(marker, normalized)

    def test_total_rule_is_block_first_and_has_no_resubmit_action(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        moderation = normalized.index("`moderation_submission_protected`")
        uncertain = normalized.index("`delivery_uncertain_protected`")
        membership = normalized.index("`current_membership_observed`")
        eligible = normalized.index("`eligible_group_addition`")
        self.assertLess(moderation, membership)
        self.assertLess(uncertain, membership)
        self.assertLess(membership, eligible)
        self.assertIn(
            "the only pair-specific actions are `view_status` and `inspect_flickr`",
            normalized,
        )
        self.assertIn("`send_anyway`", normalized)
        self.assertIn("`force_resubmit`", normalized)

    def test_reviewed_copy_does_not_infer_moderator_decision(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        self.assertIn(
            "The final moderator decision is unknown. FGA components will not "
            "submit this exact pair again.",
            normalized,
        )
        self.assertIn(
            "FGA records cannot prove whether Flickr received the add request.",
            normalized,
        )
        self.assertIn("the UI does not say **pending**", normalized)
        self.assertIn("Absence never becomes rejection copy", normalized)

    def test_batch_and_status_contracts_project_the_same_block(self) -> None:
        expected_link = "moderator-safety-ui-conformance.md"
        for relative_path in (
            "docs/architecture.md",
            "docs/future-terry-faq.md",
            "docs/plugin-service-contract.md",
            "docs/queue-status-api.md",
        ):
            text = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn(expected_link, text, relative_path)

        plugin_contract = (REPOSITORY_ROOT / "docs" / "plugin-service-contract.md").read_text(
            encoding="utf-8"
        )
        status_contract = (REPOSITORY_ROOT / "docs" / "queue-status-api.md").read_text(
            encoding="utf-8"
        )
        self.assertIn('"permanentSubmissionBlock": null', plugin_contract)
        self.assertIn("insert-only server relation", plugin_contract)
        self.assertIn("joins the insert-only `submission_blocks` row", status_contract)

    def test_conformance_inventory_covers_ui_and_server_mutations(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        for case_number in range(1, 11):
            self.assertIn(f"`MSUI-{case_number:03d}`", text)

        normalized = " ".join(text.split())
        for marker in (
            "accessibility inventories",
            "modified client repeats a blocked pair",
            "before/after evidence",
            "Exact-copy snapshots",
            "Mutation tests",
        ):
            self.assertIn(marker, normalized)


if __name__ == "__main__":
    unittest.main()
