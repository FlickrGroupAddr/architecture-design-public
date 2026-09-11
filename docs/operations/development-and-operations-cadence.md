# FGA development and operations diligence cadence

Last updated: 2026-08-31

This is Future Terry's repeatable maintenance checklist. It turns release
events and calendar reminders into recorded evidence instead of depending on
memory. Event triggers take precedence over an assumed calendar: Lightroom
Classic major releases have historically arrived around October, but the full
major-release gate runs when Adobe actually ships one, whenever that occurs.

## Trigger summary

| Trigger | Required work |
| --- | --- |
| New production Lightroom Classic major release | Run the complete major-release gate below before treating the new LrC release as accepted for FGA |
| New production Lightroom Classic point release | Install it as required, run the point-release smoke gate, and escalate to the complete gate if any result changes or fails |
| New downloadable Lightroom Classic SDK | Review its release notes and relevant API documentation, update the local SDK, and run the code-quality and plug-in smoke gates |
| New production/stable Windows major release reaches the owner's adoption point | After the first major servicing/feature update has shaken out early defects, adopt it and run the complete major-release gate on the new sole Windows target |
| Initial FGA deployment | Run the complete TLS edge, health/diagnostic, route, and end-to-end staging-to-production acceptance gates |
| Edge provider, DNS, certificate, HTTPS, HSTS, proxy, load-balancer, asset routing, or network-policy change | Re-run the complete TLS edge gate and HTTP route-conformance gate before or immediately after the controlled change, as their rollback plans permit |
| FGA API, authentication, Flickr signing, upload, or queue behavior change | Run the affected contract, security, integration, and end-to-end tests before deployment |
| Quarterly while FGA is deployed | Run the quarterly operational gate below |
| Confirmed dependency, platform, certificate, or protocol security advisory affecting FGA | Assess promptly; patch and run the affected gates without waiting for the next scheduled review |

## Dedicated Lightroom diligence plug-in

Maintain a second development-only Lightroom plug-in named **FGA Diligence**.
It is separate from both the production publish provider and the focused FGA
Diagnostics experiments. Its purpose is to turn the Lightroom side of annual
compatibility and end-to-end acceptance into one explicit **Run FGA Diligence
Checks** command.

Terry's normal annual interaction is deliberately small:

1. Start the adopted Windows target and latest production Lightroom Classic.
2. Load or reload **FGA Diligence** if Lightroom has not already loaded it.
3. Click **Run FGA Diligence Checks** once and leave Lightroom running while
   Codex monitors and completes the external half of the gate.

The one command will eventually exercise the complete real chain, using a
deliberately admitted public fixture and designated low-impact Flickr test
destination:

1. Record sanitized Lightroom, SDK, plug-in, and Windows versions.
2. Confirm the plug-in can retrieve its scoped test credential from
   `LrPasswords` without recording the value.
3. Reach the strict FGA edge through `LrHttp` and complete authenticated API
   access.
4. Locate the admitted public fixture without requiring Terry to browse or
   select private catalog content.
5. Render the canonical PNG and publish its temporary artifact location for
   the external analyzer.
6. Have the external analyzer verify PNG structure, dimensions, bit depth,
   color profile, and decoded-pixel SHA2-256 against the accepted baseline.
   A whole-file SHA2-256 change by itself is not material because harmless
   container metadata can change. A decoded-pixel or structural change is
   retained for explicit review, not silently accepted.
7. Exercise direct Flickr upload, durable FGA intent acceptance, queue
   processing, the designated Flickr group submission, and the observable
   terminal result.
8. Retain the deliberately created Flickr photo and pool membership under the
   policy below, dispose of temporary local render artifacts after their
   required measurements and sanitized evidence are retained, and never touch
   catalog source data.

