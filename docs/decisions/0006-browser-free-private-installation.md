# ADR 0006: Provision the private installation without a plug-in browser flow

Date: 2026-08-21

Administrative authentication supplement accepted under ADR 0039: 2026-08-28

Plugin Code naming and FGA User API amendment accepted: 2026-08-28

Canonical Plugin Code presentation amendment accepted: 2026-09-03

Status: Accepted

Phase 1 in full—Part 1 hosted-Flickr authorization and Part 2
Lightroom-installation credential provisioning—was reviewed and accepted as-is by Terry on
2026-08-21. This includes the opaque 256-bit credential, absent HMAC tag, and
unsalted SHA2-256 server verifier.

## Context

A fresh Lightroom host has no FGA credential in `LrPasswords`. An empty client
cannot authenticate itself: secure bootstrap requires either a pre-established
secret, an independently authenticated approval channel, or a trusted user
identity flow.

Browser/device pairing can provide that approval for a public product, but it
adds browser sessions, polling secrets, pairing expiry, rate limiting, and
ambiguous-delivery recovery. The private MVP already has an administrator who
controls the hosted service and can perform the bounded same-workstation
transfer in ADR 0018. The
Lightroom SDK also has no documented cryptographically secure random source, so
the plug-in must not generate its own credential or proof-of-possession key.

The thing provisioned in advance is one server-side Lightroom installation
identity and its credential, not a special plug-in binary. Downloading or
installing the common plug-in package may occur before or after provisioning;
the credential is required only before that installation can activate and make
authenticated FGA requests.

## Decision

Provision the private MVP's Lightroom installation administratively without
requiring or integrating with the Lightroom host's browser:

The FGA User UI action is labeled **Create Plugin Code**. `Plugin Code` is the
user-facing name for the complete opaque installation credential described
below; it does not register a special plug-in binary or mean a short device
code. ADR 0040 fixes its collection API.

1. The FGA API backend generates 32 octets from its runtime or operating system
   cryptographically secure random generator and encodes them as the canonical
   grouped Crockford Base32 Plugin Code specified by ADR 0044.
2. The FGA database stores the credential's SHA2-256 digest, server-assigned
   non-null `lrc_plugin` class, installation/user association, and
   active/revoked state, not its plaintext. The administrative request cannot
   select or override the class.
3. The FGA User UI displays the plaintext Plugin Code exactly once.
   Terry transfers it through the same-workstation private-window and local-
   clipboard ceremony defined by ADR 0018.
4. The FGA LrC plug-in displays the FGA User UI Plugin Code URL and a transient
   Plugin Code input. The photographer obtains the value through that user
   flow, pastes it into the input, and compares the browser and plug-in's
   simultaneous clear-text values with identical fixed grouping and typography.
   The FGA LrC plug-in strictly validates the canonical spelling without repair,
   immediately stores it with `LrPasswords`, and clears the ordinary UI value.
5. The plug-in presents the opaque credential as
   `Authorization: Bearer <FGA installation credential>` over HTTPS to
   `GET /api/v001/installations/current`. The request has no body, query
   parameter, or client-supplied profile.
6. The FGA API backend hashes and verifies the credential server-side. A
   current match returns `200 OK` plus a minimal active-installation
   representation with `presentedCredentialState: "current"`, after which the
   FGA LrC plug-in marks its FGA connection authenticated and proceeds to
   ordinary hosted API calls.

The resource read creates no server-side session and returns no replacement token.
Every later hosted API request still presents and independently authenticates
the installation credential with the same `Authorization` header. The
credential is never placed in a URL, query parameter, or request body.

The internal `lrc_plugin` credential class is version-neutral and server-
assigned. It is neither supplied by the request nor returned by the resource.
A future concrete second profile may add explicit capability representation or
negotiation without renaming the current-installation resource or silently
changing API `v001`. ADR 0032 records this amendment to the unreleased route.

