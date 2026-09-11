"""Upload a private PNG to Flickr and verify its downloadable original."""

# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import flickrapi
import requests
from flickr_support import (
    EXPECTED_PROFILE_URL,
    load_credentials,
    normalized_profile_identity,
)

REPORT_SCHEMA_VERSION = 2
ORIGINAL_SIZE_ATTEMPTS = 30


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Privately upload one PNG, verify Flickr reports and returns the original, "
            "and compare SHA2-256 hashes. The photo is not deleted."
        )
    )
    parser.add_argument("--image", required=True, type=Path, help="8-bit sRGB PNG to test")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(".secrets/flickr.json"),
        help="ignored JSON file containing api_key and api_secret",
    )
    parser.add_argument(
        "--token-cache",
        type=Path,
        default=Path(".secrets/flickr-token-cache"),
        help="ignored directory for the OAuth token database",
    )
    parser.add_argument(
        "--report-directory",
        type=Path,
        default=Path("artifacts"),
        help="ignored directory for the local result report",
    )
    return parser.parse_args()


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def original_size(flickr: flickrapi.FlickrAPI, photo_id: str) -> dict[str, Any]:
    for attempt in range(ORIGINAL_SIZE_ATTEMPTS):
        response = flickr.photos.getSizes(photo_id=photo_id)
        sizes = response["sizes"]["size"]

        for size in sizes:
            if size.get("label") == "Original" and size.get("source"):
                return size

        if attempt + 1 < ORIGINAL_SIZE_ATTEMPTS:
            time.sleep(2)

    raise RuntimeError("Flickr did not expose the Original size within 60 seconds")


def hash_url(url: str) -> tuple[str, int]:
    digest = hashlib.sha256()
    byte_count = 0

    try:
        response_context = requests.get(url, stream=True, timeout=(15, 180))
    except requests.RequestException as error:
        raise RuntimeError("Flickr Original download request failed") from error

    with response_context as response:
        if not response.ok:
            raise RuntimeError(f"Flickr Original download returned HTTP {response.status_code}")

        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                digest.update(chunk)
                byte_count += len(chunk)

    return digest.hexdigest(), byte_count


def run(args: argparse.Namespace) -> Path:
    image_path = args.image.resolve(strict=True)

    if image_path.suffix.casefold() != ".png":
        raise RuntimeError(f"Expected a PNG test image, got: {image_path}")

    api_key, api_secret = load_credentials(args.config)
    token_cache = args.token_cache.resolve()
    token_cache.mkdir(parents=True, exist_ok=True)

    flickr = flickrapi.FlickrAPI(
        api_key,
        api_secret,
        format="parsed-json",
        token_cache_location=str(token_cache),
        timeout=60,
    )

    if not flickr.token_valid(perms="write"):
        print("Opening Flickr authorization in your browser (permission: write).")
        flickr.authenticate_via_browser(perms="write")

    token = flickr.token_cache.token

    if token is None:
        raise RuntimeError("Flickr authentication completed without an access token")

    profile_response = flickr.urls.getUserPhotos(user_id=token.user_nsid)
    authenticated_profile_url = profile_response["user"].get("url")

    if not authenticated_profile_url:
        raise RuntimeError("Flickr did not return the authenticated account's profile URL")

    if normalized_profile_identity(authenticated_profile_url) != normalized_profile_identity(
        EXPECTED_PROFILE_URL
    ):
        raise RuntimeError(
            "Refusing to upload: authenticated profile is "
            f"{authenticated_profile_url}, expected {EXPECTED_PROFILE_URL}"
        )

    started_at = datetime.now(UTC)
    stamp = started_at.strftime("%Y%m%d-%H%M%S")
    report_path = args.report_directory.resolve() / f"flickr-roundtrip-{stamp}.json"
    local_hash = hash_file(image_path)
    title = f"FGA private PNG round-trip {started_at:%Y-%m-%d %H:%M:%S} UTC"
    report: dict[str, Any] = {
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "status": "uploading",
        "startedAt": started_at.isoformat(),
        "expectedProfileUrl": EXPECTED_PROFILE_URL,
        "authenticatedProfileUrl": authenticated_profile_url,
        "oauthPermission": token.access_level,
        "libraryVersions": {
            "flickrapi": importlib.metadata.version("flickrapi"),
            "requests": importlib.metadata.version("requests"),
        },
        "local": {
            "path": str(image_path),
            "fileSizeBytes": image_path.stat().st_size,
            "SHA2-256": local_hash,
        },
        "upload": {
            "title": title,
            "isPublic": False,
            "isFriend": False,
            "isFamily": False,
            "hiddenFromSearch": True,
        },
    }
    write_report(report_path, report)

    try:
        print(f"Uploading privately: {image_path.name} ({image_path.stat().st_size:,} bytes)")
        upload_response = flickr.upload(
            filename=str(image_path),
            title=title,
            description="FGA private integration test; safe to delete after verification.",
            is_public="0",
            is_friend="0",
            is_family="0",
            safety_level="1",
            content_type="1",
            hidden="2",
            format="etree",
            timeout=300,
        )
        photo_id = upload_response.findtext("photoid")

        if not photo_id:
            raise RuntimeError("Flickr upload succeeded without returning a Flickr photo ID")

        report["upload"]["photoId"] = photo_id
        report["status"] = "uploaded"
        write_report(report_path, report)

        info_response = flickr.photos.getInfo(photo_id=photo_id)
        photo = info_response["photo"]
        photo_page_url = next(
            (url.get("_content") for url in photo["urls"]["url"] if url.get("type") == "photopage"),
            None,
        )
        original_format = photo.get("originalformat")
        original = original_size(flickr, photo_id)
        original_hash, original_bytes = hash_url(original["source"])
        hashes_match = original_hash == local_hash
        sizes_match = original_bytes == image_path.stat().st_size

        report["flickr"] = {
            "originalFormat": original_format,
            "originalWidth": int(original["width"]),
            "originalHeight": int(original["height"]),
            "downloadedOriginalBytes": original_bytes,
            "downloadedOriginalHashes": {"SHA2-256": original_hash},
            "photoPageUrl": photo_page_url,
        }
        report["verification"] = {
            "formatIsPng": original_format == "png",
            "hashesMatch": hashes_match,
            "sizesMatch": sizes_match,
        }
        report["finishedAt"] = datetime.now(UTC).isoformat()
        report["status"] = (
            "passed" if original_format == "png" and hashes_match and sizes_match else "failed"
        )
        write_report(report_path, report)

        if report["status"] != "passed":
            raise RuntimeError("Flickr original verification failed; inspect the local report")

        print(f"PASS: Flickr returned an identical PNG original ({original_bytes:,} bytes).")
        print(f"Private test photo: {photo_page_url or photo_id}")
        print("The photo was intentionally not deleted; OAuth permission is write, not delete.")
        return report_path
    except Exception as error:
        report["status"] = "failed"
        report["finishedAt"] = datetime.now(UTC).isoformat()
        report["errorType"] = type(error).__name__
        report["error"] = str(error)
        write_report(report_path, report)
        raise


def main() -> int:
    try:
        report_path = run(parse_args())
    except (
        RuntimeError,
        OSError,
        flickrapi.FlickrError,
        requests.RequestException,
    ) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Local report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
