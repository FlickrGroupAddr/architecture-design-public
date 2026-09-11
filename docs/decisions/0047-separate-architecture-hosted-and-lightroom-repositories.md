# ADR 0047: Separate architecture, hosted, and Lightroom repositories

Date: 2026-09-05

Status: Proposed

Review boundary: FGA localswim ticket #0099

## Context

The architecture repository deliberately owns accepted decisions, scoped
contracts, derived design projections, research, and host diagnostics. It does
not contain a production FGA API backend or production FGA LrC plug-in. Turning
it into an implementation repository would mix architecture authority with
generated artifacts, deployment configuration, licensed local SDK material,
and two unrelated release toolchains.

The legacy `FlickrGroupAddr/backend-api` repository is useful implementation
evidence, but its D1, Durable Object, routing, and contract choices predate the
current accepted architecture. Importing its history wholesale would make
obsolete decisions appear current. The new public
`FlickrGroupAddr/api-cloudflare` repository exists as a clean Cloudflare
implementation workspace.
[ADR 0050](0050-select-cloudflare-and-evaluate-native-storage-first.md)
now explicitly selects Cloudflare and evaluates Durable Objects and D1 before
the RDS fallback.
This repository proposal and the license choice remain separate decisions.

The hosted TypeScript runtime and the Lua plug-in differ materially:

- the hosted implementation owns Worker deployment, selected-storage migrations,
  server route registration, JAMstack assets, and provider conformance;
- the FGA LrC plug-in is packaged and versioned as an Adobe Lightroom Classic
  plug-in, uses the locally restored Adobe SDK, and must increment `Info.lua`
  for every loadable build; and
- neither component needs the other's source code to build or release.

Accepted ADR 0003 requires MIT licensing for both components. On 2026-09-06,
Terry reaffirmed that project-wide license and directed that `api-cloudflare`
be public. This resolves the hosted-code license question independently of this
repository-boundary proposal. The private Localswim state-store repository
continues to hold sensitive coordination state.

## Proposed decision

1. Keep `FlickrGroupAddr/architecture-design` as the architecture and evidence
   repository. It retains accepted ADRs and contracts, derived public design
   projections, research, diagnostic FGA LrC plug-ins, and architecture
   validation. It does not acquire production hosted or production plug-in
   code.
2. Use `FlickrGroupAddr/api-cloudflare` for the selected Cloudflare platform.
   After this repository decision and the required deployment gates pass, it
   becomes the production hosted repository. It owns the FGA API backend,
   refresh and group-submission handlers, JAMstack administrative assets,
   selected-storage migrations, Cloudflare configuration, dependency lock,
   and hosted tests. TypeScript remains the current language recommendation.
   Platform selection does not claim deployed conformance.
3. Create `FlickrGroupAddr/lightroom-plugin` after this decision is accepted.
   It owns the production Lua FGA LrC plug-in, distributable assets, packaging,
   host-facing tests, and release notes. The Adobe SDK stays local and ignored;
   the repository records the exact supported SDK build and SHA2-256 digest
   needed to restore it.
4. Do not merge or replay the legacy `backend-api` history. Reuse a specific
   implementation only through a normal reviewed change that identifies its
   current requirement, tests it against accepted contracts, and retains every
   compatible third-party notice.
5. The hosted application's typed route and runtime-schema registry is the
   executable source for server routes. Its build deterministically emits:

   - `route-inventory.json`, as required by ADR 0016; and
   - a complete OpenAPI document for the same registered build.

   The architecture repository's current OpenAPI file remains a derived design
   projection. Hosted CI compares the generated executable document with the
   accepted architecture commit and fails on an unexplained route, authority,
   or schema difference. A release records the architecture commit, generated
   OpenAPI SHA2-256 digest, route-inventory SHA2-256 digest, migration head, and
   hosted build ID. It does not make a second hand-maintained route list.
6. The repositories release independently. The URI version
   (`/api/v001`) changes only for a deliberately incompatible HTTP contract;
   JSON `schemaVersion` fields follow their scoped contracts; hosted builds
   use an immutable commit/build identifier; and every loadable FGA LrC plug-in
   build uses its exact `Info.lua` version. Lockstep repository versions are
   not required.
7. Hosted releases publish the generated OpenAPI document, route inventory, and
   a sanitized response-fixture corpus as immutable build artifacts. The
   FGA LrC plug-in pins their build identifier and SHA2-256 digests for its
   contract tests. Neither repository imports mutable source from the other's
   default branch, and neither uses a Git submodule.

## First end-to-end vertical slice

