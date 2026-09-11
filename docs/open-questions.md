# Architecture question register

Last updated: 2026-09-05

Status: Non-normative inventory of open, deferred, and resolved questions

Authority: Non-normative decision inventory. Accepted ADRs and scoped contracts,
not this list, close questions under the
[documentation authority hierarchy](README.md).

This register preserves the original question numbers for provenance. Every
open item has one FGA localswim ticket; the public text records only the
sanitized question and ticket ID, not private board discussion. Deferred items
are not current private-MVP work. Resolved entries point to the source that now
answers them.

## Open questions

### Q001 — Public product name

Resolved on 2026-08-26 by owner decision on ticket #0069: the public product
name is **FlickrGroupAddr**, abbreviated **FGA**. The exact joined spelling is a
deliberate play on Flickr. The project-owner-controlled `flickrgroupaddr.com`
domain is the selected origin for the FGA API backend and administrative
control plane.

### Q003 — Exact group-selection interaction

Resolved on 2026-09-04 by Terry's approval of ticket #0068. The architecture
fixes per-photo editable selection inside the FGA LrC
plug-in, a single-photo-first workflow, and no serial modal dialogs during a
multi-photo callback. Accepted
[ADR 0045](decisions/0045-use-a-library-modal-and-photo-metadata-for-group-selection.md),
which selects a Library menu command, native modal, and private per-photo
plug-in metadata record using only documented Lightroom SDK 15.3 interfaces.

### Q007 — Oversized render

Resolved on 2026-08-26 by owner decision on ticket #0070: when a rendered PNG
exceeds Flickr's configured 200 MB upload ceiling, the FGA LrC plug-in hard
fails that photo before upload authorization. It does not resize, convert to
JPEG, offer a fallback action, or start any upload. The user may separately
change the publish settings and publish again. On 2026-09-03, Terry proposed
concurrently rendering 8-bit and 16-bit PNGs and letting an under-limit 16-bit
file win. After review, Terry accepted rejection of concurrent and sequential
automatic winner selection. [ADR 0002](decisions/0002-lossless-png-output.md)
preserves the proposal, objections, rejected fallback, and boundary for a later
explicit 16-bit mode.

### Q018 — Annual diligence destination

