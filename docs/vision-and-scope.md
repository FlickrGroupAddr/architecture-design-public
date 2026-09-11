# Vision and scope

Last updated: 2026-08-26

Status: Derived product and scope synthesis

Authority: Derived scope synthesis. Accepted scope comes from accepted ADRs and
scoped contracts under the [documentation authority hierarchy](README.md).

## Problem

A Lightroom Classic photographer publishes edited photos to Flickr and then
manually adds each photo to relevant Flickr group pools. Groups independently
limit how many photos a member may submit in a time period. The limit may be as
small as one photo per day or span many months, and Flickr's API does not expose
the group's configured limit or its reset time.

Manual submission is repetitive and makes it difficult to preserve the desired
order when several photos are waiting for the same group.

Before FGA, Terry maintained a spreadsheet to remember which photo/group
requests had not yet succeeded because Flickr throttled them. Automating that
bookkeeping must not turn a personal efficiency tool into repeated work for
Flickr's volunteer moderators. Permanently abandoning an uncertain request is
infinitely preferable to risking a duplicate moderation submission.

The built-in Lightroom Flickr publisher also presents a second limitation for
this workflow: it is oriented around JPEG output. A photographer starting with
a high-resolution RAW file wants the option to upload Lightroom's developed
pixels as a losslessly compressed PNG.

FGA originally began as a backend-centered service with a JAMstack browser
interface. Terry later recognized that an FGA LrC plug-in could keep the two
actual customer jobs inside his already optimized cull/edit/publish loop:
choosing groups without a browser interruption and optionally replacing the
JPEG-only publish path with 8-bit PNG. The product is therefore the in-Lightroom
Classic workflow; hosted components are supporting infrastructure selected only
after that customer experience is understood.

Terry's dominant workflow begins by culling thousands of candidates to roughly
20–30 photos for a Flickr album. He then works through those survivors one at a
time: edit one photo, choose the Flickr groups the FGA group-submission workers
should try to add it to, and publish it before moving to the next. He estimates
this one-photo interaction as the 99th-percentile case. The FGA LrC plug-in
should therefore make that
repeated loop excellent; multi-photo publishing is supported failure behavior,
not the center of the interface.

The album workflow preserves Lightroom Classic's established Flickr-provider
shape. Terry right-clicks the FGA publish service and chooses **Create Album…**,
adds candidates to the resulting album while culling, then uses Lightroom's
native publish controls and status sections for selected work or the album's
pending work today.

That current flow is a required capability baseline, not a compatibility target
for its own sake. Every job Terry performs today is in scope, while every menu,
click, serial step, state presentation, and Adobe-provider limitation is open to
challenge. FGA succeeds by making the one-photo loop materially more efficient;
it may retain, combine, move, or replace current interactions when documented
Lightroom SDK capabilities support a clearer and faster experience.

## Product vision

From Lightroom Classic, the photographer can either choose groups for a newly
edited photo before publishing it to Flickr as an 8-bit PNG or select an
existing public photo in the configured owner's Flickr account to increase its
exposure through additional groups. Existing-photo eligibility does not depend
on which uploader created the photo or on a Lightroom Classic catalog binding.
In both workflows, the photographer chooses the group pools that should
eventually receive the photo. The FGA LrC plug-in uploads only photos in its
original-publisher workflow, the FGA API backend records the selected group
intents durably, and FGA group-submission workers process them without requiring
the Lightroom Classic host process or the photographer's computer to remain
running.

The [existing public Flickr photo intake contract](existing-public-photo-intake.md)
defines the no-upload selector, owner-fixed advisory discovery, fresh hosted
owner/public proof, and common photo-binding handoff. A client Flickr photo ID
is only a lookup key and never authority.

Every FGA published collection corresponds one-to-one with one Flickr album,
and every photo published from that collection must eventually be attached to
that album. Album attachment is a required per-photo outcome, not an atomic
batch boundary or an ordering promise. The FGA LrC plug-in supports ordinary
albums only; it does not offer smart albums or automatic rule-based membership.
Terry chose that as a product boundary because deliberate album membership is
part of his control model.

