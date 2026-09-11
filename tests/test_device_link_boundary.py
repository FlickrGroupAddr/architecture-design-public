import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DeviceLinkBoundaryTests(unittest.TestCase):
    def test_private_mvp_exposes_no_device_link_route(self) -> None:
        document = json.loads((ROOT / "openapi" / "openapi.json").read_text(encoding="utf-8"))

        self.assertFalse(
            any("device" in path.casefold() for path in document["paths"]),
            "the private-MVP API must not expose a device-link route",
        )

    def test_future_allocator_cannot_overwrite_a_collision(self) -> None:
        contract = (ROOT / "docs" / "private-install-credential-transfer.md").read_text(
            encoding="utf-8"
        )

        for required_text in (
            "atomic create-if-absent",
            "enforce the\nhuman code's uniqueness",
            "generates an entirely fresh code and retries",
            "Retries are bounded",
            "A check-then-create sequence does not satisfy this contract",
        ):
            self.assertIn(required_text, contract)

    def test_review_records_the_legacy_finding_as_resolved(self) -> None:
        review = (
            ROOT / "docs" / "research" / "2026-08-23-fresh-eyes-architecture-review.md"
        ).read_text(encoding="utf-8")

        n09 = next(line for line in review.splitlines() if line.startswith("| N-09 |"))
        self.assertIn("Resolved at the current design boundary by ticket #0040", n09)
        self.assertIn("atomic create-if-absent", n09)
        self.assertIn("no mutation or disclosure of the existing attempt", n09)


if __name__ == "__main__":
    unittest.main()
