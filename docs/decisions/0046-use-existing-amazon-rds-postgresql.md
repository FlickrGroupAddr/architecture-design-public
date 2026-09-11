# ADR 0046: Use the existing Amazon RDS for PostgreSQL database

Date: 2026-09-05

Status: Accepted; database-selection scope amended by ADR 0050 on 2026-09-06

Private-deployment amendment: [ADR 0051](0051-trust-private-storage-runtime-with-guarded-writes.md)
accepts native SQL guards with a trusted storage-owning runtime. Broad native
schema authority alone no longer requires the RDS fallback; actual remaining
transaction, recovery, and other requirement failures still may.

Current disposition:
[ADR 0050](0050-select-cloudflare-and-evaluate-native-storage-first.md)
selects Cloudflare and evaluates Durable Objects and D1 first. RDS PostgreSQL
is the fallback when
native services cannot meet the requirements. The original comparison below
remains rationale for that fallback, not a veto on native exploration.

## Context

The provider-neutral FGA database contract requires ordinary PostgreSQL
transactions, relational constraints, row locking, database-clock timestamps,
fenced conditional updates, backups, and production-like conformance evidence.
Proposed ADR 0033 previously carried Cloud SQL for PostgreSQL 18 as part of one
self-contained Google Cloud candidate.

Terry has an existing Amazon RDS for PostgreSQL 18.6 instance and prepaid three
years of its compute. Replacing that instance solely to colocate the database
with an API provider would discard a material owner investment without
satisfying an unmet FGA requirement. Conversely, using the RDS fallback does not require
the FGA API backend or FGA group-submission worker to run on AWS; Cloudflare and
Google Cloud can reach PostgreSQL through separately evaluated network paths.

The instance is currently Internet-accessible. That describes its present RDS
configuration, not permission for unrestricted PostgreSQL ingress. The selected
compute topology must still define and test a least-privilege network boundary.

On 2026-09-05 Terry clarified that D1 remains in scope if a requirements-first
comparison finds it more attractive than RDS. The prepaid term is therefore a
cost advantage, not a prohibition on reconsideration. The dated hosted-compute
comparison evaluated D1's transactional batches, single-writer behavior,
consistency, recovery, and privilege surface against the accepted fail-polite
contract. D1 removed several cross-provider concerns but required less
conventional transaction composition and a custom replacement for PostgreSQL
runtime roles. ADR 0050 later reopened native storage evaluation as the selected
implementation order while preserving RDS as the conventional fallback.

## Decision

1. If the native evaluation under ADR 0050 cannot satisfy the requirements,
   the production FGA database uses Terry's existing RDS PostgreSQL instance.
   PostgreSQL 18.6 is the fallback conformance target; later minor-version
   maintenance remains an explicit tested operational change.
2. The prepaid compute is a cost constraint, not a correctness exception. The
   instance must still satisfy every accepted FGA database, backup, restore,
   migration, role-separation, observability, and conformance requirement.
3. Database hosting does not select FGA API backend, FGA group-submission
   worker, queue, scheduler, CDN, HTTPS-edge, or managed-secret providers.
4. An AWS compute candidate should use private VPC connectivity where practical.
   A non-AWS compute candidate must use a supported private connector or narrow
   provider egress allowlist. Every path requires verified TLS and
   least-privilege database roles. `0.0.0.0/0` PostgreSQL ingress is prohibited.
5. The FGA database remains the sole authority for durable intent order, due
   work, fenced leases, dispatch markers, gates, and permanent suppression.
   No provider queue, proxy, cache, or edge store may weaken those semantics.

## Consequences

- RDS retains its transaction and runtime-role advantages as the fallback.
  Cloudflare compute is selected by ADR 0050; database locality does not
  reopen that choice by itself.
- Cloudflare Workers must prove Hyperdrive compatibility with the exact engine,
  fresh transaction behavior, acceptable background-handler placement, and a
  proportionate network path.
- Google Cloud Run would add a cross-cloud database path and static-egress
  infrastructure without supplying database locality.
- Every hosted candidate avoids the cost and migration risk of a second managed
  production database.
- RDS connection-pooling behavior, engine upgrades, backup/restore, and network
  failure modes become mandatory release evidence rather than provider-default
  assumptions.

## Rejected alternatives

- **Retain Cloud SQL because proposed ADR 0033 already describes it:** rejected
  because ADR 0033 is Proposed and cannot override the later accepted RDS
  decision.
- **Create another database beside the selected compute provider:** rejected
  because it adds migration, synchronization, cost, and split-authority risk
  without an unmet FGA requirement.
- **Select all AWS hosted components automatically:** rejected because database
  locality is one comparison factor, not a dependency that determines every
  other provider boundary.
- **Permit unrestricted public PostgreSQL access:** rejected because public
  reachability does not require or justify accepting connections from every
  Internet source.
- **Replace RDS with D1 for a smaller Cloudflare-only topology:** reconsidered
  with Terry's explicit permission on 2026-09-05 and not selected. D1 removes
  Hyperdrive, database-placement, and cross-provider networking concerns, but
  the reviewed binding supplies transactional batches rather than a
  conventional interactive transaction and does not document PostgreSQL-like
  runtime table/role grants. That privilege-based objection was narrowed by
  ADR 0051 on 2026-09-11: a custom privilege service is not required solely to
  contain the trusted private native runtime. Transaction and recovery proofs
  remain necessary before selecting D1.

## Related evidence

- [Hosted compute candidate comparison](../research/2026-09-05-hosted-compute-candidate-comparison.md)
- [Worker persistence and scheduler contract](../worker-persistence-scheduler-contract.md)
- [Fail-polite worker/database conformance suite](../testing/fail-polite-worker-database-conformance.md)
- [Proposed ADR 0033](0033-deploy-on-google-cloud.md)
