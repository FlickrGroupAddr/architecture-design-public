# ADR 0007: Fail polite after moderation or an ambiguous group submission

Date: 2026-08-21

Amended: 2026-08-22 to make FGA group-pool management explicitly add-only and
require fresh Flickr-derived membership display.

Amended: 2026-08-26 to require a strict attempt-scoped membership read before
the moderation preflight and to fail closed when that read is unavailable.

Status: Accepted

## Context

FGA exists to submit a photographer's photos to Flickr group pools without
turning automation into work or harassment for volunteer group moderators.
This social boundary is more important than maximizing automatic delivery.
Terry names the requirement **fail-polite**: FGA must not unknowingly submit the
same Flickr photo/group pair to a volunteer moderation queue more than once.

Terry previously maintained a spreadsheet of photo/group requests that had not
yet succeeded because of Flickr throttling. FGA automates that bookkeeping; it
must not convert the convenience into a burden on the volunteer community.
Terry explicitly ranks permanent abandonment of an uncertain request as
infinitely preferable to risking another moderation event.

Terry may volunteer as a Flickr group moderator in retirement. FGA must protect
him in that role just as it protects every other moderator; being the system's
creator or customer does not make the submitting client trusted. The official
hosted service must not offer a mechanism that a buggy, modified, or hostile
client can weaponize against the community.

`flickr.groups.pools.add` reports method-specific application results inside
the Flickr response body. “Photo added to the pool's pending queue” (code `6`)
means Flickr placed the photo in that queue. “Photo already in the pool's
pending queue” (code `7`) means that photo was already there. Both are
definitive evidence that the photo/group pair reached moderation, even though
Flickr represents them as `stat="fail"` results rather than the empty
`stat="ok"` response used for a direct pool addition.

Flickr documents `ispoolmoderated` on `flickr.groups.getInfo`, but group owners
may change moderation at any time. Terry requires a fresh `getInfo` call before
every individual add attempt so entry into a known moderated queue is never an
uninformed operation. The value remains only a dated observation: because the
metadata GET and group-add POST are separate operations, it cannot predict an
atomic future state or make a later retry safe.

As of 2026-08-21, Flickr documents no submitter-facing API that reports whether
a pending photo remains queued or was rejected. A documented pool-membership
query can later prove acceptance when the photo appears in the pool. Continued
absence cannot distinguish pending review from rejection. FGA will not depend
on undocumented administrator methods or screen scraping to cross that
boundary.

The high-impact lifetime case is easy to miss. A volunteer moderator may place
a group into moderated mode, take a multi-month break while the group becomes
unmoderated, then return and place it into moderated mode again. The same person
may remember rejecting the same photo months earlier. A present-day
`ispoolmoderated="0"` observation therefore cannot erase the historical fact
that the exact photo/group pair once reached a moderation queue. Time and an
intervening unmoderated period provide no safe resubmission signal.

There is a second ambiguity after the FGA group-submission worker commits
`dispatch_started`. If no durable record proves that zero add-POST request bytes
could have left the worker and the response is lost or the worker crashes, the
original call could have entered moderation. Automatically repeating that call
could resubmit a photo that a moderator already rejected between attempts.
Flickr's operation has no FGA-supplied idempotency key that closes this gap.

Flickr also cannot atomically commit its response into FGA's database. A worker
can receive “photo added to the pool's pending queue” (code `6`) and fail before
durably recording that exact status. The unresolved `dispatch_started` marker
and absence of durable zero-byte proof require the FGA group-submission worker's
recovery path to preserve the safety guarantee with a permanent
`delivery_uncertain` block even when the more precise historical label is lost.

The provider-neutral implementation supplement is the
[worker persistence and scheduler contract](../worker-persistence-scheduler-contract.md)
and ADR 0015. It gives immediate hints, scheduled sweeps, and recovery
one database-fenced claim path; defines marker-before-POST as a
structural invariant; and makes a post-add result-persistence failure terminally
blocked rather than automatically pending again.

