# ADR 0034: Expose read-only group-submission intent status

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31

## Context

The FGA API backend returns durable intent IDs from a group-submission batch,
but the current contract does not define how the FGA LrC plug-in later
distinguishes waiting, throttled, paused, completed, needs-attention, or
delivery-uncertain work. A status surface must preserve the difference between
intent state, active FIFO membership, shared write gates, latest outcome, and a
permanent exact-pair block.

A combined “status and retry” endpoint would be surprising and unsafe. Reading
state does not establish that a Flickr request is safe to repeat. Active retries
already have database-authoritative due times and FIFO order; gate repair has a
separate recent-authenticated proof; and moderation or ambiguous delivery
permanently forbids FGA resubmission for the exact pair.

## Decision

1. The FGA LrC plug-in receives read-only collection and item routes at
   `/api/v001/group-submission-intents`; the FGA administrative control plane
   receives separately authenticated mirrors beneath
   `/api/v001/admin/group-submission-intents`.
2. The collection exposes exact `active`, `attention`, and `history` views,
   optional authenticated photo-binding filtering, immutable descending
   `(created_at, intent_id)` keyset pages, a database-snapshot summary, current
   gate projections, and a minimum recommended poll interval.
3. One intent representation returns immutable IDs, exact durable state and
   revision, database times, attempt count, advisory per-partition queue
   position/due/holds, an allowlisted latest outcome, permanent-block presence,
   and structured attention guidance. It returns no raw Flickr message,
   credential, task/lease identifier, SQL/debug state, or another user's data.
4. `needs_attention` and `delivery_uncertain` form the attention view.
   `moderation_submitted` is a completed FGA action with a permanent block, not
   evidence of moderator acceptance/rejection and not a resubmission prompt.
   A paused write gate remains a separate hold on active intents.
5. Status reads are side-effect free with respect to domain state and upstream
   services. They cannot enqueue, claim, retry, refresh Flickr, clear a gate,
   cancel, reopen, reorder, or remove a permanent block.
6. The private MVP exposes no manual retry-now, reopen, force-resubmit, clear-
   block, reorder, or cancellation operation. Active safe retries obey their
   database due times. Terminal attention intents remain terminal. Gate repair
   uses only ADR 0013's administrative verification and does not revive the
   terminal intent that exposed a fault.
7. The FGA LrC plug-in presents status inside Lightroom Classic, coalesces
   polling through collection reads, honors server minimum intervals and
   `Retry-After`, stops polling when the dialog closes, and never turns a failed
   or partial read into an empty-success display.
8. Route, authorization, PostgreSQL projection, pagination, fail-polite,
   no-side-effect, rate-limit, and reviewed-copy tests are predeployment gates.

## Consequences

- The API reports one existing durable state model instead of inventing a
  client queue or a second presentation-state machine.
- Users can distinguish ordinary waiting, shared repair holds, successful adds,
  moderation handoff, terminal correctable selection faults, and ambiguous
  delivery without reading logs.
- Advisory position is only within one Flickr-group partition. No response
  promises cross-group order, percentage complete, or completion time.
- Terminal safety records remain visible without becoming buttons or bearer
  capabilities.
- The API surface is smaller than a command-oriented queue manager. Future
  cancellation, reorder, or carefully scoped replay semantics require their own
  explicit decision and conformance evidence.

## Rejected alternatives

- **One route that reads status and retries:** rejected because a GET must not
  schedule work and a status observation does not prove replay safety.
- **Manual retry-now for active rows:** rejected because it would let a client
  defeat due times, group throttling, FIFO, gate holds, and global rate
  reservations.
- **Reopen `needs_attention`:** rejected for the private MVP because its failure
  classes need human/external correction, while repeated automated submission
  is not required and can be discourteous. A user can correct future selection
  or act manually in Flickr.
- **Treat every paused-gate row as `needs_attention`:** rejected because the
  fault belongs to one shared gate and bulk state rewrites obscure FIFO.
- **Snapshot generations or random cursors:** rejected because status is an
  observational view, retained history has immutable membership, and simple
  keyset traversal meets the private UI requirement.
- **Expose raw Flickr text/debug records:** rejected because allowlisted reason
  codes are stable and non-secret; raw external/internal text expands privacy,
  injection, and compatibility risk.

## Detailed contract

The complete wire schemas, filters, reason/action vocabulary, FGA LrC plug-in
copy, failure behavior, and conformance cases are in the
[group-submission status API contract](../queue-status-api.md).
