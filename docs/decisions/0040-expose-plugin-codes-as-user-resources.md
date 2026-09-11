# ADR 0040: Expose Plugin Codes as user-owned resources

Date: 2026-08-28

Authoritative interaction-map designation accepted: 2026-08-28

Canonical creation representation amendment accepted: 2026-09-03

Status: Accepted

## Context

The normal FGA user experience needs to list, create, and revoke the bearer
credentials used by the user's FGA LrC plug-in installations. Earlier drafts
placed those operations under `/api/v001/admin/installations` and called the
browser surface an administrative UI. That language incorrectly suggests a
separate FGA-operator surface instead of the product's standard happy path.

`Plugin Code` is the user-facing name for the complete opaque 256-bit FGA
installation credential accepted by ADR 0006. It is not an OAuth device code,
short pairing code, database digest, or public identifier. The FGA User UI
needs a separate non-secret identifier with which to select one Plugin Code
record without redisplaying or transmitting its plaintext.

## Decision

The FGA User UI uses this resource-oriented interface:

```http
GET   /api/v001/plugin-codes
POST  /api/v001/plugin-codes
PATCH /api/v001/plugin-codes/{pluginCodeId}
```

Under [ADR 0041](0041-use-clean-room-authentication-tabs-as-interaction-authority.md),
tab 2 of the
[clean-room authentication diagram](../diagrams/clean-room-authentication-legal.drawio)
is the authoritative happy-path interaction map for listing and creating a
Plugin Code and transferring it into the FGA LrC plug-in. Its numbered actors,
ordering, trust/persistence boundaries, and explicit security invariants
control. This ADR owns the detailed resource semantics, including the PATCH
revocation behavior that the tab labels but does not number.

The plural `plugin-codes` collection identifier is canonical for both the
collection and its selected members. These routes have no trailing slash.
This follows the conventional collection/member shape instead of changing the
noun to singular merely because one member is selected.

`pluginCodeId` is an opaque, non-secret public identifier. It is never the
Plugin Code, its prefix, or its `SHA2-256` digest.

Each Plugin Code record has an internal `fgaUserId` ownership foreign key. The
FGA Plugin Code API obtains that value only from the validated server-side FGA
browser session and applies it to every collection query, creation, and member
update. A request cannot supply or override `fgaUserId`. Google email is mutable
display metadata and is never a Plugin Code primary key, foreign key, ownership
selector, or authorization input.

`GET /api/v001/plugin-codes` returns only bounded display metadata whose
`fgaUserId` ownership key matches the authenticated FGA browser session:
`pluginCodeId`, non-secret installation label,
authoritative `state`, revision/validator, creation time, and approximate last
authenticated time. It never returns plaintext, a digest, credential class,
Google claims, or Flickr authority. The collection is paginated from its first
release with optional `page_size` and opaque `page_token` query parameters. The
default page size is 50 and the hard maximum is 100. Results use stable keyset
ordering by `createdAt` descending and then `pluginCodeId` descending. The
response contains `pluginCodes` and includes `nextPageToken` only when another
page exists. The token conveys continuation state only, is bound to the
session's `fgaUserId` and unchanged query, and never grants authority. The API
does not calculate or return a total count.

The FGA database treats `audit_events` as a first-class append-only relation,
not as ordinary process logging. Every Plugin Code collection read, creation,
and revocation attempt produces a sanitized event. A successful collection
read durably appends its event before the FGA Plugin Code API releases any
metadata; an audit-write failure returns no collection data. Creation and
revocation commit their domain change and successful audit event in the same
database transaction. Rejected and failed attempts append their outcome when
the database remains available.

Each event contains an opaque event ID, UTC event time, internal `fgaUserId`,
action, request and browser-session correlation IDs, outcome and sanitized
reason, and only the minimum non-secret target/result facts needed for review.
A list event may retain effective page size, returned count, and whether a next
page existed, but not the opaque page token or individual returned IDs. Audit
events never contain the FGA session token or digest, Plugin Code plaintext or
digest, Google assertion, CSRF value, Flickr credential, request body, or
arbitrary exception text. The same relation records `GET`, `POST`, and `PATCH`;
deploying a separate audit service or database is not part of the private MVP.

`POST /api/v001/plugin-codes` creates one internal installation identity and
its first `lrc_plugin` credential in the existing atomic database/audit
transaction. The FGA API backend generates the accepted 32 random octets and
encodes them exactly as ADR 0044 specifies, then stores only the complete
64-character credential's unsalted `SHA2-256` digest. A successful `201 Created`
response returns `schemaVersion`, `pluginCodeId`, and the canonical plaintext as
`pluginCode` exactly once with `Cache-Control: no-store`; no read, retry,
history, or support route can recover it. The request cannot supply the code,
credential class, user ID, authority, or expiry override.

