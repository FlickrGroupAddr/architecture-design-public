# ADR 0045: Use a Library modal and photo metadata for group selection

Date: 2026-09-04

Status: Accepted by Terry on 2026-09-04

## Context

The accepted first-publish journey requires the photographer to save zero or
more add-only Flickr group choices for one photo in one FGA Album before using
Lightroom Classic's native publish action. A previously FGA-published photo
uses the same selector to request additional groups without rendering or
uploading the photo again. Current Flickr memberships and existing or blocked
submission pairs remain read-only.

The production interaction must use only interfaces documented in the newest
Adobe-published Lightroom Classic SDK. The local SDK 15.3 API Reference and
Adobe sample plug-ins establish the following supported building blocks:

- `LrLibraryMenuItems` registers a Library menu command;
- `LrCatalog:getTargetPhotos()` and `LrCatalog:getActiveSources()` identify the
  selected photos and visible source;
- `LrPublishedCollection:type()`, `getService()`, and `localIdentifier`, plus
  `LrPublishService:getPluginId()` and `localIdentifier`, identify one ordinary
  Album owned by the FGA LrC plug-in;
- `LrPhoto:getContainedPublishedCollections()` and
  `getRawMetadata("uuid")` verify the photo and Album scope;
- `LrDialogs.presentModalDialog`, `LrBinding.makePropertyTable`, and documented
  `LrView` radio-button, checkbox, text, and scrolled-view controls provide a
  native modal selector;
- an `LrMetadataProvider` field without a title is private plug-in metadata on
  an individual photo; and
- `LrPhoto:getPropertyForPlugin()`, `LrPhoto:setPropertyForPlugin()`, and
  `LrCatalog:withPrivateWriteAccessDo()` read and synchronously replace that field
  in the Lightroom Classic catalog without putting the edit on the ordinary
  undo stack.

The SDK exposes service and collection settings surfaces, but no documented
hook for injecting an arbitrary per-photo control into the Publish Services
panel or a published-photo context menu. `LrPrefs` is application-scoped rather
than catalog/photo-scoped. Collection settings are the wrong granularity and
would require repeatedly rewriting one growing photo map. Prompting once per
rendition from a multi-photo publish callback would serialize unrelated photos
and violate ADR 0009.

## Decision

The production FGA LrC plug-in registers exactly one routine
command through `LrLibraryMenuItems`, enabled under the documented
`photosAvailable` condition:

**Library > Plug-in Extras > FlickrGroupAddr: Choose Group Additions…**

The command starts one asynchronous task and proceeds only when all of these
conditions hold:

1. `catalog:getTargetPhotos()` returns exactly one photo;
2. `catalog:getActiveSources()` returns exactly one
   `LrPublishedCollection`;
3. that collection is an ordinary, non-smart collection whose parent
   `LrPublishService:getPluginId()` is the production FGA LrC plug-in ID; and
4. `photo:getContainedPublishedCollections()` contains that exact collection.

Otherwise the FGA LrC plug-in opens no selector and states the corrective
action: select one photo while viewing one ordinary FGA Album. Names and
titles are display only. The durable scope key is the tuple of the publish
service's numeric `localIdentifier`, the published collection's numeric
`localIdentifier`, and the photo's persistent `uuid` raw metadata.

After resolving the scope, the FGA LrC plug-in assembles the complete bounded
selector model required by the moderator-safety UI conformance contract. For a
photo without an FGA photo binding it displays **Not yet published by this FGA
collection** instead of a current-membership result and makes no Flickr
membership request. This state is distinct from **Unavailable**, which is
reserved for a failed or incomplete required read. For a bound photo it obtains
a new complete membership observation and complete retained intent history
before enabling any addition. An incomplete, failed, unknown, or contradictory
required projection disables the save/queue action; prior data is never
substituted as current reality.

The FGA LrC plug-in opens one resizable
`LrDialogs.presentModalDialog` titled **FlickrGroupAddr — Group additions**.
The dialog uses documented `LrView` controls and contains:

- the selected photo and FGA Album names as non-authoritative context;
- the writable-group snapshot status and refresh time;
- for a bound photo, timestamped **Currently in Flickr groups** and existing or
  protected submission rows, all read-only;
- for an unpublished photo, a radio choice between **No group additions** and
  **Add to selected groups**;
- one ordinary checkbox for each eligible group inside a `scrolled_view`,
  sorted by display name while retaining the exact Flickr group ID as identity;
  the checkboxes appear under **Add to selected groups** for an unpublished
  photo and directly for a bound photo; and
- **Save for publish** and **Cancel** actions for an unpublished photo, or
  **Queue selected additions** and **Cancel** for a bound photo.

For an unpublished photo, **Save for publish** is enabled only when **No group
additions** is selected or from one through 60 eligible group checkboxes are
selected. Choosing one mode clears the other mode. For a bound photo, **Queue
selected additions** is enabled only for one through 60 eligible group
checkboxes. Cancel changes no durable state. Current membership, an existing
intent, or a permanent submission block never has a checkbox, and deselection
never means removal, cancellation, retry, or resubmission.

For an unpublished photo, a successful save returns to Lightroom Classic and
the photographer invokes the Album's ordinary **Publish** action separately,
matching the approved storyboard. For a bound photo, a nonempty successful save
also snapshots the choice into the local outbox and enters the existing Phase 6
batch handoff without rendering or uploading. Closing or canceling a bound-photo
selector without additions is a local no-op and sends no empty batch.

