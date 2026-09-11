# ADR 0002: Prefer lossless PNG output

Date: 2026-08-20

Amended: 2026-09-03 to reject concurrent opportunistic 8-bit and 16-bit
rendering and define the evidence boundary for any later explicit 16-bit mode.

Status: Accepted

## Context

The photographer develops high-resolution Canon RAW captures in Lightroom and
wants to avoid JPEG encoding loss in the file retained by Flickr. Flickr
currently accepts PNG, retains the exact uploaded file as the downloadable
original, and limits each photo to 200 MB. Lightroom's SDK permits PNG output.

PNG losslessly represents Lightroom's rendered pixels; it is not a substitute
for retaining the RAW source and Lightroom catalog/develop settings. Flickr
creates JPEG display derivatives, so the main benefit is the downloadable
original.

High-resolution photographic PNG files can be large. A 16-bit full-resolution
render may exceed Flickr's limit depending on content and metadata.

The first Lightroom Classic 15.5 matrix rendered three representative
full-resolution EOS R5 files. All nine 8-bit PNGs were between 51.52 and 78.87
MiB; all nine 16-bit PNGs were between 219.23 and 237.32 MiB. Requested bit
depths, dimensions, and ICC profiles were confirmed independently with
ExifTool. This supports 8-bit sRGB as the provisional default and rules out
16-bit PNG as a generally viable default under Flickr's stated limit.

The photographer is comfortable with an 8-bit/channel final image because the
intended viewing audience overwhelmingly uses displays with no more than
8-bit/channel output. The goal is therefore to avoid JPEG compression loss in
the delivered 8-bit image, not to preserve a 16-bit rendering at any cost.

The measured Lightroom quality-100 JPEG is itself 8 bits/sample, sRGB,
baseline DCT, and YCbCr 4:4:4. The proposed 8-bit sRGB PNG does not reduce
channel precision relative to that baseline and avoids its irreversible DCT
quantization. This fidelity claim applies to the downloadable original;
Flickr's generated display derivatives may still be JPEG.

## Decision

Make full-resolution 8-bit sRGB PNG the preferred FGA still-image output.
Retain JPEG as an explicit, user-controlled fallback. Do not use 16-bit PNG as
an automatic default or fallback for full-resolution EOS R5 images.

The FGA LrC plug-in must preflight the rendered file against Flickr's current
size limit and must not silently convert, resize, or lower quality.

Terry refined the accepted interaction on 2026-08-26. A rendered PNG whose
exact byte size is strictly greater than the configured Flickr byte limit is a
hard failure for that photo before upload authorization. The FGA LrC plug-in
reports the rendered size, limit, and absence of any upload. It does not resize,
convert, or offer an in-flow fallback. JPEG remains available only when the user
separately selects it in the publish settings and starts a new publish action.

The representative Lightroom matrix and private Flickr round-trip are complete.
Flickr reported the tested upload as PNG and returned an Original whose byte
count and SHA2-256 hash exactly matched the local 56,454,128-byte export.

The first usable FGA LrC plug-in keeps its image-format control disabled at
`PNG - 8-bit - sRGB`. A later version may offer `PNG - 16-bit - sRGB` only as an
explicit user choice. That mode renders one 16-bit file and applies the same
hard size preflight; it does not silently produce an 8-bit file when the
16-bit file is too large. Before that option is offered, a private, under-limit
16-bit PNG must complete a Flickr round trip whose downloaded Original has the
same byte count and SHA2-256 hash as the local render.

## Consequences

- The Flickr original avoids JPEG encoding loss.
- Uploads use more local time, network bandwidth, and storage than JPEG.
- The product needs clear size-policy UX and end-to-end format tests.
- Users still need to retain RAW files and catalogs for true source preservation
  and future re-editing.

## Rejected alternatives

### Render 8-bit and 16-bit concurrently and let the file that fits win

Terry proposed this opportunistic dual-render design on 2026-09-03 so the
16-bit PNG could be uploaded whenever it remained within Flickr's configured
size limit, while an already-rendered 8-bit PNG would be available otherwise.
The proposal was reviewed against the Lightroom Classic SDK publish-provider
contract and the completed EOS R5 render matrix.

The conventional recommendation was one explicit output setting and one render
per photo. Concurrent dual rendering was rejected because:

- every sampled full-resolution 16-bit EOS R5 PNG exceeded the limit, so the
  measured workload would incur and discard the second render every time;
- it would add rendering load, temporary storage, cancellation, cleanup, and
  error states to every publication;
- the Lightroom Classic publish-service runtime ordinarily supplies the FGA
  LrC plug-in with one rendition produced from one export-settings table, so a
  second simultaneous rendition would require unusual orchestration outside
  the straightforward publish-provider path; and
- one fixed-looking image-format setting could silently produce different bit
  depths according to image compressibility, violating least surprise and
  making the retained Flickr Original harder to predict.

Sequential automatic 16-bit-to-8-bit fallback was also rejected. It has a
simpler concurrency model but would usually render twice under the measured
workload and would still make the output format data-dependent. Terry accepted
the conventional recommendation and these tradeoffs on 2026-09-03. Future
interest in 16-bit output follows the explicit, single-render, private-probe
boundary above rather than reviving an automatic winner-selection path.
