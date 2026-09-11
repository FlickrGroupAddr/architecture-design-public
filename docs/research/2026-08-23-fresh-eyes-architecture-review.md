# Fresh-eyes architecture review

Status: **complete — independent assessment, full comparison, reconciliation,
and ticket handoff complete**

Date: 2026-08-23

## Scope and provenance

This review resumes FGA architecture work from durable state while treating chat
history as nonexistent. The review baseline is clean `main` commit `d362a1a`
(`Allow board-specific localswim monitor alerts`), which is commit 105 in the
repository's first-parent-independent commit count. The inventory below is the
complete output domain of `git ls-files` at that baseline: 76 tracked files.

The authoritative FGA localswim board identifies ticket `#0012`,
`claude-repository-review`, as the relevant handoff. At recovery time it was P1,
owned by `bot`, and in `ready_for_review`. That is a sanitized coordination
conclusion; private board prose is not reproduced here.

The working method is intentionally ordered:

1. read the current FGA design, evidence, operations material, and implementation;
2. write an independent assessment from those sources;
3. only then read the earlier high-level-diagram comments and Claude comparison;
4. reconcile every earlier point against the independent assessment and repository
   evidence;
5. close this ledger only when every tracked file and every identified external
   Claude design artifact has an explicit coverage disposition.

`Complete` means the file was read from beginning to end. `Inspected` means an
implementation, generated dependency lock, or vendored artifact was examined to
the depth stated in the final ledger; these files do not carry the complete-read
requirement that applies to project documentation. `Pending` means no review
claim is yet made.

External-repository citations below use the form
FlickrGroupAddr/backend-api@ea40755:path:line-range. They identify the pinned
source reviewed on 2026-08-23 without depending on the transient checkout. The
repository history was rewritten for privacy on 2026-08-24; the byte-identical
successor for every unaffected current-tree blob is backend-api commit
`26b7070cb1092bb9fbac045ddd845884f6aa9ea4`. Citations to removed artifacts are
archival review provenance and intentionally no longer resolve. Short commit
IDs identified as backend-api commits refer to that external repository; all
other commit IDs refer to this repository.

## Coverage ledger

### Recovery and coordination

- [x] Complete — `AGENTS.md`
- [x] Complete — `scripts/watch_localswim.py`
- [x] Inspected — all 105 Git commit subjects, authors, dates, and order
- [x] Inspected — clean worktree and complete `git ls-files` inventory
- [x] Inspected through `localswim-cli` — FGA board summary and ticket `#0012`
- [x] Verified — healthy detached FGA and inception services with `push.state=ok`
- [x] Verified — detached board-specific monitors target the active Codex thread

### Batch 1 — independent documentation and evidence

- [x] Complete — `README.md`
- [x] Complete — `LICENSE`
- [x] Complete — `THIRD_PARTY_NOTICES.md`
- [x] Complete — `docs/architecture.md`
- [x] Complete — `docs/decisions/0001-clean-room-publish-provider.md`
- [x] Complete — `docs/decisions/0002-lossless-png-output.md`
- [x] Complete — `docs/decisions/0003-mit-license-boundary.md`
- [x] Complete — `docs/decisions/0004-single-user-mvp.md`
- [x] Complete — `docs/decisions/0005-service-signed-direct-upload.md`
- [x] Complete — `docs/decisions/0006-browser-free-private-installation.md`
- [x] Complete — `docs/decisions/0007-fail-polite-group-submissions.md`
- [x] Complete — `docs/decisions/README.md`
- [x] Complete — `docs/diagrams/photo-group-add-state-machine.puml`
- [x] Complete — `docs/diagrams/zero-state-publish-flow.puml`
- [x] Complete — `docs/future-terry-faq.md`
- [x] Complete — `docs/open-questions.md`
- [x] Complete — `docs/operations/development-and-operations-cadence.md`
- [x] Complete — `docs/operations/development-environment.md`
- [x] Complete — `docs/operations/flickr-roundtrip.md`
- [x] Complete — `docs/operations/photography-data-handling.md`
- [x] Complete — `docs/operations/tls-edge-acceptance.md`
- [x] Complete — `docs/plugin-service-contract.md`
- [x] Complete — `docs/project-log/2026-08-20-flickr-roundtrip-harness.md`
- [x] Complete — `docs/project-log/2026-08-20-flickr-roundtrip-results.md`
- [x] Complete — `docs/project-log/2026-08-20-flickr-upload-signing-probe.md`
- [x] Complete — `docs/project-log/2026-08-20-inception.md`
- [x] Complete — `docs/project-log/2026-08-20-lightroom-diagnostic.md`
- [x] Complete — `docs/project-log/2026-08-20-png-matrix-results.md`
- [x] Complete — `docs/project-log/2026-08-20-production-catalog-flickr-state.md`
- [x] Complete — `docs/project-log/2026-08-20-raw-archive-survey.md`
- [x] Complete — `docs/project-log/2026-08-20-session-closeout.md`
- [x] Complete — `docs/project-log/2026-08-22-session-closeout.md`
- [x] Complete — `docs/project-log/README.md`
- [x] Complete — `docs/research/flickr.md`
- [x] Complete — `docs/research/lightroom-classic.md`
- [x] Complete — `docs/research/png-experiment.md`
- [x] Complete — `docs/research/upload-signing-boundary.md`
- [x] Complete — `docs/vision-and-scope.md`
- [x] Complete — `docs/zero-state-publish-flow.md`
- [x] Complete — `lightroom/FGA Diagnostics.lrdevplugin/README.md`
- [x] Complete — `lightroom/FGA Diagnostics.lrdevplugin/vendor/README.md`
- [x] Complete — `vendor/LrC SDK/README.md`

### Batch 2 — implementation, schema, configuration, tests, and history

- [x] Complete — `.gitignore`
- [x] Complete — `.luacheckrc`
- [x] Complete — `.luarc.json`
- [x] Complete — `.python-version`
- [x] Complete — `config/flickr.example.json`
- [x] Complete — `lightroom/FGA Diagnostics.lrdevplugin/DirectUploadProbe.lua`
- [x] Complete — `lightroom/FGA Diagnostics.lrdevplugin/Info.lua`
- [x] Complete — `lightroom/FGA Diagnostics.lrdevplugin/PngMatrix.lua`
- [x] Complete — `lightroom/FGA Diagnostics.lrdevplugin/RunDirectUploadProbe.lua`
- [x] Complete — `lightroom/FGA Diagnostics.lrdevplugin/RunPngMatrix.lua`
- [x] Inspected — `lightroom/FGA Diagnostics.lrdevplugin/dkjson.lua`; verified the
  vendored 2.11 header, license disposition, 812-line extent, and SHA2-256 digest
  against the tracked vendor notice rather than re-reviewing upstream serializer
  internals as FGA architecture
- [x] Complete — `pyproject.toml`
- [x] Complete — `scripts/__init__.py`
- [x] Complete — `scripts/analyze_png_exports.py`
- [x] Complete — `scripts/check_lua.py`
- [x] Complete — `scripts/check_python.py`
- [x] Complete — `scripts/compare_lightroom_sdk_api.py`
- [x] Complete — `scripts/flickr-roundtrip.py`
- [x] Complete — `scripts/flickr-signed-upload-probe.py`
- [x] Complete — `scripts/flickr-signing-probe-server.py`
- [x] Complete — `scripts/flickr_support.py`
- [x] Complete — `scripts/flickr_upload_signing.py`
- [x] Complete — `tests/__init__.py`
- [x] Complete — `tests/test_analyze_png_exports.py`
- [x] Complete — `tests/test_compare_lightroom_sdk_api.py`
- [x] Complete — `tests/test_flickr_upload_signing.py`
- [x] Complete — `tests/test_watch_localswim.py`
- [x] Inspected — `uv.lock`; verified the complete package/version/source/hash
  inventory and the generated lock's Python constraint
