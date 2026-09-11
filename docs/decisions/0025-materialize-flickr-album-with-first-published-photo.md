# ADR 0025: Materialize a Flickr album with its first published photo

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31

## Context

Terry's established Lightroom Classic workflow creates a local album before he
publishes any survivor. Flickr's documented `flickr.photosets.create` method,
however, requires an owned `primary_photo_id`; its API does not create an empty
album.

Using a placeholder or unrelated photo would add an unexplained public resource,
misrepresent album membership, and require a destructive cleanup path. Creating
the Flickr album before the first real upload is therefore neither necessary nor
supported by the documented contract.

## Decision

**Create Album…** creates only one ordinary local FGA published collection with
no remote ID or URL. The first real photo from that collection whose Flickr
upload and hosted exact-photo binding succeed becomes the immutable candidate
primary for one hosted album binding. The FGA album worker creates the Flickr
photoset with that exact photo and records the returned opaque ID and navigation
URL.

The create operation itself supplies the first photo's album membership. Later
photos use separate idempotent membership obligations. The FGA LrC plug-in
records or repairs the remote collection ID/URL only from the hosted binding
through documented Lightroom Classic SDK methods. It never derives identity
from a title or URL and never invents a placeholder.

Ambiguous create and attachment handling remains governed by ticket #0062 and
must be defined before this decision is implementation-ready.

## Consequences

- Terry can create, populate, cull, and edit an empty local album without
  network access or a Flickr side effect.
- An empty local album legitimately has no Flickr navigation target.
- The first successfully bound photo, not UI or rendition order, establishes
  the primary photo.
- A missed Lightroom Classic catalog write can be repaired from the hosted
  binding without replaying Flickr album creation.
- Album materialization can remain pending after the photo itself is published,
  so the FGA LrC plug-in needs truthful attachment status.

## Alternatives considered

- **Create a placeholder photo:** rejected because it is surprising public
  content and creates cleanup risk.
- **Use an existing unrelated photo:** rejected because it asserts a membership
  Terry did not choose.
- **Delay local album creation until publication:** rejected because it breaks
  Terry's cull-and-edit workflow and Lightroom Classic's conventional model.
- **Use the title or URL as album identity:** rejected because titles are not
  unique and URLs are presentation data.
- **Create a duplicate after a lost response:** rejected; ticket #0062 must
  reconcile the original attempt.

## Detailed contract

The [album-scoped publish contract](../album-scoped-publish-contract.md) defines
the local and hosted identities, normal first-photo path, multi-photo behavior,
catalog repair, and required evidence.
