# Lightroom Classic SDK research

Verified locally: 2026-08-20; additional catalog evidence: 2026-08-23; Flickr
sample workflow inspection: 2026-08-24; group-selection API review: 2026-09-04

## Environment

- Installed Lightroom Classic: 15.5
- Newest SDK offered by Adobe Developer Console at download time: 15.3
- SDK build: `202604090947-8f3672ed`
- Local SDK path: `vendor/LrC SDK/15.3/` (ignored by Git)
- Installed Adobe publisher:
  `C:\Program Files\Adobe\Adobe Lightroom Classic\Flickr.lrplugin`

Adobe may ship an SDK version behind the current Lightroom application. The
15.3 SDK is the correct local reference until Adobe publishes a newer download.

## PNG capability

The 15.3 SDK API reference lists these still-image render formats for export
settings and provider restrictions:

```text
ORIGINAL, JPEG, JXL, AVIF, PNG, TIFF, PSD, PSB, DNG
```

A provider can expose a subset through `allowFileFormats`; therefore an FGA
publish provider can offer PNG and JPEG even though Adobe's Flickr sample sets:

```lua
allowFileFormats = { 'JPEG' }
```

The provider can similarly restrict color-space choices to sRGB, Adobe RGB, or
ProPhoto RGB. The completed local matrix and Flickr round-trip are recorded in
[the PNG experiment](png-experiment.md).

Local references in the licensed SDK:

- `API Reference/modules/SDK - Export service provider.html`
- `API Reference/modules/LrExportSettings.html`
- `Sample Plugins/flickr.lrdevplugin/FlickrExportServiceProvider.lua`

## Installed provider versus SDK sample

These are not the same implementation:

- The installed production `Flickr.lrplugin` is a roughly 70 KB Windows PE
  binary. Its embedded strings show OAuth and Flickr API behavior, but it is not
  provided as editable Lua source and has no documented FGA extension point.
- The SDK's `flickr.lrdevplugin` is Lua sample source. It is an old reference
  implementation and explicitly reports that it does not support Flickr OAuth.
- The production provider does use OAuth 1.0a, consistent with Flickr's current
  requirements.

Consequently, “extend Adobe's plug-in” is not currently a viable implementation
path. The project can build the FGA LrC plug-in as a separate publish provider
using documented SDK interfaces. A separate companion plug-in could observe
published Flickr remote IDs, but it would not solve the built-in publisher's
JPEG restriction.

### Flickr plug-in terminology and source-evidence boundary

In this project, **Flickr plug-in** means Adobe's maintained Lightroom Classic
Flickr publish service that ships with the application. **FGA plug-in** in
owner discussion means the `FGA LrC plug-in`. These names are not
interchangeable.

The SDK 15.3 payload includes the licensed Lua source for Adobe's Flickr
*sample* under `Sample Plugins/flickr.lrdevplugin/`. Its package metadata carries
the SDK 15.3 build number, while its service declaration and implementation are
SDK-3.0-era sample code. It is valuable evidence for Adobe's provider model and
the workflow mechanics available through documented callbacks. It is not proof
that the installed binary Flickr plug-in has the same code, current labels, or
current behavior. Terry's current installed behavior and owner walkthroughs are
authoritative for the required customer-job baseline; the sample is
corroborating implementation evidence, not product-design guidance.

### Capability mechanics evidenced by the Flickr sample

The sample implements the following complete publish-service shape:

- A Flickr account connection is required before publication. Service-level
  controls select the Flickr title source and fallback, republish-title
  behavior, public/private visibility with friend and family access, safety
  level, public-area visibility, and Flickr content type. Lightroom Classic's
  standard file naming, file settings, sizing, sharpening, metadata, and
  watermarking sections remain available. The sample itself restricts output
  to JPEG and sRGB and rejects video; those are sample choices, not SDK limits.
