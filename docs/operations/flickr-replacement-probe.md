# Disposable Flickr replacement probe

Last updated: 2026-08-26

Status: first authorized live run passed on 2026-08-26; the synthetic photo is
private and the temporary album was deleted

## Purpose and authorization boundary

This probe collects bounded evidence about Flickr's current binary replacement
endpoint without touching a personal, historical, private, or engagement-bearing
photo. It is the executable part of FGA localswim ticket #0054.

Live execution is an external mutation and requires Terry's specific approval
after reviewing these effects:

- create one synthetic photo as public and hidden from public search;
- add one synthetic owner comment;
- create one temporary Flickr album with that photo as primary;
- dispatch exactly one synchronous replacement with a different synthetic PNG;
- read photo, favorite, comment, album-context, group-context, and Original-size
  evidence;
- make the photo private and delete the temporary album; and
- retain the now-private synthetic photo because the existing token has `write`,
  not the broader Flickr `delete`, permission.

The public-to-private cleanup is attempted even after a probe failure, but a
network or Flickr failure can leave the synthetic photo public or leave the
temporary album present. The ignored local report retains their IDs for
deliberate repair. The command acknowledgement prevents accidental launch; it
does not substitute for specific human authorization.

## Implementation

[`scripts/flickr_replacement_probe.py`](../../scripts/flickr_replacement_probe.py)
uses the already-pinned `flickrapi` 2.4.0 integration library and the existing
ignored Flickr application/token files. It generates two deterministic 192×128
8-bit RGB PNG test patterns locally; no Lightroom Classic catalog or photograph
is read.

Before replacement, the probe stores a report with the synthetic file hashes,
remote photo ID, temporary photoset ID, and `dispatchCount: 0`. Immediately
before invoking `flickrapi.replace`, it writes `dispatchCount: 1` and a dispatch
time. Any exception after that point is ambiguous and the process never invokes
replacement again.

The report is written beneath ignored `artifacts/` and contains the exact IDs
needed for cleanup. Public architecture documents retain only sanitized counts,
booleans, and conclusions. The probe prints only pass/failure and the local
report path; it does not print credentials, tokens, photo IDs, album IDs, or
signed headers.

## Offline validation

From the repository root:

```console
$env:UV_CACHE_DIR = "$env:TEMP\localswim-uv-cache"
uv run --frozen python scripts/check_python.py
```

The unit tests verify that the two fixtures are distinct, valid 8-bit RGB PNGs
and that the preservation comparator rejects changed identity/context fields.
They make no network call.

## Live command after specific approval

Terry specifically approved the listed effects in chat on 2026-08-26. The
operator ran the following command exactly once. It is retained here for audit
and reproducibility, not as permission to run another probe:

Run exactly once from the repository root:

```console
$env:UV_CACHE_DIR = "$env:TEMP\localswim-uv-cache"
uv run --frozen python -m scripts.flickr_replacement_probe `
  --execute-disposable-public-probe `
  I-understand-this-creates-and-replaces-a-disposable-public-photo
```

Do not rerun after a timeout, exception, cancellation, or missing response.
Inspect the latest ignored `artifacts/flickr-replacement-probe-*/report.json`
and follow the [replacement ambiguity and reconciliation
contract](../replacement-ambiguity-reconciliation.md). A new command invocation
would create another baseline photo and is not recovery for the prior one.

## First live result

The authorized run completed with `passed_and_quarantined_private` after one
synchronous replacement dispatch. The replacement response and a fresh
observation retained the exact Flickr photo ID and photopage URL. The Flickr
Original matched the intended replacement bytes and remained a 192x128, 8-bit
RGB PNG. Owner, title, description, tags, public visibility during evidence
capture, the one controlled owner comment, and the one controlled album context
remained stable; the view count did not decrease.

Cleanup made the synthetic photo private and deleted the temporary album. The
ignored local report retains the private photo ID for deliberate later cleanup.
No resource ID, OAuth material, signed request, or private board content is
recorded in this public document.

The fixture had zero favorites and zero group contexts, so the run did not prove
preservation of nonempty state for either field. It also did not test
asynchronous replacement, ambiguous delivery, reverse replacement, rollback,
a historical photo, or bulk operation. Flickr's published contract still does
not promise preservation of identity, social state, or contexts. Existing
production and historical-photo replacement prohibitions therefore remain
unchanged.

Terry confirmed on 2026-08-26 that he has one Flickr account and no controlled
test group. The project will not recruit another account or use a
volunteer-managed group merely to expand this probe. Nonzero-favorite and
nonempty-group preservation therefore remain explicitly unproven.

## Lightroom Classic host follow-up

Ticket #0056 used a separate fresh disposable catalog, the installed Flickr
plug-in, and one private synthetic photo. The Flickr plug-in first published
the baseline PNG. Terry then performed exactly one replacement through Flickr's
website with the probe's replacement PNG. The Flickr photopage changed to the
replacement pixels while retaining the same page and baseline title.

The provider-owned Lightroom Classic catalog record did not detect or reconcile
the external replacement. It remained under **Published Photos**, retained the
baseline thumbnail, and did not enter a modified or republish state. That result
persisted after a normal Lightroom Classic host restart and catalog reopen. The
published-photo context menu offered **Show in Flickr** and **Mark to
Republish**, but no supported pull, refresh, or reassociation action. No
republish action was attempted.

This host observation covers external pixel replacement only. It does not
generalize to comment, favorite, or metadata synchronization. Terry's normal
workflow uses the Flickr plug-in for photo-content changes; the Flickr website
replacement was a controlled probe rather than a production practice. The
final synthetic photo remains private under the approved retention boundary.

## Evidence and limits

A passing first run can show only what that disposable case observed:

- the replacement response and a fresh `getInfo` retained the exact photo ID;
- the downloaded Flickr Original became the exact intended 8-bit PNG bytes;
- photopage URL, owner, public visibility during observation, title,
  description, tags, owner comment, views, favorite count, album contexts, and
  group contexts compared equal or met the explicit monotonic rule; and
- privacy quarantine succeeded after evidence capture.

The probe cannot turn observation into a Flickr guarantee. Unless separately
seeded under an authorized safe fixture, zero favorites and zero group contexts
prove only the empty case. It does not test asynchronous replacement, ambiguous
delivery, reverse replacement, backup/rollback, historical photos, or bulk
operation. The separate disposable-catalog follow-up establishes only the
Lightroom Classic host behavior recorded above. Those limits remain explicit
inputs to tickets #0055 through #0058 and prevent acceptance of production
replacement.
The accepted [backup and reverse-replacement
contract](../replacement-backup-and-reverse-replacement.md) treats a restore as
a new one-dispatch write rather than a rollback supplied by Flickr.