- [x] Inspected — all 105 baseline commits at subject/author/date/order level and
  the complete reverse path-level change history; targeted line-level attribution
  remains part of final citation work

### Batch 3 — deliberately deferred comparison material

- [x] Complete — `docs/project-log/2026-08-23-claude-architecture-diagram-reveal.md`
- [x] Complete — `docs/project-log/2026-08-23-clean-room-comparison-provenance.md`
- [x] Complete — `docs/project-log/2026-08-23-session-closeout.md`
- [x] Complete — `docs/research/claude-design-repository-review.md`
- [x] Complete — all 50 documentation/design paths in the pinned original Claude
  repository; the exact file-by-file inventory and architecture-relevant
  disposition of all 102 remaining tracked paths are recorded in
  `docs/research/2026-08-23-claude-repository-coverage-ledger.md`
- [x] Inspected — all three original Draw.io encodings, including XML labels,
  endpoints, geometry, and style; all three have 90 cells, 58 labeled cells, and
  20 edges
- [x] Visually inspected — the original 8.5-by-14 PNG rendering
- [x] Reverified — the three supplied-artifact SHA2-256 digests recorded in
  `docs/project-log/2026-08-23-claude-architecture-diagram-reveal.md`; the canonical
  Draw.io copy remains byte-identical to the supplied source
- [x] Complete — architecture-relevant inspection of the pinned external
  repository's implementation, six migrations, configuration, browser client,
  tests, tooling, generated artifacts, and all 473 Git commits; critical
  correctness and security paths received complete reads and targeted blame

### Review document itself

- [x] Complete — `docs/research/2026-08-23-fresh-eyes-architecture-review.md`
- [x] Complete —
  `docs/research/2026-08-23-claude-repository-coverage-ledger.md`

## Current recovered state

The repository is documentation- and experiment-led. Its tracked implementation is
a set of Lightroom Classic diagnostic plug-ins, Flickr/PNG research harnesses, and
repository validation/coordination scripts; the production FGA LrC plug-in, FGA API
backend, FGA workers, database migrations, and deployment configuration do not yet
exist here. This inventory observation anchors the conclusions below.

The zero-state publish flow had already completed eight owner-reviewed phases before
the Claude comparison handoff. At the independent-assessment checkpoint no comparison
conclusion was adopted; the frozen assessment below preserves that ordering, and the
later sections complete the comparison.

## Independent assessment frozen before comparison

This section records the assessment formed from completed Batches 1 and 2 before the
Batch 3 comparison documents or pinned Claude repository were read as review inputs.
It deliberately does not claim that earlier reviewers did or did not identify the
same points. `Fact` below means the statement is directly supported by the cited
repository material. `Inference` means the architectural consequence is this
reviewer's judgment from those facts.

### Recovered architecture and implementation state

| ID | Kind | Independent finding and evidence |
| --- | --- | --- |
| I-01 | Fact | This remains an architecture-and-research repository. The production publish provider and hosted service are explicitly not implemented (`README.md:24`), and the tracked inventory contains no production service source, database migration, deployment manifest, or machine-readable API schema. The executable material consists of diagnostic Lightroom plug-ins, bounded research/probe scripts, tests for those scripts, and the board monitor. |
| I-02 | Fact | The accepted design is a private single-user MVP (`docs/decisions/0004-single-user-mvp.md:1-5`) with a clean-room FGA LrC plug-in, direct signed Flickr upload, a Lightroom-local recovery outbox, durable hosted group intents, per-user/group FIFO partitions, fresh fail-polite moderation preflight, add-only membership behavior, and permanent exact-pair suppression for uncertain or moderated submissions (`docs/architecture.md:47-99`, `docs/architecture.md:109-138`, `docs/architecture.md:167-260`). |
| I-03 | Fact | The repository's probes support, but do not implement, the accepted PNG and upload-boundary decisions. The current docs distinguish the diagnostic code from a production provider (`docs/operations/development-and-operations-cadence.md:28-30`), while the upload and PNG ADRs record the accepted evidence (`docs/decisions/0002-lossless-png-output.md:5`, `docs/decisions/0005-service-signed-direct-upload.md:5`). |
| I-04 | Fact | The prose contract is accepted architecture but has not been encoded as OpenAPI (`docs/plugin-service-contract.md:3-8`). Consequently there is no implementation, migration, or conformance test against which most hosted semantics can yet be judged. Any statement that the production repository agrees with the design would overclaim the evidence. |
| I-05 | Inference | The strongest part of the design is its treatment of irreversible or socially costly Flickr writes: image bytes do not traverse the FGA API backend; the FGA group-submission worker must freshly preflight every add; uncertain delivery permanently suppresses automatic repeat; and Flickr remains authoritative for observed membership. These are proportionate security and moderator-protection boundaries, not optional UI behavior (`docs/architecture.md:167-260`, `docs/decisions/0007-fail-polite-group-submissions.md:75-199`). |

### Required boring-and-obvious pushback

| ID | Kind | Independent finding, consequence, and conventional alternative |
| --- | --- | --- |
| I-06 | Inference requiring owner checkpoint | Group discovery uses an asynchronous refresh state machine whose work items each fetch exactly one Flickr page, builds immutable generations, and allocates server-stored random 256-bit continuation handles with expiry, binding, budgets, and garbage collection (`docs/zero-state-publish-flow.md:342-410`; `docs/plugin-service-contract.md:321-389`). The same stateful-handle machinery paginates a complete `getAllContexts` response (`docs/plugin-service-contract.md:396-465`). For a private single-user MVP this is speculative infrastructure with tables, recovery, cleanup, observability, and test burden disproportionate to the data. The boring default is one bounded refresh job that walks upstream pages within explicit count/time/row limits and atomically replaces a compact snapshot, plus either one bounded response or conventional stateless/keyset paging over stored rows. This review pushes back on implementing the accepted mechanism without Terry explicitly choosing that complexity after this objection. |
| I-07 | Inference requiring owner checkpoint | `/api/v001/flickr-api-proxy/` says “proxy,” but the contract itself describes snapshot reads, split direct-upload authorization, and asynchronous durable intent creation rather than transparent proxying (`docs/plugin-service-contract.md:233-242`). Resource-oriented routes such as `/groups`, `/photos/{id}/group-memberships`, `/upload-authorizations`, and `/submission-batches` are more conventional and leave internal Flickr integration replaceable. Keeping the current name creates permanent coupling and incorrect operator/client expectations. |
| I-08 | Inference requiring owner checkpoint | `GET /auth/device/token-check?device_type=lrc15_plugin` is neither a device authorization flow nor naturally a version-specific operation, and the project targets only the latest Lightroom Classic release (`docs/decisions/0006-browser-free-private-installation.md:41-66`; `docs/zero-state-publish-flow.md:239-290`). A conventional version-independent `/auth/credential-check` or `/installations/current` resource is less surprising; capabilities should be negotiated only when a concrete second profile exists. The accepted ADR records the chosen spelling but not this least-surprise objection. |
| I-09 | Inference requiring owner checkpoint | The deployment gate calls for a broad recurring external-scanner matrix in addition to a real `LrHttp` probe (`docs/operations/tls-edge-acceptance.md:16-64`, `docs/operations/development-and-operations-cadence.md:159-241`). For a private single-user MVP, maintaining six-to-eight third-party scanner dependencies risks turning security verification into a flaky ritual. A conventional risk-based gate is the real client probe, one strong local scanner, one independent hosted scanner, plus certificate-renewal and restore checks; expand the matrix for public operation, an incident, or a material edge change. This is pushback on scope, not on the TLS requirement. |

