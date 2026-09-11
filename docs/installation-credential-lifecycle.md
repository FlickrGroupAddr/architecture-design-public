# Private installation credential lifecycle

Last updated: 2026-09-05

Status: Accepted private-MVP lifecycle under ADR 0019; exact unresolved FGA User
API routes remain explicit

## Purpose and authority boundary

This contract defines issuance, endpoint storage, authentication, rotation,
revocation, lost-workstation recovery, repair, and audit for the private MVP's
FGA installation credentials. It extends
[ADR 0006](decisions/0006-browser-free-private-installation.md), the
[Plugin Code User API decision](decisions/0040-expose-plugin-codes-as-user-resources.md), the
[authoritative clean-room interaction maps](decisions/0041-use-clean-room-authentication-tabs-as-interaction-authority.md),
the
[private transfer ceremony](private-install-credential-transfer.md), and the
[plug-in/service authentication contract](plugin-service-contract.md).

An installation credential is a high-entropy bearer authenticator for one FGA
LrC plug-in installation. Its internal class is `lrc_plugin`, and it authorizes
only the corresponding route/method allowlist. It is not administrator identity,
Flickr authority, a browser session,
a refresh token, a claim about the Lightroom Classic host, or proof that a
request came from an uncompromised workstation. Anyone who obtains its
plaintext can exercise its current server-side authority until revocation.

The FGA API backend authenticates every request from the credential's complete
value and current FGA database state. There is no positive authorization cache
that can outlive a request. The FGA LrC plug-in stores current and in-progress
rotation values only with documented `LrPasswords`; the FGA database stores
only their unsalted SHA2-256 digests and lifecycle metadata.

## Durable records and states

The FGA database separates the stable installation from credential versions.

`installations` contains the opaque installation ID, internal `fgaUserId`
ownership foreign key, immutable
server-assigned credential class, operator label, state, revision, creation and
revocation metadata, current credential-version ID, optional pending rotation-
version ID, advisory next-rotation date, and sanitized activity summary.
`active` and `revoked` are the only installation states. Unknown values fail
closed.

`installation_credential_versions` contains an opaque version ID, parent
installation ID, unique SHA2-256 digest, state, creation/activation/expiry/
replacement/revocation times, originating audit-event ID, and
sanitized reason class. It never contains plaintext. The exhaustive states are:

- `current`: the one version allowed on normal `lrc_plugin` routes;
- `pending_rotation`: a 15-minute candidate allowed only to read the safe
  current-installation resource until the administrator completes its approved
  rotation;
- `replaced`: a formerly current version retired by successful rotation;
- `revoked`: explicitly invalidated before replacement; and
- `expired_unactivated`: a pending candidate whose database-clock deadline
  elapsed before administrative completion.

An active installation has exactly one `current` version and at most one
unexpired `pending_rotation` version. A revoked installation has no usable
version. Database constraints enforce the parent/class relationship, unique
digest, allowed states, one-current/one-pending cardinality, monotonic version
ordinal, and consistency between installation pointers and version states.
Application validation is defense in depth, not a substitute for constraints.

Every security-state transition increments the installation revision. Unknown,
null, differently cased, future, or internally inconsistent installation,
class, or credential-version state returns the same `401 invalid_token` as any
other invalid credential and emits a sanitized integrity alert. It never falls
through to another authority.

## Initial issuance and endpoint storage

Initial issuance uses `POST /api/v001/plugin-codes`. It requires the exact
Google-authenticated FGA browser session, accepted ADR 0043's five-minute recent
Google reauthentication, CSRF and origin checks, the server-assigned
`lrc_plugin` class, and the
same-workstation transfer checklist. Under
[ADR 0044](decisions/0044-use-canonical-crockford-base32-plugin-codes.md), the
FGA API backend generates exactly 32 random octets and encodes them as one
64-character Plugin Code: 52 uppercase canonical Crockford Base32 symbols in 13
four-symbol groups separated by 12 ASCII hyphens. It then atomically commits:

- the active installation and its first `current` version;
- the credential's unsalted SHA2-256 digest;
- an advisory `rotationDueAt` 12 months after creation; and
- the successful Plugin Code audit and credential-lifecycle events.

The response displays plaintext once under the transfer contract. The browser
and FGA LrC plug-in show the same clear-text grouped value simultaneously for
side-by-side comparison before storage. Failed or ambiguous display/transfer
requires revocation and new issuance; no route recovers or redisplays the
value.

The FGA Plugin Code API derives `fgaUserId` only from the validated browser
session. The request cannot select an owner, and email is never an ownership
key. Initial issuance and revocation commit their successful `audit_events` row
in the same FGA database transaction as the installation change. A successful
`GET /api/v001/plugin-codes` appends its sanitized list-read event durably
before returning any bounded Plugin Code metadata.

The FGA LrC plug-in uses two fixed plug-in-scoped `LrPasswords` keys:

- `fga.installation.current` for the current credential; and
- `fga.installation.rotation_candidate` only while completing rotation.

The names contain no user, installation, catalog, machine, or credential
identifier. `LrPasswords.store` and `retrieve` use the FGA LrC plug-in ID and
the documented default salt. The FGA LrC plug-in treats nil and the empty string
as no credential. SDK 15.3 documents no deletion operation, so clearing a key
means storing an empty string and retrieving it to verify empty. The FGA LrC
plug-in never uses an undocumented delete symbol.

The credential is not copied to the Lightroom Classic catalog, ordinary
preferences, publish-service settings, recovery records, preset/export files,
logs, crash/diagnostic payloads, environment variables, or source code. Catalog
backup, catalog migration, plug-in reinstall, and workstation migration do not
count as credential transfer.

## Verification and ordinary use

On activation or after a disconnected start, the FGA LrC plug-in reads
`fga.installation.rotation_candidate` first. A nonempty candidate means an
incomplete rotation and enters the recovery path below; it must not silently
fall back to the old current value. Otherwise it retrieves the current key and
performs the fixed safe `GET /api/v001/installations/current` using the
credential only in the HTTPS `Authorization: Bearer` header, with no body or
query parameters.

The FGA API backend first requires the exact canonical spelling defined by ADR
0044, with no case folding, aliases, trimming, hyphen repair, or re-encoding. It
then computes SHA2-256 over all 64 characters, including the hyphens, loads the
matching version, installation, class, and current revision from the FGA
database, and exhaustively authorizes the route/method. A current version
of an active `lrc_plugin` installation receives the `200 OK` minimal
current-installation representation with exact
`presentedCredentialState: "current"`. An unexpired pending candidate receives
the same shape with `presentedCredentialState: "pending_rotation"` only on this
resource. The response contains no replacement token, credential version ID,
class, digest, user/Flickr identity, or session. Every later request
independently repeats authentication.

Before a state-changing FGA LrC plug-in API transaction commits—especially
direct-upload authorization and group-intent admission—the FGA API backend rechecks
that exact credential version and installation revision in the authoritative
database transaction. Rotation or revocation that commits first defeats the
old request. A read response or external request already handed to a networking
stack cannot be recalled. A signed direct-upload envelope issued before
revocation remains usable until its short immutable expiry, and already
accepted group intents continue under their FGA user safety rules; the
administrative confirmation states both limitations.

Successful authentication may enqueue a coalesced, sanitized activity
observation outside the business transaction. At most one observation per
installation per 15 minutes advances approximate `lastAuthenticatedAt`; failure
to record it never changes authentication or a response. This logging-like
side effect does not change authorization/resource semantics of a safe GET.
The FGA User UI labels the time approximate and shows its observation
delay. Authentication failures feed bounded metrics and alerts, not an
attacker-amplified database audit event per request.

## Planned and incident-driven rotation

The private MVP schedules a planned rotation during the annual diligence run
and may rotate earlier after a non-compromise endpoint maintenance event or a
material credential-handling change. `rotationDueAt` is an operational
reminder, not automatic expiration: missing the date raises one deduplicated
warning but does not unexpectedly break an offline Lightroom installation.
Suspected disclosure or unexpected activity involving the current credential
is not a planned-rotation case; it uses server-first revocation and a new
installation identity as defined below. Uncertain cleanup of a still-pending
candidate cancels that candidate; if administrative completion may already have
made it current, Terry revokes the installation instead of guessing.

