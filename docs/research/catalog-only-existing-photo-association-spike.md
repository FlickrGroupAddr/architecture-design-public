# Catalog-only existing-photo association spike

Last updated: 2026-08-28

Status: ticket #0067 disposable-catalog host probe passed and its synthetic
Flickr photo was deleted; ADR 0038 keeps product behavior queue-only

## Scope and fixture

The probe used only a purpose-built disposable Lightroom Classic catalog, the
development-only FGA Diagnostics 0.4.0.10 provider, and the deterministic
160x120 public-safe fixture with SHA2-256
`a64d5bfa01b27dcb6772b388baaef4e9e6289886bd40f2a8e26c573f65014968`.
Adobe's Flickr plug-in uploaded that fixture exactly once as a public, Safe
photo, without an album or group addition.

Flickr recorded upload time `2026-08-27T15:13:13-04:00`, photo ID
`55491872256`, and photopage
`https://www.flickr.com/photos/terryott/55491872256/`. An unauthenticated final
request returned HTTP 200 at that exact URL. Flickr's unauthenticated oEmbed
response identified the resource as a photo titled
`catalog-association-0067.jpg`. After that evidence capture, Terry clarified
that test fixtures must avoid public follower/feed exposure whenever possible
and directed deletion. The exact owner/title-verified fixture was immediately
made private, after which an unauthenticated request returned HTTP 403. The
existing integration-test OAuth grant lacks delete permission and was not
broadened for cleanup. Terry deleted the exact private fixture through Flickr's
UI and confirmed from his logged-in Photostream—which includes his private
uploads—that the fixture was absent. No replacement, second upload, album
mutation, or group mutation occurred. The deletion was owner-directed cleanup
after the probe, not provider behavior exercised by the probe.

The probe matched catalog records by the exact fixture bytes rather than a
catalog path. That excluded a different private synthetic photo already present
in the disposable catalog and prevented a visually plausible but false source
association.

## Observed Lightroom Classic behavior

The probe used documented
`LrPublishedCollection:addPhotoByRemoteId(photo, remoteID, remoteUrl, true)` to
create one record owned by the FGA diagnostics provider. Across every phase,
the Adobe Flickr source record retained the same photo, remote ID, remote URL,
publish count `1`, and unedited state.

| Operation | Observation |
| --- | --- |
| Create association | One FGA provider-scoped published-photo record appeared with the same remote ID and URL. A complete before/after source snapshot matched. |
| Normal restart | Both provider records survived two normal Lightroom Classic host restarts with stable service/collection identifiers, remote identity, publish count, and edited state. |
| Harmless metadata edit | A one-star rating placed only the FGA association in **Modified Photos to Re-Publish**. Adobe's Flickr source record remained unedited. |
| Publish modified association | The diagnostics provider received one `processRenderedPhotos` call, skipped one rendition before rendering, and reported upload failure. Its implementation has no networking boundary. |
| Remove association | `removePhotos` produced one pending local deletion. **Publish Now** invoked `deletePhotosFromPublishedCollection`, acknowledged that local record, and left the Adobe Flickr source intact. |
| Undo create | Lightroom Classic's **Undo Create ticket #0067 catalog-only association** removed the new FGA record without invoking a publish or deletion callback. |
| Recreate after Undo | The association could be recreated, survived another normal restart, and was removed through the same local-only callback path. |

The final catalog report contained one Adobe Flickr source record and zero FGA
association records. The cumulative diagnostics counters were one blocked
publish rendition, one `processRenderedPhotos` call, two acknowledged local
association removals, and zero catalog-photo-delete, published-collection-
delete, or publish-service-delete callbacks.

## Conclusion and limits

The current Lightroom Classic host can create a reversible, restart-persistent,
provider-scoped catalog association for an existing Flickr photo using the
documented SDK API. The association is not a transfer of Adobe's Flickr record,
Flickr photo ownership, pixels, album membership, group membership, or hosted
proof. Its modified and removal states require deliberate provider behavior;
an ordinary network-capable publish provider could otherwise treat them as
remote work.

This one synthetic-photo result does not accept the association as FGA product
behavior, authorize production-catalog mutation, or make catalog state
authoritative for current Flickr ownership/public visibility. Queue-only
existing-photo intake remains the accepted behavior.
[ADR 0038](../decisions/0038-keep-existing-photo-intake-queue-only.md) concludes
that the observed mechanism does not justify the extra provider record and its
republish/removal lifecycle when queue-only intake already meets the customer
requirement. Any later reconsideration must identify an unmet requirement and
retain the explicit-action, fresh-hosted-proof, no-network-republish,
local-only-removal, provenance, and reconciliation safeguards.
