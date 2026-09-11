# ADR 0029: Bind each ordinary collection to one Flickr album

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31

## Context

Terry organizes a publish session by creating one ordinary Lightroom Classic
Album, culling photos in it, and explicitly publishing survivors. Flickr album
creation requires a real primary photo, while upload, album creation, album
attachment, hosted proof, and Lightroom Classic catalog writes cannot form one
atomic transaction.

Mutable names and URLs cannot identify the remote target. Replaying an
ambiguous Flickr photoset creation could create duplicates, while treating
album attachment as optional would violate Terry's organizing model.

## Decision

Each user-created ordinary FGA published collection maps one-to-one to one
hosted album binding and one opaque Flickr photoset ID. Selecting the local
Album selects that target. The FGA LrC plug-in offers neither a default
collection nor an arbitrary existing-Flickr-album picker; only the guarded
ambiguous-create repair can select a freshly verified candidate from the same
creation attempt.

An empty local Album performs no Flickr write. Its first real, successfully
bound published photo becomes the immutable primary candidate, and the FGA
album worker materializes the photoset through one durably marked create
dispatch. Creation is never automatically replayed after an ambiguous result.

Every exact hosted photo binding for that Album creates one idempotent durable
attachment obligation. The FGA album worker derives the Flickr identities from
hosted bindings and reconciles membership through fresh reads around a guarded
`flickr.photosets.addPhoto` call. Upload and attachment progress independently;
cross-photo order is unspecified, and an attachment failure never authorizes
another image upload.

## Consequences

- A local Album, not mutable text or a URL, is the photographer's target
  selection boundary.
- Empty Albums remain local and do not need placeholders.
- The FGA database is authoritative for binding identity and obligations;
  Flickr is authoritative for current album membership; the Lightroom Classic
  catalog is authoritative for local membership and native publish state.
- Each photo reaches verified album membership or a truthful repair state.
- Arbitrary pre-existing Flickr albums cannot be adopted through the ordinary
  creation path.
- Repair is operation-specific: ambiguous creation needs owner selection,
  whereas attachment can reconcile from exact membership.

## Alternatives considered

- **Use collection title or URL as identity:** rejected because both are
  mutable and neither proves remote ownership or continuity.
- **Create an empty placeholder photo:** rejected because it would publish an
  unrelated synthetic resource into Terry's account.
- **Make album attachment best-effort:** rejected because every published photo
  must eventually belong to its selected Album or expose a repair state.
- **Replay an ambiguous photoset create:** rejected because Flickr offers no
  client idempotency key and a duplicate might already exist.
- **Let the client supply remote Flickr IDs:** rejected because a modified or
  stale client is not authority for owner, photo, or album identity.

## Detailed contract

The [album-scoped publish contract](../album-scoped-publish-contract.md) defines
the complete binding flow. The
[album-write reconciliation contract](../album-write-reconciliation.md) defines
operation-specific ambiguity handling, and the
[album lifecycle contract](../album-lifecycle-contract.md) defines rename,
hierarchy, and non-destructive local removal.
