# Group-submission status API contract

Last updated: 2026-09-05

Status: Accepted wire and presentation contract under ADR 0034; executable
implementation evidence remains pending in the future hosted repository

Authority: Accepted normative contract under ADR 0034. It is accepted policy,
but it is not executable evidence.

## Purpose and boundary

The FGA LrC plug-in must show what happened after the FGA API backend accepted
a durable group-submission batch. `202 Accepted` means only that intent rows
committed; it does not mean Flickr added the photo, accepted a moderation
submission, or even received a write.

The status surface is a read model over authoritative FGA database intent,
partition, gate, outcome, and permanent-block records. It does not implement a
second queue, store a client cursor, start a worker, refresh Flickr, estimate
completion, clear a write gate, reopen a terminal intent, or authorize another
group submission. The decision is recorded by
[ADR 0034](decisions/0034-expose-read-only-group-submission-status.md).
The closed copy/action projection shared with group selection is defined by the
[moderator-safety UI conformance contract](moderator-safety-ui-conformance.md).

## Routes and authentication

The current `lrc_plugin` installation credential gains these exact read routes:

| Method | Path | Meaning |
| --- | --- | --- |
| `GET` | `/api/v001/group-submission-intents` | Read one filtered, bounded page of the authenticated FGA user's intents plus a queue/gate summary |
| `GET` | `/api/v001/group-submission-intents/{submissionIntentId}` | Read the authenticated FGA user's current representation of one intent |

The FGA administrative control plane gains equivalent browser-session reads:

| Method | Path | Meaning |
| --- | --- | --- |
| `GET` | `/api/v001/admin/group-submission-intents` | Read the private deployment owner's filtered status page and summary |
| `GET` | `/api/v001/admin/group-submission-intents/{submissionIntentId}` | Read one current intent representation |

The private MVP has one linked FGA user, but both route families still scope the
query through authenticated identity. A syntactically valid missing or foreign
intent ID returns the same non-oracular `404 Not Found`; no response reveals
whether another user owns it. A current installation credential cannot
use the administrative routes, and an administrative session cannot use the
plug-in routes. An unexpired `pending_rotation` credential remains limited to
the current-installation read and receives `403 insufficient_scope` here.

Every response is JSON with `Cache-Control: no-store`. A status read may append
a coalesced access observation or sanitized metric, but it performs no domain
mutation and no Flickr or identity-provider call. `POST`, `PUT`, `PATCH`, and
`DELETE` are not status operations. The registered collections/items return
server-owned `405 Method Not Allowed`; guessed `/retry`, `/retry-now`,
`/reopen`, `/force`, `/clear-block`, and `/cancel` subpaths are unregistered
server-owned `404` responses and never reach an administrative shell.

## Collection query

The collection accepts only these query parameters:

| Parameter | Rule |
| --- | --- |
| `view` | Optional; `active` by default, or exact `attention` or `history` |
| `photo_binding_id` | Optional opaque FGA photo-binding ID owned by the authenticated user |
| `page_size` | Optional integer from 1 through 100; default `50` |
| `before_created_at` | Optional keyset boundary; exact RFC 3339 UTC timestamp with six fractional digits returned by the preceding page |
| `before_intent_id` | Optional keyset boundary; exact opaque intent ID returned by the preceding page |

Unknown, repeated, empty, differently cased, malformed, or unsupported query
parameters return `400 invalid_status_query` with no rows. The two keyset
parameters are required together; a missing or malformed half returns
`400 invalid_status_continuation`. A conforming continuation repeats the same
`view`, `photo_binding_id` presence/value, and normalized `page_size` returned
by the preceding page. The boundary is deliberately stateless, so changing a
valid filter creates a different bounded query rather than invoking hidden
cursor state or additional authority.

The views are exact server concepts:

- `active` contains only `queued`, `attempting`, `retrying`, and `throttled`;
- `attention` contains only terminal `needs_attention` and
  `delivery_uncertain`; and
- `history` contains every retained intent state, including active and terminal
  rows.