- Adobe's Flickr sample opts into a non-deletable default Photostream plus
  user-created ordinary and smart published collections through the documented
  optional `getCollectionBehaviorInfo` callback. The sample labels those
  containers as photosets and disallows nested collection sets. The installed
  Flickr plug-in and Terry's workflow use the current **Album** terminology.
  The FGA LrC plug-in deliberately omits that callback, creates no default
  collection, and supports user-created ordinary Albums only under
  ADRs 0028 and 0029.
- A single `processRenderedPhotos` callback handles the exact rendition set
  selected by the Lightroom Classic host, whether one photo or several, and
  receives the published collection's local name and existing remote binding.
  The sample has no separate provider callback for a photo-level versus
  collection-level `Publish Now` command. Terry's observed selected-photo and
  album commands therefore converge on the same conventional provider boundary;
  host selection determines the work set.
- An empty local published collection has no Flickr album yet. After the first
  successful upload, the provider uses that real Flickr photo as the album's
  required primary photo, creates or reconciles the remote album, adds each
  uploaded photo to it, and records opaque remote photo and collection IDs plus
  navigation URLs in Lightroom Classic. This directly corroborates the lazy
  first-photo path now defined in the [album-scoped publish
  contract](../album-scoped-publish-contract.md). The [album-write
  reconciliation contract](../album-write-reconciliation.md) defines ambiguous
  create and attachment outcomes.
- Publication carries Lightroom title, caption, export keywords, GPS, and
  capture date semantics. Changes to those fields mark a published photo for
  republication. The sample updates title/description, permissions, safety,
  content type, and tags during replacement and takes care not to erase tags
  that were added outside Lightroom Classic. The FGA LrC plug-in and hosted
  components must define their own explicit metadata authority rather than
  inherit these choices accidentally.
- For a Flickr Pro account, republication replaces the existing Flickr photo
  while retaining its remote identity. The sample's free-account delete-and-
  reupload fallback can lose comments and favorites; it is irrelevant to FGA's
  required Flickr Pro baseline and should not be copied.
- The provider supports opening the remote album or photo, renaming a bound
  album, propagating user sort order while retaining externally added album
  photos, deleting remote photos and albums, reading Flickr comments and
  favorite counts into Lightroom Classic, and posting a new Flickr comment from
  Lightroom Classic. These are available Flickr plug-in capabilities, but only
  the jobs Terry actually uses become required FGA scope through ticket #0065.

The important UX consequence is that the FGA LrC plug-in can retain Lightroom
Classic's native publication state machine and `Publish Now` commands without
copying the Flickr plug-in's surrounding UI. For Terry's normal one-photo loop,
the publish callback is a documented place to present one FGA preflight before
render/upload. An album-level publish can contain many renditions, so a design
that opens an independent group dialog for every photo would create serial
modal friction and is not acceptable. The batch path instead needs one coherent
preflight or previously prepared per-photo group intents. Ticket #0065 records
the customer workflow decision; the album-scoped and album-write reconciliation
contracts define binding and failure-safe materialization.

### External Flickr replacement state probe

On 2026-08-26 Terry used Lightroom Classic 15.5 and the installed Flickr
plug-in with a fresh disposable catalog and one private synthetic photo. After
the Flickr plug-in published the baseline PNG, Terry performed exactly one
replacement through Flickr's website with a visibly different synthetic PNG.
The same Flickr photopage showed the replacement while retaining the original
title.

The Flickr plug-in did not reconcile that external pixel change. In the active
Lightroom Classic host session, the catalog record remained under **Published
Photos**, retained the baseline thumbnail, and did not enter a modified or
republish state. The same state and thumbnail remained after a normal
Lightroom Classic host restart and reopening the disposable catalog. The
published-photo context menu exposed **Show in Flickr** and **Mark to
Republish**, but no supported pull, refresh, or reassociation action. Marking the
photo for republication was deliberately not attempted because it would start
a new write using the catalog's baseline source rather than reconcile the
external replacement.

This result is limited to externally replaced image content and publication
state. It does not establish one-way behavior for comments, favorites, or every
metadata field. Terry also confirmed that his normal workflow has used the
Flickr plug-in, not Flickr's website editing dialog, for adding or changing
photo content for years. The website replacement was a controlled probe only.
Any future FGA hosted replacement would therefore introduce an external
mutation that leaves the Flickr plug-in's provider-owned catalog state stale
unless a separately proven, documented reconciliation mechanism exists.

