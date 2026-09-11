# Architecture review session closeout

Date: 2026-08-22

## Review state

- Terry has explicitly approved Phases 1 through 6 of
  `docs/zero-state-publish-flow.md`; every signoff is recorded in that canonical
  document and committed.
- Phase 7, **Queue wake-up and independent group progress**, is the current
  unsigned phase. Its review is in progress; Terry has not approved the phase
  in full.
- Phase 8, **Additional photos and final state**, remains unreviewed and awaits
  explicit signoff after Phase 7.
- The prose plug-in/service contract remains a draft for review and has not yet
  been encoded as OpenAPI. No production FGA hosted service or production FGA
  LrC plug-in has been implemented.

## Design settled during this review

- The FGA API backend computes SHA2-256 over the presented opaque installation
  bearer credential to locate the active installation record. That record's
  linked FGA user and Flickr NSID—not the credential digest—select the Flickr
  OAuth 1.0a access token and token secret used to sign the exact documented
  Flickr operation.
- FGA REST operations that expose data volumes outside FGA's control use bounded
  pagination with opaque continuation handles rather than offsets or client-
  interpretable cursor state.
- The FGA LrC plug-in is a Lightroom Classic publish service. It obtains fresh
  Flickr group membership for each selected photo so its UI can distinguish
  current membership from groups selected for addition. FGA group management is
  add-only; no FGA component removes a photo from a Flickr group.
- Direct image upload remains split across components: the FGA API backend signs
  the exact upload metadata and the FGA LrC plug-in streams the rendered photo
  directly to Flickr. The upload authorization binds the later durable intent
  handoff to the authenticated FGA user and resulting Flickr photo ID.
- Every individual `flickr.groups.pools.add` attempt has an exceptionless fresh
  `flickr.groups.getInfo` preflight. Confirmed moderation submission and
  ambiguous post-dispatch delivery permanently block automatic resubmission of
  the exact Flickr photo/group pair under ADR 0007's fail-polite rule.
- Durable submission-intent history is separate from active FIFO membership.
  Only `queued`, `attempting`, `retrying`, and `throttled` intents occupy the
  active queue; a terminal transition atomically removes queue membership while
  retaining the intent row and history.
- Flickr outcomes are now written human-first throughout the architecture: the
  documented status name precedes its numeric application code. Result tables
  follow the same convention.

## Repository and validation state

- Branch: `main`.
- Last substantive commit before this closeout:
  `9a70378 Name Flickr statuses before result codes`.
- The two changed PlantUML flow diagrams pass PlantUML 1.2026.6 `-checkonly`.
- `git diff --check` passed after the status-name cleanup.
- Obsolete references to repository-local board state were removed. The private
  external state-store remains the only board snapshot described by the working
  agreement.

## Exact resume point

Resume the phase-by-phase review at Phase 7 in
`docs/zero-state-publish-flow.md`. Start from its current complete canonical
text, including the active-FIFO versus durable-history distinction and the
human-readable Flickr status names in steps 7.14 through 7.18.

Do not mark Phase 7 approved until Terry explicitly approves it in full. Record
that signoff in the flow document and commit it in the same turn. Then present
Phase 8 for review. After both remaining phases have explicit committed
signoff, reconcile the approved prose contract and deferred bounds before
encoding the OpenAPI description.
