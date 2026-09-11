# Architecture session closeout

Date: 2026-08-20

## Completed

- Moved the working repository from NAS storage to the local SSD and restored a
  reliable non-administrator PowerShell, Git, uv, Lua, and Python workflow.
- Established the engineering defaults, cryptographic naming convention,
  Lightroom entropy boundary, photography-data privacy boundary, current-
  Lightroom-only target, uv workflow, and sanitized `C:\Temp` diagnostic
  handoff in `AGENTS.md`.
- Selected an original MIT-licensed Lightroom publish provider rather than
  extending Adobe's compiled Flickr provider.
- Established full-resolution 8-bit sRGB PNG as the preferred output. The
  representative PNG matrix remained below Flickr's 200 MB limit, and Flickr
  returned a tested PNG original byte-for-byte.
- Verified a public Flickr fixture independently before using it with the
  production catalog. The current-root Lightroom photo UUID is recorded in the
  privacy-safe project log and enforced by the diagnostic probe.
- Proved the service-signed upload boundary first with a secret-free Python
  sender and then end to end from Lightroom Classic 15.5 through
  `LrHttp.postMultipart`.
- Confirmed through Flickr's authenticated API that the Lightroom upload was
  retained as PNG and was private, not friend-visible, and not family-visible.
  Its private Flickr photo ID is intentionally absent from Git.
- Accepted ADR 0005: the hosted service signs exact Flickr metadata while
  Lightroom streams image bytes directly to Flickr. The service retains the
  Flickr consumer secret and OAuth token secret.
- Added a regression test for `requests-oauthlib` returning an authorization
  header as bytes and hardened Flickr XML parsing with `defusedxml`.
- Configured Ruff formatting/linting and strict Pyright analysis, including
  `pyright-langserver`. The Python and Lua quality gates are green.
- Drafted the plug-in/service semantics and adopted `/api/v001/*` as the hosted
  API prefix.

## Current development state

- Lightroom Classic: 15.5; latest downloaded SDK: 15.3.
- Diagnostic plug-in build: `0.2.0.4`.
- Python: CPython 3.14 managed through uv.
- Repository branch: `main`.
- The last functional checkpoint is the successful Lightroom direct Flickr
  upload. The production publish provider and hosted service do not yet exist.
- One private, search-hidden Flickr duplicate from the successful probe remains
  available for manual cleanup. Do not add its Flickr photo ID to the public
  repository.

## Resume point

Resume semantic review of `docs/plugin-service-contract.md`; do not write the
OpenAPI document yet. Natural intent idempotency was refined and accepted as:

```text
(Flickr photo ID, Flickr group ID)
```

Flickr photo information supplies the owner NSID, so FGA user identity remains
validated stored context for authorization and queue partitioning rather than
part of the minimal unique key. Review the complete interaction sequence next,
followed by the three provisional endpoints, error behavior, and deferred
scope. Encode `openapi/fga-service.yaml` only after the prose semantics are
agreed.

## Plan from here

1. **Review the prose contract.** Natural idempotency is accepted. Review the
   interaction sequence next, followed by endpoint responsibilities, errors,
   and deferred scope. This is the current phase.
2. **Encode the approved contract.** Create OpenAPI 3.1 under
   `openapi/fga-service.yaml`, sanitized request/response fixtures, and contract
   validation tests. OpenAPI becomes the machine-readable source of truth.
3. **Select the hosting stack.** Compare current provider cost and capabilities
   for the private single-user deployment, then record the API, database,
   scheduler, worker, and managed-secret choices in an ADR.
4. **Implement the service core.** Build the authenticated API, relational
   intent/partition model, transactional natural idempotency, per-partition
   lease, FIFO worker, immediate trigger, and nightly scheduler. Test the Flickr
   result-state table and crash/retry behavior independently of Lightroom.
5. **Build the production Lightroom publish provider.** Implement the publish
   service definition, group-selection experience, PNG rendering and size
   preflight, service-signed direct upload, Lightroom remote-ID handling, local
   outbox, and durable group-intent handoff.
6. **Exercise the complete system.** Run contract and integration tests, then a
   controlled end-to-end publish against the private Flickr deployment. Verify
   FIFO behavior, throttling, moderation terminal states, retry recovery,
   observability, and secret/log hygiene before calling the MVP usable.

The exact next step is step 1: review the complete plug-in/service interaction
sequence from group discovery through durable intent acceptance.

## Commands

Run the complete local quality gates from the repository root:

```powershell
.\scripts\check-lua.ps1
.\scripts\check-python.ps1
```