## Decision

FGA policy treats both confirmed moderation and group-add attempts meeting the
explicit `delivery_uncertain` predicates as permanent do-not-resubmit facts for
that exact `(Flickr photo ID, Flickr group ID)` pair.

1. Before every possible individual `flickr.groups.pools.add` attempt, the
   worker calls `flickr.photos.getAllContexts` for the exact photo and applies
   the complete strict membership-response contract. A cached selector or
   worker observation is not authority. If the observation is unavailable, the
   FGA group-submission worker sends neither `getInfo` nor add and retries the
   safe read later from the same FIFO head. If the target group is present, the
   FGA database terminalizes the intent as `added` with source
   `pre_add_membership_observation`, and the worker sends no later Flickr
   operation. Only a complete target-absent observation continues.
   Before this read, the worker atomically reserves global rate-limit capacity
   for the membership GET, moderation GET, and possible add POST; it never waits
   for rate capacity between them and releases proven-unused capacity exactly
   once.
2. After a complete target-absent membership observation, the worker calls
   `flickr.groups.getInfo` for that group. It records `ispoolmoderated`, the
   observation time, and the source attempt. A cached value does not satisfy
   this precondition. If the metadata call fails or omits an interpretable
   moderation value, the worker sends no add request and retries the safe read
   later.
   This preflight is an exceptionless protocol invariant: automatic workers,
   manual actions, recovery tools, tests, and administrators all obey it.
   The worker uses monotonic elapsed time and begins dispatching the add POST
   less than 1,000 milliseconds after receiving the successful preflight response. If
   durable recording or scheduling consumes that window, it discards the
   observation and performs another GET. It checks immediately before and
   after committing the dispatch marker. A live worker that still knows no
   bytes were sent can record `not_dispatched_preflight_expired` and read again;
   an unresolved marker after a crash fails closed as `delivery_uncertain`.
3. After a successful preflight and before sending
   `flickr.groups.pools.add`, the worker durably records the write attempt in a
   dispatch-started state. A crash recovery path never assumes that an attempt
   left in that state was unsent.
4. Flickr's “photo added to the pool's pending queue” status (code `6`) or
   “photo already in the pool's pending queue” status (code `7`) atomically
   creates or confirms a permanent photo/group submission block and places the
   intent in terminal `moderation_submitted` state. The block records the first
   observation time, Flickr status and code, and source attempt. It is never
   cleared by an ordinary state transition, retry, reconciliation,
   cancellation, or retention job.
   It also survives every later moderated/unmoderated transition and any
   elapsed interval; a fresh unmoderated observation never clears or bypasses
   it.
5. If “photo added to the pool's pending queue” (code `6`) follows a preflight
   that reported `ispoolmoderated="0"`, FGA records a moderation-setting race or
   upstream inconsistency for operator visibility. It still applies the same
   permanent block and never retries. FGA cannot guarantee that this
   contradiction never occurs because Flickr exposes no operation that reads
   moderation state and adds the photo atomically.
6. An attempt receives a permanent block with reason `delivery_uncertain` and
   enters terminal `delivery_uncertain` state in either of two cases: a durable
   `dispatch_started` marker exists, no durable record proves that zero add-POST
   request bytes could have left the FGA group-submission worker, and no
   definitive documented Flickr result was durably committed; or Flickr
   returned an unknown application code whose side effects are undocumented.
   The first case includes a worker crash after `dispatch_started`; a network
   exception, timeout, or cancellation after the POST was handed to the HTTP
   stack; a missing, truncated, or unparseable response; and a crash or database
   failure after receipt but before durable result classification. No FGA
   component retries the pair. An unknown code could represent a new
   side-effecting moderation outcome and therefore fails closed.
