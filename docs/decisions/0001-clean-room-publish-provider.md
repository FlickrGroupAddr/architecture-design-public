# ADR 0001: Build an original publish provider

Date: 2026-08-20

Status: Accepted; extended by ADR 0008 on 2026-08-23; licensing boundary
confirmed on 2026-08-26

## Context

FGA needs both control over Lightroom's rendered output format and the Flickr
photo ID needed for durable group submissions. Adobe's installed Flickr
publisher is a compiled binary and does not expose a supported extension point.
The SDK contains an old Lua Flickr sample. The current Adobe Developer Terms of
Use cover Developer Console downloads and Developer Tools including SDK files
and Sample Code. Their non-sublicensable, non-transferable grant and
object-code-only distribution boundary do not permit Adobe Lua source to be
copied into FGA's public MIT source.

A companion plug-in could discover remote IDs created by Adobe's publisher, but
would require reconciliation and would not allow PNG output through that
publisher.

## Decision

Implement a new Lightroom Classic publish provider from original FGA source,
using the documented SDK contracts and Flickr API. Do not copy or adapt the
Adobe Flickr sample implementation into tracked FGA source. The sample may be
used locally for development reference and testing only under Adobe's terms;
FGA implementation code remains independently written from the documented API
contract.

## Consequences

- FGA can expose PNG and own the complete upload-to-group-intent handoff.
- The project has a defensible MIT licensing boundary.
- FGA must implement more publisher behavior and OAuth integration itself.
- Compatibility with Adobe's existing Flickr publish collections is not
  automatic; migration or coexistence may be considered later.

## Alternatives considered

- **Patch/extend Adobe's installed provider:** no editable source or documented
  extension point is available.
- **Fork the SDK sample:** rejected because its OAuth implementation is obsolete
  and Adobe's current distribution grant is incompatible with publishing the
  Lua source under MIT.
- **Companion plug-in:** useful if group queuing alone were the goal, but it does
  not solve PNG publishing and lacks a reliable cross-provider completion hook.

## Later scope extension

ADR 0008 retains this original publish-provider decision and adds a separate
existing-photo queueing path to the same FGA LrC plug-in. Photos uploaded
through another path are therefore first-class add-only queue inputs, but they
do not pass through this ADR's render and upload flow.