### Newly found correctness, lifecycle, and contract gaps

| ID | Kind | Independent finding and evidence |
| --- | --- | --- |
| I-10 | Resolved by owner decision on 2026-08-23 | Terry accepted that multi-photo publishing **MUST** be eventually consistent, not atomic or ordered: every requested photo has to keep progressing or reach a durable truthful outcome, while relative order is immaterial. Per-group FIFO begins only at durable intent insertion and remains an internal worker invariant, not a cross-photo publication-order promise. ADR 0009 supersedes the earlier fixed-order language. |
| I-11 | Inference requiring owner judgment | The FGA LrC plug-in writes Flickr's photo ID into the Lightroom Classic catalog before the Phase 6 hosted transaction (`docs/zero-state-publish-flow.md:587-599`), while the accepted success invariant says FGA policy does not classify the image as successfully “in Flickr” until the FGA API backend verifies ownership and commits that proof (`docs/zero-state-publish-flow.md:870-882`). The local outbox protects eventual handoff, but the user-visible meaning and repair behavior for “remote ID present, hosted proof absent” are not specified. |
| I-12 | Fact and risk inference | Upload delivery ambiguity is explicitly left for later reconciliation UX (`docs/zero-state-publish-flow.md:915-918`; `docs/plugin-service-contract.md:587-595`, `docs/plugin-service-contract.md:961-962`). Because blind replay can duplicate an image, this is an implementation-blocking product and recovery decision, not optional polish. |
| I-13 | Resolved by accepted ADR 0013; Terry accepted the decision on 2026-08-26 | Systemic Flickr authentication/configuration failures were classified per intent as terminal `needs_attention`, which could consume many partition heads. Ticket #0022 now defines durable linked-user and deployment write gates, immediate trip on definitive scoped results, deduplicated alerting, unchanged queued FIFO state, and explicit compare-and-set resume after a non-mutating OAuth token/permission check. Post-dispatch intent safety remains unchanged. See `docs/decisions/0013-durable-flickr-write-circuit-breaker.md`. |
| I-14 | Resolved by owner decision on 2026-08-25 | Terry accepted zero-group publication. Flickr publication and required album attachment are core photo outcomes; group additions are optional intents. A zero-group photo does not block a batch or create queue work, and the FGA LrC plug-in does not fake an empty group batch to obtain hosted photo proof. ADR 0010 is authoritative; #0020 owns the separate proof contract. |
| I-15 | Resolved by contract clarification in ticket #0023 | A timeout or transport failure is no longer generic replay permission. Read-only FGA API requests follow their operation-specific rules; a mutating FGA API request may repeat only when its contract is explicitly idempotent and the exact resource/natural key, body, and owner are preserved. Once `LrHttp.postMultipart` is invoked, a missing definitive Flickr result becomes `upload_outcome_unknown` because the documented Lightroom SDK contract supplies no zero-byte proof. |
| I-16 | Resolved at the provider-neutral design boundary by tickets #0024, #0026, #0046, and #0027; executable evidence and provider selection remain outstanding | Accepted ADRs 0039 and 0043 plus `docs/administrative-control-plane-contract.md` define the private-MVP administrative boundary. Accepted ADR 0015 and `docs/worker-persistence-scheduler-contract.md` define the worker/database boundary: committed per-partition FIFO ordinals, database-clock due times, fenced leases, disposable wake hints, durable dispatch markers, explicit crash recovery, and relational constraints. Proposed ADR 0033 and `docs/hosted-deployment.md` preserve Google Cloud and PostgreSQL 18 as a provider candidate; they are not accepted policy. Accepted ADR 0034 and `docs/queue-status-api.md` select owner-scoped read-only active/attention/history projections with no retry/reopen authority. Other separately ticketed lifecycle/UX work remains legitimate pre-implementation work. |
| I-17 | Resolved at the documentation-policy boundary by ticket #0028 | Accepted ADR 0035 and `docs/README.md` define explicit precedence for the working agreement, accepted ADRs, scoped accepted contracts, future executable projections, proposals, derived views, and evidence/history. `docs/architecture.md`, the FAQ, vision, open questions, and both diagrams declare their roles; the mixed-status zero-state flow and accepted wire contract declare theirs. A repository test requires every ADR file to appear in the ADR index with the exact header status and guards the ambiguous-document role markers. Executable OpenAPI/runtime drift evidence still awaits the hosted implementation. |
| I-18 | Fact | Smaller documentation/configuration drift exists: the architecture date predates its 2026-08-23 changes (`docs/architecture.md:3`); the diagnostic README uses mutable `uv run python` rather than `uv run --frozen` (`lightroom/FGA Diagnostics.lrdevplugin/README.md:48-49`); and the development-environment Git example omits the repository-required `core.excludesFile=.git/info/exclude` override (`docs/operations/development-environment.md:95-101`; `AGENTS.md:84-91`). These need correction later, not architecture decisions in this pass. |
| I-19 | Fact | `docs/open-questions.md` is dated 2026-08-21 and has not been reconciled after later phase approvals (`docs/open-questions.md:3`). For example, it still asks whether `needs_attention` should allow later photos to advance (`docs/open-questions.md:42-46`), while the accepted active-FIFO model now makes `needs_attention` terminal and removes it from the queue (`docs/zero-state-publish-flow.md:695-705`). The question is answered by repository evidence even if the consequences merit a new owner discussion. |

### Questions already answerable from repository evidence

| Question | Repository answer |
| --- | --- |
| Is there a production architecture to compare against code? | No. Only diagnostic/research implementations exist; the hosted contract remains prose (`README.md:24`; `docs/plugin-service-contract.md:3-5`). |
| Is per-photo group intent part of the accepted flow? | Yes. The photographer confirms a per-photo immutable selection, and the Phase 6 handoff creates one natural-key intent per photo/group pair (`docs/zero-state-publish-flow.md:478-500`, `docs/zero-state-publish-flow.md:608-680`). |
| Does one terminal `needs_attention` row block later work forever? | No. It is removed from active FIFO; only throttled or safely retryable active heads continue to precede later intents (`docs/zero-state-publish-flow.md:695-705`). |
| May the FGA LrC plug-in remove current Flickr pool membership? | No. Current memberships are fresh, read-only context; all automated pool behavior is add-only (`docs/decisions/0007-fail-polite-group-submissions.md:31-52`). |
| May a blocked exact photo/group pair be force-resubmitted? | No. The permanent block survives moderation cycles and ordinary recovery/retention, with no FGA API backend or plug-in bypass (`docs/decisions/0007-fail-polite-group-submissions.md:91-131`). |

## Pinned Claude-repository architecture

The reviewed source was the repository
https://github.com/FlickrGroupAddr/backend-api at the exact pre-remediation pin
identified by the citation convention above. The repository remains private.
Its reachable branch history was sanitized, but the old direct commit remains
available to authenticated viewers; Terry explicitly accepted that residual
history exposure on 2026-08-24 and declined a GitHub Support purge. Any future
proposal to make the repository public must reassess that decision first. The
complete original 152-file disposition is in
docs/research/2026-08-23-claude-repository-coverage-ledger.md. The review
included all 50 documentation/design paths, all production modules, all six
migrations, the browser client, configuration, tests, generated artifacts,
tooling, and all 473 commit subjects, with complete reads and targeted blame on
the correctness and security paths cited below.

