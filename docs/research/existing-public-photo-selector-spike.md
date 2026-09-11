# Existing public photo selector spike

Last updated: 2026-08-26

Status: implementation, offline validation, and current Lightroom Classic host
acceptance complete

## Result

The smallest conventional selector is one documented
`LrDialogs.presentModalDialog` per hosted discovery page. Each row is a bound
radio button beside a local `LrView.picture`, title, capture date, upload date,
and exact opaque Flickr photo ID. Documented `LrDialogs.stopModalWithResult`
lets Previous and Next close the current modal and reconstruct it from another
complete page. No custom list widget, browser, catalog binding, undocumented
interface, or persistent cache is needed.

The development-only **Test Existing Public Photo Selector** command in
`FGA Diagnostics.lrdevplugin` implements that interaction with six generated
fixtures across two pages. The command copies only the displayed page's three
fixtures to an opaque per-run temporary directory, removes that page after the
modal closes, and registers whole-run cleanup with the Lightroom Classic
function context. A copy failure makes the complete page **Public photos
unavailable** and enables no selection. The probe never uses Flickr or the
Lightroom Classic catalog.

Offline Lua and fixture checks establish source validity, deterministic fixture
bytes, and the absence of undocumented SDK names. They do not establish actual
layout, clipping, keyboard behavior, high-DPI rendering, modal navigation, or
cleanup in the current Lightroom Classic host.

## Production thumbnail boundary

The production FGA LrC plug-in will keep the same page-loader seam but replace
the fixture copier with a bounded transient downloader:

1. Accept only a completely validated discovery page from the FGA API backend.
   Its owner, public visibility, media type, page bounds, and `url_q` fields are
   advisory presentation data, never selection authority.
2. Create one opaque per-dialog directory beneath Lightroom Classic's documented
   temporary path. Derive neither directories nor filenames from Flickr IDs,
   titles, URLs, or other remote text.
3. Fetch only the current page's `https` thumbnail URLs with documented
   `LrHttp.get`. Apply a fixed timeout, maximum response-byte count, accepted
   image media types, and image-signature validation before writing an opaque
   filename.
4. Publish no row until every entry and required thumbnail on that page passes.
   A missing, oversized, malformed, non-image, redirected-to-disallowed-origin,
   or failed thumbnail makes the complete page **Public photos unavailable**;
   it is not an empty page and never silently removes visual identity.
5. Remove the preceding page before presenting the next or previous page, and
   remove the entire per-dialog directory through function-context cleanup.
   Cache cleanup is best effort for availability but emits a sanitized local
   diagnostic if it fails; filenames and messages contain no Flickr ID or title.
6. Submit only the exact selected opaque photo ID to the fresh hosted
   `flickr.photos.getInfo` binding proof. A thumbnail, catalog hint, title, or
   discovery observation never proves ownership or public visibility.

The FGA API backend should retain Flickr's validated `url_q` host allowlist and
redirect policy so the FGA LrC plug-in does not become a general URL fetcher.
The eventual implementation must select concrete byte, timeout, media-type,
redirect, and page-count limits alongside the hosted HTTP contract; this spike
does not invent values without runtime measurements.

## Host acceptance

Host acceptance passed on 2026-08-26 with FGA Diagnostics plug-in 0.3.0.5 in
Lightroom Classic 15.5, build `202607291506-b8869fa7`, with Camera Raw 18.5 on
Windows 11 Pro 25H2, build 26200.9168. Windows display scaling and the separate
Lightroom Classic UI scaling were both 150%.

Both pages displayed three distinct, undistorted thumbnails with legible
titles, dates, and full fixture IDs. Previous, Next, and Choose Photo used the
expected enabled states. Selecting fixture photo 1 returned its exact fixture
ID. Cancellation succeeded, and the persistent cache root contained no
per-run directory afterward. No clipping, overlap, or other layout defect was
observed.

The accepted procedure was:

In the latest supported Lightroom Classic release on Windows:

1. load or reload `lightroom/FGA Diagnostics.lrdevplugin`;
2. choose **Library → Plug-in Extras → Test Existing Public Photo Selector**;
3. confirm page 1 shows three distinct, undistorted thumbnails with legible
   title, dates, and full ID, with **Previous** disabled;
4. confirm **Choose Photo** is disabled until a row is selected;
5. choose **Next**, confirm page 2 replaces page 1 and **Next** is disabled;
6. choose **Previous**, select a different page-1 row, and choose
   **Choose Photo**;
7. confirm the result reports the exact selected fixture ID; and
8. cancel a second run, then confirm no run directory remains beneath
   `%TEMP%\fga-existing-photo-selector-probe` after the dialogs close.

Record only the Lightroom Classic version, Windows version, display scale,
pass/fail per step, and sanitized layout observations. Do not capture a catalog,
photo, filename, path, or other photography data. A failure returns ticket
#0053 to design; thumbnails are not optional.

Local Adobe sources checked in SDK 15.3:

- `API Reference/modules/LrDialogs.html` for
  `presentModalDialog` and `stopModalWithResult`;
- `API Reference/modules/LrView.html` for `radio_button`, `picture`,
  `push_button`, and `scrolled_view`;
- `API Reference/modules/LrFileUtils.html` for `copy`, `delete`, and
  `createAllDirectories`; and
- `API Reference/modules/LrPathUtils.html` for `getStandardFilePath`.
