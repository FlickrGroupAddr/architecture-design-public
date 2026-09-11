# Browser-session lifecycle contract

Last updated: 2026-08-31

Status: Accepted normative contract under accepted ADRs 0039 and 0043; Terry
accepted the complete lifecycle mechanics on 2026-08-31

Authority: Accepted normative contract

## Purpose and scope

This contract closes the browser-session mechanics intentionally omitted by the
authoritative tab-1 interaction map and accepted
[ADR 0039](decisions/0039-use-google-identity-services-browser-sessions.md). It
defines the exact login route, database record, cookie and CSRF lifecycle,
rotation, concurrent sessions, recent Google reauthentication, revocation,
retention, cleanup, and incident invalidation for the private single-user MVP.

The [OAuth and account lifecycle](oauth-and-account-lifecycle.md) continues to
own the detailed logout response-loss state machine. The
[administrative control-plane contract](administrative-control-plane-contract.md)
continues to own the operation allowlist and authorization policy. This contract
does not grant browser authority to the FGA LrC plug-in or equate an FGA browser
session with a Flickr grant, installation credential, or Google Account session.

## Fixed routes and time limits

| Item | Exact contract |
| --- | --- |
| Login page | `GET /admin/login` |
| GIS form-post target | `POST /admin/google-login` |
| Current-session resource | `GET /api/v001/admin/session` |
| Reauthentication start | `POST /api/v001/admin/session/reauthentication` |
| Current-session logout | `POST /api/v001/admin/session/logout` |
| Session inventory | `GET /api/v001/admin/sessions` |
| Revoke another session | `POST /api/v001/admin/sessions/{sessionId}/revocation` |
| Revoke all other sessions | `POST /api/v001/admin/sessions/revoke-others` |
| Cookie | `__Host-fga_admin` |
| Absolute session lifetime | 24 hours from creation or successful reauthentication; non-sliding |
| Idle timeout | None for the private MVP |
| Recent-authentication window | Five minutes from successful initial login or reauthentication |
| Login/reauthentication transaction lifetime | Five minutes; single use |
| Revoked/expired session-row retention | 30 days after terminal time |
| Consumed/expired transaction-row retention | At most 24 hours after terminal time |

All deadlines are server-side instants. Client clocks, cookie presence, database
cleanup, page activity, polling, and last-activity observations neither extend
nor revive authority.

## Login transaction and exact endpoint

`GET /admin/login` is the bounded login-start exception to the rule that an
ordinary `GET` does not create server state. After the administrative login
admission controls succeed, the FGA API backend generates independent 256-bit
state and nonce values with its runtime or operating system CSPRNG. It stores
only `SHA2-256(state)`, `SHA2-256(nonce)`, purpose `initial_login`, creation and
expiry times, one-use state, and a fixed same-origin success destination. The
response uses the plaintext values only to configure Google's supported GIS
button. It never places either value in a URL, log, metric, or persistent browser
storage.

GIS posts `credential`, `state`, and matching cookie/body `g_csrf_token` values
to exact route `POST /admin/google-login`. The FGA Google Login Endpoint applies
the accepted admission limit, bounded form parsing, and GIS CSRF comparison
before ID-token processing. It resolves one unexpired transaction without
revealing whether a supplied state existed and validates the ID token with the
accepted maintained-library and JWKS-cache rules, including the exact nonce.
The unsigned `select_by` form value is diagnostic-only and never authorizes,
identifies, or establishes recent authentication.

Successful identity mapping, transaction consumption, session creation, the
principal session-set revision increment, and the sanitized
`authentication.login_succeeded` audit event commit in one database transaction
before the response sets the cookie. A database or audit failure creates no
session and does not consume a transaction in a separate commit. A committed
transaction can never mint a second session after response loss or replay.

The success response is `303 See Other` to the transaction's fixed same-origin
destination and sets:

```http
Set-Cookie: __Host-fga_admin=<256-bit-random-value>; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=86400
```

The cookie has no `Domain` attribute. Every login, reauthentication, and logout
response is `Cache-Control: no-store`.

## Session record

Each session row has exactly these security and lifecycle fields, plus ordinary
database bookkeeping needed to implement their constraints:

| Field | Contract |
| --- | --- |
| `sessionId` | Server-generated non-secret opaque 128-bit random identifier exposed only for inventory/revocation |
| `tokenDigest` | Unique 32-byte `SHA2-256` digest of the complete 256-bit cookie token; plaintext is never stored |
| `fgaUserId` | Ownership foreign key resolved from canonical Google issuer plus validated `sub` |
| `googleIssuer` and `googleSub` | Canonical validated identity values required by the private owner policy |
| `csrfToken` | Independent 256-bit synchronizer token; never used as authentication and never logged |
| `createdAt` | Server commit time for the current token |
| `recentAuthenticationAt` | Server commit time of the nonce-bound Google assertion that created this token |
| `expiresAt` | Exactly `createdAt + 24 hours`; immutable |
| `lastActivityAt` | Advisory time of a successful authenticated request; never extends authority |
| `revokedAt` and `revocationReason` | Nullable terminal revocation evidence; no unrevocation transition exists |
| `revision` | Monotonic per-session compare-and-set revision |
| `creationCorrelationId` | Non-secret link to the sanitized creation audit event |

Required profile display fields live on the FGA user record rather than being
copied into every session. The session contains no Google ID token, complete
claim map, Google access or refresh token, cookie plaintext, IP address, raw user
agent, browser fingerprint, Flickr secret, or installation credential.

`lastActivityAt` begins at `createdAt`. After a request has authenticated and
authorized normally, the FGA API backend may advance it at most once per five
minutes per session. The coalesced observation is not an audit event, security
decision, idle timer, or prerequisite for returning the already-authorized
response. Failure to advance it is observable operational degradation but does
not falsely reject an otherwise verified request.

The principal owns a monotonic `sessionSetRevision`. Each committed transaction
that explicitly creates or revokes one or more active sessions increments it
exactly once, regardless of the number of rows changed. Ordinary login,
reauthentication rotation, revoking one session, revoking all other sessions,
and incident invalidation therefore each increment it once. Time-based expiry
and deletion of already-terminal rows do not increment it because they cannot
add or restore authority.

## Session authentication and CSRF

For every protected request, the FGA API backend computes
`SHA2-256(presented cookie)`, performs one exact unique lookup, checks that the
row is not revoked and `now < expiresAt`, resolves the current principal, and
applies the current authorization policy. Missing, malformed, unknown, expired,
and revoked values receive the same non-oracular `401` JSON response. An expired
cookie may be cleared with the fixed cookie attributes, but client deletion is
not the authority decision.

No administrator flag or allowlist result is cached in the session row. Removing
the Google `sub` from the deployment's current owner policy denies the very next
request even if the session row remains active. The private MVP has no role
elevation. A future privilege model must rotate the session on elevation and
requires a new accepted decision.

Each new session has a new independent 256-bit CSRF synchronizer token. The
current-session resource returns it over same-origin HTTPS in a no-store JSON
response after cookie authentication. Browser code holds it only in memory; it
does not write it to a cookie, URL, HTML source, local storage, session storage,
log, or telemetry. Every unsafe API request supplies it as `X-CSRF-Token` and
supplies exact `Origin: https://flickrgroupaddr.com`. The FGA API backend compares
the token in constant time and rejects missing, null, or different origins.
CORS remains disabled. Session rotation invalidates the old CSRF token.

Another tab that retained the old CSRF token after rotation receives a CSRF
rejection before its next unsafe request mutates state. The browser UI never
replays that request automatically. It fetches the current-session resource and,
on success, replaces the stale in-memory session and CSRF state, says **Your FGA
administrative session changed in another tab. Review and submit this action
again.**, and requires a new user submission. If the current session cannot be
refreshed, the UI scrubs the administrative view and returns to login.

The logout state machine may retain the current in-memory CSRF token only long
enough to retry an unconfirmed logout. A `401`, confirmed logout, or successful
session rotation erases it from the in-memory view model.

## Recent Google reauthentication and rotation

The sensitive operations named by the administrative and installation
credential contracts require `now - recentAuthenticationAt <= 5 minutes` when
the FGA API backend admits the mutation. Boundary equality is accepted; a later
commit may finish normally after admission. A stale proof returns
`403 recent_authentication_required` and no pending mutation, credential,
authorization transaction, or queued work survives for automatic continuation.