A multi-photo publish run is eventually consistent, not atomic or ordered.
Every photo progresses independently, and one ambiguous or failed photo does
not stop other healthy photos merely to preserve Lightroom Classic selection,
render, upload, or callback order. Every requested photo must keep progressing
toward its destination or reach a durable, truthful state requiring attention;
none may disappear silently. Per-group FIFO applies only after intents are
durably accepted and is not a promise about publication order.

For each Flickr user and group, the FGA database preserves the photographer's
requested order. The FGA API backend emits at most one immediate partition hint
for a complete client batch, and FGA group-submission workers revisit every
other due queue on a conservative schedule. The
photographer can see whether an intent is queued, retrying, added, submitted for
moderation with final decision unknown, abandoned because delivery is
uncertain, or needs attention.

## Goals

- Integrate with Lightroom Classic's Publish Services workflow.
- Bind each FGA published collection one-to-one with a Flickr album and attach
  every newly published photo to that album through an
  explicit, idempotent, and recoverable workflow.
- Preserve Lightroom Classic's native album creation, publish commands, and
  unpublished/modified/published capabilities unless an explicitly better FGA
  interaction replaces them without losing a current job.
- Queue add-only group intents for existing public photos in the configured
  owner's Flickr account, including photos without a Lightroom Classic catalog
  binding, without rendering, uploading, importing into an FGA published
  collection, moving between albums, replacing, or deleting them.
- Show a fresh Flickr-derived current group-pool view before selecting more
  groups for a photo from either intake path; do not infer current membership
  from FGA's own intent history.
- Keep group-pool management add-only. The FGA API backend never removes a photo
  from a Flickr group, and the FGA LrC plug-in never turns deselection into a
  removal request.
- Render developed RAW images as PNG, with JPEG available as an explicit
  compatibility or size fallback.
- Preserve FIFO ordering among active intents already durably accepted into
  each `(user, group)` pair, without promising cross-photo publication order.
- Permit at most one newly enqueued idle head per client batch to receive an
  immediate hint; recover every other due head through the scheduled sweep.
- Run scheduled retries for every due queue even when the Lightroom Classic
  host process is closed.
- Stop advancing a queue when Flickr reports that the user's group limit has
  been reached.
- Treat successful addition and entry into a moderated group's pending queue as
  successful terminal outcomes.
- Fail polite toward volunteer moderators: perform a fresh moderation-state
  preflight before every group-add write, permanently remember every
  photo/group pair that entered or was already in moderation, and never
  resubmit that pair through FGA.
- Permanently abandon rather than repeat a group-add write whose delivery
  outcome is ambiguous.
- Remain safe across network failures, duplicate delivery, worker crashes, and
  repeated publish callbacks. Repeat a mutating FGA API request only when its
  operation-specific contract is idempotent and the same identity and payload
  are preserved; never replay a direct Flickr image POST after bytes might have
  left the Lightroom Classic host networking stack.
- Keep Flickr credentials and photo metadata appropriately protected.
- Release original FGA source under the MIT license.
- Respect Flickr API limits, terms, privacy requirements, and attribution.

## Non-goals for the first usable version

- Discovering or predicting each group's undocumented limit window.
- Circumventing group limits or moderation.
- Replacing Flickr's website or reproducing its browsing experience.
- Treating catalog association, album membership, pixel replacement, deletion,
  or re-upload as an implicit part of existing-photo group queueing.
- Treating Flickr as storage for Canon CR3/RAW files. Flickr does not accept RAW
  uploads; FGA's PNG is a rendered derivative of the RAW source.
- Mirroring Flickr photos in the FGA API backend or database after upload.
- Supporting Lightroom (cloud), Photoshop, or non-Adobe photo managers.
- Supporting video.
- Supporting smart albums, smart-filter definitions, or automatic
  metadata-driven album membership. This is an ordinary-albums-only product
  decision, not merely an MVP deferral.
- Supporting every feature of Adobe's built-in Flickr publisher before the
  core upload-and-group workflow works.