The first slice is **validate one FGA installation credential from the FGA LrC
plug-in through the same-origin HTTPS edge to the selected durable storage and
back**:

```text
FGA LrC plug-in
  -> GET /api/v001/installations/current
  -> Cloudflare HTTPS edge and FGA API backend
  -> SHA2-256 credential lookup in an isolated storage fixture
  -> exact no-store installation representation
  -> exhaustive FGA LrC plug-in validation
```

This slice is intentionally read-only after fixture provisioning. It does not
need Flickr application credentials, call Flickr, create group intents, rotate
an installation credential, or touch production data.

### Entry gates

- ADR 0047 is accepted; ADR 0003 already supplies the hosted-code license.
- ADR 0050 selects Cloudflare. The storage path has passed its scoped proof
  gates, or Terry authorizes this slice as isolated storage evidence.
- The two implementation repositories exist with the chosen public visibility,
  protected default branches, pinned toolchains, dependency/license review, and
  no Adobe SDK files.
- Isolated native storage, or PostgreSQL 18.6 for the fallback, can be
  destroyed and recreated without production data or credentials.
- The accepted current-installation schema and authorization matrix in ADR 0032
  and the plug-in/service contract remain closed and unchanged.

### Exit evidence

The slice is complete only when one immutable pair of hosted and plug-in builds
passes all of these checks:

1. A migration creates the installation and credential-version invariants in a
   fresh isolated instance of the selected storage and rolls forward from the
   preceding migration head.
2. The hosted route registry generates both OpenAPI and the route inventory;
   neither artifact is hand-maintained, and their SHA2-256 digests are recorded
   with the build.
3. The real development asset router and an isolated provider preview route
   exact `/api` and prefix `/api/` to the FGA API backend before any JAMstack
   asset or application-shell fallback.
4. A current fixture credential returns the exact `200` representation and
   `Cache-Control: no-store`; an unexpired pending fixture returns
   `presentedCredentialState: pending_rotation`; missing, malformed, unknown,
   replaced, revoked, and expired fixtures return their accepted non-oracular
   failures.
5. A pending credential cannot authorize an ordinary plug-in route. Every test
   proves that no Flickr call or protected mutation occurs.
6. An actual versioned FGA LrC plug-in build retrieves its fixture credential
   from `LrPasswords`, sends the documented `Authorization` header through
   `LrHttp`, exhaustively validates the response, and writes only the
   probe-specific sanitized JSON handoff under `C:\Temp`.
7. The same generated response corpus passes hosted schema validation and
   FGA LrC plug-in decoder tests. The recorded plug-in manifest names the exact
   hosted build and artifact digests exercised.
8. Teardown removes the isolated credential and database. Logs and artifacts
   contain no bearer value, digest, private photo metadata, production
   identifier, or provider secret.

Provider preview evidence is a gate for the end-to-end slice, not permission to
deploy production resources. Local tests may be developed first, but they do
not satisfy this exit boundary alone.

## Consequences

- A maintainer can understand each repository's authority and release boundary
  without learning a monorepo-specific build system.
- The hosted implementation can use TypeScript and Cloudflare-native tooling
  without imposing Node tooling on the Lua plug-in.
- The Adobe SDK license boundary remains isolated from hosted code and public
  architecture documents.
- Cross-repository compatibility is explicit and build-bound rather than
  inferred from both repositories currently passing their own tests.
- A future provider change replaces or supersedes the hosted candidate without
  rewriting architecture or plug-in history.
- The first slice proves the client, edge, runtime, database, generated
  contract, and redaction boundaries without risking a Flickr write.

## Alternatives considered

- **Turn `architecture-design` into a monorepo:** rejected because it mixes
  authority/evidence with two production toolchains and makes generated
  implementation artifacts look like architecture permission.
- **Put hosted and Lua implementation in `api-cloudflare`:** rejected because
  their runtime, packaging, licensing inputs, release cadence, and provider
  portability differ, while they share only a versioned HTTP contract.
- **Continue `backend-api`:** rejected because its long history contains
  superseded architecture and would make selective reuse harder to audit than
  a clean reviewed port.
- **Copy OpenAPI and route lists between repositories:** rejected because two
  editable copies recreate the drift ADR 0016 is intended to prevent.
- **Require lockstep releases:** rejected because a compatible API deployment
  or plug-in-only fix should not force an unrelated release.
- **Begin with Flickr OAuth or publication:** rejected because credential
  validation proves the complete client-to-database skeleton without secrets
  lifecycle, irreversible publication, or moderator-facing writes.
