# Pinned Claude repository coverage ledger

Status: **complete — 152 of 152 tracked paths accounted for**

Date: 2026-08-23

This is the file-by-file coverage ledger for the external Claude-era repository
used by the fresh-eyes architecture review. The source is the public repository
`https://github.com/FlickrGroupAddr/backend-api`, inspected from a clean transient
checkout at exact commit `ea407553704aa7a950c341653b0e7d21073f271f`. At that
commit, `git ls-files` returns exactly 152 paths. No conclusion depends on the
transient checkout surviving.

**Post-review privacy remediation, 2026-08-24:** the source repository was made
private and its history was rewritten under #0013 and #0014. The public-safe
successor commit is `26b7070cb1092bb9fbac045ddd845884f6aa9ea4`; it retains 148
of the reviewed current-tree paths byte-for-byte and intentionally omits four
private current-tree artifacts. One additional private board path that existed
only in history was also removed from every rewritten ref. The inventory below
preserves what the review covered without preserving any private content.

`Complete` means read from beginning to end. `Inspected` means generated, vendored,
binary, implementation, configuration, schema, or test material was examined to
the architecture-relevant depth stated in the finished review. `Pending` means no
review claim is made yet. The external repository is evidence only; it is not an
FGA source-of-truth repository.

## Complete-read documentation scope (50 paths)

- [x] Complete — `CLAUDE.md`
- [x] Complete — `README.md`
- [x] Complete — `docs/FLICKR.md`
- [x] Complete before privacy removal — `docs/LRC-CLIENT-NOTES.md`
- [x] Complete — `docs/ORIENTATION.md`
- [x] Complete — `docs/PNG-PUBLISH-SPIKE-NOTES.md`
- [x] Complete — `docs/SETUP.md`
- [x] Complete — `docs/TRACEABILITY.md`
- [x] Complete — `docs/TRELLO-SPIKE-NOTES.md`
- [x] Complete — `docs/WORK-LOG.md`
- [x] Complete — `docs/architecture/BADGE-PLACEMENT.md`
- [x] Complete — `docs/architecture/DECISIONS.md`
- [x] Complete — `docs/architecture/DIAGRAM-NOTES.md`
- [x] Complete and XML-inspected — `docs/architecture/FlickrGroupAddr-Architecture-2026-08-19-16x9.drawio`
- [x] Complete and XML-inspected — `docs/architecture/FlickrGroupAddr-Architecture-2026-08-19-8.5x14.drawio`
- [x] Complete and XML-inspected — `docs/architecture/FlickrGroupAddr-Architecture-2026-08-19-canvas.drawio`
- [x] Complete — `docs/architecture/KEY-ROTATION-NOTES.md`
- [x] Complete — `docs/architecture/LONG-POLL-NOTES.md`
- [x] Complete and XML-inspected — `docs/architecture/logos/cloudflare-mark.svg`
- [x] Complete and XML-inspected — `docs/architecture/logos/flickr-mark-tight.svg`
- [x] Complete and XML-inspected — `docs/architecture/logos/flickr-mark.svg`
- [x] Complete and XML-inspected — `docs/architecture/logos/lightroom-classic-mark.svg`
- [x] Complete and XML-inspected — `docs/architecture/logos/users.svg`
- [x] Complete and XML-inspected — `docs/architecture/logos/workstation.svg`
- [x] Complete before privacy removal — `docs/lrc-spike/README.md`
- [x] Complete before privacy removal — `docs/lrc-spike/RESULT-2026-08-15.txt`
- [x] Complete — `docs/lrc-spike/plugin/BindTitleProbe.lua`
- [x] Complete — `docs/lrc-spike/plugin/CheckboxPicker.lua`
- [x] Complete — `docs/lrc-spike/plugin/ConnectivityProbe.lua`
- [x] Complete — `docs/lrc-spike/plugin/DeviceLink.lua`
- [x] Complete — `docs/lrc-spike/plugin/DeviceLinkProbe.lua`
- [x] Complete — `docs/lrc-spike/plugin/DumpPublishServices.lua`
- [x] Complete — `docs/lrc-spike/plugin/EntropyProbe.lua`
- [x] Complete — `docs/lrc-spike/plugin/FgaApi.lua`
- [x] Complete — `docs/lrc-spike/plugin/FgaApiProbe.lua`
- [x] Complete — `docs/lrc-spike/plugin/HostVersion.lua`
- [x] Complete — `docs/lrc-spike/plugin/HostVersionProbe.lua`
- [x] Complete — `docs/lrc-spike/plugin/Info.lua`
- [x] Complete — `docs/lrc-spike/plugin/PhotoIds.lua`
- [x] Complete — `docs/lrc-spike/plugin/PhotoIdsProbe.lua`
- [x] Complete — `docs/lrc-spike/plugin/PickerProbe.lua`
- [x] Complete — `docs/lrc-spike/plugin/PreflightProbe.lua`
- [x] Complete — `docs/lrc-spike/plugin/QueueAdds.lua`
- [x] Complete — `docs/lrc-spike/plugin/QueueAddsDialog.lua`
- [x] Complete — `docs/lrc-spike/plugin/TransferPicker.lua`
- [x] Complete — `docs/lrc-spike/plugin/json.LICENSE.txt`
- [x] Complete and provenance-inspected — `docs/lrc-spike/plugin/json.lua`
- [x] Complete before privacy removal — `docs/lrc-spike/probe-catalog.py`
- [x] Complete — `docs/lrc-spike/test/lrc-stubs.lua`
- [x] Complete — `docs/lrc-spike/test/run.lua`

