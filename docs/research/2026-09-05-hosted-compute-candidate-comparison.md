# Hosted compute candidate comparison

Date: 2026-09-05

Status: Complete historical comparative research for the ADR 0033 re-review.
ADR 0050 now selects Cloudflare; the implementation language remains unselected.
Ticket #0104 found a native Cloudflare immutable-secret-version gap.

Authority: Evidence and recommendation, not an architecture decision. Accepted
ADR 0050 records the later owner choice.

Current direction update, 2026-09-06:
[ADR 0050](../decisions/0050-select-cloudflare-and-evaluate-native-storage-first.md)
records Cloudflare as selected and Durable Objects/D1 as the first storage
evaluation, with RDS PostgreSQL as
fallback. The dated findings and recommendations below remain evidence, not a
current provider-selection veto. The native secret-version issue remains open
for separate owner explanation and review; no credential-safety exception
has been accepted.

Current native-storage evidence, checked 2026-09-06:

- Cloudflare documents SQLite-backed Durable Object storage as transactional
  and strongly consistent within one object. Each object's storage is private
  to that object, supports SQL and explicit transactions, and offers 30-day
  point-in-time recovery. New Durable Object namespaces use this backend.
- Durable Object alarms execute at least once and retry a failing handler. They
  are a plausible due-work wake mechanism, but their delivery is never the
  durable permission to dispatch a Flickr write.
- D1 remains auto-commit for ordinary calls, while `batch()` executes its
  prepared statements as one transaction and rolls the batch back when a
  statement fails.

These capabilities reopen a useful native design space that the earlier
provider ranking did not settle. A user-scoped Durable Object could potentially
keep multiple group partitions inside one transaction boundary for the private
single-user MVP, while D1 could potentially own a different global or derived
surface. That is a hypothesis, not a mapping decision: cross-object atomicity,
single authority, runtime privilege separation, migrations, recovery, and
failure around external dispatch still require executable proof. The
implementation board tracks those proofs individually.

Primary Cloudflare sources, rechecked 2026-09-06:

