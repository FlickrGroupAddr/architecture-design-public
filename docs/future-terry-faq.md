# Future Terry FAQ

Last updated: 2026-09-03

Authority: Derived explanation; not a normative source. Follow the
[documentation authority hierarchy](README.md) and each linked source's status.

Purpose: answer the architecture, authentication, and bootstrap questions that
are easy to ask after returning to FGA cold.

## What is the shortest correct mental model?

```text
Phase 1, Part 1: Authorize hosted FGA to call Flickr as Terry.
Phase 1, Part 2: Create a credential for one Lightroom installation to call FGA.
Phase 2:         Paste that credential into the installed plug-in and activate it.
```

Flickr's credentials remain in the FGA managed secret store. The FGA LrC
plug-in receives only its revocable FGA installation credential.

## What does “fail-polite” mean, and why is it FGA's highest-priority rule?

Before FGA, Terry used a spreadsheet to track photo/group requests delayed by
Flickr's group throttles. FGA exists to automate that bookkeeping, not to turn
Terry's convenience into repeated work for Flickr's volunteer moderators.
Permanently abandoning a request is infinitely preferable to risking a second
moderation event.

The exceptionless rule is:

1. Before every possible individual `flickr.groups.pools.add`, the FGA group-
   submission worker performs a fresh strict `flickr.photos.getAllContexts`
   read for the exact photo. If that read is unavailable, it sends neither
   `getInfo` nor add. If the exact target group is already present, it
   terminalizes the intent without a write.
2. After a complete target-absent result, the FGA group-submission worker calls
   `flickr.groups.getInfo` for that group and durably records the returned
   `ispoolmoderated` value and observation time. No cached value counts. If the
   preflight fails or its value is not interpretable, it sends no add request.
   The FGA group-submission worker starts POST dispatch less than 1,000
   milliseconds after receiving the preflight response; otherwise it discards
   the observation and GETs again.
3. The FGA group-submission worker reserves capacity for the membership GET,
   moderation GET, and possible POST atomically before the first read. The
   `getInfo` call remains the immediately preceding Flickr operation before an
   add.
4. Flickr's “photo added to the pool's pending queue” status (code `6`) or
   “photo already in the pool's pending queue” status (code `7`) permanently
   blocks FGA from adding that exact Flickr photo ID to that exact Flickr group
   ID again.
5. If `dispatch_started` is durable, no durable record proves that zero add-POST
   request bytes could have left the FGA group-submission worker, and no
   definitive documented Flickr result was committed, the FGA
   group-submission worker permanently abandons the request as
   `delivery_uncertain` instead of retrying it. An unknown Flickr result code
   receives the same block because the FGA group-submission worker cannot assume
   the new code had no moderation side effect.
5. FGA never provides a force-resubmit path for a blocked pair. Terry may log
   into Flickr and resubmit manually; FGA is intentionally not a participant.

The preflight is mandatory informed context, not magic concurrency control.
Moderation can switch between the metadata GET and add POST. If the preflight
says unmoderated and Flickr then returns “photo added to the pool's pending
queue” (code `6`), FGA records the race or upstream inconsistency, permanently
blocks the pair, and never retries it.
Flickr exposes no documented atomic read-and-add operation that could make this
two-call race impossible. The sub-second deadline bounds only FGA's local gap,
not network transit or Flickr's internal processing. Terry explicitly accepted
that smallest documented-API residual race on 2026-08-21 as responsible best
effort without shame; ADR 0007 preserves the complete rationale.

Flickr also exposes no documented submitter-facing query that distinguishes
still pending from moderator-rejected. If the photo later appears in the pool,
FGA can record that acceptance was observed. If it does not appear, FGA learns
nothing: pending and rejected remain indistinguishable. Time and absence never
clear the permanent block.

Flickr and FGA also cannot share a database transaction. If FGA receives
“photo added to the pool's pending queue” (code `6`) but crashes before
committing the exact result, recovery records the pair as `delivery_uncertain`
rather than confirmed moderation. The label is less precise, but the safety
result is identical and permanent: FGA never resubmits the pair.

Flickr reports “photo added to the pool's pending queue” (code `6`) and “photo
already in the pool's pending queue” (code `7`) as application-level failure
payloads, so the worker must parse `stat` and the numeric body code rather than
relying on the HTTP status. The authoritative design is
[ADR 0007](decisions/0007-fail-polite-group-submissions.md); the complete result
matrix is in [Flickr API research](research/flickr.md#adding-to-a-group).

## Why is the moderation block permanent if the group is unmoderated now?

Because “unmoderated now” does not mean “nobody remembers the earlier
submission.” A realistic lifecycle is:

1. The group is moderated and FGA submits the photo to its queue.
2. The volunteer moderator takes a multi-month break.
3. The group becomes unmoderated while that person is away.
4. Months pass.
5. The same moderator returns and makes the group moderated again.
6. That moderator may remember rejecting this exact photo the first time.

Resubmitting at step 5 could create precisely the repeated volunteer burden
that fail-polite exists to prevent. Consequently, “photo added to the pool's
pending queue” (code `6`) or “photo already in the pool's pending queue” (code
`7`) is a permanent historical fact for that exact Flickr photo ID and Flickr
group ID.
No current `ispoolmoderated` value, moderation transition, elapsed time,
retention cleanup, or moderator absence clears it. A fresh unmoderated
preflight can inform a first submission; it can never authorize resubmission of
a permanently blocked pair.

