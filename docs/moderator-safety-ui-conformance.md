# Moderator-safety UI conformance contract

Last updated: 2026-09-05

Status: Accepted UI and API projection under ADRs 0007 and 0034; executable
implementation evidence remains pending in the future hosted and FGA LrC
plug-in repositories

Authority: [ADR 0007](decisions/0007-fail-polite-group-submissions.md) controls
the permanent exact-pair block. Accepted
[ADR 0034](decisions/0034-expose-read-only-group-submission-status.md) and the
[group-submission status API contract](queue-status-api.md) control the read
projection. This contract does not create an exception to either source.

## Purpose

Every FGA-owned user interface must tell the same truth about a Flickr photo and
group pair. In particular, a screen cannot promise that FGA components will not
repeat a moderator submission while another screen offers an acknowledged
resubmission, **Send anyway**, retry, override, or block-clear control.

The accepted safety fact lives in the FGA database's insert-only
`submission_blocks` relation. UI copy, local plug-in history, current Flickr
membership, a cached moderation observation, and the current group moderation
setting are not authorities that can create, weaken, or clear that fact.

## Authoritative input and fail-closed assembly

When the FGA LrC plug-in opens group selection for an already bound photo, it
assembles one display model from three bounded server projections:

1. the complete current writable-group snapshot;
2. one new complete binding-scoped Flickr membership observation from
   `GET /api/v001/photo-bindings/{photoBindingId}/group-memberships`; and
3. the complete retained `history` view from
   `GET /api/v001/group-submission-intents?view=history&photo_binding_id={photoBindingId}`.

The FGA API backend joins each status intent to the authoritative exact-pair
block row and emits `permanentSubmissionBlock`; it does not reconstruct block
presence from the intent state or attempt log. Durable intent rows are retained,
so the complete binding-scoped history projects every prior pair. The selector
follows every keyset page before enabling confirmation. A missing, malformed,
contradictory, changed, or failed page in any input discards the incomplete
assembly, labels the relevant data **Unavailable**, and enables no group-add
confirmation. Prior successful data may remain visibly stale for diagnosis but
cannot enable a submission action.

The batch response repeats the same `permanentSubmissionBlock` shape for each
intent. That response is the immediate authority after handoff. A response with
`created: false` and a block is a server-confirmed no-op, not an invitation to
ask for consent and try again. A status or batch representation that omits a
required block, reports an unknown block reason, or contradicts the durable
state fails closed as a whole; the client exposes no mutation control.

The server-side transaction remains the final enforcement boundary. A modified,
stale, or hostile client can submit any syntactically valid group ID, but an
existing natural-key intent or permanent block returns the existing intent with
`created: false`, creates no row, emits no worker hint, and cannot dispatch a
Flickr write.

## Total presentation rule

The FGA LrC plug-in and future FGA administrative UI apply the following rows in
order for each exact `(Flickr photo ID, Flickr group ID)` pair. The first
matching row controls submission availability. Multiple informational badges
may remain visible; for example, a pair can be both currently observed in a
pool and permanently protected.

| Priority | Server-derived condition | Semantic presentation code | Submission control |
| --- | --- | --- | --- |
| 1 | Any required selector projection is unavailable, incomplete, unknown, or contradictory | `selection_data_unavailable` | Disabled for the complete handoff |
| 2 | `permanentSubmissionBlock.reasonCode == "moderation_submission_recorded"` | `moderation_submission_protected` | Absent |
| 3 | `permanentSubmissionBlock.reasonCode == "delivery_uncertain"` | `delivery_uncertain_protected` | Absent |
| 4 | The fresh membership observation contains the group | `current_membership_observed` | Absent; membership is read-only |
| 5 | A retained intent exists without a permanent block | `existing_submission_intent` | Absent; status is view-only |
| 6 | The group is writable, freshly absent from membership, and has neither an intent nor block | `eligible_group_addition` | Ordinary selection checkbox |

There is no default-to-eligible branch. An unknown semantic code, state, block
reason, or combination renders `selection_data_unavailable` and no checkbox.
Current `ispoolmoderated`, elapsed time, current non-membership, a prior
moderation acknowledgement, or a user's willingness to accept the risk cannot
change the priority.

An ordinary selection checkbox creates a first intent only through the complete
group-submission batch operation. It is not a retry button and disappears after
the server reports any intent for that pair. Removing a local check mark never
removes Flickr membership, cancels an intent, or clears a block.

## Reviewed copy catalog

Client code selects reviewed local copy by the closed semantic presentation
code. It does not concatenate a Flickr message, block reason, state, or Boolean
into prose. The FGA LrC plug-in and any future FGA administrative UI run the same
language-neutral fixture table against their local catalogs.

