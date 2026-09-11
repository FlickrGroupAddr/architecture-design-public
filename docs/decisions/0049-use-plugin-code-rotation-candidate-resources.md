# ADR 0049: Use Plugin Code rotation-candidate resources

Date: 2026-09-05

Status: Proposed

Review boundary: FGA localswim ticket #0097

## Context

Accepted ADR 0019 defines a complete revisioned credential-rotation lifecycle:
create one short-lived candidate, verify it through the current-installation
read, explicitly complete or cancel it, and retain all version history. ADR
0040 later moved initial issuance and revocation to user-owned Plugin Code
resources but deliberately left the replacement rotation routes unresolved.

Rotation cannot be deferred beyond the private MVP without amending ADR 0019's
predeployment conformance and annual-rotation requirements. Folding rotation
into the existing generic Plugin Code revocation PATCH would also make one
member resource appear to have two unrelated state machines.

The candidate is already a durable, independently identified credential-version
record. Representing it as a subordinate resource makes creation, selection,
retention, and its two allowed terminal outcomes explicit.

## Proposed decision

Add these authenticated FGA User API routes:

| Method | Path | Meaning |
| --- | --- | --- |
| `GET` | `/api/v001/plugin-codes/{pluginCodeId}` | Read one display-safe Plugin Code record, including current and pending version metadata |
| `POST` | `/api/v001/plugin-codes/{pluginCodeId}/rotation-candidates` | Create the only pending candidate and reveal its Plugin Code exactly once |
| `PATCH` | `/api/v001/plugin-codes/{pluginCodeId}/rotation-candidates/{rotationCandidateId}` | Move that retained candidate only to `current` (complete) or `revoked` (cancel) |

`pluginCodeId` selects the user-owned installation identity.
`rotationCandidateId` is the opaque, non-secret credential-version ID
returned at creation; it is never derived from the Plugin Code or its digest.
Every lookup also applies the FGA browser session's internal `fgaUserId`.

The detail GET returns the Plugin Code's label, installation state and revision,
strong entity tag, creation/revocation/activity metadata, advisory rotation due
state, current credential-version metadata, optional pending candidate
metadata, and last sanitized lifecycle outcome. It never returns plaintext,
digests, credential class, `LrPasswords` keys, or provider storage details.

Candidate creation requires recent Google reauthentication, exact origin,
session CSRF, `Content-Type: application/json`, and a strong `If-Match` for
the current Plugin Code representation. Its closed request repeats the transfer
precondition confirmations used for initial issuance. A successful `201`
returns only:

```json
{
  "schemaVersion": 1,
  "pluginCodeId": "opaque-plugin-code-id",
  "rotationCandidateId": "opaque-version-id",
  "pluginCode": "AAAA-...-AAA0",
  "expiresAt": "2026-09-06T00:15:00.000000Z"
}
```

The response and transfer view apply the same one-time, no-store, nonlogging,
five-minute browser-erasure, clipboard, comparison, and `LrPasswords`
ceremony as initial issuance. The database candidate lifetime remains 15
minutes.

Candidate PATCH requires the same authentication, origin, CSRF, recent-
authentication, content type, ownership, and strong parent-representation
`If-Match` checks. The only accepted documents are:

```json
{
  "schemaVersion": 1,
  "state": "current",
  "pluginValidationConfirmed": true
}
```

or:

```json
{
  "schemaVersion": 1,
  "state": "revoked"
}
```

The confirmation is Terry's explicit report that the FGA LrC plug-in displayed
the expected `pending_rotation` state; it is not cryptographic proof and does
not replace the server's exact parent, revision, state, and expiry checks.
Success returns the updated no-secret Plugin Code detail representation.

Completion, cancellation, expiry, and whole-installation revocation retain ADR
0019's serialization, compare-and-set, idempotency, and audit behavior. An
exact replay whose transition is already the recorded result may return that
same successful representation as permitted for an already-applied
state-changing request; every other failed validator or conflicting outcome
returns `412` or `409` without mutation.

No DELETE route exists because candidate, installation, and lifecycle records
are retained. No `complete`, `cancel`, `promote`, `rotate-now`, or
plaintext-recovery action route exists. The existing
`PATCH /api/v001/plugin-codes/{pluginCodeId}` remains revocation-only.

## Consequences

- The URI hierarchy mirrors the durable installation/version relationship.
- One PATCH schema exposes exactly the two candidate outcomes while preserving
  history.
- A normal detail GET supplies the validator and recovery state needed after a
  lost response.
- The FGA User UI cannot broaden a pending candidate by changing a generic
  installation state.
- The private-MVP API gains three routes, but avoids one route per lifecycle
  verb and avoids pretending that DELETE removes retained security history.

## Alternatives considered

- **Defer rotation until after private MVP:** rejected because it contradicts
  accepted ADR 0019's release and annual-rotation gates.
- **Use action routes for start, complete, and cancel:** rejected because the
  candidate is already a durable resource with a small explicit state machine.
- **Use DELETE for cancellation:** rejected because cancellation retains the
  candidate and its security history.
- **Extend the top-level Plugin Code PATCH:** rejected because revoking an
  installation and transitioning one version are distinct resources and
  invariants.
- **Use the secret value or digest as selector:** rejected because neither is a
  public resource identifier.

## Detailed contract

Upon acceptance, the installation credential lifecycle, private transfer
contract, administrative allowlist, and OpenAPI projection must add these exact
routes and schemas in one change.

