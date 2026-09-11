# ADR 0004: Start with a private single-user deployment

Date: 2026-08-20

Status: Accepted; owner scope reconfirmed 2026-08-23; phased expansion confirmed
2026-09-03

## Context

The first FGA user is the project owner, who has a Flickr application key and
is comfortable operating developer-oriented tooling. Designing public signup,
shared application credentials, account isolation, and support processes before
the core workflow exists would add substantial security and product scope.

On 2026-08-23, Terry clarified that he is not merely the first MVP user; he is
the only expected customer. Routine use must optimize his highly tuned
Lightroom Classic cull/edit/publish loop. A browser application, public signup,
and multi-user operation are not latent MVP requirements.

FGA still needs a hosted worker because group submissions must continue while
Lightroom and the photographer's laptop are offline.

## Decision

Build the MVP as a private, owner-operated hosted service for one Flickr user
and one Lightroom installation. Use the owner's Flickr application and
authorization. Provision service-side secrets administratively rather than
building public onboarding.

Authenticate calls from the Lightroom plug-in to the hosted API with a
revocable installation credential over HTTPS. Select the credential storage
mechanism together with the hosting stack. Decide the Flickr upload-signing and
token-transfer boundary separately in ADR 0005.

Retain explicit user identity and `(user, group)` partition keys in the domain
model. Single-user deployment is a scope boundary, not permission to bake a
global singleton into queue behavior.

Keep routine photo selection, group selection, publication, and queue-status
interaction inside the FGA LrC plug-in. Do not introduce a browser context
switch merely because the FGA API backend is easier for its developer to build
or reason about.

### Phased deployment path

Expansion is a sequence of explicit release boundaries, not one latent public-
signup feature:

1. **Owner-only MVP.** The accepted scope above remains the first deployment.
   The FGA API backend admits only Terry's exact allowlisted, validated Google
   `sub`; a valid Google identity is authentication, not public admission.
2. **Invite-only closed beta.** This phase requires a separately accepted design
   for tenant isolation, admission and administration, conservative per-user and
   per-group limits, outstanding-intent caps, spend limits, monitoring,
   suspension, support and incident handling, Flickr-terms compliance, and a
   privacy-compatible erasure and re-registration policy that preserves required
   moderator-protection memory. Entry remains explicitly invited; this phase has
   no open signup.
3. **Public signup.** Admission for any otherwise eligible Google Account requires
   operational evidence from the closed beta and a separate accepted go/no-go
   decision covering the same security, privacy, abuse, support, terms, and cost
   gates at public scale. Google authentication alone never silently advances the
   service into this phase.

Later phases are not implementation commitments. Each remains out of scope until
Terry deliberately authorizes it after its entry gates are satisfied.

## Consequences

- The MVP avoids signup, account recovery, tenant administration, and shared
  Flickr application-key distribution.
- The hosted service may assume one administratively authorized Flickr
  identity while still enforcing authentication on every plug-in request.
- Secrets can be provisioned directly into managed secret storage for the first
  deployment.
- Database and API contracts remain capable of representing more than one user,
  avoiding an unnecessary migration if the product later expands.
- A public or multi-user release requires a new security, onboarding, privacy,
  support, and Flickr-terms review.
- Multi-user expansion has an explicit invite-only proving phase before open
  signup; neither phase inherits authorization from the owner-only MVP.
- Public/browser product work is out of scope unless Terry deliberately changes
  the expected-customer decision; retained user keys are domain clarity, not a
  mandate to build speculative multi-user infrastructure.