| Semantic presentation code | Required English meaning |
| --- | --- |
| `selection_data_unavailable` | **Group-addition status is unavailable. No FGA component submitted anything. Refresh before selecting groups.** |
| `moderation_submission_protected` | **Flickr recorded a moderation submission for this photo and group. The final moderator decision is unknown. FGA components will not submit this exact pair again.** |
| `delivery_uncertain_protected` | **FGA records cannot prove whether Flickr received the add request. To avoid a duplicate request, FGA components will not submit this exact pair again. Inspect Flickr manually.** |
| `current_membership_observed` | **Currently in this Flickr group as observed at {observedAt}. Membership is read-only in FGA.** |
| `existing_submission_intent` | **FGA already has a submission record for this photo and group. View its status; creating another submission is unavailable.** |
| `eligible_group_addition` | **Select to ask the FGA group-submission worker to add this photo to the group. Flickr may accept it, queue it for moderation, or refuse it.** |

For `moderation_submission_protected`, the UI does not say **pending** because
Flickr exposes no documented submitter-facing way to distinguish still pending
from rejected. A later positive membership observation may add **Membership was
later observed**, but it does not replace or hide the permanent-protection copy.
Absence never becomes rejection copy.

For `delivery_uncertain_protected`, **Inspect Flickr manually** is navigation or
guidance only. It does not invoke `flickr.groups.pools.add`, synthesize a request,
or deep-link to an action that submits the pair. A user may independently use
Flickr's own UI; no FGA component automates or facilitates that resubmission.

## Available actions

The UI model has a closed action vocabulary:

- `select_for_first_add` applies only to `eligible_group_addition`;
- `view_status` is read-only navigation to an existing intent;
- `inspect_flickr` is read-only navigation or guidance;
- `refresh` repeats the complete safe read sequence;
- `reauthorize_flickr` enters the separately authorized OAuth repair flow; and
- `repair_deployment` enters the separately authorized administrative repair
  flow.

None of those action codes is an API endpoint or replay authority. For a pair
with `permanentSubmissionBlock != null`, the only pair-specific actions are
`view_status` and `inspect_flickr`. The application route inventory, OpenAPI,
FGA LrC plug-in command registration, context menus, keyboard accelerators, and
accessibility action tree contain no `retry`, `retry_now`, `send_anyway`,
`acknowledge_and_submit`, `force_resubmit`, `reopen`, `clear_block`,
`cancel_and_resubmit`, or override action.

Changing button text while retaining one of those behaviors is nonconforming.
Likewise, a generic retry component cannot be reused on a protected-pair screen
unless its mutation action is structurally absent.

## Batch and status response invariants

The future FGA API backend serializer enforces these cross-field invariants:

- `moderation_submitted` has a non-null block reason
  `moderation_submission_recorded`;
- `delivery_uncertain` has a non-null block reason `delivery_uncertain`;
- a non-null permanent block always produces `created: false` in a repeated
  batch response and never emits a worker hint;
- `permanentSubmissionBlock` contains no expiry, delete token, override flag,
  resubmission Boolean, or capability URL;
- every block is loaded by exact server-derived photo and group identity within
  the authenticated FGA user's scope; and
- an unknown block reason or impossible state/block combination fails the
  complete response with the existing closed projection error.

The FGA LrC plug-in treats a lost batch response as permission to repeat only
the same idempotent batch handoff. It then renders the returned current intent
and block. It never changes that recovery operation into a Flickr resubmission
or a weaker request.

## Required conformance evidence

The future implementation repositories must run these cases against production
route registration, serializer/database adapters, and real client view-model
code. Fixture IDs are stable review references.

| ID | Required proof |
| --- | --- |
| `MSUI-001` | Every state, block reason, membership presence, and existing-intent combination follows the total priority table; unknown and contradictory combinations fail closed with no selection control. |
| `MSUI-002` | Code `6` and code `7` results produce `moderation_submission_protected`, the exact reviewed meaning, no **pending** or rejection inference, and no mutation action. |
| `MSUI-003` | Every ambiguous-dispatch and unknown-side-effect case produces `delivery_uncertain_protected`, the exact reviewed meaning, and no mutation action. |
| `MSUI-004` | A positive later membership observation adds read-only membership information without hiding or clearing an existing permanent-protection notice. |
| `MSUI-005` | A complete history or membership paging failure, changed revision, malformed row, unknown enum, or database failure leaves prior data visibly stale and disables the complete handoff. |
| `MSUI-006` | The plug-in and administrative copy catalogs pass the same language-neutral semantic fixtures and expose only the closed action vocabulary. |
| `MSUI-007` | Route, OpenAPI, command, context-menu, accelerator, and accessibility inventories contain no resubmit, retry, send-anyway, acknowledge, reopen, block-clear, or override mutation. |
| `MSUI-008` | A modified client repeats a blocked pair through the only batch route; the FGA database returns the existing intent and block with `created: false`, and before/after evidence proves no intent, attempt, due time, hint, gate, block, or Flickr-call mutation. |
| `MSUI-009` | Exact-copy snapshots cover status, selector, repeated-batch recovery, stale/unavailable, current-membership-plus-block, and narrow/keyboard-accessible layouts. |
| `MSUI-010` | Mutation tests that remove the server block lookup, weaken the priority, add a generic retry handler, or change protected-pair copy without updating the reviewed fixture must fail. |

The legacy browser's contradictory copy and acknowledged **Send anyway** path
are historical evidence, not a compatibility requirement. The clean-room FGA
LrC plug-in and hosted implementation must satisfy this contract directly and
must not carry that behavior forward.
