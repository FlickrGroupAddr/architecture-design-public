# OAuth grant, administrative-session, and account lifecycle

Last updated: 2026-09-11

Status: Accepted lifecycle semantics under ADRs 0017, 0039, 0043, and the scoped
private replacement amendment ADR 0052; the
private MVP remains single-user and does not expose public enrollment or
self-service account deletion

## Purpose and scope

This contract defines how the private deployment links, replaces, disconnects,
and repairs Terry's Flickr OAuth 1.0a grant; how Terry can inventory and revoke
FGA administrative sessions; which safety records survive those actions; and
what the UI may claim. It extends the
[administrative control-plane contract](administrative-control-plane-contract.md)
and [ADR 0013](decisions/0013-durable-flickr-write-circuit-breaker.md).

The Flickr grant and an FGA administrative session are separate authorities.
Disconnecting Flickr does not terminate Terry's FGA administrative session,
and revoking an FGA administrative session does not revoke Flickr permission.
An FGA installation credential is a third authority with its own revocation
lifecycle. No component may infer one revocation from another.

As checked on 2026-08-26, Flickr's documented OAuth interface provides request-token,
authorization, access-token, and token-check operations. Its documented API
method index does not provide an application-side access-token revocation
method. Flickr instead directs the account owner to remove an application's
permission under **Sharing & Extending** in Flickr account settings. The FGA
administrative control plane therefore distinguishes a local disconnect from
confirmed Flickr-side removal and never screen-scrapes Flickr to bridge that
gap.

## Durable Flickr-link state

The FGA database stores one link record for the private deployment. It contains
the internal `fgaUserId` ownership foreign key, the immutable expected Flickr
owner NSID, current state,
monotonically increasing revision, permission class, active managed-secret
reference and version when one exists, link/replacement/disconnect times,
sanitized verification result, and opaque audit correlation IDs. It never
contains the OAuth token or token secret.

The exhaustive states are:

- `unlinked`: no grant has ever been activated;
- `linked`: exactly one managed-secret generation is active and was verified
  for the expected owner NSID and at least `write` permission;
- `relink_required`: no new ordinary Flickr operation may start because Flickr
  definitively rejected the active grant or its permission;
- `disconnecting`: the database has removed all active authority, but deletion
  of one or more inactive managed-secret versions is still pending; and
- `disconnected`: no managed-secret version remains usable by an FGA hosted
  component.

Unknown stored values fail closed as no Flickr authority. The FGA API backend,
FGA refresh worker, and FGA group-submission worker may obtain a secret only by
resolving the exact active reference from a `linked` row at its current
revision. A historical secret reference, an inactive version, a cached token,
or a secret-store object discovered by name is not authority. In the scoped
ADR 0052 native candidate, the selected generation is carried inside the
managed-secret bundle and must match the current database authority; a durable
replacement pause prevents new ordinary operations even if values still match.
Secret values
remain in request-local memory only for the minimum signed Flickr operation and
are never logged, traced, returned to a browser, or copied into the FGA
database.

Every state mutation and its append-only administrative audit event commit in
one FGA database transaction. Requests carry `expectedRevision`; a stale
request returns `409 Conflict` and performs no mutation. The link revision is
also captured when an operation is authorized. A worker rechecks the current
link and both applicable write gates immediately before its durable
`dispatch_started` transition. A disconnect or replacement can prevent a new
start but cannot recall bytes already handed to a networking stack.

## Link and relink

Only a recently reauthenticated administrator can start Flickr authorization.
The FGA API backend creates the five-minute, single-use OAuth transaction
defined by the administrative control-plane contract. The callback consumes
the exact request token and verifier, exchanges them once, and verifies the
returned owner NSID and permission through a fresh documented
`flickr.auth.oauth.checkToken` call.

The owner NSID **MUST** equal the deployment's immutable expected Flickr owner
NSID, and the permission **MUST** be at least `write`. A different Flickr
account is not a relink target: the callback is rejected, its staged secret is
deleted, the prior link state is unchanged, and the event is audited without
exposing either token. Moving the deployment to another Flickr owner is a
separate data-migration and safety decision, not an OAuth repair shortcut.

### Provider-versioned replacement

For the provider-versioned path, after successful verification, replacement
uses this order:

1. Store the new token and token secret under one new versioned managed-secret
   object that is not yet referenced by the FGA database.
2. In one compare-and-set database transaction, activate that exact reference,
   increment the link revision, preserve the immutable owner NSID, and append
   the successful audit event.
3. Make the prior version inactive and delete it. If deletion is temporarily
   unavailable, queue bounded cleanup and alert; the prior reference is not
   authoritative and no FGA hosted component may resolve it.

If staging fails, nothing changes. If the database transaction fails, the old
link remains authoritative and the unreferenced staged version is deleted or
queued for deletion. The callback never activates two grants and never returns
a secret to the browser.

### Paused native replacement for the private deployment

Accepted [ADR 0052](decisions/0052-evaluate-paused-native-credential-replacement.md) authorizes evaluating
one fixed managed-secret bundle with the token, token secret, and an opaque
application generation. Each distinct pair gets a new generation. A provider
VersionId and retention of the old pair for rollback are not required for this
candidate. The provider-versioned sequence above remains a fallback option.

Before changing the native value, durably pause new ordinary Flickr operations
and fence/serialize lifecycle changes. This pause must cover reads and signing
as well as writes; pausing only a process or only the write gate is insufficient.
Only the authorized replacement validation may use a candidate grant during
that pause. Check the fixed owner and required permission, and commit the
matching active generation and its audit event with a compare-and-set. Consumers
reject malformed or unavailable values, generation mismatches, stale authority,
and the replacement pause. Retain the existing final dispatch-authority check.

An uncertain store write, delayed response, or failed/lost database activation
must remain paused for reconciliation, repair, or another relink. This path
does not promise that the old credential can be recovered. Store and database
updates are never one transaction. Successful PATCH acknowledgement alone
proves neither global propagation nor permission to resume. In-flight Flickr
requests keep their original result/ambiguity handling; no credential change
permits replay. Stale errors cannot disable a newer generation.

Disconnect and cleanup must be serialized/fenced with replacement. A cleanup
for an old generation cannot delete an active successor from the shared slot.
Until native retirement/deletion is confirmed, retain the existing truthful
pending-cleanup behavior. A denied or uncertain provider operation is not
removal. Prove delayed/reordered mutations and recovery before adoption.

Implementation #0009 owns the bounded synthetic proof, durable schema, and
UI/wire reconciliation. These requirements accept the pause/repair tradeoff;
they do not add an undocumented public state/field or claim a selected native
production adapter. Credentials remain outside the database, browser, and logs.

### Common post-replacement behavior

Activating a repaired grant does not automatically resume a user or deployment
write gate. The UI shows the new link revision and the still-paused gate. Terry
must use ADR 0013's separate recent-authentication, fresh token-check, and
compare-and-set resume operation. This keeps credential replacement from
silently overriding a pause caused by a different fault.

Queued group intents, upload bindings, permanent photo/group suppression
records, delivery-ambiguity records, and audit history remain attached to the
same FGA user and expected Flickr owner NSID. Relinking neither requeues nor
terminalizes an intent.

## Definitive external revocation or permission loss

A complete, parseable Flickr application result `98` or `99` pauses the linked
user's write gate under ADR 0013. In the same recovery transaction, the FGA
database changes a still-current `linked` revision to `relink_required`,
removes its active secret authority, and appends the sanitized evidence. A
concurrent replacement defeats that compare-and-set so an old in-flight result
cannot disable the new revision.

The inactive managed-secret version is then deleted. Deletion failure leaves
no active database reference, raises a deduplicated operational alert, and is
retried by bounded cleanup. The FGA API backend reports `relink_required`
without claiming why Flickr withdrew permission beyond the documented result.
Transient transport failures, malformed responses, and ordinary Flickr
temporary codes do not prove revocation and do not mutate the link state.

An operation whose dispatch already started retains its normal durable result
or ambiguity handling. Revocation is not evidence that zero request bytes left
an FGA hosted component. In particular, it cannot clear the permanent
submission block required after an ambiguous group-add dispatch.

## Local disconnect and Flickr-side removal

`POST /api/v001/admin/flickr-connection/disconnection` is an explicit,
recent-authentication operation with CSRF and exact-origin protection. The
request contains `expectedRevision` and the exact expected Flickr owner NSID as
a confirmation value. Before submission, the UI shows:

