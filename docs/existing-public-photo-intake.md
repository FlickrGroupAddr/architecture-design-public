# Existing public Flickr photo intake contract

Last updated: 2026-09-05

Status: Accepted authority and wire contract under ADR 0021; ticket #0053's
selector spike passed current Lightroom Classic host acceptance

## Scope and eligibility

The existing-photo path queues add-only group intents for a photo that, at the
time of hosted verification:

- has an exact Flickr photo ID;
- is owned by the Flickr owner NSID configured for the authenticated FGA user;
- is public according to Flickr; and
- is queryable through a documented Flickr API method.

Eligibility does not depend on which uploader created the photo, whether the
FGA LrC plug-in uploaded it, which Flickr album contains it, or whether any
Lightroom Classic catalog or publish service stores its Flickr ID. The FGA LrC
plug-in does not render, upload, replace, delete, move, attach to an album, or
create a Lightroom Classic published-photo record in this path.

This contract does not authorize a Lightroom Classic published-photo record,
Flickr album change, pixel replacement, deletion, or re-upload. The
[non-destructive existing-photo boundary](non-destructive-existing-photo-boundary.md)
separates those records; tickets #0052 through #0058 own the separate disposable
replacement evidence.
[ADR 0038](decisions/0038-keep-existing-photo-intake-queue-only.md) retains this
queue-only catalog boundary after reviewing ticket #0067's disposable-catalog
association evidence.

## Documented source and advisory discovery

The FGA LrC plug-in opens the existing-photo selector with:

```http
GET /api/v001/existing-public-photos?page=1&page_size=100
Authorization: Bearer <FGA installation credential>
```

The FGA API backend authenticates the installation, reads the current linked
Flickr account and revision from the FGA database, and sends a signed
`flickr.people.getPhotos` request using that exact grant with:

```text
user_id=<configured owner NSID>
privacy_filter=1
content_types=0
extras=date_upload,date_taken,media,url_q
page=<validated page>
per_page=<validated page_size>
format=json
nojsoncallback=1
```

Flickr documents `privacy_filter=1` as public photos, `content_types=0` as
photos, conventional page/per-page pagination, a default page size of 100, and
a maximum of 500. The FGA API backend caps `page_size` at 100 for this private
MVP. It never accepts a client-supplied `user_id`, privacy filter, content type,
Flickr OAuth value, or upstream method name.

The FGA API backend publishes a page only after validating the complete Flickr
JSON root and successful status, page metadata, explicit photo array, and every
entry. Every entry must contain one bounded opaque photo ID, the exact expected
owner NSID, `ispublic="1"`, photo media, a bounded title, and interpretable
requested extras. A missing, duplicate, mismatched-owner, nonpublic, malformed,
truncated, or over-budget entry invalidates the whole page. The FGA API backend
returns `503 Service Unavailable` with code
`existing_photo_discovery_unavailable`; it never filters bad entries into a
plausible partial or empty result.

A successful page has this shape:

```json
{
  "schemaVersion": 1,
  "linkedFlickrRevision": 7,
  "observedAt": "2026-08-26T12:34:56.123456Z",
  "page": 1,
  "pageSize": 100,
  "pages": 12,
  "total": 1142,
  "photos": [
    {
      "flickrPhotoId": "opaque-flickr-photo-id",
      "title": "Public photo title",
      "dateUploaded": "1770000000",
      "dateTaken": "2026-02-01 14:30:00",
      "thumbnail": {
        "url": "https://live.staticflickr.com/..._q.jpg",
        "sizeClass": "q"
      }
    }
  ]
}
```

Photo IDs remain strings; no FGA component parses, increments, sorts
numerically, or derives identity from their current spelling. The thumbnail URL
is public display data and is never authority. The FGA API backend does not
proxy, persist, or log thumbnail bytes.

Flickr's page result can change between requests. `page`, `pages`, and `total`
are advisory observations, not a stable snapshot or proof that every public
photo was seen. The FGA LrC plug-in de-duplicates loaded rows by exact photo ID,
labels the observation time, and may request another page. A later page failure
is **Unavailable**, not end-of-list or a successful empty page. The selector may
retain already loaded rows with their original observation label, but selecting
one never bypasses the fresh binding proof below.

Official Flickr sources:

