# Flickr replacement ambiguity and reconciliation contract

Last updated: 2026-09-05

Status: Accepted conditional safety contract under ADR 0023; Flickr replacement
remains prohibited until the complete #0052 through #0058 evidence passes and
a later scope decision accepts the feature

## Scope and safety posture

This contract defines how a future one-photo replacement operation would retain
truth after a lost response, process failure, or delayed Flickr result. It does
not accept replacement into FGA product scope, prove preservation of social or
album state, define backup/rollback, authorize a historical photo, or permit a
batch operation.

Flickr replacement is a non-idempotent write with no documented idempotency key
or processing deadline. The FGA LrC plug-in therefore gets at most one Flickr
POST dispatch for one durable replacement operation. After the dispatch marker
commits, neither an old Original, elapsed time, a missing Flickr response, a
manual retry command, nor process recovery authorizes another POST.

This deliberate loss of automatic liveness is the conventional safe boundary:
the established public photo is more valuable than an automatic retry. If
Flickr cannot prove the intended new Original, the operation remains visible
and unresolved or requires manual repair outside FGA.

## Durable identities and fingerprints

The FGA database owns a server-generated `replacementOperationId` and one
natural key over the FGA user, photo binding, expected binding revision,
Lightroom Classic catalog photo UUID, and intended fingerprint. A retry of the
creation request with the same exact tuple returns the original operation; any
changed binding, revision, or fingerprint is a distinct request and conflicts
while an operation is active. At most one nonterminal replacement operation may
exist for one FGA photo binding. This deterministic key is non-secret
idempotency data and uses no plug-in-generated random value.

Before creating an operation, the FGA LrC plug-in finishes one replacement file
and streams its bytes through the documented `LrDigest.SHA256` digester. A
forward FGA publication upgrade uses the accepted PNG output; a separately
authorized reverse replacement can use the exact retained prior format.
The API spelling required by Adobe remains `SHA256`; FGA project records and
prose call the result SHA2-256. The plug-in retains this immutable intent
fingerprint:

- exact lowercase SHA2-256 hex digest;
- exact byte count;
- exact validated media type and format;
- image width, height, bit depth, and color type when the format exposes them;
  and
- the Lightroom Classic catalog photo UUID and render completion time as local
  diagnostic correlation, never as remote identity or authorization.

The digest is the intended byte identity, not evidence that those bytes reached
Flickr. A local file change between hashing and transmission can only make
post-dispatch verification fail; it cannot silently redefine the intent.

The FGA API backend creates an operation only after fresh exact-photo proof for
the current binding and link revision. Through documented Flickr information
and size APIs, it retrieves the current Original from an allowlisted Flickr CDN
origin, enforces redirect and byte budgets, and stores the same fingerprint
fields as `baselineOriginal`. The intended and baseline SHA2-256 values must
differ. Flickr can still change after that observation; the timestamp is
evidence, not a lock.

The FGA database stores fingerprints and observations, not Original or
replacement bytes. The [backup and reverse-replacement
contract](replacement-backup-and-reverse-replacement.md) owns separately
retained byte copies.

## Record and state model

One `replacement_operations` row retains at least:

- operation ID, FGA user ID, photo-binding ID, exact Flickr photo ID derived
  from that binding, client operation key, and linked/binding revisions;
- immutable intended and baseline fingerprints plus their observation times;
- `prepared_at`, `dispatch_started_at`, response and observation timestamps;
- dispatch count constrained to `0` or `1` and a sanitized correlation ID;
- exact response photo ID and documented Flickr result class when received;
- current state, terminal reason, and one monotonic state revision; and
- append-only state, dispatch, response, observation, and operator events.

The state machine is intentionally small:

| State | Meaning | Flickr replacement POST eligibility |
| --- | --- | --- |
| `prepared` | Intent and both fingerprints committed; no dispatch marker | Exactly one dispatch transition may begin |
| `abandoned_before_dispatch` | Owner canceled while still `prepared` | None; a new operation may later be created |
| `dispatch_started` | Marker and count `1` committed before a signed envelope left the FGA API backend | Never again |
| `response_received` | Complete response recorded; Original still needs authoritative verification | Never again |
| `verification_pending` | A read was unavailable, incomplete, or not yet conclusive | Never again; read-only observations only |
| `verified_new_original` | Exact Flickr photo and Original match the intended fingerprint | None; successful byte outcome only |
| `replacement_outcome_unknown` | Dispatch may have occurred but no definitive intended Original was established | Never again; permanent FGA automated-replacement block |
| `diverged_original` | Exact photo currently has neither baseline nor intended fingerprint, or identity/result fields conflict | Never again; permanent block and manual investigation |

`dispatch_started_at` and dispatch count never clear. A later state does not
rewrite the fact that a POST may have left. A database constraint and the only
dispatch transaction make count greater than one impossible.

## One-shot dispatch transaction

The FGA LrC plug-in first durably saves the operation ID, local render path,
intended fingerprint, and `prepared` state. It then requests the one dispatch
envelope for that exact operation.

