# Worker persistence and scheduler contract

Last updated: 2026-09-11

Status: Accepted persistence and scheduling semantics under ADR 0015, with
private runtime enforcement amended by ADR 0051 on 2026-09-11.
ADR 0050 selects Cloudflare and evaluates Durable Objects and D1 first;
ADR 0046 retains RDS PostgreSQL as fallback. Native adapter proof and hosted
implementation remain pending.

## Purpose and scope

This contract turns the accepted group-submission FIFO, fail-polite ambiguity,
and Flickr write-gate rules into implementable persistence and worker
transactions. It defines the FGA database as the authority for queue order,
claims, dispatch markers, recovery, and due work. It does not select a cloud
queue as another authority.

The private MVP uses one ordinary transactional relational database. The chosen
database **MUST** provide atomic transactions, foreign keys, unique and check
constraints, row-level concurrency control or equivalent conditional updates,
database-generated UTC timestamps, and an indexed way to find due active rows.
A hosted queue or event service may reduce latency, but it is never the durable
owner of an intent or a source of dispatch permission.

[ADR 0050](decisions/0050-select-cloudflare-and-evaluate-native-storage-first.md)
requires native Durable Objects and D1 evaluation before using the RDS fallback.
The sections below retain the
accepted invariants and their conventional relational mapping. A native adapter
must demonstrate equivalent atomicity, durable authority, conditional fencing,
authoritative time, guarded immutable writes, and recovery. The private
runtime enforcement boundary follows accepted
[ADR 0051](decisions/0051-trust-private-storage-runtime-with-guarded-writes.md): ordinary native SQL
guards may enforce protected facts while the deployed storage-owning runtime
is trusted not to dismantle them. Other least-privilege boundaries remain
required. PostgreSQL-specific syntax is not itself a provider requirement.
Material semantic changes require explicit amendments; Cloudflare selection
alone grants no exception. No transaction may be assumed to span native
services.

If the native mapping cannot satisfy the requirements, instantiate this model
on RDS PostgreSQL 18.6 under amended ADR 0046. Either path must pass the real
adapter and migration conformance suite before production use.

