# ADR 0042: Use the Flickr wordmark in the tab-three service boundary

Date: 2026-08-30

Status: Accepted

Decision type: Explicit owner override

## Context

Tab 3 of the clean-room authentication interaction map depicts Flickr as an
external service boundary. Terry requested that its plain `Flickr` heading be
replaced by the Flickr vector wordmark.

Codex recommended retaining the plain text heading or using a neutral
photo-service glyph. Flickr's developer guidance says that use of the Flickr
API does not grant permission to use Flickr trademarks, including the logo and
dots, without explicit written permission. Wikimedia Commons marks the selected
wordmark as public-domain for copyright purposes but separately warns that it
may remain protected as a trademark. A downloadable public-domain vector source
therefore resolves copyright provenance, not trademark permission.

On 2026-08-30 Terry explicitly rejected the conventional recommendation and
directed Codex to use the wordmark. His stated justification was that FGA is a
hobby project and he is willing to risk receiving a cease-and-desist demand.

Sources:

- [Flickr Developer Guide — Business](https://www.flickr.com/services/developer/business/)
- [Wikimedia Commons — Flickr wordmark.svg](https://commons.wikimedia.org/wiki/File:Flickr_wordmark.svg)

## Decision

The tab-three Flickr service boundary uses the Wikimedia Commons Flickr
wordmark vector. FGA does not claim ownership of the mark, permission from
Flickr or SmugMug, endorsement, partnership, or any trademark right. This is a
narrow visual-documentation exception and does not authorize the wordmark in
the FGA product, user interface, website, marketing, distribution package, or
other project artifacts.

The maintainable diagram builder embeds the sourced vector directly so the
diagram remains deterministic and does not depend on a remote asset at render
time. The source comment and this ADR preserve its provenance and the owner
override.

## Consequences

- The diagram identifies the external Flickr boundary more quickly for Terry.
- The public repository contains a Flickr trademark without documented written
  permission from its owner.
- Flickr or SmugMug may request or require removal. FGA must be able to replace
  the wordmark with the former plain heading promptly.
- Public-domain copyright status does not eliminate trademark exposure.
- Future maintainers must not infer broader branding permission from this one
  accepted exception.

## Alternatives considered

- **Retain the plain `Flickr` heading:** Codex's conventional recommendation;
  rejected by Terry because he prefers the official wordmark and accepts the
  hobby project's cease-and-desist risk.
- **Use a neutral photo-service glyph:** avoids copying the wordmark while
  remaining visual; rejected for the same owner preference.
- **Wait for written trademark permission:** lowest-risk route to the requested
  mark; rejected because Terry accepts the risk of proceeding without it.