A paused write gate does not rewrite an active intent into `attention`.
Applicable gate holds appear in that active intent's queue projection and in the
page summary. `moderation_submitted` is a completed FGA action, not an attention
state or proof of later moderator acceptance/rejection.

Rows use immutable descending `(created_at, submission_intent_id)` order. A
continuation selects only keys strictly less than the returned pair. This is an
ordinary stateless keyset, not a random bearer cursor or retained generation.
New rows appear before an existing traversal, and state may change between page
requests. The response is an operational observation, not an audit snapshot;
the FGA LrC plug-in starts from the initial page whenever the user refreshes.
The `history` traversal is membership-stable because retained intents are not
deleted and its filter includes every state. The `active` view may lose a row
that terminalizes between pages, which is truthful progress rather than a reason
to retain snapshot generations.

The FGA API backend resolves the optional photo binding through the authenticated
user and returns the same non-oracular `404` for a missing or foreign binding.
The filter never accepts a client Flickr photo ID, group ID, user ID, state list,
sort expression, arbitrary SQL fragment, or include-secret/debug option.

## Collection response

One repeatable-read FGA database transaction obtains database `observedAt`, the
summary counts, applicable current gate projections, and page rows. It takes no
worker/partition lock and can become stale immediately after commit. The exact
shape is:

```json
{
  "schemaVersion": 1,
  "observedAt": "2026-08-26T18:14:22.123456Z",
  "view": "active",
  "pageSize": 50,
  "photoBindingId": null,
  "summary": {
    "activeIntentCount": 3,
    "activePartitionCount": 2,
    "attentionIntentCount": 1,
    "oldestActiveEnqueuedAt": "2026-08-26T17:02:11.000001Z",
    "writeGates": [
      {
        "scope": "user",
        "state": "enabled",
        "revision": 4,
        "pausedAt": null,
        "reasonCode": null,
        "affectedActiveIntentCount": 0
      },
      {
        "scope": "deployment",
        "state": "enabled",
        "revision": 2,
        "pausedAt": null,
        "reasonCode": null,
        "affectedActiveIntentCount": 0
      }
    ]
  },
  "intents": [
    {
      "fgaSubmissionIntentId": "server-generated-intent-id",
      "fgaPhotoBindingId": "server-generated-binding-id",
      "flickrPhotoId": "example-flickr-photo-id",
      "flickrGroupId": "example-group-id",
      "groupDisplayName": "Example group",
      "groupDisplayNameObservedAt": "2026-08-26T17:00:00.000000Z",
      "state": "retrying",
      "stateRevision": 4,
      "createdAt": "2026-08-26T17:02:11.000001Z",
      "stateChangedAt": "2026-08-26T18:10:00.000000Z",
      "terminalAt": null,
      "attemptCount": 2,
      "queue": {
        "isPartitionHead": true,
        "activeAheadInPartition": 0,
        "nextWorkNotBefore": "2026-08-26T18:15:00.000000Z",
        "holds": []
      },
      "lastOutcome": {
        "reasonCode": "temporary_flickr_failure",
        "flickrResultCode": 105,
        "observedAt": "2026-08-26T18:10:00.000000Z",
        "correlationId": "server-generated-correlation-id"
      },
      "permanentSubmissionBlock": null,
      "attention": null
    }
  ],
  "nextPage": {
    "beforeCreatedAt": "2026-08-26T17:02:11.000001Z",
    "beforeIntentId": "server-generated-intent-id"
  },
  "recommendedPollAfterSeconds": 15
}
```

An empty page has `intents: []`. `nextPage` is `null` when no older matching row
exists. `photoBindingId` echoes the validated opaque filter or is `null`.
`pageSize` is the normalized bound used for this response.
`oldestActiveEnqueuedAt` is `null` when the authenticated scope has no active
intent. Counts describe the complete authenticated scope, not just the returned
page; `attentionIntentCount` is the sum of current `needs_attention` and
`delivery_uncertain` rows.

The two initial gate projections appear in deterministic `user`, `deployment`
order. A paused projection contains its database pause time, allowlisted
sanitized reason code, and affected active-intent count. It contains no gate ID,
Flickr token state, secret identifier, raw upstream message, signer detail, or
repair control. The administrative
`GET /api/v001/admin/flickr-write-gates` resource remains the authority for
review and verified resume.

