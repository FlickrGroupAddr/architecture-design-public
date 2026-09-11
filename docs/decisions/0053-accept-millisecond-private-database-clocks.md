# ADR 0053: Accept millisecond database clocks for the private deployment

Date: 2026-09-11

Status: Accepted by Terry on 2026-09-11

## Context and owner decision

The administrative audit contract required a UTC timestamp with microsecond
precision, while the persistence contract assigns persisted time to the database.
The hosted D1 foundation proof observed a millisecond source clock. Serializing
six fractional digits or storing integer microsecond units does not supply finer
clock resolution. Explicit revisions and sequences already own durable ordering.

Codex recommended accepting the database's millisecond source resolution for
Terry's private hobby deployment instead of adding RDS solely for a finer clock.
Terry approved this recommendation and continued implementation #0007/#0011 on
2026-09-11. The objection to the earlier requirement was its service/maintenance
cost without an identified private-deployment need for finer persisted time.
The accepted tradeoff is that events in one millisecond may share a timestamp.
[Measured evidence and the approved recommendation](https://github.com/FlickrGroupAddr/api-cloudflare/blob/5f128ba/docs/research/2026-09-11-d1-foundation-and-installation-read.md).

## Decision and scope

For the private single-owner deployment, database-generated persisted UTC
timestamps may have millisecond source resolution. This applies to audit,
creation, transition, due and lease times. Six fractional UTC digits remain a
valid serialization; the implementation must truthfully document any lower
three zero digits. Integer microsecond units do not imply microsecond resolution.

The FGA database still supplies every persisted time. Explicit sequence/revision
fields supply durable ordering; clock values need not be unique. This decision
amends the audit timestamp precision clause in the administrative control-plane
contract and clarifies the worker persistence/scheduler contract under ADR 0015.
It does not permit worker wall-clock authority for persisted deadlines.

Atomicity, permanent suppression, guarded history, lease generation fencing,
expiry comparisons and restore requirements are unchanged. The independent live
monotonic moderation-preflight timing rule and its test resolution are unchanged.
Finer database clocks remain valid, but their absence alone does not justify an
AWS service. Hosted conformance and production operational gates remain evidence
requirements; this approval alone does not pass them.

## Hosted evidence after approval

The [fresh D1 foundation proof](https://github.com/FlickrGroupAddr/api-cloudflare/blob/6e18b1a/docs/evidence/foundation-guards-approved-2026-09-11.json)
passes 46 scoped checks under this decision, including database UTC formatting
and source resolution, ordinary SQL guards, migrations, exact export/import
and Time Travel recovery. It fingerprints implementation `308e46f` and this
decision's acceptance commit `0cf54f3`. Temporary resources have confirmed
cleanup. Full scheduling/dispatch conformance and production backup operations
remain separate from this bounded foundation proof.