The UI starts reauthentication with
`POST /api/v001/admin/session/reauthentication`. This request requires the active
session, exact origin, and CSRF token. The FGA API backend creates independent
256-bit state and nonce values and stores their digests in a five-minute,
single-use transaction with purpose `reauthentication`, bound `sessionId`, bound
`fgaUserId`, creation/expiry times, and a fixed same-origin return destination.
The response returns the plaintext state, nonce, and expiry once so the UI can
render Google's supported Sign in with Google button. Automatic and One Tap
selection are disabled for this interaction.

The FGA Google Login Endpoint applies the ordinary GIS CSRF and Google-token
validation rules, then additionally requires all of the following:

- the transaction is unexpired, unused, and has purpose `reauthentication`;
- the signed ID-token nonce exactly matches the transaction nonce;
- canonical issuer plus validated `sub` resolves to the transaction's exact
  `fgaUserId`;
- the bound old session still exists, is active, and has not reached its
  absolute expiry; and
- the transaction, session, and principal revisions still permit one
  compare-and-set commit.

Success atomically consumes the transaction, revokes the bound old session with
reason `reauthenticated`, creates a wholly independent token and CSRF value,
sets `createdAt = recentAuthenticationAt = now`, sets the new 24-hour
`expiresAt`, increments the principal session-set revision, and appends both
sanitized rotation and login-success audit evidence. Only then does it replace
the cookie and return `303` to the fixed review destination. Every failure leaves
the old session and its cookie unchanged and never returns replacement secret
material.

This proves a newly minted, nonce-bound Google assertion for the same account.
It does not prove that Google asked for a password, passkey, MFA, physical user
presence, or a phishing-resistant challenge. The UI says **Confirm your Google
Account to continue**, not **Verify your passkey**, **Complete MFA**, or another
stronger claim. Initial login receives the same five-minute recent window.

## Concurrent sessions and revocation

The private MVP permits multiple active sessions. Ordinary login creates one
session without revoking others. There is no arbitrary active-session cap;
admission limits and the fixed 24-hour expiry bound creation and authority. The
inventory is the user's control for recognizing and terminating other sessions.

`GET /api/v001/admin/sessions` returns reverse-chronological opaque-cursor pages
of at most 50 rows for the current `fgaUserId`, plus the current
`sessionSetRevision`. Each item contains only `sessionId`, `revision`,
`createdAt`, `recentAuthenticationAt`, `lastActivityAt`, `expiresAt`, derived
state `active`, `expired`, or `revoked`, nullable `revokedAt`, and `isCurrent`.
It returns neither credential material nor a network/browser fingerprint.

`POST /api/v001/admin/sessions/{sessionId}/revocation` requires recent Google
reauthentication, exact origin, CSRF, and JSON `schemaVersion: 1` plus the target
`expectedRevision`. The route refuses the current session with
`409 current_session_requires_logout`; logout owns that transition. For a
non-current row, an active exact revision is atomically revoked with reason
`user_revoked` and its audit event. An unknown ID and an already-terminal row
produce the same no-store `204` after authorization; stale known active state
returns `409 stale_session_revision`.

`POST /api/v001/admin/sessions/revoke-others` requires recent Google
reauthentication, exact origin, CSRF, and JSON `schemaVersion: 1`,
`expectedSessionSetRevision`, and `expectedActiveOtherSessionCount`. One
transaction locks the principal session set, rejects a stale revision or count
with `409 stale_session_set`, revokes every other active session with reason
`user_revoked_others`, appends the sanitized audit evidence, increments the set
revision once, and preserves the exact current session. Success is no-store
`204`.

Current-session logout continues to follow the separately specified idempotent
commit-before-cookie-expiration state machine. A failed or indeterminate logout
never turns cookie deletion or UI clearing into proof of revocation.

Every revocation is effective on the next request and survives process restart.
It cannot recall a response already returned, terminate the independent Google
Account session, disconnect Flickr, or revoke an FGA installation credential.
No ordinary API exposes an unrevocation operation.

## Expiry, retention, and cleanup

