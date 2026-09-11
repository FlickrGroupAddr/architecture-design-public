# Architecture decision records

Decision records preserve why consequential choices were made. A proposed ADR
is a recommendation under discussion; only an accepted ADR is project policy.
The ADR's own `Status:` header is canonical; this table is a tested navigation
projection. The repository-wide precedence and conflict rules are in the
[architecture documentation authority](../README.md).

| ADR | Status | Topic |
| --- | --- | --- |
| [0001](0001-clean-room-publish-provider.md) | Accepted | Build an original publish provider instead of extending Adobe's binary |
| [0002](0002-lossless-png-output.md) | Accepted | Prefer 8-bit sRGB PNG with explicit size handling |
| [0003](0003-mit-license-boundary.md) | Accepted | License original FGA work under MIT |
| [0004](0004-single-user-mvp.md) | Accepted | Start with a private single-user deployment |
| [0005](0005-service-signed-direct-upload.md) | Accepted | Use direct Flickr uploads signed by the FGA API backend |
| [0006](0006-browser-free-private-installation.md) | Accepted | Provision the private installation without a plug-in browser flow |
| [0007](0007-fail-polite-group-submissions.md) | Accepted | Permanently suppress repeat group submissions after moderation or ambiguous delivery |
| [0008](0008-hybrid-publisher-and-existing-photo-queueing.md) | Accepted | Publish new PNG photos and queue add-only group intents for existing Flickr photos |
| [0009](0009-eventually-consistent-unordered-publishing.md) | Accepted | Treat multi-photo publishing as eventually consistent and unordered |
| [0010](0010-zero-group-publication.md) | Accepted | Permit Flickr publication without group additions |
| [0011](0011-catalog-remote-id-and-hosted-proof.md) | Accepted | Treat a catalog remote ID as an upload result until hosted proof |
| [0012](0012-photographer-reconciliation-after-ambiguous-upload.md) | Accepted | Require photographer reconciliation after an ambiguous upload |
| [0013](0013-durable-flickr-write-circuit-breaker.md) | Accepted | Pause Flickr writes at durable account and deployment fault gates |
| [0014](0014-allowlisted-oidc-administration.md) | Rejected | Use one allowlisted OIDC owner for private administration |
| [0015](0015-database-fenced-worker-scheduling.md) | Accepted | Use database-fenced partition leases and due-time scheduling |
| [0016](0016-derived-route-conformance.md) | Accepted | Derive and black-box-test server-first route ownership |
| [0017](0017-explicit-oauth-and-account-lifecycle.md) | Accepted | Separate local disconnect, Flickr permission removal, and retained safety state |
| [0018](0018-same-workstation-private-credential-transfer.md) | Accepted | Transfer the private installation credential by same-workstation paste |
| [0019](0019-revisioned-installation-credential-lifecycle.md) | Accepted | Rotate revisioned installation credentials without normal-authority overlap |
| [0020](0020-single-courteous-group-batch-admission.md) | Accepted | Admit every group selection through one courteous server batch |
| [0021](0021-fresh-server-proof-for-existing-public-photos.md) | Accepted | Bind existing public photos only after fresh owner/visibility proof |
| [0022](0022-separate-photo-identity-from-catalog-and-album-records.md) | Accepted | Separate Flickr photo identity from catalog records and album membership |
| [0023](0023-never-replay-an-ambiguous-flickr-replacement.md) | Accepted | Never replay a Flickr replacement after its durable dispatch marker |
| [0024](0024-treat-reverse-replacement-as-a-new-write.md) | Accepted | Treat reverse replacement as a new non-idempotent write |
| [0025](0025-materialize-flickr-album-with-first-published-photo.md) | Accepted | Materialize a Flickr album with its first real published photo |
| [0026](0026-reconcile-create-by-owner-and-attachment-by-membership.md) | Accepted | Reconcile album creation by owner and attachment by membership |
| [0027](0027-rename-albums-but-do-not-delete-them-from-local-actions.md) | Accepted | Rename bound albums but keep local removal non-destructive |
| [0028](0028-support-ordinary-albums-only.md) | Accepted | Support ordinary published albums and exclude smart albums |
| [0029](0029-bind-each-ordinary-collection-to-one-flickr-album.md) | Accepted | Bind each ordinary published collection to one Flickr album |
| [0030](0030-use-one-refresh-job-and-keyset-pages.md) | Accepted | Use one bounded group refresh job and revisioned keyset pages |
| [0031](0031-use-resource-oriented-fga-api-routes.md) | Accepted | Name plug-in API routes for FGA resources, not Flickr plumbing |
| [0032](0032-read-the-current-installation-resource.md) | Accepted | Validate credentials by reading the current installation resource |
| [0033](0033-deploy-on-google-cloud.md) | Superseded | Deploy the private hosted components on Google Cloud |
| [0034](0034-expose-read-only-group-submission-status.md) | Accepted | Expose read-only group-submission intent status |
| [0035](0035-use-adrs-and-scoped-contracts-as-authority.md) | Accepted | Use accepted ADRs and scoped contracts as architecture authority |
| [0036](0036-use-a-right-sized-private-tls-gate.md) | Accepted | Use a right-sized private TLS acceptance gate |
| [0037](0037-expose-only-coarse-public-health.md) | Accepted | Expose only coarse public health |
| [0038](0038-keep-existing-photo-intake-queue-only.md) | Accepted | Keep existing-photo intake queue-only |
| [0039](0039-use-google-identity-services-browser-sessions.md) | Accepted | Use Google Identity Services with opaque FGA browser sessions |
| [0040](0040-expose-plugin-codes-as-user-resources.md) | Accepted | Expose Plugin Codes as user-owned resources |
| [0041](0041-use-clean-room-authentication-tabs-as-interaction-authority.md) | Accepted | Use the clean-room authentication tabs as interaction authority |
| [0042](0042-use-flickr-wordmark-in-architecture-diagram.md) | Accepted | Use the Flickr wordmark in the tab-three service boundary |
| [0043](0043-use-transaction-bound-google-session-reauthentication.md) | Accepted | Use transaction-bound Google session reauthentication |
| [0044](0044-use-canonical-crockford-base32-plugin-codes.md) | Accepted | Use canonical grouped Crockford Base32 for Plugin Codes |
| [0045](0045-use-a-library-modal-and-photo-metadata-for-group-selection.md) | Accepted | Use a Library modal and photo metadata for group selection |
| [0046](0046-use-existing-amazon-rds-postgresql.md) | Accepted | Retain the existing RDS PostgreSQL fallback under ADR 0050 |
| [0047](0047-separate-architecture-hosted-and-lightroom-repositories.md) | Proposed | Separate architecture, hosted, and Lightroom implementation repositories |
| [0048](0048-return-flickr-authorization-target-as-json.md) | Proposed | Return the Flickr authorization target as JSON |
| [0049](0049-use-plugin-code-rotation-candidate-resources.md) | Proposed | Use subordinate Plugin Code resources for credential rotation |
| [0050](0050-select-cloudflare-and-evaluate-native-storage-first.md) | Accepted | Select Cloudflare and evaluate Durable Objects and D1 before the RDS fallback |
| [0051](0051-trust-private-storage-runtime-with-guarded-writes.md) | Accepted | Trust the private storage runtime while retaining guarded writes and permanent suppression |
| [0052](0052-evaluate-paused-native-credential-replacement.md) | Accepted | Evaluate paused native credential replacement and require a high need threshold for AWS |
| [0053](0053-accept-millisecond-private-database-clocks.md) | Accepted | Accept millisecond database clocks for the private deployment |
| [0054](0054-accept-early-duplicate-authorization-rejection.md) | Accepted | Accept early provider rejection of duplicate Authorization fields |