## Architecture-relevant inspection scope (102 paths)

The six migrations and all 22 production `src/` modules were read completely.
The critical queue, schema, session, device-link, plug-in-scope, membership,
batch, preflight, contract-conformance, and Worker-routing tests were read
completely; every remaining test received a declaration-and-assertion inventory
and targeted risk search. Configuration and browser files were either read
completely or inspected to the architecture-relevant depth. Tooling scripts were
inspected for purpose, imports, entry points, mutation boundaries, and generated
artifacts; their internal formatting and diagram-geometry algorithms were not
re-reviewed as production architecture. Generated, locked, vendored, and binary
artifacts received the specific provenance and contract checks described below.

- [x] Complete — `.claude/settings.json`
- [x] Complete — `.dev.vars.example`
- [x] Complete — `.gitattributes`
- [x] Complete — `.gitignore`
- [x] Complete — `.luarc.json`
- [x] Complete — `.sqlfluff`
- [x] Complete — `LICENSE`
- [x] Inspected — `biome.jsonc`
- [x] Inspected — `lrc.toml`
- [x] Complete — `migrations/0001_initial.sql`
- [x] Complete — `migrations/0002_withdrawn_outcome.sql`
- [x] Complete — `migrations/0003_public_id.sql`
- [x] Complete — `migrations/0004_sessions.sql`
- [x] Complete — `migrations/0005_session_client_type.sql`
- [x] Complete — `migrations/0006_client_type_names_the_client.sql`
- [x] Inspected lock/provenance — `package-lock.json`; lockfile version 3,
  213 package records, and root dependency, version, integrity, source, engine,
  and license metadata were inspected
- [x] Complete — `package.json`
- [x] Inspected — `ruff.toml`
- [x] Inspected tooling — `scripts/argparse-check.py`
- [x] Inspected tooling — `scripts/badge-positions.py`
- [x] Inspected generated-diagram tooling — `scripts/build-diagram.py`
- [x] Inspected tooling — `scripts/check-diagram-date.py`
- [x] Inspected tooling — `scripts/claude-dirty-words.py`
- [x] Inspected tooling — `scripts/diagram_sheets.py`
- [x] Inspected generated SDK index — `scripts/lrc-sdk-api.json`; valid JSON,
  SDK 15.3 provenance, 38 namespaces, and SHA2-256 digest checked
- [x] Inspected generated SDK index — `scripts/lrc-sdk-modules.json`; valid JSON,
  SDK 15.3 provenance, 56 modules, and SHA2-256 digest checked
