# ADR 0032: Read the current installation resource

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31

## Context

The draft credential-validation route was
`GET /api/v001/auth/device/token-check?device_type=lrc15_plugin`. Its path named
an authentication operation, while its required query parameter encoded one
client and Lightroom Classic release even though the private MVP has no second
profile to negotiate.

The FGA LrC plug-in needs to prove that its stored bearer credential currently
resolves to one active installation. Planned rotation also needs a safe read
that can identify a narrowly scoped unexpired candidate without promoting it.

## Decision

The FGA LrC plug-in validates either stored credential with:

```http
GET /api/v001/installations/current
Authorization: Bearer <FGA installation credential>
```

The request has no body or query parameters. A current credential for an active
installation returns `200 OK`, `Cache-Control: no-store`, and this minimal JSON
representation:

```json
{
  "schemaVersion": 1,
  "installationId": "server-generated-installation-id",
  "installationRevision": 7,
  "installationState": "active",
  "presentedCredentialState": "current"
}
```

An unexpired `pending_rotation` credential may read the same resource and
receives `presentedCredentialState: "pending_rotation"`; it remains forbidden
from every ordinary plug-in operation. This safe GET never promotes the
candidate or changes authorization state.

The response contains no credential version ID, credential class, user or
Flickr identity, secret, digest, replacement token, or session. The internal
credential class is `lrc_plugin`, not a Lightroom-version label. A concrete
future second authentication profile may add explicit capability
representation or negotiation without renaming this resource.

Missing authentication returns a bare Bearer `401`. A malformed bearer value,
unknown digest, inactive installation, expired/replaced/revoked version,
unknown stored class, or failed verification returns the same nonspecific
`401 invalid_token`. Repeated authorization fields, multiple token transmission
methods, a request body, or any query parameter is `400 invalid_request`.

The unreleased device token-check route is not registered, redirected, or
aliased. Route conformance requires an ordinary API `404`/`405` and no backend
operation for that path.

## Consequences

- The route names the authenticated resource and follows ordinary HTTP GET
  semantics.
- The wire contract contains no Lightroom version or speculative profile query.
- The FGA LrC plug-in receives enough stable identity/revision state to detect
  an unexpected installation change without receiving Flickr identity.
- Planned candidate verification remains safe and explicit.
- A future real capability difference can extend representation or negotiation
  without another route rename.

## Alternatives considered

- **Keep token-check and `device_type`:** rejected because there is no second
  profile and the path names mechanics rather than a resource.
- **Return `204` plus a custom state header:** rejected because the selected
  resource has a small useful representation and ordinary JSON is clearer.
- **Accept only current credentials:** rejected because it would remove the
  narrow pre-promotion proof required by the accepted rotation lifecycle.
- **Promote a pending candidate on GET:** rejected because a safe read must not
  broaden authority.

## Detailed contract

The [plug-in/service contract](../plugin-service-contract.md) defines request,
response, and error semantics. The [installation credential
lifecycle](../installation-credential-lifecycle.md) defines rotation,
revocation, and recovery.
