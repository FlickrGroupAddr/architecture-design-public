# Customer-centered scope discovery and synthesis

Date: 2026-08-23

Status: durable product provenance; accepted decisions are in ADRs 0004 and
0008, while photo replacement remains test-gated research

## Why the project changed shape

FGA began as a backend-centered service with a JAMstack browser interface. That
starting point reflected Terry's professional familiarity with backend systems,
not a settled customer-experience requirement.

During the Claude-era work, Terry realized that not personally knowing Lua was
no longer a product limitation. An FGA LrC plug-in could keep group selection
inside his highly optimized Lightroom Classic cull/edit/publish loop instead of
interrupting it with a browser context switch. The in-Lightroom Classic workflow
therefore became the product center, with hosted components treated as supporting
plumbing rather than the driver of product shape.

After that shift, Terry recognized that a second long-standing customer job
could share the same plug-in and hosted foundation: publish Lightroom
Classic-developed pixels to Flickr as an 8-bit PNG instead of relying on the
JPEG-oriented Adobe Flickr publisher. The two jobs were discovered
incrementally, which explains why the older repository and diagram remained
backend/browser-heavy while later requests pulled them toward a plug-in.

## Why the clean-room track existed

Terry restarted with Codex Sol from himself as the only expected customer and
from the desired Lightroom Classic workflow. The Claude-era artifacts were
withheld until the independent track had developed and reviewed its own
architecture. Disclosure was intended to support an evidence-led comparison,
not forced convergence or maximal reuse.

Any reuse percentage is a successful outcome. Selective adoption means the
comparison found useful prior work; zero adoption would mean the isolated
customer-centered pass successfully avoided importing unsuitable assumptions.
The durable process criterion is recorded in
`2026-08-23-clean-room-comparison-provenance.md`.

## Product jobs now accepted

The single FGA LrC plug-in serves Terry, the only expected customer, through two
explicit workflows:

1. For a newly edited photo, Terry can select desired Flickr groups before
   publication, render and upload an 8-bit PNG to public Flickr, and enqueue the
   selected add-only group intents.
2. For a photo already public in Terry's configured Flickr account, Terry can
   select it later and enqueue additional add-only group intents to increase its
   exposure. Eligibility does not depend on which uploader created the photo or
   whether a Lightroom Classic catalog stores its Flickr binding.

The FGA API backend must verify configured-account ownership and public
visibility. Both workflows use the same queue, fail-polite moderation preflight,
ambiguous-delivery handling, permanent exact-pair suppression, and prohibition
against group removal. Routine operation stays inside the FGA LrC plug-in; a
browser application, public signup, and multi-user service are not current or
latent product requirements.

## Dominant one-photo loop

Terry estimates that the 99th-percentile workflow is one culled photo at a time.
He first reduces thousands of candidates to roughly 20–30 photos intended for a
Flickr album. He then iterates through those survivors in order, editing and
publishing each photo before moving to the next. In the FGA LrC plug-in workflow,
that inner loop becomes: edit one photo, record the groups FGA should try, then
publish.

This customer behavior makes multi-photo ordering machinery especially poor
value. The product still needs honest recovery if Lightroom Classic supplies
multiple photos, but batch controls must not complicate the ordinary one-photo
interaction. Terry then clarified the album invariant: every photo published by
the FGA LrC plug-in will be attached to one Flickr album. He then stated that
the built-in Flickr published collections and Flickr albums have a one-to-one
relationship. FGA therefore preserves that mental model: every FGA published
collection corresponds to one Flickr album, and each photo published from the
collection must eventually be attached there. This is a required per-photo
outcome, not a claim that attachment is atomic with upload or that multiple
photos complete in album order. Ticket #0060 tracks the remaining binding
creation, durable identity, lifecycle, idempotency, and repair contract.

Terry supplied a screenshot of the current built-in Flickr publish service on
2026-08-23. It confirms that the Lightroom Classic Publish Services panel
presents the Flickr service with many published collections and per-collection
photo counts. The screenshot also contains private photo thumbnails, collection
labels, filenames, and metadata, so it is not copied into Git; only this
sanitized structural observation is durable.

Terry also supplied the public albums-page provenance URL
`https://www.flickr.com/photos/terryott/albums/` and explicitly confirmed the
one-to-one correspondence. The browser tool could not open that page because
its URL safety resolver rejected it, so this record attributes the mapping to
Terry and the Lightroom Classic screenshot rather than claiming independent
guest verification. No album names or images are retained here.

Later owner-supplied screenshots established the creation and dispatch
interaction. Terry right-clicks the built-in Flickr publish service, chooses
**Create Album…**, and adds candidate photos to that Lightroom album container
while culling. He edits and publishes the survivors one at a time. The album
context supplies **Publish Now**, while Lightroom shows state-specific
published and modified-to-republish sections and actions. The screenshots also
show **Create Smart Album…**, but Terry has not identified smart albums as
required FGA scope. Only this control structure is retained; the screenshots
remain private and are not copied into Git.

