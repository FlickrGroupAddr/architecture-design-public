# ADR 0037: Expose only coarse public health

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31

## Context

The reviewed legacy service exposed unauthenticated `/api/debug` state that
included whether the caller was signed in and configured origin values. It sat
outside the versioned API's authentication and no-store policy. A production
debug route is both surprising and unnecessary for the private deployment.

The Cloud Run deployment candidate still needs startup and liveness probes. Google
Cloud documents that HTTP probe endpoints are externally accessible, so hiding
details behind an obscure health path is not a security boundary. Conversely,
making liveness depend on the database or an upstream service would create
restart loops that cannot repair the dependency.

## Decision

The FGA API backend registers only two unauthenticated operational routes:
`GET`/`HEAD /healthz/startup` and `GET`/`HEAD /healthz/live`. Their fixed JSON,
status, headers, and no-store policy expose no identity, configuration,
deployment, origin, or dependency detail. Startup proves the instance is safe
to receive traffic; liveness proves only that its request loop can respond.

The FGA API backend registers no `/api/debug` compatibility route, and the
server owns exact `/api`, prefix `/api/`, and `/healthz/` before static fallback.
Django debug behavior is absent from production and preview.

Detailed non-secret deployment state is available only from
`GET /api/v001/admin/deployment` under the existing Google-authenticated FGA administrative
session and no-store policy. Logs, metrics, alerts, and provider exports remain
the primary diagnostic evidence.

Cloud Run uses stable startup and liveness probes. The current Preview readiness
probe is not a private-MVP dependency; startup already establishes initial
readiness, and application routes fail closed during later dependency outages.

The complete route schemas, exclusions, probe settings, failure behavior, and
conformance matrix are in
[`docs/operations/health-and-diagnostics.md`](../operations/health-and-diagnostics.md).

On 2026-09-07 Terry accepted the scoped
[provider-rejection clarification](../operations/http-route-conformance.md#provider-rejection-before-application-routing):
a provider's own HTTP 400 for a malformed target rejected before application
routing need not use the application's JSON/no-store representation. It must
not expose application/session data, serve the application shell, or redirect
to an operation. Application-generated API and health responses retain every
existing requirement. This clarifies the early parser boundary rather than
adding a public diagnostic response or waiving failures on valid routes.

On 2026-09-11 Terry accepted [ADR 0054](0054-accept-early-duplicate-authorization-rejection.md),
which explicitly extends only this early-parser boundary to duplicate
Authorization fields. Application-generated authentication and health responses
retain their original requirements.

## Consequences

- Anyone may learn only whether a probe returned its coarse status code; no
  public endpoint reports who is signed in or how the deployment is configured.
- Liveness cannot amplify public requests into database, secret-store, Google-authentication,
  Flickr, queue, DNS, or provider calls and cannot restart-loop on their outage.
- A new instance receives traffic only after its startup configuration,
  signing-key, database/schema, route, and middleware invariants pass.
- Terry can inspect useful build/migration/application/database state through
  an already authenticated administrative resource rather than a secret URL.
- Route conformance must prove legacy/debug paths are truthful server-owned
  failures and cannot fall through to HTML.
- Detailed executable evidence remains pending until the hosted repository and
  isolated preview exist.

## Rejected alternatives

- **Keep `/api/debug` but remove a few fields:** rejected because its public
  existence invites future sensitive additions and duplicates established
  administration/monitoring boundaries.
- **Protect debug with a secret query string or header:** rejected because that
  creates another bearer secret, parsing/logging/rotation boundary, and a
  surprising operational back door.
- **Require an administrative session on `/api/debug`:** rejected in favor of a
  resource-oriented versioned deployment resource with an explicit schema.
- **Put build/dependency detail in public health:** rejected because probes need
  only a status code and their endpoints are externally accessible.
- **Make liveness query dependencies:** rejected because process restarts do not
  repair external dependencies and can worsen an outage.
- **Adopt Preview readiness probes now:** rejected because startup supplies the
  required pre-traffic boundary without making a non-GA feature operationally
  mandatory.
