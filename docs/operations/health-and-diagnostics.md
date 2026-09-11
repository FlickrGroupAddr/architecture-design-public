# FGA API backend health and diagnostics contract

Last updated: 2026-09-07

Status: Accepted provider-neutral health contract under ADR 0037; Cloud Run
details are one provider-specific candidate, no hosting provider is selected,
and hosted implementation is pending

## Boundary

The private deployment exposes no production debug endpoint. The only
unauthenticated operational routes are two fixed HTTP health probes required by
the Google Cloud candidate lifecycle. Richer deployment state is a read-only
administrative resource protected by the existing Google-authenticated FGA
session.

This split is deliberate. Google Cloud documents that [Cloud Run HTTP health
endpoints are externally
accessible](https://cloud.google.com/run/docs/configuring/healthchecks), so a
probe must be safe when called by anyone. Authentication state, configured
origins, identity-provider values, deployment topology, environment variables,
host names, stack traces, and dependency details are not health-probe content.

The exact prohibited legacy route is `/api/debug`. The FGA API backend registers
no handler or compatibility redirect for it. Exact `/api`, prefix `/api/`, and
the health namespace remain server-owned before any static/application-shell
fallback, so `/api/debug` and unknown `/healthz/` paths cannot become plausible
HTML or an accidental framework debug page.

Production and preview run Django with `DEBUG = False`, no debug-toolbar
package/middleware, no interactive exception page, and no source/configuration
dump. Development debug behavior is loopback-only and is never compiled into or
enabled by a deployable configuration.

## Public health routes

The route registry contains exactly these unauthenticated health handlers:

| Route | Purpose | Success condition |
| --- | --- | --- |
| `GET`/`HEAD /healthz/startup` | Cloud Run startup and pre-traffic safety | This process completed every startup invariant below |
| `GET`/`HEAD /healthz/live` | Detect an unrecoverable stuck process | The application request loop can execute the fixed handler |

All other methods return server-owned `405 Method Not Allowed`. Query strings,
cookies, authorization headers, forwarded headers, `Origin`, `Referer`, user
agent, source, and content negotiation do not alter either result. The handlers
perform no authentication and never create or refresh a session. They return no
redirect and no `Set-Cookie`, `ETag`, `Last-Modified`, `Age`, CORS, or bearer
challenge header.

Every success response is exactly:

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: no-store

{"schemaVersion":1,"status":"ok"}
```

Before startup succeeds, the endpoint is either not reachable because the
application server has correctly refused to start or returns exactly the same
headers with `503 Service Unavailable` and
`{"schemaVersion":1,"status":"unavailable"}`. `HEAD` returns the same status
and headers with no body. Server-owned `404`, `405`, and malformed-request
responses in these namespaces are also JSON and `Cache-Control: no-store`.

The [accepted 2026-09-07 provider-rejection clarification](http-route-conformance.md#provider-rejection-before-application-routing)
permits a provider's own HTTP 400 for a malformed target rejected before
application routing. That early response need not be JSON or carry the
application's no-store header, but must not contain application-shell or
application/session data or redirect to an operation. This does not change any
application-generated health response or excuse provider errors on valid requests.
[ADR 0054](../decisions/0054-accept-early-duplicate-authorization-rejection.md) extends only that
early-parser boundary to duplicate Authorization fields, with the same no-data,
no-shell and no-redirect restrictions. It adds no public health information.

The public response intentionally omits:

- build/revision/image/configuration/database identifiers;
- environment, host, region, project, origin, route inventory, or provider
  values;
- administrator, session, Google-authentication, Flickr, installation, queue, or gate state;
- dependency names/status, timings, counts, versions, or failure reasons; and
- request values, stack traces, exception classes/messages, or correlation
  identifiers.

The status code is the complete public signal. The application records only
route ID, result class, and latency for these calls; it does not copy request
headers/query/body into application logs. Provider access logs remain under
their separately accepted retention/redaction policy.

## Startup and liveness semantics

The startup result becomes `200` only after this FGA API backend process has:

1. loaded the immutable build and generated route inventory;
2. validated all production settings, including framework-signing-key,
   Google-client/audience, allowed-host/origin/login-URI, cookie, CSRF,
   credential-class, and limiter configuration;
3. opened a time-bounded FGA database connection and proved the exact expected
   migration head and required startup invariants; and
4. initialized the application/middleware graph without an import, dependency,
   or configuration error.

It does not call Flickr, Google sign-in/JWKS endpoints, Cloud Tasks, or
provider control APIs. Secret Manager access occurs only where another startup
contract requires an exact secret; public probe calls never repeat it. Once
this instance passes startup, its startup status stays `200`. A later dependency
failure is handled by the affected request's fail-closed behavior, metrics, and
alerts rather than pretending that restarting a healthy process repairs an
external service.

The liveness handler performs no database, filesystem, network, secret-store,
queue, Google sign-in/JWKS, Flickr, DNS, or provider call and takes no contended application
lock. A database, Flickr, Google, Secret Manager, Cloud Tasks, or network outage
therefore does not create a restart loop. If the request loop is deadlocked or
cannot answer, the Cloud Run probe itself times out/fails and the platform may
restart the instance.

Terraform configures stable Cloud Run HTTP probes rather than depending on the
current Preview readiness-probe feature:

| Probe | Path | Initial delay | Period | Timeout | Failure threshold |
| --- | --- | ---: | ---: | ---: | ---: |
| Startup | `/healthz/startup` | `0 seconds` | `2 seconds` | `1 second` | `30` |
| Liveness | `/healthz/live` | `5 seconds` | `10 seconds` | `1 second` | `3` |

Both use success threshold `1` and HTTP/1. Cloud Run holds liveness until the
startup probe succeeds. Cloud Run does not receive a secret probe header. The
startup probe is the readiness boundary for a new instance; the provider must
not route traffic before it succeeds. Reconsider a separate readiness probe
only after the feature is generally available and a concrete ongoing
dependency-gating requirement justifies it.

## Authenticated deployment resource

The existing private administrative allowlist adds exactly:

```text
GET /api/v001/admin/deployment
```

It requires a valid Google-authenticated FGA administrative session. No installation
credential, pending rotation credential, bearer token, source address, secret
URL, or health-probe header grants access. Missing/invalid authorization returns
the ordinary non-oracular administrative `401`; an unavailable session/database
dependency returns the ordinary sanitized `503`. Every result is
`Cache-Control: no-store`, creates no session, and performs no state mutation.

The successful response has a fixed versioned shape:

```json
{
  "schemaVersion": 1,
  "environment": "production | preview",
  "buildId": "immutable non-secret build identifier",
  "imageDigest": "OCI digest",
  "cloudRunRevision": "non-secret revision name",
  "routeInventoryDigest": "hex SHA2-256",
  "databaseMigrationHead": "non-secret migration identifier",
  "startedAt": "RFC 3339 timestamp",
  "observedAt": "RFC 3339 timestamp",
  "checks": [
    {"id": "application", "status": "ok | degraded | unavailable"},
    {"id": "database", "status": "ok | degraded | unavailable"}
  ]
}
```

Check IDs and status values are a closed enum in deterministic order. The
handler may perform one time-bounded read-only FGA database check because the
caller is authenticated and the administrative request already depends on that
database. It performs no Flickr, Google sign-in/JWKS, Secret Manager, task-queue, DNS, or
provider-control call. Secret/configuration checks report only the startup
result already established for this process; no secret or secret resource name
appears.

The resource never returns the signed-in subject/email, cookie/session/CSRF
state, configured/public/internal origins, host/IP/project/account identifiers,
environment variables, settings, feature flags, secret names/versions/status,
Google/Flickr identifiers, queue/customer/photo/group data, stack/error text, log
content, arbitrary check names, or raw provider responses. Existing dedicated
resources remain authoritative for administrator session, Flickr connection,
installations, write gates, queue status, and audit events.

## Monitoring and failure handling

Cloud Monitoring consumes probe metrics, FGA API backend request/error metrics,
database metrics, FGA JWKS refresh-worker metrics, and deployment evidence. It—not
a public diagnostic payload—owns detailed alerts. JWKS metrics expose only the age
and freshness deadline of the last successfully validated key set, refresh result
class, bounded unknown-key refresh count and wait time, and single-flight
contention; they contain no token, signing key, key ID, or Google response body.
Alert before the current validation-authority window expires and on repeated
refresh failure. Health failures are deduplicated and identify only the service/
revision, route ID, result class, and sanitized failure category.

No caller can request a deeper mode, add a query switch, change verbosity,
supply an origin, fetch arbitrary configuration, echo headers, or turn on
framework debug behavior. Temporary support needs use retained sanitized logs,
metrics, provider exports, and the authenticated deployment resource. A future
diagnostic field or route is an explicit administrative-contract and route-
inventory change with privacy review and conformance tests.

## Required conformance evidence

The hosted implementation must bind these cases to the immutable FGA web image,
route-inventory SHA2-256, Terraform plan/apply, effective Cloud Run export, and
preview revision:

- startup remains unready for every invalid configuration/key/database/schema
  case and becomes `200` only after all startup invariants pass;
- liveness stays `200` through simulated database, Flickr, Google, Secret Manager,
  Cloud Tasks, and DNS outages, while a deliberately wedged handler causes the
  probe to fail;
- public probe `GET`/`HEAD` success/unavailable and every `404`/`405` case has
  exact status, JSON media type, `no-store`, fixed schema/body, and no forbidden
  header or field;
- cookies, authorization, origins, forwarded headers, query values, and content
  negotiation cannot personalize or enrich a public probe;
- `/api/debug` and unknown `/healthz/` paths return server-owned non-HTML
  `404`/`405` responses,
  never a static shell, redirect, or compatibility handler;
- Django `DEBUG` and debug middleware are absent in production/preview settings
  and generic failures expose no traceback/settings page;
- the deployment resource rejects unauthenticated, installation-credential,
  pending-rotation, and wrong-class callers before lookup;
- its authenticated response contains exactly the allowlisted schema and
  deterministic checks, with no forbidden origin/identity/secret/configuration
  data and no upstream call or mutation;
- direct default Cloud Run URLs remain unreachable from the public Internet;
  all public black-box probes traverse the accepted HTTPS edge; and
- rollback artifacts carry and pass their own health/route inventory rather
  than reusing another revision's result.

This repository has no hosted application, Cloud Run revision, Terraform, or
provider account and therefore records no executable health/diagnostic pass.
