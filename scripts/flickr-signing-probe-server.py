"""Serve one loopback-only Flickr upload authorization for Lightroom."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import flickrapi
from flickr_support import load_credentials, require_authorized_token
from flickr_upload_signing import sign_upload

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
SIGNING_PATH = "/api/v001/upload-authorizations"
MAX_REQUEST_BYTES = 4096
MAX_PORT = 65535


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the cached Flickr account, listen only on loopback, and "
            "serve exactly one private-upload authorization to Lightroom."
        )
    )
    parser.add_argument("--config", required=True, type=Path, help="ignored Flickr credential file")
    parser.add_argument(
        "--token-cache",
        type=Path,
        default=Path(".secrets/flickr-token-cache"),
        help="ignored directory containing the authorized Flickr token",
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="loopback TCP port")
    return parser.parse_args()


def private_metadata(api_key: str, issued_at: datetime) -> dict[str, str]:
    return {
        "api_key": api_key,
        "title": f"FGA private Lightroom multipart probe {issued_at:%Y-%m-%d %H:%M:%S} UTC",
        "description": "FGA private Lightroom multipart probe; safe to delete.",
        "is_public": "0",
        "is_friend": "0",
        "is_family": "0",
        "safety_level": "1",
        "content_type": "1",
        "hidden": "2",
    }


def handler_type(
    api_key: str,
    api_secret: str,
    oauth_token: str,
    oauth_token_secret: str,
) -> type[BaseHTTPRequestHandler]:
    class SigningHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            del format, args

        def send_json(self, status: HTTPStatus, value: dict[str, Any]) -> None:
            body = json.dumps(value, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            if self.path != SIGNING_PATH:
                self.send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return

            content_length = int(self.headers.get("Content-Length", "0"))

            if content_length > MAX_REQUEST_BYTES:
                self.send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "request_too_large"})
                return

            request_body = self.rfile.read(content_length)

            try:
                request = json.loads(request_body or b"{}")
            except json.JSONDecodeError:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
                return

            if request != {}:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": "unexpected_request_fields"})
                return

            issued_at = datetime.now(UTC)
            metadata = private_metadata(api_key, issued_at)
            signed = sign_upload(
                api_key,
                api_secret,
                oauth_token,
                oauth_token_secret,
                metadata,
            )
            self.send_json(
                HTTPStatus.OK,
                {
                    "schemaVersion": 1,
                    "issuedAt": issued_at.isoformat(),
                    "uploadUrl": signed.url,
                    "authorizationHeader": signed.authorization,
                    "metadata": signed.metadata,
                },
            )

    return SigningHandler


def run(args: argparse.Namespace) -> None:
    if not 1 <= args.port <= MAX_PORT:
        raise RuntimeError(f"Port must be between 1 and {MAX_PORT}: {args.port}")

    api_key, api_secret = load_credentials(args.config)
    _, token = require_authorized_token(api_key, api_secret, args.token_cache)
    server = HTTPServer(
        (DEFAULT_HOST, args.port),
        handler_type(api_key, api_secret, token.token, token.token_secret),
    )

    print(
        f"Ready for one Lightroom signing request at http://{DEFAULT_HOST}:{args.port}{SIGNING_PATH}"
    )
    print("The server is loopback-only and will stop after handling one request.")

    try:
        server.handle_request()
    finally:
        server.server_close()

    print("Signing request handled; server stopped.")


def main() -> int:
    try:
        run(parse_args())
    except (RuntimeError, OSError, flickrapi.FlickrError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
