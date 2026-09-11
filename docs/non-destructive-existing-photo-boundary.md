# Non-destructive existing-photo boundary

Last updated: 2026-09-05

Status: Accepted preservation boundary under ADRs 0022 and 0038; no existing-
photo migration, catalog association, album move, pixel replacement, deletion,
or re-upload is accepted

## Purpose

An existing public Flickr photo can participate in add-only group queueing
without becoming an FGA-published photo. That distinction protects a public
photo's established identity and social history while keeping Lightroom Classic
publish records and Flickr album membership truthful.

This contract separates five records that can refer to the same photograph but
are not interchangeable:

| Record | Authority and scope | What it does not prove |
| --- | --- | --- |
| Lightroom Classic catalog photo | One catalog's editable source/develop object | Flickr existence, Flickr owner, public visibility, album membership, or upload provenance |
| Lightroom Classic published-photo record | Publication data for one catalog photo in one published collection and publish-service connection; its remote ID/URL are values recorded by that provider | That another provider owns the record, that the remote resource still exists, or that any Flickr mutation is safe |
| Flickr photo | The remote resource named by the exact opaque Flickr photo ID | A Lightroom Classic catalog correlation, a particular uploader, or membership in any album |
| Flickr photoset/album membership | A mutable relationship between one Flickr photo ID and one photoset ID | Ownership of the photo's pixels, public identity, group membership, or a Lightroom Classic publish record |
| FGA photo binding | Hosted proof and stable FGA identity for one `(FGA user, Flickr photo ID)` | A Lightroom Classic published-photo record, Flickr album membership, pixel equivalence, or permission to replace/delete |

The exact Flickr photo ID is FGA's preservation key for the public resource.
Views, favorites, comments, photopage navigation, metadata, group contexts, and
album contexts are observable properties or relationships around that resource;
this architecture does not claim that Flickr guarantees all of them across replacement. It
therefore preserves the original photo ID and treats replacement evidence as a
separate prerequisite rather than guessing from an unchanged response ID.

## Accepted queue-only behavior

The existing-public-photo intake path performs only these actions:

1. The FGA LrC plug-in presents advisory public-photo discovery and explicit
   selection.
2. The FGA API backend freshly proves the exact Flickr photo ID, configured
   owner NSID, public visibility, and linked-account revision.
3. The FGA API backend creates or refreshes the common FGA photo binding.
4. The FGA LrC plug-in reads current Flickr group membership and submits
   add-only group intents through that binding.

This path creates no Lightroom Classic published-photo record and makes no
Flickr album, photo, pixel, metadata, or deletion write. A missing catalog
correlation never makes an otherwise eligible public Flickr photo unavailable.
Optional catalog evidence can label a row but remains a read-only hint.

## Documented Lightroom Classic boundary

The SDK 15.3 API Reference documents that:

- `LrPublishedPhoto` represents publishing information for a photo that is part
  of a published collection; its remote ID and URL are provider-recorded
  publication data.
- `LrPublishedCollection:addPhotoByRemoteId(photo, remoteID, remoteUrl,
  published)` can add a catalog photo and remote fields to one non-smart
  published collection, or replace those fields if that photo is already in the
  collection.
- `LrPublishedCollection:addPublishedPhotos` adds a set of publication-data
  objects to a collection, while `removePhotos` removes local membership.
- `LrPublishedCollection:setParent` rejects a parent from another publish
  service or even another connection.
- `LrPublishedPhoto:setRemoteId`, `setRemoteUrl`, and `setEditedFlag` mutate
  catalog publication state inside a catalog write gate.
- `LrExportRendition:recordPublishedPhotoId` is for publishing and marks that
  rendition successfully published.

These APIs prove that a plug-in can create or change catalog publication data;
they do not make that data a Flickr migration. In particular,
`addPhotoByRemoteId` would create an FGA-owned publication association. It
would not transfer Adobe's Flickr plug-in record, transfer a Flickr album, or
prove that a local catalog photo produced the remote pixels.

