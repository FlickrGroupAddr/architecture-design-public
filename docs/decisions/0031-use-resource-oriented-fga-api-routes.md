# ADR 0031: Use resource-oriented FGA API routes

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31

## Context

The draft plug-in API placed group discovery, upload authorization, and group
batch creation beneath `/api/v001/flickr-api-proxy/`. That name exposed an
internal integration boundary even though none of the operations is a
transparent proxy: the FGA API backend authenticates, validates, derives
authority, persists state, schedules work, and sometimes makes no synchronous
Flickr request at all.

Terry approved removing the namespace before the wire contract is frozen. He
still needs to observe whether an operation stopped at the FGA API backend or
reached Flickr, but URI spelling is the wrong operational signal.

## Decision

The plug-in API uses these resource-oriented paths:

| Method | Path | Resource meaning |
| --- | --- | --- |
| `GET` | `/api/v001/groups` | Current revisioned writable-group snapshot |
| `GET` | `/api/v001/photo-bindings/{photoBindingId}/group-memberships` | Fresh group-membership observation for one hosted photo binding |
| `POST` | `/api/v001/upload-authorizations` | Create one short-lived signed upload authorization |
| `PUT` | `/api/v001/upload-authorizations/{uploadAuthorizationId}/photo-binding` | Bind and prove the upload result |
| `GET` | `/api/v001/upload-authorizations/{uploadAuthorizationId}/ambiguity-candidates` | Read reconciliation candidates |
| `PUT` | `/api/v001/upload-authorizations/{uploadAuthorizationId}/ambiguity-resolution` | Resolve one ambiguous upload |
| `POST` | `/api/v001/group-submission-batches` | Create one durable bounded batch of group intents |
| `GET` | `/api/v001/group-submission-intents` | Read the authenticated user's bounded intent-status collection |
| `GET` | `/api/v001/group-submission-intents/{submissionIntentId}` | Read one authenticated intent status |

Existing-public-photo and administrative routes retain their already
resource-oriented names. The photo-membership route remains under hosted
`photo-bindings`, not client-supplied Flickr photo IDs, because the binding is
the authenticated authority boundary.

ADR 0034 separately adds read-only administrative mirrors beneath
`/api/v001/admin/group-submission-intents`. Neither route family includes a
retry, reopen, cancel, force, or block-clear action.

The draft `flickr-api-proxy` paths were never a released compatibility contract.
The FGA API backend registers no aliases or redirects for them; conformance
tests require ordinary API `404`/`405` responses with no Flickr call.

The FGA API backend, FGA refresh worker, and FGA group-submission worker expose
the internal boundary through sanitized structured logs, metrics, and traces.
They record the FGA operation name, whether an upstream dispatch began, the
allowlisted Flickr method name, result class, duration, and internal correlation
IDs. They do not log credentials, OAuth fields, raw request/response bodies,
photo titles, group names, or local catalog data.

## Consequences

- Client paths describe stable FGA resources rather than upstream plumbing.
- The FGA LrC plug-in does not need route changes if an implementation stops
  calling Flickr synchronously or adds an internal queue.
- Operators retain explicit, queryable evidence of upstream dispatch and
  failure boundaries.
- There is no compatibility alias or deprecation period for an unreleased draft
  namespace.

## Alternatives considered

- **Retain `flickr-api-proxy`:** rejected because it is misleading for persisted,
  asynchronous, derived-authority operations.
- **Use `/photos/{flickrPhotoId}/group-memberships`:** rejected because a client
  Flickr ID is only a lookup key and does not prove hosted ownership or binding.
- **Expose an `upstream=flickr` query flag:** rejected because client input must
  not select internal dispatch behavior.
- **Keep aliases for safety:** rejected because no released client depends on
  the draft paths and aliases would permanently expand the route surface.

## Detailed contract

The [plug-in/service contract](../plugin-service-contract.md) defines the route
templates, request authority, response semantics, and error behavior. The
[HTTP route conformance plan](../operations/http-route-conformance.md) owns edge
and negative-route verification.