## Which hostname belongs to which system?

| Host | Owner and role |
| --- | --- |
| `flickrgroupaddr.com` | Project-owner-controlled FGA API, administrative control plane, and Flickr OAuth callback |
| `www.flickr.com` | Flickr OAuth and ordinary Flickr REST methods |
| `up.flickr.com` | Flickr's separate binary photo-upload endpoint |

Every HTTP call in the zero-state flow names its host so an FGA endpoint cannot
be mistaken for a Flickr endpoint.

## How can an existing Flickr photo enter without trusting a client photo ID?

The FGA LrC plug-in exposes a separate **Add Groups to Existing Flickr Photo…**
command. It asks the FGA API backend for advisory pages of public photos from
the configured Flickr owner, shows a recognizable title/date/thumbnail
selection inside Lightroom Classic, and neither renders nor uploads anything.
The listing helps Terry choose; it is not proof.

After selection, and again immediately before a handoff that could create new
intents, the FGA API backend calls documented `flickr.photos.getInfo` with the
current linked grant. It requires the exact returned photo ID, configured owner
NSID, public visibility, and unchanged link revision before committing a
server-generated common photo binding. The group batch carries only that
binding ID, its current verification revision, and group IDs; it contains no
client Flickr photo ID. Upload-origin photos converge on the same binding.

Catalog remote IDs may improve labels or shortcuts but never decide
eligibility, ownership, visibility, or authority. The detailed boundary is the
[existing public Flickr photo intake contract](existing-public-photo-intake.md)
and [ADR 0021](decisions/0021-fresh-server-proof-for-existing-public-photos.md).

## Does selecting an existing photo migrate it into the FGA publish service?

No. The queue-only command creates a hosted FGA photo binding and selected
group intents. It does not create or alter a Lightroom Classic published-photo
record, attach or remove a Flickr album membership, replace pixels, delete the
photo, or upload another copy.

Lightroom Classic does document a catalog operation that can add a local photo
and remote ID to a published collection, but that would create a second
provider-scoped catalog association—not transfer Adobe's Flickr plug-in record
or prove anything about the remote pixels. Ticket #0067's disposable-catalog
probe proved that the local association is restart-persistent, provider-scoped,
undoable, and removable without changing Adobe's Flickr source record.
[ADR 0038](decisions/0038-keep-existing-photo-intake-queue-only.md) keeps the
feature absent because group queueing already works without the duplicate
provider record and its republish/removal lifecycle.
[ADR 0022](decisions/0022-separate-photo-identity-from-catalog-and-album-records.md)
and the [non-destructive boundary](non-destructive-existing-photo-boundary.md)
record the distinction.

## Why does FGA use an apex domain while Flickr calls retain `www`?

FGA intentionally uses the no-`www` origin `https://flickrgroupaddr.com`. The
project owner controls that domain and chooses its canonical form.

As checked on 2026-08-21, Flickr's apex and `www` names both served the ordinary
REST path without redirecting, but Flickr's official OAuth and REST
documentation specifies `www.flickr.com`. OAuth 1.0a signs the exact request
URL, including its host. FGA therefore follows Flickr's documented spelling
instead of treating a currently working alias as a supported contract.

## Does the Lightroom SDK guarantee "best TLS" or TLS 1.3-or-newer?

No. The current Adobe `LrHttp` documentation promises HTTPS support and reports
generic security or certificate failures, but it documents no TLS minimum,
maximum, version selector, newest-version promise, or negotiated-version query.
The FGA LrC plug-in gets the TLS version that the Lightroom Classic host
networking stack and the remote server negotiate.

FGA can configure its own edge to reject protocol versions below a chosen
minimum. That would be an FGA deployment rule validated using the latest
production Lightroom Classic release offered through Adobe Creative Cloud on
the latest production/stable Windows release adopted by the owner, not a
capability guaranteed by Adobe's SDK.

Owner preference: try TLS 1.3-or-newer only, with the tightest conventional
cipher configuration that this LrC-on-Windows target and the current
administrative browsers can actually negotiate. If the real LrC probe fails,
relax only the smallest necessary setting and commit the evidence and
exception. Do not preserve old-client compatibility speculatively.

