# Flickr direct-upload signing boundary

Verified: 2026-08-20

Last reconciled: 2026-08-26

Status: Completed validation evidence; the selected boundary is recorded by
[ADR 0005](../decisions/0005-service-signed-direct-upload.md) and projected by
the current [plug-in/service contract](../plugin-service-contract.md)

Authority: Research evidence, not an independent architecture decision

## Question

Can the FGA managed secret store keep Flickr secrets in the hosted environment
while the FGA LrC plug-in sends a large rendered image directly to Flickr?

Routing every 50–80 MiB representative PNG through the FGA API backend would
increase hosted bandwidth, request duration, cost, and image-data exposure.
Signing in the FGA LrC plug-in would avoid that transfer but would require OAuth
secrets and an HMAC with SHA1-160 implementation in the distributed plug-in.

## Flickr contract

Flickr's upload specification requires every non-file POST parameter to be
included in the OAuth signature and explicitly excludes the binary `photo`
parameter. The upload is then sent as multipart form data to:

```text
https://up.flickr.com/services/upload/
```

This permits a signature service to bind the OAuth authorization to the upload
metadata without receiving the image bytes.

Official sources:

- [Flickr upload API](https://www.flickr.com/services/api/upload.api.html)
- [Flickr OAuth documentation](https://www.flickr.com/services/api/auth.oauth.html)

## Lightroom capabilities

The Lightroom Classic 15.3 SDK provides both required client primitives:

- `LrHttp.postMultipart` accepts arbitrary request headers and streams a MIME
  part directly from `filePath`. The Lightroom Classic host's `LrHttp`
  implementation calculates the multipart content length and reports upload
  progress.
- `LrPasswords` stores encrypted strings using operating-system services and
  scopes them by plug-in ID. It is suitable for the revocable FGA installation
  credential.

The documented `LrDigest.HMAC` support does not include the algorithm Flickr
requires. Local Flickr signing would therefore require another reviewed
dependency in addition to storing the Flickr consumer and token secrets on the
laptop.

The SDK also exposes no documented secure-random source or general-purpose UUID
generator for plug-ins. Existing Lightroom UUIDs identify catalog objects, and
machine- or installation-keyed identifiers are stable rather than random.
`LrPasswords` protects a value after it has been created; it does not generate
one. Lua `math.random`, timestamps, clocks, and stable identifiers are not
acceptable sources for authentication material.

Local SDK references:

- `API Reference/modules/LrHttp.html`
- `API Reference/modules/LrPasswords.html`
- `API Reference/modules/LrDigest.html`

## Mature implementation evidence

The pinned `flickrapi` 2.4.0 package already implements a split upload:

1. It prepares a metadata-only URL-encoded request with `requests-oauthlib`
   2.0.0.
2. It captures the resulting OAuth `Authorization` header.
3. It creates a separate multipart request containing the same metadata and the
   photo stream.
4. It sends that multipart request with the previously generated header.

The successful FGA PNG round trip used this path. A separate FGA probe then
generated the header in a signer that held the Flickr secrets and used it in a
sender that received only the header, exact metadata, upload URL, and image
path. Flickr accepted that upload. The subsequent Lightroom Classic probe
rendered a full-resolution PNG and uploaded it successfully with
`LrHttp.postMultipart`, proving that the Lightroom Classic host's `LrHttp`
implementation reproduces the required multipart fields without receiving the
Flickr secrets.

Installed implementation reference:

- `.venv/Lib/site-packages/flickrapi/auth.py`, `do_upload`

## Validated boundary

1. The FGA LrC plug-in authenticates to the FGA API backend and requests upload
   authorization for an exact allowlisted set of Flickr metadata fields.
2. The FGA API backend uses the current exact-version Flickr credential and a
   mature OAuth library to return the fixed upload URL, authorization header,
   exact signed metadata fields, FGA upload authorization ID, and issue time.
   It does not claim a hard expiry that Flickr does not enforce.
3. The FGA LrC plug-in sends those fields plus the rendered file directly to
   Flickr using `LrHttp.postMultipart`.
4. Flickr returns the Flickr photo ID to the plug-in.
5. The FGA LrC plug-in obtains a verified hosted photo binding, records the
   remote ID through the Lightroom SDK, and durably hands any selected group
   intents to the FGA API backend.

The FGA API backend never receives the rendered image. The FGA LrC plug-in
never receives the Flickr consumer secret or token secret.

## Entropy ownership

FGA hosted components require cryptographic entropy, but the FGA LrC plug-in
does not produce it. The appropriate hosted component owns generation of every
security-sensitive random value using its runtime or operating system's secure
generator.

| Value | Generator | FGA LrC plug-in responsibility |
| --- | --- | --- |
| FGA installation credential | FGA administrative control plane | Store with `LrPasswords` |
| Administrative session, CSRF token, and OIDC/Flickr transaction state | FGA API backend | None; the FGA LrC plug-in never receives them |
| Flickr OAuth nonce and timestamp | FGA API backend OAuth library | Forward only in the short-lived signed request |
| Upload-attempt and correlation identifiers | FGA API backend | Persist and echo for reconciliation |
| Flickr photo ID | Flickr | Record through the Lightroom SDK as the catalog remote ID and send to the FGA API backend |
| Lightroom photo UUID | Lightroom Classic catalog | Use only as stable, non-secret identity |

The pinned `oauthlib` 3.3.1 implementation imports `randbits` from Python's
`secrets` module and combines 64 random bits with the current timestamp for its
OAuth nonce. FGA installation credentials require a longer server-generated
secret, provisionally at least 256 bits.

OAuth 1.0 defines a nonce as a randomly generated value that must be unique for
the same timestamp and credential combination. Its security guidance requires
shared secrets to be generated by a cryptographically secure random number
generator. FGA keeps both responsibilities out of the Lua process.

Specification reference:

- [OAuth 1.0 nonce and timestamp](https://www.rfc-editor.org/rfc/rfc5849.html#section-3.3)
- [OAuth 1.0 entropy of secrets](https://www.rfc-editor.org/rfc/rfc5849.html#section-4.9)

## Validation results

On 2026-08-20, the Python probe exercised the first three cases against Flickr
using a 56,454,128-byte private PNG:

1. A separately generated upload header and secret-free sender successfully
   created a private Flickr photo.
2. Reusing the identical header and metadata reached Flickr successfully; the
   request failed only with Flickr's “No photo specified” status (code `2`)
   because the probe deliberately omitted the `photo` part. Flickr therefore
   accepted the reused nonce during the observed timestamp window.
3. Changing the signed title while retaining a freshly signed header produced
   HTTP 401, confirming that Flickr binds the non-file metadata to the
   signature.

The completed sanitized report remains under ignored `artifacts/`; Flickr
credentials, OAuth material, and the private Flickr photo ID are not committed.

The Lightroom split-upload validation returned a Flickr photo ID. A subsequent
authenticated API check reported original format `png` and private visibility.
The private Flickr photo ID remains outside Git.

The replay result is security-significant. A signed upload header is reusable
bearer material until Flickr's timestamp acceptance window closes. Because the
binary `photo` part is intentionally excluded from Flickr's signature, the
header binds metadata but not image bytes. The FGA API backend cannot impose a
shorter hard expiry at Flickr or make the header truly single-use. It must
return the header only over HTTPS, instruct the FGA LrC plug-in to use it
immediately, exclude it from logs, and never persist it in Lightroom preferences
or the Lightroom Classic catalog.

## Alternatives retained

- **Local signing:** viable for a private installation because `LrPasswords`
  can protect local secrets, but it adds cryptographic and OAuth code to the Lua
  plug-in and exposes the Flickr secrets to that installation.
- **Service-proxied upload:** simplest authorization boundary, but needlessly
  transfers large image files through the FGA API backend and may conflict with
  serverless body-size and execution limits.

The service-signed direct upload is selected. Local signing and service-proxied
upload remain historical alternatives, not preauthorized fallbacks. A change in
Flickr or the Lightroom Classic host's `LrHttp` behavior would reopen the
architecture decision and its security, privacy, cost, and dependency review.
