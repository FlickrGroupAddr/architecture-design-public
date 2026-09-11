"""Run one disposable public Flickr photo replacement experiment."""

# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import time
import zlib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import flickrapi
import requests

from scripts.flickr_support import load_credentials, require_authorized_token

REPORT_SCHEMA_VERSION = 1
PNG_WIDTH = 192
PNG_HEIGHT = 128
BORDER_WIDTH = 5
ORIGINAL_ATTEMPTS = 60
EXECUTION_ACKNOWLEDGEMENT = "I-understand-this-creates-and-replaces-a-disposable-public-photo"


@dataclass(frozen=True)
class ImageSpec:
    """Deterministic colors for one synthetic probe image."""

    name: str
    first: tuple[int, int, int]
    second: tuple[int, int, int]
    accent: tuple[int, int, int]


@dataclass(frozen=True)
class Observation:
    """Sanitized identity and preservation evidence for one Flickr observation."""

    photo_id: str
    owner_nsid: str
    photo_page_url: str
    title: str
    description: str
    is_public: bool
    views: int
    favorite_count: int
    comment_count: int
    comment_ids_sha2_256: str
    tag_count: int
    tag_values_sha2_256: str
    album_context_count: int
    album_context_ids_sha2_256: str
    group_context_count: int
    group_context_ids_sha2_256: str
    original_format: str
    original_width: int
    original_height: int
    original_bytes: int
    original_sha2_256: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create one synthetic public Flickr photo, replace it once, record sanitized "
            "before/after evidence, then make it private."
        )
    )
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
        help="ignored directory containing an existing write-authorized OAuth token",
    )
    parser.add_argument(
        "--report-directory",
        type=Path,
        default=Path("artifacts"),
        help="ignored directory for generated images and the local evidence report",
    )
    parser.add_argument(
        "--execute-disposable-public-probe",
        required=True,
        help="required exact acknowledgement for the external mutation",
    )
    return parser.parse_args()


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    """Encode one PNG chunk."""
    checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)