Accepted ADR 0036 right-sizes the private-MVP set to the real supported
Lightroom Classic `LrHttp` path, pinned `testssl.sh` with structured output, one
fresh Qualys SSL Labs assessment (`A+` required), and certificate issuance,
rollover, renewal, and deployment-restore checks. Incidents, material edge
changes, and public/multi-user expansion add diagnostics selected for the
actual risk; they do not create a standing scanner-vendor matrix. MDN HTTP
Observatory and SecurityHeaders.com check HTTP headers rather than TLS. See
[FGA HTTPS-edge TLS deployment acceptance](operations/tls-edge-acceptance.md).
The core set is rerun and graded for every actual LrC major release and each
quarter after deployment; see the
[development and operations diligence cadence](operations/development-and-operations-cadence.md).

## How much work is the annual Lightroom/Windows diligence run?

Terry's intended workload is three actions: start the adopted Windows and
latest Creative Cloud LrC target, load or reload the development-only **FGA
Diligence** plug-in if needed, and click **Run FGA Diligence Checks** once.
Codex watches `C:\Temp\FGA-diligence-status.json`, performs the external TLS and
decoded-image checks, and assembles the evidence.

This is a separate development plug-in so annual test machinery cannot enlarge
or destabilize the production publish provider. Its eventual one-click chain
covers credential retrieval, strict-edge `LrHttp`, a canonical PNG render,
decoded-pixel/structure comparison, direct Flickr upload, durable FGA queue
acceptance, group submission, terminal visibility, and deliberate cleanup. A
missing unimplemented component reports `blocked`; it never quietly passes.
See [development and operations diligence
cadence](operations/development-and-operations-cadence.md#dedicated-lightroom-diligence-plug-in).

## Does the Lightroom plug-in launch a browser during private-MVP setup?

No. The browser-based Flickr authorization starts in FGA's administrative
control plane. An administrative browser on any trusted machine visits Flickr,
Terry approves FGA, and the browser returns Flickr's verifier to the hosted FGA
callback. The plug-in does not participate.

The Flickr grant in Part 1 may happen on another trusted machine. The private
installation-credential ceremony in Part 2 deliberately uses a clean private-
browsing window on the target Lightroom workstation for one local paste, then
overwrites the current clipboard and closes the whole private window. The
security boundary is that the plug-in never launches, requires, controls, or
exchanges data with that browser; same-machine presence does not create a
plug-in/browser protocol.

When no installation credential is stored, the plug-in displays the FGA User
UI Plugin Code URL beside its transient Plugin Code input.
Terry may open that URL manually in a browser on any trusted device. The
plug-in does not launch that browser, send data to it, receive a callback from
it, or poll it; Terry simply pastes the generated credential into the input.
Before **Store and verify**, both surfaces show the same clear-text 64-character
Plugin Code with identical four-character grouping and typography so Terry can
compare them side by side. The FGA LrC plug-in accepts only ADR 0044's exact
uppercase Crockford Base32 spelling; it never fixes case, aliases, whitespace,
or hyphens.

## After Phase 1, Part 1, can the FGA backend interact with Flickr as Terry?

Yes, within the Flickr permissions Terry granted. FGA retains the Flickr
consumer secret plus Terry's Flickr OAuth access token and token secret in
managed secret storage and associates Terry's Flickr owner NSID with the FGA
account. That allows the API and workers to make signed Flickr calls for Terry.

Lightroom never receives those long-lived Flickr signing secrets.

## What exactly is "pre-registered" in Phase 1, Part 2?

One server-side Lightroom installation identity and its revocable credential.
It is not the plug-in binary, a customized download, or a different build of
the plug-in. Every installation can use the same ordinary plug-in package while
receiving a different installation identity and credential.

## Must Phase 1, Part 2 happen before downloading or installing the plug-in?

No. Provisioning must precede successful activation, not download or
installation. Both of these orders are valid:

```text
Create credential -> install plug-in -> paste credential -> activate

Install plug-in -> see "not connected" -> create credential
              -> paste credential -> activate
```

The zero-state walkthrough uses the second order: the plug-in is already
installed, finds no credential in `LrPasswords`, and waits for Terry to paste
one.

## What happens immediately after I paste the credential?

The plug-in stores it in `LrPasswords`, clears the visible input, then presents
it to:

```text
GET https://flickrgroupaddr.com/api/v001/installations/current
Authorization: Bearer <FGA installation credential>
```

The request has no body, query parameter, or client-supplied profile. A current
matching credential returns `200 OK` with the active installation's identifier,
revision, state, and `presentedCredentialState: "current"`; only then does the
FGA LrC plug-in mark its FGA connection authenticated. A later pending rotation
candidate may read the same resource with `presentedCredentialState:
"pending_rotation"`; it has no ordinary route authority. This read does not
call Flickr or fetch the group list. Group discovery is the next, separate
request. It creates no session and returns no new token; every later API call
authenticates the stored credential again.

The internal server-assigned class is `lrc_plugin`; it is neither supplied by
the request nor returned by this resource. If a future concrete second profile
is justified, the FGA API backend can add explicit capability representation
or negotiation without renaming the current-installation resource. The HTTPS
connection may remain open for reuse after the `200`; that is normal keep-alive,
not an unfinished request.

## Why is the credential in `Authorization` instead of an `HttpOnly` cookie?

Because the plug-in is not a browser. The LrC 15.3 SDK explicitly lets
`LrHttp.get` callers supply headers and even uses `Authorization` in Adobe's
example. It can return and parse `Set-Cookie`, but Adobe documents no persistent
browser-style cookie jar, automatic replay, or `HttpOnly` isolation boundary.

`HttpOnly` protects browser-managed cookies from browser script APIs. If Lua
has to read the cookie, store it in `LrPasswords`, and construct later `Cookie`
headers itself, that protection does not exist. The explicit HTTPS
`Authorization: Bearer ...` header is simpler, is conventional bearer-secret
transport, and is easier for infrastructure to redact consistently. The
credential is never placed in a URL, query parameter, or body.

Receipts, so this does not look like a 2026 YOLO convention:

- [RFC 9110 §11.6.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-11.6.2)
  defines the `Authorization` field for origin-server credentials.
- [RFC 6750 §§1 and 2.1](https://www.rfc-editor.org/rfc/rfc6750.html#section-2.1)
  defines the exact `Authorization: Bearer <b64token>` format and explicitly
  permits bearer tokens from any source, not only an OAuth issuance flow.
- [RFC 6750 §5.3](https://www.rfc-editor.org/rfc/rfc6750.html#section-5.3) and
  the [OWASP REST Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html#sensitive-information-in-http-requests)
  require or recommend HTTPS/header transport and keeping secrets out of URLs.
- [RFC 10025 §4.1.2.6](https://doi.org/10.17487/RFC10025) defines `HttpOnly` as
  a conforming user-agent cookie boundary; Adobe documents no such Lightroom
  cookie store or enforcement contract.

The comprehensive standards map, including the accepted private-MVP bearer
limitations, is in the
[plug-in/service contract](plugin-service-contract.md#standards-and-best-practice-map).

## Why does an inactive or bad-signature credential return `401`, not `403`?

Because successfully parsing a token is not successfully authenticating it.
[RFC 6750 §3.1](https://www.rfc-editor.org/rfc/rfc6750.html#section-3.1) assigns
expired, revoked, malformed, and otherwise invalid tokens to
`401 Unauthorized` with `invalid_token`. It reserves `403 Forbidden` with
`insufficient_scope` for an authenticated token whose privileges are too small
for the requested resource.

An earlier FGA draft used `401` for missing/malformed credentials and `403` for
well-formed credentials that were unknown, inactive, revoked, disabled, or
failed verification. The intent was to conceal which credential check failed,
but the status split added no protection. One generic `401 invalid_token` for
every invalid-token cause reveals no more detail and matches standard clients,
middleware, dashboards, and developer expectations. Terry rejected the custom
split on 2026-08-21 under the boring/least-surprise rule.

## What if this release sees a credential class it does not recognize?

It rejects the credential as `401 invalid_token`. The stored class is
authoritative; no request field can create or broaden it. There is
no default that treats an unknown, null, differently cased, retired, or future
class as a browser, administrator, legacy client, or nearest supported version.
Browser administration uses its separate Google-authenticated FGA cookie session and never
enters the installation Bearer dispatcher.

Adding a class follows expand/deploy/create order: every server first learns the
new exact class and route/method allowlist, then the database constraint expands,
then credentials are created. An older binary encountered during rollback fails
closed. Service for that new class may be unavailable until its rows are
revoked/migrated or the supporting release returns, but its privilege never
increases. The authentication suite explicitly tests both forward and rollback
version skew.

## What additional up-front friction are we accepting?

For the private MVP, Terry must:

1. Sign into the FGA User UI with Google.
2. Connect FGA to Flickr once.
3. Select **Create Plugin Code** to create one FGA LrC plug-in installation
   identity and reveal its Plugin Code once.
4. On the target Lightroom workstation, use a clean private-browsing window
   with Windows clipboard history/sync off to copy the one-time value;
5. Paste it directly into the plug-in once, compare both simultaneous clear-
   text values, then store and verify it; and
6. overwrite the clipboard with the page's non-secret cleanup text and close
   the private window.

The FGA User UI's current browser route remains under `/admin/` until that
route is separately renamed. [ADR 0040](decisions/0040-expose-plugin-codes-as-user-resources.md)
fixes the user-owned collection as `GET` and `POST /api/v001/plugin-codes`,
with `PATCH /api/v001/plugin-codes/{pluginCodeId}` for terminal revocation.
ADR 0018 and the
[private installation credential transfer ceremony](private-install-credential-transfer.md)
fix the security-relevant sequence. Accepted
[ADR 0044](decisions/0044-use-canonical-crockford-base32-plugin-codes.md) fixes
the canonical grouped spelling and identical clear-text comparison style; other
ordinary page styling remains implementation detail.

For the concise memory map, all three tabs of the
[clean-room authentication diagram](diagrams/clean-room-authentication-legal.drawio)
are authoritative for the depicted browser-session, Plugin Code, and
publish-and-group-submission happy paths under
[ADR 0041](decisions/0041-use-clean-room-authentication-tabs-as-interaction-authority.md).
They are necessary but not sufficient: the surrounding contracts add required
detail without changing those sequences.

## Is this the smart-TV device-code dance we wanted to avoid?

Yes. An OAuth device-authorization flow would work approximately like this:

1. The plug-in asks FGA for a temporary device code, user code, and verification
   address.
2. The plug-in displays the user code and address.
3. Terry opens the address in a browser, authenticates to FGA, and approves the
   waiting Lightroom installation.
4. The plug-in polls FGA until approval succeeds, fails, or expires.
5. FGA issues the permanent installation credential.

The standard smart-TV pattern normally tells the user to open a browser on a
second device; the TV does not necessarily launch that browser. A different
native-application flow could launch the Lightroom host's browser and wait for
a callback. The private MVP avoids both interaction models.

See [RFC 8628](https://www.rfc-editor.org/rfc/rfc8628.html) for the standardized
OAuth device-authorization flow and
[RFC 10027](https://www.rfc-editor.org/rfc/rfc10027.html) for the
current-at-writing cross-device security guidance. Any future FGA
implementation must make a new decision and review the then-current guidance
rather than blindly copying this summary.

## What machinery does manual pre-provisioning avoid?

- Device-code and approval endpoints.
- Human-entered short-code generation and guessing protection.
- Temporary pairing records and expiration.
- Plug-in polling and polling rate limits.
- One-time code redemption and replay protection.
- Browser-to-installation approval binding.
- Ambiguous completion and abandoned-pairing recovery.
- A browser callback listener or custom URI handler on the Lightroom host.

That is why the private design accepts a manual create, transfer, and paste
operation: it removes an entire temporary authentication protocol.

## How does Terry authenticate to the FGA administrative control plane?

Through direct Google Identity Services sign-in and one exact allowlisted,
validated Google `sub`. The FGA database maps the canonical Google issuer and
`sub` to one opaque internal `fgaUserId`; FGA-owned records use that internal ID
rather than email as their ownership key. GIS posts a Google-signed ID token and
matching cookie/body `g_csrf_token` values to exact endpoint
`POST /admin/google-login`. The endpoint checks
that double-submit pair, then uses a maintained Google authentication library
and the FGA backend's cache of Google's current JWKS to validate trusted key and
algorithm, signature, audience, issuer, and applicable time claims. Only `sub`
is stable Google identity.

The FGA JWKS refresh worker normally updates that shared cache outside login
requests, by the earlier of six hours and Google's metadata-driven freshness
deadline. A login naming an unknown signing key ID is the rare exception: after
admission and CSRF validation, it may wait for one bounded refresh and fails
closed if the key still is not available.

The FGA Google Login Endpoint generates a 256-bit opaque token, stores only its
`SHA2-256` digest as the session-database lookup key, and keeps `fgaUserId`,
validated `sub`, only needed profile fields, and explicit FGA session metadata
as the value. It
returns the token only in a `Secure`, `HttpOnly`, `SameSite=Strict`, `Path=/`,
`__Host-` cookie with no `Domain` and `Max-Age=86400`. The server-side session
has the same non-sliding 24-hour lifetime and no shorter idle timeout. Unsafe
operations also require an exact-origin, session-bound CSRF token. Accepted ADR
0043 binds rare sensitive mutations to a five-minute, one-use GIS state/nonce
transaction, rotates that current session, and expressly does not claim a fresh
factor, passkey, MFA, or phishing-resistant challenge.

It does not use a local FGA password, email address as identity, IP address,
secret URL, Flickr login, or FGA installation credential. The last option would
be circular: the control plane is the component that creates and revokes that
credential. Accepted ADRs 0039 and 0043, the accepted
[browser-session lifecycle](browser-session-lifecycle.md), and the accepted
private-MVP administrative control-plane contract contain the authentication,
authorization, audit, expiry, and failure boundaries.

If the hosted stack uses Django, its installation-wide framework-signing key is
a separate managed secret, not the cookie value and not the FGA session
verifier. The purpose-built session table uses only `SHA2-256(token)` for
lookup. The proposed provider-specific [session-signing key
contract](operations/session-signing-key.md) preserves one candidate for
framework-key generation, binding, rotation, and negative tests.

## How do we know an asset router will not swallow an authentication callback?

The hosted build derives one route inventory from the FGA API backend's actual
route registrations. Exact `/api/v001` and prefix `/api/v001/`, exact
`/admin/google-login`, and `/admin/flickr-oauth/callback` are server-first and
precede every static asset or administrative-shell fallback. Accepted ADR 0043
requires that login URI to be registered before implementation.
Development and deployment do not maintain a separate manual
`/auth`/`oauth` list.

One required gate checks the generated inventory and both real router artifacts,
then sends safe black-box probes through the development topology and an
isolated provider preview for the exact build. A handler unit test or mock
router cannot substitute. This architecture repository has no hosted router,
so it truthfully records that no pass exists yet.
[ADR 0050](decisions/0050-select-cloudflare-and-evaluate-native-storage-first.md) selects Cloudflare; its actual
development and preview asset routers must pass this gate. ADR 0033 preserves
only the superseded Google Cloud proposal.
ADR 0016 and the HTTP route/asset-router conformance contract define the
evidence.

## Is there a public debug or deployment-status endpoint?

No public debug endpoint exists. ADR 0037 deliberately leaves
`/api/debug` unregistered and server-owned as a no-store JSON `404`; it cannot
fall through to the administrative shell. The only unauthenticated operational
routes are fixed `/healthz/startup` and `/healthz/live` responses needed by
Cloud Run. They reveal no signed-in identity, origin, build, environment,
configuration, dependency, or provider detail, and liveness calls no external
dependency.

Useful sanitized build, revision, route-inventory, migration, application, and
database state lives at `GET /api/v001/admin/deployment`. It requires Terry's
existing Google-authenticated FGA administrative session and remains `Cache-Control:
no-store`. Logs, metrics, alerts, and provider exports supply deeper operator
evidence without creating a secret query switch or public support back door.
The accepted [health and diagnostics
contract](operations/health-and-diagnostics.md) owns the exact schemas and
negative tests.

## What if I click sign out and the server does not answer?

The administrative UI immediately stops polling, cancels outstanding reads,
and removes administrative data from its view, but it does not call that a
successful logout. The session cookie is `HttpOnly`, so client code cannot
inspect or delete it. Until the FGA API backend returns a complete `204` after
durably revoking the server session, the UI says **Sign-out unconfirmed. This
browser may still hold an active FGA administrative session.**

**Retry sign out** repeats the same idempotent POST. It succeeds whether the
first transaction never committed, committed but lost its response, or already
cleared the browser cookie. A failed or indeterminate server transaction leaves
the cookie in place specifically so that retry remains possible. Closing every
window in the private-browsing context clears that context's local cookie but
does not prove server revocation; the row expires at its non-sliding 24-hour
absolute deadline or can be revoked from a separately authenticated session
inventory. The
[OAuth and account
lifecycle](oauth-and-account-lifecycle.md#logout-outcome-and-recovery) owns the
wire ordering, exact copy, and failure-injection gates.

## Can someone fill the service with login or device-link attempts?

There is no device-link start, device code, signup, or self-service OAuth-start
route in the private MVP. A guessed legacy path creates nothing and receives the
ordinary API `404`. Any future public flow remains blocked on its separate abuse
threat model; this admin-only control does not pre-approve it.

The exposed `/admin/login` route is bounded before it creates state: 5 starts
per normalized source per 10 minutes with burst 2, 30 starts deployment-wide
per 10 minutes, and at most 20 live five-minute transactions. Unknown callback
traffic has separate source/global windows. The browser callback consumes one
exact state before one upstream exchange; it is not tied to an IP that may
change legitimately.

All counters are shared across FGA API backend instances, and source keys are
short-lived HMAC using SHA2-256 values rather than stored addresses. A limiter
failure denies only login/callback work. Limits return generic `429` without
bucket details, sustained saturation alerts once per window, and changing the
values reruns authentication, routing, and end-to-end gates. CAPTCHA or provider
bot scoring may supplement but cannot replace those hard bounds.

## Why not let the plug-in create or claim its own credential?

The Lightroom SDK has no documented cryptographically secure random generator,
so it cannot safely create the credential. More fundamentally, an empty client
has no proof that it belongs to Terry. A public "first caller wins" claim
endpoint would let an attacker become the owner. FGA therefore generates the
secret and transfers it through an already trusted administrative channel.

## What about an importable but undocumented Lightroom call such as `LrUUID`?

No. FGA depends only on interfaces in Adobe's newest published Lightroom SDK
API Reference. A symbol that happens to be importable or visible in a binary is
an implementation detail, not a supported contract; it may disappear or change
without notice. `LrUUID` also has no documented cryptographic-security promise.
The annual SDK call-zoo review will notice if Adobe adds a documented secure
random or UUID primitive, and only then will FGA evaluate it.

## Which credential is stored where?

| Credential or identity | Stored where |
| --- | --- |
| Flickr application consumer secret | FGA managed secret storage only |
| Terry's Flickr OAuth access token and token secret | FGA managed secret storage only |
| Terry's Flickr owner NSID | FGA database as non-secret identity |
| Plaintext FGA installation credential | Displayed once, transferred confidentially, then stored by the FGA LrC plug-in in `LrPasswords` |
| FGA installation credential SHA2-256 digest and state | FGA database |
| Long-lived Flickr secrets in Lightroom | Nowhere; Lightroom never receives them |

## Why is a SHA2-256 digest appropriate for the installation credential?

The credential is not a human password. The FGA API backend generates 32 random
octets and preserves all 256 bits in ADR 0044's canonical grouped encoding, so
it does not have the small, guessable search space that requires a slow
password-hashing function. Storing its SHA2-256 digest lets the FGA API backend
find and verify the random bearer credential without retaining its plaintext.

## Why is there no HMAC tag appended to the credential?

The opaque credential contains no client-visible identity, permission,
expiration, or other claim for an HMAC to protect. FGA must query the database
anyway to resolve the installation and enforce revocation. A valid HMAC would
not stop anyone who stole the complete bearer credential from using or
replaying it. It would add a global HMAC key and its storage, rotation, parsing,
and failure modes without removing existing work.

## Why is the stored SHA2-256 digest unsalted?

Salts protect low-entropy, frequently repeated human passwords from
precomputation and amortized guessing. Every FGA installation credential has
256 independently generated random bits, so a database attacker already faces
an infeasible search and credentials will not meaningfully repeat. A stored
salt would not change that search and would prevent direct digest lookup unless
the credential also exposed a public selector solely to retrieve its salt.

These choices do not weaken protection against the actual bearer-token risk:
theft of the plaintext credential. Neither an appended HMAC nor a stored salt
would prevent an attacker from presenting a stolen complete credential. HTTPS,
`LrPasswords`, nonlogging, narrow authorization, and revocation address that
risk.

## What if the installation credential is lost or compromised?

The FGA database cannot recover the one-time plaintext from its digest. For a
lost, stolen, or suspected-compromised workstation, Terry uses a different
trusted device to revoke the whole installation first, remediates the endpoint,
and creates a wholly new installation identity. The FGA administrative control
plane reports server revocation separately because it cannot prove the lost
workstation erased its `LrPasswords` copy.

Routine planned rotation is less disruptive. The administrator creates one
15-minute candidate; the FGA LrC plug-in stores it under a second
`LrPasswords` key and proves it by reading the current-installation resource.
Terry then uses
the recent-authenticated administrative completion action; the FGA database
atomically promotes the candidate and retires the old version—there is never a
normal-route interval with two active credentials. Only after the FGA LrC
plug-in observes the candidate's `current` state does it move its local current key. If
a response or process is lost, the candidate key and administrative inventory
resume the exact state rather than falling back to the old value. ADR
0019 records the full lifecycle.

Revocation stops new FGA API transaction commits after their authoritative
credential recheck. It cannot recall a short-lived upload envelope already
returned or erase actions and group intents already durably accepted.

## What happens if Flickr revokes the linked grant or the application configuration breaks?

The affected hosted components stop starting Flickr writes after the first
definitive scoped result. A revoked or under-permissioned OAuth grant pauses one
linked user's durable write gate; a bad application key, signer, request method,
format, protocol, or unknown result code pauses the deployment gate. Existing
queued intents keep their FIFO positions instead of being terminalized one by
one.

The pause survives restarts and never expires automatically. Terry repairs or
reauthorizes the affected scope through the FGA administrative control plane.
Before the exact pause revision can resume, the FGA API backend uses the
repaired credentials for a fresh, non-mutating
`flickr.auth.oauth.checkToken` call and requires the expected Flickr identity
and `write` permission. Request-builder and classifier defects also require the
corrected deployment's conformance result. Normal bounded scheduling then
continues; the resume does not rewrite intent history or clear a moderator-
protection block. ADR 0013 records the full contract.

If Terry explicitly disconnects instead, the FGA API backend first removes the
active secret authority and pauses new Flickr operations, then deletes the
inactive managed-secret version. Flickr does not document an application-side
token-revocation method, so the FGA administrative control plane reports that
local result separately and sends Terry to Flickr's Sharing & Extending
settings to use **Remove Permission**. It does not claim that Flickr permission
was revoked merely because the local copy was deleted. A same-owner relink
preserves every permanent submission block,
dispatch-ambiguity record, queued intent, upload binding, gate event, and audit
event, and it still requires a separate verified gate resume. ADR
0017 records the full lifecycle.

## What happens if a group-submission worker or wake-up message disappears?

The FGA database, not the message or worker process, owns the queue. Each
`(FGA user, Flickr group ID)` partition has an exact next-work time and an
expiring database-clock lease with a monotonically increasing generation. An
immediate message is only a disposable partition/revision hint. A periodic
database due sweep runs at least once per minute, so it recovers a lost hint and
claims an expired lease without changing FIFO order.

The generation fences an older worker after takeover. Recovery first examines
the durable attempt: no dispatch marker is safely retryable; an unresolved
`dispatch_started` marker without zero-byte proof creates the permanent
photo/group block and terminal `delivery_uncertain` state. It never guesses from
elapsed time that Flickr did not receive the POST. ADR 0015 and the
worker persistence/scheduler contract define the complete transaction matrix.

## How do I see queue progress or a problem that needs attention?

The FGA LrC plug-in's **FGA Queue Status** view reads owner-scoped
`group-submission-intents` resources. It shows exact durable state separately
from advisory position within that Flickr group's FIFO, next due time, shared
write-gate holds, the latest sanitized outcome, and any permanent exact-pair
block. It never turns `202 Accepted` into “added,” a paused gate into a failed
intent, or absence from a group into moderator rejection.

The view has `active`, `attention`, and retained `history` pages. Attention
means terminal `needs_attention` or `delivery_uncertain`; a moderation-queue
submission is a completed FGA action with a permanent do-not-resubmit block,
not an attention prompt. The administrative control plane has separately
authenticated read mirrors and its existing verified gate-repair workflow.

There is no status-screen retry button. Reading or refreshing status cannot
wake a worker, defeat a due time, reopen a terminal row, clear a gate, or remove
a permanent block. Active safe retries progress through the database scheduler;
terminal attention remains terminal, and Terry can inspect or act manually in
Flickr when the reviewed guidance calls for it. ADR 0034 and the
group-submission status API contract define the exact schemas and copy. The
[moderator-safety UI conformance
contract](moderator-safety-ui-conformance.md) applies one block-first rule to
the selector, status view, repeated-batch response, and future administrative
UI, so no screen can pair a no-repeat promise with an acknowledged resubmission
control.

## Why does every client submit groups through one batch operation?

One photo selection is one admission event even though the FGA database creates
one intent per group. The FGA LrC plug-in sends the complete bounded unique
group-ID set once; a future authorized browser must use the same operation. The
FGA API backend has no single-group create alias, validates the whole request,
and commits every missing intent in one transaction or none.

The request handler makes no Flickr call and emits at most one immediate hint
for the canonical-lowest newly eligible partition. Every other due partition
remains indexed for the scheduled sweep. This prevents one multi-group click
from becoming one immediate worker notification per group. An over-limit
selection is refused as a whole rather than silently sliced. ADR 0020
and the `CBA-*` conformance contract define the boundary.

## What if Flickr says success but returns malformed group memberships?

The FGA API backend treats the observation as unknown, not empty. A successful
membership snapshot requires the complete Flickr JSON root, `stat: "ok"`, an
explicit array-valued pool collection, and valid bounded ID/title fields for
every pool entry. One missing, null, non-array, duplicate, malformed, truncated,
or over-budget element invalidates the whole observation; the parser never
filters bad entries or defaults the collection to `[]`.

The FGA LrC plug-in receives **Membership Unavailable**, discards any incomplete
page aggregate, and cannot confirm additions for that already-published photo
until a new initial read succeeds. It does not show a previous snapshot as
current. Only a fully validated explicit empty pool array means Flickr was
observed to report no current memberships.

## What if the worker cannot re-read membership before an add?

The FGA group-submission worker sends no add. Every possible add attempt starts
with a new strict `flickr.photos.getAllContexts` read for the exact photo; the
selector's earlier snapshot and prior worker observations are not write
authority. A failed, incomplete, malformed, truncated, or over-budget response
keeps the intent at its FIFO head for a bounded safe-read retry and prevents
both the moderation preflight and add POST.

If the complete fresh result already contains the target group, the FGA
database records terminal `added` from that observation and the worker sends no
write. If it does not, the worker proceeds to the mandatory fresh
`flickr.groups.getInfo`, which remains the immediately preceding Flickr
operation before any `flickr.groups.pools.add`. These reads are advisory rather
than atomic; Flickr code `3` still safely handles the race in which membership
appears before the add reaches Flickr.

## Does the plug-in ever communicate directly with Flickr?

Yes, but only for the large image upload. The FGA API backend creates a fresh signed upload
envelope; Lightroom adds the rendered file and sends it directly to Flickr.
The FGA LrC plug-in does not receive the permanent Flickr secrets, and the FGA
API backend does not receive the image bytes. An FGA group-submission worker
later calls Flickr to add the photo to group pools.

That direct image POST is not covered by generic FGA API retry behavior. Once
the FGA LrC plug-in invokes `LrHttp.postMultipart`, a timeout or connection loss
cannot prove that zero bytes escaped, so the plug-in records
`upload_outcome_unknown` and requires reconciliation instead of replaying the
upload.

## Would a public, self-service FGA product keep this manual setup?

Probably not. Manual provisioning is a deliberate private single-user MVP
choice. A public product would need a separate onboarding decision, an
independently authenticated user session, and likely a properly designed
browser or device-authorization flow with current threat analysis.
