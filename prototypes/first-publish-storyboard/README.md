# First-publish customer storyboard

Date: 2026-09-04

Status: Disposable low-fidelity design prototype

Authority: Non-normative design evidence. Accepted ADRs, scoped contracts, and the
three interaction-map tabs designated by ADR 0041 remain authoritative.

## Run the storyboard

Open [`index.html`](index.html) directly in a browser. The artifact has no build
step, package dependency, external asset, network request, credential, or service
connection. All people, photos, groups, identifiers, times, and outcomes are fake.

Use the primary action in each scene, the numbered scene rail, or the left and right
arrow keys. **Restart** returns the walkthrough to its initial state.

User-visible datetimes use `YYYY-MM-DD h:mmam/pm TZ`, such as
`2031-01-13 9:34am EST`. The current storyboard uses the applicable `EST` or `EDT`
suffix. This is a storyboard display convention, not a production timezone or
localization decision.

## Scope and deliberate limits

The storyboard follows one photographer from deciding to use FGA through:

1. Google authentication and Flickr authorization in a private administrative
   browser window;
2. one-time Plugin Code creation and same-workstation transfer;
3. FGA LrC plug-in publish-service and Album setup in Lightroom Classic;
4. per-photo group selection;
5. Lightroom Classic rendering, direct Flickr upload, Album attachment, and durable
   group-intent handoff;
6. asynchronous partial success, a known-safe scheduled retry, and ambiguous-delivery
   recovery; and
7. returning to status after the Lightroom Classic host has been closed.

The prototype intentionally does not choose a production UI framework, hosted
provider, browser-application structure, or exact Lightroom SDK control. It contains
no real API integration and does not claim implementation feasibility for a specific
Lightroom Classic surface. Ticket #0068 owns the exact documented-SDK group-selection
interaction.

The depicted allowlisted Google Account is the owner-only MVP from
[ADR 0004](../../docs/decisions/0004-single-user-mvp.md). The storyboard is not a
generic public-onboarding flow. ADR 0004 records the separately gated progression
from owner-only MVP to invite-only closed beta and, only after another accepted
go/no-go decision, public signup.

The storyboard treats **retry** narrowly. The photographer can refresh status, but
cannot retry, reorder, reopen, or force a group submission. The FGA
group-submission worker may make a later attempt only when the durable state proves
that doing so is safe. An ambiguous dispatch becomes a permanent no-resubmission
boundary with read-only Flickr inspection guidance.

## Walkthrough findings

1. **One-time setup is two different trust jobs.** The browser establishes the
   owner's Flickr grant and creates a Plugin Code; the FGA LrC plug-in separately
   validates its installation credential. The browser and transient plug-in input
   show the same canonical value in clear text with identical grouping and typography
   until the user compares them and selects **Store and verify**. Presenting these as
   a short checklist makes the boundary understandable without inventing a browser-
   to-plug-in callback.
2. **The routine loop should start at the photo, not at infrastructure.** After setup,
   the useful recurring sequence is edit one photo, choose additions, publish, and
   optionally inspect status. Administrative state can recede to a small connected
   indicator.
3. **Publication, Album attachment, and group delivery need separate milestones.** A
   photo can be safely published while its Album attachment and group requests
   progress independently. One combined success/failure banner would incorrectly
   impose ordering and imply that delayed follow-up work prevented publication.
4. **Current membership and requested additions must look different.** Existing
   Flickr pool membership is read-only, but a brand-new photo has no Flickr identity
   to inspect before upload. First-publish selection therefore shows only eligible
   additions; a later reopening for the bound photo must separate fresh observed
   membership from new checkboxes.
5. **Background retry needs exact language.** “Eligible for a safe retry after…”
   communicates a lower bound without promising an appointment or offering a
   photographer-controlled write. **Refresh status** is the only routine status
   action.
6. **Ambiguous delivery needs a calm terminal treatment.** The useful recovery is to
   preserve the published photo, explain the permanent protection, and offer
   read-only Flickr inspection. A generic retry component would be actively unsafe.
7. **Status must survive the Lightroom session.** Showing that the hosted worker
   progresses after the Lightroom Classic host closes makes the asynchronous value
   proposition visible and keeps the user from waiting at a progress dialog.
8. **Audience expansion is a release sequence, not a signup toggle.** The current
   allowlisted-owner scene remains correct for the MVP. An invite-only closed beta
   must prove the multi-tenant and operational controls before a separately accepted
   public-signup phase may admit otherwise eligible Google Accounts.

## Contract-gap disposition

The initial walkthrough exposed no new architecture contract gap. Follow-up review
identified an eventual broader audience as FGA ticket #0086. ADR 0004 now records
the phased deployment path without authorizing or designing the closed-beta or public
signup phases. A later visual-verification review found and resolved the Plugin Code
presentation gap under FGA ticket #0087 and
[ADR 0044](../../docs/decisions/0044-use-canonical-crockford-base32-plugin-codes.md).
FGA ticket #0068 subsequently mapped the group-selection scene to documented
Lightroom SDK interfaces in proposed
[ADR 0045](../../docs/decisions/0045-use-a-library-modal-and-photo-metadata-for-group-selection.md).
That proposal, not this disposable artifact, owns the exact production command,
modal, and persistence recommendation and still requires Terry's decision.

The storyboard's state and copy were derived from:

- [ADR 0041](../../docs/decisions/0041-use-clean-room-authentication-tabs-as-interaction-authority.md),
  which controls the three happy-path interaction maps;
- [ADR 0044](../../docs/decisions/0044-use-canonical-crockford-base32-plugin-codes.md),
  which controls Plugin Code encoding and simultaneous clear-text presentation;
- the [zero-state publish flow](../../docs/zero-state-publish-flow.md);
- the [browser-session lifecycle](../../docs/browser-session-lifecycle.md);
- the [group-submission status contract](../../docs/queue-status-api.md); and
- the [moderator-safety UI conformance contract](../../docs/moderator-safety-ui-conformance.md).