The FGA LrC plug-in therefore does not call any of those catalog-mutating APIs
from existing-photo group intake. It does not modify a Flickr plug-in record,
copy its `LrPublishedPhoto`, clear its remote ID/URL, change its edited flag, or
remove its catalog membership. Direct catalog-database access is prohibited.

Ticket #0067 used a disposable catalog to determine the exact visible, restart,
modified/republish, removal, callback, and Undo behavior of a catalog-only
`addPhotoByRemoteId` association. The [host-probe
report](research/catalog-only-existing-photo-association-spike.md) records the
passing evidence.
[ADR 0038](decisions/0038-keep-existing-photo-intake-queue-only.md) reviews that
evidence and keeps the association out of product scope because queue-only
intake already meets the customer requirement without duplicate provider state.

The deterministic public-safe fixture admitted for this spike, its exact
SHA2-256 digest, and the one-upload mutation boundary are recorded in
[Photography test-data handling](operations/photography-data-handling.md).
Creating the local fixture does not itself create a Flickr resource or mutate a
Lightroom Classic catalog.

## Documented Flickr boundary

Flickr documents these operations as separate mutations:

- `flickr.photosets.addPhoto` adds an existing owned photo ID to a photoset and
  reports “Photo already in set” separately.
- `flickr.photosets.removePhoto` removes that photo/photoset relationship.
- `flickr.photosets.create` creates a new photoset and requires an owned
  `primary_photo_id`.
- the binary replace endpoint accepts a `photo_id` and returns the ID of the
  photo being replaced; it does not promise preservation of engagement,
  contexts, metadata, URLs, old pixels, or rollback.

Album membership is therefore a mutable relation, not the public photo
identity. Adding the photo to another album is not a move; removing it from the
old album is a separate write. The existing-photo path performs neither.
Ticket #0060 owns album behavior for photos originally published through the
FGA LrC plug-in. It must not silently broaden that contract to imported photos.

## Operation decision matrix

| Proposed action | Current decision | Reason |
| --- | --- | --- |
| Create/refresh an FGA hosted binding for a verified existing public photo | Allowed | Read plus hosted proof state; no Lightroom Classic catalog or Flickr mutation |
| Use documented catalog records as optional selector labels | Allowed, read-only | Convenience evidence is not remote authority |
| Add the existing photo to group pools through the accepted queue | Allowed | This is the explicit add-only product job and retains all fail-polite safeguards |
| Create an FGA published-photo record with `addPhotoByRemoteId` | Not accepted; ADR 0038 keeps the feature absent | Ticket #0067 proved reversible current-host behavior, but the operation creates duplicate provider state and a surprising republish/removal lifecycle without an unmet customer requirement |
| Copy or modify a Flickr plug-in `LrPublishedPhoto` record | Prohibited | Provider-owned catalog state is not an FGA migration surface |
| Reparent a collection across publish services/connections | Prohibited | The documented SDK rejects this and it would conflate provider ownership |
| Attach an existing photo to an FGA Flickr album | Not implied or accepted by intake | Separate remote write and product meaning; #0060 is limited to original FGA publication unless later expanded |
| Remove the photo from its existing Flickr album | Prohibited | Destructive membership mutation with no queueing requirement |
| Replace the photo's pixels in place | Prohibited pending #0052 through #0058 | An unchanged photo ID alone does not prove preservation or rollback |
| Upload a new copy and call it migration | Prohibited | A new Flickr photo ID is a distinct public resource and abandons existing engagement |
| Delete the Flickr photo | Prohibited | Destroys the preservation target and is unnecessary for add-only queueing |

## Reconsideration boundary for catalog-only association

ADR 0038 retains the queue-only path. A later proposal may
reconsider a reversible FGA catalog association only after identifying a
concrete customer requirement that queue-only intake cannot meet. At minimum,
that proposal must:

- require an explicit per-photo owner action and show that no Flickr upload,
  replacement, album write, group write, or deletion occurs;
