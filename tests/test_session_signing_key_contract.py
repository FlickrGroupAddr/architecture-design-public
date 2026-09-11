"""Tests for the FGA API backend framework-signing key contract."""

from __future__ import annotations

import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONTRACT = REPOSITORY_ROOT / "docs" / "operations" / "session-signing-key.md"


class SessionSigningKeyContractTests(unittest.TestCase):
    def test_contract_pins_canonical_256_bit_representation(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        for marker in (
            "exactly 32 bytes",
            "canonical RFC 4648 base64url without padding",
            "^[A-Za-z0-9_-]{43}$",
            "strict base64url decode",
            "exactly 32 decoded bytes",
            "cannot prove that the bytes were random",
        ):
            self.assertIn(marker, normalized)

    def test_contract_requires_exact_version_and_fail_closed_startup(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        for marker in (
            "FGA_DJANGO_SECRET_KEY_VERSION",
            "FGA_DJANGO_SECRET_KEY_FALLBACK_VERSION",
            "`latest`",
            "Verify the response's payload CRC32C",
            "never becomes ready",
            "It does not generate a replacement",
            "worker service account has no access",
        ):
            self.assertIn(marker, normalized)

    def test_rotation_has_one_bounded_fallback_and_compromise_path(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        self.assertIn("At most one fallback exists", normalized)
        self.assertIn("24-hour absolute administrative-session lifetime", normalized)
        self.assertIn("do not configure the exposed key as a fallback", normalized)
        self.assertIn("revoke every administrative session", normalized)

    def test_normative_and_derived_documents_link_the_contract(self) -> None:
        expected_link = "operations/session-signing-key.md"
        for relative_path in (
            "docs/administrative-control-plane-contract.md",
            "docs/architecture.md",
            "docs/future-terry-faq.md",
            "docs/hosted-deployment.md",
        ):
            text = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn(expected_link, text, relative_path)


if __name__ == "__main__":
    unittest.main()