Session authentication rejects a row at `now >= expiresAt` without waiting for
a worker to mark or delete it. Derived state is `revoked` when `revokedAt` is set
and otherwise `expired` after the deadline. Revocation wins the displayed state
when both conditions are true because it records an explicit action.

The FGA database retains expired and revoked session rows for 30 days after
`max(expiresAt, revokedAt)` so session inventory, ambiguous-logout recovery, and
incident review have bounded evidence. An idempotent cleanup task runs at least
hourly, deletes terminal session rows past that deadline in bounded batches,
and deletes consumed or expired login/reauthentication transactions no later
than 24 hours after their terminal time. It never deletes an active session,
changes an expiry, clears a revocation, or treats its own delay as continued
authority.

Cleanup failure alerts and retries with bounded backoff. It does not make the
FGA API backend accept an expired/revoked session or make readiness depend on a
successful deletion pass. Sanitized audit events follow their separately
accepted retention policy and are not deleted merely because their session row
ages out.

## Incident invalidation

Suspected disclosure of an FGA browser cookie, CSRF token paired with a cookie,
session-bearing browser profile, or authentication handler requires revocation
of every potentially affected session. The operator uses a narrowly scoped
deployment command, not a public or administrative web bypass. In one database
transaction it locks the affected principal or complete private deployment,
revokes every active matching session with reason `security_incident`, increments
the session-set revision, and appends one sanitized incident invalidation event
with an operator-supplied non-secret incident reference.

If the FGA database is unavailable, normal session verification already fails
closed. The deployment does not restore administrative readiness after database
recovery until the required invalidation transaction succeeds. The command
never logs token/CSRF material and never asks for a cookie value merely to revoke
the whole principal.

Changing the owner allowlist takes effect immediately at request authorization
whether or not invalidation has run. Exposure of only high-entropy token digests
does not make those digests usable as cookies, but database compromise still
triggers credential review and may conservatively use the same all-session
invalidation. Compromise of a framework-signing key follows its dedicated
operations contract and also revokes every administrative session before the
new version is promoted.

## Required conformance evidence

Implementation acceptance must prove at least:

- exact cookie spelling and attributes on login, reauthentication, and logout,
  including absence of `Domain`;
- 256-bit independent CSPRNG values and `SHA2-256` verifier storage for session
  tokens, transaction state, and transaction nonce;
- missing/mismatched GIS CSRF, state, nonce, issuer, subject, audience,
  signature, key, or time authority creates no session and no partial commit;
- transaction replay and concurrent consumption create at most one session;
- reauthentication rotates only the bound session, invalidates its old cookie
  and CSRF value, preserves unrelated sessions, and never carries a pending
  mutation across the boundary;
- five-minute recent-auth boundary values and the immutable 24-hour deadline;
- ordinary login concurrency, inventory scoping/pagination, single-session
  revocation, revoke-others revision/count races, and current-session refusal;
- exact-origin and CSRF failure does not mutate or expire any session;
- logout failure injection required by the OAuth/account lifecycle contract;
- expired and revoked rows fail authentication before cleanup and cleanup never
  deletes an active row;
- owner-allowlist removal denies the next request without trusting cached
  session authority; and
- incident invalidation, database outage, restart, and signing-key compromise
  all fail closed and cannot revive a session.

The architecture repository contains no production FGA API backend, database
migration, browser UI, cleanup job, or operator command. These cases are
required implementation gates, not claims that executable evidence exists here.

## References

- [ADR 0039 — Google Identity Services and opaque FGA sessions](decisions/0039-use-google-identity-services-browser-sessions.md)
- [ADR 0043 — transaction-bound Google session reauthentication](decisions/0043-use-transaction-bound-google-session-reauthentication.md)
- [Administrative control-plane contract](administrative-control-plane-contract.md)
- [OAuth and account lifecycle](oauth-and-account-lifecycle.md)
- [Session-signing key candidate](operations/session-signing-key.md)
- [Google GIS HTML API reference](https://developers.google.com/identity/gsi/web/reference/html-reference)
- [Google GIS JavaScript API reference](https://developers.google.com/identity/gsi/web/reference/js-reference)
- [Google server-side ID-token validation](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token)
- [NIST SP 800-63B session management](https://pages.nist.gov/800-63-4/sp800-63b/session/)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