Rotation uses one current credential until the FGA LrC plug-in proves
possession of the candidate and Terry explicitly completes the change in the
authenticated FGA User UI. There is no interval with two credentials
authorized for normal routes.

### Create one candidate

ADR 0040 leaves the exact FGA User API route for creating a rotation candidate
unresolved. That eventual operation requires recent authentication,
CSRF/origin checks, a strong current-representation validator, and an active
installation with no pending candidate. The FGA API backend generates a
new 256-bit credential, stores one `pending_rotation` digest with a database-
clock expiry 15 minutes later, updates the installation pointer/revision, and
commits the administrative audit/lifecycle event in one transaction. It returns
the candidate plaintext exactly once through the same transfer ceremony.

The candidate has exactly one authority: read
`GET /api/v001/installations/current`, whose response identifies the active
installation plus `pending_rotation` presented-credential state. It receives
`403 insufficient_scope` on every ordinary FGA LrC plug-in API route and cannot
authenticate to
administrative routes. Creating another candidate while one is pending returns `409 Conflict`;
Terry must cancel or let the exact candidate expire first.

### Verify, administratively complete, and promote locally

The FGA LrC plug-in blocks new ordinary FGA API operations for the short local
rotation window but does not cancel already accepted hosted work. It stores the
candidate in `fga.installation.rotation_candidate`, retrieves it exactly, clears
the transient FGA LrC plug-in field, and reads the current-installation resource
with the candidate. Only `200`, the expected installation ID, exact active
state, and `presentedCredentialState: "pending_rotation"` establish that the
transferred value is the live candidate. Once the candidate-key round trip
succeeds, Terry performs the transfer ceremony's
clipboard/view cleanup even if the later administrative result is lost; all
recovery reads the candidate only from `LrPasswords` and never redisplays it.

The FGA LrC plug-in displays **Candidate verified—complete rotation in FGA
administration** with no secret or version identifier. Terry returns to the
same recent-authenticated FGA browser session, reviews the exact installation
label, old/current and pending opaque version IDs, and invokes

the still-unresolved FGA User API completion operation with a strong current-
representation validator and an explicit confirmation that the FGA LrC plug-in
showed the verified state. In one FGA database transaction, the FGA API backend locks
the installation and both versions, requires the candidate to be unexpired
`pending_rotation` for that exact parent/revision, activates it as `current`,
changes the prior current version to `replaced`, updates the pointers/revision
and next annual due date, and appends the administrative/lifecycle events.
A repeated exact request for the recorded from-revision returns the same
successful no-op outcome; another stale revision returns `409 Conflict`.

The FGA LrC plug-in then invokes **Finish local rotation**, repeats the safe
current-installation read with the candidate, and requires the expected
installation ID plus `presentedCredentialState: "current"`. It stores the
candidate under
`fga.installation.current`, retrieves it and requires an exact match, then
stores empty under `fga.installation.rotation_candidate` and verifies that key
is empty. Only then does it re-enable ordinary operations. `LrPasswords` has no
rename/transaction primitive, so the candidate key is the crash-recovery
anchor: it is never cleared before the current-key round trip succeeds.

If the completion response, browser, or FGA LrC plug-in process is
lost, both local keys remain and the administrative detail is authoritative. On restart
or **Resume credential rotation**, the FGA LrC plug-in checks the candidate
first:
`pending_rotation` tells Terry to complete or cancel in administration;
`current` completes the local key move; `401 invalid_token` requires an
administrative refresh to distinguish expiry/cancellation/revocation. It never
restores ordinary use of the old local value merely because that value remains
readable while a candidate key is nonempty.

### Cancel or expire an uncommitted candidate

