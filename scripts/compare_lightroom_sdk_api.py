"""Compare calls documented by two Lightroom Classic SDK releases."""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

SIGNATURE_PATTERN = re.compile(
    r'<dt><a name="(?P<anchor>[^"]+)"></a>\s*'
    r"<strong>(?P<name>[^<]+)</strong>\((?P<parameters>.*?)\)</dt>",
    re.DOTALL,
)
SUMMARY_PATTERN = re.compile(
    r"^\s*<dd>\s*(?P<summary>.*?)(?=<h3>|</dd>)",
    re.DOTALL,
)
TAG_PATTERN = re.compile(r"<[^>]+>")
WHITESPACE_PATTERN = re.compile(r"\s+")

REVIEW_PATTERNS = {
    "security_and_entropy": re.compile(
        r"random|entropy|cryptograph|crypto|nonce|uuid|password|credential|"
        r"secret|digest|hash|encrypt",
        re.IGNORECASE,
    ),
    "transport": re.compile(
        r"http|https|tls|ssl|socket|certificate|network",
        re.IGNORECASE,
    ),
    "publish_export_and_render": re.compile(
        r"publish|export|render|rendition|photo",
        re.IGNORECASE,
    ),
}


@dataclass(frozen=True)
class DocumentedCall:
    """One callable interface found in Adobe's published API Reference."""

    key: str
    name: str
    signature: str
    summary: str
    module_file: str
    anchor: str


@dataclass(frozen=True)
class ApiInventory:
    """The documented calls extracted from one SDK release."""

    sdk_root: str
    calls: tuple[DocumentedCall, ...]

    @property
    def call_count(self) -> int:
        return len(self.calls)


class CallRecord(TypedDict):
    """JSON representation of one documented call."""

    key: str
    name: str
    signature: str
    summary: str
    module_file: str
    anchor: str


class ChangedCallRecord(TypedDict):
    """JSON representation of a changed documented call."""

    key: str
    name: str
    signature_changed: bool
    summary_changed: bool
    previous_signature: str
    current_signature: str
    previous_summary: str
    current_summary: str
    previous_module_file: str
    current_module_file: str


class ComparisonReport(TypedDict):
    """Complete JSON report shape."""

    schema_version: int
    generated_at_utc: str
    previous_sdk_root: str
    current_sdk_root: str
    previous_call_count: int
    current_call_count: int
    added_count: int
    removed_count: int
    changed_count: int
    added: list[CallRecord]
    removed: list[CallRecord]
    changed: list[ChangedCallRecord]
    current_review_candidates: dict[str, list[CallRecord]]


def call_record(call: DocumentedCall) -> CallRecord:
    """Convert a documented call to its stable JSON shape."""

    return {
        "key": call.key,
        "name": call.name,
        "signature": call.signature,
        "summary": call.summary,
        "module_file": call.module_file,
        "anchor": call.anchor,
    }


def normalize_documentation_html(value: str) -> str:
    """Reduce a small HTML fragment to stable, human-readable text."""

    without_tags = TAG_PATTERN.sub(" ", value)
    decoded = html.unescape(without_tags)
    return WHITESPACE_PATTERN.sub(" ", decoded).strip()


def inventory_sdk(sdk_root: Path) -> ApiInventory:
    """Inventory calls from the SDK's documented API modules."""

    resolved_sdk_root = sdk_root.resolve()
    modules_root = resolved_sdk_root / "API Reference" / "modules"
    if not modules_root.is_dir():
        message = f"The SDK does not contain 'API Reference/modules': '{resolved_sdk_root}'."
        raise ValueError(message)

    calls: list[DocumentedCall] = []
    for module_file in sorted(modules_root.glob("*.html"), key=lambda path: path.name):
        module_html = module_file.read_text(encoding="utf-8", errors="replace")
        matches = tuple(SIGNATURE_PATTERN.finditer(module_html))
        for index, match in enumerate(matches):
            next_index = (
                matches[index + 1].start() if index + 1 < len(matches) else len(module_html)
            )
            body = module_html[match.end() : next_index]
            summary_match = SUMMARY_PATTERN.match(body)
            name = normalize_documentation_html(match.group("name"))
            parameters = normalize_documentation_html(match.group("parameters"))
            summary = (
                normalize_documentation_html(summary_match.group("summary"))
                if summary_match
                else ""
            )
            calls.append(
                DocumentedCall(
                    key=f"{module_file.name}::{name}",
                    name=name,
                    signature=f"{name}({parameters})",
                    summary=summary,
                    module_file=module_file.name,
                    anchor=html.unescape(match.group("anchor")),
                )
            )

    calls.sort(key=lambda call: call.key)
    duplicate_keys = sorted(
        key for key in {call.key for call in calls} if sum(c.key == key for c in calls) > 1
    )
    if duplicate_keys:
        message = "The SDK inventory contains duplicate documented call keys: " + ", ".join(
            duplicate_keys
        )
        raise ValueError(message)

    return ApiInventory(
        sdk_root=str(resolved_sdk_root),
        calls=tuple(calls),
    )