7. Failures accompanied by durable proof that zero add-POST request bytes could
   have left the FGA group-submission worker—such as DNS resolution, TCP
   connection, or TLS-handshake failure—remain retryable and do not create a
   permanent block.
   Flickr's explicit “service currently unavailable” (code `105`) and “write
   operation failed due to a temporary issue” (code `106`) statuses remain
   retryable because the documented Flickr contract classifies them as
   temporary failures.
8. Every ordinary handoff, scheduled worker, and crash-recovery path checks the
   existing intent and permanent block before making a Flickr call. ADR 0034
   exposes no retry-now operation. A repeated handoff returns the existing
   state and performs no
   outbound write.
9. A later positive observation that the photo belongs to the pool may record
   `observed_in_pool_at` and display that acceptance was observed. It never
   erases the moderation or uncertain-delivery fact. Absence from the pool
   never becomes evidence of rejection and never makes resubmission safe.
10. The mandatory preflight observation may also be cached for display and
   diagnosis, but it never selects a retry policy, clears a block, or overrides
   the authoritative add result. A later attempt always performs a new
   preflight.
11. Permanent means excluded from ordinary history pruning and retained for as
   long as FGA retains the user's operational data. A deliberate account-
   erasure operation may remove it only while clearly warning that FGA's
   resubmission protection will also be lost.
12. FGA exposes no force-resubmit operation for a blocked pair. If Terry
   consciously chooses to resubmit, he logs into Flickr and performs that act
   manually in Flickr's own UI. FGA neither automates nor facilitates it. A
   warning followed by an FGA write is not an acceptable substitute for the
   block.
13. The hosted worker obtains membership and moderation metadata itself. It
    never trusts client-supplied membership or moderation values. The hosted
    service and database enforce
   block uniqueness and write suppression, and no ordinary API can clear or
   replace a block.
14. FGA's pool-management surface is add-only. It can read fresh current pool
    membership with `flickr.photos.getAllContexts`, but it never calls
    `flickr.groups.pools.remove`, offers no group-removal control, and does not
    interpret deselection as removal. Flickr and other clients may add or remove
    memberships independently; FGA displays the fresh observation without
    treating it as permission to repeat an existing photo/group intent or clear
    a permanent block. The FGA API backend publishes that observation only
    after validating the complete successful upstream shape and every pool
    entry. Missing, non-array, partial, or uninterpretable pool data remains
    unknown; it is never filtered or defaulted to an empty membership list.

This terminal classification describes completion of FGA's submission duty,
not a claim that the group accepted the photo. User-facing wording is
"submitted for moderation; final decision unknown" rather than "currently
pending," because rejection is silent and the queue is opaque to FGA.

## Accepted non-atomic race

Codex explicitly cautioned that separate Flickr GET and POST operations cannot
provide an atomic moderation-state guarantee. FGA can bound only its local
interval from receipt of the metadata response to start of POST dispatch; it
cannot bound network delay, Flickr's request scheduling, or the instant at
which Flickr reads the moderation setting.

On 2026-08-21, Terry accepted that residual race without reservation. His
justification is that FGA performs the fresh check before every single request,
enforces a sub-second FGA-controlled window, and therefore does the best the
documented Flickr API permits. A moderation flip at the worst possible instant
is an upstream limitation, not an excuse to weaken the preflight or pretend the
two calls are atomic. Terry considers that best-effort residual risk consistent
with responsible participation in the Flickr community.

## Consequences

- Moderator courtesy wins over automatic liveness. Some requests that never
  reached Flickr will be suppressed after an ambiguous post-dispatch failure.
- “Photo already in the pool's pending queue” (code `7`) protects pairs first
  submitted manually or by another integration; FGA adopts the already-pending
  fact and never calls the add method again.
- The append-only attempt history remains useful for diagnosis, but retention
  of attempts is not the safety mechanism; the permanent photo/group block is.
- A crash between receiving “photo added to the pool's pending queue” (code
  `6`) or “photo already in the pool's pending queue” (code `7`) and persisting
  it can degrade the recorded reason to `delivery_uncertain`. The permanent
  block remains correct and deliberately favors a conservative superset over
  exact telemetry.
