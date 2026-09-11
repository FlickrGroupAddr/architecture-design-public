# Album-scoped publish contract

Last updated: 2026-09-11

Status: Accepted architecture contract under ADRs 0025, 0026, 0028, and 0029;
executable implementation evidence remains outstanding

## Product invariant

Every user-created ordinary FGA published collection is presented as an
**Album** and maps one-to-one to one Flickr album. Selecting that local Album
selects the target Flickr album for every photo published from it. Every such
photo has a durable obligation to belong to that exact album. Upload and album
attachment are separate operations: they need not be atomic or ordered across
photos, but each photo must reach verified membership or a truthful
owner-visible repair state.

The Flickr photoset ID is the remote album identity. The FGA LrC plug-in, FGA
API backend, FGA album worker, and FGA database each treat it as an opaque
string. A title, URL, local collection name, first photo, primary-photo role,
ordering position, or current membership is not album identity. The URL is
navigation data only and may use Flickr's legacy `/sets/` or current `/albums/`
presentation without changing the binding.

The existing-public-photo group-intake command does not participate in this
contract. It creates no Lightroom Classic published collection and performs no
Flickr album write.

## Ordinary albums only

The FGA LrC plug-in supports ordinary Lightroom Classic published collections
only. It labels them **Album**, exposes **Create Album…**, and does not expose
**Create Smart Album…**, smart-filter settings, or automatic membership
reconciliation. This is a product-scope boundary, not an MVP deferral.

Terry's album membership is deliberate: he adds culling candidates, removes
non-survivors, edits, and explicitly publishes the photos he chooses. A smart
collection would make local membership change when metadata, date, location,
or another rule changes. That would require new departure, unpublish, and
remote-membership semantics that conflict with the current non-destructive
local-removal boundary and solve no identified owner workflow.

ADR 0028 records this decision. Any future support requires a new
owner decision and architecture record that defines dynamic departure and
reconciliation before an implementation exposes smart-album creation.

## No default or remote-album picker

The FGA LrC plug-in does not implement the documented optional
`getCollectionBehaviorInfo` callback that asks Lightroom Classic to create a
built-in default collection. The supported path starts when Terry creates or
selects an ordinary Album. If a future supported Lightroom Classic version
nevertheless supplies a collection whose documented `isDefaultCollection` is
true, the plug-in must stop before rendering or uploading and show **Create or
select an Album to publish**. It must not turn that special collection into an
implicit Flickr album or photostream target.

The normal creation dialog creates a new local Album; it does not browse for or
adopt an arbitrary existing Flickr album. The only remote-album selection path
is the narrow ambiguous-create repair in the album-write reconciliation
contract, where Terry chooses among freshly verified candidates produced by the
same guarded creation attempt. Titles and URLs never authorize adoption.

Published collection sets are local organization only. They have no Flickr
identity and reparenting an Album does not change its target.

## Lightroom Classic records

The FGA LrC plug-in uses only documented Lightroom Classic SDK state:

- `titleForPublishedCollection` and its standalone form display **Album**;
- **Create Album…** creates an ordinary `LrPublishedCollection` locally;
- collection settings store schema version, local lifecycle, and the non-secret
  hosted `fgaAlbumBindingId` after one exists;
- `LrPublishedCollection.localIdentifier` supplies the collection ID that is
  unique within the catalog;
- a server-generated `fgaPublishServiceId` stored with the configured publish
  service distinguishes the owning FGA service;
- `recordRemoteCollectionId`/`recordRemoteCollectionUrl` persist the Flickr
  photoset ID and navigation URL during a publish session; and
- `setRemoteId`/`setRemoteUrl` repair the same fields later inside documented
  catalog write access.

The stable local-to-hosted key is `(FGA user, fgaPublishServiceId,
localCollectionIdentifier)`. It is non-secret idempotency data. No FGA LrC
plug-in random generator, catalog path, collection title, or Flickr URL is
needed. A copied/restored catalog retains the same logical key; two concurrently
used copies compete through hosted revisions rather than create another Flickr
album silently.

At local creation, the collection settings contain only:

```json
{
  "schemaVersion": 1,
  "albumLifecycle": "local_unbound"
}
```

The remote ID and URL remain absent. The FGA LrC plug-in makes no Flickr call,
requires no placeholder photo, and lets the owner add, cull, edit, and remove
local candidates before any publication.

## Hosted album binding

The FGA database owns one `album_bindings` row per stable local-to-hosted key.
It retains:

- server-generated `fgaAlbumBindingId`, FGA user, publish-service ID, and local
  collection identifier;
- exact linked-Flickr revision and immutable Flickr owner NSID;
- desired title and title revision;
- nullable opaque Flickr photoset ID and navigation URL;
- first-photo FGA binding ID and derived exact Flickr photo ID;
- lifecycle, materialization, and local-catalog-sync revisions;
- create/attachment dispatch and result evidence defined by the
  [album-write reconciliation contract](album-write-reconciliation.md); and
