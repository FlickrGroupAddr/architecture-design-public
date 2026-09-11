# Hosted deployment contract

Last updated: 2026-09-11

Status: Historical Google Cloud proposal under superseded ADR 0033.
Accepted ADR 0050 selects Cloudflare with native storage evaluated first;
the Cloudflare deployment contract and executable acceptance remain pending.

## Current decision boundary

[ADR 0050](decisions/0050-select-cloudflare-and-evaluate-native-storage-first.md) records Terry's 2026-09-06 correction:
Cloudflare is selected; Durable Objects and D1 are the first storage and
coordination approach to evaluate. RDS PostgreSQL is the fallback when native
services cannot meet the requirements. Accepted
[ADR 0051](decisions/0051-trust-private-storage-runtime-with-guarded-writes.md) narrows the private
runtime privilege-isolation gate: native SQL guards and trusted deployed code
are acceptable while destructive application behavior remains prohibited.
Historical privilege comparisons below must be read with that amendment.

The Google Cloud resources, libraries, costs, and topology below are historical
evidence, not accepted Cloudflare configuration. Current proofs must establish
the component mapping, authoritative persistence, identity and privileges,
scheduling, routing/TLS, recovery, operations, and bounded preview costs.
Hyperdrive work is conditional on using the RDS fallback.

The native secret-version issue remains open for separate owner explanation
and review. This document claims no production provider pass or exception to
accepted safety requirements.

## Google Cloud candidate summary

The candidate private production deployment would use Google Cloud in `us-east4` and a
separate Google Cloud project for preview. Terraform declares the provider
resources. One immutable OCI image supplies two narrowly configured Cloud Run
services:

- the public FGA web service contains the FGA HTTPS handlers, FGA API backend,
  FGA User UI static assets, and administrative handlers on one origin; and
- the internal FGA group-submission worker contains the due-sweep and partition
  claim/attempt entry points.

A global external Application Load Balancer, Google-managed certificate, and
one serverless network endpoint group are the only public ingress. The URL map
sends every application path to the public FGA web service; it does not
duplicate application route ownership. The FGA web service resolves registered
handlers before static or administrative-shell fallback. The service uses
`internal-and-cloud-load-balancing` ingress, and its default `run.app` URL is
disabled. HTTP redirects to HTTPS.

The FGA database is a private-IP Cloud SQL for PostgreSQL 18 Enterprise
instance. Cloud Run Direct VPC egress supplies the network path; the Cloud SQL
Python Connector and automatic IAM database authentication supply connection
verification and short-lived database credentials. Cloud Tasks carries
best-effort post-commit partition hints to the internal worker. Cloud Scheduler
invokes the internal due-sweep once per minute. Neither service owns queue
truth; the FGA database contract remains authoritative.

The proposal is recorded by [ADR 0033](decisions/0033-deploy-on-google-cloud.md).
No production service, migration, Terraform module, preview deployment, or
provider account is present in this architecture repository. This document
therefore preserves candidate adapters and values without claiming selection or an executable
deployment, route-conformance, TLS, worker/database, backup/restore, or rollback
pass.

## Original Google Cloud comparison

This section preserves the comparison made on 2026-08-26 from provider
documentation. It predates the fixed RDS decision and is superseded for current
candidate ordering by the dated comparison above. The
private MVP needs more than a place to run one HTTP handler: it needs ordinary
PostgreSQL transactions and row fencing, a versioned managed-secret lifecycle,
separate web and worker identities, an authenticated at-least-once hint path,
a minutely recovery sweep, an exportable edge configuration, an isolated
preview, and control over the public TLS policy.

