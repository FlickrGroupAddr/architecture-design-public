# ADR 0003: License original FGA work under MIT

Date: 2026-08-20

Status: Accepted; reaffirmed by Terry on 2026-09-06

## Context

FGA is intended to remain easy to inspect, modify, self-host, and redistribute.
The repository contains original FGA work, a vendored open-source JSON library,
and a placeholder for an Adobe SDK that is licensed separately and excluded
from version control.

A repository-wide license and an explicit third-party boundary are needed so
users do not have to infer redistribution rights from individual documents.

## Decision

License original FGA source code and documentation under the MIT License,
copyright 2026 Terry Ott. Keep the authoritative license text in the repository
root.

Third-party components retain their upstream copyright and license notices.
Record bundled components in `THIRD_PARTY_NOTICES.md` and preserve required
notices in vendored source. Do not treat separately licensed or locally
installed materials, including the Adobe Lightroom Classic SDK, as covered by
FGA's MIT grant.

This decision applies to both the Lightroom plug-in and the hosted service.
Terry reaffirmed that project-wide scope on 2026-09-06 and directed that the
`FlickrGroupAddr/api-cloudflare` implementation repository be public. Repository
visibility does not narrow the MIT rights granted to anyone who receives a copy.
The private Localswim state-store repository is coordination state rather than
distributed FGA source or documentation and remains outside this decision.

## Consequences

- Users may use, modify, distribute, sublicense, and sell original FGA work
  under the conditions in `LICENSE`.
- Distributed copies must retain FGA's MIT copyright and permission notice.
- Dependency adoption includes a license-compatibility and notice-retention
  check.
- dkjson remains under David Heiko Kolf's MIT license; FGA does not relicense or
  remove its upstream notice.
- Adobe SDK files remain outside the repository unless their governing terms
  are obtained, reviewed, and handled explicitly.