- append-only sanitized events.

The FGA database never treats a local collection title as unique. It permits
two albums with the same title and refuses a second Flickr photoset ID for one
binding. Database guards must reject an ordinary runtime attempt to rewrite a
committed photoset ID to a different value. The private native enforcement
boundary follows [ADR 0051](decisions/0051-trust-private-storage-runtime-with-guarded-writes.md);
the immutable binding behavior is unchanged.

## First-photo materialization

Flickr's documented `flickr.photosets.create` requires a real
`primary_photo_id`. The following path is therefore the only ordinary initial
materialization:

1. The Lightroom Classic publish-service runtime gives the FGA LrC plug-in one
   or more renditions for an ordinary local album. The plug-in reads its
   documented publish-service ID, local collection identifier, collection name,
   settings, and any recorded remote ID.
2. Each new photo follows the normal render, direct Flickr upload, catalog
   remote-photo-ID write, and hosted exact-photo binding proof. An ambiguous
   upload creates no album operation until ADR 0012 deliberately resolves one
   exact Flickr photo.
3. The first photo in this local album that obtains a committed FGA photo
   binding becomes a candidate primary. “First” means the first candidate
   committed by the FGA database for this album binding; Lightroom Classic
   selection, rendition, upload, and response order carry no guarantee.
4. The FGA LrC plug-in idempotently creates or retrieves the hosted album
   binding using the stable local-to-hosted key, desired title snapshot, current
   linked revision, and candidate FGA photo binding. The FGA API backend derives
   the Flickr owner and photo ID from hosted records; the client cannot supply
   an authoritative owner, photoset ID, or alternate Flickr photo ID.
5. In one FGA database transaction, the FGA API backend creates the binding in
   `materialization_pending` or returns the existing exact binding. It fixes the
   first-photo binding before any Flickr create dispatch. Later photos cannot
   replace that candidate while create is pending or ambiguous.
6. The FGA album worker calls `flickr.photosets.create` with the desired title
   and that exact owned Flickr photo as `primary_photo_id` under the album-write
   contract's durable dispatch rules. It never uploads or chooses a placeholder, default image,
   previous album photo, unrelated public photo, or synthetic resource.
7. A complete successful Flickr response supplies the opaque photoset ID and
   URL. The FGA album worker validates the whole result and commits them once.
   Because creation makes the primary photo a member, it creates no redundant
   `flickr.photosets.addPhoto` call for that first pair.
8. A fresh documented Flickr read must verify the exact album and first-photo
   membership before the corresponding obligation becomes
   `membership_verified`. A response ID alone establishes binding evidence but
   does not silently assert the read-after-write postcondition. The
   [album-write reconciliation contract](album-write-reconciliation.md) governs
   missing, ambiguous, conflicting, and retryable outcomes.
9. The FGA LrC plug-in reads the committed binding and records the exact remote
   ID and URL. During the still-active publish callback it uses
   `recordRemoteCollectionId` and `recordRemoteCollectionUrl`; after that
   callback it uses `setRemoteId` and `setRemoteUrl` inside catalog write access.
10. The plug-in then stores the `fgaAlbumBindingId` and matching binding revision
    in collection settings. If either catalog write fails, it retains
    `album_catalog_sync_pending` and retries only the local write from the hosted
    binding. It never creates another Flickr album.

The first photo can already be marked published in Lightroom Classic before
album materialization completes, because the Flickr upload itself succeeded.
The FGA LrC plug-in must simultaneously show **Published — album attachment
pending** or the applicable repair state; Lightroom's native published section
does not prove the album obligation.

## Multiple-photo first publish

When one callback publishes several new photos, every photo proceeds
independently through upload and hosted photo proof. The first database-committed
candidate owns materialization. Every other successfully bound photo receives
an attachment obligation for the same `fgaAlbumBindingId`; those obligations
wait for the photoset ID and then use `flickr.photosets.addPhoto` under the
album-write reconciliation contract.

A failed or ambiguous candidate upload cannot reserve the album. A committed
photo binding can. Once photoset creation dispatch starts, a later faster photo
cannot replace the candidate merely to improve latency. Cross-photo order and
Flickr album order remain unspecified.

## Per-photo attachment obligation

When an exact hosted photo binding is committed for a materialized or pending
Album, the FGA API backend atomically upserts one natural-key obligation for
`(fgaAlbumBindingId, fgaPhotoBindingId)`. Repeating the same handoff returns the
same obligation. A different Album is a distinct explicit obligation; no
component infers album movement or removes the earlier membership.

