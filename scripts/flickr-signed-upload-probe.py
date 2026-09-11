"""Probe a service-signed, direct-to-Flickr multipart upload boundary."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import flickrapi
import requests
from defusedxml import ElementTree
from flickr_support import (
    EXPECTED_PROFILE_URL,
    load_credentials,
    require_authorized_token,
)
from flickr_upload_signing import SignedUpload, sign_upload
from requests_toolbelt import MultipartEncoder

REPORT_SCHEMA_VERSION = 1
AUTHENTICATION_ERROR_CODES = {96, 97, 98, 99, 100}
MISSING_PHOTO_ERROR_CODE = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sign upload metadata separately, privately upload one PNG, then probe "
            "signature replay and metadata tampering without sending more image bytes."
        )
    )
    parser.add_argument("--image", required=True, type=Path, help="PNG to upload privately")
    parser.add_argument("--config", required=True, type=Path, help="ignored Flickr credential file")
    parser.add_argument(
        "--token-cache",
        type=Path,
        default=Path(".secrets/flickr-token-cache"),
        help="ignored directory containing the authorized Flickr token",
    )
    parser.add_argument(
        "--report-directory",
        type=Path,
        default=Path("artifacts"),
        help="ignored directory for the sanitized local report",
    )
    return parser.parse_args()


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def send_upload(
    signed: SignedUpload,
    *,
    image_path: Path | None,
    metadata: dict[str, str] | None = None,
) -> dict[str, Any]:
    actual_metadata = metadata if metadata is not None else signed.metadata

    with ExitStack() as resources:
        fields: list[tuple[str, Any]] = sorted(actual_metadata.items())

        if image_path is not None:
            image_stream = resources.enter_context(image_path.open("rb"))
            fields.append(("photo", (image_path.name, image_stream, "image/png")))

        encoder = MultipartEncoder(fields=fields)
        response = requests.post(
            signed.url,
            data=encoder,
            headers={
                "Authorization": signed.authorization,
                "Content-Type": encoder.content_type,
            },
            timeout=(15, 300),
        )

    try:
        root = ElementTree.fromstring(response.content)
    except ElementTree.ParseError as error:
        if response.status_code in {401, 403}:
            return {
                "httpStatus": response.status_code,
                "flickrStatus": "fail",
                "errorCategory": "authentication",
            }

        raise RuntimeError(
            f"Flickr returned invalid XML with HTTP {response.status_code}"
        ) from error

    result: dict[str, Any] = {
        "httpStatus": response.status_code,
        "flickrStatus": root.get("stat"),
    }

    if root.get("stat") == "ok":
        flickr_photo_id = root.findtext("photoid")

        if not flickr_photo_id:
            raise RuntimeError("Flickr upload succeeded without returning a Flickr photo ID")

        result["flickrPhotoId"] = flickr_photo_id
        return result

    error_node = root.find("err")

    if error_node is None:
        raise RuntimeError("Flickr returned a failure response without an error element")

    result["errorCode"] = int(error_node.get("code", "-1"))
    result["errorMessage"] = error_node.get("msg", "")
    return result


def authorization_outcome(result: dict[str, Any]) -> str:
    error_code = result.get("errorCode")

    if result.get("errorCategory") == "authentication":
        return "rejected_authentication"
    if error_code == MISSING_PHOTO_ERROR_CODE:
        return "accepted_missing_photo"
    if error_code in AUTHENTICATION_ERROR_CODES:
        return "rejected_authentication"
    if result.get("flickrStatus") == "ok":
        return "accepted_upload_created"
    return "indeterminate"


def run(args: argparse.Namespace) -> tuple[Path, bool]:
    image_path = args.image.resolve(strict=True)

    if image_path.suffix.casefold() != ".png":
        raise RuntimeError(f"Expected a PNG test image, got: {image_path}")

    api_key, api_secret = load_credentials(args.config)
    _, token = require_authorized_token(api_key, api_secret, args.token_cache)
    started_at = datetime.now(UTC)
    stamp = started_at.strftime("%Y%m%d-%H%M%S")
    report_path = args.report_directory.resolve() / f"flickr-signed-upload-probe-{stamp}.json"
    title = f"FGA private signed-upload probe {started_at:%Y-%m-%d %H:%M:%S} UTC"
    metadata = {
        "api_key": api_key,
        "title": title,
        "description": "FGA private signing-boundary probe; safe to delete.",
        "is_public": "0",
        "is_friend": "0",
        "is_family": "0",
        "safety_level": "1",
        "content_type": "1",
        "hidden": "2",
    }
    report: dict[str, Any] = {
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "startedAt": started_at.isoformat(),
        "expectedProfileUrl": EXPECTED_PROFILE_URL,
        "image": {"path": str(image_path), "fileSizeBytes": image_path.stat().st_size},
        "signedMetadataNames": sorted(metadata),
        "status": "running",
    }
    write_report(report_path, report)

    try:
        signed = sign_upload(api_key, api_secret, token.token, token.token_secret, metadata)
        print(f"Uploading privately without Flickr secrets in the sender: {image_path.name}")
        valid_result = send_upload(signed, image_path=image_path)
        report["validUpload"] = valid_result
        write_report(report_path, report)

        if valid_result.get("flickrStatus") != "ok":
            raise RuntimeError(f"Valid split upload failed: {valid_result}")

        replay_result = send_upload(signed, image_path=None)
        replay_outcome = authorization_outcome(replay_result)
        report["replay"] = {"outcome": replay_outcome, "response": replay_result}
        write_report(report_path, report)

        tamper_metadata = dict(metadata)
        tamper_metadata["title"] = f"{title} TAMPERED"
        tamper_signed = sign_upload(api_key, api_secret, token.token, token.token_secret, metadata)
        tamper_result = send_upload(tamper_signed, image_path=None, metadata=tamper_metadata)
        tamper_outcome = authorization_outcome(tamper_result)
        report["metadataTamper"] = {
            "outcome": tamper_outcome,
            "response": tamper_result,
        }

        results_are_conclusive = (
            replay_outcome != "indeterminate" and tamper_outcome != "indeterminate"
        )
        tamper_was_rejected = tamper_outcome == "rejected_authentication"
        report["finishedAt"] = datetime.now(UTC).isoformat()
        report["status"] = (
            "completed" if results_are_conclusive and tamper_was_rejected else "failed"
        )
        write_report(report_path, report)

        print(f"PASS valid upload; private Flickr photo ID: {valid_result['flickrPhotoId']}")
        print(f"Replay authorization outcome: {replay_outcome}")
        print(f"Metadata tamper outcome: {tamper_outcome}")
        return report_path, report["status"] == "completed"
    except Exception as error:
        report["finishedAt"] = datetime.now(UTC).isoformat()
        report["status"] = "failed"
        report["errorType"] = type(error).__name__
        report["error"] = str(error)
        write_report(report_path, report)
        raise


def main() -> int:
    try:
        report_path, passed = run(parse_args())
    except (
        RuntimeError,
        OSError,
        requests.RequestException,
        flickrapi.FlickrError,
    ) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Sanitized local report: {report_path}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
