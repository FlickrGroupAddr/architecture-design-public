# ADR 0052: Evaluate paused native credential replacement before AWS

Date: 2026-09-11

Status: Accepted by Terry on 2026-09-11; evaluation direction and private
availability tradeoff accepted; bounded native proof complete, production
integration/conformance pending

## Context and owner decision

ADR 0017 originally requires independently addressable immutable managed-secret
versions so a new Flickr grant can be staged while the previous grant remains
available until database activation commits. The native Secrets Store binding
exposes the configured secret's value without a provider version selector.
Codex therefore recommended AWS Secrets Manager and completed a disposable
Worker-to-AWS integration proof.

Terry challenged whether that requirement justified the additional service,
AWS credentials, and cross-provider operations for his private hobby deployment.
Codex explained the actual interruption case: replacing A with B in a mutable
store before database activation can leave the store and database disagreeing,
and A may no longer be available for rollback. Provider versions address that
availability/recovery promise; they do not create a cross-service transaction.
No probability for the race was measured.

Codex then recommended evaluating one native secret containing the credential
pair and an application generation, with a durable pause during replacement,
generation-mismatch rejection, and repair or another relink after failure.
Terry approved that recommendation on 2026-09-11 and explicitly set a very high
bar for adding AWS services. This is an owner-approved narrowing of the
previous availability promise, not a claim that mutable values equal provider
version history or that the native lifecycle has already passed testing.
[Decision review and proposal](https://github.com/FlickrGroupAddr/api-cloudflare/blob/1b68497/docs/research/2026-09-07-flickr-credential-store-decision.md).

## Decision

1. Evaluate the paused Cloudflare-only Flickr credential lifecycle before
   adopting unattended AWS credentials or progressing AWS as the default
   secret store. The accepted private tradeoff permits interrupted replacement
   to remain paused and require repair or another relink. It need not retain
   the previous credential for automatic rollback.
2. The candidate uses one configured native managed secret containing the token,
   token secret, and an opaque application generation together. Each distinct
   pair receives a new generation; never reuse a generation for changed bytes.
   The FGA database holds generation and lifecycle metadata, never credential
   bytes. A provider VersionId is not required for this scoped evaluation.
3. Durably pause new ordinary Flickr operations before mutable replacement,
   serialize lifecycle actions, and explicitly handle in-flight requests.
   Verify the expected Flickr owner and required permission before activation.
   Activate only the intended generation with a database compare-and-set and
   audit event. Consumers reject malformed bundles, unavailable secrets,
   generation mismatch, stale revisions, and a replacement pause. Recheck
   current authority at the existing dispatch boundary.
4. No pause recalls bytes already dispatched. An uncertain Flickr write retains
   the accepted ambiguity outcome and cannot be replayed because a credential
   changed. Stale failures cannot disable a newer grant. Preserve the explicit
   write-gate resume ceremony; completing replacement does not resume writes.
5. Missing, late, or uncertain native mutations and database commits leave a
   truthful paused/repair state. Never activate merely because a PATCH returned
   success, assume instant propagation to all Workers, or select an older
   grant as fallback. A late cleanup or replacement must not silently restore
   authority, delete an active successor, or produce a false completed status.
6. Use the native read binding for consumers. Automated updates require a
   separately reviewed, narrowly scoped Cloudflare management credential;
   the binding does not supply write authority. This decision does not approve
   broad administration credentials in runtime code, application-encrypted
   credentials in D1, a custom secret broker, or a deployment coordinator.
7. Authorize bounded synthetic evaluation on implementation #0009, with
   checkpointed disposable fixtures, sanitized evidence, and verified cleanup.
   Actual provider update/propagation/deletion and failure behavior must be
   proved. Local models and the existing AWS proof do not establish those
   results. Complete the durable schema and UI/wire mapping before production;
   this ADR adds no undocumented public state enum or response field.
8. Keep AWS services available as fallbacks, with a high need threshold across
   the project. Identify a concrete unmet private-deployment requirement and
   why its consequence matters; support the native limitation with applicable
   evidence; first consider a simpler native implementation or owner-approved
   workflow such as a maintenance pause. Compare the total identity, network,
   recovery, cost, and maintenance burden. A missing preferred API shape,
   unexamined seamless-availability assumption, or completed AWS prototype is
   not enough. Do not build elaborate native machinery merely to avoid AWS,
   or waive an accepted safety boundary without owner approval.

## Scope and amended authority

This ADR amends ADR 0050's unresolved secret-selector decision and strengthens
its fallback criteria. It amends ADR 0017 and the OAuth lifecycle's exact
provider-version/old-grant-preservation requirements for the accepted private
paused candidate only. The provider-versioned replacement sequence remains a
conforming fallback design. A selected native production adapter must satisfy
the amended lifecycle and its proof gates; this approval is not deployment or
conformance evidence.

Recent authentication, CSRF/origin checks, owner/permission validation, secret
redaction, explicit disconnect/cleanup, stale-result fencing, and permanent
submission safety remain required. The native deletion mechanism must not be
claimed complete until demonstrated. This decision does not change static
application keys, browser-session signing keys, Plugin Codes, or their separate
contracts, nor does it expand the private deployment to public/multi-user use.

## Required bounded proof

- Read a valid matching generation; reject mismatches and malformed/unavailable
  bundles without a Flickr call or credential-bearing output.
- Pause durably before replacement and reject ordinary reads/writes during it;
  reopen after a process interruption and retain that pause.
- Replace the fixed native value, observe propagation without assuming a global
  atomic switch, and activate the intended generation with durable fencing.
- Inject lost/delayed store responses, failed/lost database activation,
  competing relinks, stale results, and replacement versus disconnect/cleanup.
  Mismatch or uncertainty prevents work; repair never replays a Flickr write.
- Prove native removal/retirement and resumed-cleanup behavior without deleting
  an active replacement; distinguish stopped authority from confirmed removal.
- Verify the actual management/read permission boundary, redaction, source/build
  identity, bounded timeouts, and cleanup using only disposable synthetic data.

## Consequences

A relink may interrupt background work, and failed replacement may require
operator repair. Terry accepts that availability cost to avoid AWS operations
unless a real unmet requirement warrants them. Generation checking detects
incorrect selection; it is not immutable storage or a guarantee of provider
propagation. D1 and Secrets Store never share an assumed atomic transaction.

The earlier AWS proof remains useful fallback evidence and is retained. It is
not a reason to create unattended AWS keys or select AWS while native proof
remains incomplete.

## Bounded proof outcome, 2026-09-11

The hosted [native lifecycle proof](https://github.com/FlickrGroupAddr/api-cloudflare/blob/8d2cd48a7417caca3c3a6e66d8c3ff3e427398c9/docs/research/2026-09-11-native-secret-lifecycle-proof.md) passed all 29 cases, with
source/build evidence and confirmed cleanup of every disposable resource.
D1 retained pending and retiring generation metadata, and the native binding
returned the current bundle. Tests covered pause across deployment replacement,
competing starts, activation/audit rollback, lost-response reconciliation,
stale/malformed values, correlated retirement, and relink through the same
binding. The local runtime additionally passed disposal/reopen tests.

Normal disconnect in this candidate retires the credential payload by replacing
it with a noncredential marker identifying the exact retiring generation;
it keeps the provider entry available for later relink. Physical entry deletion
was separately verified during teardown after removing the Worker. This is
bounded evidence of payload retirement and resource removal, not physical
erasure of provider backups or globally atomic propagation.

The successful run demonstrates no need for AWS for this bounded lifecycle.
It does not accept production routes, management-token scope, real Flickr
owner/permission validation, final UI/wire mapping, or the production database
and dispatch/restore gates. The test controller's local operator is not an
unattended production management identity. Those remain implementation work;
the fixture schema and public probe outcomes must not become production wire
schemas by inference.

## Related authority

- [OAuth and account lifecycle](0017-explicit-oauth-and-account-lifecycle.md)
- [Detailed lifecycle](../oauth-and-account-lifecycle.md)
- [Native-first hosting](0050-select-cloudflare-and-evaluate-native-storage-first.md)
- [Private runtime trust](0051-trust-private-storage-runtime-with-guarded-writes.md)
- [Historical native secret review](../research/2026-09-05-cloudflare-secret-versioning-gate.md)
