# Research and review evidence

Authority: Evidence and provenance; not a normative architecture source. Apply
the [documentation authority hierarchy](../README.md).

Research files record external contracts, experiments, implementation probes,
reviews, and reconciliation. `Complete`, `verified`, or `validated` means the
stated investigation reached its evidence boundary; it does not accept a
product decision or prove a future production deployment.

Externally changeable claims retain their source and verification date and must
be refreshed before implementation or release when the governing contract
requires it. Reviews preserve what was found at their pinned baseline. Current
decisions and corrections belong in ADRs/scoped contracts; review text points to
that resolution rather than becoming another live specification.

## Current candidate evaluations

- [Hosted compute candidate comparison](2026-09-05-hosted-compute-candidate-comparison.md)
  compares Cloudflare Workers, AWS Lambda, and Google Cloud Run after the FGA
  database hosting changed to Amazon RDS for PostgreSQL 18.6. It records a
  provisional order and provider-acceptance gates without selecting a provider.
