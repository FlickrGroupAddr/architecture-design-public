# ADR 0010: Permit Flickr publication without group additions

Date: 2026-08-25

Status: Accepted by Terry on 2026-08-25

## Context

The accepted zero-state flow required every photo to have at least one selected
Flickr group before the FGA LrC plug-in would render it. That made group
submission a prerequisite for Flickr publication even though uploading the
photo and attaching it to the published collection's one-to-one Flickr album
are useful outcomes on their own.

The requirement was also a poor fit for Lightroom Classic's album-level
publish callback. Stopping a photo with no selected groups could block useful
work or tempt the FGA LrC plug-in to open one serial modal dialog per photo.
Neither behavior protects Flickr moderators or improves publication safety.

## Decision

The FGA LrC plug-in **MUST** permit a new photo to be published to Flickr with
zero selected group additions. Flickr publication and eventual attachment to
the published collection's one-to-one Flickr album are required photo outcomes;
group submissions are optional, add-only intents.

- In the normal single-photo preflight, the FGA LrC plug-in **MUST** present
  **No group additions** as an explicit, confirmable choice rather than making
  an empty selection look accidental.
- In a multi-photo publish callback, a photo with zero selected group additions
  **MUST NOT** block another photo or require a serial per-photo modal. The FGA
  LrC plug-in **MUST** show the zero-group outcome truthfully in per-photo state
  or the batch summary.
- The FGA LrC plug-in **MUST** snapshot zero or more selected group IDs before
  rendering. An empty snapshot creates no group-submission intent and no queue
  work.
- When the snapshot is nonempty, the existing durable group-intent handoff and
  every add-only, fail-polite, FIFO, ambiguity, and permanent-suppression rule
  remain unchanged.
- The FGA LrC plug-in **MUST NOT** send an empty request to an operation whose
  contract requires a group submission merely to trigger an unrelated hosted
  side effect. Hosted photo binding and ownership proof must have a conventional
  explicit contract independent of whether group intents exist. FGA localswim
  ticket #0020 owns that still-open contract and its user-visible state.
- A later **Add more groups** action may create intents for a zero-group photo
  after the applicable fresh-membership and hosted-ownership checks succeed. It
  does not render or upload the photo again.

## Consequences

- The FGA LrC plug-in remains useful as a PNG Flickr publisher even when Terry
  does not want group distribution for a particular photo.
- Album attachment remains mandatory for every newly published photo and is not
  weakened by the absence of group work.
- A zero-group photo has no FGA group-submission worker state, rate-limit work,
  moderation preflight, or photo/group suppression record.
- The current provisional group-submission-batch operation continues to require
  at least one group. The product decision exposes, rather than hides, the need
  to decouple hosted photo proof from group-intent creation before
  implementation.
- Publish progress and summaries need to distinguish **No group additions**
  from pending, failed, or omitted group work.

## Alternatives considered

- **Require at least one group:** rejected because group distribution is not a
  prerequisite for Flickr publication or album attachment and would add
  avoidable friction to the dominant one-photo workflow.
- **Stop only the zero-group photo in a batch:** rejected because an optional
  group choice must not prevent an otherwise valid photo outcome.
- **Send an empty group-submission batch:** rejected because an operation named
  and validated for group work should not acquire a hidden photo-binding side
  effect. A separate explicit hosted photo contract is easier to understand,
  test, and remove.
