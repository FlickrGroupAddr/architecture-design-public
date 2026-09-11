"""Regression tests for the Flickr upload-signing boundary."""

from __future__ import annotations

import json
import unittest

from scripts.flickr_upload_signing import sign_upload


class SignUploadTests(unittest.TestCase):
    def test_authorization_header_is_json_serializable_text(self) -> None:
        signed = sign_upload(
            "test-api-key",
            "test-api-secret",
            "test-oauth-token",
            "test-oauth-token-secret",
            {"api_key": "test-api-key", "title": "test"},
        )

        self.assertIsInstance(signed.authorization, str)
        json.dumps({"authorizationHeader": signed.authorization})


if __name__ == "__main__":
    unittest.main()
