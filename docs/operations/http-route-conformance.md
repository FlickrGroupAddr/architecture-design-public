# HTTP route and asset-router conformance

Last updated: 2026-09-07

Status: Accepted required predeployment gate under ADRs 0016, 0031, 0037, and
0043; provider adapters remain undecided, and no server or deployment router
exists in this repository from which to run the gate yet

## Purpose

The FGA HTTPS edge serves both browser assets and server handlers on
`flickrgroupaddr.com`. A static-file or single-page-application fallback must
never intercept an authentication, callback, or API request. Direct unit tests
of FGA API backend handlers do not prove that development or deployed routing
can reach those handlers.

This gate uses one inventory derived from the application route registry and
tests it against both the development topology and a provider preview
deployment. It specifically prevents the legacy defect in which source used
`/auth` while asset-routing configuration allowed `/oauth`.

[ADR 0016](../decisions/0016-derived-route-conformance.md) records the
decision. [ADR 0033](../decisions/0033-deploy-on-google-cloud.md) preserves one
Google Cloud export/preview candidate; choosing a provider does not weaken this
acceptance gate.
[ADR 0031](../decisions/0031-use-resource-oriented-fga-api-routes.md)
records the resource-oriented plug-in route names and removal of the unreleased
`flickr-api-proxy` draft namespace.
[ADR 0037](../decisions/0037-expose-only-coarse-public-health.md)
records the coarse public health and authenticated deployment-resource split.

## Routing ownership

Routing classification is path-first and independent of HTTP method. An
unsupported method still reaches the server owner and receives its `405` or
other non-asset response; it must not fall through to HTML.

The initial ownership rules are:

| Match | Owner | Required precedence |
| --- | --- | --- |
| Exact `/api` and prefix `/api/` | FGA API backend | Before every static-file and application-shell rule; includes versioned APIs and truthful failures for retired/guessed paths such as `/api/debug` |
| Exact `/healthz/startup` and `/healthz/live`, plus prefix `/healthz/` for unknown paths | FGA API backend | Before every static-file and application-shell rule |
| Exact `/admin/login` | FGA API backend login-start handler | Before administrative assets or shell fallback; its bounded `GET` creates the accepted five-minute login transaction |
| Exact `/admin/google-login` | FGA API backend Google-login handler | Before every browser asset or shell fallback; accepted ADR 0043 fixes this route for implementation |
| Exact `/admin/flickr-oauth/callback` | FGA OAuth handler | Before `/admin/` assets or shell fallback |
| Prefix `/admin/assets/` for `GET`/`HEAD` | Versioned administrative static assets | After server-exact rules |
| Exact `/admin/` for `GET`/`HEAD` | Administrative application shell | After server-exact rules |
| Other allowlisted client-side `/admin/` navigation for `GET`/`HEAD` | Administrative application shell | Last within the administrative namespace |

Unknown `/api/` and `/healthz/` paths still belong to the FGA API backend and
return its non-HTML `404`; the asset router does not decide whether a server
route exists.
Unsafe methods under a static namespace never return the application shell.
There is no `/oauth` alias, compatibility fallback, case folding, or inferred
rewrite for the registered Google-login and Flickr-callback paths.

The edge performs one standards-compliant URL parse. Route classification uses
the resulting path and ignores the query for ownership. Invalid percent
encoding, encoded separators, backslashes, control characters, or an otherwise
invalid request target is rejected before static fallback. A proxy must not
decode or normalize a path a second time into a different owner.

### Provider rejection before application routing

Terry accepted this scoped clarification on 2026-09-07 after the isolated
Cloudflare routing proof rejected `GET /api/%00` with the provider's own HTTP
400 page. A provider may reject a malformed request target before application
routing with its own `400 Bad Request` response, including a non-JSON body and
without the application's `Cache-Control: no-store` header. The response must
not serve application-shell content, redirect to an application operation, or
contain application/session data. Every application-generated API and health
response retains its existing JSON/no-store requirements, including malformed
requests that reach the application.

The conventional recommendation, accepted by Terry, is to distinguish an early
HTTP-parser rejection from an application response rather than add an edge
adapter solely to restyle that rejection. The tradeoff is that clients must
handle an early non-JSON HTTP 400. On 2026-09-11 Terry accepted
[ADR 0054](../decisions/0054-accept-early-duplicate-authorization-rejection.md), extending this boundary
to duplicate Authorization fields rejected by the provider parser before the
application. That HTTP 400 may also omit the application Bearer challenge; it
must not redirect, set an application/session cookie, serve an application shell,
or expose application/session data or credentials. Every application-generated
authentication response still uses JSON/no-store and matching Bearer error codes.
There is no exception for ordinary route 404/405 responses, provider outages on
valid requests, successful operations, other authentication failures, or static
fallback. The gate records this distinction explicitly
and continues to fail on unproven response ownership. It must not use any HTML
400 as a substitute for evidence of provider rejection.

## Derived route inventory

