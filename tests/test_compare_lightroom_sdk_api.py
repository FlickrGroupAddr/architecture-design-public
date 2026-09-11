"""Tests for the documented Lightroom SDK API comparison."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.compare_lightroom_sdk_api import (
    ApiInventory,
    DocumentedCall,
    compare_inventories,
    inventory_sdk,
    normalize_documentation_html,
)


class CompareLightroomSdkApiTests(unittest.TestCase):
    def test_normalize_documentation_html(self) -> None:
        self.assertEqual(
            normalize_documentation_html("&nbsp;one, <code>two</code>&nbsp;"),
            "one, two",
        )

    def test_inventory_reads_documented_calls_including_zero_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            sdk_root = Path(temporary_directory)
            modules_root = sdk_root / "API Reference" / "modules"
            modules_root.mkdir(parents=True)
            (modules_root / "LrExample.html").write_text(
                """
                <dt><a name="LrExample.noArgs"></a>
                <strong>LrExample.noArgs</strong>()</dt>
                <dd>Returns a value.<h3>Return value</h3></dd>
                <dt><a name="LrExample.withArg"></a>
                <strong>LrExample.withArg</strong>(&nbsp;value&nbsp;)</dt>
                <dd>Accepts <code>value</code>.</dd>
                """,
                encoding="utf-8",
            )

            inventory = inventory_sdk(sdk_root)

        self.assertEqual(inventory.call_count, 2)
        self.assertEqual(
            [call.signature for call in inventory.calls],
            ["LrExample.noArgs()", "LrExample.withArg(value)"],
        )
        self.assertEqual(inventory.calls[0].summary, "Returns a value.")

    def test_compare_reports_added_removed_and_changed_calls(self) -> None:
        unchanged = self._call("LrExample.unchanged", "value", "Same summary.")
        previous = ApiInventory(
            sdk_root="previous",
            calls=(
                unchanged,
                self._call("LrExample.changed", "old", "Old summary."),
                self._call("LrExample.removed", "", "Removed."),
            ),
        )
        current = ApiInventory(
            sdk_root="current",
            calls=(
                unchanged,
                self._call("LrExample.added", "", "Added secure random bytes."),
                self._call("LrExample.changed", "new", "New summary."),
            ),
        )

        report = compare_inventories(previous, current)

        self.assertEqual(report["added_count"], 1)
        self.assertEqual(report["removed_count"], 1)
        self.assertEqual(report["changed_count"], 1)
        changed = report["changed"]
        self.assertIsInstance(changed, list)
        self.assertEqual(changed[0]["name"], "LrExample.changed")

    @staticmethod
    def _call(name: str, parameters: str, summary: str) -> DocumentedCall:
        module_file = "LrExample.html"
        return DocumentedCall(
            key=f"{module_file}::{name}",
            name=name,
            signature=f"{name}({parameters})",
            summary=summary,
            module_file=module_file,
            anchor=name,
        )


if __name__ == "__main__":
    unittest.main()
