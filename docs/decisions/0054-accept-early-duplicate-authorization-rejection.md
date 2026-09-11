# ADR 0054: Accept early duplicate-Authorization rejection

Date: 2026-09-11

Status: Accepted by Terry on 2026-09-11

## Context and owner decision

The current-installation read proof rejected repeated Authorization header
fields before the Worker and returned Cloudflare's stock HTTP 400 HTML body,
without the application's no-store header or Bearer challenge. The observed
response contained no application/session data, cookie or redirect. Application
requests that reached the handler received the accepted JSON authentication
errors. The existing early-parser exception covered malformed request targets
and explicitly excluded authentication, so this result was recorded as a failure.

Codex recommended extending the same narrow exception to duplicate Authorization
fields instead of adding a proxy solely to restyle the provider's rejection.
Terry approved that recommendation on 2026-09-11. The private project's benefit
is avoiding another component and its maintenance; the accepted tradeoff is that
clients must handle this early non-JSON HTTP 400 as they already do for malformed
targets. No credential is accepted by either rejection path.
[Original failing evidence and approved recommendation](https://github.com/FlickrGroupAddr/api-cloudflare/blob/5f128ba/docs/research/2026-09-11-d1-foundation-and-installation-read.md).

## Decision and amended authority

A provider HTTP parser may reject duplicate Authorization header fields before
application execution with its own HTTP 400, including a non-JSON body without
the application's Cache-Control: no-store or Bearer challenge. It must not
redirect, serve an application shell, set an application/session cookie, or
expose application/session data or credentials.

This explicitly extends ADR 0037's early-parser clarification and the HTTP route
conformance, health/diagnostics and plug-in service error contracts. Every
application-generated authentication response retains the accepted JSON/no-store
and matching Bearer error-code requirements. Repeated/comma-separated fields
that reach the handler still receive invalid_request, not a successful lookup.

The existing malformed-target exception remains. There is no blanket exception
for authentication failures, valid operations, ordinary 404/405 responses,
provider outages on valid requests, unknown HTML, redirects or static fallback.
Conformance evidence must establish the early provider boundary and keep these
negative controls. A known response fingerprint may be a bounded test fixture
discriminator; it is not a production dependency or permission to accept any
HTML 400. Previous failures remain historical evidence, not retroactive passes.

## Hosted evidence after approval

The [fresh installation-read proof](https://github.com/FlickrGroupAddr/api-cloudflare/blob/6e18b1a/docs/evidence/foundation-read-approved-2026-09-11.json)
passes all 26 scoped checks, including the bounded provider duplicate-header
rejection. Negative regression cases reject other statuses, unknown bodies,
redirects, cookies and application response markers. Application test cases
have no retries, the read phase changes no durable state, and cleanup is
confirmed. The [implementation handoff](https://github.com/FlickrGroupAddr/api-cloudflare/blob/6e18b1a/docs/research/2026-09-11-d1-foundation-and-installation-read.md)
retains the failed preliminary sweep and its diagnostic limits. This does not
claim uninterrupted provider availability, production TLS or real LrC execution.