The source confirms a coherent but different product boundary. It is a
companion to Adobe's built-in Flickr publish service: the FGA LrC plug-in reads
an existing Flickr photo ID through documented Lightroom SDK publish records
and does not upload image bytes
(FlickrGroupAddr/backend-api@ea40755:docs/LRC-CLIENT-NOTES.md:31-52,
FlickrGroupAddr/backend-api@ea40755:docs/LRC-CLIENT-NOTES.md:96-102). It ships a
browser and plug-in against one Cloudflare Worker, D1, Durable Objects, Worker
Secrets, and Cron deployment
(FlickrGroupAddr/backend-api@ea40755:README.md:12-19,
FlickrGroupAddr/backend-api@ea40755:README.md:72-73). Its queue partitions by
(Flickr NSID, Flickr group ID) and orders by a monotonic request row ID, not a
timestamp
(FlickrGroupAddr/backend-api@ea40755:docs/architecture/DECISIONS.md:112-153).

Those facts explain much of the high-level diagram. They do not make the source
safe to adopt. The complete implementation read found routing, credential,
membership-read, dispatch-ambiguity, courtesy, privacy, and operational defects
that the earlier documentation-only review could not establish.

## Reconciliation of every earlier comment and question

The category column deliberately uses the five requested dispositions. A point
can be factually answered yet still leave a narrower owner choice; in that case
the category reflects the unresolved material part.

### Original seven high-level-diagram questions

| # | Earlier question | Category | Reconciled answer and evidence |
| --- | --- | --- | --- |
| 1 | Is the original repository and ADR set available? | resolved by the repository | Yes. The source is pinned above; all 152 tracked paths and 473 commits are accounted for in the coverage ledger. The reviewed Draw.io source is byte-identical to the originally supplied artifact (docs/project-log/2026-08-23-claude-architecture-diagram-reveal.md:5-12). |
| 2 | Is the design a companion, and how does it obtain a Flickr photo ID? | resolved by the repository | Yes. It filters Adobe Flickr published collections, joins wrappers by Lightroom local identifier, and reads publishedPhoto:getRemoteId(); collection getRemoteId() is deliberately not used as the photo ID (FlickrGroupAddr/backend-api@ea40755:docs/LRC-CLIENT-NOTES.md:31-52). |
| 3 | Was public or multi-user operation a requirement? | changed or narrowed by repository evidence | The implementation unquestionably supplies Internet-facing browser OAuth, device linking, multiple users, and two client classes. The repository cannot prove whether Terry required that scope or Claude assumed it. This narrower product-intent question remains on #0031; public launch also requires #0032 (FlickrGroupAddr/backend-api@ea40755:README.md:12-19, FlickrGroupAddr/backend-api@ea40755:src/routes/device.ts:93-187). |
| 4 | What is the queue partition key and insertion order? | resolved by the repository | The key is (Flickr NSID, Flickr group ID); FIFO uses monotonic requests.id (FlickrGroupAddr/backend-api@ea40755:docs/architecture/DECISIONS.md:112-153). |
| 5 | Which results throttle, and how are moderation, unknown results, and lost responses handled? | changed or narrowed by repository evidence | The classifier retries only Flickr codes 5, 105, and 106; codes 6 and 7 are terminal moderation results and unknown/unconfirmed results are terminal for that request (FlickrGroupAddr/backend-api@ea40755:src/adds/classify.ts:25-63, FlickrGroupAddr/backend-api@ea40755:src/adds/classify.ts:80-106). Deeper source inspection contradicts the implied pair safety: only 6/7 enter moderated_pairs, and a post-add persistence failure leaves the request pending for retry. See #0035 and #0045. |
| 6 | Are browser and plug-in sessions one credential and authority? | changed or narrowed by repository evidence | They use one signed-token mechanism but distinct rows, transports, client_type values, lifetimes, and route policy. However, an unknown stored client type falls back to browser authority, so the documented fail-closed distinction is not fully implemented (FlickrGroupAddr/backend-api@ea40755:src/session.ts:204-215, FlickrGroupAddr/backend-api@ea40755:src/middleware/session.ts:94-149). See #0033. |
| 7 | Is fga.com shorthand for flickrgroupaddr.com? | resolved by the repository | The intended origin is flickrgroupaddr.com; fga.com in three numbered diagram steps is a stale artifact defect (FlickrGroupAddr/backend-api@ea40755:README.md:12-19, FlickrGroupAddr/backend-api@ea40755:docs/architecture/DIAGRAM-NOTES.md:1-18). |

### Provisional diagram comparison

| Earlier comment | Category | Reconciliation |
| --- | --- | --- |
| The 31-step authentication flow dominates while application behavior is collapsed. | changed or narrowed by repository evidence | The supporting source defines the application behavior omitted from the authentication-focused diagram. The ceremony is internally coherent for browser OAuth, self-service linking, and revocable client classes, but remains unnecessary unless #0031 confirms that broader product scope. |
| The Claude track is a companion while the independent track is an original publisher. | resolved by the repository | This is confirmed, not a missing upload box. The current accepted FGA LrC plug-in boundary remains the original publisher (docs/decisions/0001-clean-room-publish-provider.md:1-33; external companion evidence cited above). |
| The Claude track binds to Cloudflare while the independent track remains provider-neutral. | changed by ticket #0025 | The source contains Worker/D1/Durable Object/Secrets/Cron configuration. ADR 0033 now independently selects Google Cloud/Cloud SQL after the application contracts closed; it does not inherit the legacy Cloudflare persistence shape (FlickrGroupAddr/backend-api@ea40755:wrangler.jsonc:1-103; docs/hosted-deployment.md). |
| Browser/device onboarding is broader than the private administrative credential. | resolved for private transfer/lifecycle; public onboarding remains deferred | The current MVP remains private and single-user. Accepted ADRs 0018 and 0019 close its same-workstation transfer, rotation, revocation, and lost-workstation recovery without adding a browser/device-pairing protocol. Public onboarding remains a materially different decision under #0031 and the abuse gate (docs/decisions/0004-single-user-mvp.md:1-37; docs/decisions/0006-browser-free-private-installation.md:1-72). |
| Nightly queue walking differs from immediate progress and durable jittered due times. | still valid and materially unchanged | The legacy sweep walks partitions at 00:15 UTC and stops a partition at a retryable head; the current design requests immediate progress and stores per-intent scheduling state (FlickrGroupAddr/backend-api@ea40755:src/sweep.ts:20-108; docs/architecture.md:109-138). The legacy needs_relink exclusion is nevertheless useful precedent for #0022's systemic circuit breaker. |
| The diagram omitted moderation preflight, permanent blocks, and ambiguous-delivery rules. | changed or narrowed by repository evidence | Some detail was merely off-diagram, but the material safety differences are real: the source has no immediately preceding getInfo preflight, permits acknowledged re-submission after 6/7, and lacks permanent suppression for other possible deliveries (FlickrGroupAddr/backend-api@ea40755:src/adds/attempt.ts:49-62, FlickrGroupAddr/backend-api@ea40755:src/db/requests.ts:122-171, FlickrGroupAddr/backend-api@ea40755:test/schema.test.ts:230-252). Current ADR 0007 supersedes all three policies. |
| Diagram-only omissions such as queue keys, retry codes, cookies, and documented Lightroom access might be design gaps. | contradicted or obsolete | The full repository documents these. They are no longer criticisms of the design, although the implementation defects separately identified below remain. |

