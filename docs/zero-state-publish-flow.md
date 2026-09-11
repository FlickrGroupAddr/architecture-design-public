# Zero-state private-MVP publish flow

Last updated: 2026-09-05

Status: Accepted browser-free client bootstrap and publish-flow semantics,
including the browser-authentication supplements under accepted ADRs 0039 and
0043 and the accepted browser-session lifecycle

Authority: Mixed-status normative contract. Sections with explicit accepted
`Review:` records are normative inside accepted ADR boundaries; text labeled
proposed is not policy. See the [documentation authority hierarchy](README.md).

## Purpose

This document follows one fresh installation of the latest production/stable
Windows client target from empty local state through direct Flickr publication
and, when groups are selected, durable FGA group-queue acceptance.
It deliberately spells out DNS, TLS, credential, storage, and transaction
boundaries that a shorter API contract normally leaves implicit.

ADR 0008 additionally accepts an existing-photo path for public photos in the
configured owner's Flickr account, regardless of uploader or Lightroom Classic
catalog binding. This document remains the detailed contract for the
original-publisher path; the
[existing public Flickr photo intake contract](existing-public-photo-intake.md)
and ADR 0021 define the separate no-upload selector and its convergence
on the common hosted photo binding.

The corresponding PlantUML source is
[`diagrams/zero-state-publish-flow.puml`](diagrams/zero-state-publish-flow.puml).
The accepted prose contract in
[`plugin-service-contract.md`](plugin-service-contract.md) owns the detailed
hosted request/response semantics. Explicitly unresolved wire shapes remain
non-executable until their own closure work lands.

