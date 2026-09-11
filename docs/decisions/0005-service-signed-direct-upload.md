# ADR 0005: Use direct Flickr uploads signed by the FGA API backend

Date: 2026-08-20

Retry boundary clarified: 2026-08-26

Status: Accepted

## Context

Flickr requires OAuth 1.0a request signing with the Flickr application secret
and user's token secret. Shipping those secrets in an MIT-licensed Lightroom
Lua plug-in would not keep them secret. Proxying every representative 50–80 MiB
PNG through the hosted service would add bandwidth, duration, cost, and image-
data exposure.

Flickr excludes the multipart `photo` field from the OAuth signature while
requiring every non-file upload field to be signed. This permits a component
holding the secrets to sign exact metadata without receiving the image bytes.

Python probes showed that a secret-free sender could use such an envelope to
upload successfully. A Lightroom Classic 15.5 probe then rendered a
full-resolution 8-bit sRGB PNG and uploaded it directly through
`LrHttp.postMultipart`. Flickr accepted the upload, and an authenticated API
check reported original format `png` and private visibility.

## Decision

The FGA API backend signs direct Flickr upload requests:

1. The FGA LrC plug-in sends the intended, allowlisted non-file Flickr metadata
   to the FGA API backend over authenticated HTTPS.
2. The FGA API backend generates fresh OAuth material and returns the upload
   URL, exact signed metadata, OAuth authorization header, and a
   server-generated correlation identifier.
3. The FGA LrC plug-in keeps that envelope only in memory, adds the rendered
   `photo` multipart part, and streams the request directly to Flickr through
   `LrHttp.postMultipart`.
4. The FGA LrC plug-in records the returned Flickr photo ID and durably hands
   that Flickr photo ID plus selected Flickr group IDs to the FGA API backend.
5. Once the FGA LrC plug-in invokes `LrHttp.postMultipart`, any timeout,
   connection loss, or other missing definitive Flickr result is ambiguous.
   The documented Lightroom SDK contract does not prove that zero request bytes
   left the Lightroom Classic host networking stack, so the FGA LrC plug-in
   records `upload_outcome_unknown` and does not replay the image POST.

The FGA managed secret store retains the Flickr application secret and OAuth
token secret. The FGA API backend never receives the rendered image.

## Consequences

- The FGA LrC plug-in streams large image bytes directly to Flickr through
  `LrHttp.postMultipart`.
- The signed OAuth header is reusable bearer material during Flickr's accepted
  timestamp window because the image bytes are not signature-bound. The FGA API
  backend must return it with `Cache-Control: no-store`; neither component may
  persist or log it; the FGA LrC plug-in must use it immediately.
- The FGA LrC plug-in must reproduce the signed metadata fields exactly. Any
  metadata change requires a fresh envelope.
- The FGA API backend cannot make the Flickr-facing header truly single-use or
  impose a hard Flickr expiry shorter than Flickr enforces.
- The FGA LrC plug-in needs a local outbox because the Flickr upload and hosted
  intent handoff cannot share one transaction.
- Generic FGA API retry policy does not apply to the direct Flickr image POST.
  A failure proven before `LrHttp.postMultipart` is invoked may start a new
  request with a fresh authorization; after invocation, only the explicit
  reconciliation or deliberate-new-copy paths may make progress.
- Runtime regression tests must preserve the JSON-safe conversion of the OAuth
  header returned by `requests-oauthlib`.

## Alternatives

- **Sign in the FGA LrC plug-in:** rejected as the default because it distributes
  Flickr secrets and adds OAuth/HMAC implementation surface to Lua.
- **Proxy uploads through the FGA API backend:** retained as a fallback, but
  rejected as the default because it needlessly routes large private image data
  through that hosted component.
- **Require a separate Flickr application per installation:** viable for a
  developer-only tool but rejected as unnecessary for the private MVP and poor
  future user experience.