`recommendedPollAfterSeconds` is `15` when any matching returned or summary
intent is active and neither gate is paused, `60` when an applicable gate is
paused, and `null` when no matching active intent exists. It is a minimum client
poll interval, not a promise that progress occurs by that time.

## Intent representation

The item route returns:

```json
{
  "schemaVersion": 1,
  "observedAt": "2026-08-26T18:14:22.123456Z",
  "intent": {
    "fgaSubmissionIntentId": "server-generated-intent-id",
    "fgaPhotoBindingId": "server-generated-binding-id",
    "flickrPhotoId": "example-flickr-photo-id",
    "flickrGroupId": "example-group-id",
    "groupDisplayName": "Example group",
    "groupDisplayNameObservedAt": "2026-08-26T17:00:00.000000Z",
    "state": "delivery_uncertain",
    "stateRevision": 5,
    "createdAt": "2026-08-26T17:02:11.000001Z",
    "stateChangedAt": "2026-08-26T18:12:00.000000Z",
    "terminalAt": "2026-08-26T18:12:00.000000Z",
    "attemptCount": 2,
    "queue": null,
    "lastOutcome": {
      "reasonCode": "post_dispatch_result_unavailable",
      "flickrResultCode": null,
      "observedAt": "2026-08-26T18:12:00.000000Z",
      "correlationId": "server-generated-correlation-id"
    },
    "permanentSubmissionBlock": {
      "reasonCode": "delivery_uncertain",
      "createdAt": "2026-08-26T18:12:00.000000Z"
    },
    "attention": {
      "kind": "delivery_uncertain",
      "reasonCode": "post_dispatch_result_unavailable",
      "occurredAt": "2026-08-26T18:12:00.000000Z",
      "operatorAction": "inspect_flickr_no_fga_resubmit",
      "fgaResubmissionAllowed": false
    }
  },
  "writeGates": [],
  "recommendedPollAfterSeconds": null
}
```

The collection and item routes use the same intent object. Fields are governed
as follows:

| Field | Contract |
| --- | --- |
| Identity | Intent, binding, Flickr photo, and Flickr group IDs are exact immutable identifiers already authorized for this FGA user; no catalog ID or title is stored or returned |
| Group display | `groupDisplayName` and its observation time are optional advisory values from the last complete reduced group snapshot; absence is `null`, never a fabricated ID-as-name |
| State | `state` is the exact durable enum; `stateRevision` increases on every state/projection-relevant intent mutation; clients do not infer a hidden state from text |
| Time | UTC database timestamps use RFC 3339 with six fractional digits; an inapplicable value is JSON `null`, not missing or an empty string |
| Attempts | `attemptCount` counts committed attempts under the persistence contract; it is not a retry allowance or proof of Flickr receipt |
| Queue | Present only for an active state; its head/ahead count and `nextWorkNotBefore` are advisory at `observedAt`, apply only within that Flickr-group partition, and never form a cross-group rank or ETA; the time is the effective database lower bound for a head and is `null` for a non-head or an attempt already in progress |
| Holds | A sorted array containing zero or more of exact `user_flickr_write_gate_paused` and `deployment_flickr_write_gate_paused`; a hold does not mutate intent state or due time |
| Outcome | The latest allowlisted reason, numeric Flickr application code when one was completely parsed, observation time, and non-secret correlation ID; no raw Flickr/body/exception text |
| Block | Present only when the exact-pair permanent block exists; the FGA API backend joins the insert-only `submission_blocks` row by server-derived photo/group identity rather than inferring it from state or attempt history, and it never contains a delete/clear token, expiry, or resubmit authority |
| Attention | Present only for `needs_attention` or `delivery_uncertain`; every current terminal attention record has `fgaResubmissionAllowed: false` |

`writeGates` on an item contains only currently applicable paused gate
projections. It is empty when neither gate is paused. The same stable gate shape
is used by the collection summary.

