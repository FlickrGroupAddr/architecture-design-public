# ADR 0026: Reconcile album creation by owner and attachment by membership

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31

## Context

Flickr album creation and album membership have different ambiguity costs.
`flickr.photosets.create` has no documented idempotency key, so replay can make
a second album. `flickr.photosets.addPhoto` establishes a set-like relation and
documents an already-in-set outcome, so a repeat cannot create a duplicate
membership.

Album titles are not unique identity. A lost create response can leave one or
more plausible albums, while a strict membership read can directly observe the
desired add postcondition.

## Decision

The FGA album worker will commit a durable marker before either write.

After an ambiguous create, no FGA component will replay creation. The FGA API
backend will present albums newly observed in the first photo's contexts as
candidates, and the FGA LrC plug-in will require Terry to select or enter one
exact photoset ID. Fresh hosted owner and first-photo membership proof precedes
one immutable binding. No candidate is selected automatically and no duplicate
is deleted automatically.

After an ambiguous `addPhoto`, the FGA album worker will perform a strict fresh
membership read. Present membership satisfies the obligation. Verified absence
permits a bounded new attempt because the relation cannot duplicate and Flickr
documents code `3` for already-in-set. An unavailable or incomplete read permits
no write.

## Consequences

- Rare ambiguous creates require explicit owner judgment but cannot silently
  duplicate albums.
- Attachment normally repairs itself without asking Terry and remains truthful
  through read failures.
- The implementation needs two attempt models instead of a misleading generic
  Flickr-write retry policy.
- An unresolved create blocks new uploads for that local album while preserving
  already uploaded photo obligations.
- The FGA album worker remains add-only until a separate accepted lifecycle
  contract explicitly says otherwise.

## Alternatives considered

- **Retry create after listing by title:** rejected because title is not unique
  and list consistency does not prove absence.
- **Automatically bind the only new candidate:** rejected because another
  Flickr client can create or modify an album in the same interval.
- **Embed a hidden marker in the album title or description:** rejected because
  it exposes surprising implementation metadata on a user-visible resource.
- **Never retry album membership:** rejected because exact present/absent state
  is observable and the relation is non-duplicating.
- **Treat an `addPhoto` response as final proof:** rejected because a fresh read
  is the authoritative membership observation.

## Detailed contract

The [album-write reconciliation contract](../album-write-reconciliation.md)
defines dispatch persistence, candidate repair, attachment retries, owner-visible
states, and conformance evidence.
