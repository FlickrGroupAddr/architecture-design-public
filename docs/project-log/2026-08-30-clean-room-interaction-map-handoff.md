# Clean-room interaction-map session handoff

Date: 2026-08-30

Authority: Historical session handoff. Current architecture authority remains
with the accepted ADRs, scoped contracts, and the first two diagram tabs named
by ADR 0041.

## Why this handoff exists

Terry is ending a long collaborative diagram session and intends to restart on
2026-08-31 with fresh model context. This is the cold-start resume point for the
clean-room interaction-map work. Read `AGENTS.md`, this handoff, and
[`docs/diagrams/README.md`](../diagrams/README.md) before changing the diagram;
chat history is not required.

## Completed diagram state

The canonical source is
[`clean-room-authentication-legal.drawio`](../diagrams/clean-room-authentication-legal.drawio).
Its maintainable model is `scripts/build_clean_room_auth_diagram.py`; the legal
SVG, 4K draw.io, and 4K SVG files are generated derivatives. Do not edit a
generated derivative as the source of truth.

- **Tab 1 — Browser auth w/ backend** is an authoritative happy-path map under
  ADR 0041. It includes the proactive FGA JWKS refresh worker, a maximum
  six-hour nominal refresh interval with cache-metadata-driven earlier refresh,
  and the bounded unknown-signing-key fallback on the login path.
- **Tab 2 — Plugin Code transfer** is an authoritative happy-path map under ADR
  0041. It covers Plugin Code list/create/audit, the same-workstation one-time
  transfer, immediate `LrPasswords` storage, and transient-field clearing.
- **Tab 3 — Publish PNG + groups** is a review draft. It starts with local
  **Create Album…**, one or more photos added to the Album, per-photo group
  selection, and Album **Publish Now**. It then traces one representative photo
  through FGA LrC plug-in authentication, PNG render and preflight, direct Flickr
  upload, hosted photo binding, durable group-intent handoff, and fail-polite
  add-only group submission. Remote Flickr Album materialization and attachment
  remain deliberately omitted and subordinate to their controlling contracts.

The legal sheet retains Terry's `0.3 in` content margin on every edge. Tab 3
uses the owner-approved Flickr wordmark recorded by ADR 0042. Its legend font is
`13.25`, the largest fitting quarter-point candidate: `13.5` placed step 19 on
the bottom border, while `13.25` fits both axes in the pixel render. Arrow
endpoints, badge stacks, label alignment, boundary gutters, and the component
triangles were pixel-reviewed during the session.

## Documentation and validation state

The closeout reconciled the authority prose to say **first two tabs** wherever
the now-three-tab source is discussed. The diagram notes now describe tab 3's
local Album setup, 19-step numbering, zero-group skip, and remote Album omission.
Tab 3 was not silently promoted to normative authority.

At the beginning of closeout, local `main` was clean at `302d583` and 20 commits
ahead of `origin/main`. This handoff adds one further local commit; no push is
implied or authorized by this document. The final gate ran Ruff formatting and
lint, strict Pyright, all 138 unit tests, generated-diagram freshness, and
`git diff --check` successfully.

## localswim handoff

FGA cards `#0076`, `#0077`, `#0079`, `#0080`, `#0081`, `#0082`, and `#0083`
are at **Ready for review**. Their authoritative private comments record the
individual evidence and commit history; this public handoff intentionally does
not reproduce that prose. The recorded dependency from `#0077` to `#0076`
remains intact and has not been declared resolved merely because both cards are
reviewable.

## Exact restart point

1. Let the trusted session-start hook restore and retarget both localswim
   services and monitors, then run the inception-priority barrier before FGA
   work.
2. Confirm `git status -sb`, because the diagram series and this handoff are
   local commits ahead of `origin/main` at closeout.
3. Open the legal tab-3 SVG or draw.io tab and review the Ready-for-review card
   hierarchy. No further diagram edit is queued by this handoff.
4. Terry's next design decision is whether tab 3 remains a derived review draft
   or is accepted as a narrowly scoped interaction authority. Acceptance would
   require an explicit ADR 0041 amendment plus the matching authority prose and
   drift-test changes; do not infer it from the visual closeout alone.
5. If a later content change reflows the tab-3 legend, repeat the quarter-point
   pixel-fit check instead of assuming `13.25` remains maximal.

Use `/exit` for the supported session boundary so the SessionEnd hook initiates
the detached graceful shutdown and final board autopush.