The documented Lightroom SDK provides native terminology, collection-settings,
remote-ID/URL, lifecycle, and publishing-status hooks for this interaction.
Flickr's documented `flickr.photosets.create` method requires a first photo ID,
so the remote album cannot be created at the moment the empty Lightroom album
is created. The recommended flow is to create and cull in the local published
collection, then materialize the Flickr album after the first successful photo
upload. Tickets #0061–#0064 separate first-photo materialization, ambiguous-
write repair, rename/delete behavior, and optional smart-album scope.

Terry then made the governing UX direction explicit: every capability in his
current Adobe Flickr publish-service workflow is in FGA scope, but Adobe's
implementation and interaction design impose no limitation on FGA. The current
flow is evidence and a completeness baseline, not a UI specification. Codex is
directed to challenge it aggressively and recommend fewer clicks, less hidden
state, less waiting, or a better in-Lightroom Classic composition wherever the
documented SDK permits. Ticket #0065 owns the complete current-capability
inventory and optimization review so the design does not overfit only the
screenshots captured in this session.

## Historical-photo quality opportunity

Terry has repeatedly re-edited older RAW-derived photos from scratch after
Lightroom Classic gained materially useful editing capabilities. This creates a
real customer desire to improve a multi-year corpus of already-public photos
without losing the public identity that carries their views, favorites,
comments, URLs, and memberships.

Flickr publishes a binary replacement endpoint that accepts and returns an
existing Flickr photo ID. Terry reports continuous Flickr Pro membership since
2018 and **MUST** maintain it for FGA's supported lifetime. Flickr Pro is
therefore an architecture baseline rather than an optional entitlement, though
the live probe must still verify current availability. Official sources do not
promise preservation of the engagement and membership state Terry cares about,
and current official sources are inconsistent about third-party replacement
support. Photo replacement is therefore a promising hypothesis, not accepted
product behavior.

The first experiment must use a disposable synthetic public photo and must not
touch historical or private photography. Bulk replacement remains prohibited.
Even successful evidence permits only a later, explicit one-photo-first owner
decision and ADR. The exact personal trip, catalog-history, and machine-storage
details motivating this opportunity are retained only in the private localswim
handoff because the public repository's photography-privacy boundary requires a
sanitized rationale.

## Durable work decomposition

The private FGA architecture/design board is the authoritative work queue. This
table is a public-safe map, not a parallel Markdown backlog.

| Ticket | Purpose | Dependency state |
| --- | --- | --- |
| #0050 | Define existing-public-photo discovery, selection, provenance, and backend verification | Parent scope question |
| #0051 | Separate Lightroom Classic publish records, Flickr memberships, and durable public photo identity | Child of #0050 |
| #0052 | Prove whether Flickr replacement preserves the required public photo identity | Child of #0051 |
| #0053 | Spike an in-Lightroom Classic selector for existing public Flickr photos | Child of #0050 |
| #0054 | Build the disposable synthetic public-photo replacement probe | Child of #0052 |
| #0055 | Verify engagement, metadata, URL, album, and group preservation | Blocked by #0054 |
| #0056 | Verify Lightroom Classic publish state after external Flickr replacement | Blocked by #0054 |
| #0057 | Define replacement delivery ambiguity and reconciliation | Blocked by #0054 |
| #0058 | Define verified backup and rollback safeguards | Blocked by #0054 |
| #0059 | Design an explicit one-photo-first historical PNG upgrade workflow | Blocked by #0055 through #0058; bulk use needs a later ADR |
| #0060 | Define the one-to-one FGA published collection/Flickr album binding and its recovery contract | P1 owner-judgment work |
| #0061 | Define first-photo remote Flickr album materialization | Child of #0060 |
| #0062 | Reconcile ambiguous Flickr album creation and attachment writes | Child of #0060; blocked by #0061 |
| #0063 | Define Flickr album rename and deletion semantics | Child of #0060 |
| #0064 | Decide whether smart albums belong in FGA scope | Child of #0060 |
| #0065 | Inventory and improve Terry's complete current Flickr publish workflow | P1 product/CX review |

## Current synthesis result

The clean-room comparison has produced the expected “some but not all” result.
The current architecture adopts the useful existing-photo job, documented
Lightroom SDK evidence, selected credential and circuit-breaker ideas, and the
older repository's evidence discipline. It rejects browser-centered product
scope, speculative public/multi-user machinery, acknowledged moderator
resubmission, fail-open membership handling, and unsafe retries after possible
delivery. That selective outcome is evidence that the isolated customer-first
pass and later reveal both worked as intended.
