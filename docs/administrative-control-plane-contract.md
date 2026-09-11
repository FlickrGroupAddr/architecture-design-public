# Private-MVP administrative control-plane contract

Last updated: 2026-09-11

Status: Accepted private-MVP administrative semantics under ADRs 0017, 0039,
0040, and 0043; unresolved wire schemas remain explicit, hosted providers remain
undecided, and hosted implementation is pending

Private replacement amendment: [ADR 0052](decisions/0052-evaluate-paused-native-credential-replacement.md)
accepts a paused, generation-checked native credential proof with repair after
interruption. Its scoped OAuth lifecycle rules qualify the versioned-path
sequence below; exact UI/wire mapping and hosted conformance remain pending.

## Purpose and boundary

The FGA administrative control plane is the browser-only operator surface for
the private single-user deployment. It authenticates Terry independently of the
FGA LrC plug-in and authorizes a deliberately small set of security-sensitive
operations. It is not a general database console, secret viewer, arbitrary
Flickr proxy, public user portal, or alternate client for routine photography.

The browser UI lives under `https://flickrgroupaddr.com/admin/`. Its JSON
operations live under `https://flickrgroupaddr.com/api/v001/admin/`. The FGA
HTTPS edge **MUST** route those namespaces explicitly and **MUST NOT** fall back
from a missing administrative API route to a static application shell. The
[HTTP route and asset-router conformance gate](operations/http-route-conformance.md)
derives its inventory from server registrations and proves this boundary
through both development and provider-preview routing.

[ADR 0039](decisions/0039-use-google-identity-services-browser-sessions.md)
selects direct Google Identity Services browser authentication and a
purpose-built opaque FGA session. The CDN, backend-hosting, database, and
managed-secret providers remain undecided. The implementation **MUST** pin
maintained, appropriately scoped, license-compatible framework and Google
authentication libraries and **MUST NOT** implement a password verifier, JWT
parser/signature validator, session framework, or CSRF framework from scratch.

[ADR 0041](decisions/0041-use-clean-room-authentication-tabs-as-interaction-authority.md)
designates all three clean-room authentication tabs as authoritative interaction
maps. Its first two tabs own the browser-session creation and Plugin Code
list/create/transfer happy paths relevant to this contract. This contract
supplies omitted administrative authorization, failure, lifecycle, and wire
detail without changing those depicted actors, boundaries, ordering, or
explicit invariants.

## Administrator authentication

### One independently authenticated owner

The private MVP has exactly one administrative principal. Deployment
configuration pins Terry's immutable Google `sub`. The FGA Google Login
Endpoint first validates the Google issuer and every other current Google
ID-token requirement, then the FGA administrative control plane compares the
validated `sub` with that exact allowlist. An email address, display name,
hosted domain, Flickr identity, FGA installation credential, source IP address,
or possession of the Lightroom computer is not administrator identity.

Google authentication creates an ordinary FGA browser session; it does not by
itself grant administrative authority. Every administrative request resolves
the server-side FGA session and then applies the owner allowlist and operation
policy. No browser parameter, unsigned token payload, email, or client-side
claim can satisfy the allowlist.

The FGA administrative control plane **MUST NOT** contain a local password,
password-reset, signup, invitation, role-management, or account-recovery
system. Google Account recovery remains outside FGA application code.

### Google Identity Services login flow

The JAMstack frontend loads Google's supported GIS client from
`https://accounts.google.com/gsi/client` and renders the Sign in with Google
experience. The accepted [browser-session lifecycle](browser-session-lifecycle.md)
selects `POST /admin/google-login` as GIS's exact `login_uri`; the frontend does
not accept an arbitrary post-login destination.

After Google sign-in and consent, GIS sends an HTTPS form `POST` to that
endpoint. The request contains the Google-signed ID token in `credential` and
the GIS CSRF value both in the `g_csrf_token` cookie and request body. The
endpoint requires both values and an exact match before processing the ID
token. A missing or unequal pair is a generic no-store rejection and creates no
FGA session.

