# ADR 0038: Keep existing-photo intake queue-only

Date: 2026-08-28

Status: Accepted by Terry on 2026-08-31

## Context

Accepted ADR 0008 lets the photographer select an existing public Flickr photo
and submit add-only group intents without rendering or uploading the photo
again. ADR 0021 gives that path fresh hosted owner/public proof, and
ADR 0022 separates the Flickr photo from every provider-scoped
Lightroom Classic published-photo record.

Ticket #0067 proved a narrower technical possibility in a disposable catalog.
Using the documented
`LrPublishedCollection:addPhotoByRemoteId` API, a diagnostics provider created
a second provider-scoped record for a photo already published through Adobe's
Flickr plug-in. The record survived restart, was undoable, and could be removed
locally without changing the Flickr plug-in's source record or the Flickr
photo.

The same probe exposed the product cost. A harmless metadata edit placed only
the new association under **Modified Photos to Re-Publish**. **Publish Now**
then invoked the FGA provider's publication callback, and local removal required
another **Publish Now** action to invoke its deletion callback. A safe product
implementation would therefore need a distinct provenance, fresh hosted proof,
fail-closed rendering and network boundaries, local-only deletion semantics,
and restart/Undo reconciliation for a record that can still look like an FGA
publication.

The accepted queue-only path already satisfies the customer requirement: choose
an existing public photo and add it to groups without changing its catalog or
Flickr publication state. No unmet requirement justifies the second record and
its extra lifecycle.

## Decision

Keep existing-public-photo intake queue-only. The production FGA LrC plug-in
does not call `LrPublishedCollection:addPhotoByRemoteId` or another
catalog-mutating publication API for that path and does not create a
provider-scoped catalog association for the selected Flickr photo.

The FGA LrC plug-in may read documented catalog publication data as an optional
selector label or shortcut. That evidence remains read-only and cannot replace
fresh proof from the FGA API backend. Existing-photo intake creates or refreshes
only the FGA hosted photo binding and submits the explicitly selected add-only
group intents.

The ticket #0067 diagnostics provider and evidence remain a bounded research
artifact, not a production feature or a compatibility promise. Production code
does not need `catalog_association_only` provenance, imported-association
republish handling, or local-association deletion handling while this decision
stands.

A later proposal may reconsider catalog association only after identifying a
concrete customer requirement that queue-only intake cannot meet. That proposal
requires a new ADR and must preserve the explicit per-photo action, fresh hosted
proof, source-record immutability, no-render/no-network republish boundary,
local-only removal, restart/Undo reconciliation, and no automatic or bulk
association safeguards established by the non-destructive existing-photo
boundary.

## Consequences

- Queueing an existing public Flickr photo does not add it to an FGA published
  collection or imply that the FGA LrC plug-in published it.
- The Lightroom Classic catalog remains truthful about which provider owns each
  publication record; the FGA LrC plug-in does not create a duplicate
  **Published Photos** entry merely to support group queueing.
- Existing photos cannot enter an FGA-specific **Modified Photos to Re-Publish**
  or local-deletion workflow through group intake.
- The production FGA LrC plug-in needs no permanent callback path whose only job
  is to refuse rendering, uploading, replacement, or remote deletion for an
  imported association.
- The photographer uses the explicit existing-photo selector and FGA queue
  status instead of an FGA published collection to find and manage group work
  for photos published elsewhere.
- The disposable-catalog result remains useful evidence if a later unmet
  requirement justifies reconsideration.

## Rejected alternatives

- **Accept a guarded per-photo association:** rejected because it introduces a
  second provider-scoped publication record and surprising republish/removal
  states without satisfying a customer job that queue-only intake misses.
- **Create associations automatically or in bulk:** rejected because discovery
  is advisory, catalog correlation is not hosted authority, and the resulting
  duplicate state and failure surface would scale silently.
- **Copy or modify Adobe's Flickr plug-in record:** rejected because the record
  belongs to another provider and the documented SDK exposes no ownership
  transfer.
- **Write the Lightroom Classic catalog database directly:** rejected because
  its schema is not a documented SDK contract and direct writes bypass host
  transaction and publish-service semantics.
