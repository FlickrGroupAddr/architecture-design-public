"""Tests for the proposed health and diagnostics boundary."""

from __future__ import annotations

import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
HEALTH_CONTRACT = REPOSITORY_ROOT / "docs" / "operations" / "health-and-diagnostics.md"


class HealthDiagnosticsContractTests(unittest.TestCase):
    def test_public_health_is_fixed_coarse_and_dependency_free(self) -> None:
        text = HEALTH_CONTRACT.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        for marker in (
            "`GET`/`HEAD /healthz/startup`",
            "`GET`/`HEAD /healthz/live`",
            '{"schemaVersion":1,"status":"ok"}',
            "Cache-Control: no-store",
            "liveness handler performs no database, filesystem, network",
            "Cloud Run does not receive a secret probe header",
        ):
            self.assertIn(marker, normalized)

    def test_public_debug_is_absent_and_admin_resource_is_explicit(self) -> None:
        text = HEALTH_CONTRACT.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        self.assertIn("registers no handler or compatibility redirect", normalized)
        self.assertIn("GET /api/v001/admin/deployment", normalized)
        self.assertIn(
            "requires a valid Google-authenticated FGA administrative session",
            normalized,
        )
        self.assertIn(
            "performs no Flickr, Google sign-in/JWKS, Secret Manager",
            normalized,
        )

    def test_selected_cloud_run_probes_avoid_preview_readiness(self) -> None:
        text = HEALTH_CONTRACT.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        self.assertIn("Startup | `/healthz/startup` | `0 seconds`", normalized)
        self.assertIn("Liveness | `/healthz/live` | `5 seconds", normalized)
        self.assertIn("current Preview readiness-probe feature", normalized)
        self.assertIn("Reconsider a separate readiness probe only after", normalized)

    def test_route_and_admin_contracts_project_the_boundary(self) -> None:
        route_contract = (
            REPOSITORY_ROOT / "docs" / "operations" / "http-route-conformance.md"
        ).read_text(encoding="utf-8")
        admin_contract = (
            REPOSITORY_ROOT / "docs" / "administrative-control-plane-contract.md"
        ).read_text(encoding="utf-8")
        hosted_contract = (REPOSITORY_ROOT / "docs" / "hosted-deployment.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Exact `/api` and prefix `/api/`", route_contract)
        self.assertIn("GET /api/debug", route_contract)
        self.assertIn("Read deployment status", admin_contract)
        self.assertIn("GET /api/v001/admin/deployment", admin_contract)
        self.assertIn("current Preview Cloud Run readiness", hosted_contract)


if __name__ == "__main__":
    unittest.main()
