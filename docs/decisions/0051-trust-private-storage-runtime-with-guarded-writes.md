# ADR 0051: Trust the private storage runtime with guarded writes

Date: 2026-09-11

Status: Accepted by Terry on 2026-09-11

## Context and owner decision

The accepted persistence and fail-polite contracts originally required database
privileges that let application runtimes insert permanent submission blocks
but prevent them from changing/deleting those rows or their schema. The
2026-09-06 implementation probe found that D1 and owning SQLite-backed Durable
Object runtimes could remove their SQL guards or erase their storage. The
ordinary update/delete/replace/upsert/cascade guards themselves held.
[Original evidence and owner review](https://github.com/FlickrGroupAddr/api-cloudflare/blob/7387b14/docs/research/2026-09-06-native-runtime-permission-evidence.md).

Codex initially recommended retaining that strict privilege boundary and
evaluating the existing RDS PostgreSQL fallback with separate runtime and
migration/table-owner identities. The material concern was containment:
arbitrary SQL issued with a native runtime capability can dismantle its own
protection, including after an injection defect. PostgreSQL roles provide an
independent database check when runtime credentials do not carry ownership or
other bypass authority. Neither arrangement makes data undeletable to an
administrator.

Terry judged that extra threat model disproportionate for his private,
single-owner hobby deployment: deployed Worker logic removing its own guards
would indicate a larger application failure. After discussing the tradeoff,
Codex recommended trusting the deployed storage-owning runtime while retaining
ordinary-write guards and behavioral tests. Terry explicitly approved those
updates on 2026-09-11. This records the owner's narrowing of the previously
accepted security requirement, not an assertion that native guards provide
the same isolation as PostgreSQL privileges.

## Decision

1. For the private single-owner deployment, trust the deployed FGA API backend,
   FGA worker, and owning Durable Object code holding a required native storage
   capability. Database-enforced inability of that runtime to remove its own
   guards, change schema, or invoke whole-storage erasure is not an independent
   acceptance prerequisite. Do not require RDS or a custom privilege service
   solely because that broad native capability exists.
2. Preserve permanent exact-pair suppression without expiry and append-only
   protected audit/history behavior. Use database constraints and SQL guards
   to reject ordinary update, delete, replacement, upsert, and cascading-delete
   attempts against protected facts. Application checks alone are insufficient.
   Fixed authorized operations and parameterized values remain required; no
   endpoint may accept caller-selected SQL or expose destructive storage APIs.
3. Ordinary runtime code must not remove/disable those guards, execute schema
   changes, or erase protected storage. Keep migration code and its operator
   invocation outside ordinary request, scheduling, and recovery paths. No
   API, administrative control, retry, retention, migration, or recovery
   workflow may clear suppression to permit another submission. Preserve
   existing controlled decommissioning requirements.
4. Continue least privilege for client authorization, component bindings,
   provider management, secret access, and deployment credentials. If
   PostgreSQL is used, retain its conventional non-owner runtime roles.
   This exception grants no permission to place administrator or deployment
   credentials in ordinary runtimes.
5. Preserve atomic admission, durable FIFO order, dispatch markers, stale-worker
   fencing, fresh moderation checks, hostile-client protection, and
   backup/restore of safety history. Assign each fact one durable authority;
   never assume a transaction spans D1 and Durable Objects. The immutable
   album-binding behavior and authentication/secret lifecycles are unchanged.
6. Amend the private-deployment enforcement clauses of the worker persistence
   contract and FP-BLOCK-009 as described below. They must test ordinary
   destructive statements with guards installed, actual application paths,
   and migration/recovery preservation. A deliberate guard-removal capability
   probe remains evidence of the accepted trust boundary, not a production
   conformance pass or an automatic native-provider failure.
7. Resume D1/Durable Object evaluation against the remaining requirements.
   This decision selects no production storage mapping, claims no production
   adapter pass, and does not resolve the separate Secrets Manager or clock
   questions. Reopen this threat-model decision before public or multi-user
   operation; public source-code visibility alone is not that expansion.

## Scope and amended authority

This ADR narrows ADR 0050's runtime-erasure/privilege preservation gate for the
private deployment and ADR 0046's privilege-based fallback rationale. It amends
the worker persistence contract's native-equivalence wording, Safety and history
relations clause, and acceptance checklist; it also amends FP-BLOCK-009 and the
related role/mutation wording in the fail-polite conformance contract. References
to immutable facts elsewhere retain their behavioral requirements; ordinary
native SQL guards may enforce them under this explicit runtime trust model.
No Flickr behavior or permanent-suppression exception is introduced.

## Consequences and accepted tradeoff

A compromised storage-owning runtime, SQL-injection defect, or bad deployment
that removes guards can cause broader damage than a properly restricted
PostgreSQL role. Triggers, parameterized operations, tests, and backups do not
supply equivalent privilege isolation or guarantee recovery of missing safety
history. Terry accepts that containment limitation for this private deployment
in exchange for avoiding cross-provider networking/identity work or a custom
privileged storage service solely for this requirement.

The retained tests must still catch ordinary data-loss defects and unsafe
resubmission. Migration and restore drills must prove preservation; uncertain
safety history keeps automated writes disabled. The earlier capability reports
remain unchanged and accurately record the stronger boundary they tested.

## Related authority

- [Private MVP](0004-single-user-mvp.md)
- [Permanent suppression](0007-fail-polite-group-submissions.md)
- [Native-first hosted direction](0050-select-cloudflare-and-evaluate-native-storage-first.md)
- [RDS fallback](0046-use-existing-amazon-rds-postgresql.md)
- [Worker persistence contract](../worker-persistence-scheduler-contract.md)
- [Fail-polite conformance](../testing/fail-polite-worker-database-conformance.md)
