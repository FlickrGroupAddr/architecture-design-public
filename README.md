# FlickrGroupAddr (FGA)

This is the owner-approved sanitized public snapshot of the architecture
repository. It begins with a new root commit and includes no inherited Git
history. The existing private architecture repository remains the working
source; see [snapshot provenance](PUBLICATION.md) for scope and validation.

FlickrGroupAddr (FGA) is a proposed Lightroom Classic publishing workflow for
photographers who
use Flickr groups to improve the visibility of their work.

The project has two related goals:

1. Publish Lightroom's developed image to Flickr as a losslessly compressed
   PNG when practical.
2. Reliably submit both newly FGA-published photos and existing public photos in
   the owner's Flickr account to user-selected group pools, despite per-group
   posting limits that may span days, weeks, or months.

The current direction is one original, MIT-licensed FGA LrC publish provider
that also queues group additions for Flickr photos uploaded through another
path, whether or not Lightroom Classic stores their Flickr bindings, plus a
small hosted service. The plug-in owns both explicit Lightroom Classic
workflows; the service durably serializes group submissions by
`(Flickr user, group)`, retries only outcomes known to be safe, and permanently
suppresses a repeat photo/group submission after moderation or ambiguous
delivery. This **fail-polite** boundary protects Flickr's volunteer moderators
even when it costs automatic liveness.

This repository is currently in architecture and contract design. It includes
a development-only Lightroom diagnostic plug-in that completed the PNG output
experiment and proved a service-signed direct Flickr upload from Lightroom.
The production publish provider and hosted service are not yet implemented.

## Project record

- [Architecture documentation authority](docs/README.md)
- [Vision and scope](docs/vision-and-scope.md)
- [Architecture overview](docs/architecture.md)
- [Selected Cloudflare direction and native-storage evaluation](docs/decisions/0050-select-cloudflare-and-evaluate-native-storage-first.md)
- [Editable system architecture diagram](docs/diagrams/system-architecture.drawio)
- [Clean-room interaction maps: all three tabs authoritative](docs/diagrams/clean-room-authentication-legal.drawio)
- [Accepted Google browser-session decision](docs/decisions/0039-use-google-identity-services-browser-sessions.md)
- [Accepted browser-session lifecycle contract](docs/browser-session-lifecycle.md)
- [OpenAPI design projection](openapi/README.md)
- [Draft plug-in/service contract](docs/plugin-service-contract.md)
- [Proposed Lightroom group-selection interaction](docs/decisions/0045-use-a-library-modal-and-photo-metadata-for-group-selection.md)
- [Existing public Flickr photo intake contract](docs/existing-public-photo-intake.md)
- [Album-scoped publish contract](docs/album-scoped-publish-contract.md)
- [Flickr album-write reconciliation](docs/album-write-reconciliation.md)
- [Flickr album lifecycle](docs/album-lifecycle-contract.md)
- [Group snapshot and pagination contract](docs/group-snapshot-and-pagination.md)
- [Non-destructive existing-photo boundary](docs/non-destructive-existing-photo-boundary.md)
- [Flickr replacement ambiguity and reconciliation](docs/replacement-ambiguity-reconciliation.md)
- [Flickr replacement backup and reverse-replacement safeguards](docs/replacement-backup-and-reverse-replacement.md)
- [Private-MVP administrative control-plane contract](docs/administrative-control-plane-contract.md)
- [Private installation credential transfer ceremony](docs/private-install-credential-transfer.md)
- [Private installation credential lifecycle](docs/installation-credential-lifecycle.md)
- [OAuth grant, administrative-session, and account lifecycle](docs/oauth-and-account-lifecycle.md)
- [Worker persistence and scheduler contract](docs/worker-persistence-scheduler-contract.md)
- [Group-submission status API contract](docs/queue-status-api.md)
- [Moderator-safety UI conformance contract](docs/moderator-safety-ui-conformance.md)
- [Hosted deployment contract](docs/hosted-deployment.md)
- [Hosted compute candidate comparison](docs/research/2026-09-05-hosted-compute-candidate-comparison.md)
- [Fail-polite worker/database conformance suite](docs/testing/fail-polite-worker-database-conformance.md)
- [Courteous group-batch admission conformance](docs/testing/courteous-batch-admission-conformance.md)
- [HTTP route and asset-router conformance](docs/operations/http-route-conformance.md)
- [Zero-state publish flow](docs/zero-state-publish-flow.md)
- [First-publish clickable customer storyboard](prototypes/first-publish-storyboard/README.md)
- [Future Terry FAQ](docs/future-terry-faq.md)
- [Open questions](docs/open-questions.md)
- [Flickr research](docs/research/flickr.md)
- [Lightroom SDK research](docs/research/lightroom-classic.md)
- [Catalog-only existing-photo association spike](docs/research/catalog-only-existing-photo-association-spike.md)
- [Direct-upload signing research](docs/research/upload-signing-boundary.md)
- [PNG size and fidelity experiment](docs/research/png-experiment.md)
- [Decision records](docs/decisions/README.md)
- [Engineering working agreement](AGENTS.md)
- [Development environment](docs/operations/development-environment.md)
- [Development and operations diligence cadence](docs/operations/development-and-operations-cadence.md)
- [FGA API backend framework-signing key candidate](docs/operations/session-signing-key.md)
- [FGA API backend health and diagnostics contract](docs/operations/health-and-diagnostics.md)
- [FGA HTTPS-edge TLS deployment acceptance](docs/operations/tls-edge-acceptance.md)
- [Photography test-data handling](docs/operations/photography-data-handling.md)
- [Flickr PNG round-trip procedure](docs/operations/flickr-roundtrip.md)
- [Disposable Flickr replacement probe](docs/operations/flickr-replacement-probe.md)
- [Project log](docs/project-log/README.md)

