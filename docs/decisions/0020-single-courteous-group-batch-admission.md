# ADR 0020: Use one courteous server batch for group-intent admission

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31

## Context

A photographer normally selects several Flickr groups for one photo. Each
selected `(Flickr photo ID, Flickr group ID)` pair needs its own durable intent
and independent `(FGA user, Flickr group ID)` FIFO position, but that does not
make each pair a separate client operation.

The pinned legacy browser called its single-group route once per selected group,
while its backend also had a batch route designed to avoid immediate fan-out.
Client-side pacing could therefore bypass the courteous behavior: one UI action
could produce a separate HTTP request and immediate worker opportunity for
every group. A faster browser, another official client, or a modified client
could make that burst worse.

The current private MVP exposes only the FGA LrC plug-in, but a future browser
or other client must not recreate two admission semantics. The FGA API backend
already has a natural batch transaction and service-enforced unique
`(Flickr photo ID, Flickr group ID)` keys. Preserving one operation is simpler
than adding a single-group compatibility route, client pacing rules, or a
second idempotency scheme.

This boundary governs admission and immediate scheduling, not eventual worker
throughput. Global Flickr rate limiting, per-partition FIFO, fail-polite reads,
and the public-launch abuse gate remain independent controls.

## Decision

1. The only authenticated client operation that creates group-submission
   intents is
   `POST /api/v001/group-submission-batches`. Every official
   client uses that operation even when exactly one group is selected. The FGA
   API backend registers no single-group create route or compatibility alias.
2. One request names one validated photo binding and the complete nonempty set
   of group IDs the user selected for that handoff. The set contains unique
   group IDs and cannot exceed the fixed deployment value
   `max_group_ids_per_batch`, which is recorded in the generated OpenAPI and
   deployment configuration. An empty, duplicate, malformed, or
   over-limit request is rejected before any database write or wake hint.
3. An official client never splits one selection into several requests. If the
   selection exceeds the advertised limit, it shows a whole-selection refusal
   and asks the user to reduce the selection. It does not silently slice,
   pace, or retry individual group IDs.
4. After complete authentication, common-binding ownership/revision, and
   request validation, one FGA database transaction creates or reuses every natural-key intent,
   assigns all new FIFO ordinals, updates all affected partition due rows, and
   commits the complete result before `202 Accepted`. A failure rolls back the
   entire handoff. Response order is only for client reconciliation.
5. The FGA API backend performs no `flickr.groups.getInfo` or
   `flickr.groups.pools.add` call in the HTTP request. It does not invoke one
   worker per group. After commit, it emits at most one best-effort immediate
   partition hint for the complete batch: the canonical-lowest newly eligible
   partition, if one exists. Every other newly due partition remains indexed at
   database current time and is discovered by the scheduled due-work sweep
   within its normal at-least-once-per-minute cadence.
6. A retry that creates no new eligible head emits no new immediate hint. A
   partial retry may emit at most one hint for its newly eligible partitions.
   Lost hints do not change correctness because the FGA database due rows are
   authoritative.
7. The client cannot choose the hinted partition, worker priority, attempt
   time, or a synchronous/immediate flag. The route registry and black-box
   conformance gate prove that plausible single-group create paths are absent
   and cannot fall through to a static application shell.
8. Any later official browser, API client, or administrative surface that gains
   group-intent authority must use this same operation and transaction. Adding
   a different write path requires a new architecture decision and equivalent
   courtesy, idempotency, authorization, and conformance evidence.

## Consequences

- One multi-group user action cannot create one immediate worker notification
  per group. At most one newly idle partition gets the low-latency optimization;
  the others normally wait no more than the due-sweep cadence before claim.
- The FGA database still stores one intent per exact pair and preserves each
  partition's FIFO independently. Batch admission does not promise cross-group
  ordering, atomic Flickr completion, or all-at-once worker progress.
- A one-group action uses the same schema, validation, transaction, response,
  and recovery path as a many-group action.
- The fixed request bound protects validation, transaction, response, and lock
  budgets without introducing automatic slicing. ADR 0033 proposes and requires
  tests for `max_group_ids_per_batch=60` before hosted implementation is called
  ready.
- This contract prevents official-client and one-request fan-out. It does not
  prove that a hostile user cannot submit many separate batches over time.
  Public or multi-user launch remains prohibited until the separate abuse
  threat model supplies conservative admission and rate limits.

## Rejected alternatives

- **One client request per group with browser pacing:** rejected because pacing
  is not a server invariant and was the legacy courtesy defect.
- **Keep both single-group and batch routes:** rejected because two write paths
  invite semantic drift and make the surprising path the easiest one to call.
- **Silently slice an over-limit selection:** rejected because it recreates
  multiple admission events and makes partial commitment a client problem.
- **Synchronously attempt every newly idle partition after commit:** rejected
  because one selection would fan out into a burst and tie request behavior to
  Flickr latency.
- **Add a separate batch idempotency key:** rejected for the private MVP because
  the verified photo binding plus service-enforced natural pair keys already
  make an identical retry safe.

## Required evidence

The eventual hosted repository must test the production route, transaction,
scheduler, and route-registry adapters for at least:

- one-group and many-group requests use the same route and transaction;
- complete validation failure creates no intent, ordinal, due-row change, or
  hint;
- a valid many-group request commits every requested intent or none;
- one committed batch emits zero or one hint, never one hint per group;
- an identical retry creates no intent and emits no hint;
- a lost hint is recovered by the due sweep without changing FIFO;
- an over-limit official-client selection is not sliced; and
- single-group create-path probes receive a server-owned `404` or `405`, never
  a handler, redirect, or static application shell.

This architecture repository specifies those cases but has no hosted FGA API
backend, FGA database, or FGA group-submission worker against which to claim an
executable pass.
