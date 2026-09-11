# ADR 0039: Use Google Identity Services with opaque FGA browser sessions

Date: 2026-08-28

Authoritative interaction-map designation accepted: 2026-08-28

Proactive JWKS refresh amendment accepted: 2026-08-30

Status: Accepted

## Context

FGA needs a browser sign-in boundary for its hosted user interface and private
administrative control plane. The earlier proposed design routed that boundary
through Auth0 Universal Login and a full OpenID Connect Authorization Code flow.
During the clean-room authentication review, Terry chose the smaller direct
integration already supported by Google Identity Services (GIS): Google proves
the Google Account, while FGA components own their own application session.

The Google assertion is a short-lived login credential, not an FGA session.
Persisting the complete decoded claim map would retain unnecessary personal
data, encourage dependence on stale or incidental claims, and still would not
define FGA expiry, revocation, or authorization semantics.

## Decision

The JAMstack frontend uses the Sign in with Google authentication experience.
Authentication and Google API authorization remain separate; an FGA sign-in
does not request a Google access or refresh token.

Under [ADR 0041](0041-use-clean-room-authentication-tabs-as-interaction-authority.md),
tab 1 of the
[clean-room authentication diagram](../diagrams/clean-room-authentication-legal.drawio)
is the authoritative happy-path interaction map for this decision. Its numbered
actors, ordering, trust/persistence boundaries, and explicit security invariants
control. This ADR and narrower contracts own unpictured validation detail,
failure behavior, and session lifecycle mechanics.

After the user approves sign-in, GIS sends an HTTPS `POST` to the FGA Google
Login Endpoint. The request carries the Google-signed ID token in `credential`
and the GIS CSRF value both in the `g_csrf_token` cookie and in the request body.
The endpoint rejects a missing or unequal pair before processing the ID token.

The FGA Google Login Endpoint validates the ID token with a maintained Google
authentication library and a backend cache of Google's current public JWKS. It
follows Google's current server-side requirements, including trusted
algorithm/key selection, signature validation, exact configured audience,
accepted Google issuer, and applicable time claims.

A hosted timer invokes the FGA JWKS refresh worker outside login requests. The
worker refreshes by the earlier of six hours after the preceding successful
refresh and a safety margin before the current Google response's published
freshness expiry. It applies jitter, bounded timeouts and backoff, and a
deployment-wide single-flight boundary; validates the response before atomically
replacing the shared cache; and never destroys the last successfully validated
key set merely because a refresh attempt fails. Google's cache metadata, not
the six-hour maximum interval, remains the freshness authority.

After admission and the GIS CSRF check, an ID token naming an unknown signing
key ID may make that login join or initiate one bounded, coalesced refresh. The
FGA Google Login Endpoint retries key selection once against the resulting
cache and otherwise rejects the login. A request cannot force repeated or
unconditional upstream refreshes. Login fails closed whenever the endpoint
cannot establish current validation authority.

Only the validated, canonical Google issuer and `sub` pair identifies the
external Google Account. The FGA database maps that pair uniquely to one
server-generated, opaque, non-secret internal `fgaUserId`. The FGA Google Login
Endpoint atomically resolves or creates that mapping before it creates the FGA
browser session. All FGA-owned resources use `fgaUserId` as their ownership key;
neither a browser request nor an identity-provider profile field can choose it.

Successful identity mapping, browser-session creation, and the sanitized
`authentication.login_succeeded` audit event commit in one FGA database
transaction before the endpoint sets the cookie. An audit-write failure creates
no usable session. Rejected login attempts append a sanitized failure event when
the database is available; before identity validation, the actor remains null
and the event records only the failed stage and request correlation ID. Neither
event class contains the Google assertion, session token or digest, CSRF value,
profile claims, request body, or arbitrary exception text.

Email, display name, picture, locale, hosted-domain presentation, source
address, Flickr identity, and FGA installation credentials are not stable FGA
user identity. Email is mutable display metadata, never a primary key, foreign
key, ownership selector, or authorization input. The FGA session database
retains `fgaUserId`, the validated Google `sub` needed by the private owner's
authorization policy, only the validated profile fields that a named FGA
component actually needs, and explicit FGA session metadata. It does not retain
the complete decoded Google claim map, the Google ID token, a Google access or
refresh token, or the plaintext FGA session token.