- [`flickr.people.getPhotos`](https://www.flickr.com/services/api/flickr.people.getPhotos.html)
- [`flickr.photos.getInfo`](https://www.flickr.com/services/api/flickr.photos.getInfo.html)
- [Flickr identifier overview](https://www.flickr.com/services/api/misc.overview.html)

## In-Lightroom Classic selection boundary

The FGA LrC plug-in exposes an explicit command named **Add Groups to Existing
Flickr Photo…**. It is separate from Publish and states that it will not upload,
replace, delete, or move the photo. The initial interaction selects one Flickr
photo, obtains the initial fresh hosted binding proof below, then opens the same
binding-scoped fresh membership and group-addition selection used by the
original-publisher path. Immediately before a non-idempotent group handoff, the
FGA LrC plug-in refreshes that proof and uses the returned revision.

The baseline selector stays inside Lightroom Classic and uses documented
`LrDialogs.presentModalDialog` with an `LrView` hierarchy. Each row must remain
recognizable with at least title, upload or capture date, exact public
thumbnail, and a visible shortened/display photo ID whose full opaque value is
available for diagnosis. A successful explicit empty first page says **No
public photos observed**; a failed page says **Public photos unavailable** and
does not enable selection.

The Lightroom Classic SDK documents `LrView.picture` for a static file or
plug-in resource, not a remote URL. Ticket #0053's
[selector spike](research/existing-public-photo-selector-spike.md) implements
the smallest transient current-page cache and a modal-per-page interaction with
deterministic fixtures. Current Lightroom Classic host acceptance passed on
2026-08-26 at 150% Windows and Lightroom Classic UI scaling. If a later
supported host cannot present thumbnails reliably, the selector must return to
design; silently dropping recognizable visual identity is not an accepted
fallback.

Documented `catalog:getPublishServices` data and published-photo remote IDs may
later provide optional labels or shortcuts. They cannot hide an otherwise
eligible Flickr photo, establish ownership or visibility, alter a catalog
record, or become a prerequisite for selection.

Local Adobe sources checked in SDK 15.3:

- `API Reference/modules/LrDialogs.html` for
  `LrDialogs.presentModalDialog`;
- `API Reference/modules/LrView.html` for `viewFactory:picture`; and
- `API Reference/modules/LrCatalog.html` for
  `catalog:getPublishServices`.

## Fresh hosted proof and stable binding

After the photographer selects a discovery row, the FGA LrC plug-in requests a
fresh binding proof before reading membership. It repeats the same safe proof
immediately before a durable group handoff that could create a missing intent:

```http
POST /api/v001/existing-public-photo-bindings
Authorization: Bearer <FGA installation credential>
Content-Type: application/json
```

```json
{
  "schemaVersion": 1,
  "flickrPhotoId": "opaque-flickr-photo-id",
  "expectedLinkedFlickrRevision": 7
}
```

The client-supplied photo ID is only an opaque lookup key. It is never ownership,
visibility, discovery, or authorization evidence. The FGA API backend:

1. authenticates the installation and loads its FGA user;
2. requires the exact current linked-Flickr revision and `linked` state;
3. signs `flickr.photos.getInfo` with the exact current application and OAuth
   grant, passing the photo ID but no client-supplied Flickr `secret`;
4. validates the complete successful result and exact returned photo ID;
5. requires `owner.nsid` to equal the immutable configured owner NSID;
6. requires `visibility.ispublic` to equal the documented public value `"1"`;
   and
7. commits the verified observation and binding revision in one FGA database
   transaction only if the linked revision is still current.

A first proof creates a server-generated opaque `fgaPhotoBindingId`; a later
proof for the same `(FGA user, Flickr photo ID)` reuses that identity and
increments `verificationRevision`. If the same Flickr photo already has an FGA
upload-origin binding, the proof reuses it rather than creating two identities.
The binding retains its first provenance and appends the new existing-photo
verification event.

The FGA database stores only the binding ID, FGA user, exact Flickr photo ID,
first provenance, current link and verification revisions, observed owner NSID,
public observation, observation time, and sanitized events. It does not persist
titles, descriptions, tags, thumbnail URLs/bytes, comments, favorites, album
membership, or raw Flickr responses merely to prove intake.

The first proof returns `201 Created`; a refresh returns `200 OK`:

```json
{
  "schemaVersion": 1,
  "fgaPhotoBindingId": "server-generated-binding-id",
  "sourceKind": "existing_public_flickr_photo",
  "flickrPhotoId": "opaque-flickr-photo-id",
  "linkedFlickrRevision": 7,
  "verificationRevision": 3,
  "verifiedAt": "2026-08-26T12:45:00.123456Z"
}
```

The response is a timestamped observation. Flickr can change owner-visible
state or public visibility immediately afterward; no FGA component claims an
atomic or lifetime guarantee.

## Errors and ambiguity

| Condition | Response and state |
| --- | --- |
| Credential is missing, malformed, unknown, or revoked | Generic `401 invalid_token`; no Flickr call or binding mutation |
| Linked account is not `linked`, or expected revision is stale | `409 flickr_link_changed`; no Flickr call for a known stale request and no binding mutation |
| Flickr returns a complete exact photo owned by another NSID | `403 photo_owner_mismatch`; no binding mutation |
| Flickr returns a complete exact owned photo with `ispublic!="1"` | `422 existing_photo_not_public`; no binding mutation |
| Photo is not found or exact returned ID differs | `422 invalid_existing_photo`; no binding mutation |
| Transport, temporary Flickr result, malformed/incomplete response, or database failure | `503 existing_photo_verification_unavailable` with bounded retry guidance; no new verified revision |
| Link revision changes before commit | `409 flickr_link_changed`; roll back the proof |

An unavailable discovery or verification result is never an empty public
photostream, wrong-owner proof, private-photo proof, or permission to use a
previous verification revision for new intents. The FGA LrC plug-in may safely
retry the same proof request with bounded backoff because it performs only a
read plus a natural-key upsert; it never uploads or mutates Flickr.

## Group-handoff contract

The common group-submission batch evolves before OpenAPI implementation to use
a server binding rather than a client photo ID:

```json
{
  "schemaVersion": 2,
  "photoBinding": {
    "fgaPhotoBindingId": "server-generated-binding-id",
    "expectedVerificationRevision": 3
  },
  "flickrGroupIds": [
    "group-id-1",
    "group-id-2"
  ]
}
```

The FGA API backend derives the Flickr photo ID, FGA user, owner NSID, source
kind, and linked revision exclusively from the binding. It rejects a binding
owned by another installation/user, a changed link revision, or a verification
revision that is not current. The client cannot replace those fields or submit
an alternate photo ID.

For an existing-public-photo binding, every handoff that would create at least
one missing natural-key intent requires a fresh proof call immediately before
the batch and a proof age within the fixed deployment value
`existing_photo_proof_max_age`, selected as 15 seconds by ADR 0033. Expiry
returns `409 existing_photo_reverification_required`; the FGA LrC plug-in
repeats the safe proof and then retries the batch. A fully
idempotent retry whose every pair already exists returns the stored states even
after proof expiry and never creates or resubmits work.

The freshness window limits accidental long-term reuse; it does not make the
Flickr read and later worker operations atomic. Once accepted, intents follow
the same attempt-scoped membership guard, moderation preflight, FIFO,
ambiguity, permanent-block, and courteous-batch rules as upload-origin photos.

The binding and batch are two explicit hosted transactions. If proof succeeds
but batch handoff fails, the FGA LrC plug-in retries only proof when required and
the idempotent batch. It does not render, upload, replace, attach, or mutate a
Lightroom Classic catalog record.

## Required conformance evidence

Before hosted implementation is ready, production-adapter tests must prove at
least:

- discovery always fixes the configured owner, public privacy filter, and photo
  content type regardless of client query input;
- every malformed or mixed discovery page fails as unavailable without partial
  rows;
- page drift and page failure are not presented as a stable complete set;
- catalog bindings are optional hints and never authority;
- arbitrary, wrong-owner, private, missing, and malformed-result photo IDs
  create no verified binding revision;
- successful proof records exact ID, owner, public visibility, link revision,
  observation time, and one stable server binding without photo metadata;
- a link-revision race rolls back proof;
- schema-version-2 group batches contain no client Flickr photo ID and derive
  all authority from the binding;
- stale/expired proof cannot create a missing intent, while a fully idempotent
  retry remains a no-op; and
- no intake path renders, uploads, replaces, deletes, attaches, or writes a
  Lightroom Classic catalog binding.

The architecture repository has no production FGA LrC plug-in selector, FGA API
backend, FGA database, or OpenAPI implementation and therefore claims no
executable pass.
