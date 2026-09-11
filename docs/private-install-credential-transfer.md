# Private installation credential transfer ceremony

Last updated: 2026-09-05

Status: Accepted private-MVP ceremony under ADRs 0018, 0040, 0041, and 0044

## Purpose and boundary

This contract defines the one supported private-MVP path for moving a newly
created FGA installation bearer credential, presented to Terry as a **Plugin
Code**, from the authenticated FGA User UI into the FGA LrC plug-in. The
plaintext may exist briefly in the FGA API backend response, the trusted
browser,
the current Windows clipboard, the plug-in's transient Plugin Code input, and
`LrPasswords`. It may not pass through a file, command line, URL, email, chat,
issue, terminal, log, trace, catalog, ordinary Lightroom preference, diagnostic
handoff, or cloud-synchronized clipboard.

Tab 2 of the
[clean-room authentication diagram](diagrams/clean-room-authentication-legal.drawio)
is the authoritative happy-path interaction map under
[ADR 0041](decisions/0041-use-clean-room-authentication-tabs-as-interaction-authority.md).
This ceremony adds the omitted endpoint preconditions, clipboard cleanup,
failure handling, and later Bearer verification without changing that sequence.

The ceremony is intentionally manual and same-workstation. Terry opens a clean
private-browsing window on the Windows workstation running Lightroom Classic,
authenticates to the allowlisted FGA User UI, copies the
one-time value, and immediately pastes it into the plug-in's transient Plugin
Code input. Before storing it, the browser and FGA LrC plug-in show the same
clear-text value simultaneously with identical fixed grouping and typography so
Terry can compare them side by side.
The FGA LrC plug-in does not open, automate, inspect, or receive cookies from
the browser. No device code, local callback listener, custom URI scheme,
temporary claim endpoint, polling protocol, password-manager record, removable
file, or cross-device message is introduced.

This is a private single-owner bootstrap, not a public onboarding design. The
eventual public or multi-user product must make a separate independently
authenticated pairing decision and satisfy the public abuse threat model.

## Why same-workstation paste

An empty plug-in has no credential and the Lightroom SDK documents no secure
random source that could establish a client-held half of a pairing protocol.
The accepted design already has one independently authenticated owner
and one server-generated 256-bit bearer credential. A same-workstation paste is
the smallest conventional bridge between those boundaries.

A short human code plus unauthenticated redemption would add another bearer
secret, endpoint, expiry store, admission limiter, ambiguous claim state, and
recovery protocol. A password manager or encrypted note would deliberately
persist the credential outside `LrPasswords`. Cross-device clipboard, email,
chat, and remote-control sessions add third-party synchronization or recording
boundaries. Manual transcription of the complete opaque value is permitted only
as recovery from a blocked local clipboard write while both trusted screens are
physically controlled by Terry; it is not the normal path and creates no
permission to photograph, print, or save the value.

The ceremony limits exposure; it cannot protect a compromised Windows account,
browser, Lightroom Classic process, plug-in, keyboard hook, clipboard reader,
screen recorder, or endpoint. Those are explicit endpoint-trust assumptions,
not risks a more elaborate server pairing dance would remove.

## Device-link collision boundary

The private MVP allocates no device code or user code, so it has no device-link
collision path. The legacy implementation's behavior of naming mutable state
with a human code and overwriting any state already at that name is not a
compatibility requirement.

If a later accepted onboarding decision introduces device linking, the hosted
component that allocates each code **MUST** generate it with an operating-system-
backed cryptographically secure random generator and commit the attempt with an
atomic create-if-absent operation. The persistence boundary **MUST** enforce the
human code's uniqueness for every live attempt. A collision **MUST NOT** read,
replace, extend, approve, or otherwise mutate the existing attempt; the allocator
generates an entirely fresh code and retries. Retries are bounded, and exhausting
the bound fails closed without returning a code or disclosing which value was
occupied. A check-then-create sequence does not satisfy this contract because two
allocators can both observe absence before either commits.

Those requirements record the minimum conventional integrity boundary; they do
not authorize a device-link endpoint, select its future storage technology, or
satisfy the separate public abuse threat model.

## Preconditions

Before generating a credential, Terry verifies all of the following:

