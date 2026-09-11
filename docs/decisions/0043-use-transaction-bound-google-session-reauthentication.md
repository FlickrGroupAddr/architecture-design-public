# ADR 0043: Use transaction-bound Google session reauthentication

Date: 2026-08-31

Status: Accepted by Terry on 2026-08-31

## Context

Accepted [ADR 0039](0039-use-google-identity-services-browser-sessions.md)
selects direct Google Identity Services (GIS) login, a purpose-built server-side
FGA browser session, and a non-sliding 24-hour absolute lifetime. It deliberately
leaves the exact login URI, session rotation, concurrent-session policy,
post-login CSRF, recent authentication, cleanup, and incident invalidation to a
narrower lifecycle contract.

Several rare administrative mutations deserve a proof newer than the surrounding
24-hour session. Reintroducing the rejected Auth0 tenant solely for that proof
would restore an identity runtime, Action, secret, and passkey-claim dependency
that the private MVP otherwise does not need. Implementing an FGA password or a
custom passkey enrollment and recovery system would create a second account
recovery boundary for one private administrator.

GIS can mint an ID token containing an application-provided nonce and return an
application-provided button state value. A fresh ID token can therefore be bound
to one short-lived server transaction and to the exact existing FGA browser
session being reauthenticated. It cannot prove that Google required Terry to
re-enter a password, activate a passkey, or complete a phishing-resistant
challenge; Google's existing account session may satisfy the interaction.

## Decision

The exact GIS form-post target is `POST /admin/google-login`. An initial
`GET /admin/login` creates one five-minute, single-use login transaction. The FGA
API backend generates independent 256-bit state and nonce values, stores only
their unsalted `SHA2-256` digests, and configures the rendered GIS button with the
plaintext values. The FGA Google Login Endpoint requires the matching GIS
cookie/body CSRF pair, resolves the state transaction, validates the Google ID
token and its exact nonce, and consumes the transaction in the same database
transaction that creates the FGA browser session and successful audit event.

The initial session and every replacement use the exact cookie name
`__Host-fga_admin`. The cookie and server record retain ADR 0039's non-sliding
24-hour absolute lifetime. Each session receives an independent 256-bit
synchronizer CSRF token that browser code keeps only in memory and sends in
`X-CSRF-Token` with the exact FGA origin on unsafe API requests.

A sensitive operation accepts only a session whose server-recorded
`recentAuthenticationAt` is no more than five minutes old when the operation is
admitted. If the proof is stale, the attempted mutation creates no pending work
and returns `403 recent_authentication_required`. The UI must ask Terry to review
the operation again after reauthentication.

The authenticated UI begins reauthentication with
`POST /api/v001/admin/session/reauthentication`. The endpoint requires the
current session, exact origin, and session CSRF token, then creates another
five-minute, single-use state/nonce transaction bound to that session and its
`fgaUserId`. The GIS UI uses an explicit Sign in with Google button with automatic
selection disabled. The FGA Google Login Endpoint accepts the result only when
the validated canonical issuer and `sub` resolve to the same `fgaUserId` and the
ID token contains the exact transaction nonce. Success atomically consumes the
transaction, revokes the prior session, creates a new 256-bit session token and
CSRF token, records `recentAuthenticationAt`, appends the sanitized audit event,
and returns the replacement cookie. Failure leaves the old session unchanged.

This mechanism is named **recent Google reauthentication** within FGA, but its
assurance is stated precisely: it proves a newly issued, nonce-bound Google
assertion for the same account and a new user-initiated GIS button flow. It does
not claim fresh Google authenticator use, authentication assurance level,
multi-factor authentication, user presence at a local authenticator, or phishing
resistance. The server does not use the unsigned GIS `select_by` value as a
security input and does not infer freshness from ID-token `iat`, `exp`, or an
optional `auth_time` value.

The private MVP allows multiple independent browser sessions. A new ordinary
login does not revoke other sessions, and there is no arbitrary active-session
count limit beyond the accepted login admission controls and 24-hour expiry.
Reauthentication rotates only its bound current session. Current authorization
is evaluated on every request; no administrator role or allowlist result is
cached as session authority. A future privilege model must rotate the session on
elevation and requires a new accepted decision.

The principal's aggregate `sessionSetRevision` increments exactly once per
committed transaction that explicitly creates or revokes any number of active
sessions. Another tab holding a CSRF token invalidated by rotation receives no
automatic replay: it refreshes the current session and asks Terry to review and
submit the action again, or scrubs the administrative view and returns to login
when the session cannot be refreshed.

The detailed record, revocation, retention, cleanup, incident, response-loss,
and conformance rules are in the accepted
[browser-session lifecycle contract](../browser-session-lifecycle.md).

## Consequences

- The private MVP gains a meaningful stolen-session defense for sensitive
  mutations without creating a local FGA password, passkey-recovery ceremony, or
  second identity provider.
- The UI adds one explicit Google button interaction when the five-minute proof
  is stale. The protected mutation is never replayed automatically afterward.
- One-time state and nonce records add a small bounded table and cleanup task.
- Multiple windows remain usable and an independently authenticated session can
  revoke an orphan after an ambiguous logout.
- The implementation and UI must not describe this mechanism as a fresh factor,
  MFA, passkey verification, or phishing-resistant step-up.

## Alternatives considered

- **Restore Auth0 only for a passkey claim:** rejected because it recreates a
  provider tenant, secret, callback, Action runtime, and recovery dependency for
  a private single-administrator deployment.
- **Implement an FGA password or direct WebAuthn registration:** rejected for the
  private MVP because enrollment, multiple-authenticator support, loss recovery,
  and privileged reset would become a second authentication product.
- **Treat any fresh GIS ID token as proof without state and nonce:** rejected
  because a still-valid assertion could be replayed and would not be bound to the
  current FGA session or one intended interaction.
- **Trust `select_by`, `iat`, `exp`, or optional `auth_time` as the step-up:**
  rejected because those values do not establish the exact property FGA needs;
  `select_by` is not a signed claim, token issue/expiry is not authenticator use,
  and GIS does not promise a fresh phishing-resistant challenge.
- **Allow only one active session:** rejected because it makes ordinary private
  windows and ambiguous-logout recovery fight each other without materially
  strengthening a 24-hour, inventory-and-revocation-controlled private system.
- **Require only the existing session and a confirmation dialog:** rejected for
  the named sensitive mutations because it gives a stolen session no additional
  boundary.

## Controlling references

- [Sign in with Google HTML API reference](https://developers.google.com/identity/gsi/web/reference/html-reference)
- [Sign in with Google JavaScript API reference](https://developers.google.com/identity/gsi/web/reference/js-reference)
- [Verify the Google ID token on the server](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token)
- [NIST SP 800-63B session management](https://pages.nist.gov/800-63-4/sp800-63b/session/)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
