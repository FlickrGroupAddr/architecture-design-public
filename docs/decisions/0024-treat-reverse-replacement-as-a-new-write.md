# ADR 0024: Treat reverse replacement as a new write

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31

## Context

Flickr does not document retained prior Originals or an atomic rollback API.
Sending the previously downloaded bytes to the replacement endpoint is another
non-idempotent write, not restoration of the whole public resource. It can lose
its response, race an external change, or preserve pixels while remote metadata
and social state differ.

The prior Original is also not reproducible merely because Lightroom Classic
retains a RAW source and develop settings. Encoder, metadata, application, and
settings changes can produce different file bytes.

## Decision

Before any future FGA LrC plug-in replacement dispatch, retain two independently
verified operation bundles on different owner-controlled volumes. Each bundle
contains the exact downloaded baseline Original, exact intended replacement,
and a canonical manifest with fingerprints and the pre-write remote-state
snapshot. Retain both bundles indefinitely and introduce no product cleanup
control in this scope.

A reverse replacement is allowed only after exact forward success, fresh proof
that Flickr still holds the intended new Original, fresh verification of both
backup bundles, and explicit one-photo owner confirmation. It creates a new
replacement operation with its own durable marker and one-dispatch ambiguity
rules. It never runs automatically and never claims to restore metadata,
engagement, albums, groups, permissions, dates, or URLs.

This decision is conditional safety design. It does not accept replacement into
FGA product scope while ADR 0008 and ADR 0022 still prohibit it.

## Consequences

- Each operation consumes twice the sum of the baseline and intended file sizes
  across the two required vaults, plus small manifests.
- The FGA API backend and FGA database store fingerprints and state, not
  photography bytes or local metadata snapshots.
- Missing capacity or either unavailable copy prevents a destructive write.
- Exact reverse bytes remain possible after a successful forward operation, but
  an ambiguous forward or external byte change correctly sacrifices automated
  recovery.
- A reverse can itself become permanently ambiguous and require manual Flickr
  repair.

## Alternatives considered

- **Trust Flickr to retain the prior Original:** rejected because no such
  contract is documented.
- **Re-render the RAW when a restore is needed:** rejected because it does not
  prove exact prior bytes.
- **Keep only one temporary copy:** rejected because ordinary disk loss or
  cleanup would remove the sole recovery input after a destructive write.
- **Store image backups in the FGA API backend:** rejected because the direct
  image boundary avoids hosted photography storage and two local volumes are
  sufficient for the private conditional design.
- **Build a custom encrypted/deduplicated vault:** rejected until actual scale
  demonstrates a need; ordinary owner-controlled volumes and explicit byte
  verification are easier to understand and recover.
- **Automatically reverse when the forward operation fails:** rejected because
  the forward outcome may be unknown and the reverse is itself another
  non-idempotent write.

## Detailed contract

The [replacement backup and reverse-replacement
contract](../replacement-backup-and-reverse-replacement.md) defines bundle
contents, pre-dispatch verification, retention, failure behavior, and reverse-
replacement acceptance.