In one FGA database transaction, the FGA API backend locks the operation and
photo binding, requires state `prepared`, confirms unchanged linked/binding
revisions and absence of a photo-level replacement block, sets
`dispatch_started_at`, increments dispatch count to `1`, and appends an event.
Only after commit may it use its mature OAuth library to create a short-lived
Flickr replacement envelope bound to the exact derived photo ID and
`async=0`. The binary `photo` part remains outside Flickr's OAuth signature.

The first successful request can return that envelope once. A repeat, timeout
recovery, or resumed process receives only `replacement_dispatch_already_started`
and current state—never another or repeated envelope. Failure after the marker
but before the client receives the envelope is conservatively ambiguous even
when no Flickr bytes actually left. This false-positive cost is accepted because
there is no atomic transaction across the FGA database, Lightroom Classic host,
and Flickr.

“Once” describes FGA API issuance and official FGA LrC plug-in behavior, not a
cryptographic Flickr guarantee. Flickr's OAuth header is bearer material and the
binary file is not signed; Flickr may accept reuse during its timestamp window.
The FGA API backend cannot revoke that remote material after release. The FGA
LrC plug-in keeps it only in memory, invokes the exact request once, then drops
it. No FGA component claims it can prevent a modified client from replaying a
captured envelope against the owner's own photo.

After receiving the envelope, the FGA LrC plug-in durably records local
`dispatch_started`, invokes `LrHttp.postMultipart` once, and never reuses the
envelope. A complete response is durably submitted to the FGA API backend using
an idempotent exact-result update. A missing response, timeout, cancellation,
Lightroom Classic crash, or hosted acknowledgement failure changes only which
read-only reconciliation starts; it never reopens dispatch.

No FGA component accepts client testimony that zero POST bytes left after the
server marker. The safe automatic retry boundary is exclusively before the
marker transaction commits.

## Authoritative post-dispatch observation

The FGA replacement reconciliation worker performs only documented read calls
and Original downloads for the exact Flickr photo ID derived from the binding.
Each observation records exact returned photo ID, owner NSID, visibility,
Original format and dimensions, byte count, SHA2-256, Flickr/API completion
signals when documented, and database observation time. Raw responses, signed
URLs, and image bytes are not retained merely for reconciliation.

An observation is published only after the complete result and entire Original
pass identity, ownership, URL-origin, redirect, media, byte, and hash
validation. Failed or partial reads are **Unavailable**, never evidence for old
or new pixels.

| Authoritative observation after dispatch | Durable conclusion |
| --- | --- |
| Exact same photo ID and intended fingerprint | `verified_new_original`; replacement bytes are proven for that observation |
| Exact same photo ID and baseline fingerprint | Keep `verification_pending` within a bounded observation schedule, then `replacement_outcome_unknown`; an asynchronous write might still converge later |
| Exact same photo ID with any third fingerprint | `diverged_original`; another write, unexpected transform, or local-file race occurred |
| Different/missing photo ID, wrong owner, or inconsistent complete result | `diverged_original`; never bind or target the other resource |
| Unavailable or incomplete read | Keep `verification_pending` until the observation budget ends, then `replacement_outcome_unknown` |

The observation schedule may use bounded backoff and a fixed operational budget,
but no chosen duration proves that Flickr will never apply a late write. A fresh
manual **Recheck Original** action is safe because it performs the same reads and
hash only. It cannot dispatch, relabel an unmatched Original as success, or
clear a permanent block.

`verified_new_original` proves only current byte identity on the same Flickr
photo. It does not prove that Flickr preserved views, favorites, comments,
metadata, albums, groups, dates, URLs, or future availability. Ticket #0055
owns those separate observations.

## Recovery and operator choices

- **Before the marker:** the owner may cancel, producing
  `abandoned_before_dispatch`, or resume the exact prepared operation.
- **After the marker and before exact verification:** every process resumes
  read-only reconciliation. No background, retry-now, administrative, or
  recovery path can obtain a second envelope.
- **Exact intended Original observed:** record byte success, then allow only
  separately accepted social-state and Lightroom Classic reconciliation.
- **Unknown or divergent outcome:** keep the photo-level automated-replacement
  block permanently. The owner may inspect or repair the photo with Flickr's
  own UI. No FGA component automates a retry, rollback, deletion, or new upload.

A later manual Flickr repair does not erase the ambiguous operation or prove
that a delayed first replacement can no longer arrive. Any future design that
would clear the block needs a new evidence-backed ADR; ordinary administration
cannot do so.

## Required implementation evidence

Before a replacement implementation can be accepted, executable tests must
prove at least:

- creation idempotency and conflict behavior for every fingerprint field;
- exact binding/owner/revision checks and baseline Original verification;
- no signed envelope can leave before the durable marker commits;
- the first envelope is never returned by a repeat or recovery path;
- every exception boundary before and after `LrHttp.postMultipart` has the
  specified dispatch eligibility;
- response persistence and all Original observations are idempotent and
  append-only;
- intended, baseline, third, unavailable, wrong-photo, and wrong-owner
  observations enter only their specified states;
- no elapsed time or baseline observation enables another replacement POST;
- one operation and a photo-level block survive process, deployment, and
  credential revisions; and
- no reconciliation path uploads, replaces, deletes, changes visibility, or
  mutates Lightroom Classic catalog publication state.

The architecture repository has no production replacement endpoint, FGA
replacement reconciliation worker, or database implementation and therefore
claims no executable pass.
