# ADR 0030: Use one refresh job and keyset pages

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31

## Context

The earlier group-discovery design split one Flickr refresh into a durable work
item per upstream page, retained immutable snapshot generations, and created a
random server-stored continuation handle for every client page. The same cursor
lifecycle was reused for one fresh photo-membership response.

Those mechanisms bound work, but they also added job choreography, cursor
storage and expiry, generation retention, garbage collection, and more failure
states. FGA's private single-user deployment has no measured scale requiring
that machinery.

## Decision

One bounded FGA refresh worker job walks all Flickr writable-group pages, writes
staging rows, and atomically replaces one current snapshot only after complete
success. Fixed page, row, response-byte, elapsed-time, freshness, and admission
limits keep the job finite. Failure retains and truthfully labels the last good
snapshot.

The FGA API backend serves the current snapshot through ordinary keyset pages
ordered by exact Flickr group ID. A visible integer revision plus the last group
ID replaces random continuation handles and retained generations. A revision
change returns `409 Conflict`, and the FGA LrC plug-in restarts the read.

A fresh per-photo membership read uses the same revisioned keyset response after
one complete bounded `flickr.photos.getAllContexts` validation. It never serves
an old observation as current after the fresh read fails.

## Consequences

- One job and one current snapshot are straightforward to implement, inspect,
  retry, and remove.
- The FGA database needs no cursor table, cursor expiry, immutable-generation
  retention, or page-work dependency chain.
- A rare refresh race may make the FGA LrC plug-in restart a bounded read.
- Group discovery can remain usable from a truthfully labeled stale snapshot
  when refresh fails; fresh photo membership still fails closed.
- Flickr page numbers remain an upstream implementation detail.

## Alternatives considered

- **One work item per Flickr page:** rejected because durable page choreography
  is unnecessary for a bounded private-user list.
- **Random server-stored cursors:** rejected because the client already receives
  non-secret Flickr group IDs and a revision check prevents mixed reads.
- **Retain immutable generations until cursors expire:** rejected because a
  `409` restart is simpler and rare at this scale.
- **Offset pagination:** rejected because insertion or replacement can shift
  offsets and because exact group ID is already a stable unique key.
- **Serve old photo membership after a failed fresh read:** rejected because
  current membership is safety-relevant UI evidence and must remain truthful.

## Detailed contract

The [group snapshot and pagination
contract](../group-snapshot-and-pagination.md) defines state, limits, responses,
failure behavior, and required evidence.
