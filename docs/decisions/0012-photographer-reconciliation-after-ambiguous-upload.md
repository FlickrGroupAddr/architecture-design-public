# ADR 0012: Require photographer reconciliation after an ambiguous upload

Date: 2026-08-25

Status: Accepted by Terry on 2026-08-26

## Context

The FGA LrC plug-in uploads a rendered photo directly to Flickr. Flickr's
documented synchronous upload response contains the new Flickr photo ID, but
the response can be lost after image bytes have left the Lightroom Classic
host networking stack. In that case, the plug-in cannot distinguish “Flickr
created the photo and the response was lost” from “Flickr did not create the
photo.” Replaying the upload can create a second photo.

Flickr documents authenticated owner-photo queries with upload-date bounds and
useful display fields. Those reads can find plausible recent photos, but Flickr
does not document them as a read-after-write idempotency or exact-upload
identity mechanism. Search delay, another upload in the same interval, changed
metadata, or an externally deleted photo can all make automatic inference
wrong. Absence from a result is not proof that the ambiguous upload failed.

Flickr's upload documentation also mentions optional duplicate checking in
the description of error code `9`. It does not document the `dedup_check`
argument or the meanings of its values in the upload argument contract, nor
does it define the match, indexing, retention, or ordering semantics needed to
identify one ambiguous attempt safely. A reported duplicate could also predate
the FGA upload attempt.

ADR 0011 proposes the normal successful-upload binding and hosted ownership-
proof boundary. This decision defines the exceptional path when the FGA LrC
plug-in never received a Flickr photo ID.

Official Flickr contracts:

- [Uploading Photos](https://www.flickr.com/services/api/upload.api.html)
- [`flickr.people.getPhotos`](https://www.flickr.com/services/api/flickr.people.getPhotos.html)
- [`flickr.photos.search`](https://www.flickr.com/services/api/flickr.photos.search.html)
- [`flickr.photos.getInfo`](https://www.flickr.com/services/api/flickr.photos.getInfo.html)

## Decision

### Preserve uncertainty and stop automatic writes

Before dispatch, the FGA LrC plug-in **MUST** already have a durable local
recovery record containing the Lightroom photo UUID, the FGA upload
authorization ID, the target published collection, and the snapshotted group
selections. If image bytes may have left the Lightroom Classic host networking
stack but no complete, definitive Flickr result was durably recorded, the
plug-in **MUST** move that record to `upload_outcome_unknown`.

That state **MUST NOT** contain an invented Flickr photo ID. The FGA LrC
plug-in **MUST NOT** automatically replay the upload, create or attach a Flickr
album, attach a photo to an album, create group-submission intents, or mark the
photo published in the Lightroom Classic catalog. Other photos continue
independently under ADR 0009.

The FGA LrC plug-in **MUST** expose the state as **Upload outcome unknown —
action required**. It may remain unresolved indefinitely without background
replay.

### Present candidates without inferring identity

The FGA LrC plug-in **MAY** request an advisory candidate resource:

```http
GET /api/v001/upload-authorizations/{fgaUploadAuthorizationId}/ambiguity-candidates
Authorization: Bearer <FGA installation credential>
```

The FGA API backend **MUST** authenticate the installation, require ownership
of the path's upload authorization, and use the linked Flickr account to query
documented owner-photo results beginning slightly before the authorization's
server-recorded issue time. It may paginate through later uploads and return
only the minimum display information needed to distinguish candidates: Flickr
photo ID, title, upload time, thumbnail URL, and photopage URL. The response
**MUST** use `Cache-Control: private, no-store`.

The FGA LrC plug-in **MUST** label the results as candidates, never matches. It
**MUST NOT** choose a candidate automatically, rank one as the upload, treat a
single result as conclusive, or treat an empty or failed query as proof that no
photo was created. The photographer may instead paste a Flickr photo ID or
photopage URL when the intended photo is absent from the candidate page.

Before accepting a candidate, the FGA LrC plug-in **MUST** show its Flickr
photo ID, thumbnail, title, and upload time and require an explicit per-photo
**Use this Flickr photo** confirmation. This is a photographer assertion of
identity, not a byte-for-byte proof supplied by Flickr.

### Bind one explicitly selected photo

After confirmation, the FGA LrC plug-in **MUST** durably store the selected
Flickr photo ID in `ambiguity_resolution_pending` state before making this
idempotent request:

```http
PUT /api/v001/upload-authorizations/{fgaUploadAuthorizationId}/ambiguity-resolution
Authorization: Bearer <FGA installation credential>
Content-Type: application/json
```

```json
{
  "schemaVersion": 1,
  "flickrPhotoId": "photographer-selected-flickr-photo-id"
}
```

For an unbound authorization, the FGA API backend **MUST** apply ADR 0011's
installation-ownership, exact-photo, linked-owner, conditional-binding, and
transaction rules. In the same FGA database transaction, it **MUST** record
that the binding provenance is `photographer_reconciled_ambiguous_upload`.
The successful response **MUST NOT** claim that Flickr proved the selected
photo contains the ambiguous request's exact bytes.

The first committed response is `201 Created`; the same authorization/photo
tuple returns `200 OK`; a different photo ID after a binding commits returns
`409 Conflict` and never changes the binding. A failed or inconclusive Flickr
read commits no binding. The FGA LrC plug-in may safely retry only the same
pending tuple after a timeout or retryable failure.

After the FGA LrC plug-in receives the committed binding, it **MUST** durably
record the acknowledgement before calling the documented Lightroom SDK's
`recordPublishedPhotoId`. A crash or catalog-write failure after hosted commit
moves only the local catalog write to `reconciled_catalog_write_pending`; it
does not authorize another upload or a different binding. Once the catalog
remote ID is recorded, the local state is `hosted_photo_verified` and normal
album and group obligations may proceed.

If ADR 0011 and this decision are both accepted, a Lightroom Classic catalog
remote ID means either that Flickr returned the ID as the successful upload
result or that the photographer selected the ID through this reconciled path.
The FGA LrC plug-in's durable provenance distinguishes those cases. Neither
meaning by itself claims album attachment, group completion, or continued
existence on Flickr.

### Permit only a deliberate new upload

The photographer **MAY** choose **Publish a new copy** instead of selecting an
existing photo. The FGA LrC plug-in **MUST** warn that the ambiguous attempt may
already exist on Flickr and that continuing can create a duplicate. It **MUST**
require a per-photo confirmation, terminally retain the original recovery
record as `abandoned_possible_flickr_photo`, and create a new recovery record
and fresh upload authorization. It **MUST NOT** reuse the original upload
authorization or call the action a retry.

A later-discovered original remains photographer-managed Flickr content. No
FGA component automatically deletes it, rewrites the new catalog binding, or
submits it to albums or groups. Choosing **Leave unresolved** performs no
Flickr write and leaves `upload_outcome_unknown` intact.

## Consequences

- A lost upload response becomes visible owner work instead of an unsafe
  automatic replay.
- Candidate retrieval reduces manual Flickr spelunking while preserving the
  truth that only the photographer can identify the intended result from the
  documented evidence available.
- Hosted ownership verification prevents binding another user's photo, but it
  deliberately does not overclaim byte identity.
- The ambiguity-resolution resource is idempotent after client timeouts and
  preserves immutable provenance separately from the normal upload-result
  path.
- An explicit new upload can leave an orphaned first photo. The warning and
  retained terminal record make that accepted risk visible; no API can erase
  the underlying uncertainty.
- The FGA LrC plug-in needs a small repair UI and two additional local states,
  while the FGA API backend needs one read-only candidate resource and one
  idempotent resolution resource.

## Alternatives considered

- **Automatically replay the upload:** rejected because the first request may
  already have created a photo.
- **Treat no recent-photo result as proof of failure:** rejected because the
  documented query is not a consistency or idempotency guarantee.
- **Automatically select the only recent result:** rejected because another
  upload can occupy the same interval and metadata is not exact identity.
- **Depend on Flickr duplicate checking:** rejected as the safety boundary
  because the official upload contract does not define the argument and match
  semantics needed for this use, and an identical photo could predate the
  ambiguous attempt.
- **Add a hidden FGA machine tag as an idempotency marker:** rejected because it
  exposes implementation metadata on the photographer's Flickr photo, depends
  on search visibility and later cleanup, and invents surprising distributed
  coordination where an explicit rare repair is simpler.
- **Proxy image bytes through the FGA API backend:** rejected by ADR 0005 for
  the default path and unnecessary for this minimum repair workflow.
