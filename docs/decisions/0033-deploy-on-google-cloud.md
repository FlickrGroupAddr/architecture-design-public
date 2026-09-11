# ADR 0033: Deploy the private hosted components on Google Cloud

Date: 2026-08-26

Status: Superseded by accepted ADR 0050 on 2026-09-06

Current disposition: [ADR 0050](0050-select-cloudflare-and-evaluate-native-storage-first.md) selects Cloudflare and
evaluates Durable Objects and D1 first, with RDS PostgreSQL as the fallback.
This unaccepted Google Cloud proposal remains historical evidence; its
candidate decisions and rejected alternatives are not current project policy.
The native secret-version finding remains an unresolved scoped gate, not a
decision to replace Cloudflare with AWS compute.

## Context

FGA's provider-neutral contracts are now specific enough to select a hosting
stack without letting provider defaults decide application semantics. The
private deployment needs one same-origin HTTPS web/API surface, an isolated
worker, PostgreSQL transaction and fencing behavior, versioned managed secrets,
at-least-once wake hints, a minutely database-authoritative sweep, an exportable
route/TLS configuration, and an isolated provider preview.

AWS and Azure can meet the requirements but introduce an equivalent or larger
set of runtime, load-balancer, queue, scheduler, database, secret, network, and
identity resources with no project-specific advantage. Render is simpler for
ordinary web/worker hosting but does not supply the selected dynamic
secret-version lifecycle or explicit minimum-TLS/export evidence as one
integrated contract. Cloudflare's edge stack is compact, but replacing the
already designed PostgreSQL row-lock, role, constraint, and migration boundary
with SQLite-compatible D1 would be a persistence redesign rather than a
deployment decision.

The fixed-cost tradeoff is material. A dedicated high-availability Cloud SQL
instance and global load balancer cost substantially more than a shared-core or
single-process hobby deployment. Shared-core Cloud SQL is documented for
development/testing rather than production, while a single-zone instance has no
SLA. Choosing the conventional production database avoids an undeclared
availability exception and keeps the irreversible moderator-protection records
inside the strongest ordinary managed boundary selected here.

## Decision

1. Production uses a dedicated Google Cloud project in `us-east4`; preview uses
   a separate project and `preview.flickrgroupaddr.com`.
2. Terraform declares provider infrastructure. Python remains the repository
   orchestration/validation language. The JAMstack frontend loads Google's
   supported GIS client directly; FGA does not add an identity-provider Action
   runtime.
3. One immutable OCI image supplies a public FGA web Cloud Run service and an
   internal FGA group-submission worker Cloud Run service with separate commands,
   IAM service accounts, scaling limits, concurrency, and database roles.
4. A global external Application Load Balancer with a Google-managed certificate,
   `RESTRICTED` TLS policy, minimum TLS 1.3, and one serverless NEG is the only
   public edge. Its URL map sends every path to the public FGA web service. The
   application route registry owns handler-before-asset precedence.
5. The FGA database uses private-IP Cloud SQL for PostgreSQL 18 Enterprise,
   initially 1 dedicated vCPU and 3.75 GiB memory, high availability, 20 GiB
   auto-growing SSD, automated backups, point-in-time recovery, deletion
   protection, IAM database authentication, and separate API, worker, migration,
   and restore-verification principals.
6. Cloud Tasks carries disposable authenticated partition hints. Cloud Scheduler
   invokes an authenticated due-sweep every minute. FGA database due rows,
   natural keys, and fenced leases remain authoritative.
7. Secret Manager holds static application/provider secrets and immutable
   versions of dynamic Flickr OAuth token/token-secret pairs. The FGA database
   stores an exact active version reference; runtime code never resolves
   `latest` as authority.
8. Google Identity Services is the browser identity provider under ADR 0039.
   GIS posts `credential` and matching cookie/body `g_csrf_token` values to the
   FGA Google Login Endpoint. The FGA API backend validates the CSRF pair, then
   uses a maintained Google authentication library and bounded current-JWKS
   cache to validate the ID token before exact Google-`sub` allowlisting and
   creation of an opaque server-side FGA session. A provider timer invokes the
   FGA JWKS refresh worker outside login requests; the shared cache's six-hour
   maximum interval is shortened when Google's cache metadata requires it.
9. The hosted application uses CPython 3.14.7 initially, Django 5.2 LTS,
   a compatible locked Google Auth Library release, and maintained Google
   Cloud/PostgreSQL libraries. The implementation lock records exact patches,
   licenses, and maintenance evidence.
10. Initial deployment values are `max_group_ids_per_batch=60`,
    `existing_photo_proof_max_age=15 seconds`, one active head per worker claim,
    a 45-second internal worker deadline, a 60-second database lease, and the
    timeout/queue/scaling values in the hosted deployment contract.
11. Provider selection instantiates but does not weaken existing gates. The
    future hosted repository must black-box the exact preview image through the
    public load balancer and test real PostgreSQL migrations, worker crash
    boundaries, TLS, secret lifecycle, backup/restore, deployment, and rollback.

## Consequences

- The public topology remains easy to understand: one host, one load balancer,
  one web backend, and application-owned routing.
- Web and Flickr-write authorities have separate process, ingress, IAM,
  concurrency, and database boundaries while sharing one tested image.
- Managed PostgreSQL directly instantiates the selected relational semantics;
  no custom queue authority, distributed lock, D1 translation, or encrypted
  credential table is invented.
- Scale-to-zero web/worker compute fits private traffic, but the high-availability
  database and load balancer create an honest quiet-deployment cost floor. A
  dated provider estimate and budgets are release gates.
- Preview can export and exercise real routing/TLS configuration without
  production secrets or data. It is temporary and cannot substitute a provider
  simulator or hand-maintained expected-routing fixture.
- Selecting a provider does not create production evidence. This architecture
  repository still has no executable hosted implementation or passing provider
  gate.

## Rejected alternatives

- **Cloud SQL shared-core or single-zone production:** rejected because Google
  documents the former for development/testing and excludes both from the SLA;
  silent low-cost availability compromises are surprising for production.
- **Multiple load-balancer path backends:** rejected because the application can
  serve the small same-origin surface directly and duplicate path ownership
  would recreate the drift that route conformance is meant to prevent.
- **A queue as the job authority:** rejected because hints can be duplicated,
  delayed, lost, or reordered; the FGA database already owns FIFO, due time,
  leases, and dispatch safety.
- **Render plus application-encrypted OAuth secrets:** rejected because it adds
  novel cryptographic key/lifecycle machinery to compensate for a provider gap.
- **Cloudflare Workers/D1 rewrite:** rejected because an edge rewrite is not an
  unmet FGA requirement and would replace conventional PostgreSQL semantics.
- **AWS or Azure:** rejected for the private MVP because both conform but add no
  material capability or owner integration that offsets their broader resource
  surface.
- **Kubernetes:** rejected because two small services do not justify cluster,
  ingress-controller, autoscaler, secret-controller, and upgrade operations.

## Detailed contract

The authoritative resource, identity, cost, configuration, evidence, and
rollback details are in the
[hosted deployment contract](../hosted-deployment.md).
