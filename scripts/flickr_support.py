"""Shared Flickr integration-test support without secret logging."""

# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

import flickrapi

if TYPE_CHECKING:
    from pathlib import Path

EXPECTED_PROFILE_URL = "https://www.flickr.com/photos/terryott/"


def load_credentials(path: Path) -> tuple[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise RuntimeError(f"Credential file not found: {path}") from error

    if text.lstrip().startswith("{"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as error:
            raise RuntimeError(f"Credential file is not valid JSON: {path}") from error
    else:
        data = {}
        labels = {
            "api_key": "api_key",
            "key": "api_key",
            "flickr_api_key": "api_key",
            "api_secret": "api_secret",
            "secret": "api_secret",
            "flickr_api_secret": "api_secret",
        }

        for line in text.splitlines():
            label, separator, value = line.partition(":")

            if not separator:
                continue

            normalized_label = label.strip().casefold().replace(" ", "_")
            target = labels.get(normalized_label)

            if target:
                data[target] = value.strip()

    api_key = str(data.get("api_key", "")).strip()
    api_secret = str(data.get("api_secret", "")).strip()

    if not api_key or not api_secret:
        raise RuntimeError(f"Fill in api_key and api_secret in the ignored file: {path}")

    return api_key, api_secret


def normalized_profile_identity(url: str) -> tuple[str, str]:
    parsed = urlsplit(url)
    return parsed.netloc.casefold(), parsed.path.rstrip("/").casefold()


def require_authorized_token(
    api_key: str,
    api_secret: str,
    token_cache: Path,
) -> tuple[flickrapi.FlickrAPI, Any]:
    flickr = flickrapi.FlickrAPI(
        api_key,
        api_secret,
        format="parsed-json",
        token_cache_location=str(token_cache.resolve()),
        timeout=60,
    )

    if not flickr.token_valid(perms="write"):
        raise RuntimeError("The token cache has no valid Flickr write authorization")

    token = flickr.token_cache.token

    if token is None:
        raise RuntimeError("Flickr token validation succeeded without returning a token")

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

    return flickr, token
