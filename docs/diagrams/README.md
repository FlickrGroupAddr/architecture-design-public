# Architecture diagrams

Authority: Mixed. Under
[ADR 0041](../decisions/0041-use-clean-room-authentication-tabs-as-interaction-authority.md),
all three tabs in `clean-room-authentication-legal.drawio` are authoritative
happy-path interaction maps within their declared scope. They are necessary but
not sufficient: the controlling ADRs and contracts supply omitted requirements
and detail. Every other diagram is a derived visual. Apply the
[documentation authority hierarchy](../README.md) and the controlling ADRs and
contracts cited by each source.

- [`zero-state-publish-flow.puml`](zero-state-publish-flow.puml) visualizes the
  mixed-status zero-state flow.
- [`photo-group-add-state-machine.puml`](photo-group-add-state-machine.puml)
  visualizes the fail-polite intent state machine.
- [`system-architecture.drawio`](system-architecture.drawio) is the editable,
  uncompressed diagrams.net source for the private-MVP component walkthrough,
  one explicitly non-selected Google Cloud deployment candidate, and the
  safety-critical group-add path.
- [`clean-room-authentication-legal.drawio`](clean-room-authentication-legal.drawio)
  is the canonical legal-landscape source for the deliberately simplified,
  collaboratively rebuilt interaction memory map and its three tabs. Its first tab
  creates the Browser session for the normal FGA User UI; its second tab creates
  and transfers an FGA Plugin Code into the FGA LrC plug-in; its third tab
  starts with local Album creation, photo placement, and per-photo group
  selection before **Publish Now**, then renders and directly uploads one
  representative PNG, binds the returned Flickr photo, and hands selected group
  additions to the FGA API backend. Each tab restarts its local interaction
  numbering at step 1 so it remains independently readable; tab order carries
  the cross-page sequence. The companion page-one
  [`SVG`](clean-room-authentication-legal.svg) and page-two
  [`SVG`](clean-room-authentication-plugin-code-transfer-legal.svg), plus the
  page-three
  [`SVG`](clean-room-authentication-publish-png-groups-legal.svg), are ready to
  view or print. The native-4K
  [`drawio`](clean-room-authentication-4k.drawio), page-one
  [`SVG`](clean-room-authentication-4k.svg), and page-two
  [`SVG`](clean-room-authentication-plugin-code-transfer-4k.svg), and page-three
  [`SVG`](clean-room-authentication-publish-png-groups-4k.svg) files are generated
  derivatives.
  Run `uv run --frozen python scripts/build_clean_room_auth_diagram.py` after
  editing the Python model, or add `--check` to verify the committed outputs.

The tab-3 legend uses font size `13.25`, the largest value that fits its fixed
box at Terry's requested quarter-point precision. A pixel render at `13.5`
placed step 19 on the bottom border. Preserve `13.25` unless later content or
layout changes justify repeating the fit check; the regression suite pins the
accepted value.

The legal sheet is the real composition. The 16:9 native-4K sheet stretches
that same composition to fill a display. Do not add an 11 × 17 derivative
unless the high-level content can no longer remain legible on legal paper.
Terry's standing diagram preference, recorded 2026-08-30, is a `0.3 in` outer
content margin on all four page edges. Preserve that margin independently of
the internal component and container gutters.

## External glyphs