- the Windows workstation is owner-controlled, fully updated, and not in an
  active remote-control, screen-sharing, screen-recording, presentation, or
  support session;
- Windows **Clipboard history** and **Sync across devices** are off, and no
  third-party clipboard manager is running;
- Lightroom Classic and the installed FGA LrC plug-in are the expected current
  versions, and the plug-in shows no stored credential;
- a supported browser private-browsing window has no extensions enabled beyond
  explicitly reviewed accessibility or security tooling;
- the address bar shows exactly `https://flickrgroupaddr.com/admin/` with a
  valid HTTPS connection, not a link supplied through email or chat;
- Terry's pinned Google `sub` is present in a valid Google-authenticated FGA
  session, and accepted ADR 0043's five-minute recent Google reauthentication
  for this sensitive operation has succeeded; and
- no observer or camera can see the administrative or plug-in window.

If any precondition is false, the FGA Plugin Code API does not create
the installation identity. The browser page presents this short checklist
before enabling **Create Plugin Code**. It cannot technically
attest the workstation state, so the checkboxes are an operator ceremony and
their completion time—not secret values—enters the administrative audit event.

Part 1 Flickr authorization may still occur on any trusted owner-controlled
device. Part 2 credential generation must use the target Lightroom workstation
for this same-workstation transfer. Opening the FGA User UI there
does not make the browser part of plug-in activation: the plug-in neither
launches nor communicates with it.

## Creation response and transfer view

The authenticated browser submits
`POST /api/v001/plugin-codes` with the FGA browser session cookie,
exact-origin and synchronizer-CSRF controls, accepted recent Google
reauthentication proof,
supported schema version, an operator-entered non-secret installation label,
and confirmation of the precondition checklist. The browser cannot provide a
credential, class, user ID, permission, expiry override, or post-creation
redirect.

The FGA API backend creates the installation exactly as specified by ADR 0006,
[ADR 0044](decisions/0044-use-canonical-crockford-base32-plugin-codes.md), and
the administrative control-plane contract: 32 random octets from the hosted
runtime or operating-system cryptographically secure generator, one canonical
Plugin Code, an unsalted SHA2-256 digest of that complete canonical text,
server-assigned class `lrc_plugin`, and one active installation/audit
transaction. The plaintext is returned only in that successful response.

The response and every transfer-view asset use HTTPS and `Cache-Control:
no-store`; the response also uses `Pragma: no-cache` for conservative legacy
intermediaries. The secret is JSON response data, never a URL, query, fragment,
redirect, cookie, HTML source literal, or server-rendered page. The FGA HTTPS
edge and FGA API backend redact the complete `Authorization` field and the
credential field by structured field name before access logging, tracing,
exception reporting, analytics, and support diagnostics. Request and response
bodies for this route are not captured.

The FGA User UI page has no analytics, advertising, third-party script,
service worker, form submission, print control, download control, or secret-
echo endpoint. Existing same-origin CSP, no-store, no-referrer, and no-frame
controls apply. Client code holds the response only in one in-memory transfer
view and renders a clear-text, read-only, non-form control with
`autocomplete="off"`, a one-time **Copy Plugin Code** button, and an explicit
**Erase transfer view** button. It never writes the value to browser storage,
IndexedDB, a URL/history entry, crash telemetry, console output, or form state.

## Canonical Plugin Code format

The FGA API backend encodes exactly 32 random octets with the canonical
Crockford Base32 alphabet `0123456789ABCDEFGHJKMNPQRSTVWXYZ`. It interprets the
octets as one left-to-right bit string, appends four zero bits after the final
random bit, emits 52 uppercase symbols, and inserts an ASCII hyphen after every
four symbols. The resulting Plugin Code has 13 four-symbol groups, 12 hyphens,
and 64 characters total. Its final symbol is necessarily `0` or `G`; the format
adds no checksum.

The only accepted spelling matches this complete regular expression:

```regex
^[0-9A-HJKMNP-TV-Z]{4}(?:-[0-9A-HJKMNP-TV-Z]{4}){11}-[0-9A-HJKMNP-TV-Z]{3}[0G]$
```