Use the standard `Authorization` field and `Bearer` wire syntax because the LrC
15.3 SDK explicitly supports caller-provided headers and shows an
`Authorization` header in its `LrHttp` example. Do not use an HTTP cookie. The
SDK documents `Set-Cookie` response parsing but no persistent browser-style
cookie jar or `HttpOnly` protection contract; Lua code that manually stores and
resends the value would not gain the browser isolation that `HttpOnly` exists
to provide. The wire format follows
[RFC 9110 §11.6.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-11.6.2)
and [RFC 6750 §§1 and 2.1](https://www.rfc-editor.org/rfc/rfc6750.html#section-2.1),
which explicitly defines a general HTTP authorization method for bearer tokens
from any source. The full source-to-decision map is in the
[plug-in/service contract](../plugin-service-contract.md#standards-and-best-practice-map).

Follow RFC 6750 error semantics. A malformed request envelope, request body,
query parameter, duplicate authorization field, or multiple token transport
returns `400 Bad Request` with `invalid_request`. Missing
authentication returns `401 Unauthorized` with a bare Bearer challenge. A
malformed token value or a credential that is unknown, inactive, expired,
revoked, disabled, or fails any signature, integrity, or verification check
returns the same nonspecific `401 Unauthorized` with `invalid_token`. Reserve
`403 Forbidden` for a successfully authenticated installation that lacks
permission for the requested action or resource.

The installation record stores non-null credential class `lrc_plugin`. The
FGA API backend resolves it through an exhaustive class-to-route/method
allowlist on every request. Null, corrupt, retired, differently cased, or
future unknown classes fail as `401 invalid_token`; no default branch maps one
to browser, administrator, legacy, or another client authority. No client-
supplied field can create or override stored authority. The plug-in/service contract defines the
database constraint, forward-version deployment order, safe rollback behavior,
and required authorization regression tests.

An earlier draft returned `403` for any syntactically well-formed but invalid
credential in an attempt to avoid disclosing which verification check failed.
Reject that distinction. Syntactic parsing is not authentication, a uniform
`401 invalid_token` still reveals no failed check, and differing from standard
Bearer behavior adds no value while surprising clients, middleware, operators,
and Future Terry.

The Flickr OAuth authorization needed to provision the hosted service may use
an administrative browser on any trusted machine. That flow begins in FGA's
administrative control plane; the plug-in neither starts it nor receives its
Flickr credentials. It is not part of Lightroom client activation or routine
publishing.

An OAuth device-authorization flow would instead have the plug-in request a
temporary device code, tell the photographer to approve it in a browser, and
poll until FGA could issue the installation credential. A smart-TV-style flow
normally uses a browser on a second device rather than requiring the constrained
client to launch one. This decision avoids that flow as well as a host-browser
callback flow; it does not claim that device authorization inherently launches
a browser from the client.

## Rejected credential embellishments

Do not append an HMAC tag to the opaque Lightroom credential. HMAC provides
message authentication for content using a shared secret key, but this
credential contains no client-visible identity, permission, expiration, or
other claim whose integrity needs protection. FGA must still read the database
to resolve the credential and enforce revocation. An appended HMAC would not
protect a stolen bearer credential from use or replay and would add a global
key, rotation, parsing, and failure path without replacing the database lookup.
See [RFC 2104](https://www.rfc-editor.org/rfc/rfc2104.html) for HMAC's purpose.

Do not add a per-credential salt to the stored SHA2-256 digest. Salts prevent
precomputation and cross-account reuse when verifying low-entropy, frequently
repeated human passwords. Each FGA credential instead contains 256 independent
random bits, making useful guessing and precomputation infeasible without a
salt. A stored salt would provide no material resistance to a database-only
attacker and would prevent direct digest lookup unless the wire format gained a
public record selector solely to find the salt. NIST's salted-verifier guidance
is specifically motivated by offline guessing of memorized secrets; this is a
random machine credential, not a memorized secret. See
[NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b/passwords/).

The selected server verifier is therefore the unsalted SHA2-256 digest of the
complete canonical credential. The credential carries no appended HMAC tag.

## Consequences

- The private Lightroom plug-in needs no browser integration, cookies, device
  code, polling endpoint, client-generated entropy, or OAuth implementation.
- Private-MVP setup accepts a one-time authenticated Plugin Code create, confidential
  transfer, and paste operation in place of self-service pairing machinery.
- Security depends on 256 bits of server-generated entropy, HTTPS,
  `LrPasswords`, nonlogging, revocation, and a confidential administrative
  transfer channel.
- The credential is a bearer secret. Anyone who extracts it can act as that
  installation until it is revoked; browser pairing would not remove that
  endpoint-compromise risk.
- A public or self-service deployment needs a separate onboarding decision and
  likely an independently authenticated browser/device flow.
- Accepted ADRs 0039 and 0043 plus the administrative control-plane contract
  define the authenticated command/UI boundary.
  [ADR 0018](0018-same-workstation-private-credential-transfer.md) and the
  [private installation credential transfer ceremony](../private-install-credential-transfer.md)
  define the exact confidential handoff.
  [ADR 0019](0019-revisioned-installation-credential-lifecycle.md) defines
  planned rotation, revocation, and lost-workstation recovery.
- [ADR 0040](0040-expose-plugin-codes-as-user-resources.md) defines the
  user-owned plural collection, one-time create response, and terminal PATCH
  revocation.

The [Future Terry FAQ](../future-terry-faq.md) restates this decision in
cold-return question-and-answer form.
