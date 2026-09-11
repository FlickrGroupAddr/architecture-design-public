"""Create Flickr upload authorization without handling image bytes."""

from __future__ import annotations

from dataclasses import dataclass

import requests
from requests_oauthlib import OAuth1

UPLOAD_URL = "https://up.flickr.com/services/upload/"


@dataclass(frozen=True)
class SignedUpload:
    """Upload material safe to give only to the immediate image sender."""

    url: str
    authorization: str
    metadata: dict[str, str]


def sign_upload(
    api_key: str,
    api_secret: str,
    oauth_token: str,
    oauth_token_secret: str,
    metadata: dict[str, str],
) -> SignedUpload:
    oauth = OAuth1(
        api_key,
        api_secret,
        oauth_token,
        oauth_token_secret,
        signature_type="auth_header",
    )
    prepared = requests.Request("POST", UPLOAD_URL, data=metadata, auth=oauth).prepare()
    authorization = prepared.headers.get("Authorization")

    if not authorization:
        raise RuntimeError("OAuth library did not produce an Authorization header")

    if isinstance(authorization, bytes):
        authorization = authorization.decode("ascii")

    return SignedUpload(UPLOAD_URL, authorization, dict(metadata))
