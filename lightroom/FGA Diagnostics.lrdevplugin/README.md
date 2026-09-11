# FGA Diagnostics Lightroom plug-in

This development-only Lightroom Classic plug-in contains focused experiments
for PNG rendering, direct Flickr upload, existing-public-photo selection, and a
disposable-catalog association. It is not the eventual Flickr publish provider.

## Install or reload

1. In Lightroom Classic, open **File → Plug-in Manager**.
2. Choose **Add** and select this `FGA Diagnostics.lrdevplugin` directory.
3. If it is already installed, choose **Reload Plug-in** after pulling or
   editing its source.

## PNG matrix

1. Select one or more fully edited photos in Library or Develop.
2. Choose **Library → Plug-in Extras → Run PNG Test Matrix on Selected Photos**.
3. Choose an output parent directory and confirm the potentially large render.

Each run creates a timestamped directory containing one subdirectory per
variant and a `manifest.json` with source paths, render settings, sizes,
durations, and errors. This command never uploads, changes, or deletes a photo.

## Direct Flickr upload probe

This diagnostic is locked to one explicitly configured catalog record. Copy
`DirectUpload.example.json` to the ignored `DirectUpload.local.json` in this
plug-in directory. Fill in the exact catalog photo UUID, source filename and
public Flickr page only after independently verifying that page without Flickr
authentication. The example values are intentionally unusable. Missing or
malformed configuration fails before reading a catalog photo or making a
network request. Never commit the local file or copy its values into reports.

Start the one-request loopback signer described in
`docs/operations/flickr-roundtrip.md`, select the configured photo, and choose
**Library → Plug-in Extras → Test Direct Flickr Upload from Public Photo**.
The confirmation remains mandatory; this snapshot authorizes no live upload.

Lightroom renders a temporary full-resolution 8-bit sRGB PNG, obtains an
in-memory signing envelope, and streams the PNG directly to Flickr. The probe
creates one private, search-hidden Flickr photo. It deletes only the exact
temporary render during context cleanup; it never changes or deletes the
catalog source. The signed header is neither logged nor persisted.

JSON encoding uses the vendored, unmodified dkjson 2.11 library. Its upstream
provenance, checksum, and license are recorded in `vendor/README.md`.

Run `uv run --frozen python scripts/analyze_png_exports.py --run-directory <path>`
afterward to add SHA2-256 hashes and image metadata to an analysis report.

## Existing public photo selector

Choose **Library → Plug-in Extras → Test Existing Public Photo Selector**. The
fixture-only command presents two pages of recognizable thumbnails, titles,
dates, and exact opaque photo IDs. Previous and Next reconstruct the modal with
only the current page's thumbnails in a temporary cache. Choosing a row reports
its exact fixture ID.

This command makes no network request, reads no catalog photo or publication
record, and performs no upload, replacement, group operation, or catalog write.
It exists only to validate the current Lightroom Classic host's documented
`LrDialogs` and `LrView` presentation behavior. See
[`docs/research/existing-public-photo-selector-spike.md`](../../docs/research/existing-public-photo-selector-spike.md)
for the production cache boundary and acceptance steps.

## Ticket #0067 catalog-only association probe

This live host probe is complete, and its one-public-upload authorization is
consumed. The numbered sequence below records the completed procedure; do not
repeat the upload or create a replacement fixture without a new explicit
authorization that satisfies the repository's private-by-default test boundary.

Run this probe only in its purpose-built disposable Lightroom Classic catalog.
The `FGA Catalog Association Probe` development provider has no networking
implementation: it blocks publish and republish renditions before rendering,
and its deletion callbacks acknowledge only local catalog cleanup.

Every probe command, callback, cancellation, and caught failure replaces one
complete sanitized JSON document at
`C:\Temp\FGA-catalog-association-0067.json`. The report includes the phase,
catalog path, fixture path, provider-scoped publication records, saved-source
comparison, and callback counters. It contains no Flickr credentials or
authorization material. Codex monitors this exact path during the live run.

1. Reload the plug-in, then choose **Library → Plug-in Extras → 0067: Prepare
   Disposable Catalog Fixture**. Confirm the displayed disposable catalog path.
2. Adobe's Flickr publish service published the selected fixture exactly once
   as a public, Safe photo with no Flickr album or group membership. That upload
   was recorded and later deleted; this step must not be repeated under ticket
   #0067's consumed authorization.
3. In Publishing Manager, create exactly one **FGA Catalog Association Probe**
   service. Its built-in **Catalog Association Only** collection requires no
   connection settings and cannot publish image bytes.
4. Select the fixture and choose **0067: Create Catalog-Only Association**. The
   command copies the Adobe Flickr record's remote ID and URL into a second,
   provider-scoped record with documented `addPhotoByRemoteId`. It refuses the
   operation unless exactly one source record and one probe service exist, and
   it verifies that the source record did not change across the write.
5. Choose **0067: Inspect Catalog Associations**, restart Lightroom Classic,
   and inspect again. Change one harmless local metadata field, observe the
   modified/republish state, click Publish in the probe collection, and inspect
   the recorded blocked-callback count. No render or network request occurs.
6. Restore the harmless metadata edit. Choose **0067: Remove Catalog-Only
   Association**, click Publish in the probe collection to exercise the local
   removal callback, and inspect again. Confirm the Adobe Flickr record remains
   and the public fixture is still available at the recorded photopage URL.
7. Repeat the association once, use Lightroom Classic's Undo command, and
   inspect. Recreate it, restart the Lightroom Classic host, inspect, remove it
   again, and perform the final Flickr observation required by
   [`docs/operations/photography-data-handling.md`](../../docs/operations/photography-data-handling.md).

Do not run these commands in the production catalog. Do not add a fixture to an
album or group, publish or replace another Flickr photo under ticket #0067, or
infer that this local association transfers Adobe's Flickr publish record.
