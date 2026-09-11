# OpenAPI design projection

Status: Derived design documentation; not executable implementation evidence

Authority: Apply the [architecture documentation hierarchy](../docs/README.md)
and then each operation's `x-fga-source` contracts and ADRs. A conflict is a
defect in this projection; this file does not amend the controlling source.

[`openapi.json`](openapi.json) documents the complete planned private-MVP HTTP
API inventory: public health, installation-authenticated FGA LrC plug-in
operations, cookie-authenticated FGA User UI operations, and separately
authorized administrative operations. It uses
[OpenAPI 3.1.2](https://spec.openapis.org/oas/v3.1.2.html) and that version's
JSON Schema 2020-12-based OAS dialect. OpenAPI 3.2 is newer, but this repository
has no implementation toolchain that needs its feature set; 3.1 remains the
smaller interoperability target.

The projection is deliberately explicit about schema maturity:

- `x-fga-schema-status: closed` means the named scoped contract currently
  defines the represented request and response shape closely enough to project
  it here.
- `x-fga-schema-status: not_closed` means the route and authority are designed,
  but at least one request, query, header, status, or representation detail is
  not yet fixed. The operation remains visible, but the OpenAPI document omits
  the unknown schema instead of inventing one.

No production FGA API backend or generated route inventory exists yet. Before
implementation treats this description as executable evidence, every
`not_closed` operation must become exact, an implementation-selected OpenAPI
validator/generator must be pinned and license-reviewed, and the route,
authorization, provider-preview, and drift gates in the controlling contracts
must pass for the same build.