The embedded Google wordmark comes from Wikimedia Commons'
[`Google 2026 logo.svg`](https://commons.wikimedia.org/wiki/File:Google_2026_logo.svg).
Commons identifies Google LLC as the author and lists the image as public
domain. Google trademarks remain Google property; this derived architecture
visual uses the mark only to identify the external Google identity provider.

The embedded Browser glyph comes from Wikimedia Commons'
[`Google Chrome icon (February 2022).svg`](https://commons.wikimedia.org/wiki/File:Google_Chrome_icon_(February_2022).svg).
Commons identifies Google as the author and classifies the simple geometry as
public domain while separately flagging trademark restrictions. Chrome
trademarks remain Google property; the glyph identifies the Browser used in the
walkthrough and does not imply endorsement.

The embedded Lightroom Classic `LrC` mark reuses the hand-drawn vector from the
earlier [`FlickrGroupAddr-Architecture-2026-08-19-8.5x14.drawio`](https://github.com/FlickrGroupAddr/backend-api/blob/main/docs/architecture/FlickrGroupAddr-Architecture-2026-08-19-8.5x14.drawio)
diagram. It was drawn from the application icon rather than copied from an
Adobe-distributed asset, uses the Lightroom Classic colors `#001E36` and
`#31A8FF`, and identifies Lightroom Classic nominatively without implying Adobe
endorsement.

## Session-token semantics in the authentication diagram

The diagram projects the browser-authentication decision in
[ADR 0039](../decisions/0039-use-google-identity-services-browser-sessions.md)
and reuses the opaque-verifier construction accepted in
[ADR 0006](../decisions/0006-browser-free-private-installation.md): the FGA
Google Login Endpoint generates 256 independent random bits with its runtime or
operating system cryptographically secure random generator, sends only the
opaque token to the Browser, and stores the unsalted `SHA2-256` digest of the
complete token as the FGA database lookup key. The digest is a one-way verifier,
not encryption or obfuscation. A password KDF, per-token salt, or appended HMAC
would add machinery without material resistance to guessing a uniformly random
256-bit token; ADR 0006 records that rationale in full.

The FGA database maps the validated canonical Google issuer and `sub` to one
opaque internal `fgaUserId`. The FGA session database value is a purpose-built
record containing that `fgaUserId`, validated Google `sub`, only the profile
fields named FGA components actually need, and explicit FGA session metadata.
Email remains mutable display metadata and is never an ownership key. The
session record does not retain the complete decoded Google claim map or the
opaque token. The Browser receives the opaque value only in a
`__Host-` `Secure`, `HttpOnly`, `Path=/`, `SameSite=Strict` cookie with no `Domain`
attribute and `Max-Age=86400`. The server-side record has the same non-sliding
24-hour absolute expiry and no shorter idle timeout. This aligns with the
server-side session shape in the
[administrative control-plane contract](../administrative-control-plane-contract.md#server-side-administrative-session),
but the authoritative tab does not replace the accepted
[browser-session lifecycle contract](../browser-session-lifecycle.md) for
rotation, revocation, logout, cleanup, or incident response.

The Google JWT and CSRF checks named in the flow are load-bearing minimums, not
an exhaustive validation checklist. The authoritative sequence may omit but
never waive Google's current server-side validation requirements or the
maintained framework/library contracts selected for implementation.

The unnumbered asynchronous path on tab 1 is deliberately outside the login
request sequence. A hosted timer invokes the FGA JWKS refresh worker, which
retrieves Google's current public keys and atomically updates the shared FGA
Google JWKS cache. `maximum 6h` is the longest nominal interval between
scheduled refresh attempts; Google's published cache metadata can require an
earlier refresh, while failure invokes the bounded retry policy. Ordinary
logins therefore validate from the cache without upstream latency. After
admission and CSRF validation, a login naming an unknown signing key ID may wait
for one bounded, coalesced refresh and is rejected if current validation
authority still cannot be established. ADR 0039 owns those omitted failure,
retry, jitter, and single-flight details.

## Plugin Code semantics in tab 2

`Plugin Code` is the diagram's 2031-Terry-friendly name for the opaque FGA
installation credential accepted by
[ADR 0006](../decisions/0006-browser-free-private-installation.md). It is the
complete credential containing 256 independent server-generated random bits,
not a short pairing or redemption code. The FGA API backend stores only its
unsalted `SHA2-256` digest with the server-assigned `lrc_plugin` installation
record and returns the plaintext exactly once.

[ADR 0040](../decisions/0040-expose-plugin-codes-as-user-resources.md) controls
the component labeled **FGA Plugin Code API**. Its canonical collection is
`GET` and `POST /api/v001/plugin-codes`; terminal revocation is
`PATCH /api/v001/plugin-codes/{pluginCodeId}`. The GET is paginated from its
first release with bounded `page_size` and opaque `page_token` inputs. The
diagram shows `GET · POST · PATCH` on the component but numbers only the list
and creation interactions that belong to this transfer sequence.

The list flow resolves the opaque browser session to `fgaUserId`, queries only
that owner's bounded Plugin Code page, and durably appends a sanitized list-read
event before returning metadata. Creation writes the Plugin Code record and its
success event atomically. The separately drawn **FGA append-only audit log** is
the first-class `audit_events` relation in the same private-MVP FGA database,
not a separately deployed logging service. It records every Plugin Code
`GET`, `POST`, and `PATCH` outcome without session values, Plugin Code
plaintext/digests, Google assertions, Flickr credentials, or request bodies.

The authoritative second tab stops after the same-workstation transfer,
validation, documented `LrPasswords` storage, and transient-input clearing
described by the
[private installation credential transfer ceremony](../private-install-credential-transfer.md).
The subsequent `Authorization: Bearer ...` verification belongs on the next
tab. Accepted ADR 0043 and the browser-session lifecycle define the
transaction-bound recent Google reauthentication named on the create request;
the tab does not depict or independently amend that mechanism.

## Publish PNG and group-submission semantics in tab 3

Tab 3 is an authoritative happy-path interaction map under ADR 0041. It
projects the accepted split-auth direct-upload design from
[ADR 0005](../decisions/0005-service-signed-direct-upload.md), the
FGA LrC plug-in authentication boundary from
[ADR 0006](../decisions/0006-browser-free-private-installation.md), and the
add-only fail-polite group contract from
[ADR 0007](../decisions/0007-fail-polite-group-submissions.md).
The tab is necessary but not sufficient: those controlling ADRs and detailed
contracts supplement its deliberately simplified path, and an omission from the
tab never waives one of their requirements.

The page begins before the network path. The photographer chooses **Create
Album…**, which creates an empty local Album without a Flickr remote ID, and adds
one or more catalog photos. The FGA LrC plug-in retrieves the Plugin Code from
`LrPasswords`, attaches it as a Bearer credential to every FGA API backend
request, verifies the current active `lrc_plugin` installation, and loads the
bounded writable-group snapshot. The photographer records zero or more add-only
group selections per photo and chooses the Album's **Publish Now** action. The
Lightroom Classic publish-service runtime then supplies the pending photos.

After that Album-level dispatch, the page deliberately traces one representative
photo. The Lightroom Classic rendering engine produces the configured PNG. The
FGA LrC plug-in waits for the complete render and rejects a file that fails the
exact-size preflight before requesting upload authority.

Only allowlisted non-file metadata crosses into the FGA API backend. The FGA API
backend commits a fresh service-signed upload authorization and returns the
exact Flickr upload envelope with `Cache-Control: no-store`; the FGA LrC
plug-in keeps that envelope in memory and streams the rendered PNG directly to
the Flickr Upload API. Rendered image bytes never pass through the FGA API
backend. After Flickr returns a photo ID, the FGA LrC plug-in records its local
recovery evidence and Lightroom Classic catalog remote ID, then retries only
the safe photo-binding request. It never automatically replays an upload whose
outcome is unknown.

For a nonempty selected group set, the FGA LrC plug-in hands the verified photo
binding and expected revision to the FGA API backend. A `202` response means the
idempotent group intents are durably owned by the FGA backend; it does not mean
Flickr accepted any group addition. Before each individual add attempt, the FGA
group-submission worker obtains a fresh exact-photo membership observation. If
the photo is absent, it obtains and records fresh group-moderation state, marks
dispatch started durably, and begins `flickr.groups.pools.add` within 1,000 ms
of that moderation response. Existing membership, moderation queues, ambiguous
delivery, and other permanent safety outcomes follow the controlling add-only,
fail-polite contract. No FGA component removes a photo from a group or
automatically resubmits a possibly delivered add.

Zero selected groups is valid and skips steps 16–19, the durable group-intent
path. The local Album setup is shown, but remote Flickr Album materialization
and attachment progress independently under their controlling contracts and
remain omitted so the upload-to-group story stays readable. Multiple photos
repeat the post-dispatch one-photo flow independently; the tab does not
promise cross-photo ordering.

## Owner-approved DNS simplification

Date: 2026-08-28

Codex recommended showing the browser's operating-system/stub resolver and a
recursive resolver before authoritative DNS, and placing authoritative DNS in
a separate undecided DNS-provider boundary rather than inside the undecided FGA
backend-hosting boundary. The material objection was that a direct
Browser-to-authoritative-DNS arrow implies a direct protocol relationship, while
the shared hosting boundary implies a provider topology that has not been
selected. Those implications can mislead later troubleshooting, deployment, or
provider-replacement work if the interaction map is mistaken for a literal
protocol or deployment contract.

Terry explicitly overrode that recommendation. He spent multiple years on the
AWS Route 53 DNS team, understands the omitted resolver and provider layers, and
wants a simpler conceptual memory aid for 2031 Terry. The diagram therefore
uses bidirectional User-to-Browser and Browser-to-authoritative-DNS arrows and
places authoritative DNS inside the undecided FGA backend-hosting rectangle.
Terry knowingly accepted that the picture collapses the resolver chain, uses a
bidirectional arrow as a logical dependency rather than literal packet flow,
and groups DNS with hosted backend components without deciding that one provider
will operate both. Under ADR 0041, this relationship is authoritative only as a
simplified conceptual dependency. Protocol and deployment documents must not
infer a literal resolver path or shared-provider requirement from it.

The three authoritative tabs own their numbered happy-path interactions, named
actors and boundaries, ordering, and explicit invariants. They do not own exact
unshown URIs, payload schemas, error branches, lifecycle recovery, provider
selection, or other deliberately omitted detail. The controlling sources add
those requirements without contradicting the depicted paths. A mismatch is
resolved by determining the intended decision and updating the tab, controlling
detailed source, executable projections, and drift tests in the same change.
Keep the draw.io source uncompressed so its labels, relationships, and
architecture claims remain reviewable in Git.