def generate_png(path: Path, spec: ImageSpec) -> None:
    """Write one deterministic 8-bit RGB synthetic test pattern."""
    rows = bytearray()

    for y in range(PNG_HEIGHT):
        rows.append(0)
        for x in range(PNG_WIDTH):
            tile = ((x // 16) + (y // 16)) % 2
            color = spec.first if tile == 0 else spec.second
            if x == y or x == PNG_WIDTH - y - 1 or x < BORDER_WIDTH or y < BORDER_WIDTH:
                color = spec.accent
            rows.extend(color)

    header = struct.pack(">IIBBBBB", PNG_WIDTH, PNG_HEIGHT, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(bytes(rows), level=9))
        + png_chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_strings(values: list[str]) -> str:
    """Hash a canonical string set without exposing its member values."""
    canonical = "\n".join(sorted(set(values))).encode()
    return hashlib.sha256(canonical).hexdigest()


def text_content(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("_content", ""))
    if value is None:
        return ""
    return str(value)


def object_list(container: object, member: str) -> list[dict[str, Any]]:
    if not isinstance(container, dict):
        return []
    value = container.get(member, [])
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def integer(value: object) -> int:
    try:
        return int(text_content(value) or "0")
    except TypeError, ValueError:
        return 0


def download_hash(url: str) -> tuple[str, int]:
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


def original_evidence(
    flickr: flickrapi.FlickrAPI,
    photo_id: str,
    expected_sha2_256: str,
) -> tuple[str, int, int, int]:
    """Wait until Flickr exposes the expected downloadable Original."""
    last_observation: tuple[str, int, int, int] | None = None

    for attempt in range(ORIGINAL_ATTEMPTS):
        response = flickr.photos.getSizes(photo_id=photo_id)
        for size in object_list(response.get("sizes"), "size"):
            if size.get("label") != "Original" or not size.get("source"):
                continue
            digest, byte_count = download_hash(str(size["source"]))
            last_observation = (
                digest,
                byte_count,
                integer(size.get("width")),
                integer(size.get("height")),
            )
            if digest == expected_sha2_256:
                return last_observation
        if attempt + 1 < ORIGINAL_ATTEMPTS:
            time.sleep(2)

    if last_observation is None:
        raise RuntimeError("Flickr did not expose an Original size within the observation window")
    raise RuntimeError("Flickr Original did not converge to the intended replacement bytes")


def favorite_count(flickr: flickrapi.FlickrAPI, photo_id: str) -> int:
    response = flickr.photos.getFavorites(photo_id=photo_id, page="1", per_page="1")
    photo = response.get("photo", {})
    if not isinstance(photo, dict):
        return 0
    return integer(photo.get("total"))


def observe(
    flickr: flickrapi.FlickrAPI,
    photo_id: str,
    expected_sha2_256: str,
) -> Observation:
    info_response = flickr.photos.getInfo(photo_id=photo_id)
    photo = info_response.get("photo", {})
    if not isinstance(photo, dict):
        raise TypeError("Flickr getInfo did not return a photo object")

    contexts = flickr.photos.getAllContexts(photo_id=photo_id)
    comments_response = flickr.photos.comments.getList(photo_id=photo_id)
    comments = object_list(comments_response.get("comments"), "comment")
    tags = object_list(photo.get("tags"), "tag")
    albums = object_list(contexts, "set")
    groups = object_list(contexts, "pool")
    urls = object_list(photo.get("urls"), "url")
    photo_page_url = next(
        (text_content(item) for item in urls if item.get("type") == "photopage"),
        "",
    )
    original_sha, original_bytes, original_width, original_height = original_evidence(
        flickr,
        photo_id,
        expected_sha2_256,
    )

    return Observation(
        photo_id=str(photo.get("id", "")),
        owner_nsid=str(photo.get("owner", {}).get("nsid", "")),
        photo_page_url=photo_page_url,
        title=text_content(photo.get("title")),
        description=text_content(photo.get("description")),
        is_public=str(photo.get("visibility", {}).get("ispublic", "0")) == "1",
        views=integer(photo.get("views")),
        favorite_count=favorite_count(flickr, photo_id),
        comment_count=integer(photo.get("comments")),
        comment_ids_sha2_256=hash_strings([str(item.get("id", "")) for item in comments]),
        tag_count=len(tags),
        tag_values_sha2_256=hash_strings([text_content(item.get("raw")) for item in tags]),
        album_context_count=len(albums),
        album_context_ids_sha2_256=hash_strings([str(item.get("id", "")) for item in albums]),
        group_context_count=len(groups),
        group_context_ids_sha2_256=hash_strings([str(item.get("id", "")) for item in groups]),
        original_format=str(photo.get("originalformat", "")),
        original_width=original_width,
        original_height=original_height,
        original_bytes=original_bytes,
        original_sha2_256=original_sha,
    )


def preservation_checks(
    before: Observation,
    after: Observation,
    replacement_response_photo_id: str,
    replacement_sha2_256: str,
) -> dict[str, bool]:
    return {
        "replacementResponsePhotoIdStable": replacement_response_photo_id == before.photo_id,
        "observedPhotoIdStable": after.photo_id == before.photo_id,
        "ownerStable": after.owner_nsid == before.owner_nsid,
        "photoPageUrlStable": after.photo_page_url == before.photo_page_url,
        "publicVisibilityStable": before.is_public and after.is_public,
        "titleStable": after.title == before.title,
        "descriptionStable": after.description == before.description,
        "viewsNondecreasing": after.views >= before.views,
        "favoriteCountStable": after.favorite_count == before.favorite_count,
        "commentCountStable": after.comment_count == before.comment_count,
        "commentIdentitySetStable": after.comment_ids_sha2_256 == before.comment_ids_sha2_256,
        "tagSetStable": after.tag_values_sha2_256 == before.tag_values_sha2_256,
        "albumContextSetStable": (
            after.album_context_ids_sha2_256 == before.album_context_ids_sha2_256
        ),
        "groupContextSetStable": (
            after.group_context_ids_sha2_256 == before.group_context_ids_sha2_256
        ),
        "replacementOriginalIsPng": after.original_format == "png",
        "replacementOriginalIsIntendedBytes": after.original_sha2_256 == replacement_sha2_256,
        "replacementOriginalDimensionsCorrect": (
            after.original_width == PNG_WIDTH and after.original_height == PNG_HEIGHT
        ),
    }


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> Path:
    if args.execute_disposable_public_probe != EXECUTION_ACKNOWLEDGEMENT:
        raise RuntimeError(
            "Refusing external mutation: pass the exact documented disposable-probe acknowledgement"
        )

    started_at = datetime.now(UTC)
    stamp = started_at.strftime("%Y%m%d-%H%M%S")
    run_directory = args.report_directory.resolve() / f"flickr-replacement-probe-{stamp}"
    report_path = run_directory / "report.json"
    baseline_path = run_directory / "baseline.png"
    replacement_path = run_directory / "replacement.png"
    generate_png(
        baseline_path,
        ImageSpec("baseline", (21, 78, 121), (232, 174, 45), (255, 255, 255)),
    )
    generate_png(
        replacement_path,
        ImageSpec("replacement", (105, 35, 126), (43, 173, 113), (255, 90, 36)),
    )
    baseline_sha = hash_file(baseline_path)
    replacement_sha = hash_file(replacement_path)
    if baseline_sha == replacement_sha:
        raise RuntimeError("Synthetic baseline and replacement images unexpectedly match")

    api_key, api_secret = load_credentials(args.config)
    flickr, token = require_authorized_token(api_key, api_secret, args.token_cache)
    title = f"FGA disposable public replacement probe {started_at:%Y-%m-%d %H:%M:%S} UTC"
    description = (
        "Synthetic FGA architecture probe. No personal photograph. "
        "The photo will be made private after evidence capture."
    )
    report: dict[str, Any] = {
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "status": "starting",
        "startedAt": started_at.isoformat(),
        "oauthPermission": token.access_level,
        "syntheticImages": {
            "baseline": {"bytes": baseline_path.stat().st_size, "SHA2-256": baseline_sha},
            "replacement": {
                "bytes": replacement_path.stat().st_size,
                "SHA2-256": replacement_sha,
            },
            "width": PNG_WIDTH,
            "height": PNG_HEIGHT,
            "bitDepth": 8,
            "colorType": "RGB",
        },
        "replacement": {
            "mode": "synchronous",
            "asyncModeTested": False,
            "asyncModeReason": "Synchronous mode is sufficient for this bounded first probe.",
            "dispatchCount": 0,
        },
        "cleanup": {"photoMadePrivate": False, "photosetDeleted": False},
    }
    write_report(report_path, report)

    photo_id: str | None = None
    photoset_id: str | None = None
    probe_error: Exception | None = None

    try:
        upload_response = flickr.upload(
            filename=str(baseline_path),
            title=title,
            description=description,
            tags="fga-disposable-replacement-probe synthetic-test-image",
            is_public="1",
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
            raise RuntimeError("Flickr upload succeeded without a photo ID")
        report["resource"] = {"photoId": photo_id}
        report["status"] = "uploaded_public_baseline"
        write_report(report_path, report)

        flickr.photos.comments.addComment(
            photo_id=photo_id,
            comment_text="Synthetic owner comment for the disposable FGA replacement probe.",
        )
        photoset_response = flickr.photosets.create(
            title=f"FGA disposable replacement probe {stamp}",
            description="Synthetic temporary album for one replacement-preservation probe.",
            primary_photo_id=photo_id,
        )
        photoset = photoset_response.get("photoset", {})
        photoset_id = str(photoset.get("id", "")) if isinstance(photoset, dict) else ""
        if not photoset_id:
            raise RuntimeError("Flickr photoset creation succeeded without a photoset ID")
        report["resource"]["photosetId"] = photoset_id

        before = observe(flickr, photo_id, baseline_sha)
        report["before"] = asdict(before)
        report["status"] = "baseline_observed"
        write_report(report_path, report)

        report["replacement"]["dispatchCount"] = 1
        report["replacement"]["dispatchStartedAt"] = datetime.now(UTC).isoformat()
        write_report(report_path, report)
        replace_response = flickr.replace(
            filename=str(replacement_path),
            photo_id=photo_id,
            format="etree",
            timeout=300,
            **{"async": "0"},
        )
        replacement_response_photo_id = replace_response.findtext("photoid") or ""
        report["replacement"]["responsePhotoId"] = replacement_response_photo_id
        report["replacement"]["responseReceivedAt"] = datetime.now(UTC).isoformat()
        report["status"] = "replacement_response_received"
        write_report(report_path, report)

        after = observe(flickr, photo_id, replacement_sha)
        checks = preservation_checks(before, after, replacement_response_photo_id, replacement_sha)
        report["after"] = asdict(after)
        report["checks"] = checks
        report["limitations"] = {
            "nonzeroFavoritePreservationProven": before.favorite_count > 0,
            "nonemptyGroupContextPreservationProven": before.group_context_count > 0,
            "flickrContractPromisesSocialStatePreservation": False,
            "rollbackTested": False,
            "productionOrHistoricalPhotoAuthorized": False,
        }
        report["status"] = "evidence_captured" if all(checks.values()) else "evidence_failed"
        write_report(report_path, report)
    except Exception as error:  # preserve the one-dispatch rule and still quarantine the photo
        probe_error = error
        report["status"] = "failed_or_ambiguous"
        report["errorType"] = type(error).__name__
        report["error"] = str(error)
        write_report(report_path, report)
    finally:
        if photo_id:
            try:
                flickr.photos.setPerms(
                    photo_id=photo_id,
                    is_public="0",
                    is_friend="0",
                    is_family="0",
                    perm_comment="3",
                    perm_addmeta="2",
                )
                private_info = flickr.photos.getInfo(photo_id=photo_id).get("photo", {})
                report["cleanup"]["photoMadePrivate"] = (
                    str(private_info.get("visibility", {}).get("ispublic", "1")) == "0"
                )
            except Exception as cleanup_error:
                report["cleanup"]["photoPrivacyError"] = type(cleanup_error).__name__
        if photoset_id:
            try:
                flickr.photosets.delete(photoset_id=photoset_id)
                report["cleanup"]["photosetDeleted"] = True
            except Exception as cleanup_error:
                report["cleanup"]["photosetDeleteError"] = type(cleanup_error).__name__
        report["finishedAt"] = datetime.now(UTC).isoformat()
        if probe_error is None and report["status"] == "evidence_captured":
            if report["cleanup"]["photoMadePrivate"]:
                report["status"] = "passed_and_quarantined_private"
            else:
                report["status"] = "evidence_passed_cleanup_failed"
        write_report(report_path, report)

    if probe_error is not None:
        raise RuntimeError(
            "Disposable replacement probe failed or became ambiguous; replacement was not replayed"
        ) from probe_error
    if report["status"] != "passed_and_quarantined_private":
        raise RuntimeError("Replacement evidence or private cleanup did not pass")
    return report_path


def main() -> int:
    try:
        report_path = run(parse_args())
    except (
        RuntimeError,
        OSError,
        TypeError,
        flickrapi.FlickrError,
        requests.RequestException,
    ) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("PASS: one synthetic public photo was replaced once and made private.")
    print(f"Local evidence report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
