# ADR 0021: Require fresh server proof for existing public photos

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31

## Context

ADR 0008 accepts public photos in the configured Flickr account as first-class
group-queue inputs, regardless of uploader or Lightroom Classic catalog
binding. A client can discover or type a Flickr photo ID, but that value alone
does not prove who owns the photo, whether it is public, whether the linked
account changed, or whether the value came from a current supported workflow.

The Flickr API documents an authenticated owner photostream listing with a
public privacy filter and an exact `flickr.photos.getInfo` result containing the
owner NSID and public-visibility value. These reads provide a conventional
server authority boundary without inspecting the Lightroom Classic catalog,
scraping Flickr pages, or storing copies of public photo metadata.

The original-publisher path already needs a hosted photo-binding resource after
upload. Giving existing photos a different group API would duplicate
authorization, idempotency, and courtesy semantics. A common server binding is
the smaller contract.

## Decision

1. An eligible existing photo is an exact Flickr photo ID observed as public
   and owned by the immutable configured Flickr owner NSID. Uploader, Flickr
   album membership, and Lightroom Classic catalog/publish-service bindings are
   irrelevant to eligibility.
2. The FGA API backend provides an owner-fixed public-photo listing backed by
   authenticated `flickr.people.getPhotos` with `privacy_filter=1` and photo
   content type. Listing pages are advisory browsing aids, not snapshots or
   authority. A malformed page is unavailable, never partial or empty.
3. The FGA LrC plug-in exposes an explicit no-upload existing-photo command in
   Lightroom Classic. The baseline selects one recognizable public photo, then
   reuses the normal fresh-membership and group-addition interaction. Ticket
   #0053 may improve presentation after a documented SDK spike but cannot move
   routine selection to a browser or weaken server proof.
4. Immediately before a group handoff, the FGA LrC plug-in sends the selected
   opaque photo ID and expected linked-Flickr revision to the FGA API backend.
   The photo ID is only a lookup key. The FGA API backend calls
   `flickr.photos.getInfo` with the exact current grant and requires the exact
   photo ID, configured owner NSID, and `visibility.ispublic="1"` before it
   commits proof.
5. A successful proof creates or refreshes one stable server-generated photo
   binding unique to `(FGA user, Flickr photo ID)`. It records minimal identity,
   provenance, link/verification revisions, owner/public observation, time, and
   sanitized events. It does not retain photo metadata or thumbnail bytes.
6. If an upload-origin binding already exists for that exact user/photo, the
   existing-photo proof reuses it and appends provenance rather than creating a
   second identity.
7. The common group-submission batch accepts only a server photo-binding ID,
   expected verification revision, and group IDs. The FGA API backend derives
   photo ID, user, owner, source, and link revision from the binding; the batch
   contains no client Flickr photo ID.
8. A new existing-photo intent requires the latest proof revision within the
   fixed positive `existing_photo_proof_max_age`, selected as 15 seconds by ADR
   0033. An expired proof prompts a safe re-read. A fully idempotent retry whose
   pairs all already exist returns those states without reviving or duplicating
   work.
9. Discovery and proof observations can become stale immediately. They do not
   make Flickr state atomic with intent creation or later worker dispatch and
   do not authorize photo replacement, deletion, album movement, catalog
   mutation, or migration.

## Consequences

- An arbitrary client can propose an opaque photo ID but cannot turn it into
  authority. Wrong-owner, private, missing, malformed, and stale-link results
  create no verified revision or new intent.
- The FGA LrC plug-in can browse public photos without requiring a catalog
  correlation. Optional catalog evidence remains a non-authoritative UI hint.
- The original and existing-photo paths converge before group-intent admission,
  so fail-polite, courteous batch, FIFO, and permanent-block semantics remain
  identical.
- The common binding changes the draft group-batch wire schema before OpenAPI
  implementation. No deployed compatibility migration exists or is required.
- Thumbnail presentation needs a bounded transient local cache because the
  documented Lightroom view control accepts a file/resource rather than a
  remote URL. Ticket #0053 must prove the usable interaction.

## Rejected alternatives

- **Trust a photo ID returned by the FGA LrC plug-in:** rejected because the
  client is not ownership or visibility authority.
- **Require a Lightroom Classic remote ID:** rejected because eligible photos
  need not exist in the current catalog and catalog data cannot prove current
  Flickr state.
- **Use discovery membership as proof:** rejected because paged listing is
  advisory and can change before selection.
- **Persist a full photostream snapshot:** rejected as unnecessary state,
  cleanup, and privacy surface for a private single-user selector.
- **Use a separate existing-photo group endpoint:** rejected because it would
  duplicate the accepted group admission and worker safety paths.
- **Associate or migrate the photo into an FGA published collection:** rejected
  from this decision because Lightroom record, album, replacement, and public
  photo identity are separate boundaries under ADR 0022 and the
  replacement-evidence work beginning at ticket #0052.

## Detailed contract

The [existing public Flickr photo intake contract](../existing-public-photo-intake.md)
defines exact discovery validation, Lightroom Classic presentation, proof
request/response, errors, binding persistence, schema-version-2 handoff, and
production conformance cases.