- obtain a fresh current FGA photo-binding proof before recording the exact
  remote ID;
- leave every source publish-service record and collection membership
  unchanged;
- record provenance `catalog_association_only`, not `published_by_fga` or
  `migrated`;
- make modified/republish and delete/remove callbacks unable to replace,
  re-upload, delete, or detach the Flickr photo while replacement remains
  prohibited;
- use removal of only the new FGA catalog association as its rollback;
- reconcile restart or ambiguous local commit through documented catalog reads;
  and
- prohibit automatic or bulk association until single-photo behavior is proven
  and separately accepted.

If the proposal cannot establish both the unmet requirement and those conditions
through documented SDK APIs and clear Lightroom Classic state, the feature
remains absent.

## Replacement and destructive experimentation

Tickets #0052 through #0058 own a disposable public replacement experiment,
social/context preservation checks, Lightroom Classic state, ambiguity,
backup, and rollback. No production catalog, historical photo, private photo,
or engagement-bearing photo may be used to answer those questions. A live
replacement result cannot retroactively authorize association or bulk work;
its evidence must be reviewed in a later ADR.

Ticket #0056 found that an external Flickr pixel replacement leaves the Flickr
plug-in's provider-owned catalog record under **Published Photos** with the old
thumbnail and no modified or republish state, including after a normal
Lightroom Classic host restart. The published-photo UI exposed no supported
pull, refresh, or reassociation action. An FGA hosted replacement therefore
cannot assume that the Flickr plug-in will discover or represent the remote
pixel change. This persistent catalog mismatch strengthens the prohibition; it
does not authorize direct catalog manipulation or an automatic republish.

On 2026-08-26 Terry accepted the conventional recommendation to defer
historical-photo pixel upgrades. Existing historical Flickr photos remain
unchanged; current PNG publication applies only to new photos published through
the FGA LrC plug-in. Ticket #0059 returned to Backlog because the owner is
deliberately withholding that workflow, not because an external condition
blocks it. Reconsideration requires new controlled evidence and another
explicit owner decision.

No FGA component may use delete-and-re-upload as a fallback for unavailable
replacement, absent Pro entitlement, ambiguous delivery, catalog mismatch, or
failed association. “Leave unchanged” is the safe terminal result.

## Required evidence

Before any reconsidered operation beyond queue-only intake is
implementation-ready, tests must prove:

- each persisted identifier is typed and scoped so catalog photo, published
  record, publish-service connection, Flickr photo, Flickr album, and FGA
  binding IDs cannot be substituted for one another;
- selector hints and catalog remote IDs cannot bypass fresh hosted proof;
- queue-only intake causes no catalog or Flickr mutation other than the later
  explicitly selected group-add path;
- every documented field and relationship on source publish-service records
  remains unchanged by any future catalog-only association attempt;
- removal/republish callbacks cannot invoke Flickr mutation for an imported
  association while replacement and album migration are prohibited; and
- every failure and restart converges through documented reads without delete,
  replacement, re-upload, old-album removal, or direct catalog-database access.

This architecture repository has no production FGA LrC plug-in migration
implementation and claims no executable pass.

## Sources

Local Adobe SDK 15.3 primary references:

- `API Reference/modules/LrPublishedCollection.html`
- `API Reference/modules/LrPublishedPhoto.html`
- `API Reference/modules/LrExportRendition.html`

Official Flickr references:

- [`flickr.photos.getInfo`](https://www.flickr.com/services/api/flickr.photos.getInfo.html)
- [`flickr.photosets.addPhoto`](https://www.flickr.com/services/api/flickr.photosets.addPhoto.html)
- [`flickr.photosets.removePhoto`](https://www.flickr.com/services/api/flickr.photosets.removePhoto.html)
- [`flickr.photosets.create`](https://www.flickr.com/services/api/flickr.photosets.create.html)
- [Flickr replace API](https://www.flickr.com/services/api/replace.api.html)
