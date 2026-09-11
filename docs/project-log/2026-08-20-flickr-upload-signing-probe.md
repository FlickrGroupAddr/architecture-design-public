# Flickr direct-upload signing probe

Date: 2026-08-20

FGA tested whether a hosted signer can authorize a direct Flickr upload while
the component streaming the image has no Flickr consumer secret or OAuth token
secret. The probe used Python 3.14 in the uv-managed environment and the pinned
`flickrapi`, `requests-oauthlib`, and `requests-toolbelt` packages.

The signer prepared Flickr's exact non-file metadata and returned only the
upload URL, OAuth `Authorization` header, and metadata. A separate sender used
that material to stream the 56,454,128-byte PNG directly to Flickr. The private
upload succeeded.

Two no-image follow-up requests tested the boundary without creating more
Flickr photos:

- Reusing the original signed header and exact metadata produced Flickr's “No
  photo specified” status (code `2`). This shows Flickr accepted the replayed
  OAuth nonce during the observed timestamp window.
- Changing the signed title produced HTTP 401. This shows Flickr rejected
  metadata that did not match the signature.

The result proves that the hosted service can keep Flickr secrets out of the
upload sender. It also proves that the returned header is reusable bearer
material for Flickr's timestamp window. The signature binds the metadata but,
by Flickr's protocol design, does not bind the photo bytes. The plug-in must use
the header immediately and must never persist or log it.

The completed sanitized report is ignored under `artifacts/`. Flickr
credentials, OAuth material, and the private Flickr photo ID remain outside
Git. The same boundary was then exercised through Lightroom's
`LrHttp.postMultipart`.

## Lightroom multipart result

The follow-up boundary test passed in Lightroom Classic 15.5. Lightroom
rendered the independently verified public fixture as a full-resolution 8-bit
sRGB PNG, requested an in-memory authorization envelope from the loopback-only
signer, and streamed the multipart request directly to Flickr with
`LrHttp.postMultipart`. Flickr accepted the upload and returned a Flickr photo
ID. A subsequent authenticated, read-only API check reported original format
`png`; visibility was private, not friend-visible, and not family-visible. The
private test photo's ID is deliberately not recorded in Git.

The runtime probe exposed and resolved three integration details:

- Lightroom's toolkit `require` loader accepts top-level script names but did
  not resolve dkjson beneath a subdirectory. The unmodified single-file module
  is therefore installed at the toolkit root and loaded as `require("dkjson")`.
- Lightroom photo UUIDs identify catalog records, not image files globally.
  The safety guard must target the verified record in the catalog/root being
  exercised.
- `requests-oauthlib` returned the prepared OAuth authorization header as
  bytes. The signing boundary now converts that value to ASCII text before
  JSON serialization, with a regression test covering the behavior.

This closes the direct-upload architecture question: the eventual Lightroom
publish provider can render PNG and upload the bytes straight to Flickr while
the hosted service retains the Flickr consumer secret and OAuth token secret.
