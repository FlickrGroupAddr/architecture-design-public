# ADR 0019: Rotate revisioned installation credentials without normal-authority overlap

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31

## Context

The private MVP issues one long-lived high-entropy bearer credential to each
FGA LrC plug-in installation. One-time display and `LrPasswords` storage cover
initial provisioning but do not define safe planned rotation, an ambiguous
rotation response, revocation from a lost workstation, or recovery after one
local key is replaced and another is not.

Replacing the only local credential before proving the new server value can
strand the FGA LrC plug-in. Enabling old and new values for all routes until an
administrator remembers to revoke one creates an unbounded overlap. Promoting a
candidate during the safe current-installation GET would make GET mutate
authorization state and violate the administrative/HTTP contract.

## Decision

The FGA database separates a stable installation from revisioned credential
versions. An active installation has exactly one `current` version and at most
one 15-minute `pending_rotation` candidate; replaced, revoked, and expired
versions retain history but authorize nothing. Database constraints and
exhaustive runtime matching enforce those states.

Initial issuance creates the first current version. Planned rotation requires
the recent Google reauthentication proof required by ADR 0043 and returns one
new candidate through ADR 0018's
same-workstation transfer. The candidate cannot call ordinary FGA LrC plug-in
routes; it can only read the current-installation resource and receive the
non-secret `pending_rotation` presented-credential state. Terry then uses a recent-authenticated administrative POST
against the exact installation/candidate/revision to atomically promote it,
retire the old current version, update the installation revision, and append
lifecycle evidence. There is no normal-route interval with two active
credentials, and the candidate never grants itself broader authority.

The FGA LrC plug-in stores the candidate under a second fixed `LrPasswords`
key. After candidate verification and administrative completion, it observes
the candidate's `current` state, writes and verifies the current key, and only
then clears the candidate key. A crash or lost response resumes by checking the
candidate state and never falls back to the locally retained old value. SDK
15.3 documents no delete operation, so clearing uses documented
`LrPasswords.store` with an empty string plus `retrieve` verification.

Installation revocation is an administrator-authenticated, revisioned database
transaction that revokes current and pending versions together. Lost or
suspected-compromised workstations use revocation plus a new installation, not
rotation. The FGA administrative control plane reports server revocation
separately from unprovable endpoint erasure. Revocation stops new API
transaction commits after an authoritative in-transaction credential recheck;
it cannot recall already returned upload authority or cancel work already
durably accepted.

The current version has an annual advisory rotation date. The annual diligence
run exercises rotation, but an overdue date alerts rather than automatically
breaking an offline workstation. Incident evidence triggers immediate
revocation or rotation according to whether compromise is suspected.

The complete states, routes, races, `LrPasswords` behavior, recovery,
inventory/audit fields, and conformance matrix are in the
[private installation credential lifecycle](../installation-credential-lifecycle.md).

## Consequences

- Rotation proves the candidate and retires the old value in one database
  transaction without a long dual-authority window.
- One additional credential-version table, one pending candidate, one
  administrator completion POST, and the current-installation representation's
  presented-credential state make crash recovery explicit.
- Terry must return to the administrative browser after the FGA LrC plug-in
  verifies the candidate, then finish the local key move. Completing too early
  can strand that local transfer but does not grant a second normal credential;
  the administrator can start another candidate or revoke the installation.
- The candidate is a bearer secret with narrowly scoped pre-activation
  authority; its transfer requires the same protection as initial issuance.
- Lost-workstation recovery does not depend on the lost endpoint and does not
  overclaim local secret deletion.
- Annual planned rotation is operational work, but it continuously exercises
  the recovery path before an incident needs it.
- A stale upload envelope or already accepted intent can outlive credential
  revocation under its own bounded contract; the UI must state that residual.

## Alternatives considered

- **Two fully active credentials until manual cleanup:** rejected because a
  forgotten second value creates indefinite authority overlap.
- **Overwrite the current local key before server proof:** rejected because a
  bad transfer or outage strands the installation and destroys its only usable
  local value.
- **Promote on the safe current-installation GET:** rejected because authorization mutation
  belongs on an explicit administrator POST and must be safely repeatable after
  a lost response.
- **Let the candidate credential promote itself through an FGA LrC plug-in
  POST:**
  rejected because the already available recent-authenticated administrative
  control plane is the conventional authority for broadening credential scope;
  the candidate needs only safe proof that it was transferred correctly.
- **Automatically expire every current credential on a fixed date:** rejected
  because an offline private workstation would fail without evidence of
  compromise; the due date instead drives a tested planned rotation.
- **Rotate a suspected-stolen credential:** rejected because the thief could
  race during the planned overlap. Revoke the installation first and issue a
  new identity after endpoint repair.
- **Copy `LrPasswords` or catalog state to a replacement workstation:** rejected
  because endpoint migration is not a confidential credential lifecycle and a
  lost device must remain independently revocable.