## Publish integration observations

The SDK supports custom export and publish service providers. A custom provider
receives Lightroom render results, performs the remote upload, and records the
remote Flickr photo ID. That is the cleanest integration point for combining PNG
upload with group-intent capture.

The documented SDK object for the provider's local photo container is
`LrPublishedCollection`. A provider can customize its displayed name through
`titleForPublishedCollection`. Adobe's built-in Flickr provider uses **Album**
because it maps that container to a Flickr album. Terry confirmed that the
product must preserve the same one-to-one conceptual relationship: every
user-created ordinary FGA published collection corresponds to one Flickr album,
and every photo published from it must eventually be attached there. The
[album-scoped publish contract](../album-scoped-publish-contract.md) settles the
displayed label and binding lifecycle rather than defaulting to a local-only
collection.

Terry supplied private screenshots on 2026-08-23 showing the built-in Flickr
publish service interaction. Structurally, right-clicking the service offers
**Create Album…** and **Create Smart Album…**. Terry's normal workflow is to
choose **Create Album…**, add candidate photos to that Lightroom album container
while culling, then edit and publish the survivors individually. The album
context offers **Publish Now**. Lightroom separately displays published photos
and modified photos needing republication; an already-published photo has a
state-specific **Mark to Republish** action. Terry can dispatch selected work or
the album's pending work through Lightroom's native publishing controls. The
screenshots contain private photography and catalog metadata and are not
retained in Git.

The SDK 15.3 reference provides the conventional hooks needed to preserve this
shape without undocumented integration:

- `titleForPublishedCollection` and its standalone form customize Lightroom's
  published-collection terminology to **Album**;
- `viewForCollectionSettings` and `updateCollectionSettings` support the normal
  create/edit dialog and durable plug-in-specific settings;
- `renamePublishedCollection`, `reparentPublishedCollection`,
  `shouldDeletePublishedCollection`, and `deletePublishedCollection` expose the
  corresponding lifecycle boundaries;
- `exportSession:recordRemoteCollectionId` and
  `exportSession:recordRemoteCollectionUrl` persist the remote binding; and
- `LrPublishedCollection:getRemoteId` and `getRemoteUrl` read it later.

The [album lifecycle contract](../album-lifecycle-contract.md) now distinguishes
those callbacks deliberately: rename can create a reconciled Flickr title
intent, reparent is local-only, and removing a local photo or album does not
delete Flickr content or membership. Callback availability is a control point,
not authorization to mirror destructive behavior.

The FGA LrC plug-in can therefore use Lightroom Classic's native publish-service
interaction: right-click the FGA publish service, choose **Create Album…**, cull
and edit inside the resulting published collection, and use Lightroom Classic's
native publish commands and status sections. This proves a conventional
implementation path;
it does not require the FGA LrC plug-in to copy Adobe's UI. A custom or combined
interaction must earn its place by reducing Terry's work without hiding state
or losing a current capability. Smart-album support is visible in the built-in
provider, but Terry
explicitly chose ordinary albums only: automatic rule-based membership
conflicts with his deliberate cull and publication model. ADR 0028
records that product-scope exclusion. Ticket #0065 owns the complete
current-workflow inventory and challenge.

A separate plug-in can enumerate catalog publish services and published photos
and inspect their remote IDs. This could augment Adobe's publisher after the
fact, but no global cross-provider “after publish” callback was found. Such a
companion would need polling/reconciliation or an explicit user command, and it
would leave upload format under Adobe's provider.

### Per-photo group-selection API evidence

The 2026-09-04 review for ticket #0068 found a complete documented SDK path for
the approved one-photo interaction. It also found no documented hook for
injecting an arbitrary per-photo control into the Publish Services panel or a
published-photo context menu.

The Adobe SDK 15.3 Hello World and Custom Metadata sample plug-ins demonstrate
`LrLibraryMenuItems`, including the documented `photosAvailable` enablement
condition. The API Reference documents:

- `LrCatalog:getTargetPhotos()` and `getActiveSources()` for resolving the
  selected photo and visible FGA Album;
- `LrPublishedCollection:type()`, `isSmartCollection()`, `getService()`, and
  `localIdentifier`, plus `LrPublishService:getPluginId()` and
  `localIdentifier`, for validating the Album and service scope;
- `LrPhoto:getContainedPublishedCollections()` and `getRawMetadata("uuid")`
  for verifying membership and retaining persistent local photo identity;
- `LrDialogs.presentModalDialog`, `LrBinding.makePropertyTable`, and the
  documented `LrView` radio-button, checkbox, and scrolled-view controls for a
  native selector;
- an untitled private `LrMetadataProvider` string field for catalog-persisted
  per-photo plug-in state;
- `LrPhoto:getPropertyForPlugin()` and `setPropertyForPlugin()` for that field,
  with `LrCatalog:withPrivateWriteAccessDo()` providing the narrow write gate;
  and
- `LrExportContext.publishService` and `publishedCollection` for reading the
  exact saved scope during a publish callback.

Collection settings accept only collection-level plug-in scalars and would
require one growing encoded map for every photo. `LrPrefs` is application-wide,
not catalog/photo-scoped. Private per-photo custom metadata is therefore the
conventional durable store for the editable selection, while a Library command
and native modal provide the supported interaction.
[ADR 0045](../decisions/0045-use-a-library-modal-and-photo-metadata-for-group-selection.md)
specifies the exact context checks, record shape, lifecycle, and multi-photo
behavior.

Local references in the licensed SDK:

- `Sample Plugins/helloworld.lrdevplugin/Info.lua`
- `Sample Plugins/custommetadatasample.lrdevplugin/Info.lua`
- `Sample Plugins/custommetadatasample.lrdevplugin/CustomMetadataDefinition.lua`
- `API Reference/modules/LrCatalog.html`
- `API Reference/modules/LrPhoto.html`
- `API Reference/modules/LrPublishedCollection.html`
- `API Reference/modules/LrPublishService.html`
- `API Reference/modules/LrDialogs.html`
- `API Reference/modules/LrView.html`
- `API Reference/modules/LrExportContext.html`

### Existing-public-photo selector evidence

The SDK 15.3 API Reference documents `LrDialogs.presentModalDialog` and ordinary
`LrView` hierarchies, which provide the conventional in-Lightroom Classic
boundary for the explicit **Add Groups to Existing Flickr Photo…** command. The
documented `LrView.picture` value is a static file or plug-in resource, not a
remote URL. The [existing-public-photo selector
spike](existing-public-photo-selector-spike.md) implements a bounded current-page
local cache and a modal-per-page interaction with fixture data. Its offline
checks pass; current Lightroom Classic host acceptance still must establish
actual layout and interaction behavior.

The documented catalog API can enumerate publish services, so stored remote IDs
may supply optional labels or shortcuts. They cannot hide an otherwise eligible
public Flickr photo, establish current ownership or visibility, or become a
catalog-mutation mechanism. The hosted exact-photo proof remains authoritative.

The same SDK documents `LrPublishedCollection:addPhotoByRemoteId`, which adds a
catalog photo and remote ID/URL to one published collection and can mark it
already published. It also documents `addPublishedPhotos`, mutable
`LrPublishedPhoto` remote fields, and a `setParent` restriction that rejects a
different publish service or connection. These are publication-record APIs,
not a cross-provider migration contract. Calling `addPhotoByRemoteId` would
create an FGA-owned catalog association; it would not transfer a Flickr plug-in
record, change Flickr album membership, or prove local/remote pixel identity.

The queue-only existing-photo path therefore performs no catalog write. Ticket
#0067's [disposable-catalog host
probe](catalog-only-existing-photo-association-spike.md) proved that a provider-
scoped association can be created, survive restart, enter a provider-specific
republish state, be removed locally, and be undone without changing Adobe's
Flickr source record. That technical result does not accept the association as
product behavior.
[ADR 0038](../decisions/0038-keep-existing-photo-intake-queue-only.md) reviews
those safeguards and keeps production behavior queue-only because the extra
provider record and republish/removal lifecycle do not satisfy an unmet
customer requirement.