## Normative language

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**,
**SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and
**OPTIONAL** in this document are to be interpreted as described in BCP 14
([RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and
[RFC 8174](https://www.rfc-editor.org/rfc/rfc8174)) when, and only when, they
appear in all capitals.

## FGA component names

This flow always names the acting FGA component:

- **FGA LrC plug-in** — the Lightroom-resident publish provider.
- **FGA administrative control plane** — the operator-facing provisioning
  surface.
- **FGA OAuth handler** — the hosted OAuth client and callback endpoint.
- **FGA API backend** — the authenticated hosted HTTP API and application
  coordinator.
- **FGA refresh worker** — the hosted writable-group discovery worker.
- **FGA group-submission worker** — the hosted queued Flickr group-add worker.
- **FGA HTTPS edge**, **FGA database**, and **FGA managed secret store** — the
  named transport, persistence, and secret-storage boundaries.

Bare **FGA** names the product, project, credential or user namespace, or policy
as a whole; it never stands in for an acting component.

## Starting assumptions

- The latest production/stable Windows release adopted by the owner, the latest
  production Lightroom Classic release offered through Adobe Creative Cloud,
  and the FGA LrC plug-in are already installed.
- That installation-before-provisioning order is only this walkthrough's
  starting point. The same plug-in package may be downloaded and installed
  before or after the administrator creates its server-side installation
  identity; the credential is required before activation, not before download.
- The client has just obtained Internet connectivity.
- The relevant Windows DNS Client cache entries and FGA `LrPasswords` entry are
  empty. The private administrative window used for Part 2 starts clean and is
  closed after transfer; its 24-hour FGA cookie is administrative
  state, not plug-in state.
- The client browser is not used by the FGA LrC plug-in setup or publish flow.
  The plug-in never launches, controls, or exchanges data with the separate
  administrative private window on the same workstation.
- `flickrgroupaddr.com` is the selected, project-owner-controlled hostname for
  the FGA HTTPS edge, FGA API backend, FGA administrative control plane, and FGA
  OAuth handler. Ordinary Flickr REST and OAuth calls use `www.flickr.com`; binary
  photo uploads use Flickr's distinct `up.flickr.com` host.
- The browser on any administrator-controlled device may have been used once
  to grant Flickr OAuth access to the FGA OAuth handler. That is administrative
  service provisioning, not a dependency on the Lightroom host's browser.
- The FGA managed secret store already holds the Flickr application secret and
  Flickr OAuth token secret before a photo is published.
- For Part 2, Terry disables Windows clipboard history/cross-device sync, uses
  a clean private administrative window on the target Lightroom workstation,
  pastes the one-time-displayed FGA installation credential directly into the
  plug-in, overwrites the current clipboard with non-secret text, and closes
  that window.
- For this flow, each photo progresses independently. The FGA LrC plug-in does
  not promise Lightroom Classic selection, render, upload, handoff, or
  completion order. The FGA API backend orders each group queue only by
  successful durable intent insertion.

## Read Phase 1 this way

Phase 1 establishes two different trust relationships:

```text
Part 1: FGA OAuth handler -> Flickr, authorized to act for the owner
Part 2: one Lightroom installation -> FGA API backend
```

Part 1 starts in the FGA administrative control plane. An administrative browser on
any trusted machine first authenticates Terry through Google Identity Services
and the FGA Google Login Endpoint. From that authenticated FGA session it visits
Flickr, the owner approves FGA, and Flickr returns a verifier
to the FGA OAuth handler. The FGA OAuth handler exchanges that verifier for the
Flickr access token and token secret retained in the FGA managed secret store.
The FGA LrC plug-in **MUST NOT** launch the browser, participate in either
callback, or receive the Google ID token, FGA browser-session token, or Flickr
credentials.

Part 2 creates a server-side installation identity and one credential. It does not
register the plug-in binary, and it need not precede plug-in download or
installation. It **MUST** precede successful activation because an empty client
cannot authenticate itself. Unlike Part 1, its exact transfer ceremony uses a
clean private administrative window on the target Lightroom workstation. The
window remains independent of the plug-in even though both run on one machine.

This private-MVP choice replaces a device-code dance. In such a flow the
plug-in would request temporary device/user codes, show a verification address,
and poll while the owner approves the request in a browser. Smart TVs normally
ask the user to open that browser on a second device; they do not necessarily
launch it themselves. The FGA architecture avoids that polling flow and also
avoids a separate flow that launches the Lightroom host's browser and waits for a callback. See
the [Future Terry FAQ](future-terry-faq.md) for the cold-return explanation.

## State boundaries

| State holder | Contains | Explicitly does not contain |
| --- | --- | --- |
| Windows DNS Client cache | Temporary hostname-to-address records and negative answers | HTTP paths, cookies, credentials, photo IDs, group IDs, or image bytes |
| Client browser | Nothing required by this flow | FGA installation credential and Flickr service secrets |
| Administrative private window | Opaque 24-hour FGA administrative session cookie, response-local CSRF token, and the installation credential only in its five-minute in-memory transfer view | Google ID token, FGA installation credential after erase/close, Flickr secrets, and rendered images |
| Windows current clipboard | The installation credential only between one copy and the non-secret overwrite, with history/sync and third-party managers off | Durable credential history, Flickr secrets, browser cookies, or photo state |
| `LrPasswords` | Active FGA installation credential and, only during a later planned rotation, one current-installation-read-only candidate under a second fixed key | Browser cookies, Flickr secrets, signed upload envelope, and queue state |
| Plug-in recovery store | Lightroom-local correlation, selected group IDs, authorization ID, Flickr photo ID, common photo-binding ID/revision, and recovery state | Flickr secrets and OAuth authorization header |
| FGA database | Revisioned installation/credential digests and states, minimized validated Google identities, FGA browser sessions and audit events, OAuth transaction metadata, upload-authorization association, common photo bindings and proof events, current revisioned group and membership rows, durable intents, moderation preflight/attempt history, permanent photo/group submission blocks, and durable linked-user/deployment Flickr write gates | Rendered images, plaintext installation credentials, Google ID/access/refresh tokens, complete decoded Google claim maps, and Flickr secrets |
| FGA managed secret store | Flickr consumer secret, OAuth access token, and OAuth token secret | Rendered images |
| Flickr | Uploaded image and Flickr-owned photo/group state | FGA installation credential and Lightroom recovery state |

DNS is only a phone book. TLS authenticates the hostname reached through that
phone book and protects HTTP bytes in transit. Neither DNS nor TLS decides
whether an FGA credential is active; the FGA API backend makes that application-level
decision.

## Time-sequenced flow

Step identifiers combine the numeric phase number, a period, and a two-digit,
zero-padded number that restarts at `01` in each phase. For example, the third
step in Phase 5 is `5.03`. Global step numbering is deliberately not used.

A step identifier is reserved for an interaction, software decision, state
transition, or externally observable result in the timeline. Context,
rationale, invariants, examples, and negative scope guarantees remain prose
outside the step list. Commentary needed to understand a phase appears above
its list; otherwise it appears below.

### Phase 1 — One-time hosted-service and installation provisioning

Review: Phase 1 in full—Parts 1 and 2—was reviewed and accepted by Terry on
2026-08-21. The later separation of commentary from executable steps changed
presentation and identifiers, not the accepted semantics. Part 0 and the
browser-authentication and 24-hour session additions are accepted by ADR 0039.
Administrative authorization, post-login CSRF, recent Google reauthentication,
and audit details follow their accepted scoped contracts.

The three tabs in the
[clean-room authentication diagram](diagrams/clean-room-authentication-legal.drawio)
are authoritative for the overlapping browser-session, Plugin Code, and
publish-and-group-submission happy-path interactions under ADR 0041. This longer
flow supplies Flickr authorization, error/lifecycle requirements, remote Album
detail, and other omitted mechanics; it does not reorder or weaken the depicted
interactions. The diagrams are necessary but not sufficient for this complete
flow.

#### Part 0 — Authenticate the administrative browser

- **1.01** — The administrative browser **MUST** use the supported Google
  Identity Services sign-in experience. GIS **MUST** send `credential` and the
  `g_csrf_token` value in both cookie and request body to the exact FGA Google
  Login Endpoint. The FGA API backend **MUST** apply its shared admission limits
  and reject a missing or unequal CSRF pair before processing the ID token. The
  private MVP exposes no device-start or self-service OAuth-login route.
- **1.02** — The FGA Google Login Endpoint **MUST** use a maintained Google
  authentication library and bounded cache of Google's current JWKS to perform
  current trusted-key/algorithm, signature, audience, issuer, and time-claim
  validation. Outside login requests, a hosted timer **MUST** invoke the FGA
  JWKS refresh worker by the earlier of six hours and Google's metadata-driven
  freshness deadline. An admitted, CSRF-checked login naming an unknown signing
  key ID **MAY** wait for one bounded, coalesced refresh and **MUST** fail closed
  if the key remains unavailable. The endpoint **MUST** identify the Google
  Account only by canonical issuer plus validated `sub`, map that pair to the
  opaque internal `fgaUserId`, generate a 256-bit opaque FGA session token, and
  atomically store
  `SHA2-256(token)` as the lookup key with minimized claims, explicit session
  metadata, and the sanitized successful login audit. It returns the token only
  in a `__Host-`, `Secure`, `HttpOnly`, `Path=/`,
  `SameSite=Strict`, no-`Domain`, `Max-Age=86400` cookie. The server session has
  the same non-sliding 24-hour absolute expiry and no shorter idle timeout.
- **1.03** — Every later unsafe administrative request **MUST** present the
  opaque `__Host-fga_admin` session cookie, the session-bound synchronizer token
  in `X-CSRF-Token`, and the exact FGA origin. Creating credentials, replacing
  the Flickr grant, and resuming a Flickr write gate additionally **MUST** use
  accepted ADR 0043's five-minute, transaction-bound recent Google
  reauthentication; no text claims that it proves a fresh factor or
  phishing-resistant challenge.

#### Part 1 — Authorize the FGA OAuth handler to use Flickr

- **1.04** — The deployment operator **MUST** provision the Flickr application
  key and consumer secret through the selected provider's authenticated managed-
  secret mechanism. The FGA administrative control plane **MUST NOT** accept or
  display the consumer secret in a browser form.
- **1.05** — If the FGA OAuth handler does not already have the owner's Flickr
  authorization, the administrator **MUST** start Flickr's OAuth 1.0a flow from
  the authenticated administrative browser.
- **1.06** — The FGA OAuth handler **MUST** obtain a temporary Flickr request
  token and token secret with
  `GET https://www.flickr.com/services/oauth/request_token` and bind them to one
  five-minute, single-use server-side transaction.
- **1.07** — The administrative browser visits
  `https://www.flickr.com/services/oauth/authorize`, and Flickr authenticates
  the owner directly.
- **1.08** — The owner **MUST** grant FGA `write` permission.
- **1.09** — Flickr redirects the administrative browser to the configured FGA OAuth
  handler on `flickrgroupaddr.com` with the OAuth verifier.
- **1.10** — The FGA OAuth handler **MUST** consume the exact transaction and
  exchange the verifier and temporary token for the owner's Flickr access token
  and token secret with
  `GET https://www.flickr.com/services/oauth/access_token`.
- **1.11** — The FGA OAuth handler **MUST** verify the expected Flickr owner NSID
  and `write` permission, store the token/secret under a new versioned managed-
  secret reference, and atomically activate that reference with its sanitized
  administrative audit event. A failure **MUST** leave any prior active link
  unchanged.

These interactions neither require nor create state in the Lightroom host's
browser.

#### Part 2 — Create a Lightroom installation identity

- **1.12** — FGA User UI JavaScript **MUST** call
  `GET /api/v001/plugin-codes`; the Browser attaches the `HttpOnly` FGA session
  cookie without exposing its value to JavaScript.
- **1.13** — The FGA Plugin Code API **MUST** compute `SHA2-256(session token)`,
  resolve the active unexpired session and internal `fgaUserId`, query only that
  user's bounded Plugin Code metadata page, and durably append the sanitized
  list-read audit before returning metadata for the FGA User UI to render.
- **1.14** — Terry selects **Create Plugin Code** in the FGA User UI, which
  sends `POST /api/v001/plugin-codes` to request one FGA LrC plug-in
  installation identity and credential. The Browser attaches the FGA session
  cookie, and the request carries the required exact-origin, session-bound
  CSRF, and accepted recent Google reauthentication evidence.
- **1.15** — The FGA API backend **MUST** use its runtime or operating system
  cryptographically secure random generator to create exactly 32 random octets.
- **1.16** — The FGA API backend **MUST** encode those octets in ADR 0044's
  canonical grouped Crockford Base32 form: 52 uppercase symbols in 13
  four-symbol groups separated by 12 ASCII hyphens, for 64 characters total.
- **1.17** — The FGA API backend **MUST** compute the unsalted SHA2-256 digest of the complete
  credential.
- **1.18** — In one transaction, the FGA API backend **MUST** store the digest,
  server-assigned non-null `lrc_plugin` credential class, installation
  identity, FGA user, creation time, active/revoked state, and sanitized
  successful administrative audit event and **MUST NOT** store the plaintext
  credential. The administrative request **MUST NOT** select or override the
  class. An audit-write failure **MUST** refuse creation.
- **1.19** — The FGA User UI **MUST** display the plaintext Plugin Code exactly
  once in clear text and **MUST** keep it out of logs, traces, URLs, and browser
  caches. A lost response is not redisplayed; Terry revokes that record and
  creates another.
- **1.20** — On the target Lightroom workstation, Terry **MUST** use the
  [private installation credential transfer ceremony](private-install-credential-transfer.md):
  a clean private FGA User UI window, Windows clipboard history/sync off,
  one explicit copy, no intervening application, direct paste into the plug-in,
  simultaneous side-by-side clear-text comparison with identical grouping and
  typography, strict validation without normalization, a non-secret clipboard
  overwrite, and private-window close.

The FGA API backend **MUST NOT** append an HMAC tag to this opaque credential.
The credential **MUST NOT** contain authentication claims, and the FGA API
backend **MUST** still use the
database to resolve its installation, status, and authorization.

Password managers, files, downloads, command lines, screenshots, QR images,
email, chat, public issue trackers, cross-device clipboards, and remote-control
sessions are not the private-MVP transfer channel and **MUST NOT** be used for
this credential. An
unauthenticated "first caller wins" claim endpoint **MUST NOT** exist; an empty
client cannot authenticate itself without this pre-established trust.

### Phase 2 — Browser-free Lightroom activation

Review: Phase 2 was reviewed and accepted by Terry on 2026-08-21; Terry
approved the dedicated credential-validation, Bearer-header, and standard
Bearer error-semantics amendments the same day.

Phase 2 begins with these assumptions: Windows has working Internet
connectivity; all DNS caches relevant to this flow are empty; the latest
production Lightroom Classic and the FGA LrC plug-in are installed; and
`LrPasswords`, the Lightroom plug-in secrets store, contains no FGA credential.
An accurate-enough Windows clock for HTTPS certificate validation is part of
working Internet connectivity. These are starting conditions, not interactions
that need their own phase.

- **2.01** — The user launches Lightroom Classic.
- **2.02** — The Lightroom Classic host loads the FGA LrC plug-in.
- **2.03** — The plug-in asks `LrPasswords` for the FGA installation credential.
- **2.04** — `LrPasswords` returns no value.
- **2.05** — The plug-in **MUST** mark the publish service disconnected and **MUST NOT**
  attempt a normal authenticated FGA request.
- **2.06** — The FGA LrC plug-in **MUST** display the FGA User UI Plugin Code
  URL on `flickrgroupaddr.com` and a clear-text transient Plugin Code input
  using the same fixed grouping and typography as the browser transfer view.
- **2.07** — With no intervening application, the user pastes the
  issued Plugin Code from the current local Windows clipboard and compares the
  simultaneous browser and plug-in values side by side.
- **2.08** — The FGA LrC plug-in **MUST** reject every noncanonical spelling
  without normalization or repair, then store an accepted value immediately
  with `LrPasswords` when the user invokes **Store and verify**.
- **2.09** — The plug-in **MUST** clear the visible field and **MUST NOT** copy the
  credential into normal Lightroom preferences, the catalog, logs, or diagnostic
  handoffs.
- **2.10** — The plug-in **MUST** retrieve the stored credential to validate the
  connection.
- **2.11** — The Lightroom Classic host networking stack asks the Windows
  resolver for the address of `flickrgroupaddr.com`.
- **2.12** — The Windows DNS Client service first checks its local cache.
- **2.13** — The cache contains no matching record, so the DNS Client service asks a
  configured recursive resolver for A and/or AAAA records.
- **2.14** — The recursive resolver obtains an answer and returns one or more addresses
  plus their time-to-live values.
- **2.15** — Windows caches the answer for the applicable TTL.
- **2.16** — The Lightroom Classic host networking stack chooses a reachable address
  and opens a network connection.
- **2.17** — For the request initiated by the FGA LrC plug-in, the Lightroom
  Classic host networking stack **MUST** establish an HTTPS/TLS connection to
  `https://flickrgroupaddr.com`.
- **2.18** — The plug-in **MUST** call the Lightroom SDK's `LrHttp.get` for
  `GET https://flickrgroupaddr.com/api/v001/installations/current` and **MUST**
  supply `{ field = "Authorization", value = "Bearer " .. credential }` in the
  documented request-header table. The request **MUST** have no body or query
  parameters.
- **2.19** — For a request with no authentication information, the FGA API
  backend **MUST** return `401 Unauthorized` with
  `WWW-Authenticate: Bearer realm="fga-api"` and **MUST NOT** include an OAuth
  error attribute.
- **2.20** — A duplicate `Authorization` field, multiple token-transmission
  methods, request body, any query parameter, or other malformed request
  envelope **MUST** cause the FGA API backend to return `400 Bad Request` with
  Bearer error `invalid_request`.
- **2.21** — For one presented Bearer token, the FGA API backend **MUST**
  validate its wire grammar and, for a canonical token value, **MUST** compute
  SHA2-256 and look up the digest without retaining the presented plaintext.
  The loaded installation's non-null stored `credential_class` **MUST** equal
  the exact recognized `lrc_plugin` class. No client field can create, replace,
  or broaden that stored authority.
- **2.22** — For a malformed token value or a credential that is unknown, inactive,
  expired, revoked, disabled, or otherwise fails signature, integrity, or
  verification checks—including a null, corrupt, retired, differently cased,
  or future unknown stored credential class—the FGA API backend **MUST** return
  the same nonspecific `401 Unauthorized` with Bearer error `invalid_token`.
  It **MUST NOT** map an unrecognized class to browser, administrator, legacy,
  or any other client authority.
- **2.23** — An active matching installation identifies the FGA user and linked
  Flickr NSID, so the FGA API backend **MUST** return `200 OK`, `Cache-Control:
  no-store`, and the minimal current-installation representation defined by
  ADR 0032. It includes only `schemaVersion`, opaque
  `installationId`, `installationRevision`, exact `installationState: "active"`,
  and exact `presentedCredentialState: "current"`.
- **2.24** — The FGA LrC plug-in **MUST** exhaustively validate that JSON and
  mark its FGA API connection authenticated only after the installation ID is
  locally consistent and the exact presented state is `current`. The rotation
  lifecycle also allows `pending_rotation` on this resource but never as
  ordinary API authority.
- **2.25** — After the plug-in shows the non-secret **Connected** state, Terry
  **MUST** return directly to the FGA User UI transfer view and invoke
  **Erase transfer view**.
- **2.26** — In that user gesture, the FGA User UI page **MUST** overwrite
  the current clipboard with fixed non-secret text and erase its rendered/UI
  reference. It **MUST NOT** read the clipboard back.
- **2.27** — Terry **MUST** close the entire private-browsing window. The
  transfer is complete only after the successful current-installation read and
  this cleanup.

The Lightroom SDK exposes no TLS-version contract or control. The negotiated
version is an implementation detail of the Lightroom Classic host networking
stack and the FGA HTTPS edge. The deployment target is TLS 1.3-or-newer only if
the latest Creative Cloud LrC release on the owner's adopted latest
production/stable Windows release succeeds in the compatibility probe.

The implementation **MUST** avoid data-dependent secret comparisons wherever a
secret comparison is required. If a future credential format includes a
cryptographic signature, a well-formed credential that fails its signature
check **MUST** receive the same nonspecific `401 invalid_token`; the response
**MUST NOT** reveal which verification check failed.

The error split follows RFC 6750 instead of inventing FGA semantics. Parsing a
token's syntax is not authentication: unknown, inactive, revoked, or bad-
signature tokens remain invalid credentials and receive `401`. The FGA API
backend reserves `403 Forbidden` for a successfully authenticated installation
that lacks permission for the requested action or resource. An earlier draft used `403`
for any well-formed but invalid credential; Terry rejected that distinction as
surprising and without value on 2026-08-21.

The wire contract contains no Lightroom version or client-profile query. The
internal `lrc_plugin` class distinguishes plug-in credentials from other
authorities and is never client supplied. If a concrete future authentication
profile is needed, the FGA API backend can add explicit capability
representation or negotiation without renaming the current-installation
resource. ADR 0032 records this decision.

The FGA credential **MUST** travel only in the HTTPS `Authorization` request
header and **MUST NOT** appear in the URL, query string, or request body. The
LrC 15.3 SDK documents
caller-supplied headers and uses `Authorization` in its own `LrHttp` example.
It documents receiving and parsing `Set-Cookie`, but it does not promise a
persistent browser-style cookie jar or an `HttpOnly` isolation boundary.
Manually reading, storing, and resending a cookie from Lua would receive no
`HttpOnly` benefit, so the FGA API backend **MUST NOT** use cookie authentication for the plug-in.

Phase 2 ends when the plug-in consumes the validation response, not when the
underlying HTTPS connection closes. The Lightroom Classic host networking stack
may keep that connection open for reuse; normal HTTP keep-alive is completed
transport behavior, not an unfinished application request.

The plug-in **MUST NOT** launch or control a browser, exchange data with one, or
receive a browser callback. The user **MAY** open the displayed administrative
URL manually in a browser on any trusted device; that remains administrative
credential generation, not a browser-based plug-in activation protocol.

### Phase 3 — Writable Flickr group discovery

Review: Terry approved the original bounded discovery flow on 2026-08-22 and
explicitly approved the simpler one-job, one-snapshot, keyset-page replacement
on 2026-08-25. ADR 0030 records the superseding decision.

- **3.01** — The plug-in **MUST** call the Lightroom SDK's `LrHttp.get` for
  `GET https://flickrgroupaddr.com/api/v001/groups?page_size=100`
  and **MUST** pass `{ field = "Authorization", value = "Bearer " .. credential }` in
  its documented request-header table; on the wire this is
  `Authorization: Bearer <FGA installation credential>`.
- **3.02** — On every initial or continuation request, the FGA API backend **MUST**
  validate the bearer credential's wire grammar again, compute SHA2-256 over the complete canonical
  credential without retaining its plaintext, and use that digest to locate an
  active installation record. The installation record **MUST** resolve the
  linked FGA user and Flickr NSID; the Phase 2 check **MUST NOT** create a
  session or exempt later requests from authentication.
- **3.03** — The FGA API backend **MUST** require exactly one decimal
  `page_size` from 1 through 100. The initial request **MUST** omit
  `snapshot_revision` and `after_group_id`.
- **3.04** — The FGA API backend **MUST** serve a complete current snapshot as
  fresh while it is at most 15 minutes old. When it is older, the backend
  **MUST** create or join one refresh job for the linked user and may continue
  serving only the last good snapshot, explicitly labeled `stale_refreshing`
  or `stale_refresh_failed`. It **MUST NOT** present a failed refresh as an
  empty snapshot.
- **3.05** — If no successful snapshot exists, an active refresh **MUST**
  produce `202 Accepted` with `Retry-After` and no group data. A failed refresh
  with no successful snapshot **MUST** produce `503 Service Unavailable` with
  `group_refresh_unavailable` and no group data. The FGA API backend **MUST NOT**
  start more than one attempt for one linked user in 60 seconds.
- **3.06** — One FGA refresh worker invocation **MUST** own the complete Flickr
  page walk. It **MUST** resolve `www.flickr.com` through the hosted DNS resolver,
  open or reuse HTTPS, and retrieve the linked user's Flickr OAuth 1.0a access
  token and token secret. The installation credential digest **MUST NOT** select
  Flickr OAuth material.
- **3.07** — For Flickr page 1, the FGA refresh worker **MUST** make this exact
  Flickr API call:
  `GET https://www.flickr.com/services/rest/?method=flickr.groups.pools.getGroups&page=1&per_page=400&format=json&nojsoncallback=1`.
  A mature OAuth 1.0a library **MUST** sign the exact request with a fresh nonce
  and timestamp and the externally required `HMAC-SHA1` algorithm—HMAC using
  SHA1-160. Secrets **MUST NOT** be transmitted.
- **3.08** — The FGA refresh worker **MUST** completely validate each Flickr
  page, retain only required ID/display fields in staging, and follow the next
  Flickr page in the same job with a fresh nonce, timestamp, and signature.
  Flickr page numbers **MUST NOT** cross the FGA API backend boundary.
- **3.09** — More than 25 Flickr pages, 10,000 distinct groups, 2 MiB in one
  response, or 60 seconds of monotonic elapsed job time **MUST** fail the whole
  refresh without truncation. Page-level work items and resumable page
  checkpoints **MUST NOT** be created.
- **3.10** — After the final page passes, one FGA database transaction **MUST**
  replace the visible rows, advance `snapshotRevision`, and record
  `refreshedAt`. Failure **MUST** leave the prior revision unchanged.
- **3.11** — The FGA API backend **MUST** order stored rows by exact Flickr group
  ID and return at most `page_size` groups plus `snapshotRevision`,
  `refreshedAt`, `snapshotStatus`, and `nextAfterGroupId`. The last field is the
  final returned ID when another row exists and JSON `null` otherwise.
- **3.12** — A continuation **MUST** repeat `page_size` and send the preceding
  `snapshot_revision` and `after_group_id`. The FGA API backend **MUST**
  authenticate it, require both parameters together, require the revision still
  be current, and select IDs strictly greater than the keyset boundary.
- **3.13** — A changed revision **MUST** return `409 Conflict` with
  `snapshot_changed` and no groups. The FGA LrC plug-in **MUST** discard its
  partial aggregate and restart once at the initial request. Otherwise it
  **MUST** follow keyset pages until `nextAfterGroupId` is null, then display
  groups by name while retaining Flickr group IDs as identity and visibly
  labeling stale snapshot state.

The hosted DNS cache is independent of the Windows client's DNS cache. The
plug-in **MAY** cache the completed aggregate for display. The [group snapshot
and pagination contract](group-snapshot-and-pagination.md) defines the exact
state, limits, and conformance evidence.

### Phase 4 — Per-photo selection, rendering, and preflight

Review: Approved by Terry on 2026-08-22. Terry left the explicit localswim
comment `reviewed and approved!` at 12:34:52-04:00 and completed the Phase 4
review card at 12:34:56-04:00. Terry approved the zero-group amendment on
2026-08-25; ADR 0010 records the decision.

[ADR 0045](decisions/0045-use-a-library-modal-and-photo-metadata-for-group-selection.md)
maps the accepted behavior below to exact documented Lightroom SDK 15.3
interfaces. It selects one `LrLibraryMenuItems` command for exactly one
photo in one active FGA Album, one native `LrDialogs.presentModalDialog`, and
one private per-photo `LrMetadataProvider` JSON field scoped by service,
collection, and photo identifiers. A multi-photo callback opens no selector.
Terry accepted this implementation mapping on 2026-09-04. It refines without
amending the approved Phase 4 behavior.

The publish service **SHOULD** default this flow to a full-resolution 8-bit sRGB
PNG.

The FGA LrC plug-in is registered as a custom Lightroom Publish Service
provider. Every user-created ordinary FGA published collection **MUST** be
presented as an **Album**, correspond one-to-one with one Flickr album, and give
every photo published from it a durable attachment obligation. The plug-in
**MUST NOT** create a default collection, expose smart albums, or offer an
arbitrary existing-Flickr-album picker. The
[album-scoped publish contract](album-scoped-publish-contract.md) defines the
binding, identity, lifecycle, idempotency, and repair state.

Flickr's documented `flickr.photosets.create` method requires a primary Flickr
photo ID. Choosing **Create Album…** therefore creates the Lightroom published
collection locally but cannot yet materialize its remote Flickr album. The FGA
LrC plug-in **MUST NOT** manufacture a placeholder photo or use an unrelated
photo to work around that upstream contract. The
[album-scoped publish contract](album-scoped-publish-contract.md) defines
creation with the first real published photo, and the
[album-write reconciliation contract](album-write-reconciliation.md) defines
ambiguous-create repair plus membership verification.

- **4.01** — In Lightroom Classic's Publish Services panel, the photographer
  right-clicks the configured FGA publish service, chooses **Create Album…**, or
  selects an existing local FGA Album. Lightroom Classic creates a new
  published collection locally; an empty Album has no Flickr remote ID yet.
  Selecting the local Album selects its one bound Flickr target; titles and
  URLs are not identity and cannot adopt another remote album.
- **4.02** — The photographer selects one or more catalog photos and adds them to that
  FGA published collection.
- **4.03** — In the FGA published collection, the photographer selects the photos whose
  Flickr group targets they want to inspect or extend.
- **4.04** — The FGA LrC plug-in **MUST** read the Flickr remote publish ID, if
  any, from each selected published-collection membership's Lightroom Classic
  catalog record and retrieve the corresponding non-secret FGA photo-binding ID
  from its durable plug-in state.
- **4.05** — Each time the selector opens, for every selected photo with both
  identifiers, the plug-in **MUST** send an independently authenticated
  initial
  `GET https://flickrgroupaddr.com/api/v001/photo-bindings/<FGA photo binding ID>/group-memberships?page_size=100`
  with no `observation_revision` or `after_group_id`.
- **4.06** — The FGA API backend **MUST** require the binding to belong to the
  authenticated FGA user and derive the exact Flickr photo ID and linked Flickr
  account from it before retrieving the OAuth 1.0a access token and token secret.
- **4.07** — The FGA API backend **MUST** sign and send
  `GET https://www.flickr.com/services/rest/?method=flickr.photos.getAllContexts&photo_id=<Flickr photo ID>&format=json&nojsoncallback=1`.
- **4.08** — Flickr returns the currently visible Flickr sets and group pools for that
  photo. The FGA API backend **MUST** require a complete JSON object with exact
  `stat: "ok"`, an explicit array-valued `pool` member, and valid bounded ID/title
  fields in every pool object. It **MUST** reject missing, null, non-array,
  partially malformed, duplicated, truncated, or over-budget pool data as an
  unknown observation; it **MUST NOT** coerce or filter that data to an empty or
  partial list. After validation it **MUST** discard set entries and retain only
  pool IDs and names.
- **4.09** — The FGA API backend **MUST** atomically publish a complete bounded
  membership observation with an `observationRevision` and `observedAt`, then
  return at most `page_size` groups ordered by exact Flickr group ID plus
  `nextAfterGroupId`. It **MUST NOT** substitute FGA intent history or a
  previously cached result for this fresh Flickr read.
- **4.10** — When `nextAfterGroupId` is non-null, the plug-in **MUST** follow it
  with independently authenticated keyset requests containing the same
  `page_size`, `observation_revision`, and `after_group_id`. A concurrent newer
  observation returns `409 membership_observation_changed`; the plug-in
  **MUST** discard its partial aggregate and start one new initial read. It
  **MUST** repeat the operation for each selected photo with a Flickr remote ID.
- **4.11** — A selected photo without an FGA remote ID **MUST** be labeled **Not yet
  published by this FGA collection**; the plug-in **MUST NOT** claim that the
  Lightroom photo does or does not exist elsewhere on Flickr.
- **4.12** — If any current-membership query fails or exceeds its resource budget, the
  upstream media type/body/shape is invalid or incomplete, any keyset page
  fails, or any budget is exceeded, the plug-in **MUST** discard the incomplete
  aggregate, label that photo's membership **Unavailable**, and
  **MUST NOT** present an empty/partial/prior set as current reality or enable
  group-addition confirmation for that already-published photo until a new
  initial fresh read succeeds. Only a fully validated explicit empty upstream
  pool array is a successful empty observation.
- **4.13** — The plug-in **MUST** display each successful fresh Flickr membership as a
  timestamped, read-only **Currently in Flickr groups** set and **MUST** display the
  Phase 3 writable-group list separately for selecting additions.
- **4.14** — A current membership **MUST NOT** be selectable for removal or interpreted
  as a removal request; the FGA API backend **MUST NOT** call `flickr.groups.pools.remove`.
- **4.15** — For each unpublished selected photo, the photographer chooses zero
  or more additional target groups. The normal single-photo preflight **MUST**
  present **No group additions** as an explicit, confirmable choice. A
  multi-photo callback **MUST NOT** open serial per-photo modal dialogs or block
  a zero-group photo; it **MUST** make the empty outcome visible in per-photo
  state or the batch summary.
- **4.16** — The plug-in **MUST** durably store each editable group-addition selection
  against the FGA publish-service instance, published-collection membership,
  and Lightroom photo UUID.
- **4.17** — For a photo already published through this FGA LrC plug-in's
  publish-service instance with one or more newly selected groups, the plug-in
  **MUST** snapshot its existing FGA photo-binding ID, current verification
  revision, and newly selected group IDs in a local outbox record, then **MUST**
  proceed directly to Phase 6 without rendering or uploading the image again.
  With no newly selected group, this add-more-groups action is a no-op and
  **MUST NOT** call Phase 6.
- **4.18** — For one or more photos not yet published through this FGA collection, the
  photographer clicks Lightroom's **Publish** action for the FGA
  published collection.
- **4.19** — The Lightroom Classic publish-service runtime supplies the FGA LrC
  plug-in with the collection photos that need initial publication in this
  zero-state flow.
- **4.20** — Before requesting a render, the plug-in **MUST** snapshot each
  candidate's zero or more selected group IDs. It **MUST NOT** treat an empty
  snapshot as an error or let it block another candidate.
- **4.21** — The plug-in **MUST** treat every candidate photo as an independent unit of
  progress and **MUST NOT** stop an otherwise healthy photo merely to preserve
  Lightroom Classic publish-run order after another photo fails, blocks, or
  becomes ambiguous. It **MUST NOT** silently drop any photo.
- **4.22** — For the first photo, the plug-in **MUST** durably snapshot its
  Lightroom photo UUID and zero or more selected Flickr group IDs in a local
  recovery record.
- **4.23** — The Lightroom Classic rendering engine renders the photo with the
  configured publish settings.
- **4.24** — The FGA LrC plug-in **MUST** wait until the Lightroom Classic
  rendering engine has finished writing the rendered file.
- **4.25** — The plug-in **MUST** verify that the file exists, is readable, and has
  nonzero length.
- **4.26** — The plug-in **MUST** compare its exact byte size with the configured
  Flickr byte limit. A file is oversized only when its byte size is strictly
  greater than that limit.
- **4.27** — The plug-in **MUST** hard-fail an oversized photo before upload
  authorization. The failure **MUST** identify the rendered size and configured
  limit and state that nothing was uploaded. It **MUST NOT** resize the image,
  convert it to JPEG, offer an in-flow fallback action, request upload
  authorization, or invoke the Flickr upload endpoint. The user **MAY** later
  choose different publish settings and start a new publish action.
- **4.28** — A file that passes preflight proceeds to the Phase 5 upload-authorization
  request.

The Lightroom UUID is local correlation, not authentication entropy or proof
of Flickr ownership. Adding a photo to the FGA published collection and editing
its group selections create Lightroom-local state; neither action alone proves
that the corresponding Flickr album exists or removes a current membership.
For an unpublished photo, Phase 5 **MUST** obtain a definitive Flickr photo ID
before any nonempty group selection enters Phase 6. A zero-group publication
skips Phase 6 and creates no group intent. For an already-published FGA photo,
step 4.17 **MUST** reuse its existing binding and enter Phase 6 directly only
when newly selected groups exist. Phase 6's committed transaction **MUST** be
the only operation that creates new durable per-group queue intents.

Flickr remains authoritative for current pool membership because Flickr's UI,
other clients, group moderators, and other external actors can add or remove a
photo without updating the FGA API backend or FGA database. A fresh membership
result is therefore display guidance, not a durable write precondition: it can
become stale immediately, and absence **MUST NOT** override an existing FGA
intent or permanent submission block. The FGA LrC plug-in and FGA API backend
**MUST** remain add-only and **MUST NOT** reverse an external removal.
An oversized photo fails independently under step 4.21; it does not stop another
healthy photo in the same publish run. JPEG remains available only as a
separately selected publish setting, not as an automatic or one-click response
to an oversized PNG.

### Phase 5 — Direct Flickr upload signed by FGA API backend

Review: Approved by Terry on 2026-08-22. Terry accepted the courtesy-bounded
admission amendment in ADR 0020 on 2026-08-31.

- **5.01** — The FGA LrC plug-in **MUST** send
  `POST https://flickrgroupaddr.com/api/v001/upload-authorizations`.
- **5.02** — Windows normally answers `flickrgroupaddr.com` from its DNS cache, unless
  the TTL expired; an existing HTTPS connection **MAY** avoid a new lookup
  entirely.
- **5.03** — The FGA LrC plug-in **MUST** retrieve the credential from
  `LrPasswords` and send it as
  `Authorization: Bearer <FGA installation credential>`.
- **5.04** — The request **MUST** contain only the allowlisted, non-file Flickr upload
  metadata and **MUST NOT** contain rendered image bytes.
- **5.05** — The FGA API backend **MUST** validate the installation credential and
  request schema and **MUST** check the linked-user and deployment Flickr write
  gates. If either gate is paused, it **MUST NOT** issue a signed upload
  authorization and **MUST** return `503 Service Unavailable` with
  `flickr_writes_paused`, `retryable: false`, and no `Retry-After`.
- **5.06** — The FGA API backend **MUST** reject client-supplied `photo`, `api_key`,
  OAuth fields, unknown fields, and invalid combinations.
- **5.07** — The FGA API backend **MUST** generate a fresh Flickr OAuth nonce,
  timestamp, and FGA upload authorization ID.
- **5.08** — The FGA API backend **MUST** sign the exact non-file Flickr metadata with
  the Flickr consumer secret and OAuth token secret.
- **5.09** — The FGA API backend **MUST** create an FGA database
  upload-authorization record keyed by the authorization ID, containing the
  installation, FGA user, issue time, and a nullable Flickr photo ID field
  initialized to `null`. It **MUST NOT** persist the signed title, description,
  tags, upload URL, or OAuth authorization header.
- **5.10** — The FGA API backend **MUST** return `200 OK`, `Cache-Control: no-store`,
  the Flickr upload URL
  `https://up.flickr.com/services/upload/`, the exact signed metadata, the
  OAuth authorization header, and the FGA upload authorization ID.
- **5.11** — The FGA LrC plug-in **MUST** store only the non-secret
  authorization ID in the recovery record.
- **5.12** — The FGA LrC plug-in **MUST** keep the signed upload envelope only
  in memory and use it immediately.
- **5.13** — If no reusable connection to `up.flickr.com` exists, the Lightroom
  Classic host networking stack **MUST** ask Windows to resolve that hostname
  for the request initiated by the FGA LrC plug-in.
- **5.14** — On the first upload, Windows queries its configured resolver and caches the
  returned Flickr upload addresses by TTL.
- **5.15** — For a new connection, the FGA LrC plug-in **MUST** use the
  Lightroom SDK's documented HTTP API; the Lightroom Classic host networking
  stack opens TLS to `up.flickr.com` and validates that hostname's certificate.
- **5.16** — The FGA LrC plug-in **MUST** call the Lightroom SDK's
  `LrHttp.postMultipart` with every returned metadata field unchanged plus the
  rendered file as the `photo` part, targeting
  `https://up.flickr.com/services/upload/`.
- **5.17** — Through `LrHttp.postMultipart`, the FGA LrC plug-in **MUST** stream
  the image bytes directly to Flickr.
- **5.18** — Flickr validates the OAuth authorization and signed non-file metadata.
- **5.19** — On success, Flickr stores the image and returns a Flickr photo ID.
- **5.20** — After a definitive rejection, or after a failure proven to occur
  before `LrHttp.postMultipart` is invoked, a deliberate new FGA LrC plug-in
  attempt **MUST** obtain a fresh authorization and **MUST NOT** reuse the
  earlier signed envelope.
- **5.21** — Once the FGA LrC plug-in invokes `LrHttp.postMultipart`, a timeout,
  connection loss, or other missing definitive Flickr result **MUST** be treated
  as ambiguous because the documented Lightroom SDK contract does not prove
  that zero request bytes left the Lightroom Classic host networking stack.
  Flickr might have created the photo.
- **5.22** — For an ambiguous outcome, the FGA LrC plug-in **MUST** record
  `upload_outcome_unknown`, **MUST NOT** automatically upload again, and
  **MUST NOT** create or attach a Flickr album, attach a photo to an album,
  create group intents, or write a Lightroom Classic catalog remote ID until a
  Flickr photo ID is deliberately reconciled. ADR 0012 defines the
  owner-visible recovery path.
- **5.23** — On the normal success path, the FGA LrC plug-in **MUST** write the
  Flickr photo ID into the local recovery record first.
- **5.24** — The FGA LrC plug-in **MUST** then call the documented Lightroom
  SDK's `recordPublishedPhotoId` with that Flickr photo ID so the Lightroom
  Classic catalog holds it as the published photo's remote ID.
- **5.25** — That FGA LrC plug-in update **MUST** cause the Lightroom Classic
  publish-service runtime to treat the image as published to Flickr even though
  its selected group work has not yet been durably handed off.
- **5.26** — The FGA LrC plug-in **MUST** retain a durable
  `album_attachment_pending` obligation for the Flickr album bound one-to-one to
  the FGA published collection until attachment is verified or reaches an
  explicit repair state. Album attachment and Phase 6 group-intent handoff may
  progress independently; neither blocks the other merely to impose order.
  The album-write reconciliation contract defines the documented Flickr
  method, fresh membership proof, idempotency boundary, and recovery
  transitions.
- **5.27** — The FGA LrC plug-in **MUST** send an authenticated, idempotent
  `PUT /api/v001/upload-authorizations/<FGA upload authorization ID>/photo-binding`
  containing `schemaVersion: 1` and the exact Flickr photo ID returned by the
  upload. It **MUST NOT** use the Phase 6 batch as an implicit proof operation.
- **5.28** — The FGA API backend **MUST** require the authorization to belong to
  the installation, call documented `flickr.photos.getInfo`, and validate the
  complete successful result, exact photo ID, expected linked owner NSID, and
  unchanged linked-account revision.
- **5.29** — The FGA API backend **MUST** commit one common photo binding unique
  to `(FGA user, Flickr photo ID)` and the successful verification observation
  before responding. The upload-authorization-to-photo association remains
  immutable; a different photo for the same authorization is `409 Conflict`.
- **5.30** — The committed response **MUST** include the opaque
  `fgaPhotoBindingId`, source kind `fga_direct_upload`, exact Flickr photo ID,
  linked-account revision, current verification revision, and verification
  time. A matching repeat returns the same binding without duplicating it.
- **5.31** — The FGA LrC plug-in **MUST** retain the non-secret binding ID and
  current verification revision in its local recovery/outbox state. A timeout
  may retry only this identical safe `PUT`; a failed proof blocks Phase 6 and
  **MUST NOT** cause another image upload.

For `upload_outcome_unknown`, the FGA LrC plug-in may display private,
authenticated recent-owner-photo candidates returned through the FGA API
backend, but it must not infer a match. The photographer explicitly selects one
candidate or supplies its Flickr photo ID, after which the FGA API backend
verifies the exact photo and linked owner and commits an idempotent ambiguity
resolution before the plug-in records the catalog remote ID. Alternatively,
the photographer may acknowledge that the first photo can exist and choose a
distinct **Publish a new copy** attempt with a fresh authorization. The
original record remains `abandoned_possible_flickr_photo`; the FGA LrC plug-in,
FGA API backend, and FGA database do not automatically delete or reuse the
possible first photo.

`up.flickr.com` is a distinct hostname, so a cached result for
`flickrgroupaddr.com` or `www.flickr.com` cannot satisfy its lookup. The FGA API
backend **MUST NOT** receive the image bytes.

Flickr deliberately excludes the `photo` bytes from the OAuth signature; it
validates the authorization and exact signed non-file metadata instead.

### Phase 6 — Durable group-intent handoff

Review: Approved by Terry on 2026-08-22.

Each intent's natural identity is `(Flickr photo ID, Flickr group ID)`. Its FIFO
queue partition is `(FGA user, Flickr group ID)`.

This phase applies only to a nonempty group selection. A zero-group publication
creates no intent and **MUST NOT** send an empty batch to trigger photo binding
or ownership proof as a hidden side effect. Section 5.27 and the existing-public-
photo intake contract define the explicit proofs that create or refresh the
common binding before this phase.

- **6.01** — The FGA LrC plug-in **MUST** send
  `POST https://flickrgroupaddr.com/api/v001/group-submission-batches`.
  This **MUST** be the only authenticated client operation that creates group-
  submission intents; every official client **MUST** use it even for one group,
  and the FGA API backend **MUST NOT** register a single-group create alias.
- **6.02** — The schema-version-2 request **MUST** contain one
  `photoBinding` object with `fgaPhotoBindingId` and
  `expectedVerificationRevision`, plus a nonempty array of unique Flickr group
  IDs no larger than the fixed deployment value `max_group_ids_per_batch`. It
  **MUST NOT** contain a Flickr photo ID, image bytes, a Flickr secret, an OAuth
  header, or a client-supplied user identity.
- **6.03** — The FGA LrC plug-in **MUST** send the `LrPasswords` credential as
  `Authorization: Bearer <FGA installation credential>`.
- **6.04** — The FGA API backend **MUST** validate the credential and the complete
  request before writing an intent. It **MUST** reject empty, duplicate,
  malformed, and over-limit requests as a whole and emit no wake
  hint. The FGA LrC plug-in **MUST NOT** slice an over-limit selection into
  several requests.
- **6.05** — The FGA API backend **MUST** require the binding to belong to the
  authenticated FGA user, remain attached to the exact current linked-account
  revision, and have exactly the expected current verification revision. It
  **MUST** derive the Flickr photo ID, FGA user, owner NSID, source kind, and
  link revision exclusively from the binding.
- **6.06** — For an existing-public-photo binding, a batch that would create at
  least one missing natural-key intent **MUST** use the latest proof revision
  within the fixed positive `existing_photo_proof_max_age`; otherwise the FGA
  API backend **MUST** return `409 existing_photo_reverification_required`
  without mutation. ADR 0033 proposes 15 seconds.
- **6.07** — If every requested natural-key intent already exists, the FGA API
  backend **MAY** return the stored states after that proof age expires, but it
  **MUST NOT** revive, reset, duplicate, or resubmit work.
- **6.08** — The FGA API backend **MUST** validate group IDs syntactically but
  **MUST NOT** require them to appear in the earlier cached discovery response.
- **6.09** — After all validation succeeds, the FGA API backend **MUST** begin one
  database transaction for the complete handoff.
- **6.10** — Within that transaction, the FGA API backend **MUST** recheck the
  binding and link revisions, then create every missing intent with its server-
  generated intent ID, binding-derived Flickr photo ID and FGA user/partition,
  creation order, timestamps, and `queued` state. Any revision race **MUST**
  roll back the complete batch.
- **6.11** — For an existing intent, the FGA API backend **MUST** retain its original
  identity, state, history, queue position, and any permanent submission block.
- **6.12** — The FGA API backend **MUST** commit the transaction before
  acknowledging the FGA LrC plug-in.
- **6.13** — The FGA API backend **MUST** return `202 Accepted` with the binding
  and one intent
  snapshot per requested group.
- **6.14** — The FGA API backend **MUST NOT** call Flickr or invoke one worker per
  group in the request handler. After commit, it **MAY** emit at most one best-
  effort partition hint for the canonical-lowest newly eligible partition in
  the complete batch. Every other newly due partition **MUST** remain indexed
  at database current time for the scheduled sweep. A retry that creates no new
  eligible head **MUST NOT** emit a new hint.
- **6.15** — If the HTTP response is lost after commit, the FGA LrC plug-in
  **MAY** safely retry only the identical FGA API handoff with the same binding
  ID, expected verification revision, group-ID set, and request body. It **MUST
  NOT** upload the image again.
- **6.16** — After receiving `202`, the FGA LrC plug-in **MUST** mark its local
  outbox record complete while retaining the non-secret photo-binding ID needed
  for later add-more-groups operations.

The FGA database uniqueness and queue-ordering constraints **MUST** ensure that
a retry cannot duplicate an intent or move it later in FIFO. The database
commit is the durable ownership boundary.

A paused Flickr write gate does not reject or discard this handoff. The FGA API
backend may validate the already-proved binding and commit new intents; its
`202 Accepted` snapshots expose that worker progress is paused. The gate is
checked where Flickr write work would begin in Phase 7.

Binding authorization **MUST NOT** trust a client-supplied user or photo
identity. Response
snapshots follow request order only for reconciliation; response order **MUST NOT**
define queue order. `created: false` identifies an intent that already existed.
`202 Accepted` means the FGA API backend has committed durable ownership of the
work to the FGA database; it does not mean Flickr has
already added the photo to the group. For an existing terminal
`moderation_submitted` or `delivery_uncertain` intent, `created: false` **MUST**
be a hard no-op by the FGA API backend: the FGA LrC plug-in **MUST** report that
the FGA group-submission worker did not resubmit and
**MUST NOT** offer a retry control for that pair.

### Phase 7 — Queue wake-up and independent group progress

Review: Approved by Terry on 2026-08-23. The authoritative private localswim
board records Terry's explicit approval at 09:01:38-04:00 and completion of the
Phase 7 review card at 09:01:41-04:00. ADR 0020 proposes the later one-hint-per-
client-batch amendment; all other Phase 7 behavior remains unchanged.

The provider-neutral implementation supplement is the
[worker persistence and scheduler contract](worker-persistence-scheduler-contract.md)
and ADR 0015. It does not change the accepted Flickr result or
fail-polite semantics below.

Each `(FGA user, Flickr group ID)` partition is an independent FIFO line.

The FGA database retains every durable intent row for idempotency, history, and
status inspection, but its **active FIFO queue** contains only intents in
`queued`, `attempting`, `retrying`, or `throttled` state. `added`,
`moderation_submitted`, `delivery_uncertain`, `needs_attention`, and `cancelled`
are terminal states and **MUST NOT** remain active queue members. A transition
to a terminal state **MUST** atomically remove active queue membership while
retaining the durable intent row and history. A `throttled` or safely retryable
head remains an active queue member and continues to precede later intents in
its partition.

- **7.01** — After one client batch commits, the FGA API backend **MAY** request
  immediate asynchronous progress for only the canonical-lowest newly eligible
  partition. The one best-effort hint carries only opaque partition ID and wake
  revision, may be duplicated or lost, and grants no lease or dispatch
  authority. It **MUST NOT** emit one immediate hint per selected group.
- **7.02** — If the immediate trigger is lost, the database intents remain
  durable and a scheduled due-work sweep running at least once per minute
  **MUST** find them from indexed exact due times. The same sweep recovers
  expired leases and discovers the later nightly due time for code-`5`
  throttling.
- **7.03** — An FGA group-submission worker **MUST** acquire a lease for one
  partition so that only one current lease generation can advance that line at
  a time. The FGA database clock sets expiry, a monotonically increasing
  generation fences prior workers, and every state-changing transaction checks
  both that generation and its opaque lease ID.
- **7.04** — After acquiring the lease, the FGA group-submission worker **MUST**
  check the deployment Flickr write gate and the partition owner's linked-user
  gate. If either is paused, it **MUST** release the lease, send no Flickr
  request, and leave the active head, enqueue value, attempt count, and due time
  unchanged. Otherwise it **MUST** select the active head: the active queue
  member with the lowest immutable enqueue sequence. It **MUST NOT** scan,
  select, or step over terminal intent rows.
- **7.05** — The FGA group-submission worker **MUST** check the exact
  `(Flickr photo ID, Flickr group ID)` pair for a permanent submission block;
  if one exists, it **MUST NOT** make a Flickr write and **MUST** preserve or
  restore the blocked terminal state while atomically excluding that intent
  from active queue membership.
- **7.06** — The FGA group-submission worker **MUST** resolve `www.flickr.com`
  using the hosted DNS resolver and cache, open or reuse an HTTPS connection,
  and atomically reserve global Flickr rate-limit capacity for the membership
  GET, moderation GET, and possible add POST. It **MUST NOT** permit a rate-
  limiter wait to intervene between those operations. Capacity for an operation
  proven unnecessary **MUST** be released exactly once.
- **7.07** — For this individual attempt, the FGA group-submission worker
  **MUST** sign and send
  `GET https://www.flickr.com/services/rest/?method=flickr.photos.getAllContexts&photo_id=<Flickr photo ID>`
  and validate the complete result under the group-membership shape contract.
  A cached selector snapshot, earlier worker result, intent history, or client
  assertion **MUST NOT** satisfy this attempt-scoped read.
- **7.08** — If the membership read is unavailable because of transport, Flickr
  status, shape, truncation, or resource-budget failure, the FGA group-
  submission worker **MUST NOT** send `getInfo` or an add request. If a complete
  observation contains the exact target group, it **MUST** atomically place the
  intent in terminal `added` state with source
  `pre_add_membership_observation`, remove active FIFO membership, and send no
  later Flickr operation. Only a complete target-absent observation may
  continue. An unavailable safe read **MUST** atomically return the intent to
  `retrying` at the same active FIFO head and durably record a sanitized failure
  class, the consecutive safe-read-failure count, and
  `next_attempt_not_before`. The retry delay **MUST**
  be jittered within these inclusive windows for consecutive failures: 30–60
  seconds, 1–2 minutes, 2–4 minutes, 4–8 minutes, and 8–15 minutes for the fifth
  and every later failure. The FGA group-submission worker **MUST** select each
  delay independently, and the scheduler **MUST NOT** round due times to a shared
  boundary; the jitter exists to reduce synchronized retry bursts. A scheduled
  FGA group-submission worker **MUST NOT** retry before the recorded due time,
  and each retry **MUST** restart at step 7.06. A documented permanent,
  authentication, request, or configuration result **MUST** follow step 7.19
  instead of this retry path. A linked-user or deployment-scoped result
  observed during either read-only guard **MUST** pause its durable Flickr
  write gate and retain the intent at the active FIFO head because no add POST
  was sent.
- **7.09** — After a complete target-absent membership observation, the FGA
  group-submission worker **MUST** sign and send
  `GET https://www.flickr.com/services/rest/?method=flickr.groups.getInfo&group_id=<Flickr group ID>`.
  If the response has no usable result because of transport failure, an
  explicitly temporary Flickr result, or a missing or uninterpretable
  `ispoolmoderated` value, it **MUST** follow the unavailable safe-read path in
  step 7.08. Otherwise it **MUST** durably record the fresh moderation value,
  observation time, group ID, photo ID, and attempt ID. A cached value
  **MUST NOT** satisfy this precondition. This `getInfo` **MUST** be the
  immediately preceding Flickr operation before any add.
- **7.10** — If a monotonic clock shows that the preflight response was received at
  least 1,000 milliseconds ago, the FGA group-submission worker **MUST** discard
  that observation and repeat step 7.09 instead of sending a write.
- **7.11** — The FGA group-submission worker **MUST** durably mark the attempt
  `dispatch_started` before the group-add request can be sent. In that same
  transaction it **MUST** confirm that both gate revisions checked in step 7.04
  remain enabled. A paused or changed gate **MUST** prevent the marker and POST,
  preserve the active head without increasing its attempt count, and release
  the lease. After a successful gate check, the worker **MUST** immediately
  recheck the monotonic age; if the observation has now reached 1,000
  milliseconds while the worker still knows no request bytes were sent, it
  **MUST** record `not_dispatched_preflight_expired` and repeat step 7.09.
- **7.12** — Before the elapsed time reaches 1,000 milliseconds, the FGA
  group-submission worker **MUST** begin dispatching a signed
  `POST https://www.flickr.com/services/rest/` with
  `method=flickr.groups.pools.add`, the Flickr photo ID, and the Flickr group
  ID.
- **7.13** — The FGA group-submission worker **MUST** parse Flickr's response
  body and classify its `stat` plus numeric application result code instead of
  inferring success from the HTTP status.
- **7.14** — When Flickr returns “photo added” (`stat="ok"`) or “photo already
  in pool” (code `3`), the FGA group-submission worker **MUST** atomically place
  the intent in terminal `added` state and remove it from active queue
  membership while retaining its durable row and history.
- **7.15** — When Flickr returns “photo added to the pool's pending queue”
  (code `6`) or “photo already in the pool's pending queue” (code `7`), the FGA
  group-submission worker **MUST** atomically create or confirm the permanent
  photo/group submission block, place the intent in terminal
  `moderation_submitted` state, and remove it from active queue membership while
  retaining its durable row and history.
- **7.16** — If “photo added to the pool's pending queue” (code `6`) follows
  `ispoolmoderated="0"`, the FGA group-submission worker **MUST** additionally
  record a moderation-setting race or upstream inconsistency; it **MUST NOT**
  weaken or clear the permanent block.
- **7.17** — When Flickr returns “user has added the maximum allowed photos to
  the pool” (code `5`), the FGA group-submission worker **MUST** atomically and
  durably mark only that `(FGA user, Flickr group ID)` partition `throttled` in
  the FGA database, record the Flickr result, observation time, and
  `next_probe_not_before`, and retain the intent at its head until the next
  conservative probe. That transaction **MUST** commit before the FGA
  group-submission worker releases the partition lease.
- **7.18** — When a complete Flickr response contains the explicit temporary
  status “service currently unavailable” (code `105`) or “write operation
  failed due to a temporary issue” (code `106`), the FGA group-submission
  worker **MUST** retain the head intent for bounded-backoff retry, and every
  later attempt **MUST** restart at step 7.06 with a fresh membership guard.
- **7.19** — The FGA group-submission worker **MUST** map each other documented
  Flickr status and its code to its terminal, authentication, configuration, or
  operator-attention class. Codes `98` and `99` **MUST** pause the linked-user
  Flickr write gate. Codes `95`, `96`, `97`, `100`, `111`, `112`, `114`, and
  `115` **MUST** pause the deployment gate. If an add POST was sent, those
  documented failures remain terminal `needs_attention` for the current intent.
  Any terminal result **MUST** atomically remove active queue membership while
  retaining the durable intent row and history.
- **7.20** — The FGA group-submission worker **MUST** classify an attempt
  `delivery_uncertain` in either of two cases: a durable `dispatch_started`
  marker exists, no durable record proves that zero add-POST request bytes could
  have left the worker, and no definitive documented Flickr result was durably
  committed; or Flickr returned an unknown application code whose side effects
  are undocumented. The first case includes a worker crash after
  `dispatch_started`; a network exception, timeout, or cancellation after the
  POST was handed to the HTTP stack; a missing, truncated, or unparseable
  response; and a crash or database failure after receipt but before durable
  result classification. The FGA group-submission worker's recovery path
  **MUST** atomically create a permanent block, mark the intent terminal
  `delivery_uncertain`, remove it from active queue membership while retaining
  its durable row and history, and **MUST NOT** retry that pair. If the worker
  instead durably proves that zero POST request bytes could have left, it
  **MUST** record that fact, **MUST NOT** create the permanent block, and
  **MUST** retain the head for bounded-backoff retry beginning again at step
  7.06. An unknown numeric Flickr application code **MUST** also pause the
  deployment Flickr write gate because the deployed classifier is incomplete.
- **7.21** — Scheduled processing **MUST** revisit only safely retryable due work
  in scopes whose linked-user and deployment Flickr write gates are both
  enabled, even when the Lightroom Classic host process, the browser, and the
  client computer are closed.

Commit precedes both the success response and the trigger for an FGA
group-submission worker, but network and scheduling timing do not guarantee
which downstream observer acts first. A photo selected for three groups creates
one intent in each of three independent FIFO lines. The FGA group-submission
worker **MUST NOT** use the Windows client's DNS cache for name resolution.
The active FIFO may be implemented as a filtered database index or an equivalent
queue projection; terminal intent rows **MUST NOT** be scanned as queue entries.

Gate resume is an explicit FGA administrative control-plane compare-and-set
after a fresh signed `flickr.auth.oauth.checkToken` result proves the expected
owner NSID and at least `write` permission. It performs no bulk intent rewrite,
has no automatic timeout or bypass, and cannot clear a permanent submission
block.
[ADR 0013](decisions/0013-durable-flickr-write-circuit-breaker.md) defines the
fault scopes, repair evidence, race boundary, and alert contract.

The fresh `ispoolmoderated` read **MUST** be exceptionless, including manual,
administrative, recovery, and test paths. It prevents an uninformed write but
cannot make two separate Flickr calls atomic: the group can change moderation
between the GET and POST. The sub-second deadline bounds only the FGA
group-submission worker's local time before starting the POST; network delay and
Flickr's internal processing remain outside the FGA group-submission worker's
control. The add result remains authoritative.

`moderation_submitted` means “submitted for moderation; final decision unknown,”
not “known to still be pending.” A later positive pool-membership observation
can prove acceptance, but absence cannot distinguish pending from rejected and
**MUST NOT** authorize another add. The permanent block **MUST** survive normal
cleanup, state changes, and cancellations. The FGA API backend and FGA LrC
plug-in **MUST NOT** offer a force-resubmit path; Terry may act manually in
Flickr's own UI, outside FGA automation. The authoritative rationale and
accepted residual race are in
[ADR 0007](decisions/0007-fail-polite-group-submissions.md).

The FGA LrC plug-in **MUST** read later group-submission progress only through
the owner-scoped read-only collection/detail resources in
[ADR 0034](decisions/0034-expose-read-only-group-submission-status.md). A status
read **MUST NOT** call Flickr, emit a worker hint, change a due time, reopen a
terminal intent, or clear a gate/block. The UI **MUST** distinguish active state,
shared gate holds, `added`, `moderation_submitted`, `needs_attention`, and
`delivery_uncertain`; it **MUST NOT** infer moderator rejection or offer retry.

### Phase 8 — Additional photos and final state

Review: Approved by Terry on 2026-08-23. The authoritative private localswim
board records Terry's explicit approval at 09:35:58-04:00 and completion of the
Phase 8 review card at 09:36:01-04:00. Terry approved the zero-group amendment
on 2026-08-25; ADR 0010 records the decision.

- **8.01** — The plug-in **MUST** run steps 4.22 through 5.26 independently for
  every remaining photo and steps 6.01 through 6.21 only when that photo has a
  nonempty group selection. The FGA LrC plug-in **MUST NOT** claim atomic batch
  success or cross-photo completion order and **MUST** retain each photo's
  distinct intermediate or terminal state.
- **8.02** — If an HTTPS connection satisfies the reuse criteria in step 8.03,
  its owning HTTP stack **MAY** reuse it for another request to the same exact
  origin without a repeated DNS lookup or TLS handshake.
- **8.03** — An HTTPS connection is reusable only after the preceding response
  is fully consumed and while the owning HTTP stack retains it as open and
  eligible for the same `(scheme, hostname, port)` origin. When another request
  is ready, a new connection **MUST** be opened if no such connection is pooled,
  either endpoint closed it, the server instructed the client to close it, the
  preceding response was not fully consumed or had invalid or incomplete
  framing, a TCP, TLS, or HTTP protocol error or timeout made it unusable, or the
  HTTP stack retired it under a documented finite idle, lifetime, or
  request-count policy. The FGA LrC plug-in **MUST** leave this decision to the
  Lightroom Classic host's `LrHttp` implementation; each hosted FGA component
  **MUST** use its standard HTTP client's connection-pool decision instead of
  inventing an application-level liveness probe. DNS TTL expiry alone **MUST
  NOT** invalidate an established connection. Before opening the required
  connection, the relevant stack **MUST** resolve the hostname through its
  applicable resolver and cache—obtaining a fresh answer when no unexpired
  cached answer exists—and **MUST** perform a new TLS handshake that validates
  the requested hostname, certificate chain, validity interval, and applicable
  TLS policy.
- **8.04** — Under FGA policy, an image **MUST NOT** be classified as
  successfully “in Flickr” merely because the upload endpoint returned a Flickr
  photo ID. The image counts as durably persisted at Flickr only after the FGA
  API backend receives a complete `stat="ok"` metadata result from the documented
  `flickr.photos.getInfo` method for that exact Flickr photo ID, confirms that
  the response identifies the same photo ID and the expected linked owner NSID,
  and commits the photo ID, observed owner NSID, observation time, and successful
  verification result in the FGA database through an explicit hosted photo
  transaction. For a nonempty group selection, Phase 6 performs that work
  atomically with intent creation. For a zero-group publication, ticket #0020
  must define the separate binding and proof operation before implementation;
  the FGA LrC plug-in **MUST NOT** fake a group batch to reach this state.
  A failed, incomplete, or unparseable response, a missing-photo result, or a
  response containing a different photo ID or owner NSID **MUST NOT** satisfy
  this rule. The committed observation proves API queryability at its recorded
  time; it does not claim that an external actor cannot later delete the photo
  from Flickr.
- **8.05** — For every successful image, the FGA LrC plug-in **MUST** call the
  documented Lightroom SDK's `recordPublishedPhotoId` with the Flickr photo ID
  so the Lightroom Classic catalog durably holds that value as the published
  photo's remote ID.
- **8.06** — The FGA database **MUST** durably hold one intent for every selected
  photo/group pair; a zero-group photo has no such intent.
- **8.07** — Each intent **MUST** be in its correct user/group FIFO partition and
  be able to progress without the Lightroom Classic host process remaining
  open.
- **8.08** — `LrPasswords` **MUST** contain only the FGA installation credential.
- **8.09** — Every pair confirmed in moderation or abandoned after ambiguous delivery
  **MUST** have a permanent hosted do-not-resubmit block in the FGA database;
  the FGA LrC plug-in and FGA API clients **MUST NOT** be able to clear or bypass
  it.
- **8.10** — A later positive pool-membership observation **MAY** record acceptance,
  but silence **MUST NOT** become rejection evidence or clear that block.
- **8.11** — Every Flickr write start **MUST** be refused while either its
  linked-user or deployment gate is paused. Paused queued intents **MUST**
  retain FIFO position and become eligible through normal bounded scheduling
  only after the exact gate revision passes verified administrative resume.

The client-side FGA API and Flickr upload hostnames use Windows DNS;
server-to-Flickr calls use
the hosted environment's separate DNS. The Windows DNS cache contains only
temporary name-resolution state, not authentication or photo state.

Any browser use remains a manual administrative action outside the plug-in
activation and publishing protocols.

## Explicitly deferred details

- Public, multi-user, self-service, or browser/device pairing.
- The exact plug-in-owned storage mechanism for recovery/outbox records that
  receive an immutable selection before render or existing-photo handoff.
- Reconciliation UX for `upload_outcome_unknown`.