`permanentSubmissionBlock.reasonCode` is exactly
`moderation_submission_recorded` for Flickr code `6`/`7`, or
`delivery_uncertain` for an unknown post-dispatch result or unresolved dispatch.
It preserves the first durable block reason and never changes to reflect a
later observation.

## Reason and action vocabulary

The hosted implementation maps durable classifications to one allowlisted
`reasonCode`; it never passes Flickr text or exception strings through. Initial
codes are:

| Intent/result class | `reasonCode` |
| --- | --- |
| Explicit temporary Flickr result `105` or `106` | `temporary_flickr_failure` |
| Safe pre-dispatch transport failure | `safe_transport_failure` |
| Flickr per-group throttle code `5` | `flickr_group_limit` |
| Complete target membership already present | `membership_already_present` |
| Successful add or already-in-pool code `3` | `added` |
| Pending moderation code `6` or `7` | `moderation_submission_recorded` |
| Photo missing/ineligible | `photo_unavailable_or_ineligible` |
| Group missing/ineligible or group rules reject the photo | `group_unavailable_or_ineligible` |
| Photo pool/request-policy limit | `request_policy_rejected` |
| User credential/permission fault after add dispatch | `user_flickr_reauthorization_required` |
| Shared signer/key/protocol fault after add dispatch | `deployment_repair_required` |
| Unknown post-dispatch code or unresolved dispatch | `post_dispatch_result_unavailable` |
| User-visible cancellation retained from a future separately accepted operation | `cancelled` |

Unknown persisted reason values fail the response closed with
`500 status_projection_invalid`; they are never rendered as a known safe class
or arbitrary text. Adding a reason is an API schema change with server/client
exhaustiveness tests.

For `needs_attention`, `operatorAction` is one exact value selected from
`correct_future_selection`, `reauthorize_flickr`, or `repair_deployment`. For
`delivery_uncertain`, it is always `inspect_flickr_no_fga_resubmit`. These are
presentation guidance codes, not endpoint names or authorities. The FGA LrC
plug-in renders reviewed local copy and no automated action button. The FGA
administrative control plane may link `reauthorize_flickr` or
`repair_deployment` to its separately authorized Flickr-link/gate workflows,
but repairing a shared gate does not revive the terminal intent that revealed
the fault.

Photo/group/request-policy reasons map to `correct_future_selection`; user
credential/permission reasons map to `reauthorize_flickr`; and shared
signer/key/protocol reasons map to `repair_deployment`. No serializer or client
chooses a weaker action dynamically.

`moderation_submitted` includes a permanent block but has no `attention` object.
Its reviewed copy says that Flickr recorded a moderation-queue submission and
the FGA group-submission worker will never submit that exact pair again. It does
not claim acceptance, rejection, a queue position, or a future decision time.
The exact selector/status meanings, total block-first priority, closed action
vocabulary, and `MSUI-*` fixtures are in the
[moderator-safety UI conformance contract](moderator-safety-ui-conformance.md).

## No retry, reopen, or cancellation command

The private-MVP status surface is deliberately read-only. There is no manual
retry-now command because:

- an active safe retry already has an authoritative database due time; a client
  must not defeat backoff, group throttling, a write gate, FIFO, or global rate
  reservations;
- `moderation_submitted` and `delivery_uncertain` are protected by permanent
  exact-pair blocks;
- `needs_attention` is terminal and removed from active FIFO membership; the
  user may correct a future selection or act manually in Flickr, but the FGA API
  backend does not automate another submission for that exact intent; and
- gate resume is a separate recent-authenticated administrative operation with
  a fresh non-mutating Flickr proof and compare-and-set revision.

Status refresh, page traversal, relink, gate resume, process restart, deployment,
and an identical group-submission batch do not reopen or reschedule a terminal
intent. A future cancel, reorder, reopen, or safely scoped retry operation needs
a separate architecture decision, explicit state transition, idempotency and
authorization contract, and fail-polite conformance evidence. It cannot be
added as a UI-only shortcut.

## FGA LrC plug-in presentation and polling

