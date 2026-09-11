# ADR 0014: Use one allowlisted OIDC owner for private administration

Date: 2026-08-26

Status: Rejected

## Disposition

The Auth0 Universal Login, Authorization Code with PKCE, Auth0 Action, and
provider-specific passkey-claim proposal below was declined on 2026-08-28.
[ADR 0039](0039-use-google-identity-services-browser-sessions.md) instead
accepts direct Google Identity Services authentication, current Google ID-token
validation through the FGA Google Login Endpoint and JWKS cache, and an opaque
server-side FGA browser session. The administrative owner allowlist and
least-privilege operation boundary remain requirements to reconcile in the
administrative contract; a successful Google sign-in is not administrative
authorization.

The remaining text is preserved as the rejected proposal and rationale. It is
not a fallback implementation option.

## Context

The private MVP needs an independently authenticated browser boundary to link
the owner's Flickr grant, create and revoke Lightroom installation credentials,
inspect security state, and repair paused Flickr writes. An uncredentialed FGA
LrC plug-in cannot prove administrator identity. Reusing the long-lived plug-in
bearer credential would collapse two trust boundaries and would leave no safe
bootstrap path.

Building a local username/password, MFA enrollment, reset, and recovery system
would create a
security-critical product inside a single-owner architecture. Delegating
identity proof to a mature OIDC provider keeps the FGA administrative control
plane small while retaining a standards-based application session and audit
boundary.

## Decision

The FGA administrative control plane **MUST** authenticate exactly one owner
through OpenID Connect Authorization Code flow with PKCE `S256`. Deployment
configuration pins the exact immutable `(issuer, subject)` pair. The FGA API
backend validates issuer, audience, signature, time claims, nonce, PKCE, and a
documented authentication-context claim proving phishing-resistant MFA. Email,
display name, source network, Flickr identity, and FGA installation credentials
are not administrator identity.

The implementation uses Auth0 Universal Login and maintained, scoped,
license-compatible Authlib integration selected by ADR 0033. A checked-in Auth0
Post-Login Action denies the FGA application without recorded passkey use and
adds the exact provider-signed namespaced claim required by the administrative
contract. The implementation contains no local password, signup, invitation,
reset, or role-management system.

The private MVP has no unauthenticated device-link or self-service OAuth-start
route. Before `/admin/login` creates state, a shared atomic limiter applies
independent source/deployment buckets and a bounded live-transaction cap.
Callbacks are separately limited, consume exact state once before an upstream
exchange, and never bind to source IP. Limiter unavailability fails closed for
login/callback work. The administrative contract records the initial numeric
limits, privacy-preserving source key, metrics, alerting, and change gate.

After authentication, the FGA API backend issues an opaque 256-bit server-side
administrative session in a `__Host-` `Secure`, `HttpOnly`, `SameSite=Strict`
cookie. The session expires after 30 minutes idle and eight hours absolute.
Security-sensitive mutations require the phishing-resistant authentication to
be no more than ten minutes old.

Every unsafe administrative method also requires a session-bound 256-bit
synchronizer CSRF token in a custom header and the exact FGA origin. SameSite is
defense in depth. The administrative API permits no CORS and uses no ordinary
state-changing GET. Standards-defined OIDC and Flickr OAuth callbacks are
protected by single-use, five-minute server-side transactions and unguessable
state.

The administrative operation set is an explicit allowlist. It covers session
status/inventory/revocation/logout, Flickr link status/authorization/
disconnection, installation identity list/create/rotation/revoke, Flickr
write-gate list/verified resume, read-only group-submission intent status, and
bounded audit-event reads. It has no generic database console, secret viewer,
arbitrary Flickr call, retry/reopen/cancel action, force-resubmit,
permanent-block deletion, or credential-type bypass. The complete wire,
one-time credential, audit, and failure contract is in
[`administrative-control-plane-contract.md`](../administrative-control-plane-contract.md).

Every successful administrative database mutation commits an append-only,
sanitized audit event in the same FGA database transaction. Audit failure
refuses the mutation. The control plane fails closed when identity, session,
CSRF, recent-authentication, database, or audit evidence is unavailable, while
ordinary authenticated FGA API backend work and workers retain their separate
availability boundaries.

## Consequences

- Auth0, Authlib, and Django supply the OIDC, server-side session, and CSRF
  machinery selected by ADR 0033; the future hosted repository must pin and
  test the exact compatible releases.
- Terry maintains one phishing-resistant MFA-capable identity outside FGA and
  uses it only when administrative work is necessary.
- The FGA administrative control plane owns a small server-side session table
  and audit table. It stores no OIDC tokens after login.
- Installation credential bootstrap remains independent from the plug-in and
  preserves ADR 0006's browser-free Lightroom activation.
- Administrative identity-provider failure prevents administrative change but
  does not invalidate already active plug-in credentials or stop healthy queued
  workers.
- Public/multi-user administration still requires a new decision; the retained
  explicit user IDs do not imply roles, invitations, or tenant management.
- Conservative private-admin admission limits bound unauthenticated state and
  upstream cost without creating an attacker-controlled account lockout. They
  are not a public/self-service abuse model.

## Alternatives considered

- **Use the FGA installation credential:** rejected because it is the object
  being provisioned/revoked, has no independent owner proof, and would collapse
  the client and administrator trust boundaries.
- **Implement a local password and MFA system:** rejected because credential
  enrollment, secure password verification, reset, recovery, MFA lifecycle, and
  abuse protection are disproportionate and less trustworthy than a mature
  identity provider for one owner.
- **Rely only on a secret URL, IP allowlist, or VPN location:** rejected because
  location and obscurity are useful deployment layers but are not durable user
  authentication or auditable intent.
- **Use email as the allowlist key:** rejected because it is mutable and can be
  reassigned; the OIDC issuer and subject form the stable identity.
- **Let the hosting provider's dashboard be the only control plane:** rejected
  because application mutations still need least-privilege validation,
  transactional audit, one-time credential delivery, and domain-specific safety
  guards that a generic provider console cannot supply.
