# Flickr album-write reconciliation contract

Last updated: 2026-09-05

Status: Accepted album creation and attachment reconciliation contract under
ADR 0026; executable implementation evidence remains outstanding

## Two different write semantics

`flickr.photosets.create` creates a new resource and has no documented
idempotency key. Replaying an ambiguous call can create a duplicate album.

`flickr.photosets.addPhoto` establishes one set-like `(photoset ID, photo ID)`
membership. Flickr documents code `3` for a photo already in the set, and one
membership cannot be duplicated. After a complete authoritative read, present
membership proves the desired postcondition and absent membership permits a
bounded add retry. Album ordering is not an FGA requirement.

The FGA album worker therefore uses separate attempt tables, result classes,
and recovery rules. Neither path treats a title, URL, local collection state,
elapsed time, or an unavailable read as remote evidence.

## Common durable dispatch boundary

Every Flickr write attempt records the exact album binding, photo binding when
applicable, linked-Flickr revision, OAuth-grant revision, attempt number,
sanitized correlation ID, dispatch count, dispatch and completion times,
documented result class, and append-only events.

Before the FGA album worker gives a POST to the HTTP stack, one FGA database
transaction commits `dispatch_started_at` and increments dispatch count. That
marker never clears. Code structure and conformance tests must make an unmarked
POST impossible.

Safe automatic retry requires one of these durable conditions:

- no dispatch marker exists;
- a marked attempt has implementation-proven evidence that zero request bytes
  could have left; or
- the operation is album membership, a complete fresh read proves the exact
  relation absent, and the retry cannot create a duplicate relation.

A timeout, exception type, expired lease, process restart, old observation,
operator belief, or missing database result is not zero-byte proof. Every
attempt is fenced by the current linked/account revisions and one database
claim; a queue message or process lock is not authority.

## Album creation intent and pre-dispatch observation

One album binding has at most one active materialization attempt. Before create
dispatch, the FGA album worker freshly calls documented
`flickr.photos.getAllContexts` for the exact first Flickr photo and strictly
validates the complete successful result. It stores the exact pre-dispatch
photoset-context ID set and observation time on the attempt. A failed or
malformed read prevents dispatch.

In the dispatch transaction, the FGA album worker rechecks the unmaterialized
binding, immutable first-photo binding, current link/grant revisions, absent
photoset ID, and active attempt. It commits the marker, then calls
`flickr.photosets.create` once with the exact desired-title revision and hosted-
derived primary photo ID.

A complete successful result must contain one syntactically valid opaque
photoset ID and bounded URL. The FGA album worker then performs exact
`flickr.photosets.getInfo` and first-photo `getAllContexts` reads, requiring the
configured owner and that same photoset membership. It commits the photoset ID
once and transitions the first-photo obligation to `membership_verified`.

A known documented Flickr rejection can end the attempt as
`create_rejected` only when its classified contract proves no album was created.
An unknown application code, malformed success, transport loss after dispatch,
process failure, missing response, or failure to durably commit a received
result becomes `create_outcome_unknown` unless exact read evidence later
resolves it. Neither the FGA API backend nor FGA album worker sends another
create for that album binding in this state.

## Ambiguous-create candidates

Recovery repeats the strict complete `getAllContexts` read for the exact first
photo. IDs present after dispatch but absent in the stored pre-dispatch set are
candidates, not matches. For each candidate, the FGA API backend performs a
complete `flickr.photosets.getInfo` read and returns only the minimum private
display data: opaque photoset ID, title, owner, primary photo ID, created/updated
times when documented, bounded navigation URL, and representative thumbnail
when available.

The candidate response is authenticated, installation/binding-scoped,
paginated or explicitly bounded, and `Cache-Control: private, no-store`. A title
match, one candidate, exact primary photo, creation time, or absence from the
pre-dispatch set never permits automatic binding. Another Flickr client could
have created or edited an album in the same interval. An empty or failed result
does not prove the create failed.

The FGA LrC plug-in displays **Album creation outcome unknown — choose the
created Flickr album**. Each row shows the exact album ID, title, primary-photo
thumbnail, and created time. The owner may:

- choose **Use this Flickr album** for one candidate;
- enter one exact Flickr photoset ID when the intended album is absent from the
  candidate list; or
- choose **Leave unresolved**, which performs no Flickr write.

The FGA API backend freshly verifies an owner-selected photoset, exact configured
owner, and exact first-photo membership. In one transaction, it binds that ID
only if the album binding remains unmaterialized and the photoset ID is not
already bound to another FGA album. A repeat of the same selection is idempotent;
a different later selection conflicts. Proven membership satisfies the first-
photo obligation.

