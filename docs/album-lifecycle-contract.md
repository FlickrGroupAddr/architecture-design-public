# Flickr album rename, hierarchy, and local-removal contract

Last updated: 2026-09-05

Status: Accepted lifecycle semantics for ordinary FGA albums under ADR 0027;
Terry accepted the governing decision on 2026-08-31

## Authority split

An FGA published collection name is the local title Terry deliberately edits in
Lightroom Classic. A Flickr photoset title is independent remote metadata.
Renaming the local collection creates an explicit intent to change the bound
Flickr title; it does not change album identity.

Lightroom Classic collection-set hierarchy is local organization. Flickr
photosets have no corresponding parent relationship in this contract. Moving an
FGA album within the same publish service changes no Flickr field.

Removing an FGA published collection or photo from the Lightroom Classic
catalog is a local action. It does not imply deletion of the Flickr photoset,
Flickr photo, or album membership. Remote deletion/removal is unavailable in the
FGA LrC plug-in; Terry uses Flickr's own UI when he deliberately wants that
destructive change.

## Rename behavior

### Unmaterialized local album

Renaming a collection in `local_unbound` changes only the Lightroom Classic
collection name and desired title in collection settings. No hosted resource or
Flickr call is required. The first-photo materialization later snapshots the
current name.

If a hosted binding exists but create dispatch has not started, the FGA LrC
plug-in updates the binding's desired title with an expected binding/title
revision. The first create uses the latest committed title. A rename racing the
create marker becomes a later metadata intent; it never changes a request after
dispatch.

### Materialized album

The documented `renamePublishedCollection` callback creates or replaces one
desired-title row on the hosted binding. The FGA database retains:

- album-binding ID and immutable opaque Flickr photoset ID;
- prior observed title, desired title, and monotonically increasing title
  revision;
- linked-Flickr and OAuth-grant revisions;
- dispatch marker/count, result class, and observation times; and
- append-only sanitized events.

The desired title is bounded, valid Unicode presentation text. It is neither an
identity nor an idempotency key. A newer local rename supersedes an undispatched
older revision. Once an older revision's Flickr dispatch marker exists, recovery
must observe it before the newer revision can dispatch.

The FGA album worker freshly verifies the exact bound photoset and configured
owner, commits a durable dispatch marker, then sends one documented
`flickr.photosets.editMeta` POST with only `photoset_id` and required `title`.
It omits the optional `description`, so a description maintained in Flickr is
not overwritten with empty or stale text.

A complete `flickr.photosets.getInfo` read supplies reconciliation:

| Observed title after dispatch | Result |
| --- | --- |
| Exact desired title | Commit `title_synced` for that revision |
| Exact title from a newer local revision | Close the older attempt as superseded and satisfy the newer desired state by observation |
| Exact pre-dispatch title | A bounded same-revision retry is safe; setting the same title is idempotent |
| Any third title | Commit `title_conflict`; send no automatic overwrite |
| Unavailable, malformed, wrong-owner, or wrong-photoset result | Keep `title_reconciliation_pending`; send no write |

A complete successful POST response is followed by the same read; the empty
success body is not the final title assertion. Transport loss or process failure
uses the table instead of blind generic retry. The retry budget and shared
Flickr fault gates remain bounded. Exhaustion becomes **Album title sync needs
attention**, never infinite background churn.

For a third-title conflict, the FGA LrC plug-in shows the local and Flickr titles
and observation time. Terry may explicitly rename the Lightroom album again to
create a new desired revision or leave the values different. No FGA component
silently changes the Lightroom collection name from remote text or overwrites a
third Flickr value.

## Reparent behavior

The documented `reparentPublishedCollection` callback may move an ordinary FGA
album among supported local collection sets inside the same FGA publish service.
The FGA LrC plug-in records the local hierarchy through Lightroom Classic and
returns success without a hosted or Flickr write. The album-binding ID, photoset
ID, title revision, navigation URL, photo obligations, and remote membership do
not change.

A move across publish services/connections is outside this contract and the
documented SDK restricts cross-service parenting. Export/import, catalog copy,
or another mechanism cannot transfer a hosted album binding merely by copying a
title or Flickr ID.

## Remove a local photo from an album

For an unpublished local candidate, removal has no remote effect. For a photo
already uploaded from this FGA album, local removal:

- removes or archives only the provider-scoped Lightroom Classic publication
  relationship as the documented host lifecycle requires;
- never calls `flickr.photos.delete`, `flickr.photosets.removePhoto`,
  `flickr.photosets.removePhotos`, or the replacement endpoint;
