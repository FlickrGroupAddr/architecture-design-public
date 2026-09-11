import json
import unittest
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "queue-status-api.md"


class QueueCadenceCopyTests(unittest.TestCase):
    def test_active_copy_is_a_total_projection_of_server_behavior(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")

        for marker in (
            "## FGA LrC plug-in presentation and polling",
            "### Behavior-derived active-queue copy",
            "queue.activeAheadInPartition",
            "queue.nextWorkNotBefore",
            "queue.holds",
            "selects the first matching primary sentence",
            "A head/non-head/count/state/due combination outside",
            "status_projection_invalid",
        ):
            self.assertIn(marker, text)

    def test_copy_does_not_turn_operational_cadence_into_a_promise(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        for marker in (
            "does not say that work runs nightly, once per minute, once per group",
            "not a user-visible service promise",
            "controls only client reads",
            "**MUST NOT** be rendered or interpreted as worker cadence",
            "it remains a lower bound, not an appointment or ETA",
        ):
            self.assertIn(marker, normalized)

    def test_openapi_distinguishes_due_bound_from_poll_cadence(self) -> None:
        document = json.loads((ROOT / "openapi" / "openapi.json").read_text(encoding="utf-8"))
        schemas = cast("dict[str, dict[str, object]]", document["components"]["schemas"])

        queue_properties = cast(
            "dict[str, dict[str, object]]", schemas["IntentQueue"]["properties"]
        )
        due_description = cast("str", queue_properties["nextWorkNotBefore"]["description"])
        self.assertIn("database lower bound", due_description)
        self.assertIn("not an ETA or scheduler-cadence promise", due_description)

        for schema_name in ("IntentPage", "IntentItem"):
            properties = cast("dict[str, dict[str, object]]", schemas[schema_name]["properties"])
            poll_description = cast("str", properties["recommendedPollAfterSeconds"]["description"])
            self.assertIn("Minimum client read interval only", poll_description)
            self.assertIn("never worker cadence", poll_description)

    def test_review_records_legacy_copy_risk_as_resolved(self) -> None:
        review = (
            ROOT / "docs" / "research" / "2026-08-23-fresh-eyes-architecture-review.md"
        ).read_text(encoding="utf-8")

        n14 = next(line for line in review.splitlines() if line.startswith("| N-14 |"))
        self.assertIn("Resolved at the current design boundary by ticket #0044", n14)
        self.assertIn("no fixed scheduler-cadence promise", n14)
        self.assertIn("production-adapter fixtures and mutations", n14)


if __name__ == "__main__":
    unittest.main()