After a successful group-submission-batch response, the FGA LrC plug-in retains
the returned non-secret intent IDs and binding ID in its existing local
outbox/status record. If response delivery is ambiguous, it retains the binding
ID and original group-ID set, invents no intent ID, and may repeat only the
already-defined idempotent batch handoff before reconciling the returned/current
intents. The routine **FGA Queue Status** command remains inside Lightroom
Classic. It starts with one collection request, accumulates keyset pages for the
selected view, and publishes the new UI model only after all requested pages
succeed. A failed/malformed page leaves the prior display visibly stale; it is
never presented as a successful empty queue.

While the status dialog is visible, the FGA LrC plug-in may poll no sooner than
`recommendedPollAfterSeconds`, coalescing multiple photos into collection reads
instead of one request per intent. Closing the dialog stops polling. Manual
refresh still respects `Retry-After`; it does not cause worker work. The plug-in
uses bounded exponential backoff after transport/`503` failure and restarts an
initial traversal rather than resuming a partial failed page set.
`recommendedPollAfterSeconds: null` also stops automatic polling.

### Behavior-derived active-queue copy

The FGA LrC plug-in **MUST** derive active-queue copy from the current complete
response tuple `(observedAt, state, queue.isPartitionHead,
queue.activeAheadInPartition, queue.nextWorkNotBefore, queue.holds)`. It has no
separate deployment-cadence constant and does not say that work runs nightly,
once per minute, once per group, or by an estimated completion time. Cloud
Scheduler's at-least-once-per-minute sweep is an operational recovery cadence,
not a user-visible service promise. `recommendedPollAfterSeconds` controls only
client reads and **MUST NOT** be rendered or interpreted as worker cadence.

The English private-MVP renderer selects the first matching primary sentence:

| Projection condition | Exact primary sentence |
| --- | --- |
| Any nonempty `holds` value | `Flickr writes are paused for review. Queue order is preserved.` |
| `state = attempting` | `Work has started for this group request.` |
| `isPartitionHead = false` and `activeAheadInPartition = N` | `Waiting behind N earlier request(s) for this Flickr group.` with ordinary singular/plural substitution |
| Head in `throttled` with `nextWorkNotBefore` later than `observedAt` | `Flickr's group limit was reached. Eligible for another check after {time}.` |
| Head in `retrying` with `nextWorkNotBefore` later than `observedAt` | `Eligible for a safe retry after {time}.` |
| Head whose non-null `nextWorkNotBefore` is no later than `observedAt` | `Waiting for the next worker opportunity.` |

`{time}` is the response timestamp rendered in the user's locale with its zone
shown; it remains a lower bound, not an appointment or ETA. Ahead count and due
time may appear as secondary structured details when they do not contradict the
primary sentence. A head/non-head/count/state/due combination outside the
worker persistence contract is `status_projection_invalid`; the FGA LrC plug-in
shows the existing unavailable state instead of guessing copy.

This table is one reviewed total function over server behavior. Copy fixtures
**MUST** cover every row, singular/plural counts, due times on both sides of
`observedAt`, both gate holds, and impossible combinations. Mutation tests
**MUST** fail if a renderer substitutes `recommendedPollAfterSeconds`, a
deployment scheduler interval, or a fixed nightly/minute promise for the queue
projection. A future wording or localization change must preserve these exact
meanings and rerun the same behavior fixtures.

The FGA LrC plug-in presents exact durable meaning:

- active states say waiting/working and may show advisory ahead count, due time,
  or gate hold, but no percent complete or cross-group ETA;
- `added` says Flickr confirmed the photo is in the group;
- `moderation_submitted` says Flickr recorded a moderation-queue submission and
  the FGA group-submission worker will never submit the pair again;
- `needs_attention` shows reviewed reason/action guidance and says the current
  intent will not retry automatically;
- `delivery_uncertain` says Flickr may have received the request, the exact pair
  is permanently blocked from FGA resubmission, and the user may inspect Flickr
  manually; and
- `cancelled` says only that the retained intent is cancelled, without implying
  a Flickr removal or undo.