The FGA API backend's route-registration layer is the sole source for server
routes. Each registered route carries ordinary metadata:

- stable route ID;
- method;
- exact or templated path;
- component owner;
- routing class (`worker_first`, `static_asset`, or `admin_shell`);
- authentication boundary;
- a safe, non-destructive conformance probe ID; and
- expected response discriminator for an unauthenticated or deliberately
  invalid probe.

The build deterministically emits a sorted, versioned `route-inventory.json`
from those registrations. The artifact contains no origin secrets, provider
account IDs, Google `sub` values, credentials, query values, or production host
names. A representative generated record is:

```json
{
  "schemaVersion": 1,
  "routes": [
    {
      "id": "google_login",
      "method": "POST",
      "pathPattern": "/admin/google-login",
      "owner": "fga_api_backend",
      "routingClass": "worker_first",
      "authBoundary": "google_login",
      "probe": "missing_google_credential"
    }
  ]
}
```

This JSON is a build result, not a second hand-maintained route list. Adding,
removing, or renaming a handler changes the inventory in the same review. The
development proxy/asset router and deployable edge configuration derive their
worker-first exact/prefix matcher inputs from this artifact or from the same
typed registry module. They must not maintain a separate `/auth`/`oauth`
allowlist.

The route registry also emits the `/api` and `/healthz/` namespace guards and
the exact Google-login and Flickr-callback paths even if a provider can route
the whole application to one process. This keeps the ownership proof visible
and makes a later split deployment testable.

## One conformance gate

The hosted repository exposes one required `route-conformance` command. It
performs all of these phases and fails if a phase is absent, skipped, stale, or
inconclusive:

1. **Inventory validation.** Generate the inventory from the compiled route
   registry; reject duplicate IDs/method/path tuples, unsupported metadata,
   unowned routes, missing non-destructive probes, or a server route classified as an
   asset/shell.
2. **Configuration projection.** Generate or inspect the exact development and
   deployment router artifacts. For every inventory entry and namespace guard,
   prove the first matching decision has the expected owner. Also prove known
   assets/shell navigation remain reachable after worker-first rules.
3. **Development black box.** Start the built development topology, issue the
   safe probe matrix over HTTP, and verify the response discriminator came from
   the registered component rather than static HTML.
4. **Deployment black box.** Deploy the same build to the provider's isolated
   preview/staging environment and repeat the matrix through its public HTTPS
   edge. A configuration simulator alone does not satisfy this phase.
5. **Artifact binding.** Record the application build ID, inventory digest,
   development-router digest, deployment-artifact digest, preview URL's opaque
   deployment ID, and pass time. A gate result for another build cannot approve
   release.

The gate runs before first deployment, on every handler route change, asset
router/proxy change, provider configuration change, and rollback artifact. A
production promotion is refused unless all phases passed for the exact build.
The command has no permissive `--skip-preview`, missing-config warning, or
production-only exception.

## Safe probe matrix

The generated inventory contains every route. The following fixed boundary
probes are additionally mandatory because they distinguish server ownership
from an HTML fallback:

| Probe | Expected server evidence |
| --- | --- |
| `GET /api/v001/installations/current` without authentication | `401`, Bearer challenge, no HTML |
| `POST /api/v001/installations/current` | Server `405`/contract error, no HTML |
| `GET /api/v001/auth/device/token-check?device_type=lrc15_plugin` | Backend `404` or `405`, no redirect, no compatibility response, no HTML |
| `GET /api/v001/groups?page_size=1` without authentication | `401`, Bearer challenge, no Flickr call, no HTML |
| `GET /api/v001/existing-public-photos?page=1&page_size=1` without authentication | `401`, Bearer challenge, no Flickr call, no HTML |
| `POST /api/v001/existing-public-photo-bindings` without authentication | `401`, Bearer challenge, no Flickr call or binding mutation, no HTML |
| `GET /api/v001/photo-bindings/conformance-missing/group-memberships` without authentication | `401`, Bearer challenge, no Flickr call, no HTML |
| `POST /api/v001/upload-authorizations` without authentication | `401`, Bearer challenge, no signing or database mutation, no HTML |
| `POST /api/v001/group-submission-batches` without authentication | `401`, Bearer challenge, no intent creation or Flickr call, no HTML |
| `GET /api/v001/group-submission-intents?page_size=1` without authentication | `401`, Bearer challenge, no status rows, worker hint, or Flickr call, no HTML |
| `GET /api/v001/group-submission-intents/conformance-missing` without authentication | `401`, Bearer challenge before non-oracular owner lookup, no HTML |
| `GET /api/v001/admin/session` without a session | Administrative JSON `401`, no Bearer challenge, no HTML |
| `POST /api/v001/admin/session/logout` from the configured exact origin without a session | Server-owned no-store `204` with the fixed `__Host-fga_admin` expiration header, no redirect, HTML, session oracle, or mutation |
| `POST /api/v001/admin/session/reauthentication` without a session | Administrative JSON `401`, no transaction state/nonce, Google call, redirect, or HTML |
| `GET /api/v001/admin/deployment` without a session | Administrative JSON `401`, no deployment/configuration fields, Bearer challenge, or HTML |
| `GET /api/v001/admin/group-submission-intents?page_size=1` without a session | Administrative JSON `401`, no Bearer challenge, status rows, or HTML |
| `POST /admin/google-login` without `credential`, `state`, and the matching cookie/body `g_csrf_token` pair | Sanitized server `400`, `Cache-Control: no-store`, no session, JWKS refresh, redirect, or application shell |
| `GET /admin/flickr-oauth/callback` without transaction/verifier | Sanitized server `400`, `Cache-Control: no-store`, no application shell |
| `GET /api/v001/__route_conformance_missing__` | FGA API backend JSON `404`, no HTML |
| `GET /api/v001/flickr-api-proxy/groups` | FGA API backend JSON `404`/`405`, no compatibility alias, redirect, Flickr call, or HTML |
| `GET /api/debug` with and without cookies/authorization/query values | FGA API backend JSON `404`, `Cache-Control: no-store`, no identity/origin/configuration data, redirect, compatibility handler, or HTML |
| `GET`/`HEAD /healthz/startup` after accepted startup | Fixed public-health `200`, JSON/no body for `HEAD`, `Cache-Control: no-store`, no cookie/auth/configuration-dependent field or header |
| `GET`/`HEAD /healthz/live` | Fixed public-health `200`, JSON/no body for `HEAD`, `Cache-Control: no-store`, no dependency call or detail |
| `POST /healthz/live` and `GET /healthz/__route_conformance_missing__` | FGA API backend JSON `405` and `404` respectively, both `Cache-Control: no-store`, no HTML |
| `POST /api/v001/group-submission` | FGA API backend JSON `404`/`405`, no single-group handler, redirect, or HTML |
| `POST /api/v001/group-submissions` | FGA API backend JSON `404`/`405`, no single-group handler, redirect, or HTML |
| `POST /api/v001/group-submission-intents/conformance-id/retry-now` | FGA API backend JSON `404`/`405`, no worker hint, state change, Flickr call, redirect, or HTML |
| `POST /api/v001/admin/group-submission-intents/conformance-id/reopen` | Administrative JSON `404`/`405`, no intent/block/gate mutation, redirect, or HTML |
| `POST /admin/__route_conformance_missing__` | Edge/server rejection, no HTML shell |
| `GET /admin/` | Administrative shell HTML with required security headers |
| `GET` of one hashed asset selected from the actual build manifest | Exact asset bytes/MIME, not the shell |

Login and callback probes omit required values so they cannot validate a real
Google credential or exchange a Flickr verifier. The Google-login probe uses
no real token, performs no JWKS refresh, and creates no authenticated or
production session. The preview has no production Flickr secrets and does not
call Flickr.

Responses are distinguished through their contractual status, media type,
challenge/location, cache policy, and body schema. The production edge need not
expose a diagnostic route-owner header. If a provider makes those signals
insufficient, its preview adapter may use a build-bound test-only marker that
is absent from production.

## Development and deployment adapters

The provider implementation supplies two small adapters beside the actual
configuration they inspect:

- The development adapter boots or evaluates the real development proxy and
  asset-server artifact, not a duplicate fixture.
- The deployment adapter compiles the real provider routing artifact and drives
  the real preview deployment/health boundary.

Both consume the generated inventory. A hand-written JSON file that merely
claims the desired decisions is not evidence.

The Google Cloud candidate deployment adapter derives the Terraform URL-map input from the
compiled inventory and records the reviewed Terraform plan/state projection,
the effective `gcloud compute url-maps describe` output, and
`gcloud run services describe --format=export` output for the exact image and
revision. The initial URL map intentionally has one default serverless NEG to
the FGA web service; the exported proof must show that no earlier provider path
rule can intercept a route.

If that provider is selected, its preview adapter deploys the exact candidate image digest and migrations to
the isolated Google Cloud preview project, then sends the complete black-box
matrix through `https://preview.flickrgroupaddr.com/` and its global external
Application Load Balancer. It never tests the direct Cloud Run URL, uses no
production secret or data, and records the project, Cloud Run revision, URL-map
fingerprint, certificate/TLS-policy IDs, Terraform plan digest, and probe time.
A provider simulator, hand-written export fixture, or handler unit test does
not satisfy either adapter.

## Failure and rollback handling

A mismatch blocks deployment and reports only route ID, method, sanitized path
pattern, expected owner, actual response discriminator, build/deployment IDs,
and correlation ID. It never records cookies, authorization headers, callback
parameters, or secret configuration.

The fix is to change the route registration or derived router configuration and
rerun the entire gate. Operations must not add a one-off production rewrite that
is absent from the inventory. Rollback uses the old build's own inventory and
router artifact and must pass in preview before promotion; a previously passing
result for the same source commit but different provider configuration is not
reused.