The FGA album worker derives both Flickr IDs and the owner from their hosted
bindings. It never accepts those authority fields from the FGA LrC plug-in.
The worker satisfies the primary pair through fresh post-create membership
proof and every later pair through the read/add/read sequence in the
[album-write reconciliation contract](album-write-reconciliation.md). A
missing or ambiguous post-upload handoff retries only the idempotent hosted
binding or attachment operation; it never repeats the Flickr image POST.

Verified external removal while the local photo remains published is drift
from the desired membership and may be repaired through the same guarded add
path. Once the local relationship is removed, the non-destructive
[album lifecycle contract](album-lifecycle-contract.md) retires that desired
membership without sending a Flickr removal or undoing a previously committed
remote relation.

## Local/hosted consistency

On every publish and explicit album-status refresh, the FGA LrC plug-in compares
the collection settings, Lightroom remote ID/URL, and hosted album binding:

| Observation | Behavior |
| --- | --- |
| No hosted binding and no Lightroom remote ID | Ordinary `local_unbound`; first bound photo may create the binding |
| Hosted binding is unmaterialized and Lightroom remote ID is absent | Resume the existing materialization; never create another binding |
| Hosted photoset ID exists and Lightroom remote ID is absent | Repair only the catalog ID/URL and collection settings |
| Hosted and Lightroom IDs match | Normal; refresh URL as navigation data when needed |
| Lightroom ID exists but no hosted binding | **Album binding needs attention**; never adopt or mutate the remote album from client state alone |
| Hosted and Lightroom IDs differ | **Album identity conflict**; stop album writes and use the explicit reconciliation repair |

The FGA database remains authoritative for album identity and obligations. The
Lightroom Classic catalog remains authoritative for local collection membership
and native publish state. Flickr remains authoritative for current remote album
and photo membership. No one record substitutes for the other two.

Creation is never blindly replayed. An ambiguous create remains owner-visible
until Terry selects one freshly verified Flickr album or leaves it unresolved.
Later photo attachments reconcile automatically from strict fresh membership:
present satisfies the obligation, verified absence permits the non-duplicating
add path, and unavailable evidence sends no write. ADR 0026 records
that deliberate split.

The [album lifecycle contract](album-lifecycle-contract.md) makes explicit local
rename a revisioned remote-title intent, leaves reparenting local-only, and
preserves Flickr albums, photos, and memberships after local removal.
ADR 0027 records that a Lightroom Classic callback is not implicit destructive
Flickr authorization.

ADR 0029 records the complete one-Album/one-photoset binding and
per-photo attachment obligation.

## Required implementation evidence

Before this path is ready, executable tests must prove at least:

- the provider creates no default collection, and a host-supplied default is
  rejected before render or upload;
- Create Album persists only `local_unbound` settings and makes no Flickr call;
- no ordinary creation path browses, adopts, or binds an existing remote album
  by title or URL;
- zero photos, unrendered candidates, failed uploads, and ambiguous uploads
  create no album-binding candidate;
- the first database-committed photo binding wins under concurrent callbacks;
- retries with the same local-to-hosted key return one binding, while changed
  authority or identity fields conflict;
- only the hosted derived owner/photo ID reaches `photosets.create`;
- no placeholder or unrelated photo path exists;
- a successful create commits one immutable opaque photoset ID and does not send
  `addPhoto` for the primary pair;
- later photos create obligations against the same binding without relying on
  photo order;
- repeated photo handoff upserts one obligation for the same Album/photo pair;
- failed local remote-ID/URL/settings writes retry only catalog mutation; and
- mismatched or orphaned Lightroom remote IDs send no Flickr write.

The architecture repository has no production FGA LrC publish provider, FGA
album worker, album-binding endpoint, or FGA database schema and therefore
claims no executable pass.

## SDK and Flickr sources

Local Adobe SDK 15.3 documentation:

- optional `publishServiceProvider.getCollectionBehaviorInfo` and its default
  collection creation behavior;
- `LrPublishedCollection.localIdentifier`, `getRemoteId`, `getRemoteUrl`,
  `setCollectionSettings`, `setRemoteId`, and `setRemoteUrl`;
- `LrExportContext.publishedCollection` and `publishedCollectionInfo`; and
- `LrExportSession.recordRemoteCollectionId` and
  `recordRemoteCollectionUrl`.

Official Flickr contracts:

- [`flickr.photosets.create`](https://www.flickr.com/services/api/flickr.photosets.create.html)
- [`flickr.photosets.addPhoto`](https://www.flickr.com/services/api/flickr.photosets.addPhoto.html)
- [`flickr.photosets.getInfo`](https://www.flickr.com/services/api/flickr.photosets.getInfo.html)
- [`flickr.photosets.getPhotos`](https://www.flickr.com/services/api/flickr.photosets.getPhotos.html)