The hyphens are part of the credential value sent in the Bearer header and
included in the SHA2-256 digest. The FGA LrC plug-in accepts no lowercase,
aliases, surrounding whitespace, alternate hyphen placement, missing hyphens,
or re-encoding. In particular it does not apply Crockford's optional permissive
decoder mappings for `I`, `L`, or `O`. The exact spelling is also valid in RFC
6750's `b64token` grammar without another encoding pass.

Both transfer surfaces render this exact value in the same monospace font,
size, weight, four-character grouping, and slashed-zero treatment. The browser
view and transient plug-in input remain simultaneously visible until Terry has
compared them and invoked **Store and verify**. Visual comparison helps catch a
clipboard or focus mistake; it is not authentication or a checksum.

The transfer view expires and erases its UI reference after five minutes, on
logout, on navigation, or when Terry presses **Erase transfer view**. JavaScript
variable clearing and garbage collection are best effort, not secure memory
erasure; the trusted-browser-process assumption remains explicit. Reload/back
does not redisplay the value. If the view is lost before successful activation,
the installation identity is revoked and a new one is created; no component
reconstructs the plaintext.

## Exact operator and component sequence

1. Terry confirms the FGA LrC plug-in is installed and disconnected. If
   Lightroom Classic is already open, the plug-in displays the exact
   FGA User UI URL as selectable non-secret text and an empty transient Plugin
   Code input. It does not launch a browser or append state to the URL.
2. Terry opens the clean private-browsing window manually, types or uses a
   trusted local bookmark for `https://flickrgroupaddr.com/admin/`, and
   authenticates through Google Identity Services and the FGA Google Login
   Endpoint.
3. Terry selects the target installation label, reviews the transfer
   checklist, and invokes **Create Plugin Code** once.
4. The FGA API backend commits the active installation, credential digest, and
   audit event before returning the plaintext once. A lost or ambiguous create
   response is never repeated under the same request to redisplay a value.
5. Terry selects **Copy Plugin Code**. The page calls the standards-based
   browser clipboard write API only from that user gesture and reports success
   or failure without echoing the credential. Clipboard-read permission is not
   requested.
6. Without using any intervening application, Terry focuses or launches
   Lightroom Classic, pastes once into the FGA LrC plug-in's transient Plugin
   Code input, compares the two simultaneous clear-text renderings, and invokes
   **Store and verify** only when they match exactly. Paste is the only clipboard
   operation initiated by the FGA LrC plug-in; its code invokes no clipboard API.
7. The plug-in performs strict local syntax/length validation without logging
   or transforming the value, including the required final-symbol pad-bit
   constraint. On a syntactically valid value it immediately
   calls documented `LrPasswords.store` under the FGA LrC plug-in ID and fixed
   key.
   It then replaces the bound UI string with an empty string and drops other
   Lua references before any network request.
8. The plug-in retrieves the value from `LrPasswords` and reads
   `GET /api/v001/installations/current` with HTTPS Bearer authentication and
   no body or query. Only `200 OK` plus the exact active-installation
   representation and `presentedCredentialState: "current"` marks the initial
   installation connected. The response and plug-in UI contain no credential,
   digest, credential class, FGA user, or Flickr identity.
9. After the plug-in shows **Connected**, Terry returns directly to the
   FGA User UI page and presses **Erase transfer view**. In that same user
   gesture, the page overwrites the current clipboard with a fixed non-secret
   sentence and erases the rendered value. If browser clipboard write is
   refused, the page tells Terry to copy that displayed non-secret sentence
   manually; it never reads back the clipboard to “verify” erasure.
10. Terry closes the entire private-browsing window, confirms Windows clipboard
    history remains off, and returns to Lightroom Classic. The ceremony is
    complete only after the successful current-installation read and
    clipboard/view cleanup.

The clipboard contains the bearer secret only between steps 5 and 9. No later
step asks Terry to paste it elsewhere. The fixed overwrite cannot prove bytes
were scrubbed from RAM, browser crash storage, or a malicious clipboard reader;
it removes the ordinary current-clipboard value under the stated clean-endpoint
assumption.

## Failure and recovery

