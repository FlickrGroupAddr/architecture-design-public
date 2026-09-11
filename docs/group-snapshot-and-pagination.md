# Group snapshot and pagination contract

Last updated: 2026-09-05

Status: Accepted under ADR 0030; Terry approved the design on 2026-08-25 and
accepted the governing decision on 2026-08-31; executable implementation
evidence remains outstanding

## Scope

This contract defines two different read paths:

- the reusable list of Flickr groups to which the linked owner may submit; and
- the fresh list of Flickr group pools currently containing one exact photo.

Both paths publish only complete validated data, but neither needs retained
immutable generations or random server-stored continuation handles. The FGA API
backend exposes ordinary keyset pages from one current revision. The FGA LrC
plug-in accumulates every page before presenting a complete list.

## Writable-group refresh

The FGA database retains one current group snapshot and one refresh-control row
per linked FGA user. A snapshot contains its monotonically increasing
`snapshotRevision`, `refreshedAt`, and reduced rows keyed by exact Flickr group
ID. It never stores raw Flickr responses.

An initial group-list request follows this policy:

| Current state | FGA API backend response |
| --- | --- |
| Snapshot is at most 15 minutes old | Serve it as `fresh`; create no refresh job |
| Snapshot is older than 15 minutes and a refresh can start or is active | Create or join one refresh job and serve the last good rows as `stale_refreshing` |
| Refresh failed and a last good snapshot exists | Retain and serve those rows as `stale_refresh_failed`, with the last successful and failed-at times |
| No successful snapshot exists and refresh is active | Return `202 Accepted` with `Retry-After` and no group array |
| No successful snapshot exists and the latest refresh failed | Return `503 Service Unavailable` with `group_refresh_unavailable` and no group array |

Only one refresh job may be active for one linked FGA user. The FGA API backend
does not start more than one attempt per user in any 60-second interval. A
request during that interval joins the active job or observes its last result;
it does not create another job.

One FGA refresh worker invocation owns the complete attempt. It starts at
Flickr page 1, obtains a fresh OAuth nonce, timestamp, and signature for every
page request, validates each complete page, and writes reduced rows to staging.
It follows the next Flickr page in the same job; it does not enqueue page-level
work items or publish checkpoints as independently resumable work.

The attempt fails rather than truncates when any of these fixed private-MVP
limits is reached:

- more than 25 Flickr pages;
- more than 10,000 distinct group rows;
- more than 2 MiB in any one Flickr response body; or
- more than 60 seconds of monotonic elapsed time for the complete attempt.

A failure deletes or abandons only staging state and leaves the current snapshot
unchanged. After the final page passes validation, one FGA database transaction
replaces the current rows, advances `snapshotRevision`, records `refreshedAt`,
and marks the job successful. Readers can observe the old complete revision or
the new complete revision, never staging rows or a mixture.

## Stateless group-list pages

The initial request includes `page_size` from 1 through 100 and omits
`snapshot_revision` and `after_group_id`. The FGA API backend orders rows by the
bytewise UTF-8 representation of the exact Flickr group ID and returns at most
`page_size` rows with:

- `snapshotRevision`;
- `refreshedAt`;
- `snapshotStatus`;
- `refreshFailedAt` only when the status is `stale_refresh_failed`;
- `groups`; and
- `nextAfterGroupId`, equal to the final returned group ID when another row
  exists, otherwise `null`.

A continuation repeats `page_size` and sends the returned `snapshot_revision`
and `after_group_id`. The FGA API backend authenticates every request, requires
both continuation parameters together, requires the current revision to equal
`snapshot_revision`, and selects rows whose bytewise group-ID key is strictly
greater than `after_group_id`.

If the current revision changed between pages, the FGA API backend returns
`409 Conflict` with `snapshot_changed` and no rows. The FGA LrC plug-in discards
its partial aggregate and restarts once from the initial request. This small
optimistic check replaces retained generations and cursor lifecycle. Retrying
an identical page is idempotent because the keyset boundary and revision do not
move.

The FGA LrC plug-in may sort the completed aggregate by display name for the UI,
but Flickr group ID remains identity. It must display stale snapshot status and
times; it must never present a refresh failure as a successful empty group list.

## Fresh photo-membership pages

Every initial photo-membership request performs a new documented
`flickr.photos.getAllContexts` read for the hosted binding's exact Flickr photo.
The FGA API backend accepts the observation only after the complete response
passes the strict shape rules in the plug-in/service contract. The fixed
private-MVP budgets are 2 MiB for the response body, 10,000 combined set and
pool context entries, and 15 seconds of monotonic elapsed time.

After validation, one FGA database transaction replaces the binding's prior
paging rows, advances `observationRevision`, and records `observedAt`. The
initial response returns the first keyset page. A continuation supplies
`observation_revision` and `after_group_id`; the FGA API backend requires the
current observation revision to match and returns rows in the same bytewise
exact-group-ID order. `nextAfterGroupId` has the same meaning as group
discovery.

A concurrent newer observation produces `409 Conflict` with
`membership_observation_changed`. The FGA LrC plug-in discards the prefix and
starts one new initial read. A failed initial Flickr read or any failed page
produces no partial UI state. A prior observation may remain in the FGA database
for sanitized audit timing, but the FGA API backend never serves it as current
membership after an initial read fails.

No request creates a random cursor record, pins an old generation, or needs a
cursor expiry or garbage-collection task.

## Required conformance evidence

Executable tests must prove at least:

- one user cannot acquire two concurrent refresh jobs or start attempts more
  often than the 60-second admission interval;
- a refresh walks multiple Flickr pages inside one job and signs every page
  independently;
- page, row, response-byte, elapsed-time, malformed-page, duplicate-ID, and
  dependency failures never replace the current group snapshot;
- a successful transaction replaces all visible rows and advances one revision;
- missing, repeated, mismatched, or malformed keyset parameters fail without
  rows;
- an identical keyset retry returns the same page while its revision is current;
- a revision change returns the specified `409` and never mixes revisions;
- stale group rows are labeled with truthful refresh state and are never
  represented as a successful empty refresh;
- a fresh membership read occurs for every initial selector open and prior
  membership data is not served after failure;
- membership response, count, and elapsed budgets fail the whole observation;
  and
- no cursor table, generation-retention task, or page-level refresh work item is
  required.

The architecture repository has no production FGA API backend, FGA refresh
worker, FGA database schema, or conformance suite and therefore claims no
executable pass.
