# Private-MVP OpenAPI closure review

Date: 2026-09-05

Status: Complete evidence and recommendations; proposed ADRs 0048 and 0049
remain owner decisions

Scope: FGA localswim ticket #0097

## Outcome

The derived OpenAPI inventory has 31 operations: 21 are schema-closed and 10
are explicitly `not_closed`. No current operation is optional implementation
polish. Each supports an accepted private-MVP recovery, credential, OAuth,
moderator-protection, or audit boundary.

The review also found that accepted ADR 0019 requires credential rotation but
the replacement FGA User API routes were deliberately omitted when ADR 0040
renamed Plugin Codes. Deferring rotation would require an explicit change to
the accepted release and annual-diligence contract, so the recommendation is
to close it now.

Two owner decisions block a truthful executable projection:

1. proposed [ADR 0048](../decisions/0048-return-flickr-authorization-target-as-json.md)
   corrects the browser-incompatible Flickr authorization-start `303`; and
2. proposed [ADR 0049](../decisions/0049-use-plugin-code-rotation-candidate-resources.md)
   selects the missing resource shape for credential rotation.

The other missing fields and statuses can follow the conventions below without
another architecture choice. The OpenAPI document must continue to say
`not_closed` until the two proposals are accepted and the scoped contracts
are updated; detailed prose is not executable acceptance evidence.

## Ten-operation inventory

| Operation | Private-MVP reason | Closure disposition |
| --- | --- | --- |
| Read ambiguity candidates | Required to recover an upload whose Flickr photo ID was not received without blindly uploading again | Keep; use required `page` and `page_size` like existing-public-photo discovery, and return one complete advisory page or `503` |
| Read Flickr connection | Required before link, relink, disconnect, and gate repair | Keep; return one sanitized revisioned link representation |
| Start Flickr authorization | Required to establish or replace the only Flickr grant | Keep; apply proposed ADR 0048 |
| Disconnect Flickr connection | Required by accepted explicit OAuth/account lifecycle | Keep; return the same sanitized link representation in `disconnecting` or `disconnected` state |
| List Plugin Codes | Required by ADR 0040 and the accepted interaction map before creation | Keep; close its existing keyset page |
| Create Plugin Code | Required to activate the first FGA LrC plug-in | Keep; close the transfer-precondition request; the one-time response is already exact |
| Revoke Plugin Code | Required for loss, compromise, and ordinary retirement | Keep; return the updated display-safe representation |
| List Flickr write gates | Required to observe fail-polite pauses and their repair requirements | Keep; return at most the deployment and current-user gate |
| Resume Flickr write gate | The only permitted way to resume writes after repair; no automatic or plug-in bypass exists | Keep; require exact origin, CSRF, recent authentication, and expected revision |
| Read audit events | Required to review security-state changes and failed attempts retained by the private control plane | Keep; close a bounded reverse-chronological keyset page |

## Missing rotation surface

The recommended addition under ADR 0049 is:

- one display-safe Plugin Code detail GET;
- one subordinate rotation-candidate collection POST; and
- one subordinate candidate PATCH whose only target states are `current` and
  `revoked`.

These routes expose no new authority beyond ADR 0019. They make its already
accepted create, verify, complete, cancel, expire, and recover states reachable
without action-verb routes or destructive DELETE semantics.

## Closure conventions

Use one convention across the remaining schemas:

- lower-case `snake_case` for query parameters and `camelCase` for JSON;
- `schemaVersion: 1` and `additionalProperties: false` on every FGA-owned
  object;
- exact opaque string identifiers and timestamps with six fractional UTC
  digits where database order or compare-and-set evidence matters;
- `page_size` plus opaque `page_token`, default 50 and maximum 100, for
  FGA database keyset collections; no total counts;
- the existing required numeric `page` and `page_size` convention only for
  advisory Flickr photo searches that directly page an upstream result;
- optional continuation fields omitted when no next page exists rather than
  empty-string sentinels;
- a display-safe `entityTag` beside each list member that can be mutated and
  the same strong value in the member response's `ETag` header;
- exact `200`, `201`, `204`, `400`, `401`, `403`, `404`, `409`,
  `412`, `415`, `422`, `429`, and `503` responses as applicable—no
  wildcard `2XX`; and
- `Cache-Control: no-store` on every response, including errors.

The Flickr connection representation needs the accepted link state/revision,
expected owner NSID, display name, permission, active secret-version ID,
sanitized verification times/outcome, local credential deletion state, FGA
operation state, Flickr permission state, user write gate, and retained-work
counts shown before disconnect. It never exposes a credential or a provider
locator.

The Plugin Code summary needs the accepted opaque ID, label, state, revision,
entity tag, creation/revocation/rotation-due times, overdue flag, and
approximate last-authenticated time. Its detail adds display-safe current and
pending version IDs/states/times and the latest sanitized lifecycle outcome.

The Flickr write-gate representation needs the stable gate ID, scope, state,
revision, pause/latest-observation times, sanitized reason and Flickr result,
latest verification outcome, affected intent count, oldest affected enqueue
time, correlation ID, and required repair class. Resume accepts only
`schemaVersion` and `expectedRevision`; the server obtains linked-account,
active-secret, deployment-build, and conformance evidence from current
authority rather than browser input.

The audit-event projection exposes only event ID/time, display-safe actor
class, action, opaque target type/ID, outcome, sanitized reason and before/after
state, and correlation ID. It does not expose internal ownership keys, session
values/digests, request bodies, credential material, photo metadata, or raw
exceptions.

## Work after owner decisions

After ADRs 0048 and 0049 are accepted:

1. amend the scoped OAuth, administrative, installation, transfer, and plug-in
   contracts without weakening their accepted state machines;
2. add the three rotation routes and close all request, parameter, header,
   response, and error schemas;
3. remove the unclosed placeholder responses and require zero
   `x-fga-schema-status: not_closed` operations;
4. add tests for closed objects, internal references, exact route inventory,
   authorization/CSRF/recent-auth metadata, and absence of wildcard success
   codes; and
5. run the complete architecture gate before the generated executable
   specification is imported into an implementation repository.

No production system, provider account, RDS database, Flickr grant, or secret
store is needed for that documentation and schema change.

