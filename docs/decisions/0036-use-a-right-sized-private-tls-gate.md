# ADR 0036: Use a right-sized private TLS acceptance gate

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-25; provider-specific wording amended by
Terry's 2026-08-28 decision to keep hosting providers undecided

## Context

The initial TLS acceptance proposal made Qualys SSL Labs, Hardenize,
ImmuniWeb, `testssl.sh`, SSLyze, Nmap, and targeted OpenSSL probes part of a
recurring gate. That matrix was defensible for broad public exposure but was
disproportionate for the private, single-owner MVP. Several tools overlap in
protocol/cipher enumeration, hosted-service availability could hold routine
maintenance hostage, and each additional tool adds pinning, terms, output,
triage, and drift work without exercising the actual Lightroom Classic host
path.

The relevant risks are more directly covered by the required client, one
reproducible local scanner, one independent hosted implementation, and the
certificate/deployment lifecycle. A grade or scanner vote cannot prove that
the documented `LrHttp` path works, that managed renewal is observed, or that
the edge can be reconstructed from source.

## Decision

For the private MVP, the complete core TLS gate consists of:

1. a real request from the FGA Diligence plug-in through documented `LrHttp` in
   the supported Lightroom Classic-on-Windows target;
2. a complete scan by a pinned stable `testssl.sh`, with retained structured
   machine-readable output;
3. one fresh independent Qualys SSL Labs assessment; and
4. certificate issuance, preview rollover, naturally observed managed-renewal,
   and isolated deployment-restore evidence.

The eventual FGA HTTPS edge starts with the selected provider's tightest
conventional TLS 1.3-only policy. The Google Cloud candidate maps that rule to
the `RESTRICTED` SSL policy with minimum TLS 1.3; this mapping does not select
Google Cloud. A real-client failure does not authorize a silent relaxation; the
minimum exception requires a recorded failed probe, security tradeoff, Terry's
explicit decision, and an accepted ADR amendment.

Additional scanners are diagnostic and risk-selected. A transport incident, a
material edge change, or public/multi-user expansion requires an explicit risk
review and appropriate additional diagnostics, but not a standing vendor
matrix. Scanner results are investigated; they are never combined by majority
vote.

The detailed gate, evidence binding, outage behavior, lifecycle semantics, and
retest triggers are normative in
[`docs/operations/tls-edge-acceptance.md`](../operations/tls-edge-acceptance.md).

## Consequences

- The recurring gate remains independent and reproducible while matching the
  private deployment's actual risk and operating capacity.
- The supported Lightroom Classic host path is first-class acceptance evidence,
  rather than an afterthought beside generic scanners.
- The hosted implementation must pin and review one local tool instead of
  maintaining several overlapping toolchains.
- SSL Labs availability can still block initial or planned acceptance because
  one external implementation is deliberately required.
- Initial acceptance records managed renewal as configured but not yet
  observed. The first natural renewal is a continuing acceptance milestone;
  documentation must not invent an immediate renewal pass.
- Incidents, material edge changes, and broader exposure receive extra
  diagnostics chosen for their actual risks instead of inheriting an obsolete
  checklist.

## Rejected alternatives

- **Keep every scanner in the standing gate:** rejected as recurring overlap
  and operational burden without a private-MVP requirement.
- **Use only `testssl.sh`:** rejected because an implementation-independent
  hosted view catches vantage-point and endpoint differences.
- **Use only SSL Labs:** rejected because a hosted grade is not reproducible
  local evidence and cannot replace raw retained findings.
- **Use browser probes instead of Lightroom Classic:** rejected because they do
  not exercise the Lightroom Classic host networking stack used by the FGA LrC
  plug-in.
- **Claim renewal at initial issuance:** rejected because managed automatic
  renewal is time-dependent and cannot honestly be forced on demand.
- **Run the restore drill against production:** rejected because an isolated
  preview reconstruction proves the deployment path without manufacturing a
  production outage.
