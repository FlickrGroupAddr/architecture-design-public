# ADR 0016: Derive and black-box-test server-first route ownership

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31

## Context

The FGA HTTPS edge will serve administrative browser assets and server routes on
one origin. A static or single-page-application fallback can return plausible
HTML while intercepting the Google login endpoint, Flickr callback, or versioned API
route. Handler unit tests do not exercise that deployed boundary.

The reviewed legacy repository demonstrated the failure mode: source and tests
used `/auth` paths while development/deployment asset-routing allowlists named
`/oauth`. Maintaining another manual route list would preserve the same drift
mechanism.

The current repository contains architecture and diagnostic tools, not the
hosted server or router. It therefore cannot truthfully report an executable
deployment conformance pass yet.

## Decision

The hosted implementation will make its application route registry the sole
source of server-route metadata and deterministically emit one versioned route
inventory during the build. Development proxy/asset routing and deployable edge
configuration derive their worker-first matchers from that inventory or the
same typed registry module.

Path ownership sends exact `/api/v001` and prefix `/api/v001/`, exact
`/admin/google-login`, and exact `/admin/flickr-oauth/callback` to their FGA
hosted component before any static asset or administrative-shell fallback.
Accepted ADR 0043 fixes the Google login URI, which must appear in the
application route registry before implementation. Classification is independent
of HTTP method. Unknown API paths still reach the FGA API backend's JSON `404`.

One mandatory `route-conformance` gate validates the inventory and both router
artifacts, then sends the same non-destructive black-box probes through the real
development topology and an isolated provider preview deployment. It
binds evidence to the exact build, inventory, router artifacts, and preview
deployment. A missing/skipped/inconclusive phase fails; handler unit tests or a
hand-written expected-routing fixture cannot substitute.

ADR 0033 proposes Terraform plus effective Google Cloud exports and an isolated
`preview.flickrgroupaddr.com` deployment as the provider-specific adapters. No
real configuration exists in this architecture repository yet. The complete
probe, failure, and rollback contract is in
[`http-route-conformance.md`](../operations/http-route-conformance.md).

## Consequences

- Route registration, development behavior, and deployed edge behavior cannot
  silently maintain different `/auth`/`oauth` vocabularies.
- A newly registered auth/API route automatically enters the conformance matrix
  in the same build.
- Development-only success cannot approve a deployment; the preview HTTPS edge
  is part of the gate.
- The inventory is a generated artifact, avoiding a second manually maintained
  source of truth.
- Provider selection must include an effective configuration export or real
  preview boundary capable of producing the evidence.
- No passing result exists until hosted implementation supplies the registry
  and both real adapters. The design repository records that absence rather
  than treating a mock as deployment proof.

## Alternatives considered

- **Maintain a manual asset-router allowlist:** rejected because it recreates
  the exact drift that caused the legacy defect.
- **Route only the known API paths:** rejected because an unknown versioned API
  path could fall through to HTML instead of the backend's truthful `404`.
- **Test handlers directly:** rejected because it bypasses development and
  deployed asset routing.
- **Validate only generated provider configuration:** rejected because a
  compiler/simulator can differ from the effective preview edge.
- **Expose a permanent production debug endpoint/header:** rejected because
  contractual response discriminators and an isolated preview adapter can prove
  ownership without expanding the public diagnostic surface.
