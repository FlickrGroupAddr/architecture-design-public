"""Generate the deterministic synthetic PNG used by ticket #0067."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from scripts.generate_selector_fixtures import FixtureSpec, fixture_bytes

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_PATH = (
    REPOSITORY_ROOT
    / "lightroom"
    / "FGA Diagnostics.lrdevplugin"
    / "catalog-association-fixtures"
    / "catalog-association-0067.png"
)
FIXTURE = FixtureSpec(
    filename=DEFAULT_OUTPUT_PATH.name,
    background=(8, 55, 70),
    foreground=(151, 236, 216),
    accent=(255, 72, 112),
    motif=4,
)


def expected_bytes() -> bytes:
    """Return the canonical PNG bytes for the #0067 fixture."""

    return fixture_bytes(FIXTURE)


def sha2_256(payload: bytes) -> str:
    """Return the lower-case SHA2-256 digest for a payload."""

    return hashlib.sha256(payload).hexdigest()


def write_fixture(output_path: Path = DEFAULT_OUTPUT_PATH) -> None:
    """Write the fixture, replacing only its exact output path."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(expected_bytes())


def fixture_matches(output_path: Path = DEFAULT_OUTPUT_PATH) -> bool:
    """Return whether the fixture exists and has the canonical bytes."""

    return output_path.is_file() and output_path.read_bytes() == expected_bytes()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the committed fixture is missing or stale",
    )
    return parser.parse_args()


def main() -> None:
    """Generate or verify the committed #0067 fixture."""

    args = parse_args()
    if args.check:
        if not fixture_matches():
            raise SystemExit(
                f"Catalog-association fixture is missing or stale: {DEFAULT_OUTPUT_PATH}"
            )
        print(f"Verified {DEFAULT_OUTPUT_PATH} ({sha2_256(expected_bytes())}).")
        return

    write_fixture()
    print(f"Wrote {DEFAULT_OUTPUT_PATH} ({sha2_256(expected_bytes())}).")


if __name__ == "__main__":
    main()