The designated destination is the owner-controlled, publicly visible,
invite-only [FlickrGroupAddr
Diligence](https://www.flickr.com/groups/14968939@N22/) group. Its pool is
unmoderated and accepts only Safe still images classified by Flickr as either
Photos/Videos or Illustration/Art/Animation/CGI. It has no group-specific
posting throttle and continues to count toward Flickr's ordinary per-photo
group limit. The FGA group-submission worker still performs the normal fresh
moderation preflight before every add; configuration of this controlled group
does not create a safety bypass.

Each invocation may create at most one new purpose-built synthetic public
photo. Retain every successfully uploaded photo and its pool membership
indefinitely as operational evidence. The FGA LrC plug-in, FGA API backend,
and FGA group-submission worker provide no cleanup, pool-removal, or Flickr-
photo-deletion action. If Terry ever chooses to remove retained evidence, he
does so deliberately through Flickr's UI, outside the diligence command and
outside FGA automation.

The service and production plug-in contract do not exist yet, so implementing
stubs now would produce a deceptive green button. Build each check alongside
the corresponding real component, and do not call the annual chain complete
until every required check is live. A missing component is a visible `blocked`
result, never an implicit pass.

The plug-in must not shell out to, reimplement, or bundle `testssl.sh`, Qualys
SSL Labs, or another general-purpose scanner. Codex or the external maintenance
harness runs the required assessments and any risk-selected diagnostics, then
joins their results with the Lightroom result.

Use `C:\Temp\FGA-diligence-status.json` as the stable Codex handoff. Each
published state is a complete JSON document staged through a temporary sibling
file and then used to replace the stable file. The minimum durable schema is:

```json
{
  "schema_version": 1,
  "state": "running | passed | failed | blocked",
  "started_at_utc": "RFC 3339 timestamp",
  "finished_at_utc": "RFC 3339 timestamp or null",
  "lightroom_version": "sanitized version/build",
  "windows_version": "sanitized version/build",
  "checks": [
    {
      "name": "stable_check_name",
      "state": "pending | running | passed | failed | blocked | skipped",
      "duration_ms": 0,
      "error_category": "sanitized category or null"
    }
  ]
}
```

At run start, replace any stale document with a new `running` document. Publish
complete updates as checks advance and finish with exactly one terminal state.
The monitor waits for a schema-valid document whose `started_at_utc` belongs to
the new run and whose top-level state is `passed`, `failed`, or `blocked`; a
filesystem write alone is not proof of success. Keep the file ephemeral and
outside Git. Never include credentials, OAuth headers, tokens, host or catalog
identifiers, private Flickr photo IDs, or unverified photo filenames, paths,
captions, locations, or other photo metadata.

## Annual Lightroom SDK call-zoo review

Keep the preceding major-version SDK locally when installing its successor.
Run the checked-in API inventory tool against both licensed SDK directories:

```powershell
uv run --frozen python scripts\compare_lightroom_sdk_api.py `
    --previous-sdk-root 'vendor\LrC SDK\15.3' `
    --current-sdk-root 'vendor\LrC SDK\16.0'
```

The script inventories every documented call name, signature, and opening
summary in `API Reference\modules`, compares the two releases, and writes the
full local report to `C:\Temp\FGA-lightroom-sdk-api-comparison.json`. The SDKs
and generated report remain outside Git. The console prints a small added,
removed, and changed-call summary rather than dumping the whole licensed SDK.

The words **documented call** are a hard support boundary. Do not supplement
the inventory with symbols found by probing Lightroom binaries or calling
importable but undocumented modules. In particular, `LrUUID` is not an FGA
dependency merely because it may exist at runtime. It becomes eligible for
review only if Adobe adds it to the published API Reference.

Codex must review every added, removed, signature-changed, and summary-changed
call. It must also re-evaluate these FGA assumptions against the new full SDK
documentation and release notes, even when the inventory diff is empty:

1. Is there now a documented CSPRNG, secure-random byte source, or suitable
   UUID generator that changes the Lightroom entropy boundary?
2. Did `LrHttp` add, change, or remove TLS-version controls, negotiated-
   protocol reporting, certificate behavior, timeout behavior, or HTTP calls?
3. Did `LrPasswords` add, change, or remove storage, retrieval, deletion,
   scoping, or entropy behavior?
4. Did publish-provider, export, render, rendition, catalog, or photo APIs
   change in a way that affects the production plug-in or diligence fixture?
5. Did Adobe add a boring supported primitive that should replace an FGA
   workaround or remove the reason for an existing exception?

The regex-derived security, transport, and publish/export review buckets in
the JSON report are navigation aids, not proof that unrelated calls are safe.
The script detects documented names, signatures, and opening summaries; Codex
still reads the complete relevant pages because deeper prose and behavioral
contracts can change without changing a signature.

## New Lightroom major-release gate

Run this gate for the actual new major release. October is a reminder to look,
not the source of truth.

1. Record the date, installed Lightroom Classic version and build, Camera Raw
   version, Windows edition/version/build, and newest Adobe-published
   Lightroom Classic SDK version. Do not infer one version from another.
2. Confirm that Lightroom Classic is the latest production release offered
   through Adobe Creative Cloud and is running on the latest production/stable
   Windows release adopted by the owner. Obtain the newest SDK through Adobe's
   authorized distribution. Update
   [Development environment](development-environment.md) when any recorded
   version or tool path changes.
3. Run the annual SDK call-zoo comparison against the preceding and new SDK,
   review every reported addition/removal/change, and complete its explicit
   assumption audit. Then review Adobe's release notes and full relevant SDK
   pages, paying particular attention to `LrHttp`, `LrPasswords`, publish-
   service APIs, export/render APIs, plug-in manifests, and Lua behavior.
4. Review FGA dependencies for supported versions, active maintenance,
   security advisories, and license changes. Upgrade deliberately and retain
   lockfile or pin changes in Git.
5. Run all repository static analysis, formatting checks, type checks, unit
   tests, contract tests, and PlantUML validation with the documented project
   commands.
6. Load **FGA Diligence** in the new Lightroom version, start the one-click
   diligence command, and have Codex monitor its sanitized JSON handoff through
   a terminal state. Confirm credential retrieval, outbound `LrHttp` behavior,
   rendering, and the applicable publish/export callbacks without exposing
   private photo data or secrets.
7. From that real LrC-on-Windows target, run an `LrHttp` HTTPS probe against
   the strict staging edge. The first attempt must use TLS 1.3-or-newer only.
   Record pass/fail and, when the edge exposes it, the negotiated TLS version
   and cipher suite. Do not claim Lightroom reports those values itself.
8. Run the complete core assessment in
   [FGA HTTPS-edge TLS deployment acceptance](tls-edge-acceptance.md): pinned
   `testssl.sh` with retained structured JSON and one fresh Qualys SSL Labs
   report. Bind both results to the real `LrHttp` probe, effective provider
   export, certificate generation, and exact deployed build using the evidence
   table below; do not record only an overall "passed." Add risk-selected
   diagnostics only when that contract's expansion triggers apply.
9. Run MDN HTTP Observatory and SecurityHeaders.com against the browser-facing
   control plane. Record these as HTTP-security-header results, not TLS grades.
10. Run the required HTTP route-conformance gate for the exact build through
    the real development topology and isolated provider preview. Confirm that
    its generated inventory and both router artifacts are bound to the result;
    no phase was skipped; `/api/v001/`, the exact FGA Google Login Endpoint,
    Flickr callback, assets, and the
    administrative shell all reached their expected owners. Prove the exact
    startup/liveness probes, truthful no-store `/api/debug` failure, dependency-
    free liveness, and Google-authenticated FGA-session-protected deployment resource against the
    same image and effective Cloud Run export. Then exercise the
    current administrative browsers through GIS sign-in, cookie/body
    `g_csrf_token` comparison, current Google ID-token validation and JWKS-cache
    proactive refresh, unknown-key coalescing, rotation/failure, exact `sub`
    allowlisting, 256-bit opaque session creation, `SHA2-256` lookup, minimized
    session persistence, and the strict host-only cookie's non-sliding 24-hour
    expiry. Exercise session rotation, the accepted transaction-bound recent
    Google reauthentication, post-login CSRF and exact-origin
    rejection, logout, the Flickr OAuth
    authorization/callback flow, one-time plug-in credential generation and
    same-workstation transfer, planned credential rotation, candidate expiry/
    cancellation, lost-completion recovery, lost-workstation revocation, and bounded
    audit read. Exercise FGA Google Login Endpoint source/deployment buckets,
    Flickr-callback source/deployment buckets and single-use state, limiter
    dependency failure, and sustained-saturation alert deduplication. Prove a
    refused or invalid Google login creates no session or unconditional JWKS
    refresh; unknown/consumed Flickr state causes no upstream exchange; no
    raw/derived source key enters audit/logs;
    no guessed device-start route creates state; and the initial numeric limits
    match the administrative contract. Prove that an installation credential
    cannot authenticate to the administrative namespace; a pending rotation
    candidate can read only `GET /api/v001/installations/current` until the
    administrator completes it; no ordinary `GET`
    mutates authorization/resource state; and an audit-write failure refuses its
    associated mutation. Restart Lightroom Classic after the server commits a
    rotation but before local current-key promotion and prove candidate-key
    recovery without re-enabling the old credential.
11. Exercise plug-in activation, authenticated FGA API access, direct Flickr
    upload, durable intent creation, queue processing, Flickr group submission,
    retry behavior, systemic Flickr write-gate pause and verified resume, and
    operator-visible terminal outcomes end to end. Prove that an account fault
    pauses only its linked user, a deployment fault prevents all new Flickr
    write starts, queued intents retain FIFO state, repeated observations do not
    page per partition, restart does not clear a pause, a failed or stale-
    revision repair check leaves the gate paused, and successful resume requires
    the expected NSID and `write` permission. Also prove that every retried
    mutating FGA API request preserves its exact idempotency identity and body,
    while a direct Flickr upload with no definitive result after
    `LrHttp.postMultipart` invocation enters `upload_outcome_unknown` without a
    second image POST. Exercise existing-public-photo intake with owner-fixed
    public/photo discovery, strict whole-page validation, page drift/failure,
    optional non-authoritative catalog hints, and fresh exact-photo proof.
    Prove wrong-owner, private, missing, malformed, and stale-link results create
    no binding revision; the common schema-version-2 group batch accepts no
    client Flickr photo ID; expired existing-photo proof creates no missing
    intent; and a fully idempotent retry remains a no-op. Inject concurrent
    handoffs, duplicate/lost wake hints,
    lease expiry, a fenced stale worker, and crashes before/after
    `dispatch_started`, POST handoff, Flickr response, and result commit. Prove
    the database due sweep recovers safe work, while every unresolved dispatched
    pair becomes terminally blocked without a second group-add POST. Exercise
    null, malformed, differently cased, retired, and future unknown stored
    credential classes; forward-version and rollback skew; and every
    class/route/method combination. Prove the default branch is `401
    invalid_token`, no unknown class reaches plug-in/browser/administrator
    authority, and the database rejects unrecognized class writes.
12. Run the
    [fail-polite worker/database conformance suite](../testing/fail-polite-worker-database-conformance.md)
    without targeting a volunteer-managed group. Require its complete stable-ID
    inventory and mutation evidence for the exact production worker artifact,
    migration head, and database engine. Verify that every add has its own
    fresh strict `getAllContexts` membership guard followed by a recorded
    `getInfo` preflight as that attempt's immediately preceding Flickr
    operation; a failed membership guard sends neither `getInfo` nor POST, a
    target-present observation terminalizes without a write, and a failed
    moderation preflight sends no POST; “photo added to the pool's pending queue”
    (code `6`) and “photo already in the pool's pending queue” (code `7`) create
    a permanent block; an observation reaching 1,000 milliseconds before POST
    dispatch is discarded and repeated; a preflight value of `0` followed by
    “photo added to the pool's pending queue” (code `6`) records the
    contradiction and still blocks; ambiguous post-
    dispatch recovery becomes terminal `delivery_uncertain`; repeated
    handoffs, process restarts, guessed retry/reopen actions, and routine retention emit
    no further add for a blocked pair; modified-client attempts cannot supply
    moderation state or clear/bypass a block; and unknown Flickr codes create
    a permanent `delivery_uncertain` block. Mutate `getAllContexts` fixtures
    through missing/null/object/scalar pool values, mixed or malformed entries,
    duplicate IDs, invalid `stat`, wrong media type, truncation, and budget
    overflow. Prove every case returns membership unavailable, commits no
    snapshot, exposes no partial/empty group list, disables add confirmation,
    and prevents the worker from continuing to `getInfo` or add; prove only a
    fully valid explicit empty pool array displays an empty current set. Prove
    the worker reserves membership GET, moderation GET, and possible POST
    capacity atomically before the membership guard.
    Also run the
    [courteous batch admission conformance contract](../testing/courteous-batch-admission-conformance.md)
    against the production FGA LrC plug-in adapter, FGA API backend, FGA
    database, route registry, and hint scheduler. Prove one official-client call
    carries the complete bounded group set, the FGA database commits every
    requested intent or none, the request path calls no Flickr method, and one
    batch emits at most one canonical post-commit hint. Prove an identical retry
    emits none, a lost hint converges through the due sweep, and plausible
    single-group routes remain server-owned `404`/`405` responses rather than
    handlers or static HTML.
13. Use only the owner-controlled FlickrGroupAddr Diligence group for the
    annual real group-add call. Never create recurring submissions to a
    third-party volunteer moderation queue merely to test FGA. Record the
    actual preflight observation and result, retain the synthetic photo and
    pool membership under the policy above, and never erase FGA's permanent
    block evidence.
14. Use only test data admitted under
    [Photography test-data handling](photography-data-handling.md). Do not put
    credentials, private Flickr identifiers, or unverified photography data in
    test evidence or Git.
15. Recheck Flickr's current official endpoint, authentication/signing,
    upload, group-pool, rate-limit, and error-response documentation for
    contract changes that affect FGA.
16. Compare every result with the preceding accepted major-release record.
    Investigate regressions and scanner disagreements. Do not relax the edge
    merely to preserve historical compatibility; any necessary exception must
    identify the failed real-client probe, the minimum relaxation, and its
    security consequence.
17. Create a dated project-log entry containing versions, result summaries,
    evidence locations, exceptions, and follow-up work. Commit the record and
    all resulting documentation, configuration, dependency, and test changes.

## TLS and HTTP evidence table

Copy this table into the dated major-release or edge-change record. Record
`not available` plus the reason; never silently omit a named assessment.

| Probe or assessment | Required result | Observed grade/status and material details |
| --- | --- | --- |
| Latest Creative Cloud LrC on the adopted latest production/stable Windows, using `LrHttp` | Pass against TLS 1.3-or-newer-only edge; otherwise a committed minimal exception | |
| Current administrative browsers | All required control-plane and Flickr OAuth flows pass | |
| Pinned `testssl.sh` | Complete reliable scan; TLS 1.3 only; expected strong effective policy, certificate, SNI, and address families; no unresolved vulnerability or material finding; retain raw structured JSON, exact command, version/artifact/output SHA2-256 values | |
| Fresh Qualys SSL Labs | Every reported endpoint completes at `A+` without a warning; inspect protocols, ciphers, certificate, forward secrecy, and simulations | |
| Certificate lifecycle | Issuance and applicable rollover/renewal/restore checks pass; an automatic renewal not yet naturally observed is labeled exactly `configured; not yet observed` | |
| Effective edge binding | Terraform plan/apply and provider export identify the same forwarding rule, target proxy, URL map, SSL policy, certificate, and immutable FGA web image exercised by the probes | |
| MDN HTTP Observatory | Record grade and resolve material browser-facing HTTP findings | |
| SecurityHeaders.com | Record grade and resolve material browser-facing HTTP-header findings | |
| Advertised address families | Equivalent acceptable results for each advertised IPv4/IPv6 family; provider export proves one global policy and any observed endpoint divergence blocks | |

For every row, also record the date, target hostname and address, tool/service
version when available, evidence location, and disposition of each material
finding. Scanner grades are useful summaries, not substitutes for reading the
detailed findings.

## Lightroom point-release smoke gate

The owner must remain on the latest production Lightroom release. After each
point release:

1. Record the new Lightroom Classic and Camera Raw versions.
2. Load **FGA Diligence** and run its sanitized diagnostic/smoke path while
   Codex monitors the JSON handoff through a terminal state.
3. Confirm plug-in credential retrieval, an authenticated FGA request, render,
   direct Flickr upload, intent creation, and queue visibility with approved
   test data.
4. Confirm the real `LrHttp` probe still reaches the strict FGA edge.
5. Run the full major-release gate if a smoke check fails, transport behavior
   changes, Adobe publishes a relevant SDK/API change, or the release notes
   identify a relevant security or compatibility change.
6. Record the result in the project log when it changes accepted behavior,
   creates an exception, or requires repository changes.

## Quarterly deployed-service gate

1. Run the complete core TLS and HTTP evidence table. Add diagnostics beyond
   `testssl.sh` and SSL Labs only when the TLS contract's incident, material-
   edge-change, or public-scope trigger applies.
2. Confirm certificate issuance, chain delivery, renewal configuration and
   observed status, expiry alerting, DNS, IPv4/IPv6 coverage, HSTS, and HTTPS-
   only routing. Run the rollover or restore drill when its specific trigger
   applies; do not mislabel configured-but-unobserved renewal as a pass.
3. Review dependency and platform advisories, supported runtime versions,
   provider change notices, and Flickr API announcements.
4. Test database backups and a documented restore path; prove permanent
   photo/group submission blocks survive backup, restore, and routine retention;
   inspect queue age, retry counts, moderation-preflight contradictions,
   delivery-uncertain outcomes, dead-letter/terminal outcomes, paused Flickr
   write gates and their append-only event history, failed repair checks, and
   alert delivery.
5. Review active plug-in credentials, administrative sessions, Flickr tokens,
   service secrets, and revocation paths. Revoke anything no longer required;
   rotate only according to documented policy or a concrete exposure/event.
   Confirm the Google client ID/audience, allowed origin, exact
   `/admin/google-login` URI,
   pinned administrator `sub`, session/CSRF configuration, 24-hour absolute
   expiry, administrative route allowlist, append-only audit retention, and—if
   Django and the Google Cloud candidate are selected—the exact signing-key
   version references, canonical 32-byte key validation, and zero/one-fallback
   state still match the applicable contracts. Prove invalid or inaccessible key
   material cannot produce a ready FGA API backend process and that the worker
   identity remains denied.
6. Confirm logs and retained evidence still exclude secrets and private photo
   data, and that retention remains proportionate.
7. If replacement has been accepted and any replacement operation exists,
   verify both retained bundles for every operation under the
   [backup and reverse-replacement contract](../replacement-backup-and-reverse-replacement.md).
   Report a failed or unreachable copy by opaque operation ID only, refuse any
   reverse replacement while degraded, and never delete a bundle as routine
   cleanup.
8. Record completion, deviations, owners, and due dates in a dated project-log
   entry. Commit any repository change made by the review.

## Definition of done

A diligence gate is complete only when its evidence is dated, attributable to
specific software and tool versions, checked for sensitive data, compared with
the prior accepted result, and committed or linked from the project log. A
green summary grade does not waive a detailed finding, and an unavailable
third-party scanner does not authorize weakening the edge.
