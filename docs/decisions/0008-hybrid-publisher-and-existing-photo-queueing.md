# ADR 0008: Combine original publishing with existing-photo queueing

Date: 2026-08-23

Status: Accepted

## Context

ADR 0001 selected an original FGA LrC publish provider because Adobe's
JPEG-oriented Flickr publisher cannot satisfy the PNG requirement. Its original
scope treated compatibility with photos uploaded through another publisher as
possible later work.

FGA began as a backend-centered service with a JAMstack browser interface. That
shape reflected Terry's backend-development instincts, not the best customer
experience. During the Claude-era design, Terry recognized that unfamiliarity
with Lua was no longer a product constraint: an FGA LrC plug-in could keep group
selection inside his highly optimized Lightroom Classic cull/edit/publish loop
instead of interrupting it with a browser. He then recognized that the 8-bit PNG
publishing improvement he had wanted since 2021 could share that plug-in and
hosted foundation. The later clean-room effort intentionally restarted from
these customer jobs and deferred backend shape until the workflow required it.

On 2026-08-23, Terry clarified that one FGA LrC plug-in has two primary jobs:

1. publish Lightroom Classic-developed photos to Flickr as 8-bit PNG because
   that output is higher quality than his current JPEG-only publish path; and
2. submit add-only group intents to the FGA API backend for both photos
   published by the FGA LrC plug-in and photos published through another path.

The second job is not merely migration or future compatibility. It is part of
the intended product scope.

Terry then clarified that “existing photo” means a photo already published
publicly in his Flickr account. Eligibility does not depend on which uploader or
Lightroom Classic publish service created it, or on whether a Lightroom Classic
catalog currently stores its Flickr photo ID. Newly edited photos may receive
their group selections before the FGA LrC plug-in publishes them; existing
public photos may be selected later to increase their exposure through the same
add-only queues.

## Decision

Build one hybrid FGA LrC plug-in with two explicit photo-intake paths:

- The original-publisher path renders an 8-bit PNG, uploads it directly to
  Flickr under the accepted service-signing boundary, records the returned
  Flickr photo ID, and submits zero or more selected group intents. ADR 0010
  makes group additions optional for this publication path.
- The existing-photo path accepts a photo already public in the configured
  owner's Flickr account, regardless of its upload provenance, does not render
  or upload it again, and submits selected group intents for the existing Flickr
  photo ID.

Both paths feed the same FGA API backend, FGA database, and FGA
group-submission worker. The existing-photo path is subject to the same add-only,
fresh-membership, fail-polite moderation-preflight, FIFO, ambiguous-delivery,
and permanent exact-pair suppression rules as the original-publisher path. No
FGA component may turn the existing-photo path into a group-removal feature.

Treat the in-Lightroom Classic customer experience as the product center. The
FGA API backend, FGA database, and FGA workers exist to preserve and continue
that workflow; their implementation convenience must not force routine photo or
group work into a browser.

ADR 0021 and the existing-public-photo intake contract now define how
the FGA LrC plug-in discovers and presents those photos, and how the FGA API
backend freshly proves exact owner/public state before creating or refreshing a
server photo binding. The client photo ID is only a lookup key; group admission
uses the server binding. Ticket #0053 may refine the in-Lightroom Classic
presentation without changing that authority boundary.

ADR 0022 separates Lightroom Classic catalog photos,
provider/collection-scoped published-photo records, Flickr album membership,
Flickr photo identity, and the FGA hosted binding. Queue-only intake creates no
catalog record or Flickr album/pixel/deletion write. A possible catalog-only
FGA association is not migration. Disposable-catalog ticket #0067 proved its
visible and callback behavior. ADR 0038 reviews that evidence and keeps
the association out of product scope because the queue-only path already meets
the customer requirement without duplicate provider state or a surprising
republish/removal lifecycle.

Flickr separately publishes a binary photo-replacement endpoint that accepts an
existing Flickr photo ID and returns that same ID. That makes an in-place PNG
upgrade of an older public photo plausible, but it is not accepted by this ADR.
Flickr's official contract does not promise preservation of engagement,
memberships, metadata, URLs, or rollback, and current official sources disagree
about whether third-party API replacement remains supported. The bounded,
non-sensitive live experiment and owner decision tracked by FGA localswim ticket
#0052 must succeed before replacement enters product scope. Bulk historical
replacement is prohibited unless a later ADR accepts its safeguards and blast
radius explicitly.

Terry **MUST** maintain Flickr Pro membership for FGA's supported lifetime. The
architecture may therefore require
the Pro account tier and does not need a free-tier replacement fallback. The
live replacement path must still detect and report an unavailable entitlement
without attempting a destructive workaround.

## Consequences

- ADR 0001's original publish-provider decision remains in force for PNG
  publication; this ADR extends rather than replaces it.
- Every FGA published collection corresponds one-to-one with one Flickr album,
  and every photo published from that collection must eventually be attached to
  that album. Album attachment is a required per-photo outcome, not an atomic
  batch boundary or publication-order guarantee. Ticket #0060 defines binding
  creation, durable identity, lifecycle, idempotency, and repair.
- Existing public Flickr photos are first-class queueing inputs, including
  photos not uploaded by the FGA LrC plug-in and photos without a Lightroom
  Classic publish-service binding.
- The FGA LrC plug-in needs an explicit user workflow that distinguishes
  publish-and-queue from queue-existing-photo so it never surprises the
  photographer with an upload or re-upload.
- The FGA API backend must verify ownership and public visibility for an
  existing Flickr photo rather than trusting an arbitrary client-supplied photo
  ID.
- Detailed zero-state publishing phases remain authoritative for the
  original-publisher path. The separate existing-public-photo intake contract
  defines the second path through convergence on a common server photo binding.
- The non-destructive existing-photo boundary forbids treating catalog
  association, Flickr album membership, pixel replacement, deletion, or
  re-upload as implicit parts of group queueing.

## Alternatives considered

- **Original publisher only:** rejected because it omits the explicitly required
  ability to queue photos published through another path.
- **Companion only:** rejected because it cannot deliver the required 8-bit PNG
  publishing improvement.
- **Separate publisher and companion plug-ins:** not selected. One plug-in with
  two explicit workflows keeps shared credentials, group selection, recovery,
  and queue-status behavior in one user-visible component without conflating
  the two intake paths.
