# Flickr PNG round-trip results

Date: 2026-08-20

The first private Flickr API round-trip passed end to end. OAuth 1.0a
authorization granted `write` permission to the authorized public test profile.
Before upload, the harness verified that profile URL to protect against changing
the wrong Flickr account.

The harness privately uploaded the smallest representative 8-bit sRGB PNG,
which was 56,454,128 bytes. Flickr reported `originalformat="png"`. The
authenticated Original download was also 56,454,128 bytes and had the same
SHA2-256 hash as the local Lightroom export. Upload, inspection, and download
took 48 seconds.

The local report is ignored and contains the private Flickr photo ID and hashes. No
credential, OAuth token, private photo identifier, original URL, or hash was
committed. The test photo was left private for deliberate cleanup because the
harness used least-privilege `write` permission rather than requesting
`delete`.

This result closes the principal uncertainty behind ADR 0002. The decision is
accepted: FGA will prefer full-resolution 8-bit sRGB PNG, preflight its size,
and never silently change format, dimensions, or quality.