The endpoint uses a maintained Google authentication library and the FGA
backend's bounded cache of Google's current JWKS. It validates trusted
algorithm/key selection, signature, exact configured audience, accepted Google
issuer, and applicable time claims under Google's current server-side contract.
Outside login requests, a hosted timer invokes the FGA JWKS refresh worker by
the earlier of six hours after the preceding successful refresh and a safety
margin before Google's published freshness expiry. The worker uses jitter,
bounded timeout/backoff, and a deployment-wide single-flight boundary and
atomically installs only a successfully retrieved and validated key set.

After admission and the GIS CSRF check, a login naming an unknown signing key ID
may join or initiate one bounded, coalesced refresh and retry key selection
once. It waits for that refresh and fails closed if current validation authority
still cannot be established. No request can force repeated or unconditional
upstream refreshes.

Only canonical Google issuer plus validated `sub` identifies the Google
Account. The Google ID token is
request-local and discarded after the FGA session record is committed. FGA
components neither request nor retain a Google access or refresh token for this
authentication flow.

### Unauthenticated admission and cost boundary

The private MVP has no device-link start, device code, public signup, or
self-service OAuth-login creation route. Requests for a legacy or guessed
device-start path reach the FGA API backend's ordinary non-HTML `404`; they do
not create state or redirect. Ticket #0037 does not authorize such a flow.
Public/self-service operation remains prohibited until the separately accepted
abuse threat model required by ADR 0004 and ticket #0032 defines identity-bound
admission, re-registration resistance, cost limits, monitoring, suspension,
and repair.

Exact endpoint `POST /admin/google-login` is Internet-reachable and
receives attacker-controlled form posts before Terry is authenticated. The FGA
HTTPS edge and API backend apply all of these initial
private-MVP limits:

| Boundary | Initial limit |
| --- | --- |
| FGA Google Login Endpoint per normalized source | Token bucket allowing 5 posts per 10 minutes with burst 2 |
| FGA Google Login Endpoint for the whole deployment | Sliding window allowing 30 posts per 10 minutes |
| Invalid Google-login or Flickr callback requests per source | Sliding window allowing 20 per 10 minutes |
| Invalid Google-login or Flickr callback requests for the deployment | Sliding window allowing 120 per 10 minutes |
| Live Flickr OAuth transactions | 5 for the whole deployment; creation already requires an authenticated, recent-administration session |

One owner ordinarily needs one GIS interaction and one login POST. These values
leave room for ordinary reloads and recovery while bounding JWT-validation and
JWKS-refresh pressure. They are private-administrator defaults, not evidence
that the same volumes are safe for public onboarding.

All independent buckets and the Flickr live-state cap must admit a request.
They use a shared atomic store visible to every FGA API backend instance;
process-local counters are not acceptable. The deployment-wide bucket bounds
distributed source rotation, while the source bucket limits cheap single-
origin floods. No application account lockout exists before Google identity
proof, because an attacker must not be able to lock Terry's known administrator
identity merely by naming it.

The FGA HTTPS edge strips untrusted forwarding headers and supplies one
authenticated normalized client-address attribute. The application derives the
source limiter key as HMAC using SHA2-256 with a dedicated managed limiter
secret; it stores neither the raw address nor a reversible value. IPv4 uses the
address and IPv6 uses a documented `/64` prefix so trivial address rotation
does not create unlimited buckets. Limiter records expire within 24 hours and
never enter administrative audit or ordinary application logs. Provider edge
security logs follow their separately approved retention policy.

Admission runs before JWT parsing, signature validation, FGA database
insertion, or a JWKS refresh. The endpoint then performs bounded form parsing
and the required GIS double-submit `g_csrf_token` comparison before processing
`credential`. Google's current signing keys use the maintained library's
bounded FGA backend cache and the proactive metadata-driven refresh contract.
Only an admitted, CSRF-checked login naming an unknown signing key ID can join
or initiate the one bounded refresh described above. A limit refusal creates no
FGA session and returns generic `429 Too Many Requests`, `Cache-Control:
no-store`, a coarse `Retry-After`, and no bucket name, remaining count,
allowlisted subject, token detail, or provider detail.

The Google login POST does not bind identity to source address because a
legitimate Browser's network may change. GIS CSRF validation authenticates the
request ceremony; current JWT validation authenticates the Google assertion;
the exact `sub` allowlist separately authorizes private administration. Flickr
OAuth retains its independent five-minute single-use state transaction, and
only an authenticated recent-administration action can create it.