### Earlier full-document-review recommendations

| Earlier recommendation or question | Category | Reconciliation |
| --- | --- | --- |
| Do not adopt acknowledged automated resubmission after a moderation result. | still valid and materially unchanged | Current ADR 0007 already prohibits it with no plug-in, API, worker, administrative, or recovery bypass (docs/decisions/0007-fail-polite-group-submissions.md:91-131). Ticket #0045 now fixes the production-adapter cases and mutation obligations; the hosted implementation must make them executable before deployment. |
| Permanently block an exact pair after every ambiguous possible add delivery. | still valid and materially unchanged | Complete source review strengthened the objection: a D1 failure after the Flickr call can leave the same request pending, not merely allow a later new request (FlickrGroupAddr/backend-api@ea40755:src/sweep.ts:61-108, FlickrGroupAddr/backend-api@ea40755:test/sweep.test.ts:131-162). See #0035. |
| Decide whether broad self-service was a real requirement. | still valid and materially unchanged | Repository evidence proves the surface exists but cannot prove owner intent. See #0031 and the public-launch gate #0032. |
| Add a client operation ID for sliced legacy batches. | contradicted or obsolete | It was reasonable for the legacy client's 200-group slices, but the current accepted Phase 6 transaction uses natural (photo, group) identities and idempotently creates or returns the complete intent set. It does not need a second speculative operation-ID layer (docs/zero-state-publish-flow.md:612-676). |
| Keep credential classes explicit if another client appears. | adopted by ticket #0033 | The legacy fallback from an unknown class to browser authority is unsafe. The current contracts now require a non-null stored class, an exhaustive class/profile/route allowlist, explicit rejection for every unknown value, and deliberate addition of each future authority. |
| Adopt evidence discipline without inheriting historical documentation sprawl. | adopted by ticket #0028; smaller drift cleanup remains | Accepted ADR 0035 and `docs/README.md` establish the authority/status hierarchy and change discipline without making a monolithic architecture document. The ADR-index/role-marker test prevents the central status seam from silently recurring. Ticket #0029 still owns the smaller dated command/document corrections, and OpenAPI remains a separate executable-projection ticket. |
| Was Internet-facing multi-user self-service an owner requirement or Claude-selected scope? | still valid and materially unchanged | This remains the only original question that repository evidence cannot answer. It is now #0031 rather than an untracked Markdown question. |

### Corrections to the earlier documentation-only review

| Earlier conclusion | Category | Corrected full-repository conclusion |
| --- | --- | --- |
| Failed or malformed `getAllContexts` data is never treated as empty. | legacy claim contradicted; current shape contract resolved by #0036; pre-add enforcement remains #0048 | The legacy parser returns an empty list when `pool` is not an array and silently drops malformed entries; the legacy add attempt also continues after a failed membership read (FlickrGroupAddr/backend-api@ea40755:src/flickr/api.ts:143-168, FlickrGroupAddr/backend-api@ea40755:src/adds/attempt.ts:49-61). The current contract now rejects malformed shape as unknown; ticket #0048 separately owns the pre-add read/write ordering. |
| Same-origin routing was a mature operational strength. | legacy risk retained as evidence; current gate defined by #0034 | Source and tests use `/auth/flickr/*` and `/auth/device-link/*` while both legacy asset-routing configurations list `/oauth` rather than `/auth`; Worker unit tests bypass that edge router (FlickrGroupAddr/backend-api@ea40755:src/routes/oauth.ts:37-38, FlickrGroupAddr/backend-api@ea40755:src/routes/device.ts:93-97, FlickrGroupAddr/backend-api@ea40755:wrangler.jsonc:75-87, FlickrGroupAddr/backend-api@ea40755:vite.config.ts:52-58). The current design instead derives one inventory from application registrations and requires development plus provider-preview black-box conformance before deployment. |
| The backend/browser implementation was implementation-ready. | changed or narrowed by repository evidence | It is substantial implemented source, but the dispatch, credential, routing, membership, and courtesy defects below prevent treating it as an adoption-ready implementation. The integrated plug-in also had not completed an end-to-end Lightroom Classic run at the pinned commit (FlickrGroupAddr/backend-api@ea40755:docs/LRC-CLIENT-NOTES.md:500-515; cited only for run status, not its private data). |
| Making an ambiguous add terminal for its request prevents an automatic repeat. | contradicted or obsolete | The sweep records an attempt, calls Flickr, and then persists resolution without a durable dispatch marker or claim. A persistence failure after delivery causes the test to expect the pending request to be retried (FlickrGroupAddr/backend-api@ea40755:src/sweep.ts:61-108, FlickrGroupAddr/backend-api@ea40755:test/sweep.test.ts:131-162). Backend-api commit 08c4bdc introduced this unsafe pending-retry premise. |

## Newly discovered full-repository findings

Every row below is categorized as newly discovered after reading the full
material. Fact identifies direct source behavior; inference identifies this
review's architectural or operational conclusion.

