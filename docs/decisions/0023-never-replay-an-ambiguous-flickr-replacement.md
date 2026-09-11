# ADR 0023: Never replay an ambiguous Flickr replacement

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31

## Context

Flickr's replacement endpoint accepts an existing photo ID and new image bytes,
but it publishes no idempotency key or upper bound after which an unobserved
replacement is proven not to occur. A client can lose the response after bytes
leave, and observing the old Original afterward does not prove a delayed write
will never converge.

Replaying that operation could overwrite an established public photo twice or
apply an old intended edit after later manual repair. A response photo ID alone
also cannot establish exact new pixels.

## Decision

If replacement later enters FGA scope, the FGA API backend will commit one
durable dispatch marker and count before releasing a one-shot signed Flickr
envelope. Once that marker exists, no FGA component will release another
envelope or dispatch another replacement POST for the operation.

The FGA replacement reconciliation worker will download and hash the
authoritative Flickr Original. Only the exact intended SHA2-256, byte count,
format, and dimensions on the exact bound photo can establish
`verified_new_original`. The baseline Original after dispatch remains uncertain,
because it is not proof against later convergence. An unavailable, conflicting,
or third Original never becomes retry permission.

An unresolved or divergent operation creates a permanent automated-replacement
block for that Flickr photo. Read-only rechecks are allowed; automatic, manual,
administrative, and recovery replay through FGA are not. Manual Flickr UI repair
does not erase the durable history or clear the block.

This decision defines conditional safety behavior only. ADR 0008 and ADR 0022
continue to prohibit pixel replacement until the disposable experiment and all
remaining replacement tickets support a later explicit scope decision.

## Consequences

- A false-positive marker can strand an operation even when no Flickr bytes
  left. That is the deliberate cost of avoiding a harmful duplicate overwrite.
- Exact Original hashing can prove current intended bytes but not social-state,
  album, catalog, rollback, or long-term preservation.
- The direct-to-Flickr byte path remains possible without giving the FGA API
  backend the image, but it cannot be made atomic with hosted persistence.
- Some failed operations require permanent abstention by FGA replacement
  components and manual work in Flickr rather than a retry button.

## Alternatives considered

- **Retry when the old Original is still visible:** rejected because Flickr
  documents no deadline proving that the first replacement cannot arrive later.
- **Retry after a fixed timeout:** rejected for the same reason; elapsed time is
  not zero-byte proof.
- **Trust the response photo ID without hashing the Original:** rejected because
  it proves neither uploaded byte identity nor completion.
- **Let the owner force replay through an administrative control:** rejected
  because it turns an ambiguous destructive write into a misleading retry.
- **Proxy and retain all replacement bytes in the FGA API backend:** rejected as
  unnecessary for this boundary and contrary to the established direct image
  path; backup storage remains a separate #0058 decision.

## Detailed contract

The [replacement ambiguity and reconciliation
contract](../replacement-ambiguity-reconciliation.md) defines the durable
record, one-shot dispatch transaction, observation classifications, recovery
rules, and required conformance evidence.