This action records provenance `owner_reconciled_ambiguous_album_create`. It
proves owner-selected identity and current first-photo membership, not that the
ambiguous POST created the album. The FGA LrC plug-in then repairs its remote
collection ID/URL from the hosted binding under the main album contract.

The FGA LrC plug-in offers no **Create another album** action for an ambiguous
binding. If an unintended duplicate exists, Terry handles it deliberately in
Flickr after identifying both resources. The FGA LrC plug-in, FGA API backend,
and FGA album worker do not automatically rename, merge, empty, or delete a
candidate or duplicate.

While create remains unresolved, already uploaded photos retain durable waiting
membership obligations. A later publish invocation for that local album stops
before rendering or uploading new photos and shows the repair state, preventing
an unbounded collection of published-but-unassigned photos.

## Album-membership obligation

The FGA database owns one natural-key obligation per
`(fgaAlbumBindingId, fgaPhotoBindingId)`. It retains desired membership,
enqueue/attempt state, exact IDs derived from both bindings, and immutable
history. Client-supplied Flickr IDs or a Lightroom remote ID never override the
hosted records.

For the create operation's exact primary pair, fresh post-create membership
verification satisfies the obligation without `addPhoto`. Every later pair
uses this sequence:

1. The FGA album worker claims the obligation with a fenced database lease and
   confirms the album/photo bindings, owner, link/grant revisions, and absence
   of an album identity conflict.
2. It freshly calls `flickr.photos.getAllContexts` for the exact photo and
   strictly validates the complete photoset contexts.
3. If the target photoset ID is present, it commits `membership_verified`
   without a Flickr write, regardless of which actor added it.
4. If the target is absent, it creates an attempt, commits the dispatch marker,
   and calls `flickr.photosets.addPhoto` once.
5. A complete success or documented already-in-set code `3` proceeds to another
   strict fresh membership read. Only observed presence commits
   `membership_verified`; the write response alone is not the final assertion.
6. A lost, malformed, unknown, or uncommitted result enters
   `membership_reconciliation_pending` and performs only the same strict read.

During reconciliation:

| Fresh complete result | Behavior |
| --- | --- |
| Target photoset present | Commit `membership_verified`; send no further add |
| Target photoset absent | Schedule a bounded new add attempt; duplicate membership is impossible and code `3` is a valid concurrent-success result |
| Read unavailable or incomplete | Retain pending state with bounded backoff; send no add |
| Wrong owner, missing/deleted photoset, missing photo, or binding conflict | Move to `album_attachment_needs_attention`; send no add |

An external removal while the local photo remains published in the album is
drift from the desired membership. A later strict absence can restore it through
the same add path. The [album lifecycle
contract](album-lifecycle-contract.md) defines what happens after the owner
removes the local collection/photo relationship or deletes the local album;
this contract never infers `removePhoto` from absence or deselection.

## Owner-visible state

The FGA LrC plug-in distinguishes:

- **Published — album attachment pending**;
- **Published — album membership verified**;
- **Album creation outcome unknown — action required**;
- **Album attachment delayed — retrying after verification**;
- **Album attachment needs attention**; and
- **Album identity conflict — no album writes sent**.

The ordinary dominant path needs no dialog. Only ambiguous create identity
requires explicit selection. Status includes no OAuth material or private raw
response, and routine logs use the FGA album-binding/obligation IDs rather than
Flickr IDs, titles, URLs, or local catalog paths.

## Required conformance evidence

The production suite must prove at least:

- no create/add POST can occur without its committed dispatch marker;
- create dispatch count cannot exceed one after any timeout, exception, crash,
  takeover, retry-now, or administrative action;
- pre/post first-photo context snapshots produce candidates but never automatic
  identity, even with one exact-title/primary candidate;
- empty, malformed, mixed, duplicate, over-budget, and failed context or
  photoset results cannot bind or dispatch;
- owner selection requires fresh exact owner/membership proof and is idempotent
  only for the same photoset ID;
- an already-bound candidate and a changed selection conflict;
- unresolved create blocks later new-photo upload for that album but preserves
  existing obligations;
- primary membership sends zero `addPhoto` calls;
- present membership sends zero adds, absent membership permits one fenced
  attempt, and code `3` is followed by read verification;
- every ambiguous add branches only on complete fresh membership evidence;
- repeated add attempts cannot create a duplicate relation and use bounded
  backoff/rate limits; and
- no path calls `flickr.photosets.removePhoto`, deletes a photoset, or rewrites a
  committed album identity.

The architecture repository has no production FGA album worker, FGA database
schema, candidate resource, repair UI, or conformance suite and therefore claims
no executable pass.