| Candidate | Fit and material tradeoff |
| --- | --- |
| Google Cloud | Cloud Run, Cloud SQL for PostgreSQL, Cloud Tasks, Cloud Scheduler, Secret Manager, Artifact Registry, and the global external Application Load Balancer satisfy those boundaries directly. The deployment is conventional and fully declarative, but Cloud SQL and the load balancer impose a real fixed cost. |
| AWS | ECS/Fargate or App Runner, RDS for PostgreSQL, SQS, EventBridge Scheduler, Secrets Manager, and an Application Load Balancer can satisfy the contract. The equivalent private networking, task/runtime, load-balancer, queue, scheduler, secret, and IAM surface is larger for this one-owner deployment and adds no required capability. |
| Azure | Container Apps and Jobs, Flexible Server for PostgreSQL, Service Bus, Key Vault, and Front Door or Application Gateway can satisfy the contract. It has the same multi-resource shape without a compensating FGA requirement or existing owner integration. |
| Render | Web services, background workers, cron jobs, and managed PostgreSQL are operationally attractive. Preview environments require a paid workspace, secrets are deployment environment values/files rather than the selected runtime version-reference lifecycle, and the documented edge does not expose the required minimum-TLS policy/export evidence. Satisfying those gaps would add application secret encryption or another provider and weaken the single-provider simplicity. |
| Cloudflare | Workers, Queues, Cron Triggers, Secrets, and D1 form a compact edge deployment. Terry explicitly permitted D1 reconsideration on 2026-09-05. The dated comparison found its transactional batches, global single-writer serialization, and recovery adequate in capacity but found no documented PostgreSQL-like runtime table/role grants or conventional interactive transaction API. D1 therefore remains in scope but not selected: adopting it would require a custom persistence and privilege redesign at the fail-polite boundary. |

The original comparison did not treat vendor breadth as a benefit by itself. It
proposed Google Cloud because that then-self-contained candidate met every
already-decided contract with mature managed components and the least custom
security or persistence machinery among the candidates assessed at that time.

Primary capability references:

- [Cloud Run overview](https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run),
  [ingress controls](https://docs.cloud.google.com/run/docs/securing/ingress),
  and [global external Application Load Balancer with a serverless NEG](https://docs.cloud.google.com/load-balancing/docs/https/setup-global-ext-https-serverless)
- [Cloud SQL for PostgreSQL instance settings](https://docs.cloud.google.com/sql/docs/postgres/instance-settings)
  and [operational guidance](https://docs.cloud.google.com/sql/docs/postgres/operational-guidelines)
- [Cloud Tasks queue controls](https://docs.cloud.google.com/tasks/docs/configuring-queues)
  and [Cloud Scheduler cron syntax](https://docs.cloud.google.com/scheduler/docs/schedule-run-cron-job)
- [Secret Manager](https://cloud.google.com/security/products/secret-manager)
- [AWS App Runner](https://docs.aws.amazon.com/apprunner/latest/dg/what-is-apprunner.html),
  [RDS for PostgreSQL](https://aws.amazon.com/rds/postgresql/), and
  [Amazon SQS](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html)
- [Azure Container Apps jobs](https://learn.microsoft.com/en-us/azure/container-apps/jobs),
  [Azure Database for PostgreSQL](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/overview),
  and [Azure Service Bus](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-queues-topics-subscriptions)
- [Render preview environments](https://render.com/docs/preview-environments),
  [background workers](https://render.com/docs/background-workers), and
  [environment values and secret files](https://render.com/docs/configure-environment-variables)
- [Cloudflare D1 limits](https://developers.cloudflare.com/d1/platform/limits/),
  [Queues delivery behavior](https://developers.cloudflare.com/queues/reference/how-queues-works/),
  and [Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/)

## Cost boundary

Cost is a release input, not a promise embedded in application behavior. At
private-MVP traffic, Cloud Run request-based compute, Cloud Tasks, one Cloud
Scheduler job, Secret Manager access, logging, and artifact storage may remain
mostly within current free allowances. Production nevertheless has two fixed
cost drivers:

- the global forwarding-rule tier is currently USD 0.025 per hour for the first
  five global forwarding rules, about USD 18.25 for a 730-hour month, before
  traffic and Internet egress; and
- the dedicated high-availability Cloud SQL instance, its storage, backups,
  and network path run continuously and dominate the estimate.

The implementation pull request **MUST** attach a dated Google Cloud Pricing
Calculator export for `us-east4`, including production and one representative
preview-gate run. It **MUST** set monthly billing budgets and alerts before
creating production resources. A rough planning range of USD 120–220 per month
for the quiet production deployment is deliberately conservative and is not a
quote. It includes the high-availability database floor and load balancer but
excludes unusual egress, log growth, taxes, support, and domain registration.
Current provider pricing is authoritative:
[Cloud Run pricing](https://cloud.google.com/run/pricing),
[Cloud SQL pricing](https://cloud.google.com/sql/pricing),
[Cloud Load Balancing pricing](https://cloud.google.com/load-balancing/pricing),
[Cloud Scheduler pricing](https://cloud.google.com/scheduler/pricing), and
[Secret Manager pricing](https://cloud.google.com/secret-manager/pricing).

Preview is ephemeral. The route/deployment gate creates or updates its isolated
resources, runs the exact-build checks, retains sanitized evidence, and destroys
idle preview compute and database resources through Terraform after the
retention window. It never reuses production data or secrets. Cost reduction
must not replace the production database with a shared-core instance: Google
documents shared-core Cloud SQL types as development/test only and outside the
SLA.

## Projects, regions, and public routing

Production and preview would use separate Google Cloud projects and separate
Google web-application client IDs. Production application and data resources
would reside in `us-east4`.
Terraform pins provider versions and declares all resources, IAM bindings,
networking, timeouts, scaling limits, database flags, secret names, and alert
policies. State uses a separately access-controlled remote backend; it contains
no secret values.

Production DNS for `flickrgroupaddr.com` targets one global external Application
Load Balancer. Its URL map has one default serverless NEG for the FGA web
service. It does not split `/api`, callbacks, assets, and the administrative
shell into independent provider matchers. That boring topology makes the
application route registry authoritative while still providing a stable HTTPS
edge and an exportable effective URL map.

The load balancer uses a Google-managed certificate and an SSL policy with the
`RESTRICTED` profile and minimum TLS 1.3. The exact Lightroom Classic and browser
compatibility/scanner gate in
[FGA HTTPS-edge TLS deployment acceptance](operations/tls-edge-acceptance.md)
still controls launch. If the real client cannot negotiate, changing the
minimum requires the explicit exception process in that contract; provider
selection is not permission to relax it silently.

The preview host is `preview.flickrgroupaddr.com`. It uses the same Terraform
module, route inventory, container image digest, entry points, and database
migrations as the candidate production release. Its project, database, service
accounts, Secret Manager secrets, Google client ID, allowed origins, login URI,
and generated test data are isolated. It has no production Flickr consumer
secret or user token and cannot call live Flickr.

## Runtime and application libraries

The hosted repository uses the latest stable CPython release supported by the
selected dependencies; the initial target is CPython 3.14.7. Astral `uv` owns
the environment, dependency resolution, and committed lock. The OCI build uses
the exact locked interpreter and packages, runs as a non-root user, and emits a
single image digest for both services.

The conventional application stack is:

- Django 5.2 LTS at the latest compatible patch for routing, middleware,
  request/cookie integration, CSRF, and administrative HTML/API handlers;
- the maintained Google Auth Library for Python at a compatible locked release
  for Google ID-token signature/claim validation and bounded current-key use;
- PostgreSQL 18 with the maintained Django PostgreSQL backend and adapter; and
- the maintained Google Cloud Python libraries for Cloud SQL, Cloud Tasks,
  Secret Manager, logging, and identity integration.

The implementation records each exact version, license, maintenance check, and
dependency scope next to the lock update. Django's BSD-3-Clause and Google Auth
Library's Apache-2.0 licenses are compatible with FGA's MIT boundary. No
application component implements JWT signature validation, password
authentication, CSRF, database pooling, or cloud request signing from scratch.

The maintained framework boundaries are documented by the
[Django 5.2 release notes](https://docs.djangoproject.com/en/5.2/releases/5.2/),
[Django security documentation](https://docs.djangoproject.com/en/5.2/topics/security/),
[Google's server-side ID-token validation guide](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token),
and the [Google Auth Library for Python](https://google-auth.readthedocs.io/).

The web service uses the stable Cloud Run HTTP startup probe at
`/healthz/startup` and liveness probe at `/healthz/live` with the exact settings
in the accepted [health and diagnostics
contract](operations/health-and-diagnostics.md). Public responses are fixed,
unauthenticated, and non-identifying; the accepted authenticated deployment
resource owns richer sanitized state. The current Preview Cloud Run readiness
probe is not a deployment dependency. Startup already proves initial readiness,
while liveness never calls the database or another external dependency.

Terraform HCL would be used because it is the candidate provider ecosystem's
declarative infrastructure language, not repository orchestration. Repository
build, validation, evidence, backup-verification, and deployment wrapper scripts
remain Python. The frontend loads Google's supported GIS JavaScript library
directly from `https://accounts.google.com/gsi/client`; self-hosting that
identity library is unsupported and would miss Google's security and
compatibility updates.

## Administrative identity

Accepted ADR 0039 selects direct Google Identity Services authentication. The
[authoritative tab-1 interaction map](decisions/0041-use-clean-room-authentication-tabs-as-interaction-authority.md)
controls the depicted browser-session happy path; this provider candidate adds
deployment detail without changing it. The
JAMstack frontend uses Google's supported GIS client and exact configured web
client ID, origin, and FGA Google Login Endpoint URI. GIS posts `credential`
and matching cookie/body `g_csrf_token` values to that endpoint. The FGA API
backend compares the CSRF pair before using the maintained Google library and a
bounded cache of Google's current JWKS to validate trusted key/algorithm,
signature, audience, issuer, and applicable time claims.

A hosted timer invokes the FGA JWKS refresh worker outside login requests. The
worker refreshes the shared cache by the earlier of six hours after the
preceding successful refresh and a safety margin before Google's published
freshness expiry. An admitted, CSRF-checked login naming an unknown signing key
ID may wait for one bounded, coalesced refresh and retries key selection once;
ordinary logins do not call Google for keys.

The private administrative deployment allowlists Terry's validated Google
`sub`; email and other profile claims are not administrator identity. The
former Auth0 tenant, client secret, Action runtime, custom passkey claim, code
exchange, and PKCE are absent. Accepted ADR 0043 uses GIS's supported nonce and
button-state inputs for a five-minute transaction bound to the current FGA
browser session. It proves a new Google assertion for the same account and does
not claim the rejected passkey step-up's stronger assurance.

The FGA API backend maps canonical Google issuer plus validated `sub` to the
opaque internal `fgaUserId`, generates an opaque 256-bit session token, returns it only
in the `__Host-fga_admin` `Secure`, `HttpOnly`, `Path=/`, `SameSite=Strict`
cookie with no `Domain` and `Max-Age=86400`, and stores only its unsalted
`SHA2-256` digest as the lookup key. The purpose-built FGA session record stores
`fgaUserId`, validated `sub`, only required profile fields, and explicit session metadata;
it stores neither the plaintext token nor Google tokens or the complete decoded
claim map. Identity mapping, session creation, and the sanitized successful
login audit commit atomically before the cookie is returned. The server-side session has the same non-sliding 24-hour absolute
expiry and no shorter idle timeout. A separate 256-bit synchronizer CSRF value
and exact-origin check protect unsafe administrative requests. Signed-cookie
sessions are disabled.

## Database and secret boundaries

Production uses Cloud SQL for PostgreSQL 18 Enterprise with:

- one dedicated high-availability instance in `us-east4` with 1 vCPU and
  3.75 GiB memory initially;
- 20 GiB SSD, automatic storage increase, regional availability, automated
  backups, point-in-time recovery, retained transaction logs, and deletion
  protection;
- private IP only, required TLS through the Cloud SQL Connector, and automatic
  IAM database authentication; and
- alerts for CPU, memory, storage, connections, replication/availability,
  backup failure, oldest transaction, and application error rate.

The smallest dedicated shape is a starting limit, not a capacity claim. Load,
crash, backup/restore, and conformance evidence must pass before launch. Restore
drills create a separate instance and prove schema head, permanent-block
survival, audit retention, dispatch-marker recovery, and application read-only
inspection before deletion. A backup is not treated as valid merely because a
scheduled backup job reported success.

Runtime database principals are distinct:

| Principal | Authority |
| --- | --- |
| `fga_api` | Ordinary API/admission/session/audit transactions; no schema DDL and no permanent-block update/delete |
| `fga_worker` | Claim, fenced attempt/result, gate, event, and due-row transactions; no schema DDL and no permanent-block update/delete |
| `fga_migrator` | Migration-only DDL/DML during a controlled release; absent from both running services |
| `fga_backup_verifier` | Time-bounded read-only access to a restored drill instance |

The API and worker Cloud Run services have separate service accounts. The
worker identity cannot administer Google OAuth client configuration, deploy infrastructure, write secret
versions, or serve public traffic. The web identity cannot invoke a Flickr add
through a direct worker bypass. Deployment automation can impersonate the
migration identity only in the controlled migration job.

Secret Manager holds the Flickr consumer secret, Django installation-wide
signing key, limiter-key secret, and each dynamic Flickr
OAuth token/token-secret pair. The FGA web revision binds the Django key by an
exact numeric version resource and validates its canonical 32-byte CSPRNG
payload before readiness under the [session-signing key
contract](operations/session-signing-key.md); `latest`, arbitrary text, a
process-generated fallback, and worker access are prohibited. A successful
Flickr link exchange adds an immutable
secret version, then stores its exact resource/version reference in the FGA
database compare-and-set transaction. The FGA group-submission worker resolves
only the active reference; it never asks for `latest`. Disabling or destroying
a superseded version occurs only after the database no longer authorizes it and
the lifecycle contract permits cleanup. Secret values never enter Terraform
state, Cloud Run environment variables, build arguments, task payloads, logs,
or database columns.

## Web and worker configuration

Initial production values are fixed and emitted into deployment configuration
and generated application contracts:

| Setting | Selected value |
| --- | --- |
| `max_group_ids_per_batch` | `60` |
| `existing_photo_proof_max_age` | `15 seconds` |
| Web Cloud Run service | request-based billing; 1 vCPU; 512 MiB; concurrency `8`; minimum instances `0`; maximum instances `2`; request timeout `30 seconds`; maximum five database connections per instance |
| Worker Cloud Run service | request-based billing; 1 vCPU; 512 MiB; concurrency `1`; minimum instances `0`; maximum instances `2`; request timeout `60 seconds`; maximum three database connections per instance |
| Active heads per partition claim | `1` |
| Worker internal invocation deadline | `45 seconds` |
| Fenced database lease interval | `60 seconds` |
| Flickr membership GET deadline | `10 seconds` |
| Flickr moderation GET deadline | `10 seconds` |
| Flickr add POST deadline | `10 seconds` |
| Result/lease release margin | `5 seconds` |
| Minimum remaining lease before moderation GET | strictly greater than `30 seconds` |
| Due-sweep cadence | every minute (`* * * * *`) |
| Cloud Tasks dispatch deadline | `50 seconds` |
| Cloud Tasks queue | maximum concurrency `2`; maximum dispatch rate `2/second`; maximum attempts `5`; exponential backoff from `5` to `60 seconds` |

`max_group_ids_per_batch=60` is FGA's whole-request courtesy and transaction
bound. It is not a claim that every Flickr account or group accepts 60 additions
or that Flickr will never change an upstream limit. The FGA LrC plug-in refuses
an over-limit whole selection; the FGA API backend never slices it.

`existing_photo_proof_max_age=15 seconds` bounds the interval from the FGA API
backend's completed, validated owner/public observation to binding commit. The
positive value is short enough to avoid presenting an old selector observation
as authority while allowing a normal same-session choice and request. It does
not make Flickr state atomic.

One head per claim is deliberately obvious. It bounds every invocation to one
membership GET and, when needed, one immediately adjacent moderation GET/add
pair. The 45-second internal deadline leaves 15 seconds for Cloud Run shutdown,
response, and cleanup; the 50-second Cloud Tasks deadline remains below the
60-second service timeout. The FGA group-submission worker refuses to begin the
moderation GET unless more than 30 lease seconds remain, providing room for the
10-second GET, sub-second freshness boundary, 10-second POST, and 5-second
commit margin. It never extends a lease after `dispatch_started` to authorize
another attempt.

## Hint, sweep, and identity flow

After a group-submission transaction commits, the FGA API backend may enqueue
one Cloud Tasks message containing only the opaque partition ID, committed wake
revision, correlation ID, and schema version. Cloud Tasks signs an OIDC token as
the dedicated task-invoker service account. The worker verifies the exact
issuer, audience, and service-account subject before treating the message as a
hint. A duplicate, delayed, reordered, malformed, or retry-exhausted task changes
no authority. The minutely database sweep recovers the partition independently.

Cloud Scheduler makes one authenticated request per minute to the internal
due-sweep endpoint as a different scheduler-invoker service account. The FGA
group-submission worker queries indexed FGA database due rows using database
current time and enqueues bounded claim hints. It also discovers expired
leases. Scheduler delivery and Cloud Tasks are at least once; database natural
keys, wake revisions, due rows, and fenced leases make duplicates harmless.
Neither request accepts arbitrary SQL, Flickr IDs, due times, lease revisions,
or a bypass flag.

The worker `run.app` endpoint remains enabled because Cloud Tasks and Cloud
Scheduler invoke it, but Cloud Run ingress is `internal` and IAM denies all
other callers. The public load balancer has no backend or route to the worker.

## Delivery, migration, rollback, and evidence

Artifact Registry stores content-addressed OCI images. CI builds once, scans
the image and dependency lock, runs all application and production-adapter
tests, and promotes the same digest. Cloud Run revisions use no mutable image
tag as release evidence. Terraform plan and apply are separate reviewed steps.

The production sequence is:

1. build and retain one image digest plus dependency/license evidence;
2. create/update isolated preview infrastructure;
3. run migrations through the migration identity;
4. run route, TLS, fail-polite worker/database, backup/restore, and smoke gates;
5. retain sanitized evidence bound to image digest, migration head, Terraform
   plan digest, provider export digest, and preview revision;
6. apply production infrastructure changes;
7. run compatible migrations before traffic changes;
8. deploy the worker and web revisions at zero traffic, prove the web startup/
   liveness and authenticated deployment-resource checks plus worker invocation
   health, then shift traffic deliberately; and
9. verify metrics, gates, queue age, secret references, and route probes.

Rollback means routing the previous tested image revision only when its database
contract remains forward-compatible with the current migration head. A
destructive or backward-incompatible migration requires expand/migrate/contract
across releases and cannot use instant application rollback as a fiction. Every
rollback candidate reruns preview route and database compatibility gates.

The route adapter derives Terraform URL-map inputs from the compiled route
inventory even though the selected first deployment has one default backend. It
captures the Terraform plan/state projection plus effective exports from
`gcloud compute url-maps describe` and
`gcloud run services describe --format=export`. The preview adapter deploys the
same image digest to `preview.flickrgroupaddr.com` and drives the complete
black-box matrix through that public load balancer. A hand-written provider
fixture, Cloud Run service URL, or handler-only test cannot satisfy the gate.

Cloud Logging and Cloud Monitoring receive structured sanitized logs, metrics,
and alerts. Log sinks exclude credentials, cookies, authorization/signature
headers, Flickr response bodies, photo metadata, and task OIDC tokens. Initial
alerts cover public 5xx/authentication anomalies, paused Flickr gates, queue
age, exhausted hint retries, expired/stuck leases, dispatch ambiguity, permanent blocks,
database/storage/backup health, secret access denial, route/TLS drift, and
budget thresholds.

## Required implementation evidence

The hosted implementation cannot call this decision complete until it records:

- the exact locked CPython, Django, Google Auth Library, PostgreSQL adapter,
  Google Cloud library, and Terraform provider versions and licenses;
- reviewed Terraform plan and effective provider exports for production and
  preview;
- successful route and TLS gates through the public preview edge;
- successful production-migration fail-polite and courtesy conformance suites;
- an isolated backup/restore drill and recovery of permanent blocks, dispatch
  markers, audit, and database roles;
- least-privilege IAM and PostgreSQL privilege tests, including denied bypass
  and permanent-block deletion attempts;
- GIS login tests that reject missing or unequal cookie/body `g_csrf_token`,
  missing/malformed `credential`, untrusted algorithm/key, invalid signature,
  issuer/audience/time failures, and non-allowlisted `sub`; exercise bounded
  JWKS cache hit, proactive metadata-driven refresh, unknown-key coalescing,
  rotation, refresh failure, and unavailable-current-key behavior; and
  prove the 256-bit opaque token, `SHA2-256` lookup, minimized session record,
  strict host-only cookie, and non-sliding 24-hour expiry;
- signing-key startup/rotation tests for exact-version, format, checksum,
  length, fallback, log-redaction, readiness, and denied-worker cases;
- public-health and authenticated-deployment conformance, including fixed
  no-store responses, no debug/SPA fallback, probe dependency isolation, and
  effective Cloud Run startup/liveness configuration;
- duplicate/lost/reordered Cloud Tasks and Scheduler-delivery tests;
- a dated cost-calculator export, budgets, and alert delivery test; and
- a deploy and rollback rehearsal bound to immutable image and migration IDs.