| ID | Kind | Finding, evidence, and ticket |
| --- | --- | --- |
| N-01 | Fact; privacy risk; reachable history remediated; residual accepted | The pre-remediation repository tracked an absolute private Lightroom catalog location, catalog-local metadata, collection names, aggregate counts, and six sampled Flickr photo IDs/URLs. A read-only catalog correlation and credential-free guest check on 2026-08-24 found all six samples in Adobe Flickr publish records and all six exact `terryott` photopages publicly accessible; those Flickr IDs/URLs were already public and are not classified as sensitive. The local path and catalog-only metadata remain private, while collection names and aggregate counts were not independently established as public. The sensitive values are intentionally not repeated here. The repository was made private, all four affected current-tree paths were removed from every rewritten ref, unaffected current-tree blobs were verified byte-identical, the rewritten branch was force-pushed, the local clone was replaced, and an exact-path privacy gate was added in backend-api commit `64a900f`. The old direct commit remains available to authenticated viewers. Terry explicitly accepted that residual on 2026-08-24 and declined a GitHub Support purge; the repository remains private. Tracked by #0013. |
| N-02 | Fact; privacy risk; reachable history remediated; residual accepted | Private board material had existed in legacy public commits; no private board prose is reproduced here. The same 2026-08-24 rewrite removed that history-only path from every rewritten ref and backend-api commit `64a900f` prevents reintroduction. The old direct commit remains available to authenticated viewers. Terry explicitly accepted that residual on 2026-08-24 and declined a GitHub Support purge; the repository remains private. Tracked by #0014. |
| N-03 | Resolved at the provider-neutral design boundary by tickets #0034 and #0025 | The legacy production and development asset-router allowlists did not match implemented `/auth` routes, so a core request could be intercepted as SPA HTML. Accepted ADR 0016 and `docs/operations/http-route-conformance.md` require one inventory generated from application route registrations, derived development/deployment matchers, and build-bound black-box probes through both the real development topology and provider preview. Proposed ADR 0033 preserves Terraform, effective Google Cloud exports, and an isolated preview as candidate adapters; no provider is selected and no executable pass is claimed before the hosted implementation supplies its accepted adapters. |
| N-04 | Resolved at the current design boundary by tickets #0026, #0035, and #0045; executable evidence awaits hosted implementation | The legacy scheduled path had no durable `dispatch_started` marker or zero-byte proof, and immediate/scheduled paths lacked one shared claim (FlickrGroupAddr/backend-api@ea40755:src/sweep.ts:58-108, FlickrGroupAddr/backend-api@ea40755:src/routes/api.ts:323-336, FlickrGroupAddr/backend-api@ea40755:src/routes/api.ts:453-471). The current worker persistence contract requires one database-fenced claim/attempt implementation for every entry path, structurally commits the marker before POST handoff, and atomically creates the permanent exact-pair block plus terminal `delivery_uncertain` after unresolved dispatch unless durable zero-byte proof exists. The fail-polite conformance contract now fixes stable test IDs, production database/worker adapters, process-crash points, bypass cases, and mutation evidence. No pass is claimed until the hosted implementation runs it against the production artifact and migrations. |
| N-05 | Resolved by ticket #0033 | The legacy evidence remains that unknown persisted `client_type` values became browser rather than invalid (FlickrGroupAddr/backend-api@ea40755:src/session.ts:204-215, FlickrGroupAddr/backend-api@ea40755:src/middleware/session.ts:94-149). The current plug-in/service and administrative contracts now require a non-null constrained stored class, exhaustive class/profile/route authorization with an explicit rejecting default, no browser/admin fallback, non-oracular `401 invalid_token`, and forward-version/rollback regression cases. |
| N-06 | Resolved at the current design boundary by ticket #0036 | The legacy parser converted a structurally malformed Flickr pool field to an empty membership list and silently discarded malformed entries (FlickrGroupAddr/backend-api@ea40755:src/flickr/api.ts:143-168). The current plug-in/service and accepted-flow contracts now require exact successful root/array/entry validation, all-or-nothing immutable snapshot publication, `membership_observation_unavailable` for missing/partial/uninterpretable data, no prefix/prior snapshot display as current, and mutation fixtures for every malformed shape. |
| N-07 | Resolved at the current design boundary by ticket #0048 | The legacy worker allowed a failed fresh `getAllContexts` call to fall through to `pools.add` (FlickrGroupAddr/backend-api@ea40755:src/adds/attempt.ts:49-61). The current worker contract requires an independent strict attempt-scoped membership read before moderation preflight, atomically reserves capacity for membership GET + moderation GET + possible POST, keeps an unavailable read at the FIFO head without `getInfo` or add, and terminalizes a confirmed existing membership without a write. The conformance contract assigns stable `FP-MEM-*` cases and mutation checks; ticket #0045 remains the executable-suite umbrella. |
| N-08 | Resolved for the private-MVP boundary by ticket #0037; public launch remains prohibited by #0032 | The legacy unauthenticated device-link start created ten-minute state with no documented admission control, and OAuth start had the same public-entry concern (FlickrGroupAddr/backend-api@ea40755:src/routes/device.ts:138-168, FlickrGroupAddr/backend-api@ea40755:src/device/link-attempt.ts:77-94). The private MVP now has no device/self-service start route; its one administrator OIDC start has explicit shared source/global/live-state limits, single-use bounded callbacks, privacy-preserving limiter keys, fail-closed dependencies, and conformance tests. These controls do not satisfy the separate public abuse threat model. |
| N-09 | Resolved at the current design boundary by ticket #0040 | The legacy human device code names a Durable Object, and start overwrites a still-live attempt on a rare code collision rather than using create-if-absent semantics (FlickrGroupAddr/backend-api@ea40755:src/device/link-attempt.ts:84-93). The private MVP retains no device-link route or allocator. The private installation credential transfer contract records the minimum boundary for any future accepted reintroduction: hosted CSPRNG generation, atomic create-if-absent, persistence-enforced live-code uniqueness, bounded fresh-code retry, and no mutation or disclosure of the existing attempt. This records a future integrity constraint without authorizing the rejected protocol or claiming to satisfy the public abuse threat model. |
| N-10 | Resolved at the current design boundary by ticket #0038; executable evidence awaits hosted implementation | The legacy `SESSION_KEY` accepted arbitrary text without minimum decoded entropy or length validation even though setup prose expected a strongly generated secret (FlickrGroupAddr/backend-api@ea40755:src/session.ts:62-69). The current session-signing key contract instead requires deployment-side generation of exactly 32 CSPRNG bytes, canonical unpadded base64url, an exact numeric Secret Manager version, strict checksum/encoding/length/canonicalization checks before readiness, zero/one bounded rotation fallback, fail-closed negative cases, and denied worker access. Format is explicitly not overclaimed as proof of randomness; executable evidence remains pending in the hosted implementation. |
| N-11 | Resolved at the current design boundary by ticket #0039; executable evidence awaits hosted implementation | The legacy public `/api/debug` returned authentication state and configured origin information outside the versioned API no-store wrapper (FlickrGroupAddr/backend-api@ea40755:src/index.ts:117-181). Accepted ADR 0037 registers no compatibility handler, makes `/api/` and `/healthz/` server-owned before static fallback, limits unauthenticated operations to fixed non-identifying startup/liveness responses, and places sanitized deployment state behind the existing Google-authenticated administrative session. The conformance matrix covers cache/auth/method/path/header/query/dependency behavior; no hosted pass is claimed yet. |
| N-12 | Resolved at the current design boundary by ticket #0041; executable evidence awaits implementation | The legacy welcome copy promises repeat attempts are stopped while its group UI offers acknowledged resubmission after a prior moderation observation (FlickrGroupAddr/backend-api@ea40755:web/src/App.svelte:111-123, FlickrGroupAddr/backend-api@ea40755:web/src/routes/AddToGroups.svelte:153-157, FlickrGroupAddr/backend-api@ea40755:web/src/routes/AddToGroups.svelte:389-405). The current moderator-safety UI contract instead requires selector, status, repeated-batch, and administrative views to use a total block-first projection from the authoritative server block, exact reviewed meanings, a closed action vocabulary with no resubmission control, and `MSUI-*` production-adapter, inventory, snapshot, hostile-client, and mutation evidence. The legacy behavior is not a compatibility requirement. |
| N-13 | Resolved at the current design boundary by ticket #0049 | The legacy browser loops over the single-group submit API for a multi-group selection, which can create one immediate opportunity per group (FlickrGroupAddr/backend-api@ea40755:web/src/lib/api.ts:79-95, FlickrGroupAddr/backend-api@ea40755:web/src/lib/submission.ts:85-104, FlickrGroupAddr/backend-api@ea40755:web/src/routes/AddToGroups.svelte:203-213, FlickrGroupAddr/backend-api@ea40755:src/routes/api.ts:348-371). Accepted ADR 0020 defines one authenticated batch route for every official client, prohibits client slicing and single-group aliases, requires one all-or-nothing database transaction, and permits at most one canonical post-commit partition hint per batch. The `CBA-*` conformance inventory covers route absence, whole-request validation, transaction rollback, hints, retries, due-sweep recovery, and mutations. |
| N-14 | Resolved at the current design boundary by ticket #0044; executable evidence awaits implementation | The legacy queue UI says one request from each line is tried each night, but the sweep walks up to 25 items and continues within a partition until a retryable result (FlickrGroupAddr/backend-api@ea40755:web/src/routes/Queue.svelte:130-134, FlickrGroupAddr/backend-api@ea40755:src/sweep.ts:31-58). The current status contract contains no fixed scheduler-cadence promise. Its total active-copy projection derives one reviewed sentence from exact server state, FIFO-ahead count, database due bound, and gate holds; treats the poll interval as read cadence only; and requires production-adapter fixtures and mutations to catch copy/behavior drift. |
| N-15 | Resolved at the current design boundary by ticket #0043; executable evidence awaits implementation | The legacy browser cleared its display state only after a successful logout request and supplied no explicit recovery when that request failed (FlickrGroupAddr/backend-api@ea40755:web/src/App.svelte:45-48, FlickrGroupAddr/backend-api@ea40755:web/src/lib/api.ts:48-57). The current lifecycle instead defines one idempotent server logout transaction, commit-before-cookie-expiration ordering, exact unconfirmed UI copy for every non-`204` or lost response, immediate view scrubbing without a false authentication claim, retry convergence across commit/response boundaries, private-window and separate-session recovery, and production-adapter failure-injection evidence. |
| N-16 | Resolved for the private-MVP boundary by ticket #0042; public account deletion remains prohibited | Flickr's available OAuth scope is broader than group addition, so the legacy UI warns about that authority (FlickrGroupAddr/backend-api@ea40755:docs/architecture/DECISIONS.md:27-55, FlickrGroupAddr/backend-api@ea40755:src/routes/oauth.ts:37-134). Accepted ADR 0017 separates local secret deletion from Flickr's owner-driven Remove Permission action, makes link/relink/disconnect revisioned and fail-closed, adds FGA administrative-session inventory/revocation, and preserves moderator-protection history through credential churn. The private MVP intentionally has no self-service account-erasure route; public/multi-user privacy and deletion remain gated by the separate accepted abuse/privacy design. |
| N-17 | Fact; no decision | Public browser source maps are intentionally enabled and the architecture explicitly does not treat source as a secret (FlickrGroupAddr/backend-api@ea40755:vite.config.ts:43-48). This is not a defect by itself; secrets and private data must remain outside the bundle. |

