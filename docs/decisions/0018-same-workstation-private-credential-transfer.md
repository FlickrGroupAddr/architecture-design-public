# ADR 0018: Transfer the private installation credential by same-workstation paste

Date: 2026-08-26

Transient-input clarification: 2026-08-28

Canonical clear-text comparison clarification: 2026-09-03

Status: Accepted by Terry on 2026-08-31

## Context

ADR 0006 accepts one administratively generated 256-bit bearer credential for
each private Lightroom installation. The FGA LrC plug-in has no preexisting
authority and no documented secure-random source, so it cannot bootstrap an
independently authenticated pairing flow by itself. The accepted decision left
the exact confidential handoff unspecified.

The handoff must not put the bearer secret in a file, URL, command line, log,
chat, email, issue, ordinary Lightroom preference, catalog, or diagnostic
record. Adding a short redemption code would create another bearer endpoint,
state machine, limiter, expiry, and ambiguous recovery path for one owner and
one workstation. Persisting the secret in a password manager would add a second
durable secret store outside `LrPasswords`.

## Decision

The private MVP uses one same-trusted-workstation manual paste ceremony. Terry
opens a clean private-browsing window on the target Windows/Lightroom Classic
workstation, verifies Clipboard history and cross-device sync are off, performs
the allowlisted recent-authentication administrative create, copies the
one-time-displayed value, pastes it into the FGA LrC plug-in's transient Plugin
Code input, compares the simultaneous clear-text browser and plug-in values,
and immediately stores it with documented `LrPasswords`. Under ADR 0044, both
surfaces use the same canonical grouped Crockford Base32 spelling, monospace
font, size, weight, and slashed-zero treatment. This presentation is required
for visual verification, although it is not an authentication boundary.

The FGA LrC plug-in neither opens nor communicates with the browser. The FGA
API backend creates no device/claim code, unauthenticated redemption endpoint,
polling state, callback listener, custom URI, download, QR code, or replacement
session. The existing credential itself crosses only the current local
clipboard and only for the brief transfer interval.

The FGA administrative control plane renders the credential once in an
in-memory, no-store, same-origin transfer view with no third-party content,
form, browser persistence, print/download control, or secret-echo route. Its
copy action is an explicit user-gesture clipboard write. After the plug-in
stores and verifies the credential, an explicit erase action overwrites the
current clipboard with a fixed non-secret sentence, removes the rendered value,
and Terry closes the entire private-browsing window. Clipboard history, sync,
third-party clipboard managers, remote control, screen recording, and observers
are prohibited for the ceremony.

The plug-in performs ADR 0044's strict syntax validation without normalization,
alias mapping, trimming, or hyphen repair, stores the value under its fixed
plug-in-scoped `LrPasswords` key, clears the input
and Lua references, retrieves the stored value, and makes the fixed HTTPS
Bearer token check. A transient service failure retains the value only in
`LrPasswords` for later verification. A malformed/invalid value, lost display,
secure-store failure, or unknown create outcome requires clearing local
transient state, revoking the server identity, and creating another credential;
plaintext is never reconstructed or redisplayed.

The complete preconditions, sequence, failure table, and conformance cases are
in the
[private installation credential transfer ceremony](../private-install-credential-transfer.md).
ADR 0044 defines the exact canonical encoding and presentation.

## Consequences

- The bootstrap uses the existing owner authentication, credential, browser,
  clipboard, transient plug-in input, and OS-backed `LrPasswords`; it adds no
  second protocol or public unauthenticated route.
- Terry must perform credential creation on the target Lightroom workstation,
  even if the earlier Flickr OAuth grant was created on another trusted device.
- The bearer secret is exposed briefly to trusted endpoint memory and the
  current clipboard. This is explicit and bounded, not claimed to be secure
  memory erasure.
- A lost or mistyped value costs one revocation and replacement rather than a
  recovery or redisplay feature.
- The ceremony does not scale to public enrollment or unmanaged workstations;
  those scopes require a new independently authenticated onboarding decision.

## Alternatives considered

- **Short device or redemption code:** rejected for the private MVP because it
  adds an unauthenticated bearer endpoint, state, rate limiting, polling or
  redemption, expiry, collision, and ambiguous-completion recovery. If a later
  accepted onboarding decision reintroduces device linking, its hosted allocator
  must use the collision boundary in the private installation credential transfer
  contract: atomic create-if-absent, persistence-enforced live-code uniqueness,
  and bounded retry with an entirely fresh server-generated code, never overwrite.
- **Password-manager or encrypted-note relay:** rejected as the one supported
  ceremony because it deliberately creates another durable credential copy.
- **Email, chat, file, screenshot, QR image, cloud clipboard, or removable
  media:** rejected because each adds a persisted, synchronized, recorded, or
  independently readable copy outside the two trusted processes and
  `LrPasswords`.
- **Plug-in-launched browser callback:** rejected because the documented
  Lightroom SDK supplies no conventional native-app redirect/callback and the
  private flow does not need browser integration.
- **Manual transcription as the primary path:** rejected because the complete
  opaque value is deliberately high entropy and transcription is more
  error-prone than one local paste. It remains a no-persistence fallback when a
  trusted browser refuses clipboard write.
