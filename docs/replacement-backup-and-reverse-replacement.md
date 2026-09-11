# Flickr replacement backup and reverse-replacement safeguards

Last updated: 2026-09-05

Status: Accepted conditional safety contract under ADR 0024; replacement
remains prohibited until the complete #0052 through #0058 evidence passes and
a later scope decision accepts the feature

## What this protects

Changing the bytes behind an established Flickr photo is destructive even when
the photo ID stays the same. Flickr does not document retention of the prior
Original or a rollback operation. A future replacement workflow must therefore
retain both exact byte states before it asks Flickr to change anything.

This contract protects recoverable image bytes and records observable before-
state. It cannot make Flickr replacement transactional and cannot restore a
lost view, favorite, comment, tag edit, album membership, group membership,
date, URL, permission, or other remote state merely by sending old image bytes
again. “Reverse replacement” is used for the new write; “rollback” is reserved
for an atomic guarantee that Flickr does not provide.

## Two local operation bundles

The owner configures a primary FGA replacement vault and a recovery FGA
replacement vault. They are ordinary private filesystem directories, not
temporary paths, Git worktrees, cloud object stores, Lightroom Classic catalog
folders, or managed RAW source folders. The FGA LrC plug-in uses documented
`LrFileUtils.pathsAreOnSameVolume` and refuses replacement unless the two roots
are on different volumes.

The owner is responsible for access control, whole-volume at-rest protection,
hardware health, and any additional offline/site backup. The FGA LrC plug-in
does not invent an encryption format, hold another encryption key, or claim
that two directories alone are a complete disaster-recovery program.

For each server-generated opaque `replacementOperationId`, the FGA LrC plug-in
creates the same non-overwriting directory in both vaults. Each bundle contains:

```text
<replacementOperationId>/
  baseline-original.bin
  intended-replacement.bin
  manifest.json
```

The `.bin` suffix prevents the filename from asserting a format before
inspection. The manifest records the exact observed format. No filename or
directory contains a Flickr photo ID, title, capture date, catalog filename,
album, group, or other remote metadata.

Both byte files are required:

- `baseline-original.bin` is the exact Flickr Original downloaded immediately
  before the operation was prepared, not a Lightroom Classic re-render, RAW
  source, preview, display derivative, or assumed prior upload; and
- `intended-replacement.bin` is the exact completed file that the FGA LrC
  plug-in intends to hand to Flickr, not a later re-render from retained develop
  settings. Its manifest format is PNG for a forward FGA publication upgrade,
  while a reverse replacement may intentionally retain the prior format.

This simple duplication costs exactly twice the sum of both file sizes per
operation, plus small manifests. The cost is intentional and visible. No
content-addressed deduplication, compression wrapper, incremental store, or
custom backup service is introduced before actual scale proves it necessary.

## Canonical manifest

`manifest.json` is a versioned, UTF-8, canonical JSON document containing:

- replacement operation ID, FGA photo-binding ID, exact Flickr photo ID, and
  linked/binding revisions;
- creation time;
- for each byte file: fixed role, filename, byte count, SHA2-256, detected media
  type, format, width, height, bit depth, and color type;
- a pre-replacement metadata snapshot containing only the documented Flickr
  fields collected for the replacement experiment: owner and visibility,
  title/description/tags, upload/taken dates, permissions, URLs, view/favorite/
  comment observations, album contexts, and group contexts;
- a SHA2-256 over the canonical metadata snapshot;
- the FGA API backend's independently observed baseline fingerprint and
  observation time; and
- bundle schema version and completed state.

The local manifest may contain sensitive photography metadata. It never enters
Git, chat, routine logs, the Lightroom Classic catalog, or hosted telemetry.
The FGA database stores only the operation identities, file fingerprints,
metadata-snapshot SHA2-256, and verification times needed to compare the local
claim with hosted observation; it does not store the byte files, local paths,
or metadata snapshot.

## Prepare and verify before dispatch

The safe sequence is:

1. The FGA API backend freshly proves the exact bound Flickr photo, owner,
   visibility, and revision, collects the documented metadata snapshot, and
   independently downloads and fingerprints the current authoritative Original
   under the [ambiguity contract](replacement-ambiguity-reconciliation.md).
2. The FGA LrC plug-in downloads that exact Original from an allowlisted Flickr
   CDN URL into a temporary opaque file with fixed timeout, redirect, media, and
   byte budgets. A missing, partial, oversized, malformed, or changed response
   is **Backup unavailable**, not an empty or usable backup.
3. The FGA LrC plug-in finishes the intended file. It streams both files
   through documented `LrDigest.SHA256`, records exact structure and byte counts,
   and requires the baseline fingerprint to equal the independent hosted
   observation and differ from the intended fingerprint.
4. It writes both bundles through temporary sibling paths, refuses every
   pre-existing target, writes the canonical manifests last, then reopens and
   rehashes all four byte copies and both manifests. A copy is not verified by
   a successful filesystem return alone.