Local primary sources: licensed SDK 15.3
`API Reference/modules/LrDialogs.html`,
`API Reference/modules/LrView.html`, and
`API Reference/modules/LrCatalog.html`. The publication-record boundary also
uses `API Reference/modules/LrPublishedCollection.html`,
`API Reference/modules/LrPublishedPhoto.html`, and
`API Reference/modules/LrExportRendition.html`.

## Read-only production-catalog evidence

On 2026-08-23 Terry authorized read-only inspection of the current Lightroom
Classic catalog beneath the protected photography root. The query used Python's
standard SQLite library with URI `mode=ro` and `PRAGMA query_only=ON`. It emitted
only schema names and aggregate results; no collection name, source path,
filename, caption, coordinate, thumbnail, Flickr photo ID, album ID, or album
URL was printed or retained.

The catalog schema contains:

- `AgLibraryPublishedCollection`, including `remoteCollectionId` and
  `publishedUrl`;
- `AgLibraryPublishedCollectionImage`, which explicitly relates a published
  collection to catalog images; and
- `AgLibraryPublishedCollectionContent`, which records provider-owned published
  content relationships.

Every populated published-collection remote ID in this catalog was unique, and
every populated published URL was also unique. Explicit collection/image rows
confirm that Lightroom Classic retains per-collection photo membership. The
stored Flickr URLs use Flickr's legacy `/sets/` path shape rather than its
current `/albums/` presentation. The FGA LrC plug-in, FGA API backend, FGA album
worker, and FGA database must therefore treat the opaque remote collection ID as
album identity and treat the URL as display/navigation data; no component may
derive identity by parsing either URL spelling.

This inspection corroborates the one-to-one product model and informs migration
research only. Lightroom's catalog schema is undocumented and is not an FGA
implementation contract. Production FGA LrC plug-in code must use documented
Lightroom SDK APIs and must not query or mutate the catalog database directly.
Exact private aggregate counts and the sanitized handoff are retained on FGA
localswim ticket #0060 rather than in this public repository.

## JSON support

The 15.3 SDK exposes `LrXml` for XML parsing and generation but no corresponding
JSON module was found. Flickr supports JSON REST responses, and JSON is also the
natural payload format for the hosted FGA service.

FGA vendors unmodified dkjson 2.11 inside the deployable Lightroom plug-in.
dkjson is a dependency-free pure-Lua module, supports Lua 5.1 through 5.5, and
is released under the same permissive terms as Lua. The author's published
SHA2-256 was verified before import. Its provenance, checksum, and retained
license are recorded beside the vendored source. This library replaces FGA's
initial diagnostic-only JSON encoder and supplies both encoding and decoding.

## Upload and credential primitives

`LrHttp.postMultipart` can stream a rendered file by path while sending
caller-provided HTTP headers. `LrPasswords` provides plug-in-scoped encrypted
storage backed by operating-system services. These APIs support the candidate
direct-upload boundary without loading a PNG into Lua memory or storing the FGA
installation credential in ordinary preferences.

The SDK 15.3 `LrPasswords` reference lists only `retrieve` and `store`; it does
not document a delete operation. The FGA LrC plug-in therefore clears its fixed
credential key by storing an empty string, retrieving it to verify the empty
value, and treating both empty and absent values as disconnected. It must not
call a runtime-visible but undocumented delete symbol.

The 15.3 `LrHttp.get(url, headers, timeout)` reference documents a caller-
supplied table whose entries contain `field` and `value`, and Adobe's own module
example uses an `Authorization` header. This directly supports
`Authorization: Bearer <FGA installation credential>` on every FGA request.
The same reference documents returned `Set-Cookie` headers and
`LrHttp.parseCookie`, but it does not document a persistent cookie jar,
automatic replay, or an `HttpOnly` storage/isolation contract. Cookie-based
plug-in authentication would therefore require Lua to handle and resend the
secret itself and would provide no documented advantage over the explicit
authorization header.

