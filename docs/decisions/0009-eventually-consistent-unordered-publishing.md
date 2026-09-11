# ADR 0009: Treat multi-photo publishing as eventually consistent and unordered

Date: 2026-08-23

Status: Accepted by Terry on 2026-08-23

## Context

Publishing one new photo crosses the Lightroom Classic rendering engine, the
FGA LrC plug-in's local recovery state, Flickr's upload service, the Lightroom
Classic catalog, the FGA API backend, the FGA database, and asynchronous FGA
group-submission workers. No transaction spans those components. A photo can
therefore be visible on Flickr before its hosted ownership proof or group
intents are committed, and its group additions can complete much later.

The earlier walkthrough fixed a photo order for each Lightroom Classic publish
run. The FGA database actually orders a `(FGA user, Flickr group ID)` partition
only when each intent is durably inserted. If photo A has an ambiguous upload or
handoff while photos B and C remain healthy, preserving A-before-B-before-C
would require either stopping the whole run or reserving hosted sequence before
upload. Both choices add user-visible blocking or distributed coordination for
an ordering requirement the owner does not have.

Terry estimates that the 99th-percentile real workflow is not a multi-photo
publish action at all. He first culls thousands of candidates to roughly 20–30
photos for a Flickr album, then iterates through those survivors one at a time:
edit one photo, choose the groups FGA should try, and publish it before moving
to the next. Multi-photo callback behavior must remain correct, but it must not
drive complexity into this dominant one-photo interaction.

## Decision

Multi-photo publishing **MUST** be treated as eventually consistent, not atomic
or ordered. Terry's liveness requirement is that every requested photo “has to
get there”; relative order is explicitly immaterial.

- Every photo **MUST** progress and report status independently. An ambiguous,
  failed, blocked, or slow photo **MUST NOT** stop another otherwise healthy
  photo merely to preserve batch order.
- The FGA LrC plug-in and hosted components **MUST NOT** silently drop a photo or
  group intent. Each unit of work **MUST** continue toward its intended result
  or reach a durable, truthful state that explains why safe automatic progress
  is impossible and what, if anything, requires Terry's attention. Flickr can
  reject or moderate an operation, so “has to get there” is a liveness and
  accountability requirement, not a false guarantee that every external write
  will succeed.
- For a photo published from an FGA published collection, the intended result
  includes attachment to that collection's one-to-one Flickr album. Album
  attachment **MUST** eventually complete or reach a durable, truthful repair
  state; it need not be atomic with upload and creates no ordering guarantee
  between photos.
- No FGA component **MUST** promise publication order from Lightroom Classic
  selection order, publish callback order, render order, upload order, Flickr
  response order, or hosted-handoff order. The FGA LrC plug-in **MUST NOT**
  reserve backend queue positions before a photo has a durable group intent.
- Each successfully committed group intent still receives the FGA database's
  immutable enqueue value. The FGA group-submission worker **MUST** preserve
  FIFO among active intents already accepted into the same
  `(FGA user, Flickr group ID)` partition. This is an internal courtesy and
  scheduling invariant; it is not a promise that photos from one Lightroom
  Classic publish run reach Flickr or its groups in the photographer's original
  order.
- The FGA LrC plug-in **MUST** expose per-photo intermediate and terminal state
  honestly. “Eventually consistent” does not authorize unsafe replay: upload
  ambiguity, add ambiguity, moderator protection, and permanent suppression
  retain their existing fail-closed rules.
- A publish run **MUST NOT** claim all-or-nothing success or roll back a healthy
  photo because another photo failed. Repair and retry operate only at a stage
  whose existing idempotency and ambiguity rules make that action safe.

## Consequences

- Photo B and photo C may complete upload and durable handoff while photo A is
  still rendering, retrying a safe handoff, awaiting owner attention, or in an
  ambiguous terminal state.
- FGA needs no cross-photo transaction, pre-upload sequence reservation,
  batch-wide rollback, or stop-the-world failure coordinator.
- User-facing progress is a set of per-photo outcomes. A batch-level summary
  may aggregate them but cannot replace or conceal those states.
- The FGA LrC plug-in's primary interaction design should optimize the repeated
  one-photo edit/select-groups/publish loop. Batch-wide controls and ordering
  machinery are secondary and must justify their presence independently.
- The separate questions about the meaning of a Lightroom Classic remote ID
  before hosted proof and the recovery experience after an ambiguous upload
  remain open; this ADR determines that those states do not block later photos.

## Alternatives considered

- **Stop the run at the first uncertain photo:** rejected because one failure
  would wedge Terry's optimized Lightroom Classic workflow without protecting
  data or moderators.
- **Reserve cross-photo order before upload:** rejected because it introduces a
  distributed reservation lifecycle, abandoned-slot repair, and more hosted
  coupling solely to preserve an unwanted ordering promise.
- **Treat the whole publish run as atomic:** impossible across Lightroom
  Classic, Flickr, and hosted FGA components, and misleading even as a user
  interface abstraction because successful Flickr effects cannot be rolled
  back safely as one transaction.
