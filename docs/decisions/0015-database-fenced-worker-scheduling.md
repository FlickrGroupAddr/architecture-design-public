# ADR 0015: Use database-fenced partition leases and due-time scheduling

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31

## Context

The accepted queue model has one FIFO partition per `(FGA user, Flickr group
ID)`, durable ambiguous-dispatch suppression, immediate worker hints, retry
windows beginning at 30–60 seconds, and conservative later probes after Flickr
code `5`. The implementation needs one authority for queue position, claims,
dispatch evidence, and recovery across concurrent workers and process death.

A cloud message cannot safely be that authority: delivery may duplicate,
reorder, or disappear, and a message cannot atomically commit Flickr intent
state in the FGA database. A nightly-only scheduler also cannot discover work
in the accepted second/minute retry windows.

## Decision

The FGA database is the durable authority for worker scheduling and safety.
Each group partition stores its next FIFO ordinal, exact next-work time, wake
revision, and one expiring lease with a monotonically increasing generation as
a fencing token. Every worker mutation conditions on the lease ID and
generation. A process-local lock, queue-message delivery, or worker identity
never grants dispatch permission.

The Phase 6 transaction serializes each affected partition row and assigns
missing intents from its committed counter. This preserves FIFO among committed
intents without depending on process timing or a free-running sequence. Exact
photo/group identity and partition/ordinal pairs are database-unique.

After commit, an immediate hint may carry only opaque partition ID and wake
revision. It is latency optimization, not work state. A scheduled due-work
sweep runs at least once per minute and recovers lost hints, safe retries, and
expired leases from indexed database due times. The nightly code-`5` policy is
one partition due time, not a separate scheduler incapable of short retries.
For a client group-submission batch, ADR 0020 further limits the FGA
API backend to zero or one hint for the canonical-lowest newly eligible
partition; the other due partitions rely on the same sweep.

Every add attempt commits `dispatch_started` before the HTTP stack receives the
POST. A successor that sees an unresolved marker and no durable zero-byte proof
creates the permanent exact-pair block and terminal `delivery_uncertain` state
in one transaction. A missing marker is safely retryable only because no
conforming add path can dispatch without it.

The database clock governs persisted due and lease times. The worker's
monotonic clock alone governs the less-than-1,000-millisecond moderation
preflight freshness rule. No database transaction remains open across a network
call.

The full schema fields, transaction order, fencing semantics, recovery matrix,
and conformance evidence are defined in
[`worker-persistence-scheduler-contract.md`](../worker-persistence-scheduler-contract.md).

## Consequences

- Queue order, recovery, and permanent suppression survive message loss,
  process death, deployment, and concurrent workers.
- Accepted [ADR 0050](0050-select-cloudflare-and-evaluate-native-storage-first.md) selects Cloudflare and evaluates
  Durable Objects and D1 against these invariants first. Amended ADR 0046
  retains RDS PostgreSQL 18.6 as fallback. Provider messages and process-local
  serialization never replace the durable authority defined here.
- Immediate messages are cheap and disposable because workers always return to
  the FGA database to claim work.
- Per-partition counter locking serializes only submissions to the same group
  line. Independent groups remain concurrent.
- Lease configuration must exceed the outbound request deadlines plus commit
  margin, and worker runtime limits must leave time for a safe final commit.
- An exact Flickr result received by a fenced old worker may be discarded after
  takeover. That conservative loss is preferable to letting stale workers
  overwrite recovery or cause another add.
- Database/worker conformance tests become a deployment gate, especially around
  crash injection and the dispatch marker.

## Alternatives considered

- **Make a cloud queue authoritative:** rejected because message delivery and
  FGA database state cannot share the required atomic commit, while duplicate
  delivery still needs database idempotency and fencing.
- **Use one physical queue per user/group:** rejected because it adds dynamic
  infrastructure lifecycle without strengthening the relational FIFO
  invariant.
- **Use a process-local mutex:** rejected because it disappears on restart and
  cannot coordinate concurrent worker processes.
- **Use a global sequence as committed FIFO:** rejected because allocation
  order can contain rollbacks and need not equal commit order. The locked
  partition counter is direct and local to the promised ordering boundary.
- **Hold a database transaction open across Flickr calls:** rejected because
  network latency would extend locks, exhaust connections, and still could not
  make Flickr and the FGA database atomic.
- **Run only a nightly sweep:** rejected because it contradicts the accepted
  second/minute safe-retry windows.
