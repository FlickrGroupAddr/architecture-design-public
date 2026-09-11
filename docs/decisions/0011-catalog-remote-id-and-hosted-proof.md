# ADR 0011: Treat a catalog remote ID as an upload result until hosted proof

Date: 2026-08-25

Amended: 2026-08-26 to converge upload-origin and existing-public-photo proof on
one server-generated photo-binding identity and schema-version-2 group handoff.

Status: Accepted by Terry on 2026-08-26

## Context

After Flickr accepts an upload, the FGA LrC plug-in receives a Flickr photo ID,
writes it to its durable local recovery record, and calls the documented
Lightroom SDK to record it as the published photo's remote ID. The FGA API
backend has not yet queried Flickr or committed an ownership observation at
that point.

The catalog value is important recovery evidence: delaying or removing it could
lose the only convenient correlation to a photo that already exists on Flickr
and could invite a duplicate upload. It is not, however, proof that the FGA API
backend can query the photo, that the linked Flickr account owns it, that album
attachment finished, or that any group intent was durably accepted.

ADR 0010 permits publication with zero group additions. The FGA LrC plug-in
therefore cannot obtain hosted photo binding as a hidden side effect of an empty
group-submission batch. Photos with groups and photos without groups need the
same explicit proof boundary.

## Decision

### Catalog meaning and visible state

A Flickr photo ID stored as a Lightroom Classic remote publish ID means only:

> Flickr returned this identifier as the successful upload result, and the FGA
> LrC plug-in durably recorded that result.

The value **MUST NOT** by itself mean that FGA policy considers hosted ownership
proved or publication fully complete. After recording it, the FGA LrC plug-in
**MUST** retain a durable local outbox entry in `uploaded_proof_pending` state.
Through a documented plug-in-owned status surface, it **MUST** distinguish at
least:

- **Uploaded — verification pending** (`uploaded_proof_pending`);
- **Uploaded — verified** (`hosted_photo_verified`); and
- **Uploaded — verification needs attention**
  (`uploaded_proof_needs_attention`).

The native Lightroom Classic published state may reflect that the upload
returned a remote ID. It does not replace the FGA LrC plug-in's truthful status
for hosted proof, required album attachment, or applicable group handoff.

### Explicit idempotent resource

The FGA LrC plug-in **MUST** create or retrieve this resource after every
successful upload, regardless of the number of selected groups:

```http
PUT /api/v001/upload-authorizations/{fgaUploadAuthorizationId}/photo-binding
Authorization: Bearer <FGA installation credential>
Content-Type: application/json
```

```json
{
  "schemaVersion": 1,
  "flickrPhotoId": "example-flickr-photo-id"
}
```

The path ID is the non-secret identifier returned by the FGA API backend when
it issued the upload authorization. The request contains no image bytes,
Flickr secret, OAuth field, user identity, album operation, or group ID.

For a previously unbound authorization, the FGA API backend **MUST**:

1. authenticate the installation and require that the authorization was issued
   to it;
2. validate the complete request without writing the proposed Flickr photo ID;
3. call the documented Flickr `flickr.photos.getInfo` method for that exact
   photo ID;
4. require a complete successful response containing the same photo ID and the
   linked Flickr account's owner NSID; and
5. in one FGA database transaction, conditionally bind the still-null upload
   authorization to the photo ID and commit the observed owner NSID,
   observation time, and successful verification result.

The commit creates or reuses one server-generated `fgaPhotoBindingId` unique to
the exact `(FGA user, Flickr photo ID)`. The binding records first provenance as
`fga_upload` unless an existing-public-photo proof already created it; later
proofs append their provenance events without creating a second photo identity.

The FGA database **MUST NOT** persist the returned Flickr photo metadata merely
to prove this boundary. A matching committed binding is idempotent. A different
photo ID for an already-bound authorization returns `409 Conflict` and never
changes the binding. Concurrent matching requests converge on one binding;
concurrent different requests permit only one winner.