### Durable selection record

The production FGA LrC plug-in declares one private, untitled string field named
`groupAdditionSelections` in its `LrMetadataProvider`. The field contains one
strictly validated JSON document attached to the selected `LrPhoto`:

```json
{
  "schemaVersion": 1,
  "entries": [
    {
      "publishServiceLocalId": 12,
      "publishedCollectionLocalId": 34,
      "photoUuid": "00000000-0000-0000-0000-000000000000",
      "selectionRevision": 1,
      "choice": "groups",
      "flickrGroupIds": ["111@N00", "222@N00"]
    }
  ]
}
```

There is at most one entry for each service/collection tuple in one photo's
field. `choice` is exactly `none` with an empty `flickrGroupIds` array, or
`groups` with one through 60 unique exact group IDs. Entries are ordered by
service then collection local ID; group IDs are ordered by their bytewise UTF-8
representation. `selectionRevision` starts at 1 and increments on every
successful replacement of that scoped entry. Local identifiers and the photo
UUID are non-secret catalog correlation, never authorization or entropy.

The FGA LrC plug-in reads, validates, modifies, and writes the entire field
inside one synchronous `catalog:withPrivateWriteAccessDo()` callback. It makes
no network request and opens no dialog while holding the write gate. The write
replaces only the resolved service/collection entry and preserves every other
valid entry. A timeout or write failure leaves the prior value unchanged and
keeps the in-memory dialog choice available for another save attempt. An
unknown schema, malformed JSON, duplicate scope, mismatched photo UUID,
invalid choice, duplicate or over-limit group set, or invalid identifier fails
closed and is never overwritten as though it were empty. An explicit repair
may reset the local field only after warning that unsent group choices could be
lost; it performs no Flickr or hosted mutation.

Before a render, each rendition reads the selection for the exact
`exportContext.publishService` and `exportContext.publishedCollection` scope and
copies its group IDs and `selectionRevision` into the separately durable local
recovery/outbox record. The editable selection remains until that copy is
durable. After the FGA API backend returns the durable Phase 6 `202` result, the
FGA LrC plug-in removes the consumed entry only if its current revision still
equals the snapshotted revision; a later user edit is never cleared by an older
handoff. An explicit zero-group entry is consumed after the corresponding new
photo has been recorded as published and its durable Album-attachment
obligation exists.

The menu command accepts exactly one photo. A multi-photo publish callback
opens no selector and no serial dialogs. It independently uses each photo's
already saved entry; an unpublished photo without one proceeds with zero group
additions and is reported as **No group additions were configured**. A malformed
entry fails only that photo before render rather than silently dropping its
unknown choices or blocking another photo.

The selection field stores no credential, OAuth material, authorization
header, Flickr photo metadata, photo title, filename, Album name, or group
display name. Recovery/outbox persistence remains a separate implementation
contract; this decision fixes only the editable selection record and the
handoff boundary into that store.

## Consequences

- The dominant one-photo workflow gets one explicit, native Lightroom Classic
  command and one modal; the accepted separate Publish action remains intact.
- The storage API is designed for private per-photo plug-in metadata instead of
  overloading machine preferences or collection settings.
- One photo can retain different pending choices for different FGA Albums or
  publish-service instances in the same catalog.
- The active Album is explicit and validated, so the same photo in several
  collections cannot receive an accidental cross-Album selection.
- Removing and later re-adding the same photo to the same still-existing FGA
  Album restores its unconsumed entry because the documented SDK exposes no
  separate stable membership-incarnation identifier. The selector shows that
  saved choice before another save or publish.
- Implementation must include a JSON codec and strict validator. Reuse a
  maintained, license-compatible codec; do not invent a delimiter format.
- The design uses only documented Lightroom SDK interfaces. It does not assume
  an injectable Publish Services panel, custom context menu, or undocumented
  module.

## Alternatives considered

- **Store one photo map in published-collection settings:** rejected because
  the surface is collection-level configuration and every edit would rewrite
  a growing aggregate unrelated to ordinary Album settings.
- **Store selections in `LrPrefs`:** rejected because preferences are not bound
  to one catalog, photo, publish service, or Album.
- **Prompt for every rendition during publication:** rejected because a batch
  would become a serial modal workflow and one unattended photo could block
  unrelated work.
- **Treat missing state as an error in every batch:** rejected because the
  accepted multi-photo boundary requires zero-group photos to keep progressing
  without serial confirmation dialogs.
- **Inject a published-photo context-menu item or panel control:** rejected
  because the SDK 15.3 API Reference documents no such extension point.
- **Use an undocumented module or Lightroom catalog internals:** rejected by
  the documented-API boundary.

## References

- [First-publish customer storyboard](../../prototypes/first-publish-storyboard/README.md)
- [Zero-state publish flow](../zero-state-publish-flow.md)
- [Lightroom Classic SDK research](../research/lightroom-classic.md)
- [Moderator-safety UI conformance contract](../moderator-safety-ui-conformance.md)
- [ADR 0009: Treat multi-photo publishing as eventually consistent and unordered](0009-eventually-consistent-unordered-publishing.md)
- [ADR 0010: Permit Flickr publication without group additions](0010-zero-group-publication.md)
