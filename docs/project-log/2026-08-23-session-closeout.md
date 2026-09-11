# Completed review and comparison handoff

Date: 2026-08-23

## Why this handoff exists

Terry is intentionally clearing the active LLM context after three days of
architecture work. This document is the cold-start resume point. Chat history is
not required to continue. Read `AGENTS.md`, this handoff, the linked diagram
reveal note, and the current canonical architecture documents before acting.

## Review and repository state

- Terry explicitly approved all eight phases of
  `docs/zero-state-publish-flow.md`. Phase 7 was approved at 09:01:38-04:00 and
  Phase 8 at 09:35:58-04:00; their authoritative private localswim cards are
  completed and the signoffs are committed in the flow.
- The temporary standing instruction to print the current unsigned phase at the
  end of every response was removed in commit `887b6c4`; the walkthrough is
  finished and must not be resumed automatically.
- At the start of this closeout, FGA `main` is clean at `86f3d5b` with 98 commits
  and has no configured Git remote. The pre-disclosure independent-design
  baseline is the first 96 commits, from root `449490b` through `887b6c4`.
- `docs/plugin-service-contract.md` remains prose rather than OpenAPI. OpenAPI
  documentation and an architecture draw.io diagram remain backlog work. No
  production FGA hosted service or production FGA LrC plug-in exists yet.

## Current accepted design baseline

- The FGA LrC plug-in is an original Lightroom Classic publish-service provider,
  not a patch to Adobe's installed Flickr provider. For an unpublished photo it
  snapshots group selections, requests a render from the Lightroom Classic
  rendering engine, preflights the file, and uploads it directly to Flickr.
- The FGA API backend retains Flickr credentials, signs exact upload metadata,
  and never receives image bytes. An image counts as durably in Flickr only when
  the backend successfully queries the exact photo by Flickr photo ID through
  `flickr.photos.getInfo`, verifies the expected owner NSID, and commits that
  observation with the upload binding and group intents.
- The FGA LrC plug-in records a successful Flickr photo ID in local recovery
  state before calling the documented Lightroom SDK's
  `recordPublishedPhotoId`; the Lightroom Classic catalog then holds the remote
  publish ID.
- The private MVP uses one administratively generated, opaque installation
  bearer credential stored by the FGA LrC plug-in in `LrPasswords`. Public or
  multi-user self-service, browser/device pairing, and normal browser
  participation in plug-in activation are explicitly deferred.
- Current Flickr pool membership is advisory and refreshed with documented
  `flickr.photos.getAllContexts` whenever group selection opens for an already
  published photo. FGA behavior is add-only; no FGA component removes a photo
  from a group or interprets deselection as removal.
- Each group-submission partition is an independent FIFO line keyed by
  `(FGA user, Flickr group ID)`. Durable intent rows and history survive terminal
  transitions, while only `queued`, `attempting`, `retrying`, or `throttled`
  intents remain in active FIFO membership.
- Every individual `flickr.groups.pools.add` has an exceptionless fresh
  `flickr.groups.getInfo` preflight. The FGA group-submission worker reserves
  global rate-limit capacity for both calls, permits no unrelated Flickr call or
  token wait between them, uses a monotonic clock, and begins POST dispatch less
  than 1,000 milliseconds after receiving the successful preflight.
- Failed usable preflights retain the same FIFO head and use independently
  selected jitter in inclusive windows of 30–60 seconds, 1–2 minutes, 2–4
  minutes, 4–8 minutes, and 8–15 minutes for the fifth and later consecutive
  failure. Due times are durable and schedulers do not round them to a shared
  boundary.
- Flickr's maximum-added-to-pool result durably throttles only the affected
  `(FGA user, Flickr group ID)` partition, including its observation and
  `next_probe_not_before`, before the worker releases its lease.
- A dispatched add without a durably committed definitive result, or an unknown
  Flickr application code with undocumented side effects, becomes terminal
  `delivery_uncertain` with a permanent exact-pair do-not-resubmit block. A
  retry remains permissible only when the worker durably proves that zero POST
  bytes could have left.
- Flickr pending-queue results also create permanent exact-pair blocks that
  survive all later moderation-state cycles. No FGA API backend, FGA LrC
  plug-in, administrative path, recovery path, or retry-now path may clear or
  bypass them. A later positive membership observation may prove acceptance;
  absence never proves rejection.
- HTTPS connection reuse belongs to the owning standard HTTP stack for the same
  exact origin after complete response consumption. DNS TTL expiry alone does
  not invalidate a live connection; documented closure, framing, protocol,
  timeout, idle, lifetime, or request-count conditions require a new resolved
  connection and TLS handshake.