def compare_inventories(
    previous: ApiInventory,
    current: ApiInventory,
) -> ComparisonReport:
    """Return a JSON-compatible documented-API comparison report."""

    previous_by_key = {call.key: call for call in previous.calls}
    current_by_key = {call.key: call for call in current.calls}
    added = [
        call_record(current_by_key[key])
        for key in sorted(current_by_key.keys() - previous_by_key.keys())
    ]
    removed = [
        call_record(previous_by_key[key])
        for key in sorted(previous_by_key.keys() - current_by_key.keys())
    ]
    changed: list[ChangedCallRecord] = []

    for key in sorted(previous_by_key.keys() & current_by_key.keys()):
        old_call = previous_by_key[key]
        new_call = current_by_key[key]
        signature_changed = old_call.signature != new_call.signature
        summary_changed = old_call.summary != new_call.summary
        if signature_changed or summary_changed:
            changed.append(
                {
                    "key": key,
                    "name": new_call.name,
                    "signature_changed": signature_changed,
                    "summary_changed": summary_changed,
                    "previous_signature": old_call.signature,
                    "current_signature": new_call.signature,
                    "previous_summary": old_call.summary,
                    "current_summary": new_call.summary,
                    "previous_module_file": old_call.module_file,
                    "current_module_file": new_call.module_file,
                }
            )

    review_candidates = {
        bucket: [
            call_record(call)
            for call in current.calls
            if pattern.search(f"{call.name} {call.summary}")
        ]
        for bucket, pattern in REVIEW_PATTERNS.items()
    }

    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "previous_sdk_root": previous.sdk_root,
        "current_sdk_root": current.sdk_root,
        "previous_call_count": previous.call_count,
        "current_call_count": current.call_count,
        "added_count": len(added),
        "removed_count": len(removed),
        "changed_count": len(changed),
        "added": added,
        "removed": removed,
        "changed": changed,
        "current_review_candidates": review_candidates,
    }


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""

    parser = argparse.ArgumentParser(
        description=("Compare callable interfaces documented by two Lightroom Classic SDKs.")
    )
    parser.add_argument(
        "--previous-sdk-root",
        required=True,
        type=Path,
        help="Root directory of the preceding licensed Lightroom SDK.",
    )
    parser.add_argument(
        "--current-sdk-root",
        required=True,
        type=Path,
        help="Root directory of the new licensed Lightroom SDK.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(r"C:\Temp\FGA-lightroom-sdk-api-comparison.json"),
        help="Local JSON report path outside Git.",
    )
    return parser


def main() -> None:
    """Run the documented-API comparison."""

    arguments = build_argument_parser().parse_args()
    previous = inventory_sdk(arguments.previous_sdk_root)
    current = inventory_sdk(arguments.current_sdk_root)
    report = compare_inventories(previous, current)

    output_path = arguments.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Previous documented calls: {previous.call_count}")
    print(f"Current documented calls:  {current.call_count}")
    print(
        "Added: "
        f"{report['added_count']}; removed: {report['removed_count']}; "
        f"changed signature/summary: {report['changed_count']}"
    )
    for change in report["added"]:
        print(f"  ADDED   {change['signature']}")
    for change in report["removed"]:
        print(f"  REMOVED {change['signature']}")
    for change in report["changed"]:
        print(f"  CHANGED {change['name']}")
    print(f"Full comparison: {output_path}")


if __name__ == "__main__":
    main()