## Repository agreement, divergence, supersession, and gaps

| Classification | Evidence-based result |
| --- | --- |
| Agreement | Both designs keep Flickr application secrets and OAuth material in hosted components, use durable hosted intent state, partition FIFO work by user and group, read current membership through documented getAllContexts, and limit pool behavior to additions. The legacy parser/worker defects mean its implementation does not fully satisfy its membership-read prose. |
| Divergence | The legacy product is a browser-plus-companion service on Cloudflare with self-service OAuth and nightly sweeping. The current accepted product is a private original publish provider with administrative installation credentials, direct signed upload, a local recovery outbox, provider-neutral hosted contracts, immediate progress, and persisted jittered due times (docs/decisions/0001-clean-room-publish-provider.md:1-33, docs/decisions/0004-single-user-mvp.md:1-37, docs/architecture.md:47-138). |
| Supersession | Current ADR 0007 and AGENTS.md supersede legacy acknowledged resubmission, missing fresh `getInfo` preflight, fail-open membership handling, and request-only ambiguity handling. Current components must enforce an attempt-scoped strict membership guard, permanent exact-pair suppression, and the under-1,000-ms immediately-preceding moderation-preflight invariant (docs/decisions/0007-fail-polite-group-submissions.md; AGENTS.md). |
| Current-repository gap | The production FGA LrC plug-in, API backend, group-submission worker, database schema/migrations, deployment configuration, OpenAPI, and production conformance tests do not exist. Agreement is therefore architectural only, not implementation conformance (README.md:24; docs/plugin-service-contract.md:3-5). |
| Legacy-repository gap | The pinned source is substantial but cannot be reused as a shortcut without resolving #0013, #0014, and #0033-#0045. Tickets #0048 and #0049 resolved the current architectural boundaries but not the legacy implementation. That is an inference from the cited defects, not a claim that every unexecuted path is faulty. |

## Required boring-and-obvious pushback

The independent objections I-06 through I-08 remain after comparison. They are
owner checkpoints, not silent recommendations:

| Ticket | Pushback and conventional alternative |
| --- | --- |
| #0017 | Do not implement server-stored random continuation handles and two stateful refresh/generation machines for the private single-user MVP without an explicit owner override. Use one bounded refresh job with atomic snapshot replacement and a bounded response or ordinary keyset paging. The accepted proposal otherwise creates avoidable state, expiry, garbage collection, recovery, and test machinery. |
| #0018 and #0019 | Do not freeze /flickr-api-proxy/ or version-specific device token-check names into a public contract. They misdescribe resource and credential semantics and couple callers to implementation history. Use resource-oriented routes and a version-independent credential/installation resource. |

Terry resolved I-09 on 2026-08-25 by accepting the conventional right-sized
private TLS gate. Accepted ADR 0036 now requires the real Lightroom Classic
host probe, pinned `testssl.sh`, one fresh SSL Labs assessment, and certificate/
deployment lifecycle evidence; risk-selected diagnostics expand the set after
an incident, material edge change, or public/multi-user scope.

The legacy acknowledged-resubmission, fail-open membership, unknown-client
fallback, and retry-after-possible-delivery behaviors are not acceptable
synthesis choices under the current safety boundaries. The conventional
alternative is fail closed before authority or an irreversible write. No code
from the legacy source should be adopted until those invariants are explicit
and executable.

## Decision classification

### Factual observations needing no owner decision

| Observation | Evidence |
| --- | --- |
| The current repository contains no production service to accept or reject. | README.md:24 and the complete 76-file baseline inventory. |
| The two tracks intentionally solve different publish boundaries. | docs/decisions/0001-clean-room-publish-provider.md:1-33 and the external Lightroom evidence above. |
| The current add-only, fresh-preflight, permanent-block rules already supersede weaker legacy policy. | docs/decisions/0007-fail-polite-group-submissions.md:75-199. |
| The legacy queue key and row-ID FIFO are fully answered. | FlickrGroupAddr/backend-api@ea40755:docs/architecture/DECISIONS.md:112-153. |
| Current Phase 6 already has natural-key idempotency; another sliced-batch operation ID is not presently needed. | docs/zero-state-publish-flow.md:612-676. |
| Public source maps are intentional and are not a secret boundary. | FlickrGroupAddr/backend-api@ea40755:vite.config.ts:43-48. |

### Questions answerable from existing evidence

| Question | Answer |
| --- | --- |
| Is per-photo group intent accepted? | Yes; the photographer confirms an immutable per-photo selection and Phase 6 creates one natural-key intent per pair (docs/zero-state-publish-flow.md:478-500, docs/zero-state-publish-flow.md:608-680). |
| Does terminal needs_attention block a whole partition forever? | No; it leaves active FIFO, although #0022 asks whether systemic faults should halt a broader domain (docs/zero-state-publish-flow.md:695-705). |
| May any FGA component remove current Flickr membership? | No; current membership is read-only and behavior is add-only (docs/decisions/0007-fail-polite-group-submissions.md:31-52). |
| May a blocked pair be force-resubmitted? | No; there is no plug-in, API, worker, administrative, recovery, or test bypass (docs/decisions/0007-fail-polite-group-submissions.md:91-131). |
| Does the legacy repository settle whether public scope was owner-required? | No. It proves implementation scope, not the provenance of the product requirement. That judgment is #0031. |

### Prioritized owner questions and resolution status

The owner clarified on 2026-08-23 that every capability in his current Adobe
Flickr publish-service workflow is in scope, but no Adobe interaction or
implementation choice constrains FGA. Ticket #0065 is therefore the discovery
gate for the remaining user-experience questions: finish the sanitized current-
workflow inventory, then challenge it for efficiency before freezing lower-
level contracts.

