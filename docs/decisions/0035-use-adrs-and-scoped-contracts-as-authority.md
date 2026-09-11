# ADR 0035: Use accepted ADRs and scoped contracts as architecture authority

Date: 2026-08-26

Authoritative-interaction-map exception reconciled: 2026-08-28

Status: Accepted by Terry on 2026-08-31

## Context

The repository contains accepted flow prose, proposed ADRs, detailed draft
contracts, a broad architecture overview, diagrams, FAQs, research, and project
logs. Several files necessarily discuss the same behavior, but their authority
has been implicit. That already produced visible drift: derived prose treated
the provider recommendation in proposed ADR 0033 as a selected deployment,
while the accepted zero-state flow called a draft wire contract
authoritative without explaining how its draft status constrained that claim.

Making one large architecture document canonical would not solve the problem.
It would duplicate route, state, persistence, security, and operations detail
and would become harder to review than the scoped contracts. Treating code or
the newest edit as truth would silently convert defects and unreviewed proposals
into policy.

## Decision

1. `AGENTS.md` and explicitly recorded owner directives govern repository-wide
   working rules, safety boundaries, terminology, and the owner-override
   process.
2. An ADR is architecture policy only when its own header says
   `Status: Accepted`. Proposed and draft material remains reviewable but is not
   policy.
3. An accepted or explicitly designated normative contract, acceptance
   specification, or interaction map owns detailed semantics within the scope
   of its governing accepted ADR. The narrower accepted source controls detail
   but cannot reverse the ADR. ADR 0041 is the sole current exception to the
   default that diagrams are derived views.
4. A later accepted ADR changes an earlier accepted source only by explicitly
   naming the supersession or amendment. Filename order, edit date, or detail
   does not imply precedence.
5. Future OpenAPI, PostgreSQL migrations, locked dependencies, Terraform, and
   production artifacts are exact executable projections only after their
   governing gates pass for the same release. A conflict with accepted
   architecture is a blocking defect; neither prose nor code silently wins.
6. `architecture.md`, `vision-and-scope.md`, the FAQ, diagrams not explicitly
   designated by an accepted ADR, and indexes are derived views. Research,
   reviews, experiments, logs, and open questions are evidence/history. Neither
   class creates policy.
7. The localswim board coordinates private work and review but is not a public
   architecture source. Durable owner decisions are recorded in ADRs/contracts
   without copying private board prose.
8. A conflict that remains after applying status, scope, and explicit
   supersession stops implementation and receives a new ADR/owner decision.
   The `AGENTS.md` pushback/override record remains mandatory for a surprising
   owner-held design.
9. The repository entry point is
   [`docs/README.md`](../README.md). The ADR index is tested against every ADR's
   own header so navigation cannot silently change status or omit a decision.

## Consequences

- A reviewer can determine whether a statement is accepted policy, proposed
  design, derived explanation, or evidence without relying on chat or board
  history.
- Detailed contracts remain small and independently reviewable; the repository
  does not create a monolithic duplicate specification.
- Proposed work can be thorough and implementation-ready without being
  mislabeled as accepted.
- Generated/runtime artifacts become strong evidence while remaining unable to
  legitimize accidental drift.
- Changes may touch an ADR, one scoped contract, executable projections, and
  derived views together. That is deliberate consistency work, not permission
  to copy the same detail everywhere.

## Rejected alternatives

- **Make `architecture.md` the one canonical file:** rejected because it would
  duplicate all detailed contracts and recreate a difficult-to-review monolith.
- **Latest edit wins:** rejected because edit order is not owner acceptance or
  explicit supersession.
- **Code wins:** rejected because an implementation defect or provider default
  must not amend safety policy accidentally.
- **Documentation wins even when deployment differs:** rejected because a
  claimed contract without build-bound executable evidence is not a passing
  release.
- **Put every detail in ADRs:** rejected because ADRs preserve consequential
  choices/rationale; schemas and scenario matrices belong in scoped contracts.
- **Use the private board as architecture memory:** rejected because the board
  is coordination state, has a private safe-space boundary, and is not a
  reviewable public specification.

## Detailed policy

The complete hierarchy, status vocabulary, document roles, conflict algorithm,
and change discipline are in
[`docs/README.md`](../README.md).