## Lightroom diagnostic

The original, MIT-licensed plug-in under
[`lightroom/FGA Diagnostics.lrdevplugin`](lightroom/FGA%20Diagnostics.lrdevplugin)
renders a full-resolution PNG/JPEG matrix and contains the completed direct-
upload probe. See its
[README](lightroom/FGA%20Diagnostics.lrdevplugin/README.md) for installation and
use. Run `uv run --frozen python scripts/check_lua.py` to execute the project's Lua
static-analysis and Adobe Lua 5.1 syntax checks; run
`uv run --frozen python scripts/check_python.py` for Ruff, Pyright, and Python tests.

A second development-only **FGA Diligence** plug-in is planned as the one-click
Lightroom side of recurring compatibility and end-to-end acceptance. It will
write only sanitized machine-readable state to
`C:\Temp\FGA-diligence-status.json` while Codex monitors the Lightroom run and
performs the external checks. Its scope and handoff contract are in the
[development and operations diligence cadence](docs/operations/development-and-operations-cadence.md#dedicated-lightroom-diligence-plug-in).

The licensed Adobe Lightroom Classic SDK is deliberately excluded from Git.
See [the vendor note](vendor/LrC%20SDK/README.md) for local setup details.

## License

Original FGA source code and documentation are licensed under the
[MIT License](LICENSE), copyright 2026 Terry Ott. Bundled third-party software
remains under its own license; see [third-party notices](THIRD_PARTY_NOTICES.md).
The licensed Adobe Lightroom Classic SDK is not part of this repository or the
MIT grant.

## Name and affiliation

**FlickrGroupAddr** is the public product name, abbreviated **FGA**. The exact
joined spelling is a deliberate play on Flickr and matches the
project-owner-controlled `flickrgroupaddr.com` origin selected for the FGA API
backend and administrative control plane.

The product is independent of Adobe, Flickr, and SmugMug. Flickr's API terms
require this notice in the eventual product:

> This product uses the Flickr API but is not endorsed or certified by
> SmugMug, Inc.