5. It durably records the verified manifest SHA2-256 values locally and submits
   only those digests and verification times to the FGA API backend. The backend
   can move the operation to `prepared` only when both manifests agree with its
   immutable intent and baseline fingerprints.
6. Only then may the one-shot dispatch transaction commit. Any download, write,
   capacity, media, hash, manifest, or second-volume failure leaves dispatch
   count `0` and Flickr unchanged.

The implementation must prove the documented Lightroom Classic host can hash
the maximum accepted image incrementally without loading the entire file into Lua
memory. Until that test passes, the backup gate is unimplemented rather than a
whole-file-memory fallback.

## Retention and recurring verification

Both complete bundles are retained indefinitely. Normal cleanup, cache
eviction, log retention, catalog optimization, uninstallation, credential
rotation, account disconnect, successful forward replacement, successful
reverse replacement, and elapsed time delete nothing.

Before any read that is presented as recoverable and before every reverse-
replacement proposal, the FGA LrC plug-in rehashes all byte files and manifests
in both vaults and compares them with the FGA database fingerprints. The annual
operations gate also verifies every tracked bundle, reports missing/corrupt/
unreachable copies by operation ID only, and performs a sampled read from each
volume. A healthy primary never conceals a failed recovery copy.

The product exposes no delete, prune, retention-duration, or “backup no longer
needed” control in this scope. The owner can always remove files using operating-
system tools, but a later verification then marks the bundle unavailable and
FGA replacement components refuse reverse replacement. Removing the database
history or permanent ambiguity block is not recovery.

## Controlled reverse replacement

Reverse replacement is available only after a future ADR has accepted the
feature and all of these preconditions hold:

- the forward operation reached `verified_new_original`, with no ambiguity or
  permanent photo-level replacement block;
- both complete operation bundles pass fresh byte and manifest verification;
- fresh hosted proof confirms the exact same bound photo, owner, visibility,
  linked revision, and current Original fingerprint;
- that current Original equals the forward operation's exact intended
  fingerprint; if another actor changed it, the FGA LrC plug-in refuses to
  overwrite that change; and
- the owner explicitly chooses **Restore backed-up Original bytes…** for that
  one photo after seeing both fingerprints, before/current observation times,
  and the warning that remote social and metadata state will not be rolled back.

The restore creates a new replacement operation. Its baseline is the freshly
observed current intended PNG; its intent is the freshly verified retained
`baseline-original.bin`. It receives a new operation ID, fresh proof, two new
verified bundles, its own durable dispatch marker, and at most one Flickr POST.
It follows every ambiguity rule in ADR 0023. It is never an automatic failure
handler for the forward operation.

After the exact old Original is verified on Flickr, the FGA replacement
reconciliation worker captures another metadata/context observation and
compares it with the pre-forward snapshot. Differences are reported as
**Remote state differs after reverse replacement**. No FGA component invents
missing values or automatically edits metadata, albums, groups, comments,
favorites, views, permissions, dates, or URLs to make the snapshot look
restored.

## Failure matrix

| Condition | Required behavior |
| --- | --- |
| Baseline Original cannot be downloaded and matched to hosted observation | Do not prepare or dispatch |
| Intended render equals baseline bytes | Do not replace; the requested byte change is already a no-op |
| Either vault is missing, same-volume, unwritable, full, or unverifiable | Do not prepare or dispatch |
| Forward response is lost or Original outcome is unknown/diverged | Follow ADR 0023; do not reverse or retry |
| One retained copy later fails but the other passes | Report degraded backup, refuse reverse replacement, repair by verified copy outside any Flickr write |
| Both retained copies fail | Report backup unavailable; never infer bytes from Lightroom settings or Flickr derivatives |
| Current Flickr Original differs from the verified forward intended bytes | Refuse reverse replacement to avoid overwriting an external change |
| Reverse-replacement response is lost | Treat the reverse as its own ambiguous write; never replay it |
| Old bytes return but social/metadata observations differ | Report partial remote-state preservation; do not call it rollback |

## Required implementation evidence

Before any replacement capability is accepted, tests must prove at least:

- the two roots are distinct volumes and every target is non-overwriting;
- interrupted writes cannot publish a complete manifest;
- all four byte copies and both manifests are re-read and hashed before
  `prepared` can commit;
- baseline-hosted mismatch, equal old/new bytes, low space, partial copy,
  corruption, stale manifest, and unavailable volume prevent dispatch;
- no routine lifecycle or retention job deletes a bundle;
- annual verification detects one- and two-copy failures without logging paths,
  metadata, Flickr IDs, or hashes;
- reverse replacement requires all listed proofs and a one-photo owner
  confirmation;
- current-Original drift and every forward ambiguity block reverse dispatch;
- a reverse operation uses a new marker and cannot replay after ambiguity; and
- post-reverse metadata differences remain visible and cause no compensating
  Flickr or Lightroom Classic catalog write.

The architecture repository has no production replacement vault, FGA LrC
plug-in implementation, hosted replacement resources, or conformance suite and
therefore claims no executable pass.