- never clears the common hosted photo binding or album-binding history; and
- never treats the removal as evidence that Flickr membership is absent.

An album-membership obligation already dispatched or required by the original
publication continues to verified membership or a truthful repair state. This
preserves the standing invariant that every photo published from the album is
eventually attached. Terry can remove the remote membership separately in
Flickr after the obligation is complete; the FGA album worker does not fight a
later external removal once the local publication relationship is archived.

## Remove the local album

The `shouldDeletePublishedCollection` boundary must tell Terry exactly what
will happen:

> Remove this album from Lightroom Classic only? The Flickr album and its photos
> will remain. Any already-published photo attachments still pending will
> finish or remain visible for repair. FGA components will not delete or empty the Flickr
> album.

Cancel leaves all state unchanged. Confirming local removal uses Lightroom
Classic's documented deletion lifecycle and sends no Flickr write.

The FGA API backend archives the hosted binding as
`local_collection_removed_remote_preserved`. It retains the immutable photoset
ID, title history, membership obligations, ambiguous attempts, and events so a
later collection cannot accidentally adopt or recreate the same identity.

- Undispatched title changes are canceled because there is no longer a local
  desired title.
- A title write already dispatched is reconciled read-only and never retried.
- Already accepted album-membership obligations continue; no new photo
  obligation can be added from the removed collection.
- An ambiguous create cannot be forgotten. Before local removal, the dialog
  requires Terry to acknowledge that its candidate repair moves to the FGA
  administrative control plane; it still sends no create or delete.
- A `local_unbound` collection with no hosted binding disappears locally with
  no retained remote state.

The FGA LrC plug-in provides no **Delete Flickr album**, **Remove photos from
Flickr album**, **Delete Flickr photos**, or implicit cleanup option. Adding any
such product behavior requires a new owner requirement, explicit destructive
confirmation and ambiguity contract, and a later ADR. Flickr's documented
delete/remove endpoints existing does not make a local action authorization.

## External drift

Fresh status reads can observe:

- a changed Flickr title after a previously completed rename;
- a missing/deleted bound photoset;
- photos added to or removed from the photoset outside FGA; or
- a changed navigation URL.

A remote title change is displayed as drift and does not automatically create a
new local or remote write. A missing bound photoset becomes
`remote_album_missing_needs_attention`; no FGA component creates a replacement
photoset, clears the opaque ID, or rebinds by title. Membership reads remain
Flickr-authoritative. The URL can be refreshed as navigation data only after
exact bound-ID/owner proof.

## Required conformance evidence

Executable tests must prove at least:

- unbound rename makes no network request and first create uses the latest
  committed title;
- bound rename calls only `photosets.editMeta` with exact ID/title and omits
  description;
- every rename dispatch has a durable marker and every success/ambiguity uses a
  strict `getInfo` read;
- desired, prior, third, missing, wrong-owner, malformed, and unavailable title
  observations take only their specified branches;
- a third title cannot be overwritten without a new explicit local rename;
- reparenting changes no hosted identity, title, URL, obligation, or Flickr
  state;
- unpublished photo removal sends no write, and published-photo removal sends
  no Flickr delete/remove/replace method;
- local album removal sends no Flickr write, archives a materialized binding,
  retains unresolved attempts/obligations, and cancels only undispatched title
  work;
- no local deletion path clears or reuses an opaque photoset ID; and
- external photoset deletion never triggers automatic recreation or title-based
  adoption.

The architecture repository has no production FGA LrC publish provider, FGA
album worker, lifecycle endpoint, database schema, or conformance suite and
therefore claims no executable pass.

## Sources

Local Adobe SDK 15.3 documentation:

- publish-provider callbacks `renamePublishedCollection`,
  `reparentPublishedCollection`, `shouldDeletePublishedCollection`,
  `deletePublishedCollection`, and photo-removal callbacks; and
- `LrPublishedCollection` remote ID/URL, settings, and parent methods.

Official Flickr contracts:

- [`flickr.photosets.editMeta`](https://www.flickr.com/services/api/flickr.photosets.editMeta.html)
- [`flickr.photosets.getInfo`](https://www.flickr.com/services/api/flickr.photosets.getInfo.html)
- [`flickr.photosets.delete`](https://www.flickr.com/services/api/flickr.photosets.delete.html)
- [`flickr.photosets.removePhoto`](https://www.flickr.com/services/api/flickr.photosets.removePhoto.html)
- [`flickr.photosets.removePhotos`](https://www.flickr.com/services/api/flickr.photosets.removePhotos.html)
