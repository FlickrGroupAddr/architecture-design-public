# ADR 0022: Separate public photo identity from catalog and album records

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31

## Context

An existing public Flickr photo may also have a Lightroom Classic catalog
photo, one or more provider-scoped published-photo records, and membership in
one or more Flickr albums. Those records can share an opaque Flickr photo ID
without representing the same state or authority.

The Lightroom Classic SDK documents ways to create or mutate publication data,
including `LrPublishedCollection:addPhotoByRemoteId`, but calls that record an
association inside a particular published collection. Flickr separately
documents photo identity, photoset creation, photoset add/remove, replacement,
and deletion boundaries. Neither system documents a cross-provider migration
that transfers all local state, album relationships, pixels, and public social
history atomically.

Existing-photo group queueing does not require such a migration. Treating it as
one would add catalog and Flickr writes to a read/proof/add-only workflow and
would make failure recovery destructive.

## Decision

1. Treat the Lightroom Classic catalog photo, provider/collection-scoped
   `LrPublishedPhoto`, Flickr photo ID, Flickr photoset membership, and FGA
   photo binding as separate typed records.
2. Preserve the exact existing Flickr photo ID as FGA's public-resource key.
   Do not infer that replacement preserves views, favorites, comments,
   metadata, contexts, URLs, or rollback merely because Flickr returns the same
   ID.
3. Existing-public-photo group intake creates or refreshes only the FGA hosted
   binding and selected group intents. It creates no Lightroom Classic
   published-photo record and performs no Flickr album, pixel, metadata, or
   deletion write.
4. Catalog records from Adobe's Flickr plug-in or another provider are read-
   only optional selector hints. The FGA LrC plug-in does not copy, modify,
   reparent, remove, or delete those records.
5. `LrPublishedCollection:addPhotoByRemoteId` is a possible catalog-only FGA
   association, not migration. Ticket #0067 proved its visible and callback
   behavior in a disposable catalog. ADR 0038 keeps it outside product
   scope because queue-only intake already meets the requirement without a
   duplicate provider record and its republish/removal lifecycle.
6. Existing-photo intake does not attach the photo to an FGA Flickr album or
   remove it from an existing album. `flickr.photosets.addPhoto` and
   `flickr.photosets.removePhoto` are separate remote writes, not identity
   transfer. Ticket #0060 remains scoped to album obligations for original FGA
   publication unless a later decision expands it.
7. Pixel replacement remains prohibited pending tickets #0052 through #0058.
   Delete-and-re-upload is never a migration fallback because it creates a
   distinct Flickr photo and risks established public state.
8. No production catalog, historical photo, private photo, or engagement-
   bearing photo may be used for migration/replacement experimentation.

## Consequences

- Queueing an existing public photo remains useful without requiring its local
  catalog source or touching the Flickr plug-in's records.
- The word “migration” does not conceal several independent mutations. Any
  future proposal names each catalog association, album change, pixel
  replacement, or deletion separately with its own evidence and recovery.
- Ticket #0067 proved that a local association can be removed and undone without
  claiming the Flickr photo was rolled back. ADR 0038 records why that
  technical capability does not become product behavior.
- An unavailable or ambiguous migration-like operation leaves the established
  photo and source records unchanged.

## Rejected alternatives

- **Automatically import every discovered Flickr photo into an FGA published
  collection:** rejected because discovery does not prove a local photo
  correlation and group queueing does not need catalog mutation.
- **Copy an Adobe Flickr plug-in publication record:** rejected because it is
  provider-scoped state and the SDK documents no ownership transfer.
- **Move the photo to an FGA album:** rejected because photoset add and remove
  are separate writes and old-album removal has no queueing requirement.
- **Replace or re-upload during association:** rejected because pixel change is
  independent, replacement preservation is unproven, and re-upload creates a
  new public identity.
- **Use direct catalog database writes:** rejected because the Lightroom schema
  is undocumented and bypasses the supported publish-service runtime.

## Detailed contract

The [non-destructive existing-photo boundary](../non-destructive-existing-photo-boundary.md)
defines the entity model, operation matrix, future association preconditions,
experiment limits, and required evidence.