For each successful login, the FGA Google Login Endpoint generates 256
independent random bits with its runtime or operating system cryptographically
secure random generator. It returns only that opaque token to the Browser. The
FGA session database uses the unsalted `SHA2-256` digest of the complete token
as its one-way lookup key. A uniformly random 256-bit token does not need a
password KDF, per-token salt, or an additional HMAC to resist offline guessing.

The Browser receives the opaque value only in a cookie with a `__Host-` name,
`Secure`, `HttpOnly`, `Path=/`, and `SameSite=Strict`, and no `Domain`
attribute. The cookie has `Max-Age=86400`, and the corresponding server-side
session has the same non-sliding 24-hour absolute expiry with no shorter idle
timeout. FGA frontend code cannot read the token. The Google ID token never
becomes the browser's ongoing FGA credential.

Successful Google authentication does not itself grant administrative
authority. The FGA administrative control plane applies its exact owner
allowlist and operation policy after resolving the server-side FGA session.
Plug-in installation credentials remain a separate Bearer-authentication
boundary.

This decision selects Google as the external browser identity provider only.
It does not select the FGA authoritative-DNS, CDN, backend-hosting, database, or
managed-secret providers. Those deployment providers remain undecided.

Accepted [ADR 0043](0043-use-transaction-bound-google-session-reauthentication.md)
and the accepted [browser-session lifecycle
contract](../browser-session-lifecycle.md) define the exact login URI,
cookie-name suffix, remaining session-record fields, rotation,
concurrent-session policy, revocation, logout transaction, cleanup, post-login
CSRF, recent-authentication, and incident invalidation rules.
The authoritative interaction tab does not decide mechanics it does not depict.

## Consequences

- The Auth0 Universal Login, Auth0 Action, custom passkey claim, token exchange,
  PKCE, nonce, and Authlib integration proposed by ADR 0014 are not part of the
  accepted browser-login path.
- The FGA API backend owns a small purpose-built session table and shared Google
  JWKS cache. The FGA JWKS refresh worker normally refreshes that cache outside
  login requests, while a maintained library owns JWT parsing and cryptographic
  validation.
- FGA resource tables reference the stable internal `fgaUserId`; changing a
  display email does not orphan, merge, or transfer ownership of those records.
- Google key rotation is an ordinary cached external dependency. Scheduled
  metadata-driven refresh keeps the normal login path local. A login naming an
  unknown signing key may wait for one bounded refresh, but validation never
  falls back to an untrusted key or unsigned payload.
- Database disclosure reveals only one-way verifiers for high-entropy session
  tokens, minimized user/session records, and no reusable Google assertion.
- Google sign-in availability affects new FGA browser sessions but does not
  invalidate already active plug-in installation credentials or stop healthy
  queued workers.
- The accepted lifecycle contract must be implemented before the hosted service
  relies on its rotation, logout, revocation, cleanup, CSRF-after-login, or
  administrative-recent-authentication details.

## Alternatives considered

- **Auth0 Universal Login with Authorization Code and PKCE:** rejected for the
  current FGA browser boundary because it adds another identity tenant, client
  secret, redirect transaction, token exchange, Action runtime, custom claim,
  and operational dependency without an unmet FGA requirement.
- **Persist the complete decoded Google claim map:** rejected because most
  claims are unnecessary, can become stale, and do not define an FGA session.
- **Use the Google ID token as the FGA session:** rejected because it couples
  application-session lifetime and revocation to a login assertion and exposes
  more claim data throughout the application.
- **Store the opaque token as the database key:** rejected because the
  `SHA2-256` verifier gives a cheap one-way-at-rest boundary without changing
  client behavior.
- **Use email as user identity:** rejected because Google directs relying
  parties to use `sub`; email can change and is not uniformly authoritative.

## Controlling references

- [Google Identity Services overview](https://developers.google.com/identity/gsi/web/guides/overview)
- [Verify the Google ID token on the server](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token)
- [Google OpenID Connect — obtain user information from the ID token](https://developers.google.com/identity/openid-connect/openid-connect#obtainuserinfo)
- [ADR 0041 — authoritative clean-room interaction maps](0041-use-clean-room-authentication-tabs-as-interaction-authority.md)
- [Clean-room authentication diagram notes](../diagrams/README.md#session-token-semantics-in-the-authentication-diagram)
- [Accepted browser-session lifecycle contract](../browser-session-lifecycle.md)