`PATCH /api/v001/plugin-codes/{pluginCodeId}` applies a partial update to the
existing Plugin Code record. It requires a strong `If-Match` validator and
`Content-Type: application/merge-patch+json`. The only accepted patch document
is:

```json
{
  "state": "revoked"
}
```

The only user-controlled transition is `active` to `revoked`. The FGA API
backend atomically revokes the internal installation and all current or pending
credential versions, advances the revision, and appends the audit/lifecycle
events. It exposes no reactivation, arbitrary state editor, plaintext recovery,
or grace period. A patch against the current already-revoked representation is
a successful no-op; a failed `If-Match` returns `412 Precondition Failed` and
the FGA User UI refreshes before deciding whether another action remains.

All three routes require the authenticated FGA browser session. `POST` and
`PATCH` additionally require exact-origin, session-bound CSRF, and the proof
required by ADR 0043's recent Google reauthentication contract. They accept
neither an FGA LrC plug-in
Bearer credential nor a Google ID token as authority.

The following earlier route shapes are superseded for list, initial creation,
and revocation:

```text
/api/v001/admin/installations
/api/v001/admin/installations/{installationId}/revocation
```

The accepted credential-rotation state machine remains binding design, but
its FGA User API routes are unresolved. This decision does not force rotation
into the initial-creation `POST` or generic record `PATCH`, and it does not
change the FGA LrC plug-in's accepted
`GET /api/v001/installations/current` Bearer-authenticated resource.

## Consequences

- `FGA User UI` is the normal browser-product name. `Admin UI` is reserved for
  a future surface used by actual FGA operators or administrators.
- The UI may display a list of Plugin Code records, but it cannot list the
  Plugin Code plaintext values.
- Pagination exists before the collection ships, so a later accumulation of
  retained revoked records cannot turn one response into an unbounded result
  or force a behaviorally incompatible pagination retrofit.
- A successful Plugin Code read or mutation always has durable attributable
  audit evidence. The private MVP preserves atomic writes without introducing
  a distributed audit transaction or another deployed security boundary.
- `PATCH` accurately represents a partial state change. `PUT` would imply a
  complete replacement, `DELETE` would conceal the retained audit/state
  record, and a mutation query parameter would put update instructions in the
  target URI.
- JSON Merge Patch supplies a maintained standard media type without inventing
  an FGA patch dialect. The server still allowlists the single field, value,
  and forward-only transition.
- The internal architecture continues to use `installation`, `credential
  version`, and `FGA installation credential` where those exact trust and
  persistence boundaries matter.

## Alternatives considered

- **`PUT /api/v001/plugin-codes/{pluginCodeId}?status=revoked`:** rejected
  because PUT replaces the selected resource representation and the query is
  part of the target URI; neither expresses a one-field partial update cleanly.
- **`DELETE /api/v001/plugin-codes/{pluginCodeId}`:** rejected because FGA
  retains the record, terminal state, revisions, and audit history.
- **`POST .../revocation`:** rejected because revocation is modeled as a
  forward-only state change on the existing Plugin Code resource, not creation
  of a separately addressable revocation resource.
- **Short device code:** rejected by ADR 0018 for the private MVP; it would add
  a second bearer protocol and is not what `Plugin Code` means.

## References and design precedents

The FGA decisions and contracts below control FGA behavior. The RFCs define
the relevant Internet-standard method and media-type semantics. The approved
Google API Improvement Proposals are non-normative design precedent: they show
that plural collection identifiers and pagination-from-first-release are
established API conventions, but they do not govern FGA or override this ADR.

### FGA authority

- [ADR 0006 — Provision the private installation without a plug-in browser flow](0006-browser-free-private-installation.md)
- [Private installation credential transfer ceremony](../private-install-credential-transfer.md)
- [Private installation credential lifecycle](../installation-credential-lifecycle.md)
- [ADR 0041 — authoritative clean-room interaction maps](0041-use-clean-room-authentication-tabs-as-interaction-authority.md)

### Internet standards

- [RFC 9110 — PUT](https://www.rfc-editor.org/rfc/rfc9110.html#name-put)
- [RFC 5789 — PATCH](https://www.rfc-editor.org/rfc/rfc5789.html)
- [RFC 7396 — JSON Merge Patch](https://www.rfc-editor.org/rfc/rfc7396.html)

### Security logging guidance

- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

### Non-normative API design precedent

- [Google AIP-122 — Resource names](https://google.aip.dev/122)
- [Google AIP-158 — Pagination](https://google.aip.dev/158)
