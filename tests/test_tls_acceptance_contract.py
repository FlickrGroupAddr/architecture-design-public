"""Tests for the accepted private-MVP TLS gate."""

from __future__ import annotations

import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TLS_CONTRACT = REPOSITORY_ROOT / "docs" / "operations" / "tls-edge-acceptance.md"
TLS_ADR = REPOSITORY_ROOT / "docs" / "decisions" / "0036-use-a-right-sized-private-tls-gate.md"


class TlsAcceptanceContractTests(unittest.TestCase):
    def test_accepted_gate_names_every_core_evidence_source(self) -> None:
        contract = TLS_CONTRACT.read_text(encoding="utf-8")

        for marker in (
            "Status: Accepted normative operations contract under ADR 0036",
            "documented `LrHttp`",
            "`testssl.sh` v3.2.4",
            "`--jsonfile-pretty`",
            "Qualys SSL Labs",
            "### Initial issuance",
            "### Rollover drill",
            "### Managed renewal",
            "### Deployment restore drill",
            "configured; not yet observed",
        ):
            self.assertIn(marker, contract)

    def test_extra_scanners_are_outside_the_core_gate(self) -> None:
        contract = TLS_CONTRACT.read_text(encoding="utf-8")
        core, expansion = contract.split("## Retesting and expansion triggers", 1)

        for diagnostic in ("Hardenize", "SSLyze", "Nmap", "OpenSSL"):
            self.assertNotIn(diagnostic, core)
            self.assertIn(diagnostic, expansion)

        self.assertIn("do not become a permanent private-MVP matrix", expansion)

    def test_adr_records_terrys_accepted_decision(self) -> None:
        adr = TLS_ADR.read_text(encoding="utf-8")

        self.assertIn("Status: Accepted by Terry on 2026-08-25", adr)
        self.assertIn("a pinned stable `testssl.sh`", adr)
        self.assertIn("one fresh independent Qualys SSL Labs assessment", adr)
        self.assertIn("naturally observed managed-renewal", adr)


if __name__ == "__main__":
    unittest.main()
