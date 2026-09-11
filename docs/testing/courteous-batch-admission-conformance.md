# Courteous group-batch admission conformance

Last updated: 2026-09-05

Status: Accepted required hosted conformance contract; no executable pass
exists until the production FGA LrC plug-in, FGA API backend, FGA database,
route registry, and scheduler adapters exist

## Purpose

This contract turns accepted
[ADR 0020](../decisions/0020-single-courteous-group-batch-admission.md)
into stable acceptance cases. It proves that one photo's complete bounded group
selection enters the FGA API backend through one operation and cannot fan out
into one immediate worker notification per group.

The test target is the production request handler, transaction repository,
route registry, queue-due projection, hint publisher, and official client
adapter. A documentation parser, mock-only alternate handler, or test-only
batch implementation is not evidence.

## Required topology and observations

The suite uses a fresh production-engine database initialized through production
migrations, the compiled route registry and edge/development routing artifacts,
a deterministic hint sink, and an injected database clock. The FGA API backend
uses production authentication and binding adapters with synthetic accounts and
photo IDs. The suite supplies no real Flickr credentials and the request handler
must make no Flickr call.

Each case captures:

- HTTP requests and server-owned route identity;
- official-client calls and group-ID arrays;
- committed photo binding, intent, partition, ordinal, due-time, and event rows;
- transaction begin/commit/rollback boundaries;
- post-commit hint count, partition ID, and wake revision;
- due-sweep claims after a deliberately lost hint; and
- sanitized response and audit records.

The stable IDs below appear in production test names or metadata. CI fails for
a missing, duplicate, skipped, or selected-out ID.

## Route and official-client cases

| ID | Stimulus | Required assertions |
| --- | --- | --- |
| `CBA-ROUTE-001` | Official client selects one group | Exactly one `POST .../group-submission-batches`; no single-group operation exists in the client or server route inventory |
| `CBA-ROUTE-002` | Official client selects several groups | Exactly one request containing the complete ordered unique group-ID array; no client loop, pacing, or slice |
| `CBA-ROUTE-003` | Probe plausible singular and plural single-group create paths | FGA API backend-owned `404` or `405`; no handler invocation, redirect, or static application shell |
| `CBA-ROUTE-004` | Future credential class is added without explicit batch-route authorization | Deny by default; no fallback to plug-in, browser, or administrator authority |
| `CBA-CLIENT-001` | Selection exceeds `max_group_ids_per_batch` | Official client shows a whole-selection refusal and sends no partial request |

## Validation and transaction cases

| ID | Stimulus | Required assertions |
| --- | --- | --- |
| `CBA-VALID-001` | Empty, duplicate, malformed, or over-limit input | Reject the complete request before any binding mutation, intent, ordinal, due-row change, event, or hint |
| `CBA-VALID-002` | Compiled OpenAPI, request validator, and deployment configuration | The same fixed positive `max_group_ids_per_batch` value is present in all three; drift fails startup or deployment |
| `CBA-TXN-001` | Valid batch with several missing intents in distinct partitions | One transaction commits the binding and every intent/ordinal/due projection; `202` follows commit |
| `CBA-TXN-002` | Existing and missing natural keys are mixed | Preserve every existing intent exactly, create every missing intent once, and return one ordered snapshot per requested group |
| `CBA-TXN-003` | Fault after any insertion but before commit | Roll back the binding, every new intent/ordinal/due projection, events, and hint eligibility; no partial handoff is visible |
| `CBA-TXN-004` | Concurrent overlapping batches | Canonical partition locking and unique natural keys converge without duplicate intents, duplicate ordinals, or partial success |
| `CBA-TXN-005` | Handler is instrumented while processing a valid batch | Zero `getInfo`, `pools.add`, or other Flickr operations occur before or after the database commit inside the request path |

## Hint, retry, and recovery cases

| ID | Stimulus | Required assertions |
| --- | --- | --- |
| `CBA-HINT-001` | Batch creates several newly eligible idle heads | After commit, publish at most one hint for the canonical-lowest eligible partition; never one hint per group |
| `CBA-HINT-002` | Batch creates intents only behind active heads | Publish no hint; retain each partition's existing head and due projection |
| `CBA-HINT-003` | Identical request repeats after a lost `202` | Return `created: false` snapshots, create no row or ordinal, and publish no new hint |
| `CBA-HINT-004` | Batch mixes an existing pair with newly eligible and non-head pairs | At most one hint chosen only from newly eligible partitions; no existing or blocked pair gains authority |
| `CBA-HINT-005` | The one allowed hint is lost | The scheduled sweep claims every due partition within its normal cadence and preserves per-partition FIFO |
| `CBA-HINT-006` | Hint is duplicated or reordered | Consumers return to the FGA database; one current lease generation claims the partition and no duplicate add authority exists |

## Required mutation evidence

Before this suite can gate a release, it must fail for deliberate isolated
mutations that:

- add a single-group create handler or static-route fallback;
- make the official client loop or slice one selection;
- accept one element before discovering a later invalid element;
- emit a hint before transaction commit;
- emit one hint per inserted intent or partition;
- let the client choose the hinted partition or request synchronous progress;
- emit a hint for a fully idempotent retry;
- remove the due row for an unhinted partition; or
- let OpenAPI, validation, and deployment bounds drift.

The hosted release command fails for absent mutation evidence, infrastructure
failure, or any missing stable case. Until the hosted components and command
exist, project documents must continue to say this behavior is specified rather
than executable or passed.
