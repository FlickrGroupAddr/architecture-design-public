# Architecture documentation authority

Last updated: 2026-09-05

Status: Accepted repository documentation policy under ADR 0035; Terry accepted
the governing decision on 2026-08-31

This is the entry point for deciding which FGA document controls when several
files discuss the same subject. The repository deliberately keeps decisions,
detailed contracts, derived explanations, and evidence separate. “Newest file”
and “most detailed file” are not authority rules.

## Authority hierarchy

Apply the first applicable row. A lower row cannot silently amend a higher one.

| Precedence | Source | What it controls |
| --- | --- | --- |
| 1 | [`AGENTS.md`](../AGENTS.md) and a later explicit owner directive recorded under its override process | Repository working agreement, safety boundaries, terminology, required process, and explicit owner overrides |
| 2 | An ADR whose own header says `Status: Accepted` | Consequential architecture/product decision and rationale within that ADR's scope |
| 3 | A normative contract, acceptance specification, or interaction map whose own status says it is accepted, or whose governing accepted ADR explicitly designates it | Detailed state, wire, persistence, security, UI, operations, interaction, and evidence semantics within its declared scope |
| 4 | Locked/generated executable specifications and production artifacts that passed their governing acceptance gates | Exact OpenAPI/schema/configuration/runtime projection of accepted decisions and contracts; they supply evidence, not permission to contradict them |
| 5 | `Proposed` or `Draft` ADRs/contracts | Reviewable recommendations only; they are not accepted project policy and cannot weaken an accepted boundary |
| 6 | Architecture overview, vision synthesis, FAQ, diagrams not explicitly designated by an accepted ADR, indexes, and README navigation | Derived explanation and discovery; useful, but never an independent decision source |
| 7 | Research, reviews, experiments, project logs, and open-question inventories | Evidence, provenance, historical context, or undecided work; completion of research does not accept a design |

The current repository contains architecture, contracts, diagnostics, and
research but no production FGA LrC plug-in or hosted implementation. There is
therefore no OpenAPI, production migration head, Terraform state, or deployed
artifact at precedence 4 yet. A proposed contract may be implementation-ready
without becoming accepted merely because its ticket reached review.

## Status vocabulary

Every ADR's own `Status:` field is canonical for that ADR. The
[ADR index](decisions/README.md) is navigation derived from those headers and is
tested for exact agreement.

- `Accepted` means Terry approved the decision and it is current policy.
- `Proposed` means the recommendation is complete enough for review but is not
  policy yet.
- `Draft` means material design work or review is still open and is not policy.
- `Superseded` means a named later accepted source replaced the document's
  current authority; the file remains provenance.
- `Rejected` means the proposal was deliberately declined and remains rationale,
  not a fallback implementation option.
- `Complete`, `validated`, or `implemented` on research, a probe, or a review
  describes evidence completion only. It does not mean an architecture decision
  was accepted or a production gate passed.

A contract may contain sections with different explicit review states. The
[zero-state publish flow](zero-state-publish-flow.md) is the current example:
sections whose `Review:` text records Terry's acceptance are normative within
accepted ADR boundaries; text explicitly labeled proposed remains proposed.
When mixed status becomes difficult to review, split the proposed supplement
into its scoped contract rather than making readers infer status from dates.

## Document roles

### Decisions

[`docs/decisions/`](decisions/README.md) owns consequential choices and their
rationale. An ADR stays small enough to answer what was chosen, why, material
consequences, and rejected alternatives. It links to a detailed contract rather
than duplicating every field and test case.

If accepted ADRs overlap, the narrower ADR controls its stated detail. A later
accepted ADR changes an earlier one only when it explicitly names the
supersession or amendment. A date, filename number, or newer prose paragraph is
not implicit supersession.

### Normative contracts and acceptance specifications

Top-level contract files plus explicitly status-labeled files under
`docs/operations/` and `docs/testing/` may own detailed requirements when their
status/governing decision is accepted. Scope must be explicit. Examples include wire schemas,
state transitions, database invariants, operator ceremonies, and mandatory
conformance cases.

