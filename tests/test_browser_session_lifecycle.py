"""Tests for the accepted FGA browser-session lifecycle contract."""

from __future__ import annotations

import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONTRACT = REPOSITORY_ROOT / "docs" / "browser-session-lifecycle.md"
ADR = (
    REPOSITORY_ROOT
    / "docs"
    / "decisions"
    / "0043-use-transaction-bound-google-session-reauthentication.md"
)


class BrowserSessionLifecycleTests(unittest.TestCase):
    def test_login_cookie_and_record_are_exact(self) -> None:
        normalized = " ".join(CONTRACT.read_text(encoding="utf-8").split())

        for marker in (
            "`POST /admin/google-login`",
            "`__Host-fga_admin`",
            "Max-Age=86400",
            "no `Domain` attribute",
            "`SHA2-256(state)`",
            "`SHA2-256(nonce)`",
            "`tokenDigest`",
            "`csrfToken`",
            "`recentAuthenticationAt`",
            "Exactly `createdAt + 24 hours`; immutable",
            "Idle timeout | None for the private MVP",
        ):
            self.assertIn(marker, normalized)

    def test_reauthentication_is_bound_rotating_and_honest(self) -> None:
        normalized = " ".join(CONTRACT.read_text(encoding="utf-8").split())

        for marker in (
            "`POST /api/v001/admin/session/reauthentication`",
            "five-minute, single-use transaction",
            "bound `sessionId`",
            "exact `fgaUserId`",
            "revokes the bound old session",
            "invalidates the old CSRF token",
            "no pending mutation",
            "does not prove that Google asked for a password, passkey, MFA",
            "The unsigned `select_by` form value is diagnostic-only",
        ):
            self.assertIn(marker, normalized)

    def test_concurrency_revocation_cleanup_and_incident_rules_are_closed(self) -> None:
        normalized = " ".join(CONTRACT.read_text(encoding="utf-8").split())

        for marker in (
            "private MVP permits multiple active sessions",
            "There is no arbitrary active-session cap",
            "`expectedSessionSetRevision`",
            "`expectedActiveOtherSessionCount`",
            "`409 current_session_requires_logout`",
            "30 days after terminal time",
            "at least hourly",
            "reason `security_incident`",
            "does not restore administrative readiness",
        ):
            self.assertIn(marker, normalized)

    def test_rotation_has_exact_revision_and_stale_tab_recovery_rules(self) -> None:
        normalized = " ".join(CONTRACT.read_text(encoding="utf-8").split())

        for marker in (
            "increments it exactly once, regardless of the number of rows changed",
            "reauthentication rotation",
            "never replays that request automatically",
            "session changed in another tab",
            "requires a new user submission",
            "scrubs the administrative view and returns to login",
        ):
            self.assertIn(marker, normalized)

    def test_adr_and_derived_documents_link_the_contract(self) -> None:
        self.assertIn(
            "Status: Accepted by Terry on 2026-08-31",
            ADR.read_text(encoding="utf-8").partition("## Context")[0],
        )
        expected_link = "browser-session-lifecycle.md"
        for relative_path in (
            "README.md",
            "docs/administrative-control-plane-contract.md",
            "docs/architecture.md",
            "docs/decisions/0039-use-google-identity-services-browser-sessions.md",
            "docs/diagrams/README.md",
            "docs/future-terry-faq.md",
            "docs/oauth-and-account-lifecycle.md",
        ):
            text = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn(expected_link, text, relative_path)


if __name__ == "__main__":
    unittest.main()