ADR 0040 also leaves the exact FGA User API cancellation route unresolved. The
eventual operation requires recent authentication and a strong current-
representation validator. It atomically changes
only an uncommitted pending version to `revoked`, clears the pending pointer,
increments the installation revision, and appends audit/lifecycle events. The
prior current credential remains unchanged. A database-clock expiry performs
the corresponding `expired_unactivated` transition through an idempotent
bounded cleanup worker.

Completion, cancellation, installation revocation, and expiry serialize on the
installation row. If completion wins, cancellation sees a current version and
returns `409`; Terry can revoke the installation if the completed rotation was
not intended. If revocation wins, it invalidates current and pending versions
and completion fails. No race can leave two normal-route credentials current.

After administrative detail confirms `revoked` or `expired_unactivated` for the
candidate and the same prior version remains `current`, the FGA LrC plug-in may
offer **Discard failed rotation**. That explicit action stores/retrieves empty
under the candidate key, reads the current-installation resource with the
retained current key, and requires the expected installation ID plus
`presentedCredentialState: "current"` before resuming ordinary work. It never
infers safe fallback from a candidate `401` alone.

## Revocation

`PATCH /api/v001/plugin-codes/{pluginCodeId}` requires recent authentication,
CSRF/origin checks, a strong `If-Match`, and exactly
`Content-Type: application/merge-patch+json` with body `{"state":"revoked"}`.
The `pluginCodeId` is the non-secret selector for the underlying installation;
it is never the Plugin Code, a prefix, or its digest. In one database
transaction the operation changes the
installation to `revoked`, revokes every current or pending credential version,
clears both pointers, increments the revision, and appends administrative and
credential-lifecycle events. A repeated exact request for the recorded
already-revoked representation returns the same successful no-op outcome. A
failed validator returns `412 Precondition Failed`; the FGA User UI refreshes
the record before deciding whether another action remains. Revocation never
deletes the identity or history.

Every subsequent request using any version returns nonspecific `401
invalid_token`. The FGA User UI does not expose a grace
period, undo, plaintext recovery, force-enable, or direct state editor. To
restore a deliberately revoked workstation, Terry creates a new installation
identity and credential through the original issuance ceremony. Reusing the old
installation ID or digest is prohibited.

Server revocation is authoritative and happens before any attempted local
cleanup. When the workstation remains trusted and available, the FGA LrC
plug-in stores empty and verifies empty under both fixed `LrPasswords` keys and
clears its connected state. The FGA User UI reports
`serverRevocationState=revoked` separately from
`endpointSecretRemovalState=owner_action_required` or a later sanitized
endpoint-removal observation reported by the FGA LrC plug-in. It never claims
remote deletion from a lost or compromised workstation.

Revocation prevents new API transaction commits under the recheck above. It
does not recall already returned responses, expire a previously issued upload
envelope early, cancel durable group intents, erase upload bindings or result
history, clear Flickr write gates, or remove permanent photo/group submission
blocks.

## Lost workstation, compromise, and repair

### Lost, stolen, or untrusted workstation

From a separate trusted administrative device, Terry immediately revokes the
entire installation identity. The lost device is not expected to cooperate and
no component claims its `LrPasswords` value was erased. After endpoint/account
incident steps are complete, Terry creates a new installation identity on the
replacement workstation and uses the private transfer ceremony. A copied
Lightroom catalog does not carry or authorize the old credential.

If a lost workstation returns, its revoked credential stays invalid. Terry
clears both local keys before any new provisioning, or treats the endpoint as
untrusted and rebuilds it. The server never reactivates the old identity.

### Suspected credential disclosure on an available workstation

Terry revokes server authority first from a separate clean browser, then clears
both keys and remediates the endpoint. Rotation is appropriate only when the
current credential is not suspected and the purpose is planned replacement.
Suspected theft uses revocation plus a new installation so an attacker cannot
race the normal overlap window.

### Ordinary `401` or broken local storage

The FGA LrC plug-in clears its connected state but does not guess why
authentication failed. Terry uses the administrative inventory to distinguish active,
rotation-pending, replaced, and revoked non-secret states.