| Order | Ticket | Question and recommended discussion frame |
| --- | --- | --- |
| 1 | #0061 | Flickr requires `primary_photo_id` to create a photoset. Should **Create Album…** create only the local Lightroom album initially, then materialize its Flickr album with the first real successfully uploaded photo? This is the conventional recommendation; placeholder or unrelated photos are rejected. |
| 2 | #0016 | Resolved 2026-08-25: the FGA LrC plug-in permits zero-group publication under ADR 0010. |
| 3 | #0020 | What exactly does a Lightroom catalog remote ID mean before the FGA API backend has verified ownership and committed hosted proof? Define the visible state and repair semantics for uploaded-but-handoff-pending. |
| 4 | #0021 | What is the minimum safe user workflow after direct-upload delivery ambiguity, where replay can duplicate a photo? This is implementation-blocking recovery behavior. |
| 5 | #0031, then #0032 | Was browser-based, Internet-facing multi-user self-service actually required? If yes, the separate abuse threat model is a launch gate; if no, keep that legacy surface out of the private MVP. |
| 6 | #0017 | Accept the simpler bounded snapshot/keyset alternative, or explicitly override the pushback and accept stateful continuation-handle lifecycle cost. |
| 7 | #0018 and #0019 | Choose conventional resource/credential names before a machine-readable contract freezes the routes, or explicitly retain the surprising names with rationale. |
| 8 | #0030 | Resolved 2026-08-25: accepted ADR 0036 uses the right-sized private TLS gate and risk-triggered diagnostic expansion. |
| 9 | #0025 | Resolved 2026-08-26: ADR 0033 selects Google Cloud only after the API, worker, persistence, security, and operations contracts closed, and records the concrete deployment values and evidence boundary. |

Questions not in this table are either answered by evidence or represented by
technical follow-up tickets that do not need owner judgment before the nine
topics above. The recommended discussion order is the table order because it
settles user-visible semantics before API spelling and infrastructure.

## Localswim ticket handoff

The private board, not this document, is the work queue. Parent #0012
claude-repository-review remains in ready_for_review. On 2026-08-23 Terry
clarified that Ready for work represents Codex authorization even when a card
has an unresolved dependency; Backlog is reserved for intentionally withheld or
insufficiently scoped work. Needs Terry represents a required owner judgment,
while Blocked is reserved for an external condition that prevents both Terry
and Codex from advancing the card. The actionable technical findings below were
moved accordingly, including seven owner-decision cards moved from Backlog to
Needs Terry. The table contains only public-safe IDs and subjects, not private
board prose.

| Ticket | Priority | Public-safe subject |
| --- | --- | --- |
| #0013 | P1 | Remediate catalog-derived data in legacy public history |
| #0014 | P1 | Remediate private board snapshot in legacy public history |
| #0015 | P1 | Decide batch ordering after an earlier handoff gap |
| #0016 | P2 | Decide whether zero-group Flickr publishing is allowed |
| #0017 | P2 | Simplify group refresh and membership pagination |
| #0018 | P2 | Replace the Flickr proxy route family with resources |
| #0019 | P2 | Rename the device token-check route |
| #0020 | P1 | Define catalog remote ID before hosted ownership proof |
| #0021 | P1 | Design upload ambiguity reconciliation |
| #0022 | P1 | Add a systemic Flickr fault circuit breaker |
| #0023 | P1 | Narrow the transport retry contract |
| #0024 | P1 | Define the administrative control plane contract |
| #0025 | P2 | Choose the hosted provider and deployment shape |
| #0026 | P1 | Specify worker leases scheduler and database state |
| #0027 | P2 | Specify queue and needs-attention status APIs |
| #0028 | P2 | Establish a canonical architecture authority hierarchy |
| #0029 | P3 | Correct known architecture documentation drift |
| #0030 | P2 | Right-size the private MVP TLS acceptance gate |
| #0031 | P1 | Decide the public multi-user browser product scope |
| #0032 | P1 | Define the public-service abuse threat model |
| #0033 | P1 | Make unknown credential classes fail closed |
| #0034 | P1 | Test auth routes against deployed asset routing |
| #0035 | P1 | Enforce claim and dispatch ambiguity invariants |
| #0036 | P1 | Reject malformed membership reads as unknown |
| #0037 | P1 | Add device-link and login admission controls |
| #0038 | P2 | Validate session signing-key strength |
| #0039 | P2 | Remove or constrain the public debug surface |
| #0040 | P3 | Make device-link code creation collision-safe |
| #0041 | P2 | Keep moderator-safety UI copy consistent with policy |
| #0042 | P1 | Define OAuth revocation and account lifecycle |
| #0043 | P2 | Handle server logout failure honestly |
| #0044 | P3 | Keep queue cadence copy derived from behavior |
| #0045 | P1 | Encode ADR 0007 as worker and database conformance tests |
| #0046 | P1 | Define confidential private-install credential transfer |
| #0047 | P1 | Define installation credential rotation and recovery |
| #0048 | P1 | Fail closed when a pre-add membership read fails |
| #0049 | P1 | Make all multi-group clients use the courteous batch path |

Existing ticket #0002 remains the appropriate home for a machine-readable API
contract; this review did not create a duplicate.

## Review status and durable checkpoints

This is a complete static architecture review, not an implementation pass or a
runtime acceptance test. No architecture or production code was changed. The
external checkout was pinned and clean; its implementation was inspected but
not executed or adopted. The baseline had 76 tracked files; this review added
the canonical review and exact external coverage ledger, bringing the current
tracked inventory to 78 files before the small canonical-pointer updates made
in the final review commit.

Durable checkpoints are:

| Commit | Checkpoint |
| --- | --- |
| ce9c343 | Started the fresh-eyes review and baseline ledger. |
| 7dea731 | Froze the independent assessment before comparison. |
| d6fbedf | Completed all Claude-created documentation coverage. |
| 3a3fe55 | Completed implementation, schema, configuration, test, tooling, and history coverage. |
| f5c7258 | Completed reconciliation, ticket register, and canonical supersession pointers. |

The exact file-by-file proof is
docs/research/2026-08-23-claude-repository-coverage-ledger.md. Historical
diagram and documentation-only reviews remain as provenance but are superseded
by this document. Final Git delivery and private board handoff state are
recorded in the containing Git commit and ticket #0012 respectively.

At completion, git remote -v remained empty and the required git push attempt
after f5c7258 failed with “No configured push destination.” The review commits
are therefore durable in local main but cannot be pushed until a repository
remote is deliberately configured. This revalidates the earlier no-remote
handoff (docs/project-log/2026-08-23-session-closeout.md:21-23); this review did
not guess or add a remote.

## Post-review owner clarification

Later on 2026-08-23, Terry clarified that one FGA LrC plug-in has two primary
jobs: original 8-bit PNG publication and add-only group queueing for Flickr
photos published through either the FGA LrC plug-in or another path. ADR 0008
records this accepted hybrid product boundary. It narrows this review's earlier
publisher-versus-companion split: the original publish flow remains accepted,
while existing-photo queueing is also first-class scope. ADR 0021 and
the existing-public-photo intake contract now close ticket #0050's discovery,
selection, identifier-provenance, and backend authority-proof question. The
contract uses advisory owner-fixed public-photo paging, fresh hosted exact-photo
proof, and a common server photo binding rather than trusting catalog evidence
or a client-supplied photo ID.

Terry also clarified the product history and expected audience. FGA began as a
backend-centered JAMstack browser service, then moved into Lightroom Classic
when Terry recognized that Lua unfamiliarity was no longer a product constraint
and that preserving his optimized cull/edit/publish loop produced much better
customer experience. The PNG publishing job was added after that realization.
Terry is the only expected customer, not merely the first MVP user. ADR 0004 now
records that routine browser and public/multi-user product work is out of scope;
review question #0031 is resolved, and #0032 is only a conditional gate if that
scope is deliberately reopened.