- [x] Inspected tooling — `scripts/lsp-check.py`
- [x] Inspected tooling — `scripts/lua-balance.py`
- [x] Inspected tooling — `scripts/lua-imports.py`
- [x] Inspected tooling — `scripts/mutation-check.py`
- [x] Inspected tooling — `scripts/preview-diagram.py`
- [x] Inspected tooling — `scripts/preview-server.py`
- [x] Inspected tooling — `scripts/stale-counts.py`
- [x] Inspected tooling — `scripts/svelte-compile-check.mjs`
- [x] Inspected tooling — `scripts/traceability.py`
- [x] Inspected — `selene.toml`
- [x] Complete — `src/adds/attempt.ts`
- [x] Complete — `src/adds/classify.ts`
- [x] Complete — `src/admin/allowlist.ts`
- [x] Complete — `src/crypto/tokens.ts`
- [x] Complete — `src/db/metrics.ts`
- [x] Complete — `src/db/requests.ts`
- [x] Complete — `src/db/users.ts`
- [x] Complete — `src/device/codes.ts`
- [x] Complete — `src/device/link-attempt.ts`
- [x] Complete — `src/flickr/api.ts`
- [x] Complete — `src/flickr/oauth.ts`
- [x] Complete — `src/index.ts`
- [x] Complete — `src/middleware/admin.ts`
- [x] Complete — `src/middleware/session.ts`
- [x] Complete — `src/oauth/login-attempt.ts`
- [x] Complete — `src/oauth/return-to.ts`
- [x] Complete — `src/oauth/signature.ts`
- [x] Complete — `src/routes/api.ts`
- [x] Complete — `src/routes/device.ts`
- [x] Complete — `src/routes/oauth.ts`
- [x] Complete — `src/session.ts`
- [x] Complete — `src/sweep.ts`
- [x] Inspected tests — `test/admin.test.ts`
- [x] Complete — `test/api.test.ts`
- [x] Complete — `test/apply-migrations.ts`
- [x] Complete — `test/batch.test.ts`
- [x] Inspected tests — `test/classify.test.ts`
- [x] Complete — `test/contract-conformance.test.ts`
- [x] Inspected tests — `test/crypto.test.ts`
- [x] Complete — `test/device.test.ts`
- [x] Complete — `test/env.d.ts`
- [x] Inspected tests — `test/oauth.test.ts`
- [x] Inspected tests — `test/outcomes.test.ts`
- [x] Inspected tests — `test/photo-groups.test.ts`
- [x] Complete — `test/plugin-scope.test.ts`
- [x] Complete — `test/preflight.test.ts`
- [x] Inspected tests — `test/router.test.ts`
- [x] Inspected tests — `test/scheduled.test.ts`
- [x] Complete — `test/schema.test.ts`
- [x] Complete — `test/session.test.ts`
- [x] Inspected tests — `test/signature.test.ts`
- [x] Inspected tests — `test/submission.test.ts`
- [x] Complete — `test/sweep.test.ts`
- [x] Complete — `test/worker.test.ts`
- [x] Complete — `tsconfig.json`
- [x] Complete — `vendor/README.md`
- [x] Complete — `vite.config.ts`
- [x] Complete — `vitest.config.ts`
- [x] Complete — `web/index.html`
- [x] Inspected binary/provenance — `web/public/fonts/inter-var-latin.woff2`;
  48,256 bytes, SHA2-256 digest checked, and the pinned Fontsource Inter 5.3.0
  OFL-1.1 package record traced through `package-lock.json`
- [x] Complete — `web/src/App.svelte`
- [x] Inspected presentation layer — `web/src/app.css`
- [x] Complete — `web/src/lib/api.ts`
- [x] Complete — `web/src/lib/contract.ts`
- [x] Complete — `web/src/lib/navigate.ts`
- [x] Complete — `web/src/lib/outcomes.ts`
- [x] Complete — `web/src/lib/router.ts`
- [x] Complete — `web/src/lib/submission.ts`
- [x] Complete — `web/src/main.ts`
- [x] Complete — `web/src/routes/AddToGroups.svelte`
- [x] Complete — `web/src/routes/Admin.svelte`
- [x] Complete — `web/src/routes/Queue.svelte`
- [x] Complete — `web/src/shims.d.ts`
- [x] Complete — `web/tsconfig.json`
- [x] Inspected generated contract — `worker-configuration.d.ts`; generation
  header, FGA binding interface, 14,892-line extent, and SHA2-256 digest checked
- [x] Complete — `wrangler.jsonc`

The two section counts are exhaustive: 50 complete-read documentation paths plus
102 architecture-relevant inspection paths equals the 152-path tracked inventory
at the pinned commit. There are no pending paths.