[ADR 0015](decisions/0015-database-fenced-worker-scheduling.md) records
the architectural choice. Phase 7 of the
[zero-state publish flow](zero-state-publish-flow.md#phase-7--queue-wake-up-and-independent-group-progress)
remains authoritative for Flickr behavior and result classification.

## Non-negotiable claim and dispatch invariants

Immediate hints, periodic sweeps, and crash recovery all enter one FGA
group-submission worker claim/attempt implementation. None has a direct or
reduced-safety Flickr dispatch path. ADR 0034 exposes no manual retry-now entry
point.

1. Exactly one current database lease generation owns a partition. Every state
   mutation is fenced by that generation and its lease ID; a queue message or
   process-local lock is never a claim.
2. The current worker commits `dispatch_started_at` for the exact attempt before
   it can give the add POST to the HTTP stack. Code structure and conformance
   tests make calling the POST client without a committed marker impossible.
3. Once the marker exists, a network error, cancellation, process failure,
   lease takeover, or failure to persist a received Flickr response never
   restores `pending`, `queued`, or another automatically replayable state. If
   no definitive result was committed, recovery creates the exact-pair
   permanent block and terminal `delivery_uncertain` state atomically.
4. The only pre-dispatch recovery that retains automatic eligibility has a
   durable classification proving zero add-POST request bytes could have left.
   Missing evidence, elapsed time, an expired lease, or an operator's belief is
   not proof.

These invariants are database/worker behavior, not UI policy. The fail-polite
conformance contract requires the hosted implementation's executable suite to
exercise every entry path and mutate each guard so a second POST would fail the
suite.

## Time and identity rules

[ADR 0053](decisions/0053-accept-millisecond-private-database-clocks.md) accepts millisecond
source resolution for database-generated persisted UTC times in this private
deployment. Six-digit formatting or microsecond integer units must not be
presented as finer resolution. Durable order remains explicit sequence/revision
state; timestamps need not be unique. Live monotonic preflight timing is unchanged.

The FGA database clock supplies every persisted lease deadline, due time,
creation time, and transition time. A worker clock cannot decide whether a
lease is expired or persisted work is due. Persisted UTC time supports
coordination and audit; it is not substituted for the process-local monotonic
clock required to enforce the less-than-1,000-millisecond moderation-preflight
freshness window.

Every invocation has a non-secret opaque `worker_invocation_id`. Every claimed
partition receives a new non-secret opaque `lease_id` and an incremented
64-bit `lease_generation`. The generation is the fencing token. A worker must
present both values on every state-changing transaction for that partition.
Process IDs, host names, or an in-memory mutex are diagnostic context only and
never establish ownership.

## Relational state

The names below are logical names. A provider-specific schema may use the
ecosystem's conventional spelling while preserving every field, relationship,
and constraint.

### `group_partitions`

One row exists for each `(fga_user_id, flickr_group_id)` partition. It contains:

- an opaque `partition_id` and unique `(fga_user_id, flickr_group_id)` key;
- `next_enqueue_ordinal`, initially 1 and incremented only while the row is
  locked by an intent-insertion transaction;
- `next_work_not_before`, the database-clock lower bound for revisiting the
  active head, or null when the active FIFO is empty;
- `wake_revision`, incremented whenever a commit can make the partition newly
  or earlier eligible;
- nullable `lease_id`, `lease_generation`, `lease_expires_at`, and
  `lease_started_at` fields;
- the last claim/release time and sanitized last outcome; and
- throttling observations and `next_probe_not_before` when Flickr code `5`
  applies to the partition.

The row is the serialization point for enqueue order and claims. Lease fields
do not carry Flickr result state.

### `submission_intents`

One durable row exists for every exact `(flickr_photo_id, flickr_group_id)`
natural key. It contains the validated FGA user, immutable FGA photo-binding ID,
and partition, an opaque intent ID, immutable `enqueue_ordinal`, current state,
`active_fifo_member`, state version, timestamps, safe-read-failure count,
add-dispatch count,
`next_attempt_not_before`, the last sanitized Flickr result, and any later
positive pool-membership observation.

The FGA database enforces:

- unique `(flickr_photo_id, flickr_group_id)`;
- unique `(partition_id, enqueue_ordinal)`;
- immutable partition, natural key, and enqueue ordinal after insert;
- `active_fifo_member = true` exactly for `queued`, `attempting`, `retrying`,
  and `throttled`;
- `active_fifo_member = false` exactly for `added`,
  `moderation_submitted`, `delivery_uncertain`, `needs_attention`, and
  `cancelled`; and
- state-specific nullability: retrying has `next_attempt_not_before`, throttled
  has a partition `next_probe_not_before`, and terminal states have a terminal
  time and no future due time.

An index beginning with `(partition_id, active_fifo_member,
enqueue_ordinal)` makes the lowest active ordinal the only candidate head.
Another index begins with the partition's `next_work_not_before` so a sweep does
not scan terminal intent history.

Read-only status pages use indexes beginning with immutable
`(fga_user_id, created_at, intent_id)` and
`(fga_photo_binding_id, created_at, intent_id)`, plus partial forms for the exact
active and attention state sets. They support the descending stateless keyset
in ADR 0034 without scanning all retained history. These indexes are read
projections only and confer no queue order or dispatch authority.

### `submission_attempts`

Each worker pass over an active head creates one retained attempt row with a
unique `(intent_id, attempt_ordinal)` and the claiming lease generation. It
contains sanitized membership and moderation-preflight start/result data, the
exact observed membership outcome and database observation time, the exact
observed `ispoolmoderated` value and database observation time, the worker's
diagnostic monotonic elapsed value, dispatch and completion timestamps, zero-
byte-proof classification when applicable, documented Flickr result class/code,
and a sanitized correlation ID. The membership outcome is one of target
present, target absent, or unavailable; raw pool lists and response bodies are
not stored in the attempt.

`dispatch_started_at` is the durable dispatch marker. It is set once and never
cleared. A result or safe `not_dispatched_*` classification may complete the
row, but no code rewrites history to pretend dispatch never started. The FGA
database permits at most one incomplete attempt for an intent.

The intent's add-dispatch count increments in the same transaction that sets
`dispatch_started_at`. A claim, read-only preflight, expired preflight, or
failure proven before POST dispatch does not increment it. Preflight failures
use their separate consecutive counter.

### Safety and history relations

- `submission_blocks` retains one insert-only row for the exact Flickr
  photo/group pair, its first reason/time, and source attempt. Runtime
  operations may select and insert; database guards must reject ordinary
  update/delete, replacement/upsert, and cascading removal. Under ADR 0051,
  the private native storage runtime may hold broader schema capabilities,
  but ordinary application code must not remove guards, change schema, or
  erase storage. Schema changes belong to controlled migration code outside
  runtime request/recovery paths and must preserve the blocks. No
  administration or recovery route receives block-removal authority.
  PostgreSQL implementations retain non-owner runtime roles.
- `submission_intent_events` retains append-only sanitized state-transition,
  lease-recovery, and no-op events, protected by database guards under the same
  ADR 0051 runtime trust boundary. A state change and its event commit in the
  same transaction.
- `flickr_write_gates` and `flickr_write_gate_events` retain the durable scoped
  gate state, revisions, and append-only history defined by ADR 0013.
- A shared Flickr rate-limit reservation store atomically reserves capacity for
  the mandatory membership GET, moderation GET, and possible POST before the
  membership guard. The private MVP may use
  FGA database rows or a mature provider-managed atomic limiter. It cannot use
  per-process counters. Capacity for a proven-unnecessary later operation is
  released exactly once; an uncertain reservation expires conservatively
  according to the configured rate-limit window.

Credentials, OAuth signatures, raw request/response bodies, and photo metadata
do not appear in these relations.

## Durable FIFO insertion

The Phase 6 handoff transaction locks or creates all affected partition rows in
canonical `(fga_user_id, flickr_group_id)` order. Canonical locking prevents two
multi-group requests from deadlocking each other.

For each requested natural key, the FGA API backend first reuses any existing
intent without changing it. For each missing intent, it reads and increments
the locked partition's `next_enqueue_ordinal` and inserts the intent with the
prior value. This per-partition counter avoids the commit-order ambiguity and
gaps of a free-running process-local or database sequence. A rolled-back
transaction advances neither the committed counter nor queue state.

When a new intent is the only active member, the transaction sets the
partition's `next_work_not_before` to database current time and increments its
`wake_revision`. When an older active head already exists, insertion does not
make the later intent independently due. The upload-authorization binding, all
new intents, partition counters, event rows, and wake revisions commit in the
one Phase 6 transaction before the `202 Accepted` response.

The complete client handoff produces at most one post-commit immediate hint,
not one per inserted intent or affected partition. If the transaction creates
several newly eligible heads, the FGA API backend chooses the canonical-lowest
partition key and may publish only that partition's ID and committed wake
revision. Every other due row remains at database current time for the scheduled
sweep. A fully idempotent retry creates no newly eligible head and emits no hint.

## Due-work model and wakeups

`group_partitions.next_work_not_before` is a materialized scheduling projection
of the active head:

| Active-head condition | Persisted due value |
| --- | --- |
| New `queued` head | Database current time |
| Safely `retrying` head | Its exact jittered `next_attempt_not_before` |
| `throttled` head | The partition's exact `next_probe_not_before` |
| `attempting` under a current lease | Current lease expiry for recovery visibility |
| No active head | Null |

A transition recomputes this value from the new active head in the same
transaction. No later intent can make a partition due earlier than its head.
Paused linked-user or deployment gates make a due row ineligible without
rewriting this value, intent state, or FIFO order.

After a worker transaction commits newly eligible follow-on work, that worker
may publish a best-effort immediate hint containing only `partition_id` and
`wake_revision`. The FGA API backend follows the stricter one-hint-per-client-
batch rule above. Every hint is emitted after commit, may be duplicated,
reordered, or lost, and grants no lease or Flickr authority. A consumer must
return to the FGA database and perform the normal claim. A stale revision is a
harmless no-op. The private MVP needs no transactional outbox solely for these
hints because the due row itself is durable and the periodic sweep is the
recovery path.

A provider scheduler starts a due-work sweep at least once per minute. The
sweep claims only rows whose exact `next_work_not_before` is no later than the
database clock, whose lease is absent or expired, and whose deployment and
linked-user gates are enabled. It orders candidates by due time, then last
claim time, then opaque partition ID, and uses bounded batches with row locking,
skip-locked behavior, or equivalent atomic compare-and-set updates. It never
rounds stored due times to its cadence.

The once-per-minute sweep supports the accepted second/minute retry windows.
The conservative nightly response to Flickr code `5` is represented by that
partition's later `next_probe_not_before`; it does not require a separate
nightly-only scheduler.

## Lease acquisition, renewal, and fencing

The claim transaction:

1. locks or conditionally updates one eligible partition row;
2. confirms its active head and both Flickr write gates are still eligible;
3. increments `lease_generation`, assigns a new `lease_id`, and sets the
   database-clock lease deadline;
4. resolves any abandoned prior `attempting` head under the recovery table
   below; and
5. commits before any Flickr call begins.

A worker may renew only its matching generation and lease ID, before expiry,
and only within its bounded invocation deadline. It extends by one configured
lease interval rather than setting an arbitrary time. Before starting the
moderation preflight, the worker ensures that the remaining lease exceeds the
configured GET deadline, POST deadline, and database-commit margin. This makes
ordinary lease takeover occur after the outbound deadline, not during it.

Every later state-changing transaction locks the partition and checks the same
generation and lease ID. Expiry permits a successor to increment the
generation; the increment fences the old worker. An old worker cannot start or
retry a Flickr call after its deadline. It may commit a definitive response for
an already-dispatched attempt after the nominal deadline only if no successor
has advanced the generation. Once fenced, its late response is diagnostic
evidence only and cannot replace the successor's durable recovery result.

Release clears the lease fields only when the generation and lease ID still
match. A stale release is a no-op. Process death needs no special unlock: the
database-clock expiry makes the row claimable.

## Attempt and dispatch transactions

No database transaction remains open during DNS, secret retrieval, rate-limit
waiting, or a Flickr request.

1. **Start attempt.** With the partition locked and fenced, select the lowest
   active enqueue ordinal, check its permanent block, create an attempt row,
   and set the intent to `attempting`. If a block already exists, atomically
   restore the corresponding terminal state and active-membership invariant.
2. **Reserve rate capacity.** Reserve the membership GET, moderation GET, and
   possible POST together before the membership guard. If capacity is
   unavailable, retain the head with an exact due time, release the lease, and
   send no Flickr call.
3. **Read current membership.** Call `getAllContexts` for the exact photo and
   apply the complete strict shape contract. An unavailable observation commits
   sanitized safe-read failure evidence and retains the FIFO head for bounded
   retry without `getInfo` or add. An observation containing the exact target
   group terminalizes the intent as `added` with source
   `pre_add_membership_observation`, removes active membership, and sends no
   later Flickr operation. Only a complete target-absent observation continues.
4. **Persist moderation preflight.** After a successful `getInfo`, update only
   the current attempt with its interpretable moderation value and observation
   evidence. Persisted wall time is audit data; the live worker's monotonic
   clock remains the freshness authority.
5. **Commit dispatch marker.** In one short transaction, lock the partition,
   head intent, attempt, exact-pair block key, and both applicable gate rows.
   Confirm the lease fence, unchanged active head, absent block, current
   attempt, interpretable preflight, and the exact enabled gate revisions.
   Then set `dispatch_started_at`, increment add-dispatch count, and append the
   event. Commit before handing the POST to the HTTP stack.
6. **Recheck monotonic age.** Immediately after commit, recheck the same
   process-local preflight timer. If it has reached 1,000 milliseconds and no
   POST bytes could have left, commit `not_dispatched_preflight_expired`, keep
   the pair unblocked, and repeat with a new preflight. Otherwise begin POST
   dispatch before the timer reaches the boundary.
7. **Commit result.** In one fenced transaction, classify the complete Flickr
   result, update or terminalize the intent, create or confirm a permanent
   block when required, update or pause a Flickr write gate when required,
   append attempt/intent/gate events, recompute partition due time, and release
   or retain the lease. A terminal transition and block creation cannot be
   split across commits.

Any future cancellation, retry-like operation, or administrative repair must
use these same row locks, fences, gate checks, natural keys, and ambiguity
rules. Current administrative gate repair resumes ordinary due work but does
not call the attempt path directly or revive a terminal intent. No operation
receives a shortcut around the dispatch transaction.

## Lease recovery

A successor resolves the prior head before starting new Flickr work:

| Durable prior evidence | Recovery transaction |
| --- | --- |
| No `dispatch_started_at` | Close the abandoned read-only/pre-dispatch attempt as `abandoned_before_dispatch`; keep the head safely retryable without incrementing add-dispatch count |
| Marker plus durable proof that zero POST bytes could have left | Close as `not_dispatched_<reason>`; keep the pair unblocked and safely retryable from a new preflight |
| Marker plus a definitive documented result already committed | Preserve the committed state; recompute the next head and due time |
| Marker, no definitive committed result, and no durable zero-byte proof | In one transaction create or confirm the permanent block, terminalize the intent as `delivery_uncertain`, remove active membership, and append recovery events; never dispatch that pair |
| Unknown Flickr application code committed | Create or confirm the permanent block, terminalize `delivery_uncertain`, pause the deployment gate, and never dispatch that pair |

The absence of a marker is safe only because the implementation and conformance
suite prove that every add path commits the marker before giving the POST to the
HTTP stack. Recovery never infers zero-byte proof merely from a worker error,
lease expiry, missing response, process restart, or elapsed time.

## Bounded progress and fairness

One claim processes one active head and stops early
on throttle, retry due time, paused gate, safety terminal, rate-capacity limit,
lease-renewal failure, or insufficient invocation time. The worker's internal
deadline is 45 seconds inside a 60-second Cloud Run request timeout; the FGA
database lease interval is 60 seconds. Membership, moderation, and add calls
each have a 10-second deadline, and 5 seconds are reserved for the final fenced
commit and lease release. The FGA group-submission worker starts no moderation
GET unless strictly more than 30 lease seconds remain. A worker never holds a
partition lease while sleeping until a future due time.

After a terminal head, the same fenced worker yields rather than claiming the
next head. It releases the lease,
recomputes `next_work_not_before`, increments `wake_revision`, and emits another
best-effort hint after commit. Ordering due partitions by due/last-claim times
prevents one busy group from monopolizing all worker invocations.

## Required conformance evidence

Before deployment, automated database and worker tests must prove at least:

- concurrent identical handoffs create one intent and retain one queue ordinal;
- concurrent distinct handoffs to one partition receive committed FIFO ordinals
  without duplicates or reorder after rollback;
- duplicate/stale hints and concurrent sweeps produce one current lease
  generation;
- an old generation cannot mutate after a successor claim;
- a lost immediate hint is recovered by the periodic due sweep;
- no work starts before its exact due time and paused gates cause no claim churn;
- every possible add starts with a fresh strict attempt-scoped membership read;
  an unavailable read sends neither `getInfo` nor add, while a target-present
  observation terminalizes without a Flickr write;
- terminal transitions remove active membership atomically while retaining
  history;
- every add POST has a committed marker and every marker recovery follows the
  table above;
- crash injection before marker, after marker, after POST handoff, after Flickr
  response, and before result commit produces the required safe state;
- code `6`, code `7`, unknown results, and unresolved dispatch create the
  permanent block in the same transaction as terminal state;
- no runtime path updates/deletes a permanent block, ordinary destructive
  SQL is rejected with guards installed, and migrations/recovery preserve
  protected records under ADR 0051 and FP-BLOCK-009; and
- the live monotonic freshness check and persisted audit timestamps are not
  confused.

The [fail-polite worker/database conformance suite](testing/fail-polite-worker-database-conformance.md)
now assigns stable scenario IDs to these persistence/scheduler cases and adds
the production-adapter topology, crash matrix, bypass matrix, and mutation
requirements. The hosted implementation must instantiate that suite against
its production worker, migrations, and selected database engine. This
architecture repository still claims no executable pass because those
components do not exist here.
