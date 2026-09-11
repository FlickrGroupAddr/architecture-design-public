# ADR 0050: Select Cloudflare and evaluate native durable storage first

Date: 2026-09-06

Status: Accepted by Terry on 2026-09-06; private runtime-protection scope amended
by [ADR 0051](0051-trust-private-storage-runtime-with-guarded-writes.md) on 2026-09-11

## Context

On 2026-09-06 Terry corrected the implementation handoff: Cloudflare is
selected, the storage discussion starts with Durable Objects and D1, and
RDS PostgreSQL is an acceptable fallback if Cloudflare cannot host what the
FGA hosted components need. Terry further clarified that AWS backing services,
including secrets and databases, are acceptable when native Cloudflare services
do not meet the requirements, provided the decision is fully explained.
This records that owner direction rather than
inferring a platform choice from the implementation repository's name.

The prior recommendation favored ordinary PostgreSQL transactions and
database-enforced runtime roles. The dated comparison identified native
transaction-composition, privilege, and secret-version questions. Those are
concrete proof obligations, not permission to substitute AWS compute for
the owner's selected platform. Terry prefers evaluating the simpler native
Cloudflare topology first while keeping the conventional database fallback.

## Decision

1. Cloudflare is the selected hosted platform for the FGA API backend and
   hosted implementation. Evaluate its API, static-asset, worker, and scheduling
   surfaces against the accepted component contracts.
2. Evaluate Durable Objects and D1 first for durable storage and coordination.
   Determine each service's responsibilities from the transaction, identity,
   concurrency, recovery, retention, and operational requirements. This
   accepts an evaluation priority, not a completed native-storage design or
   a conformance pass.
3. Retain the existing Amazon RDS for PostgreSQL 18.6 instance as the fallback
   when native services cannot meet those requirements. This explicitly amends
   ADR 0046's unconditional database selection. Its verified TLS, narrow
   network access, testing, backup/restore, and least-privilege role
   requirements remain applicable when using that fallback.
4. AWS managed backing services are acceptable fallbacks for secrets, databases,
   or another required store when native Cloudflare services do not meet the
   requirements. Keep Cloudflare compute selected. Before adopting a fallback,
   explain the unmet requirement, documented native capability, alternatives
   and proof results, identity/network boundary, cost, and operational tradeoff.
   Terry strengthened this threshold in [ADR 0052](0052-evaluate-paused-native-credential-replacement.md):
   first consider simpler native workflows and justify why the remaining gap
   matters for the private deployment. A missing preferred API shape or existing
   AWS prototype does not establish need. No fallback service or resource is
   provisioned by this decision.
5. Supersede proposed ADR 0033's Google Cloud deployment direction. Preserve its
   topology and the dated comparisons as historical evidence. Cloudflare
   selection does not automatically select every managed-secret capability.
6. Preserve the accepted atomic-admission, fail-polite, dispatch-marker,
   fenced-recovery, authentication, and permanent-suppression requirements.
   Each durable fact has one explicit authority. Do not assume a transaction
   spans Durable Objects and D1, or that actor serialization alone replaces
   every persistence or privilege invariant.
7. Prove equivalent native behavior before treating PostgreSQL-specific syntax
   as a requirement. A material change to accepted security or transaction
   semantics requires a separate explicit ADR amendment. This decision grants
   no such exception by itself. The subsequently accepted
   [ADR 0051](0051-trust-private-storage-runtime-with-guarded-writes.md) explicitly narrows
   private runtime privilege isolation while retaining guarded writes and all
   permanent-suppression behavior.
8. [ADR 0052](0052-evaluate-paused-native-credential-replacement.md) resolves the next step of
   the native secret-version review: evaluate a paused native replacement with
   an application generation before selecting AWS. It explicitly accepts the
   private pause/repair availability tradeoff, not a native conformance pass.
   It does not accept application cryptography or credential-triggered Worker
   deployments. The earlier exact-version review remains historical evidence;
   AWS remains available for a demonstrated remaining requirement.
9. Place actionable implementation exploration and Cloudflare spikes in Ready
   For Work on the implementation board. Terry separately reaffirmed ADR 0003's
   project-wide MIT license on 2026-09-06. This direction does not accept
   proposed ADRs 0047, 0048, and 0049.

## Consequences and proof boundaries

Native-storage and coordination proofs come before Hyperdrive or an assumption
that the FGA database is PostgreSQL. RDS compatibility and networking probes
are conditional fallback work.

The native proofs cover complete multi-group admission, uniqueness, durable
order, concurrent claims, stale-worker fencing, failure around the dispatch
marker, atomic permanent suppression, protected-write guards and runtime
behavior under ADR 0051's private trust model, and backup/restore. A split
across services must account for every partial failure; a local simulator alone is not production provider evidence.

A mapping that needs a surprising custom storage or privilege service must
make that cost explicit. RDS remains available instead of making custom
machinery a condition of Cloudflare compute. Short-lived authentication or
coordination state may have a different storage fit from permanent submission
records.

No native-storage pass, live provider mutation, or production implementation is
recorded by this decision. ADR 0003 separately controls the license boundary.

## Related authority and evidence

- [Worker scheduling](0015-database-fenced-worker-scheduling.md)
- [Persistence contract](../worker-persistence-scheduler-contract.md)
- [Fail-polite conformance](../testing/fail-polite-worker-database-conformance.md)
- [Courteous batch admission](0020-single-courteous-group-batch-admission.md)
- [RDS fallback](0046-use-existing-amazon-rds-postgresql.md)
- [Proposed repository and first-slice boundary](0047-separate-architecture-hosted-and-lightroom-repositories.md)
- [Dated hosted comparison](../research/2026-09-05-hosted-compute-candidate-comparison.md)
- [Native secret-version evidence](../research/2026-09-05-cloudflare-secret-versioning-gate.md)