Local primary source: licensed SDK 15.3
`API Reference/modules/LrHttp.html`, restored beneath the ignored
`vendor/LrC SDK/15.3/` directory according to
[`vendor/LrC SDK/README.md`](../../vendor/LrC%20SDK/README.md).

The 15.3 `LrHttp` reference documents HTTP and HTTPS support plus generic
security and certificate error categories. It does not document a minimum or
maximum TLS version, a way to select a TLS version, a promise to negotiate the
newest mutually supported version, or a way to inspect the negotiated version.
The honest plug-in contract is therefore only HTTPS: the actual TLS version is
an implementation detail of the current Lightroom networking stack and remote
server. If FGA chooses a TLS 1.3-or-newer edge minimum, that is an FGA deployment
policy whose compatibility with the target Lightroom release must be tested;
it is not an Adobe SDK guarantee.

The project owner prefers to attempt that TLS 1.3-or-newer-only policy first
because FGA has one required, always-current LrC-on-Windows client target. The
acceptance and independent scanner matrix is recorded in
[FGA HTTPS-edge TLS deployment acceptance](../operations/tls-edge-acceptance.md).

The SDK exposes no documented secure-random source or general-purpose UUID
generator. Lightroom object UUIDs and machine- or installation-keyed identifiers
are stable identities, not entropy. `LrPasswords` stores an existing secret but
does not generate one. The applicable hosted FGA component must therefore
generate pairing codes, installation credentials, OAuth nonces, and other
security-sensitive random values through its runtime's cryptographically secure
random generator and send only scoped results to the FGA LrC plug-in over
HTTPS.

`LrUUID` is reportedly runtime-visible but is not documented in Adobe's SDK API
Reference. The FGA LrC plug-in will not call it or any other undocumented
Lightroom interface.
Runtime presence is not a support contract, and an undocumented UUID source
would not establish cryptographic security anyway. The annual SDK inventory
review will reconsider the boundary only if Adobe publishes a documented
replacement or contract.

The documented `LrDigest.HMAC` algorithms do not include Flickr's required
HMAC with SHA1-160. The evidence and completed service-signing experiment are
recorded in [direct-upload signing research](upload-signing-boundary.md).

## Licensing boundary

Adobe sample files contain this type of header:

```text
Adobe permits you to use, modify, and distribute this file in accordance with
the terms of the Adobe license agreement accompanying it.
```

No file named as a license, EULA, legal notice, or terms document was found in
the downloaded SDK tree. The governing agreement is the [Adobe Developer Terms
of Use](https://www.adobe.com/go/developer-terms), last updated June 18, 2024.
Those terms expressly cover the Adobe Developer Console and Developer Tools,
including SDK files and Sample Code. They define Sample Code as code Adobe
includes for incorporation into developer software and grant development/test
use and reproduction. Distribution of Developer Tools or portions of them is,
however, limited to approved developer software in object-code form, and the
grant is non-sublicensable, non-transferable, and revocable. Adobe also requires
its copyright and proprietary notices to remain on copies.

That boundary is incompatible with copying Adobe Lua source into FGA's public
MIT repository: Lua source distribution is not object-code distribution, and
MIT would purport to give downstream recipients rights Adobe's terms do not
grant. The reviewed working rule is therefore:

- Use the SDK documentation to understand the interface.
- Implement FGA source originally against that interface.
- Do not copy Adobe sample implementation into tracked FGA source.
- Keep the SDK archive and extracted tree local and Git-ignored.
- Use bundled samples only as local development/reference fixtures under
  Adobe's terms; do not ship them with FGA.

The reviewed archive is Lightroom Classic SDK 15.3, build
`202604090947-8f3672ed`, SHA2-256
`5A33BA3F7DCA01EBB0EFD4348F4E7C1F2148947DC62DCB7611AC43B52430BFF0`.
On 2026-08-26, the Adobe Developer Console showed v15.3 (April 2026) as the
newest download for App Version 2026. This is a conservative engineering
boundary, not legal advice.