- the owner NSID and sanitized Flickr display name;
- whether the link and user write gate are active;
- counts of queued intents, delivery-uncertain intents, and permanent
  photo/group blocks;
- that disconnect stops future Flickr reads and writes but cannot recall an
  already-dispatched request;
- that queued and safety records are retained; and
- that a separate Flickr account-settings action is required to remove the
  application permission at Flickr.

The mutation first pauses the user write gate, removes the active secret
authority, changes the link to `disconnecting`, increments both affected
revisions as applicable, invalidates every outstanding Flickr OAuth
transaction, and appends the audit events in one FGA database transaction.
From that commit onward, no FGA hosted component may start an authenticated
Flickr read, upload authorization, upload signing operation, or group write for
that user. Existing installation credentials may authenticate only to obtain
sanitized disconnected/relink-required status; they cannot revive Flickr
authority.

The FGA API backend then deletes every managed-secret version belonging to the
inactive grant. After confirmed deletion, a compare-and-set transaction moves
the row to `disconnected`. If deletion fails, `disconnecting` remains a
fail-closed state, cleanup retries with bounded backoff, and the UI shows
“locally disconnected; credential deletion pending” plus a correlation ID. It
does not show “disconnected” or “revoked” as though both systems completed.

Because Flickr documents owner-driven removal rather than an application-side
revocation method, the FGA administrative control plane then links to Flickr's
Sharing & Extending settings and instructs Terry to use **Remove Permission**.
The FGA administrative control plane does not proxy credentials to that page,
inspect Terry's Flickr browser session, scrape the page, or claim success. Its
final confirmation uses
these independent fields:

- `localCredentialState`: `deleted` or `deletion_pending`;
- `fgaOperationState`: `stopped`; and
- `flickrPermissionState`: `owner_action_required` or, if a future documented
  Flickr contract supplies proof, `confirmed_removed` with observation time.

Navigating to Flickr or Terry's later assertion alone does not produce
`confirmed_removed`. Adding a future application-side revocation call requires
a new documented Flickr contract, tests, and an update to this lifecycle; it
must not be inferred from a successful local deletion.

Disconnect is idempotent. Repeating it against the current disconnected
revision performs no destructive rewrite and records at most a sanitized no-op
audit outcome. Relink after disconnect follows the ordinary link flow, must
return the same expected owner NSID, and still does not remove retained safety
history.

## Administrative-session inventory and revocation