- Architecture prose must identify the actual FGA and Lightroom Classic actor.
  Plug-in behavior belongs to the FGA LrC plug-in; hosting, rendering, catalog,
  SDK, and networking behavior names the relevant Lightroom Classic component.

## localswim operating and source state

- The authoritative private board is
  `C:\Projects\localswim-state-store\flickgroupaddr\fga-localswim.json`.
  Use `localswim-cli`; never edit the JSON directly while the service is live.
- The board's exact project name is `FGA: Architecture/Design`, its embedded port
  is `8793`, and the service was healthy with autopush state `ok` at closeout.
- The board UI was running clean localswim build `f40b49a` with lowercase
  `localswim` product wordmark. The required FGA write monitor was `running` with
  its 15-second trailing-edge quiet window.
- Parent localswim `main` is clean and synchronized with `origin/main`. Recent
  commits are `ac05a16` (top-align lane header controls), `5388df5` (Windows-safe
  module re-exec), `7383366` (align card starts, split product and board titles,
  and live-update project renames), and `f40b49a` (lowercase wordmark).
- FGA does not vendor localswim, declare it as a project dependency, or contain a
  localswim Git submodule. The installed uv tool is editable from
  `C:\Projects\localswim`, so no FGA rebase is required for localswim UI changes.

## Clean-room reveal and comparison state

Terry disclosed after completing the review that the 96-commit FGA baseline was
an intentional independent design track created without seeing a separate
Claude Opus 5 proposal. The process provenance is in
`2026-08-23-clean-room-comparison-provenance.md`.

Terry then supplied equivalent PNG, PDF, and draw.io exports of Claude's
2026-08-19 architecture diagram under transient `C:\Temp\FGA-Claude`. Exact
artifact names and SHA2-256 hashes, the extracted architecture, provisional
comparison, fairness caveat, and seven unresolved questions are in
`2026-08-23-claude-architecture-diagram-reveal.md`.

The provisional read is that Claude's design optimizes for concrete Cloudflare
deployment and polished browser-assisted, possibly multi-user onboarding. The
independent baseline optimizes for the complete publish lifecycle, private-MVP
activation, durable per-user/group progress, and fail-polite moderator safety.
Both converge on an FGA LrC plug-in, hosted Flickr secrets and OAuth, durable
hosted state, and processing independent of the Lightroom Classic host.

Do not turn a missing box in the one revealed diagram into a claimed defect in
Claude's full design. The diagram references `docs/architecture/DECISIONS.md`
and ADR-18, which have not yet been supplied. Its 32 numbered interactions spend
steps 1–31 on OAuth/device linking and collapse application operations into step
32; supporting records may contain the omitted application semantics.

## Exact resume point

At the beginning of the next session, retrieve the original Claude design
repository from <https://github.com/FlickrGroupAddr/backend-api> and read every
file in that repository in full before resuming the comparison. Terry explicitly
deferred that retrieval and review to the next session; do not treat the diagram
alone as the completed Claude design review.

After the complete repository read, revisit every comment and all seven open
questions in the diagram-reveal note, including `docs/architecture/DECISIONS.md`,
ADR-18, and the queue, retry, Flickr-result, credential-scope, and Lightroom SDK
contracts. Resolve each question from repository evidence where possible and
identify any question that still requires Terry. Understand Claude's design on
its own terms before scoring it against the independent baseline.

Then compare component boundaries, security and privacy, failure semantics,
operational complexity, implementation complexity, independent convergence,
genuine divergence, and ideas each design exposes as missing or weaker in the
other. Keep pre-disclosure convergence separate from post-disclosure synthesis.
Use no home-team scoring and record every accepted synthesis or design change in
the appropriate canonical architecture document or ADR.

## Resume task completed

The requested Claude repository documentation review was completed on
2026-08-23 against commit `ea407553704aa7a950c341653b0e7d21073f271f` after
Terry narrowed the complete-read scope to documentation. All 50 in-scope files
were reconciled and reviewed; narrowly named implementation files were
spot-checked only to resolve ambiguous-delivery persistence semantics.

The durable result is
[`../research/claude-design-repository-review.md`](../research/claude-design-repository-review.md).
It supersedes the exact resume point above while preserving that section as the
handoff that led to the review. The next conversation should begin with the
remaining owner question about whether Internet-facing multi-user self-service
was an actual requirement, then discuss the four material design differences:
publish-provider versus companion scope, permanent moderator protection versus
acknowledged resubmission, fresh per-add moderation preflight, and public abuse
controls.

The reviewed source history was rewritten for privacy on 2026-08-24 under
#0013 and #0014. Commit `26b7070cb1092bb9fbac045ddd845884f6aa9ea4` is the
public-safe successor for every unaffected current-tree blob; the pinned
identifier above remains only as historical review provenance.