Resolved on 2026-08-26 by owner decision on ticket #0071: the real annual FGA
Diligence chain uses the owner-controlled, publicly visible, invite-only
[FlickrGroupAddr Diligence](https://www.flickr.com/groups/14968939@N22/) group.
Its pool is unmoderated, accepts only Safe still images classified as either
Photos/Videos or Illustration/Art/Animation/CGI, and has no group-specific
posting throttle. Each run creates at most one purpose-built synthetic public
photo and retains that photo and its group membership as operational evidence.
No FGA component removes the photo from the pool or deletes it from Flickr.

### Q019 — Adobe SDK license text

Resolved on 2026-08-26 by review under ticket #0072. The Lightroom Classic 15.3
SDK archive contains Adobe-copyrighted Sample Code but no standalone license
file. The governing [Adobe Developer Terms of
Use](https://www.adobe.com/go/developer-terms), last updated June 18, 2024,
cover Developer Console downloads and Developer Tools including SDK files and
Sample Code. They permit development/test use, but their non-sublicensable,
non-transferable grant and object-code-only distribution boundary are not
compatible with copying Adobe Lua source into FGA's public MIT source. Keep the
original-implementation, no-copy boundary.

## Deferred scope-change questions

### Q013 — Erasure and later public re-registration

Public signup is out of scope. If Terry deliberately reopens public or
multi-user operation, the new privacy/abuse design must reconcile lawful
erasure with moderator-protection memory before re-registration is offered.
[ADR 0004](decisions/0004-single-user-mvp.md) keeps that work outside the
private MVP.

### Q014 — Public-service abuse controls

The private owner-operated product does not need public admission, suspension,
or appeal machinery. A future public launch remains prohibited until a separate
accepted threat model defines conservative per-user/group limits,
re-registration resistance, monitoring, suspension, and repair procedures.
[Vision and scope](vision-and-scope.md#product-principles) records the gate.

## Resolved questions

### Q002 — Per-photo versus publish-batch group choices

Resolved: selections are editable per photo. Each photo snapshots zero or more
group IDs independently; a multi-photo publish run is neither atomic nor
ordered and cannot open serial per-photo modal dialogs merely to preserve
callback order. See the [zero-state publish
flow](zero-state-publish-flow.md#phase-4--per-photo-selection-rendering-and-preflight).

### Q004 — Which Flickr plug-in capabilities define FGA scope

Resolved: every job Terry uses today is required capability, but no Adobe menu,
click sequence, state presentation, implementation choice, or limitation is
binding. The FGA LrC plug-in preserves ordinary album and publish capabilities
unless a documented SDK interaction is explicitly better; destructive and
smart-album boundaries are decided separately. See [vision and
scope](vision-and-scope.md#problem) and the [album-scoped publish
contract](album-scoped-publish-contract.md).

### Q005 — Removing a local published photo or album

Resolved: local removal sends no Flickr photo, album, or membership deletion.
Remote content remains, and already accepted attachment work finishes or stays
visible for repair. See
[ADR 0027](decisions/0027-rename-albums-but-do-not-delete-them-from-local-actions.md).

### Q006 — Ambiguous upload outcome

Resolved: once the image POST might have left the Lightroom Classic host
networking stack, the FGA LrC plug-in never replays it automatically. It offers
advisory owner-photo lookup, an explicit photographer-selected binding, a
separate warned new-copy choice, or leaving the outcome unresolved. See
[ADR 0012](decisions/0012-photographer-reconciliation-after-ambiguous-upload.md).

### Q008 — Archival claims

Resolved: FGA makes no archival claim. PNG losslessly preserves Lightroom's
final 8-bit rendered sample values, not the RAW source or editing latitude;
Flickr display derivatives may still be JPEG, and FGA hosted components do not
mirror the uploaded image. See [PNG research](research/png-experiment.md) and
[vision and scope](vision-and-scope.md#non-goals-for-the-first-usable-version).

### Q009 — An impossible queue head

Resolved: `needs_attention` is terminal and atomically leaves active FIFO
membership, so later work may advance. Permanent moderation and ambiguity
blocks remain separate, stronger safety facts. See the
[group-submission status contract](queue-status-api.md).

### Q010 — “Nightly” queue timing

Resolved: the current design is not timezone-based nightly queue walking. The
FGA database stores exact due times, Cloud Scheduler runs the due sweep at least
once per minute, and Flickr code `5` sets only that partition's conservative
next probe time. See the [worker persistence and scheduler
contract](worker-persistence-scheduler-contract.md#due-work-model-and-wakeups).

### Q011 — Reorder, cancel, reopen, and manual retry controls

Resolved for the private MVP: status is read-only and exposes none of those
commands. Any future mutation requires a separate decision defining its FIFO
and fail-polite consequences. See
[ADR 0034](decisions/0034-expose-read-only-group-submission-status.md).

### Q012 — Operational attempt-history retention

Resolved for the low-volume private deployment: durable intents, attempts,
dispatch evidence, and administrative audit remain retained; the private MVP
has no automatic pruning job. Permanent photo/group blocks are independent of
attempt history, excluded from ordinary retention, and retained for as long as
the user's operational data. See
[ADR 0007](decisions/0007-fail-polite-group-submissions.md) and the
[worker persistence contract](worker-persistence-scheduler-contract.md#relational-state).

### Q015 — Direct-upload authorization boundary

Resolved: service-signed direct upload passed through the Lightroom Classic
host's `LrHttp.postMultipart`, and Flickr reported the uploaded Original as
PNG. The FGA API backend receives no image bytes, and the FGA LrC plug-in
receives no Flickr secret. See
[ADR 0005](decisions/0005-service-signed-direct-upload.md) and the
[signing-boundary evidence](research/upload-signing-boundary.md).

### Q016 — Hosted provider and deployment shape

Resolved platform direction on 2026-09-06:
[ADR 0050](decisions/0050-select-cloudflare-and-evaluate-native-storage-first.md) selects Cloudflare and evaluates
Durable Objects and D1 first, with RDS PostgreSQL as fallback. Storage
conformance, detailed deployment mapping, and the secret-lifecycle issue
remain explicit proof or review work. ADR 0033 and the dated provider
comparison are historical evidence. Accepted browser authentication and the
authoritative interaction maps remain unchanged.

### Q017 — Private-MVP token and metadata recovery/deletion

Resolved for the private owner-operated deployment: versioned managed-secret
references, grant replacement/disconnection, installation credential
revocation/rotation, database backups, retained safety records, and full
decommissioning are explicit. Public account erasure remains a deferred scope
change under Q013. See the [OAuth and account
lifecycle](oauth-and-account-lifecycle.md) and [installation credential
lifecycle](installation-credential-lifecycle.md).
