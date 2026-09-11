# ADR 0041: Use the clean-room authentication tabs as interaction authority

Date: 2026-08-28

Tab-1 proactive JWKS refresh amendment accepted: 2026-08-30

Tab-3 publish-and-group-submission amendment accepted: 2026-08-31

Status: Accepted

## Context

The clean-room authentication diagram was rebuilt collaboratively as a memory
map for Terry returning to the project in 2031. Its three tabs communicate the
browser-session, Plugin Code, and publish-and-group-submission happy paths more
directly than a prose-only walkthrough. On 2026-08-31, after reviewing the third
tab's content and presentation, Terry called it “gospel” within its declared
scope and accepted it as a 2031-Terry ramp-up tool. He also stated the governing
boundary: diagrams are necessary but not sufficient. Treating any of the three
tabs as merely illustrative would allow its numbered sequence, acting
components, or visible trust boundaries to drift while the repository continued
to call the picture canonical.

The tabs are deliberately simplified. They omit most error branches, exact
payload schemas, lifecycle recovery, and deployment choices. Making every
omission normative would turn a readable interaction map into an ambiguous
protocol specification and would duplicate the detailed contracts.

## Decision

The three tabs in
[`clean-room-authentication-legal.drawio`](../diagrams/clean-room-authentication-legal.drawio)
are authoritative interaction specifications within the following scope:

1. **Tab 1, Browser session creation**, controls the depicted happy-path actors,
   component and persistence boundaries, interaction order, and explicitly
   named security invariants for creating an FGA browser session. This includes
   direct Google Identity Services sign-in, the FGA Google Login Endpoint,
   cookie/body GIS CSRF comparison, the unnumbered asynchronous FGA JWKS refresh
   worker and shared cache, current-JWKS validation, the internal `fgaUserId`,
   256 bits of server-generated entropy, an unsalted `SHA2-256` session-token
   lookup key, atomic session/audit persistence, and the host-only 24-hour
   `Secure`/`HttpOnly`/`SameSite=Strict` cookie.
2. **Tab 2, Plugin Code transfer**, controls the depicted happy-path actors,
   component and persistence boundaries, interaction order, and explicitly
   named security invariants for listing Plugin Code metadata, creating one
   Plugin Code, and transferring it on the same workstation into the FGA LrC
   plug-in. This includes ownership through the session's `fgaUserId`, durable
   list-read audit before metadata release, 256 bits of server-generated Plugin
   Code entropy, digest-only credential persistence, atomic creation/audit,
   one-time no-store plaintext return, direct user paste, immediate
   `LrPasswords` storage, and clearing the transient plug-in input.
3. **Tab 3, Publish PNG and group submission**, controls the depicted happy-path
   actors, component and persistence boundaries, interaction order, and
   explicitly named safety invariants from local Album setup through one
   representative photo's durable group-intent handoff. This includes Plugin
   Code retrieval and Bearer verification, the bounded writable-group snapshot,
   Lightroom Classic PNG rendering and exact-size preflight, allowlisted
   metadata crossing into the FGA API backend without image bytes, one fresh
   no-store service-signed upload envelope held only in memory, direct PNG
   streaming to Flickr, local recovery evidence and remote-ID binding, a `202`
   durable group-intent handoff, fresh exact-photo membership and moderation
   reads before each add attempt, the depicted sub-second moderation-to-add
   bound, add-only behavior, and the zero-group skip. It does not authorize
   automatic replay of an upload or group add whose delivery may have occurred.
4. The tab-2 **FGA Plugin Code API** label authoritatively identifies `GET`,
   `POST`, and `PATCH` as its methods. The numbered interaction sequence covers
   list and creation only; ADR 0040 controls the unpictured PATCH request and
   revocation semantics.
5. Each tab's numbering is local and intentionally restarts at step 1. Tab
   order provides the cross-tab sequence without forcing a human reader to
   resume at step 13.

The three tabs are necessary but not sufficient. A conforming design or
implementation must not contradict their depicted actors, boundaries, ordering,
or explicit invariants, and must also satisfy the accepted ADRs and scoped
contracts that supply omitted detail. A diagram omission never waives a
requirement from those controlling sources, and matching the diagram alone does
not establish architecture or implementation acceptance.

The tabs are not exhaustive authority for exact unshown URIs, payload schemas,
error branches, rate limits, logout, session cleanup, recent-authentication
mechanics, Plugin Code revocation/rotation/recovery, provider selection, remote
Flickr Album materialization or attachment, multi-photo ordering, or omitted
failure and recovery behavior. Accepted ADRs and scoped contracts control those
details and may add requirements that do not contradict the depicted path. The
diagram does not make glyph choice, coordinates, spacing, color, or arrow
routing an architecture requirement.

The legal-landscape draw.io file is the human-reviewable authoritative map. The
Python builder is its maintainable source model, and the committed legal/4K SVG
and 4K draw.io files are generated projections. Freshness tests must keep every
projection semantically identical. A conflict between any tab and a detailed
source is a documentation defect: determine the intended decision, then update
the diagram, governing source, executable projection, and drift tests together.

The direct Browser-to-authoritative-DNS relationship and shared undecided
hosting boundary retain the explicitly recorded owner-approved simplification
in the diagram notes. It is authoritative as a conceptual dependency only, not
as a literal DNS packet path or provider-selection decision.

This decision creates a narrow exception to the repository default that
diagrams are derived views. No other diagram becomes normative without a later
accepted decision naming its file, tab, and scope.

## Consequences

- Future Terry can trust the three numbered happy paths without reconstructing
  them from several contracts.
- Detailed documents may remain more complete than the diagram, but they may
  not reverse an actor, order, boundary, or explicit invariant shown there.
- The FGA LrC plug-in input control's visual treatment is an implementation
  choice. Security depends on transient handling, validation, immediate
  `LrPasswords` storage, and clearing—not on labeling the control password-style.
- Provider-undecided labels remain real architecture state rather than blank
  space to be filled by inference.
- Diagram changes now require the same review discipline as changes to other
  normative interaction specifications.

## Alternatives considered

- **Keep the tabs derived:** rejected because the project owner explicitly
  accepted them as the durable interaction map, and derived status would permit
  silent sequence drift.
- **Make the tabs exhaustive protocol specifications:** rejected because their
  deliberate omissions would create ambiguity and duplicate detailed contracts.
- **Copy every contract detail into more tabs:** rejected because the resulting
  shock-and-awe diagram would no longer serve its 2031-Terry audience.
