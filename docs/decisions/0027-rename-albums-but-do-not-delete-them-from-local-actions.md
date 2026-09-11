# ADR 0027: Rename albums but do not delete them from local actions

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31

## Context

Lightroom Classic exposes callbacks when a published collection is renamed,
reparented, deleted, or has photos removed. Flickr separately exposes metadata,
album deletion, membership removal, and photo deletion methods. A callback does
not make those different remote effects equivalent.

Terry has a clear reason to keep an album title synchronized after explicitly
renaming it. No requirement says that removing local catalog organization should
destroy a Flickr album, its memberships, or its photos.

## Decision

For a bound ordinary album, an explicit local rename creates a revisioned,
idempotently reconciled Flickr title intent using `flickr.photosets.editMeta`.
The FGA album worker sends only the exact photoset ID and required title, omits
the optional description, and verifies the result through `getInfo`. A third
remote title causes a visible conflict rather than an automatic overwrite.

Reparenting is local-only organization and sends no Flickr write. Removing a
photo or album locally also sends no Flickr delete, photoset delete, membership
remove, or replacement call. The remote album and photos remain, hosted identity
and history are retained, and previously accepted attachment obligations finish
or remain visible for repair.

## Consequences

- The common rename interaction remains convenient without tying identity to
  mutable text.
- Flickr-authored album descriptions survive FGA title changes.
- Local organization can be rearranged or removed without a destructive remote
  surprise.
- Terry must use Flickr's UI for deliberate album/membership/photo deletion.
- A locally removed album can leave a remote album and durable archived binding;
  that is the intended preservation behavior, not an orphan-cleanup failure.

## Alternatives considered

- **Mirror every Lightroom callback to its similarly named Flickr method:**
  rejected because local organization is not remote-deletion authorization.
- **Delete the Flickr album after a confirmation inside the local removal
  dialog:** rejected without an actual product requirement and dedicated
  destructive-write ambiguity contract.
- **Remove Flickr album membership when a local photo leaves the collection:**
  rejected because publication established a durable album obligation and
  external membership can outlive local organization.
- **Synchronize Flickr description with an empty local value:** rejected because
  `editMeta` makes description optional and Flickr may hold owner-authored text.
- **Automatically adopt a remote title change:** rejected because it would
  mutate the Lightroom Classic catalog without a local rename decision.

## Detailed contract

The [album lifecycle contract](../album-lifecycle-contract.md) defines rename
revision/ambiguity handling, local hierarchy, non-destructive removal, archived
bindings, external drift, and required evidence.
