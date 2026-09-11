# Flickr API research

Verified: 2026-08-26

This document records externally changeable Flickr behavior. Recheck the linked
official sources before implementation or release.

## Authorized integration-test profile

The project's public Flickr profile is:

- <https://www.flickr.com/photos/terryott/>

The project owner explicitly approved committing this public URL. It is the
default account for manual API integration and PNG round-trip tests. Never
commit its OAuth access token, token secret, API key secret, session cookies,
or nonpublic account data. Runtime identifiers returned by Flickr should be
classified separately before deciding whether they belong in fixtures or logs.

## Uploads and PNG originals

Flickr's current help page lists JPEG and PNG as supported photo formats. It
says RAW is unsupported and each photo may be at most 200 MB. TIFF and BMP are
explicitly converted and saved as JPEG; that conversion warning is not attached
to PNG.

Flickr's image URL documentation says the original has a variable extension and
is the exact file uploaded. API responses expose `originalformat`; the official
`flickr.photos.getInfo` example demonstrates `originalformat="png"`.

Conclusions:

- A Lightroom-rendered PNG can be the Flickr original.
- “Original” means the exact rendered upload, not the Canon RAW source.
- Normal Flickr display sizes use `.jpg` URLs; the lossless benefit applies most
  clearly to the downloadable original.
- Full-resolution PNG output needs a size preflight against the 200 MB limit.

Official sources:

- [Flickr upload requirements](https://www.flickrhelp.com/hc/en-us/articles/4404079649300-Flickr-upload-requirements)
- [Photo upload API](https://www.flickr.com/services/api/upload.api.html)
- [Photo image URLs and originals](https://www.flickr.com/services/api/misc.urls.html)
- [`flickr.photos.getInfo`](https://www.flickr.com/services/api/flickr.photos.getInfo.html)

## Replacing an existing photo's pixels

Checked against Flickr's official replacement specification, current help
article, official SDK example, and the disposable live probe on 2026-08-26.

Flickr documents a binary replacement endpoint:

```text
POST https://up.flickr.com/services/replace/
```

The request requires `write` authentication, a binary `photo` field, and the
existing `photo_id`; the binary is excluded from the OAuth signature. Flickr's
successful example returns that same `photoid` and describes it as the ID of the
photo being replaced. The specification recommends asynchronous processing and
lists “Not a pro account” as a method-specific failure. Flickr's current SDK
repository also retains a replacement example that accepts an existing photo
ID.

Terry reports continuous Flickr Pro membership since 2018 and **MUST** maintain
it for FGA's supported lifetime. Flickr Pro is therefore the required account
tier rather than an optional deployment assumption. The replacement probe must
still verify the live account and endpoint response rather than treating the
contract or historical membership as an upstream API guarantee.

The specification and the 2026-08-26 disposable live probe provide strong
evidence that Flickr currently supports changing image bytes without creating a
new photo identity. In that one synchronous run, the response and fresh reads
retained the exact Flickr photo ID and photopage URL, and the Flickr Original
matched the exact intended 8-bit RGB PNG bytes. The controlled owner comment and
album context also remained present. This is not evidence for all of FGA's
required migration guarantees. The official specification does not state
whether a replacement preserves views, favorites, comments, photopage URL,
album or group membership, capture/upload dates, metadata, or the previous
original. It does not document rollback. Flickr's current help article
demonstrates replacement through the website but titles the feature “web only,”
which remains in tension with the still-published API specification, SDK
example, and successful live API observation.

The first test used a deliberately disposable synthetic public photo containing
no private photography data. It retained both generated renders locally,
recorded the before/after evidence, dispatched one synchronous replacement, and
then made the photo private and deleted its temporary album. The fixture had one
owner comment and one album context, but zero favorites and zero group contexts.
Separate authorized fixtures are therefore still required to measure nonzero
favorite and nonempty group-context preservation. Asynchronous processing and a
separately confirmed reverse replacement also remain untested; a reverse
replacement would be a new one-dispatch write, not evidence that Flickr retained
the old Original or supplied rollback.

Terry confirmed on 2026-08-26 that he has one Flickr account and no controlled
test group. The project accepts nonzero-favorite and nonempty-group preservation
as unproven rather than recruiting another account or involving a
volunteer-managed group in the experiment.

Even a successful test would justify only a separately accepted, explicitly
confirmed migration workflow. Bulk replacement of historical photos has a very
large destructive blast radius. It must begin with one-photo opt-in, durable
before/after evidence, reconciliation after ambiguous delivery, and no automatic
batch expansion until a later owner decision. FGA localswim ticket #0052 tracks
the evidence and acceptance gate.

The accepted [replacement ambiguity contract](../replacement-ambiguity-reconciliation.md)
defines that reconciliation conservatively. A durable dispatch marker permits
only one Flickr POST. The FGA replacement reconciliation worker can prove the
intended current bytes only by downloading the exact authoritative Original and
matching its SHA2-256, byte count, format, and dimensions. Observing the baseline
Original after dispatch is not retry permission because Flickr documents no
upper convergence bound. ADR 0023 records the no-replay decision.

The accepted [backup and reverse-replacement
contract](../replacement-backup-and-reverse-replacement.md) requires the exact
baseline Original and intended replacement in two verified local bundles before
dispatch. Sending the baseline bytes later is a newly confirmed replacement
operation under ADR 0023, not a Flickr rollback and not restoration of social or
metadata state. ADR 0024 records that distinction.

Official sources:

- [Flickr replacing-photos API](https://www.flickr.com/services/api/replace.api.html)
- [Flickr Help: Replace a photo in Flickr (web only)](https://www.flickrhelp.com/hc/en-us/articles/4404058489108-Replace-a-photo-in-Flickr-web-only)
- [Official Flickr SDK replacement example](https://github.com/flickr/flickr-sdk/blob/main/examples/README.md#replacejs)

## Flickr album creation and attachment

Verified against Flickr's official API documentation on 2026-08-23:

- [`flickr.photosets.create`](https://www.flickr.com/services/api/flickr.photosets.create.html)
  is an authenticated write `POST`. It requires a title and a
  `primary_photo_id` belonging to the calling user, and returns the new opaque
  photoset ID and URL.
- [`flickr.photosets.addPhoto`](https://www.flickr.com/services/api/flickr.photosets.addPhoto.html)
  is an authenticated write `POST` requiring `photoset_id` and `photo_id`.
  Flickr code `3` reports that the photo is already in the set and can satisfy
  the desired-membership postcondition.
- [`flickr.photosets.removePhoto`](https://www.flickr.com/services/api/flickr.photosets.removePhoto.html)
  is a separate authenticated write `POST` for that exact relationship. An add
  is therefore not a move, and removing old membership is never implied by
  associating or queueing an existing photo.
- Flickr's [API overview](https://www.flickr.com/services/api/misc.overview.html)
  says identifiers including photoset IDs must be treated as opaque strings.

Flickr's create contract means an empty Lightroom Classic album cannot be
materialized remotely through the documented API before the first photo has a
Flickr photo ID. The conventional mapping is therefore:

1. Lightroom Classic creates the FGA published collection locally when Terry
   chooses **Create Album…**.
2. Terry adds candidates, culls, and edits without needing a remote Flickr
   album yet.
3. The first successful photo upload supplies the required Flickr photo ID.
4. The FGA album-binding workflow creates the Flickr photoset with that photo as
   primary, then records the returned opaque remote collection ID and URL in
   Lightroom Classic through documented SDK methods.
5. Later photos use `flickr.photosets.addPhoto` for the same remote ID.

Terry accepted this recommendation on 2026-08-25. The accepted
[album-scoped publish contract](../album-scoped-publish-contract.md) now defines
the local identity, hosted binding, first-photo materialization, and catalog
repair path. Album creation is not safely replayable after an ambiguous result:
a blind retry can create a second photoset, and a title is not a unique identity.
The album-write contract must retain read-after-write reconciliation and a
truthful repair state for ambiguous creation or attachment. The
[album lifecycle contract](../album-lifecycle-contract.md) separately defines
rename and deletion semantics; neither is inferred from local UI actions.

The accepted [album-write reconciliation
contract](../album-write-reconciliation.md) now applies a durable marker to both
writes without pretending their retry semantics match. An ambiguous create is
never replayed and requires an owner-selected, freshly verified photoset.
`addPhoto` instead reconciles the exact set-like membership: present is success,
verified absence can retry, and unavailable evidence sends no write.
ADR 0026 records this split.

Flickr's documented `photosets.editMeta` POST requires the photoset ID and new
title while making description optional. The accepted [album lifecycle
contract](../album-lifecycle-contract.md) therefore synchronizes an explicit
local rename without sending a description. Flickr also publishes photoset
delete and membership-removal POSTs, but the FGA LrC plug-in does not call them
from a local Lightroom Classic removal. ADR 0027 keeps reparenting and
deletion non-destructive.

The existing-public-photo group-intake path does not call any photoset write.
Its common FGA photo binding identifies the Flickr photo but proves no album
membership. The separate
[non-destructive existing-photo boundary](../non-destructive-existing-photo-boundary.md)
keeps those relations explicit.

## Authentication

Flickr uses OAuth 1.0 Revision A for web, desktop, and mobile applications.
Requests are signed using HMAC with SHA1-160. Upload and group-add operations
require `write` permission.

Flickr's documented `flickr.auth.oauth.checkToken` method returns the
credentials attached to an OAuth token, including the Flickr user identity and
permission level. It is the conventional non-mutating repair check for a paused
FGA linked-user or deployment write gate: the FGA API backend can require the
expected owner NSID and at least `write` permission using the exact application
configuration and grant that future work will use. `flickr.test.login` proves
only authenticated `read` access and is therefore insufficient by itself for
safe write-gate resume.

Flickr uses separate hosts for ordinary OAuth/REST traffic and binary upload:

| Purpose | Endpoint |
| --- | --- |
| Request token | `GET https://www.flickr.com/services/oauth/request_token` |
| User authorization | `https://www.flickr.com/services/oauth/authorize` |
| Access token | `GET https://www.flickr.com/services/oauth/access_token` |
| Ordinary REST methods | `GET` or `POST https://www.flickr.com/services/rest/` with a `method` parameter |
| Binary photo upload | `POST https://up.flickr.com/services/upload/` |

### Apex versus `www`

On 2026-08-21, a direct check found that `flickr.com` and `www.flickr.com`
returned the same IPv4 CDN address set. Both served `/` and
`/services/rest/?method=flickr.test.echo` directly with `200`; neither
redirected to the other. In that check, `www.flickr.com` also published IPv6
AAAA records while the apex did not.

FGA nevertheless uses Flickr's documented `www.flickr.com` OAuth and REST
origins. The exact request URL is an OAuth 1.0a signature input, so substituting
the currently functional apex would create an unnecessary undocumented
dependency. This does not affect FGA's own no-`www` choice:
`https://flickrgroupaddr.com` is the selected FGA origin.

The upload endpoint is:

```text
POST https://up.flickr.com/services/upload/
```

The upload specification says the binary `photo` parameter is excluded from the
signature while all other POST parameters are included. This creates a possible
design in which the hosted service signs an upload while the plug-in streams the
file directly to Flickr; it remains an unverified hypothesis, not a decision.

Official sources:

- [Flickr OAuth](https://www.flickr.com/services/api/auth.oauth.html)
- [`flickr.auth.oauth.checkToken`](https://www.flickr.com/services/api/flickr.auth.oauth.checkToken.htm)
- [`flickr.test.login`](https://www.flickr.com/services/api/flickr.test.login.htm)
- [Flickr REST request format](https://www.flickr.com/services/api/request.rest.html)
- [Photo upload API](https://www.flickr.com/services/api/upload.api.html)

## Group discovery

`flickr.groups.pools.getGroups` returns groups to which the authenticated user
can add photos. It is paginated with a maximum of 400 groups per page. The
response includes identity and display fields but no posting-limit value,
reset time, or moderation flag.

The FGA refresh worker uses the documented `www.flickr.com` REST origin and
requests the first page in raw JSON form with this canonical call:

```text
GET https://www.flickr.com/services/rest/?method=flickr.groups.pools.getGroups&page=1&per_page=400&format=json&nojsoncallback=1
```

Later pages replace only the `page` value before receiving their own OAuth
nonce, timestamp, and signature. Flickr's JSON response contract requires
`format=json`; `nojsoncallback=1` suppresses its JSONP wrapper.

`flickr.groups.getInfo` returns a point-in-time `ispoolmoderated` attribute plus
a `throttle` element with `count`, `mode`, and `remaining`. The FGA
group-submission worker requires a fresh `getInfo` call immediately before every
individual group-add attempt and records the observed moderation value and
time. This is an informed-action preflight, not a concurrency guarantee: the
group owner can change moderation after the GET and before the subsequent POST.
No documented Flickr operation reads the moderation flag and adds a photo
atomically. The worker begins local POST dispatch less than 1,000 milliseconds
after receiving the metadata response or discards the observation and reads
again. That bounds worker-controlled delay, not network or Flickr processing
time.

Official sources:

- [`flickr.groups.pools.getGroups`](https://www.flickr.com/services/api/flickr.groups.pools.getGroups.html)
- [`flickr.groups.getInfo`](https://www.flickr.com/services/api/flickr.groups.getInfo.html)
- [Flickr JSON response format](https://www.flickr.com/services/api/response.json.html)

## Existing public photo discovery and proof

Checked against Flickr's official method pages on 2026-08-26.

Authenticated `flickr.people.getPhotos` accepts an explicit `user_id`,
`privacy_filter`, `content_types`, `page`, and `per_page`. The FGA API backend
can therefore fix the configured owner NSID, `privacy_filter=1` for public
photos, and `content_types=0` for photos while exposing bounded advisory paging
to the FGA LrC plug-in. Page membership and totals may drift between requests;
the result is a browsing aid rather than a stable snapshot or proof that every
eligible photo was observed.

`flickr.photos.getInfo` accepts an exact opaque photo ID and returns the photo's
owner NSID and visibility fields. The FGA API backend uses a fresh complete
result to require the exact requested ID, configured owner, and public
visibility before it commits or refreshes a common photo binding. The
client-proposed ID remains only a lookup key. Flickr identifiers are opaque
strings under the API overview and must not be parsed or treated as numeric
authority.

Official sources:

- [`flickr.people.getPhotos`](https://www.flickr.com/services/api/flickr.people.getPhotos.html)
- [`flickr.photos.getInfo`](https://www.flickr.com/services/api/flickr.photos.getInfo.html)
- [Flickr identifier overview](https://www.flickr.com/services/api/misc.overview.html)

## Current photo pool membership

Checked against Flickr's official method pages on 2026-08-22.

`flickr.photos.getAllContexts` accepts a Flickr `photo_id` and returns all
currently visible sets and group pools for that photo. The FGA API backend needs
only the pool entries. The method exposes no upstream paging arguments, so the
backend applies response-byte, context-count, and elapsed-time budgets to the
single Flickr response, fails without publishing a partial result if a budget
is exceeded, then exposes the complete pool observation to the FGA LrC plug-in
through revision-checked keyset pages ordered by exact Flickr group ID.
ADR 0030 replaces random server-stored cursors and retained generations with
that ordinary private-MVP read.

For an already-published FGA photo, the selector performs this Flickr request
fresh each time it opens. The FGA database cannot answer the current-membership
question: the photographer, another client, or a group moderator can add or
remove the photo without involving FGA. The resulting membership and
`observedAt` time are therefore a UI observation, not a durable truth or a
write-safety predicate. Failure is displayed as unavailable, never as an empty
membership set. Continued absence also cannot distinguish a moderated photo
that remains pending from one that was rejected.

Flickr documents `flickr.groups.pools.remove` as a separate authenticated POST.
FGA deliberately never invokes or exposes it. Current pool entries are read-only
in FGA; deselection has no removal meaning. A photographer can remove a photo
through Flickr or another non-FGA client, and the next fresh
`getAllContexts` read will reflect the then-visible result without FGA trying to
reverse the external change.

Official sources:

- [`flickr.photos.getAllContexts`](https://www.flickr.com/services/api/flickr.photos.getAllContexts.htm)
- [`flickr.groups.pools.remove`](https://www.flickr.com/services/api/flickr.groups.pools.remove.html)

## Adding to a group

`flickr.groups.pools.add` requires an authenticated HTTP POST with `write`
permission, the user's `photo_id`, and the target `group_id`. Its numbered
outcomes are Flickr application result codes carried in a response whose body
must be parsed. They are not HTTP status codes. Flickr's REST response contract
uses `<rsp stat="ok">` for success and `<rsp stat="fail"><err code="..."
msg="..." /></rsp>` for a failure. The FGA group-submission worker must inspect
`stat` and the numeric code; transport success alone is not group-add success.

Documented method-specific results:

| Flickr status | Code | FGA classification |
| --- | --- | --- |
| Photo added | `stat="ok"` | Terminal `added`; permanently retain pair identity |
| Photo not found or not owned by caller | `1` | Terminal `needs_attention`; no automatic retry |
| Group not found or caller is not a member | `2` | Terminal `needs_attention`; no automatic retry |
| Photo already in pool | `3` | Idempotent terminal `added` |
| Photo is already in the maximum number of pools | `4` | Terminal `needs_attention`; no automatic retry |
| User has added the maximum allowed photos to the pool | `5` | Throttle only this user/group partition; retry after its conservative due time with a new `getInfo` preflight |
| Photo added to the pool's pending queue | `6` | Terminal `moderation_submitted`; create permanent do-not-resubmit record |
| Photo already in the pool's pending queue | `7` | Idempotent terminal `moderation_submitted`; create or confirm permanent do-not-resubmit record |
| Content not allowed by group moderation rules | `8` | Terminal `needs_attention`; no automatic retry |
| Group pool contains the maximum number of photos | `10` | Terminal external group block; no automatic retry |
| Group pool disabled | `11` | Terminal external group block; no automatic retry |
| SSL required | `95` | Configuration failure; send no further writes until corrected |
| Invalid signature | `96` | Signing/configuration failure; send no further writes until corrected |
| Missing signature | `97` | Signing/configuration failure; send no further writes until corrected |
| Login failed or invalid auth token | `98` | Disable writes for the linked user pending reauthorization |
| User not logged in or insufficient permission | `99` | Disable writes for the linked user pending reauthorization or permission repair |
| Invalid or expired API key | `100` | Disable application writes pending operator repair |
| Service currently unavailable | `105` | Explicit temporary failure; bounded backoff and retry with a new preflight |
| Write operation failed due to a temporary issue | `106` | Explicit temporary failure; bounded backoff and retry with a new preflight |
| Requested response format not found | `111` | FGA request/configuration defect; no automatic retry |
| Requested method not found | `112` | FGA request/configuration defect; no automatic retry |
| Invalid SOAP envelope | `114` | FGA protocol defect; no automatic retry |
| Invalid XML-RPC method call | `115` | FGA protocol defect; no automatic retry |
| Bad URL found | `116` | Terminal request-policy failure; no automatic retry |

The official method page defines no application results numbered `9` or `113`;
the FGA group-submission worker does not invent a meaning for either gap. Any
undocumented numeric result follows the unknown-code rule.

An unknown application code is not assumed side-effect-free. The FGA
group-submission worker records the numeric code and a sanitized message in the
FGA database, creates the permanent block, and stops the intent in terminal
`delivery_uncertain`. Future classification cannot make that already-attempted
pair safe to resubmit through the FGA API backend or FGA group-submission
worker.

### Moderation opacity and permanent suppression

“Photo added to the pool's pending queue” (code `6`) says only that Flickr
accepted the pair into that queue. “Photo already in the pool's pending queue”
(code `7`) says the pair is already there. Flickr's documented API index
exposes no submitter-facing method that reports whether that pending item
remains queued or was rejected. A later documented pool-membership observation
can prove that the photo was accepted when the target group appears among the
photo's visible pools. Continued absence proves nothing: still pending and
rejected remain indistinguishable.

FGA therefore permanently remembers every exact `(Flickr photo ID, Flickr group
ID)` pair for which it receives “photo added to the pool's pending queue” (code
`6`) or “photo already in the pool's pending queue” (code `7`), even if the
photo later appears in or disappears from the pool. FGA never submits that pair
again. It also permanently suppresses resubmission after an add POST may have
reached Flickr but no definitive response was durably recorded. Otherwise a
moderator could reject the first submission between an ambiguous timeout and a
retry, and the retry would silently create a second moderation event.

Failures proven to occur before dispatch—DNS, TCP connection, or TLS handshake
failures—are safe to retry. Once delivery is possible, a missing, truncated, or
unparseable response becomes terminal `delivery_uncertain`. This deliberately
trades some automatic liveness for moderator courtesy.

A preflight `ispoolmoderated="0"` followed by “photo added to the pool's pending
queue” (code `6`) is possible because the GET and POST are not atomic. FGA
records that contradiction as a moderation race or upstream inconsistency, but
that returned status remains authoritative and creates the same permanent
block.

Official sources:

- [`flickr.groups.pools.add`](https://www.flickr.com/services/api/flickr.groups.pools.add.html)
- [Flickr REST response format](https://www.flickr.com/services/api/response.rest.html)
- [Flickr API method index](https://www.flickr.com/services/api/)
- [`flickr.groups.pools.getPhotos`](https://www.flickr.com/services/api/flickr.groups.pools.getPhotos.html)

The permanent handling decision is [ADR 0007](../decisions/0007-fail-polite-group-submissions.md).

## Limits, security, and terms

Flickr's developer guide currently advises staying under 3,600 API queries per
hour in aggregate across the entire application key. It permits short-term API
result caching up to 24 hours and specifically cautions against centralizing all
users' authentication tokens because that creates an attractive target.

The API terms require a privacy disclosure and prominent attribution using this
exact notice:

> This product uses the Flickr API but is not endorsed or certified by SmugMug,
> Inc.

The terms distinguish commercial use and require an appropriate key/approval.
An MIT source license does not by itself determine whether a deployed service is
commercial under Flickr's rules.

Official sources:

- [Flickr Developer Guide: API](https://www.flickr.com/services/developer/api/)
- [Flickr API Terms of Use](https://www.flickr.com/help/terms/api)
- [Flickr API keys](https://www.flickr.com/services/api/misc.api_keys.html)
