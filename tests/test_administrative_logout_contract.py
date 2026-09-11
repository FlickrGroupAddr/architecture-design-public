"""Tests for the proposed administrative logout failure contract."""

from __future__ import annotations

import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE = REPOSITORY_ROOT / "docs" / "oauth-and-account-lifecycle.md"


class AdministrativeLogoutContractTests(unittest.TestCase):
    def test_server_commits_before_cookie_expiration(self) -> None:
        text = LIFECYCLE.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        for marker in (
            "mark it revoked and append the successful logout audit event",
            "An audit failure rolls back the revocation",
            "Only after that commit, return `204 No Content`",
            "Max-Age=0",
            "SameSite=Strict",
        ):
            self.assertIn(marker, normalized)

    def test_failed_or_unknown_logout_retains_retry_authority(self) -> None:
        text = LIFECYCLE.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        self.assertIn("`503 logout_unavailable`", normalized)
        self.assertIn("`503 logout_outcome_unknown`", normalized)
        self.assertIn("Neither `503` response contains `Set-Cookie`", normalized)
        self.assertIn("preserves the authority needed to repeat", normalized)
        self.assertIn("No error response says **signed out**", normalized)

    def test_ui_separates_view_scrubbing_from_authentication_state(self) -> None:
        text = LIFECYCLE.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        for marker in (
            "`logout_submitting`",
            "`signed_out_confirmed`",
            "`logout_unconfirmed`",
            (
                "Sign-out unconfirmed. This browser may still hold an active FGA "
                "administrative session."
            ),
            "Clearing the rendered view is privacy hygiene, not authentication state",
            "Client code cannot read or delete the `HttpOnly` cookie",
        ):
            self.assertIn(marker, normalized)

    def test_retry_converges_and_private_window_does_not_overclaim(self) -> None:
        text = LIFECYCLE.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        self.assertIn("if the first transaction never committed", normalized)
        self.assertIn("if it committed but the response was lost", normalized)
        self.assertIn("the cookie-free repeat also returns `204`", normalized)
        self.assertIn("still does not prove that the FGA database row was revoked", normalized)
        self.assertIn("non-sliding 24-hour absolute expiry", normalized)

    def test_derived_contracts_link_and_route_probe_logout(self) -> None:
        expected_link = "oauth-and-account-lifecycle.md#logout-outcome-and-recovery"
        for relative_path in (
            "docs/administrative-control-plane-contract.md",
            "docs/architecture.md",
            "docs/future-terry-faq.md",
        ):
            text = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn(expected_link, text, relative_path)

        route_contract = (
            REPOSITORY_ROOT / "docs" / "operations" / "http-route-conformance.md"
        ).read_text(encoding="utf-8")
        self.assertIn("POST /api/v001/admin/session/logout", route_contract)
        self.assertIn("fixed `__Host-fga_admin` expiration header", route_contract)


if __name__ == "__main__":
    unittest.main()