| Failure | Required handling |
| --- | --- |
| Plugin Code create is rejected before commit | No identity or plaintext exists; correct the non-secret problem and retry |
| Database/audit commit outcome is unknown or response is lost | Do not retry for redisplay; use the FGA User UI's Plugin Code list to revoke the possibly created record, then create a new one |
| Clipboard write is refused before the value leaves the view | Terry may manually transcribe directly between the two visible trusted windows or revoke and retry; do not use a file, password manager, chat, screenshot, or cloud clipboard |
| Transfer view expires, reloads, navigates, crashes, or closes before activation | Revoke that installation identity and create a new one |
| Plug-in syntax check fails | Clear the field and clipboard/view, revoke the unused identity, and create a new credential; do not normalize, trim, or guess the intended value |
| `LrPasswords.store` fails or retrieval does not exactly match | Clear transient references, leave the plug-in disconnected, revoke the identity, and diagnose the local secure-store failure without logging the value |
| Current-installation read returns `401 invalid_token` | Overwrite the fixed key with an empty string using documented `LrPasswords.store`, verify retrieval is empty, clear transient state, revoke the displayed installation identity, and create a new one; the SDK 15.3 reference documents no delete operation, and no oracle says whether transfer or server state was wrong |
| Current-installation read returns a transport error or `5xx` | Keep the credential only in `LrPasswords`, clear clipboard/view, and remain not-yet-verified; a later **Verify stored credential** repeats only the safe GET without redisplaying or re-pasting the secret |
| Current-installation read returns `403` | Keep no connected state, clear clipboard/view, and require administrative repair; a pending rotation candidate is valid only in the planned-rotation flow, and no other authority mismatch is accepted |
| Clipboard cleanup cannot be completed | Close the transfer view, revoke the installation, and treat the workstation as unsuitable until the clipboard/endpoint condition is corrected |

`GET /api/v001/plugin-codes` lists bounded pages of the newly created opaque
`pluginCodeId`, label, creation time, active/revoked status, and sanitized
last-authenticated time. It accepts optional `page_size` and opaque
`page_token`; the response returns `pluginCodes` and an optional
`nextPageToken`. It never displays the digest, internal credential class, or
plaintext. This lets Terry select the exact unused or failed record for
revocation without relying on a secret value.

The [installation credential lifecycle](installation-credential-lifecycle.md)
owns rotation, compromised-workstation, and lost-workstation recovery after
successful activation. Nothing in this transfer procedure
authorizes two active credentials for one installation, recovers plaintext, or
turns a copied credential into a refreshable session.

## Conformance requirements

Before private-MVP release, automated tests and one controlled Windows/Lightroom
diligence run must prove:

- the create route requires the exact FGA browser session, CSRF, origin,
  recent authentication, fixed credential class, and one committed audit event;
- the credential appears only in the one successful response and cannot be
  recovered by reload, back, GET, list, audit, or repeated idempotency request;
- generation from 32 random octets produces only the canonical 64-character
  grouped format, preserves all 256 random bits, and rejects every noncanonical
  spelling without normalization or repair;
- the browser view and transient FGA LrC plug-in input show the same clear-text
  canary simultaneously with identical grouping and typography before storage;
- access/error logs, traces, metrics, browser console/storage/history/cache,
  diagnostic handoffs, Lightroom preferences, catalog fields, and plug-in logs
  contain a canary credential in none of their captured values;
- the plug-in's UI binding is transient, stores through `LrPasswords`, clears
  before the current-installation read, and uses only the
  fixed Bearer header over HTTPS;
- a clipboard-write failure, secure-store failure, invalid token, transient
  server failure, lost create response, expired view, and cleanup failure each
  produce the exact non-secret recovery above;
- no device-start, claim, redemption, polling, local callback, custom scheme,
  credential download, QR, or secret-bearing URL route exists; and
- the same-workstation private-window procedure works on the supported Windows
  and Lightroom Classic versions with Clipboard history and sync off.

Test automation may inject a canary into instrumented local components, but no
real credential enters test logs or artifacts. Diligence evidence records only
component versions, opaque installation ID, result, and sanitized correlation
IDs.

## References

- [ADR 0006 — Browser-free private installation](decisions/0006-browser-free-private-installation.md)
- [Private-MVP administrative control plane](administrative-control-plane-contract.md)
- [Adobe Lightroom SDK research: `LrPasswords`](research/lightroom-classic.md#upload-and-credential-primitives)
- [RFC 6750 — Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750)