The first committed response is `201 Created` with the binding URI in
`Location`; a repeat for the same binding is `200 OK`. Both return the same
resource shape:

```json
{
  "schemaVersion": 1,
  "fgaPhotoBindingId": "server-generated-binding-id",
  "sourceKind": "fga_direct_upload",
  "flickrPhotoId": "example-flickr-photo-id",
  "linkedFlickrRevision": 7,
  "verificationRevision": 1,
  "verifiedAt": "2026-08-25T12:34:56.123456Z"
}
```

An absent or non-visible upload authorization returns `404 Not Found`. An owner
mismatch returns `403 Forbidden`. An invalid Flickr photo ID returns
`422 Unprocessable Content`. A failed, incomplete, unparseable, missing, or
mismatched Flickr observation commits no binding and returns retryable
`503 Service Unavailable` with `Retry-After`; it never treats unknown as proof.

### Recovery and retry

Repeating the same `PUT` is safe after a timeout, lost response, process crash,
or retryable Flickr read failure. The FGA LrC plug-in **MUST** retry the same
authorization/photo tuple with bounded backoff. It **MUST NOT** upload the image
again merely because hosted proof is pending or failed.

A binding conflict, owner mismatch, invalid request, or exhausted automatic
retry budget moves the local record to `uploaded_proof_needs_attention`. The
catalog remote ID remains intact because it still identifies a possibly real
Flickr photo. A deliberate later verification retry is safe; changing the
photo ID or replaying the upload is not an automatic repair.

The FGA LrC plug-in **MUST** retain the authorization ID and Flickr photo ID
until every applicable local obligation is durably acknowledged. Losing the
authorization ID while retaining only the catalog remote ID is a repair state,
not permission to invent a binding or upload again.

### Independence from group work

The explicit photo binding is a precondition for group-submission intent
creation. `POST /api/v001/group-submission-batches` **MUST**
require the matching `fgaPhotoBindingId` and expected verification revision and
**MUST NOT** accept a client Flickr photo ID or perform a hidden ownership-proof
write. Its schema-version-2 request uses the same binding object for upload-
origin and existing-public-photo paths and continues to require at least one
unique Flickr group ID.

For a zero-group publication, successful photo binding creates no group intent
or FGA group-submission worker work. For a nonempty selection, the FGA LrC
plug-in proceeds to the separate idempotent group-submission batch only after
photo proof succeeds. The two hosted transactions need not be atomic; the local
outbox makes their order and recovery explicit.

Album attachment remains an independent required obligation. Hosted photo
proof does not claim that the photo is in its Flickr album, and album attachment
does not imply hosted ownership proof.

## Consequences

- The same hosted proof contract serves zero-group and nonempty-group
  publication.
- One server binding identity lets upload-origin and existing-public-photo
  intake converge before group admission without conflating their provenance.
- A Lightroom Classic remote ID remains useful recovery evidence without being
  overclaimed as total FGA completion.
- Proof retries are safe because they repeat a read plus an idempotent
  conditional binding, never an image upload.
- Nonempty group publication uses two explicit hosted transactions instead of
  combining proof with intent creation. The extra request buys one clear
  invariant and removes a hidden side effect from the group API.
- The FGA LrC plug-in needs a durable, visible secondary status because native
  Lightroom Classic publication state alone cannot express the distributed
  completion boundary.

## Alternatives considered

- **Delay the catalog remote ID until hosted proof:** rejected because a crash
  could hide the known identity of a photo already created on Flickr and make a
  duplicate upload more likely.
- **Treat Flickr's upload response as sufficient hosted proof:** rejected
  because it does not independently prove that the FGA API backend can query
  the exact photo under the expected linked owner.
- **Send an empty group-submission batch:** rejected by ADR 0010 because group
  work must not acquire an unrelated hidden side effect.
- **Keep proof atomic with nonempty group-intent creation:** rejected because it
  creates two proof contracts and leaves zero-group publication exceptional.
  One explicit binding resource is easier to understand, retry, test, and
  operate.