If the shared limiter is unavailable, the FGA Google Login Endpoint fails
closed with sanitized `503 Service Unavailable` and creates no administrative
session. The Flickr callback separately fails closed when its limiter or
transaction-cap check is unavailable. Sustained global saturation emits one
deduplicated operational alert per limiter window, not one alert per request.
Metrics contain route ID, outcome, bucket class, and count only—never source
keys, addresses, CSRF values, Google credentials, Flickr state, or codes.

These numeric limits are deployment configuration with tests, not hidden
framework defaults. A change is an authentication/availability change that
reruns the admission, route-conformance, and end-to-end gates. CAPTCHA, a secret
URL, source allowlisting, or provider bot scoring may be defense in depth but
does not replace the shared source/global/live-state limits.

### Server-side administrative session

After successful validation, the FGA API backend creates a server-side session
and sends one opaque cookie:

```http
Set-Cookie: __Host-fga_admin=<256-bit-random-value>; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=86400
```

The cookie has no `Domain` attribute. The FGA database stores the unsalted
SHA2-256 digest of the complete random value and the exact minimized fields in
the accepted [browser-session lifecycle](browser-session-lifecycle.md#session-record).
It does not store the cookie plaintext, the Google ID token, the complete
decoded Google claim map, or Google access/refresh tokens.
The FGA Google Login Endpoint obtains `fgaUserId` from the unique mapping of the
validated canonical Google issuer and `sub`; email is mutable display metadata
and never a resource-ownership or authorization key.

The issuer/`sub` mapping, session row, and sanitized
`authentication.login_succeeded` audit event commit in one FGA database
transaction before the endpoint sends the cookie. An audit-write failure creates
no usable session. Rejected attempts append only the sanitized failed stage and
correlation evidence when the database is available, never the assertion,
profile claims, session/CSRF values, request body, or arbitrary exception text.

The server-side session expires at the same instant as the cookie: 24 hours
after login, with no shorter idle timeout and no activity-based extension.
Accepted ADR 0043 binds successful reauthentication to one five-minute Google
state/nonce transaction, rotates the exact bound session value and CSRF token,
and invalidates the prior values without revoking unrelated sessions. `POST
/api/v001/admin/session/logout` revokes the server-side session before clearing
the cookie. It retains the cookie and reports an unconfirmed result when the
transaction does not produce a known durable outcome, so the same request can
converge idempotently. The [OAuth and account
lifecycle](oauth-and-account-lifecycle.md#logout-outcome-and-recovery) defines
the exact response, UI state, response-loss recovery, and tests. A process
restart does not restore an expired or revoked session.

Django's maintained request, cookie, and CSRF integration may be used, but the
purpose-built FGA session database record, `SHA2-256` lookup key, expiry, and
revocation contract above remain authoritative. Signed-cookie sessions are not
enabled. A narrow policy layer stores the independent 256-bit synchronizer
value in the server-side session and compares the submitted header in constant
time; it does not replace the framework's request or middleware boundary.

If the hosted stack uses Django, its installation-wide framework-signing key is
independent from the opaque FGA session token and digest verifier. The proposed
[framework-signing key candidate](operations/session-signing-key.md) records
one exact Google Secret Manager binding if that provider stack is selected; no
hosting or managed-secret provider is currently selected. Every implementation
still fails startup for a missing, weak, inaccessible, or invalid framework key
and never generates a process-local production default.

Every administrative HTML and JSON response uses `Cache-Control: no-store`.
The administrative UI uses a restrictive Content Security Policy with
`default-src 'self'`, no inline script exception, and `frame-ancestors 'none'`.
The login page narrowly permits Google's supported GIS library and parent
origins in `script-src`, `connect-src`, `frame-src`, and `style-src` as required
by Google's current integration guidance; it does not use wildcards or
self-host an unsupported copy of the GIS library. The UI also sends
`Referrer-Policy: no-referrer` and `X-Content-Type-Options: nosniff`. The final
edge configuration remains subject to the existing HTTPS acceptance gate.

### CSRF and recent-authentication boundary

Every authorization/domain-state-changing administrative operation uses
`POST`, `PUT`, `PATCH`, or `DELETE`; no ordinary resource `GET` changes
authorization/domain state or creates work. Coalesced append-only access/audit
observations may have the conventional logging side effect but never authorize
or drive a domain transition. The GIS login POST uses Google's double-submit
CSRF ceremony. The Flickr OAuth callback is the only retained redirect-protocol
exception and uses a one-time server-side transaction and unguessable state.

The FGA API backend issues one independent 256-bit synchronizer CSRF token per
administrative session and returns it only through the authenticated no-store
current-session resource. Browser code retains it only in memory. The
administrative UI sends it in `X-CSRF-Token` for
every unsafe method. The backend requires an exact token match and exact
`Origin: https://flickrgroupaddr.com`; it rejects a missing, null, or different
origin. `SameSite=Strict` is defense in depth, not the only CSRF control. CORS is
disabled for the administrative API.

Creating or revoking an installation credential, starting/completing/cancelling
an installation-credential rotation, replacing or disconnecting the linked
Flickr grant, revoking another administrative session, or attempting to resume
a Flickr write gate requires the accepted lifecycle contract's five-minute
recent Google reauthentication. It uses a single-use state and signed nonce
bound to the current session, then rotates that session. It proves a newly
issued Google assertion for the same account; it does not claim a fresh
password, passkey, MFA, or phishing-resistant challenge. The operator must
review and submit the action again after reauthentication; no pending mutation
crosses the boundary.

## Authorized operation allowlist

The FGA API backend authorizes the following private-MVP administrative
operations and rejects every other route. All identifiers are opaque strings,
all collection responses are bounded and paginated, and every state-changing
request requires JSON with a supported `schemaVersion` unless the operation is
the standards-defined redirect callback.

[ADR 0040](decisions/0040-expose-plugin-codes-as-user-resources.md) places the
ordinary user's Plugin Code collection outside the `/admin` API namespace.
The credential-rotation state machine remains valid, but its replacement FGA
User API routes are unresolved and therefore are not allowlisted here.

| Operation | Method and path | Required behavior |
| --- | --- | --- |
| Read deployment status | `GET /api/v001/admin/deployment` | Return only the fixed sanitized build/revision/migration and application/database check schema from the accepted [health/diagnostics contract](operations/health-and-diagnostics.md); no identity, origin, secret/configuration dump, upstream call, or mutation |
| Read current administrator/session state | `GET /api/v001/admin/session` | Return only display-safe Google-account and FGA-session metadata plus expiry; never return the Google ID token, its full claim map, or the session value |
| Start recent Google reauthentication | `POST /api/v001/admin/session/reauthentication` | Require the current session, exact origin, and CSRF; return one five-minute state/nonce transaction for an explicit GIS button without carrying a pending mutation across the boundary |
| Logout | `POST /api/v001/admin/session/logout` | Idempotently commit current-session revocation plus its audit event, then return no-store `204` and expire the host-only cookie; any unconfirmed result retains retry authority and never renders success |
| List administrative sessions | `GET /api/v001/admin/sessions` | Return bounded opaque-cursor pages of display-safe server-side session metadata for the exact principal |
| Revoke another administrative session | `POST /api/v001/admin/sessions/{sessionId}/revocation` | Require recent authentication and `expectedRevision`; never accept the current session as this route's target |
| Revoke all other administrative sessions | `POST /api/v001/admin/sessions/revoke-others` | Require recent authentication, reviewed expected count, and the principal's session-set revision; preserve only the current session |
| Read linked Flickr status | `GET /api/v001/admin/flickr-connection` | Return linked owner NSID, permission class, status, and sanitized observation times; never return Flickr secrets |
| Start or replace Flickr authorization | `POST /api/v001/admin/flickr-connection/authorization` | Require recent authentication, create one five-minute OAuth 1.0a transaction, and return `303 See Other` only to Flickr's fixed authorization origin |
| Receive Flickr authorization | `GET /admin/flickr-oauth/callback` | Consume the exact transaction and verifier, verify expected owner and `write` permission, then atomically activate the new versioned secret reference without resuming a paused write gate |
| Disconnect the linked Flickr grant locally | `POST /api/v001/admin/flickr-connection/disconnection` | Require recent authentication, `expectedRevision`, and exact owner-NSID confirmation; atomically remove active authority and pause writes, then delete the inactive managed-secret version |
| List Plugin Code records | `GET /api/v001/plugin-codes` | Query only records owned by the session's internal `fgaUserId`; durably append the sanitized list-read audit event before returning bounded metadata; never return plaintext, a digest, or credential class |
| Create a Plugin Code | `POST /api/v001/plugin-codes` | Require recent authentication; bind the new record to the session's internal `fgaUserId`, server-assign class `lrc_plugin`, and atomically commit creation plus its audit event before returning ADR 0044's canonical Plugin Code exactly once with `201 Created`; the browser cannot supply the code, owner, or class |
| Revoke a Plugin Code | `PATCH /api/v001/plugin-codes/{pluginCodeId}` | Require ownership by the session's internal `fgaUserId`, recent authentication, a strong `If-Match`, and exactly `application/merge-patch+json` body `{"state":"revoked"}`; atomically revoke the installation plus current/pending versions and append the audit event while retaining history |
| Read group-submission intent status | `GET /api/v001/admin/group-submission-intents` | Return only the authenticated owner's bounded `active`, `attention`, or `history` projection and queue/gate summary from ADR 0034; no Flickr call or worker wake |
| Read one group-submission intent | `GET /api/v001/admin/group-submission-intents/{submissionIntentId}` | Return the current sanitized owner-scoped intent, queue/gate, outcome, attention, and permanent-block projection from ADR 0034 |
| Read Flickr write gates | `GET /api/v001/admin/flickr-write-gates` | Return the bounded sanitized status defined by ADR 0013 |
| Attempt verified gate resume | `POST /api/v001/admin/flickr-write-gates/{gateId}/resume` | Require recent authentication and `expectedRevision`; perform ADR 0013's non-mutating verification and compare-and-set, with no bypass |
| Read administrative audit events | `GET /api/v001/admin/audit-events` | Return reverse-chronological opaque-cursor pages with no secret values or request bodies |

The Flickr application key and consumer secret are deployment configuration,
not browser form fields. The deployment operator provisions or rotates them in
the selected managed secret store through authenticated deployment automation.
The FGA administrative control plane exposes only configured/missing status and
an opaque version identifier, never either value. The Google web client ID,
allowed JavaScript origins, exact FGA Google Login Endpoint URI, and approved
`sub` are explicit non-secret deployment configuration and drift-checked
evidence. Google browser authentication adds no Auth0 tenant, Action, custom
claim, or client secret.

The initial allowlist has no public debug route, generic SQL/query console,
secret download, raw log viewer, arbitrary URL fetch, arbitrary Flickr method call, group-pool removal,
permanent submission-block deletion, force-resubmit, queue reorder, terminal-
state rewrite, status-triggered worker wake, retry-now, reopen, cancellation, or
Flickr write-gate bypass. The read-only status routes above do not imply an
administrator power to mutate an intent. The
[OAuth and account lifecycle](oauth-and-account-lifecycle.md) defines the
Flickr-link and administrative-session routes above. It deliberately adds no
self-service account deletion route to the private MVP.

The [installation credential lifecycle](installation-credential-lifecycle.md)
defines the installation routes above. A pending candidate can authenticate
only to `GET /api/v001/installations/current`, which returns its non-secret
`pending_rotation` presented-credential state; only the recent-authenticated
administrative completion POST may broaden it to current normal-route
authority.

An FGA installation credential is accepted only by plug-in API routes. An
administrative session is accepted only by the administrative namespace. The
FGA API backend **MUST NOT** let either credential type authenticate to the
other boundary. Installation credential classes are resolved from the stored
installation record through the plug-in contract's exhaustive fail-closed
allowlist. An unknown class is invalid and never falls through to this browser
session authority.

## Browser and error responses

An unauthenticated top-level navigation under `/admin/` returns `303 See Other`
to the fixed `/admin/login` route. An administrative JSON request never follows
that browser convenience: absent, invalid, expired, or revoked session state
returns a non-oracular `401 Unauthorized` JSON error and no Bearer challenge.
An authenticated request with failed CSRF, origin, recent-authentication, or
operation authorization returns `403 Forbidden`. Schema failure is `400 Bad
Request` or `422 Unprocessable Content` according to the existing FGA JSON
contract; stale gate/session/resource state is `409 Conflict`; rate limiting is
`429 Too Many Requests`; and unavailable identity, database, secret-store, or
Flickr repair dependencies are `503 Service Unavailable`.

The logout route is the narrow idempotency exception to the generic
administrative `401`: an exact-origin request with an absent, unknown, expired,
or already-revoked session returns its fixed no-store `204` plus cookie
expiration. An active session still requires its CSRF token. Database, audit,
or indeterminate-commit failure returns the lifecycle contract's sanitized
`503` without cookie expiration, and the UI reports sign-out as unconfirmed.

Every JSON error uses the existing `schemaVersion`, stable machine code,
non-secret message, and correlation-ID envelope. It never exposes whether a
different Google `sub` would be accepted, which claim failed, whether a
credential or secret-store object exists, or raw upstream error text. No
administrative error response is cacheable.

## One-time credential delivery

For `POST /api/v001/plugin-codes`, the FGA API backend generates the Plugin
Code and its opaque `pluginCodeId` and internal installation ID, computes the
Plugin Code's unsalted SHA2-256 digest, assigns the exact `lrc_plugin`
credential class, and commits the installation row plus successful audit event
in one FGA database transaction before responding. The browser request cannot
choose or override that class. Under
[ADR 0044](decisions/0044-use-canonical-crockford-base32-plugin-codes.md), the
FGA API backend encodes exactly 32 random octets as 52 uppercase canonical
Crockford Base32 symbols in 13 four-symbol groups separated by 12 ASCII
hyphens. The successful JSON response contains `schemaVersion`, `pluginCodeId`,
and that complete 64-character plaintext `pluginCode` exactly once with
`Cache-Control: no-store`; the FGA API backend never persists, logs, traces, or
later reconstructs the plaintext. The stored SHA2-256 input includes the
hyphens.

Refreshing the page, repeating a `GET`, or reopening the installation record
never redisplays the Plugin Code. If the response is lost or Terry is
uncertain whether the plaintext was transferred, the only safe minimum
recovery is to revoke that installation identity and create a new one. The
installation lifecycle adds crash-safe rotation and repair but no plaintext
recovery.

The [private installation credential transfer ceremony](private-install-credential-transfer.md)
is the one supported private-MVP handoff. It requires recent authentication in
a clean private-browsing window on the target Lightroom workstation, local
clipboard history/sync disabled, one user-gesture copy, direct paste into the
FGA LrC plug-in's transient Plugin Code input, simultaneous clear-text
side-by-side comparison with identical grouping and typography, strict
canonical validation without normalization, immediate `LrPasswords` storage
and current-installation read, an explicit non-secret clipboard overwrite, and
closing the private window. The transfer view has no third-party content or browser
persistence and erases its UI reference after five minutes. No claim-code,
polling, download, QR, password-manager, file, URL, or message path is
allowlisted.

Planned replacement uses a second fixed `LrPasswords` candidate key and the
current-installation-read-only candidate described by the
[installation credential lifecycle](installation-credential-lifecycle.md).
The prior credential remains the only normal-route authority until Terry's
administrative completion transaction promotes the verified candidate and
retires the prior version. Revocation
invalidates current and pending versions together. The FGA administrative
control plane reports authoritative server revocation separately from local
endpoint clearing that cannot be proven for a lost workstation.

## FGA audit trail

The FGA database maintains one first-class, append-only `audit_events` relation
for security-relevant FGA User UI and administrative-control-plane activity.
It is logically distinct from domain records and ordinary process logs but
remains in the same private-MVP database so a domain mutation and its success
event can commit atomically. Each event contains:

- a server-generated opaque event ID and database-generated UTC timestamp;
  [ADR 0053](decisions/0053-accept-millisecond-private-database-clocks.md) accepts millisecond
  source resolution for this private deployment. Six fractional digits or
  integer microsecond units do not imply finer resolution; explicit
  sequence/revision fields, not clock uniqueness, supply durable order;
- the internal `fgaUserId` for an authenticated operation,
  or null actor fields plus a sanitized authentication stage for a pre-session
  event;
- the administrative-session correlation ID, never the cookie or its digest;
- the action and opaque target type/ID;
- the request correlation ID;
- `succeeded` or `failed` plus a sanitized reason class; and
- the minimum non-secret before/after security state needed to review the
  change, such as active-to-revoked, gate revision, or secret version ID.

The table excludes installation credential plaintext/digests, Google ID tokens,
Flickr tokens/secrets, consumer secrets, OAuth headers/signatures, CSRF/session
values, request bodies, photo metadata, and arbitrary exception text.

Every successful FGA database mutation and its successful audit event commit in
the same transaction. Every successful Plugin Code collection read appends a
sanitized `plugin_codes.list` event before the FGA Plugin Code API releases the
metadata; if that append cannot be confirmed, the request fails closed and
returns no collection data. An audit-write failure refuses a mutation. An
authenticated rejected or failed operation appends its failure event before
the FGA API backend responds; if the database is unavailable, the FGA HTTPS
edge's sanitized security log remains the failure evidence and the operation
still fails closed. The private MVP performs no automatic audit-event deletion;
backups and restores preserve the table.

Authentication start, success, allowlist rejection, logout, session inventory
and revocation, Flickr link start/callback/disconnection, Plugin Code
list/create/revoke, installation rotation start/complete/cancel, gate-resume
attempt/result, and audit read are auditable actions.
Repeated identical revocation requests remain idempotent and record one initial
state change plus later no-op outcomes.

## Failure handling and isolation

- A failed proactive JWKS refresh retains the last successfully validated key
  set only while its current-authority window remains valid, schedules bounded
  retry, and emits sanitized operational evidence. Monitoring alerts before
  that window expires; the FGA JWKS refresh worker never makes a stale key set
  appear current.
- If Google sign-in, the current Google JWKS, the maintained validation library,
  or required claim evidence is unavailable or invalid, the FGA administrative
  control plane denies new login. Existing FGA API backend requests and worker
  processing continue under their separate credentials.
- If the FGA database is unavailable, no administrative session is created and
  no administrative mutation succeeds. The control plane does not fall back to
  deployment environment variables, a local password, or an installation
  credential.
- A failed or expired CSRF, recent-authentication, route, schema, expected-
  revision, or authorization check performs no mutation and returns a generic
  non-secret error with a correlation ID.
- In the provider-versioned path, the FGA API backend's OAuth handler stages
  a new version before database activation; failure preserves the prior link
  and cleans the unreferenced candidate. ADR 0052's private native alternative
  instead pauses new operations, replaces one credential bundle, and activates
  its matching application generation. Failure can require repair/relink; a
  mismatched bundle or uncertain activation never grants implicit authority.
- Flickr disconnect first removes active database authority and pauses the user
  write gate. Managed-secret deletion failure leaves the link visibly
  `disconnecting` and fail-closed; it never restores or silently retains usable
  authority. Local deletion is not reported as Flickr-side permission removal.
- A Flickr write-gate resume failure leaves the exact gate revision paused and
  follows ADR 0013. No administrative failure clears a permanent photo/group
  submission block.
- Losing the one-time installation-credential response never permits plaintext
  redisplay. Revocation plus new creation is the recovery boundary.
- Administrative HTML/API failures reveal no verifier, issuer/key detail,
  `sub` allowlist, token status, secret-store name, credential digest, or
  internal exception. The corresponding sanitized reason remains auditable.
- A failed or indeterminate logout never clears the cookie, restores the
  scrubbed administrative view, or claims server revocation; the same
  idempotent logout POST remains the first recovery action.

## Standards and security references

- [Google Identity Services overview](https://developers.google.com/identity/gsi/web/guides/overview)
- [Verify the Google ID token on the server](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token)
- [Sign in with Google HTML API](https://developers.google.com/identity/gsi/web/reference/html-reference)
- [GIS setup and Content Security Policy](https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid)
- [NIST SP 800-63B — Authentication Assurance Levels](https://pages.nist.gov/800-63-4/sp800-63b/aal/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Bot Management and Anti-Automation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Bot_Management_and_Anti-Automation_Cheat_Sheet.html)
- [OWASP Cross-Site Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