The FGA administrative control plane exposes the bounded,
reverse-chronological inventory specified by the accepted
[browser-session lifecycle](browser-session-lifecycle.md#concurrent-sessions-and-revocation).
Each row shows only an opaque session ID and revision, creation, recent Google
reauthentication, last-activity, expiry and optional revocation times, derived
state, and whether it is current. It never shows the cookie, digest, CSRF token,
Google tokens, IP address, limiter key, raw user agent, or browser fingerprint.

The allowlisted routes are:

| Operation | Method and path | Required behavior |
| --- | --- | --- |
| List sessions | `GET /api/v001/admin/sessions` | Bounded opaque-cursor pages for the exact administrator principal |
| Revoke another session | `POST /api/v001/admin/sessions/{sessionId}/revocation` | Require recent authentication and `expectedRevision`; idempotently revoke only that matching session |
| Revoke all other sessions | `POST /api/v001/admin/sessions/revoke-others` | Require recent authentication, reviewed expected count, and a principal-level session-set revision |
| Logout current session | `POST /api/v001/admin/session/logout` | Idempotently revoke the current server-side session and its audit event before returning the cookie-expiration response |

The per-session route refuses to target the current session; Terry uses logout
for that purpose. `revoke-others` preserves exactly the request's current
session. Both routes require accepted ADR 0043's five-minute, transaction-bound
recent Google reauthentication. It proves a newly issued nonce-bound assertion
for the same Google Account and deliberately does not claim a fresh factor or
phishing-resistant challenge. The database transaction commits revocations and
their audit events together. An unknown opaque ID returns the same
non-oracular result as an already revoked session. A stale session-set revision
returns `409 Conflict` so a newly created session is not silently omitted.

Revocation takes effect at the FGA API backend on the next request and survives
process restarts. It cannot recall a response already returned. It does not log
Terry out of Google, revoke a Google Account session, disconnect the
Flickr grant, or revoke an installation credential; the confirmation says so.
If the FGA database is unavailable, no revocation is reported as successful.

### Logout outcome and recovery

Logout is one explicit user-initiated `POST`, not a browser unload hook,
`sendBeacon`, duplicated best-effort requests, or deletion of client display
state. The FGA administrative control plane serializes unsafe operations and
disables **Sign out** while another state-changing request is in flight; logout
does not pretend to cancel a mutation the server may already have committed.
It applies this order:

1. Require the exact configured FGA origin. For a currently active session,
   also require the exact session-bound CSRF token before any mutation or
   cookie change.
2. Lock the row selected by the digest of the exact presented cookie and, in
   one FGA database transaction, mark it revoked and append the successful
   logout audit event. An audit failure rolls back the revocation.
3. Only after that commit, return `204 No Content`, `Cache-Control: no-store`,
   and this expiration header:

   ```http
   Set-Cookie: __Host-fga_admin=; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Secure; HttpOnly; SameSite=Strict
   ```

The `204` means the exact presented session is durably revoked or was already
expired, revoked, unknown, or absent, and the response instructed the browser
to erase the matching host-only cookie. A same-origin repeat with the old
cookie and retained CSRF token is idempotent. A same-origin request with no
valid session also receives the same `204` and expiration header, which avoids
an existence oracle and lets a retry converge after the first response was
lost. The route is handled before the generic administrative `401` response;
it never redirects to login.

A failed exact-origin check returns `403` and does not expire the cookie. A
known active session with missing or invalid CSRF also returns `403` without
revocation or cookie expiration. A database or audit failure known to have
rolled back returns `503 logout_unavailable`; an indeterminate commit outcome
returns `503 logout_outcome_unknown`. Neither `503` response contains
`Set-Cookie`. Both include only the normal sanitized correlation ID. Keeping
the HttpOnly cookie is deliberate: it preserves the authority needed to repeat
the one idempotent logout operation and determine the durable result. No error
response says **signed out**.

The FGA administrative control plane uses this client state machine:

| Client state | Trigger | Required presentation and actions |
| --- | --- | --- |
| `authenticated` | Normal administrative use | Administrative views and allowlisted actions are available |
| `logout_submitting` | Terry selects **Sign out** | Abort in-flight reads, stop polling, remove administrative data from the rendered view and in-memory view model, disable every administrative mutation, and send exactly one logout POST |
| `signed_out_confirmed` | A complete valid `204` response arrives | Replace browser history with the signed-out landing view; say **Signed out of this FGA administrative session** and separately state that the Google Account session, Flickr grant, and installation credentials were not revoked |
| `logout_unconfirmed` | Network failure, timeout, malformed response, `403`, `5xx`, or another non-`204` result | Say **Sign-out unconfirmed. This browser may still hold an active FGA administrative session.** Show the correlation ID when one exists; offer only **Retry sign out** and **Close this private window** guidance |

Clearing the rendered view is privacy hygiene, not authentication state. Client
code cannot read or delete the `HttpOnly` cookie and therefore cannot convert a
failed request into local proof of sign-out. It retains only the in-memory CSRF
value needed by **Retry sign out**; it does not restore the scrubbed
administrative view or issue another mutation. Reloading performs the ordinary
server-owned session check and never treats a client flag as revocation.

Closing every window in the private-browsing context disposes that browser
context's local cookie state, but it still does not prove that the FGA database
row was revoked. The recovery copy says that the server session may remain
active until its non-sliding 24-hour absolute expiry. Terry may sign
in through a separate private context, inspect the bounded session inventory,
and revoke the orphaned session there. That inventory shows creation/activity
times and opaque IDs without exposing the old cookie.

The retry converges across the important ambiguous boundaries: if the first
transaction never committed, the repeat revokes it; if it committed but the
response was lost, the repeat observes the retained revoked row and returns the
same `204`; if the browser received and applied the expiration header before
client code observed failure, the cookie-free repeat also returns `204`.

Production-adapter and UI tests must prove at least:

- active success commits the revocation and successful audit event before the
  `204`/expiration header, and the next authenticated request fails;
- audit failure, database rollback, exact-origin failure, and active-session
  CSRF failure do not revoke or expire the cookie and never render success;
- crash/connection injection before commit, after commit, after response
  headers, and before the client consumes the response converges through the
  same idempotent retry;
- absent, malformed, expired, and already-revoked cookies receive the same
  no-store `204`/expiration response without a session-existence oracle;
- the client scrubs administrative state and stops work on the initial gesture,
  while every non-`204` result renders the exact unconfirmed meaning and only
  the two recovery choices; and
- closing a private window, clearing a view model, Google sign-out, Flickr
  disconnect, and installation revocation are never reported as the server
  logout transaction.

## Account deletion and retained safety state

The private MVP has no FGA self-signup account and exposes no in-application
`DELETE account` route. The one FGA user is deployment-owned and pinned to one
Flickr owner NSID. Treating ordinary disconnect as deletion would either erase
moderator-protection history or leave an ambiguous partly deleted identity, so
the conventional private-deployment boundary is explicit disconnect plus
deployment decommissioning.

Disconnect, relink, installation revocation, administrative-session
revocation, and Google Account recovery **MUST NOT** delete or weaken:

- permanent exact `(Flickr photo ID, Flickr group ID)` submission blocks;
- `dispatch_started`, delivery-uncertain, and moderator-queue evidence;
- group-intent order, terminal results, and attempt history;
- upload bindings and reconciliation decisions;
- Flickr write-gate events and revisions; or
- administrative/security audit events.

Those records are necessary to prevent a later relink from presenting an old
submission as new. They remain even if the current grant is locally deleted.
They contain identifiers and minimized evidence, not OAuth secrets.

Whole-deployment decommissioning is an operator runbook action outside the web
control plane. It must first stop admissions and workers, locally disconnect
and remove Flickr permission, revoke installation and administrative sessions,
delete managed secrets, take or deliberately destroy final backups under the
accepted retention policy, and verify provider resource removal. Destruction
of the FGA database also destroys the only durable moderator-protection memory;
the confirmation must state that the erased deployment cannot later resume
automated submissions as though it still knew prior blocks. Restoring service
requires restoring compatible safety history or an explicit new architecture
decision, not merely relinking OAuth.

Public or multi-user operation remains prohibited. Before such a launch, a
separate accepted privacy/abuse design must define self-service account
deletion, legal retention, re-registration resistance, safety-record
pseudonymization or deletion, backups, appeals, and the precise point at which
the official FGA deployment relinquishes the ability to prevent resubmission.
This private lifecycle does not silently answer those materially different
questions.

## Failure and conformance requirements

- Secret-store, database, audit, expected-revision, recent-authentication,
  exact-origin, or CSRF failure is fail-closed. No response claims a completed
  disconnect, relink, or revocation unless its authoritative state committed.
- In the provider-versioned path, a staged but unreferenced secret and an
  inactive old secret are deleted by idempotent bounded cleanup. For ADR 0052's
  shared native slot, cleanup must prove it cannot remove an active successor
  and report removal only after native confirmation. Neither path reactivates
  inactive material; pending cleanup remains explicit.
- Read models never report `linked` unless the active database reference can be
  resolved and its stored class is known. They never return secret identifiers
  that help locate a provider object.
- Concurrency tests cover replace-versus-disconnect, old-result-versus-new-link,
  disconnect-versus-dispatch, revoke-others-versus-new-session, and cleanup
  retries. The losing compare-and-set performs no mutation.
- Integration tests prove that `disconnecting`, `disconnected`, and
  `relink_required` all prevent a new Flickr operation, while already-dispatched
  operations retain ordinary ambiguity handling.
- UI tests require the three independent disconnect result fields and forbid
  “Flickr permission revoked” unless supported by documented remote proof.
- Retention tests prove every permanent submission block and ambiguity marker
  survives disconnect and same-owner relink.

The ADR 0052 native proof must additionally cover durable pause across restart,
generation mismatch and unavailable values, store propagation and delayed writes,
failed/lost activation, competing replacement and disconnect/cleanup, and safe
repair without old-grant rollback or Flickr-write replay. A local state model
does not substitute for actual native binding and management evidence.

## Official Flickr references

- [Flickr OAuth 1.0a flow](https://www.flickr.com/services/api/auth.oauth.html)
- [Flickr API method index](https://www.flickr.com/services/api/)
- [Flickr privacy policy: remove third-party permission under Sharing &
  Extending](https://www.flickr.com/help/privacy)