- A nonempty candidate key resumes the candidate current-installation read and
  the administrative complete/cancel path.
- A candidate `401` requires administrative state review; only confirmed
  cancelled/expired candidate plus unchanged current state permits explicit
  **Discard failed rotation** and current-key verification.
- An active current server version with an absent/corrupt local value is repaired
  through an administratively created rotation candidate; the old plaintext is
  never redisplayed.
- A revoked installation receives a wholly new installation identity.
- A failing or inconsistent `LrPasswords` store must be repaired before any
  credential is reissued; ordinary preferences/files are not a fallback.
- A transient FGA API backend failure retains the one credential only in
  `LrPasswords` and retries the safe check later.

If the administrative database/audit state is inconsistent, issuance,
rotation, and revocation fail closed and page one deduplicated integrity alert.
Direct database repair is not an administrator UI feature; an approved migration
or operator runbook must preserve lifecycle events and least privilege.

## Audit, inventory, and retention

Administrative creation, rotation start/complete/cancel, revocation, and
inventory reads use the append-only administrative audit contract. A separate append-only
`installation_credential_events` relation records server-generated event ID,
database time, installation/version IDs, action, old/new sanitized states,
originating administrator audit ID when present, administrative actor for
rotation completion, request correlation ID, and sanitized outcome/reason.

Neither event stream contains credential plaintext/digest, Authorization
fields, request/response bodies, `LrPasswords` keys/values, source address,
catalog/photo/group data, or raw exceptions. A candidate installation read is
not mislabelled as an administrative completion. Audit-write failure refuses its
associated security-state mutation.

The administrative inventory exposes installation label/ID, class, state and
revision, current/pending version IDs and sanitized states, creation/activation/
replacement/revocation times, advisory rotation due/overdue state, approximate
last-authenticated time, and last lifecycle outcome. It does not expose a
secret, digest, URL, or enough provider detail to locate endpoint storage.

Credential and installation records are never hard-deleted by routine
retention. They retain the minimum history needed to interpret audit and
accepted work. Installation revocation or rotation does not delete durable FGA
user intents, uploads, reconciliation, gates, or moderator-protection blocks.

## Conformance requirements

Before private-MVP deployment, tests against production migrations and
authentication code must prove:

- initial issue commits one current version and one audit/lifecycle outcome and
  returns plaintext once;
- all null/unknown/class/version/state and route/method combinations fail
  closed with the standard Bearer response;
- a pending candidate can read only the safe current-installation resource and
  returns the exact `pending_rotation` presented-credential state;
- administrative completion atomically creates exactly one current version,
  replaces exactly one old version, and is idempotent after a lost response;
- premature administrative completion cannot leave two current versions, and a
  new candidate can repair the unavailable current plaintext without
  redisplay;
- crash/failure before candidate store, after candidate store, before/after
  completion, during current-key store, and before candidate-key clearing follows
  the documented recovery with no plaintext redisplay;
- complete/cancel/expiry/revoke races end with database constraints intact and at
  most one current plus one pending version;
- every state-changing API transaction rechecks credential version/revision so
  a prior rotation/revocation defeats stale authority;
- initial, current, pending, replaced, expired, and revoked credentials have the
  exact route authority and non-oracular errors specified here;
- lost-workstation revocation needs no endpoint response and no UI claims local
  erasure;
- clearing uses only documented `LrPasswords.store`/`retrieve`, and a canary
  appears in none of the prohibited endpoint/server artifacts; and
- audit failure refuses issue/rotation/revocation, while coalesced activity
  observation failure does not change authentication.

One controlled annual diligence run performs a complete planned rotation,
injects one lost administrative-completion response, restarts Lightroom Classic
between server completion and local current-key promotion, and proves recovery
without enabling the old version or exposing either plaintext in retained
evidence.

## References

- [OWASP Secrets Management Cheat Sheet: secret lifecycle](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html#27-secret-lifecycle)
- [RFC 6750 — Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750)
- [Adobe Lightroom SDK research: `LrPasswords`](research/lightroom-classic.md#upload-and-credential-primitives)