## Success criteria for an MVP

1. A full-resolution Lightroom-developed photo can be published as PNG to a
   test Flickr account and Flickr reports `originalformat="png"`.
2. The FGA LrC plug-in obtains the resulting Flickr photo ID and durably
   submits the selected group intents, if any, to the FGA API backend. A photo
   with no group additions still completes Flickr publication and required
   album attachment without creating queue work.
3. Two durably accepted intents targeting the same group are attempted in
   insertion order. Photos progress independently before handoff, and no
   Lightroom Classic publish-run order is promised.
4. Flickr error 5 (group submission limit reached) blocks only that user's queue
   for that group until the next scheduled probe.
5. Success, already-in-pool, newly pending moderation, and already pending
   moderation are handled idempotently; moderation results create permanent
   do-not-resubmit records.
6. A crash in an FGA group-submission worker does not lose an intent or produce
   uncontrolled concurrent submissions to the same `(user, group)` queue.
7. The user can inspect current state and understand any request that cannot
   reach a successful terminal state.
8. Every group-add attempt has its own successfully recorded immediately prior
   `ispoolmoderated` observation; an unavailable preflight prevents the write.
9. An ambiguous post-dispatch outcome becomes a permanently abandoned safety
   stop rather than an automatic retry.
10. An existing public photo verified as belonging to the configured Flickr
    identity can enter the same add-only group queues without being rendered or
    uploaded again.

## Product principles

- Prefer observable state over invisible background magic.
- Keep routine photo selection, group selection, publication, and queue status
  inside the FGA LrC plug-in; do not impose a browser context switch for backend
  implementation convenience.
- Let Flickr be authoritative about group eligibility and throttling.
- Never advance later work past a throttled queue head.
- Never trade volunteer moderator workload for higher automated-delivery
  success. A false abandonment is acceptable; a possibly duplicated
  moderation request is not.
- Enforce fail-polite in the FGA API backend, FGA group-submission worker, and
  FGA database against buggy, modified, or hostile clients. Design as though
  Terry may be the volunteer moderator receiving the requests, because he
  intends to volunteer in retirement.
- Do not claim the exact photo/group guard prevents all abuse. Keep public and
  multi-user signup closed until the official FGA API backend and worker
  deployment has conservative per-user/group admission and rate limits,
  monitoring, suspension, and re-registration resistance for distinct-photo
  spam.
- Treat group moderation metadata as a fresh required preflight observation,
  not an atomic guarantee: the authoritative add response may reflect a
  setting change between calls.
- Store intent and identifiers, not copies of the photographer's images, after
  upload.
- Optimize the owner-operated installation for Terry, the only expected
  customer. A public or multi-user offering is a future scope change, not an
  architecture driver to implement speculatively.
- Keep licensed vendor material outside the MIT-licensed source tree.

## Initial deployment assumptions

- The MVP is a private, owner-operated hosted deployment for the project owner,
  using the owner's Flickr application and authorization. Public signup and
  multi-user operation are not MVP constraints.
- Terry **MUST** maintain Flickr Pro membership for FGA's supported lifetime.
  Flickr Pro is the supported account baseline; no free-tier
  compatibility path is required.
- The project-owner-controlled `flickrgroupaddr.com` domain is the selected FGA
  service hostname.
- The initial edge configuration attempts TLS 1.3-or-newer only and is tightened
  to the strongest conventional configuration that the latest Creative Cloud
  LrC release on the owner's adopted latest production/stable Windows release
  and the current administrative browsers can negotiate. Any compatibility
  relaxation requires recorded evidence.
- Lightroom runs on a 64 GB travel laptop. Favor simple, reliable code over
  complexity introduced solely to minimize desktop memory use.
- Processing a complete image in memory is acceptable when it materially
  simplifies the plug-in. This does not require doing so when the platform
  already provides a simpler or more capable external operation.
- An 8-bit/channel final image is acceptable for this workflow. The intended
  audience overwhelmingly uses displays with no more than 8-bit/channel output,
  so preserving a 16-bit/channel Flickr original is not an MVP requirement.