- [SQLite-backed Durable Object storage](https://developers.cloudflare.com/durable-objects/api/sqlite-storage-api/)
- [Durable Object alarms](https://developers.cloudflare.com/durable-objects/api/alarms/)
- [D1 batch transactions](https://developers.cloudflare.com/d1/worker-api/d1-database/#batch)

## Fixed inputs and scope

This comparison treats the prototype Python implementation as disposable and
compares complete deployable systems rather than isolated compute products. It
uses these current inputs:

- The accepted database baseline is an existing Internet-accessible Amazon RDS
  for PostgreSQL 18.6 instance. Three years of its compute were prepaid. On
  2026-09-05 Terry explicitly permitted D1 to displace that baseline if a
  requirements-first comparison found D1 more attractive. The prepaid compute
  is therefore an advantage rather than a constraint that prejudges the
  comparison. The comparison below did not find grounds to displace RDS, so
  [ADR 0046](../decisions/0046-use-existing-amazon-rds-postgresql.md) remains
  accepted.
- The FGA User UI is a JAMstack application whose static assets are served from
  a CDN on the same public origin as the FGA API backend.
- Versioned `/api/vNNNN/*`, authentication, OAuth, administrative, and health
  routes are server-owned before any static-asset or SPA fallback.
- The FGA database remains authoritative for queue order, due work, fenced
  leases, dispatch markers, and permanent suppression. Provider queues carry
  disposable at-least-once hints only.
- Dynamic Flickr OAuth token/token-secret pairs require immutable managed-secret
  versions selected by an exact FGA database reference. Resolving `latest` is
  not authoritative.
- The public FGA API backend and FGA group-submission worker require distinct
  runtime identities and least-privilege database roles.

The current implementation-language recommendation is strict TypeScript for
hosted code. It is not yet an accepted decision. Cloudflare supplies TypeScript
types derived from the configured Workers runtime, recommends `node-postgres`
for Hyperdrive, and supplies a Workers-native Vitest integration. Terry also
reported that an earlier repository-activity comparison found materially more
Cloudflare investment in the TypeScript surface than the Python and Rust SDKs.
That report is useful directional evidence, but no exact repositories, time
window, or commit counts were preserved here, so it is not independently
reproducible evidence.

Primary language sources, retrieved 2026-09-05:

- [TypeScript on Cloudflare Workers](https://developers.cloudflare.com/workers/languages/typescript/)
- [PostgreSQL drivers for Hyperdrive](https://developers.cloudflare.com/hyperdrive/examples/connect-to-postgres/)
- [Cloudflare Workers Vitest integration](https://developers.cloudflare.com/workers/testing/vitest-integration/)
- [Python package support and limitations](https://developers.cloudflare.com/workers/languages/python/packages/)
- [Django on Python Workers](https://developers.cloudflare.com/workers/languages/python/packages/django/)

## Candidate shapes

| Candidate | Concrete shape |
| --- | --- |
| Cloudflare plus RDS | Worker Static Assets and a public TypeScript FGA API backend; a separately authorized Queue/Cron-triggered FGA group-submission worker; Hyperdrive to RDS |
| Cloudflare plus D1 | The same Worker surfaces with D1 replacing RDS, Hyperdrive, and the cross-provider network path; transactional D1 batches and conditional writes replace PostgreSQL transactions, row locks, and roles |
| AWS | CloudFront and a private S3 asset origin; API Gateway HTTP API and a TypeScript Lambda FGA API backend; SQS and EventBridge-triggered worker Lambdas; RDS Proxy |
| Google Cloud | Cloud CDN and Cloud Storage behind an external Application Load Balancer; TypeScript Cloud Run API and worker services; Cloud Tasks and Cloud Scheduler |

The three shapes keep the language constant so the comparison measures hosting
tradeoffs rather than repeating the language selection.

## Cloudflare Workers with RDS

### Best case

Cloudflare most directly matches the desired public product shape. Worker Static
Assets can serve the JAMstack build from the edge and selectively run the Worker
first for server-owned paths. The browser sees one public origin without a
separate API gateway or load balancer. Cloudflare Queues supplies at-least-once
hints, Cron Triggers supplies the minutely sweep, and both queue and scheduled
invocations permit 15 minutes of wall time. Those limits comfortably contain
the current 45-second FGA group-submission worker deadline.

Hyperdrive provides transaction-mode PostgreSQL pooling, while Placement Hints
can place `fetch()` execution near the known AWS region. At private-MVP traffic,
this is expected to have the smallest resource inventory and quiet-traffic cost
floor.

### Material objections and gates

1. Hyperdrive currently documents PostgreSQL versions through 17.x as known
   supported, not the selected RDS PostgreSQL 18.6 engine. Exact production-like
   transaction and fencing conformance is mandatory; ticket #0102 owns this
   gate.
2. Cloudflare placement applies to `fetch()` handlers, not directly to queue or
   scheduled handlers. The background worker performs several latency-sensitive
   database transactions. Direct Hyperdrive access must be measured against the
   simplest supported trigger-to-placed-backend topology; ticket #0103 owns this
   gate.
3. Hyperdrive query caching defaults to a 60-second maximum age plus a
   15-second stale-while-revalidate interval and does not invalidate cached reads
   after writes. Authorization, sessions, credential authority, leases, gates,
   queue order, dispatch state, permanent blocks, and worker recovery must never
   receive stale authority. Ticket #0106 owns the deliberate caching boundary:
   the safe default is no query cache, while any explicitly classified
   non-authoritative read needs measured benefit, bounded staleness, documented
   invalidation/failure behavior, and conformance evidence before opt-in.
4. The published Cloudflare Secrets Store model replaces an edited value in all
   consuming services. Ticket #0104 found no native immutable version that a
   runtime can retrieve by an exact FGA database reference: the binding names a
   mutable secret and exposes parameterless `get()`. The
   [completed gate review](2026-09-05-cloudflare-secret-versioning-gate.md)
   records why unique secret names and Worker versions would require a custom
   deployment coordinator. Under accepted ADR 0017 this mandatory gate fails.
5. Hyperdrive requires a public allowlist or a Cloudflare Tunnel for private
   connectivity. Unrestricted PostgreSQL ingress is unacceptable. Ticket #0105
   owns the least-privilege network choice and its availability, lifecycle, and
   cost evidence.

Primary Cloudflare sources, retrieved 2026-09-05:

- [Worker and static-asset routing](https://developers.cloudflare.com/workers/static-assets/routing/worker-script/)
- [Cloudflare Queues delivery guarantees](https://developers.cloudflare.com/queues/reference/delivery-guarantees/)
- [Cloudflare Queues and Worker invocation limits](https://developers.cloudflare.com/queues/platform/limits/)
- [Hyperdrive supported databases](https://developers.cloudflare.com/hyperdrive/reference/supported-databases-and-features/)
- [Hyperdrive pooling behavior](https://developers.cloudflare.com/hyperdrive/concepts/how-hyperdrive-works/)
- [Hyperdrive query caching](https://developers.cloudflare.com/hyperdrive/concepts/query-caching/)
- [Workers placement](https://developers.cloudflare.com/workers/configuration/placement/)
- [Hyperdrive networking](https://developers.cloudflare.com/hyperdrive/configuration/firewall-and-networking-configuration/)
- [Cloudflare Secrets Store edit behavior](https://developers.cloudflare.com/secrets-store/manage-secrets/how-to/)

Cloudflare remains the highest-upside product shape, but it is not an eligible
private-MVP candidate under the accepted exact managed-secret-version contract.

## Cloudflare Workers with D1

Terry explicitly placed D1 back in scope on 2026-09-05 if it proved more
attractive than the accepted RDS baseline. The legacy TypeScript spike is useful
evidence for this shape: it deployed one Worker, D1, Cron Triggers, and Durable
Objects, and used transactional `D1Database.batch()` calls for related writes.
Its OAuth and device-link Durable Objects also remain useful independently of
the durable relational database choice; their single authoritative lifecycle
avoids Workers KV's eventual-consistency boundary for short-lived
authorization state.

D1 would remove the RDS 18.6/Hyperdrive compatibility gate, the Cloudflare-to-
RDS network gate, and the background-handler database-placement concern. Its
10-GB paid-plan database limit is ample for the owner-only deployment, every
database is single-threaded and processes queries serially, foreign keys are
enforced, transactional batches roll back as a unit, and Time Travel supplies
minute-granularity point-in-time recovery for 30 days on the paid plan. The
owner-only workload does not make D1's per-database write serialization a
throughput objection.

The mismatch is in safety and privilege mechanics, not capacity:

1. The documented Worker binding is auto-commit and exposes prepared
   statements plus a transactionally executed `batch()`; it does not expose a
   conventional interactive transaction in which application code can lock,
   inspect, branch, and write. The FGA persistence contract's dependent
   multi-table transitions would have to become carefully repeated conditional
   predicates, trigger logic, or a custom storage Worker rather than direct,
   ordinary PostgreSQL transactions.
2. A D1 database serializes the entire database rather than supplying
   PostgreSQL row locks. That is safe and adequate at current volume, but it
   changes the proof and implementation of partition-local locking, counter
   allocation, fenced claim/result transactions, and multi-partition Phase 6
   handoff.
3. The reviewed D1 documentation supplies database-level Worker bindings and
   account-level `D1 Read`/`D1 Edit` administration permissions. It does not
   document PostgreSQL-like table, column, or role grants. This conclusion is
   an inference from the documented surface. Preserving the current rule that
   runtime identities cannot update or delete permanent blocks would require a
   custom method-limited storage Worker, schema triggers that the bound runtime
   can technically alter, or a deliberate weakening of the defense-in-depth
   requirement.
4. D1 read replication is asynchronous. Safety-sensitive reads would have to
   stay on the primary or start a D1 Session with `first-primary` and propagate
   bookmarks; an unconstrained replicated read can be arbitrarily stale.
   Ticket #0106 evaluates whether any non-authoritative read merits that added
   cache/replica consistency machinery in the owner-only deployment.
5. The legacy spike's built code is materially weaker than the current
   persistence contract. It has no current lease generation, durable preflight
   record, pre-dispatch marker, or crash-recovery boundary comparable to ADR
   0015. Reusing its D1 choice would not reuse a proven implementation of those
   requirements.

Application-encrypted Flickr credentials in D1 or RDS remain a separate design
option, but ticket #0104 did not accept it as a provider workaround. The spike
demonstrates a single AES-GCM key path and documents, but does not implement, a
timestamped keyring. That option could make credential activation and deletion
atomic with the FGA database link transaction, but it would reopen accepted ADR
0017 and move cryptographic rotation, re-encryption, and recovery into
application code.

On current evidence, D1 is not more attractive than the prepaid RDS PostgreSQL
18.6 baseline. It trades away conventional transaction composition and
database-enforced runtime roles precisely where FGA's fail-polite boundary is
most demanding. Reconsider D1 if Cloudflare documents method- or table-scoped
runtime database authority and a suitable transaction API, or if Terry
deliberately accepts the custom storage-service and application-encryption
trade after the required architecture pushback. Until then, D1 is a legitimate
reconsidered alternative, not the selected persistence layer.

Primary D1 and spike sources, retrieved 2026-09-05:

- [D1 Worker binding and transactional batches](https://developers.cloudflare.com/d1/worker-api/d1-database/)
- [D1 limits and single-threaded database behavior](https://developers.cloudflare.com/d1/platform/limits/)
- [D1 foreign-key enforcement](https://developers.cloudflare.com/d1/sql-api/foreign-keys/)
- [D1 read-replication consistency](https://developers.cloudflare.com/d1/best-practices/read-replication/)
- [D1 Time Travel](https://developers.cloudflare.com/d1/reference/time-travel/)
- [Cloudflare API-token permission groups](https://developers.cloudflare.com/fundamentals/api/reference/permissions/)
- [Legacy spike architecture decisions](https://github.com/FlickrGroupAddr/backend-api/blob/64a900faecb3cde303c8b0441164e91982a2691f/docs/architecture/DECISIONS.md)
- [Legacy spike D1 persistence implementation](https://github.com/FlickrGroupAddr/backend-api/blob/64a900faecb3cde303c8b0441164e91982a2691f/src/db/requests.ts)
- [Legacy spike key-rotation design](https://github.com/FlickrGroupAddr/backend-api/blob/64a900faecb3cde303c8b0441164e91982a2691f/docs/architecture/KEY-ROTATION-NOTES.md)

## AWS Lambda

### Best case

AWS removes nearly every uncertain database and secret boundary. TypeScript
Lambdas can connect privately to the existing RDS instance in the same VPC.
RDS Proxy supports PostgreSQL 18 and supplies the production connection pool
that AWS recommends for frequent short Lambda connections. AWS Secrets Manager
can retrieve one exact immutable `VersionId`. SQS event-source mappings provide
at-least-once hints, EventBridge Scheduler can invoke the due sweep, and IAM can
separate API, worker, migration, and secret authority.

This candidate has the highest probability of passing the database, secret,
and worker conformance gates without a provider-specific workaround.

### Material objections

The complete deployment is substantially larger than one Lambda. It needs a
CloudFront distribution, private S3 origin, API Gateway, multiple Lambda entry
points, VPC subnets and security groups, RDS Proxy, SQS, EventBridge Scheduler,
Secrets Manager, and observable deployment configuration. CloudFront must also
route the server-owned paths away from the static origin, duplicating part of
the application's route knowledge at the edge. The generated-route and preview
conformance gate is therefore essential.

A Lambda attached to the RDS VPC does not automatically retain public Internet
access. The conventional IPv4 path to Flickr uses private subnets and a NAT
gateway. NAT and RDS Proxy add recurring cost outside the prepaid RDS compute.
Avoiding them with a hand-operated NAT instance, broad RDS exposure, or
uncontrolled direct database connections would exchange visible cost for
surprising operational or security risk.

Primary AWS sources, retrieved 2026-09-05:

- [Using Lambda with Amazon RDS](https://docs.aws.amazon.com/lambda/latest/dg/services-rds.html)
- [RDS Proxy PostgreSQL version availability](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RDS_Fea_Regions_DB-eng.Feature.RDSProxy.html)
- [Internet access for VPC-connected Lambda functions](https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc-internet.html)
- [Lambda and SQS delivery behavior](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html)
- [AWS Secrets Manager `GetSecretValue`](https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html)

AWS is the highest-confidence candidate and has the larger resource and
operational surface.

## Google Cloud Run

Cloud Run services, not Cloud Run functions, are the appropriate Google Cloud
comparison. The hosted component is a versioned application with shared routing,
middleware, authentication, PostgreSQL transactions, and separately authorized
worker execution; it is not naturally a collection of unrelated functions.

### Best case

Cloud Run supplies the most conventional runtime: a normal Node.js container,
ordinary PostgreSQL libraries, explicit concurrency and instance limits,
scale-to-zero behavior, immutable revisions, and request timeouts up to 60
minutes. Cloud Tasks and Cloud Scheduler have the at-least-once behavior that
the FGA database-authoritative design expects. Google Secret Manager retrieves
an exact numbered secret version. Local container execution also gives this
candidate the strongest runtime parity and the least restricted library surface.

### Material objections

Once the FGA database moved from the proposed Cloud SQL candidate to fixed AWS
RDS hosting, Google Cloud lost its architectural center of gravity. Every
database transaction crosses providers. Restricting RDS ingress to a stable
Google source address requires Direct VPC egress, a VPC, Cloud Router, Cloud NAT,
and a reserved address. The public edge separately requires Cloud Storage, Cloud
CDN, an external Application Load Balancer, a URL map, and a serverless network
endpoint group.

This combines an AWS-sized service inventory with cross-cloud database latency,
failure coupling, and network cost, while gaining neither Cloudflare's compact
edge topology nor AWS's database locality.

Primary Google Cloud sources, retrieved 2026-09-05:

- [Cloud Run overview](https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run)
- [Cloud Run request timeouts](https://docs.cloud.google.com/run/docs/configuring/request-timeout)
- [Static Cloud Run outbound addresses](https://docs.cloud.google.com/run/docs/configuring/static-outbound-ip)
- [Cloud Tasks delivery behavior](https://docs.cloud.google.com/tasks/docs/dual-overview)
- [Cloud Scheduler delivery behavior](https://docs.cloud.google.com/scheduler/docs/overview)
- [Secret Manager exact-version access](https://docs.cloud.google.com/secret-manager/docs/access-secret-version)
- [Application Load Balancer URL maps](https://docs.cloud.google.com/load-balancing/docs/url-map-concepts)

Google Cloud is technically sound but currently dominated by the other two
candidates unless conventional unrestricted container execution becomes more
valuable than provider compactness and database locality.

## Provisional conclusion

The current deployable-shape order is:

1. AWS Lambda with RDS as the leading candidate that conforms to the currently
   accepted database and exact managed-secret-version contracts;
2. Google Cloud Run only if the project deliberately prioritizes its container
   runtime enough to accept the cross-cloud topology;
3. Cloudflare TypeScript Workers with RDS only if Cloudflare adds exact runtime
   secret-version retrieval or Terry explicitly reopens ADR 0017; and
4. Cloudflare TypeScript Workers with D1 only after that same credential
   decision plus a persistence redesign that proves the fail-polite transitions
   and replaces or deliberately relaxes PostgreSQL role enforcement.

This can also be stated as four different optimization targets:

- Cloudflare offers the best product fit and highest upside, but has failed one
  mandatory accepted-architecture gate.
- AWS offers the best infrastructure fit and highest pre-probe confidence.
- D1 offers the smallest Cloudflare-only topology but presently requires the
  most custom persistence and privilege design.
- Google Cloud offers the most conventional runtime but no current compensating
  system-level advantage.

Candidate order is not provider acceptance. ADR 0033 remains Proposed until
Terry makes an explicit owner decision after the deliberate re-review. Tickets
#0102, #0103, and #0105 are unnecessary unless Terry first changes the
credential decision or Cloudflare's documented secret surface changes.