The FGA LrC plug-in selects copy and controls through the total presentation
rule in the moderator-safety UI conformance contract. It never uses an
acknowledgement, current moderation value, local history, or current
non-membership to weaken a non-null `permanentSubmissionBlock`. An unknown or
contradictory projection produces an unavailable display with no mutation
control.

The UI never presents continued absence from a group as rejection, a paused
gate as intent failure, a stale group name as current Flickr authority, terminal
retention as active queue membership, or a status-read failure as an empty
queue.

## Admission limits and failures

Status reads share a per-current-installation token bucket allowing 120 reads
per 10 minutes with burst 20 and a deployment-wide sliding window allowing 600
reads per 10 minutes. Administrative reads have an independent 120-per-10-minute
session bucket with burst 20. All applicable limits must admit the request.
`429 Too Many Requests` includes an integer `Retry-After`, returns no partial
rows, and creates no worker hint. These private-MVP values accommodate one
15-second collection poll while bounding a stolen credential or broken client;
changing them requires load/cost evidence and conformance reruns.

Other failures are:

| Condition | Response |
| --- | --- |
| Missing/invalid installation credential | RFC 6750 `401` behavior from the plug-in contract |
| Valid credential class/state without route authority | `403 insufficient_scope` |
| Missing/foreign intent or binding | Non-oracular JSON `404` |
| Malformed/unsupported query or continuation | `400` with the fixed status-query code and no rows |
| FGA database unavailable | `503 status_unavailable`, `Retry-After`, and no cached/partial representation |
| Unknown durable state/reason, impossible active/terminal fields, or block contradiction | `500 status_projection_invalid`, alert, and no partial representation |

An individual malformed row fails the whole page. The FGA API backend does not
filter it out, synthesize an `unknown` state, or return a prefix. Administrative
and plug-in errors use their existing non-oracular envelopes and never include
SQL, table/secret names, raw Flickr values, stack traces, or another user's
existence.

## Required conformance evidence

The future hosted repository must run the exact production routes, authorization
middleware, PostgreSQL migrations, and serializer and prove at least:

- current `lrc_plugin` and administrative identities can read only their exact
  allowlisted route family and owner scope; pending/unknown/revoked credential
  classes and cross-boundary credentials fail closed;
- collection view membership exactly matches the durable state sets and a gate
  pause changes only holds/summary, not intent state;
- counts, page rows, gate projections, and database `observedAt` come from one
  repeatable-read snapshot;
- immutable descending keyset pages have no duplicates, require exact paired
  continuation values/filters, and retain no cursor records;
- a state transition between active pages cannot produce a false complete
  snapshot claim, while a full `history` traversal remains membership-stable;
- every state/reason/block/hold combination serializes exhaustively and an
  unknown or contradictory record fails the complete response;
- raw Flickr bodies/messages, exception text, credentials, gate IDs, leases,
  task tokens, and other users' records never appear;
- status reads create no task, due-row change, lease, attempt, Flickr call,
  gate change, terminal transition, or permanent-block mutation;
- terminal/group-limit/write-gate cases expose no retry, reopen, force, clear,
  cancellation, or scheduling authority, and guessed mutation paths receive
  server-owned `404`/`405` rather than HTML;
- polling limits, `Retry-After`, database failure, and malformed-row handling
  return no partial/empty-success response; and
- reviewed FGA LrC plug-in copy distinguishes accepted, active, paused, added,
  moderation-submitted, needs-attention, delivery-uncertain, cancelled, stale,
  and unavailable states without inferring rejection or offering resubmission;
- behavior-derived active-copy fixtures prove that state, FIFO-ahead count,
  database due bound, and holds select the reviewed sentence; they reject
  `recommendedPollAfterSeconds`, scheduler cadence, and fixed nightly/minute
  promises as presentation inputs; and
- the shared `MSUI-*` fixture suite proves that selector, status, repeated-batch,
  administrative, command, and accessibility projections derive protected-pair
  copy and available actions from the server-owned permanent block.

This architecture repository has no production FGA API backend, FGA database,
administrative UI, or FGA LrC plug-in status implementation and therefore
claims no executable status-conformance pass.
