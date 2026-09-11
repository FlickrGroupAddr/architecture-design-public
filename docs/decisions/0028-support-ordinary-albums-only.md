# ADR 0028: Support ordinary albums only

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31

## Context

Adobe's built-in Lightroom Classic Flickr provider exposes both **Create
Album…** and **Create Smart Album…**. Terry's actual workflow uses ordinary
albums as deliberate culling and publication containers. He explicitly decided
that the FGA LrC plug-in should not offer smart albums because automatic
membership based on date, location, metadata, or other criteria conflicts with
that control model.

A smart published collection is not merely another creation dialog. When its
filter changes or a photo's metadata changes, membership can change without an
explicit album edit. The FGA LrC plug-in, FGA API backend, and FGA database
would then need departure, unpublish, and remote Flickr album-membership
semantics. The current safety boundary intentionally makes local removal
non-destructive and never calls Flickr album-membership removal.

## Decision

The FGA LrC plug-in supports ordinary published collections as **Album** and
does not expose **Create Smart Album…**, smart-filter definitions, or dynamic
membership reconciliation. This is a product-scope exclusion, not a feature
deferred from the first usable version.

Any future reconsideration requires a new owner decision and architecture
record. That decision must define how automatic local entry and departure map
to publication, Flickr album membership, owner-visible state, and
reconciliation without weakening the non-destructive local-removal boundary.

## Consequences

- Album membership remains deliberate and understandable in Terry's cull,
  edit, and publish loop.
- The FGA LrC plug-in does not need to persist or evaluate smart filters.
- Metadata changes cannot silently create or withdraw a Flickr album
  obligation.
- The FGA LrC plug-in does not reproduce every feature of Adobe's built-in
  Flickr provider.
- Adding smart albums later is a product and safety decision, not a hidden
  implementation extension.

## Alternatives considered

- **Match Adobe's built-in provider:** rejected because feature parity is not a
  requirement and dynamic membership adds behavior Terry does not want.
- **Defer smart albums as post-MVP backlog:** rejected because that would imply
  they remain expected scope; Terry made an affirmative ordinary-albums-only
  product decision.
- **Treat smart-album departure as local-only:** rejected as an incomplete
  contract because it would leave dynamically departed photos attached to the
  remote album without a deliberately designed user model.

## Detailed contract

The [album-scoped publish contract](../album-scoped-publish-contract.md) defines
the ordinary published-collection boundary. The
[album lifecycle contract](../album-lifecycle-contract.md) defines explicit
rename, reparent, local removal, and non-destructive Flickr behavior.