An accepted ADR may also designate a narrowly scoped diagram tab as a normative
interaction map. The designation must name the file and tab, state exactly what
visual semantics control, and identify what remains with detailed contracts.
[ADR 0041](decisions/0041-use-clean-room-authentication-tabs-as-interaction-authority.md)
does this for all three tabs in the clean-room authentication diagram.
Coordinates, styling, and omitted mechanics do not become policy by inference.

The most specific accepted contract controls detail that its accepted ADR left
open. It cannot reverse the ADR's decision. A required test contract proves the
same behavior; it does not create different production semantics merely because
a fixture is easier to implement.

### Executable projections

The future hosted repository will generate OpenAPI from the registered FGA API
backend routes/types, apply versioned PostgreSQL migrations, lock dependencies,
and declare provider infrastructure. Those artifacts become the exact
machine-readable/runtime projection only after their acceptance gates pass for
the same build and migration head.

Code does not “win” a conflict with an accepted ADR or contract. Documentation
does not “win” by concealing a deployed mismatch either. A mismatch is a defect:
stop promotion, identify the intended decision, change the incorrect source and
all derived projections in one review, then rerun the gates. Never normalize
drift by documenting accidental implementation behavior after the fact.

### Derived views

The following are deliberately non-normative:

- [`architecture.md`](architecture.md) is the concise system overview;
- [`vision-and-scope.md`](vision-and-scope.md) synthesizes user/product intent;
- [`../openapi/`](../openapi/README.md) projects the planned HTTP route and
  closed-schema subset while preserving unresolved schema gaps explicitly;
- [`future-terry-faq.md`](future-terry-faq.md) explains the design in question
  form;
- [`diagrams/`](diagrams/README.md) visualizes selected flows and states, except
  for the three clean-room authentication tabs narrowly designated as
  normative interaction maps by ADR 0041; and
- repository/document indexes provide navigation.

Every derived view must cite the controlling ADR or contract near a consequential
claim and preserve its status. Derived prose cannot turn `Proposed` into
`Accepted`, invent an exception, or become a second list of wire fields. If a
derived view conflicts, fix or remove the derived text; do not reinterpret the
normative source to preserve the summary.

### Evidence and history

[`research/`](research/README.md) records current external evidence, experiments,
reviews, and reconciliation. [`project-log/`](project-log/README.md) preserves
chronological provenance. A completed review may identify work and say how it
was reconciled, but current decisions must be recorded in ADRs/contracts.
Historical wording remains historical unless a current source adopts it.

[`open-questions.md`](open-questions.md) is a non-normative inventory. A resolved
entry points to the decision that closed it; the question list never reserves
authority after that decision.

The private localswim board coordinates work, priority, review, and handoff. It
is not a public architecture specification and its private prose must not be
copied here. An owner decision that changes durable architecture must be
recorded in the applicable ADR/contract before implementation relies on it.

## Conflict and gap handling

When sources appear to conflict:

1. identify each source's role and explicit status;
2. apply the hierarchy and the narrowest controlling accepted scope;
3. check whether a later accepted ADR explicitly supersedes or amends the
   earlier source;
4. treat an implementation/specification mismatch as a blocking defect, not a
   tie-breaker; and
5. if accepted sources still genuinely conflict or leave a consequential gap,
   stop and record a new ADR or owner decision rather than choosing silently.

The architecture-pushback and owner-override checkpoint in `AGENTS.md` remains
mandatory. An override record states the conventional recommendation, objection,
owner justification, accepted tradeoffs, and date without rewriting disagreement
as consensus.

## Change discipline

A normal architecture change follows one visible direction:

1. record the consequential choice in an ADR and obtain acceptance when owner
   approval is required;
2. update the narrow normative contract that owns the detailed behavior;
3. update or generate OpenAPI, migrations, provider configuration, and tests
   from that accepted contract;
4. update derived overview, FAQ, and diagrams in the same change when their
   claims are affected; and
5. retain evidence bound to the exact build/migration/configuration rather than
   claiming that prose alone passed an executable gate.

Do not copy a schema, route list, state machine, or configuration value into a
new “canonical” Markdown file. Link to its existing scoped owner. If two files
both appear to own the same detail, consolidate ownership and leave the other as
a linked derived explanation.