- Current pool membership and historical moderation submission are orthogonal
  facts. The UI can show later acceptance without forgetting the reason FGA
  must never resubmit automatically.
- Current membership is read fresh from Flickr when the selector opens because
  non-FGA actors can change it. The observation can become stale immediately,
  and FGA never attempts to reverse an external removal.
- Dynamic group moderation does not create races in FGA policy because the
  current add response remains authoritative even when it contradicts the
  mandatory immediately preceding metadata observation.
- Every add now costs three Flickr API calls: the membership GET, moderation
  GET, and write POST all count against FGA's global API-key budget. An existing
  membership costs only its completed GET and avoids the other operations.
- Slow local work can cause repeated metadata reads before one write because an
  observation that reaches 1,000 milliseconds cannot be used. This is expected
  safety behavior, not a reason to extend or bypass the deadline.
- Exact safety applies to Flickr's identifiers. Reuploading the same pixels as
  a new Flickr photo creates a different photo ID and therefore a different
  pair; FGA does not infer image identity from content.
- Exact-pair suppression is not a complete anti-abuse system. A hostile user
  can create many different photo IDs, and an MIT-licensed fork can remove
  safeguards while using infrastructure outside FGA's control. The official
  hosted service will not open public or multi-user signup until a separate
  threat model defines conservative per-user/group admission and rate limits,
  monitoring, suspension, and re-registration resistance.
- A future multi-user service needs a privacy-compatible policy for account
  erasure and later re-registration. Deleting every block and immediately
  accepting the same Flickr identity again could become a guard-reset path;
  that policy must be resolved before public signup.

## Required conformance gate

The [fail-polite worker/database conformance suite](../testing/fail-polite-worker-database-conformance.md)
defines the production database topology, stable scenario IDs, exact monotonic
boundary cases, process-crash matrix, bypass attempts, and mutation evidence
required before a release capable of `flickr.groups.pools.add` may deploy. The
suite must exercise the production worker path and migrations against the
selected database engine; a reference model, mocked repository, or skipped test
does not establish conformance. No executable pass exists while this
architecture repository has no production worker or database implementation.

## Rejected alternatives

- **Retry an ambiguous POST until Flickr returns already-in-pool or already-
  pending:** rejected because a moderator can reject the first submission
  before the retry, causing a second moderation event.
- **Use `ispoolmoderated` to decide whether retry is safe:** rejected because
  the setting is dynamic and any observation can be stale before the write.
- **Promise that the preflight and add observe one atomic moderation state:**
  rejected as impossible with Flickr's two documented operations. FGA records
  and surfaces a contradiction instead of hiding it.
- **Infer rejection after a timeout or a period of pool absence:** rejected
  because Flickr exposes no documented submitter-visible distinction between
  still pending and rejected.
- **Query an undocumented moderation endpoint or scrape Flickr pages:**
  rejected because it violates FGA's documented-API boundary and creates a
  fragile dependency.
- **Keep only expiring attempt logs:** rejected because routine retention would
  eventually erase the exact safety fact needed to protect moderators.

## Official Flickr sources

- [`flickr.groups.pools.add`](https://www.flickr.com/services/api/flickr.groups.pools.add.html)
- [`flickr.groups.getInfo`](https://www.flickr.com/services/api/flickr.groups.getInfo.html)
- [Flickr REST response format](https://www.flickr.com/services/api/response.rest.html)
- [Flickr API method index](https://www.flickr.com/services/api/)
- [`flickr.groups.pools.getPhotos`](https://www.flickr.com/services/api/flickr.groups.pools.getPhotos.html)
- [`flickr.photos.getAllContexts`](https://www.flickr.com/services/api/flickr.photos.getAllContexts.htm)
- [`flickr.groups.pools.remove`](https://www.flickr.com/services/api/flickr.groups.pools.remove.html)
