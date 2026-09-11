# Project log: 2026-08-20

## Starting point

The repository began empty on branch `main`. It was moved from a NAS share to a
local SSD after Windows sandbox elevation and PowerShell execution problems.
PowerShell 7.4.19 was installed and verified from a standard shell.

The licensed Lightroom Classic 15.3 SDK was downloaded from Adobe Developer
Console for use with installed Lightroom Classic 15.5. The SDK payload is local
only and excluded from Git.

## Initial problem statement

Flickr groups throttle each member's photo submissions using group-specific
limits that can span days, weeks, or months. The photographer wants to select
groups while publishing from Lightroom and have a hosted service eventually add
the photo to every selected group in FIFO order per `(user, group)`.

New work should be attempted immediately when the relevant queue is empty. A
nightly serverless trigger should revisit nonempty queues and advance each until
Flickr reports its submission limit. Successful addition and pending moderation
are the desired terminal outcomes.

The project scope was expanded to include uploading Lightroom-developed RAW
photos as losslessly compressed PNG rather than JPEG when practical.

## Findings captured

- Flickr accepts PNG and JPEG, retains the exact upload as the original, rejects
  RAW, and currently limits photos to 200 MB.
- Flickr group posting limits are not returned by the group-list API; error 5
  from `flickr.groups.pools.add` is the authoritative throttle signal.
- Flickr group-add errors distinguish added, already added, pending moderation,
  already pending, throttled, transient, authentication, and ineligible states.
- Flickr authentication is OAuth 1.0a using HMAC with SHA1-160.
- The Lightroom 15.3 SDK permits PNG output from custom export/publish providers.
- Adobe's installed Flickr provider uses OAuth but is a compiled binary. The SDK
  Flickr sample is separate, old, and explicitly lacks OAuth support.
- The license governing Adobe sample-derived code has not been located, so the
  current recommendation is an original FGA implementation against documented
  SDK interfaces.
- A durable database partition per `(user, group)` can provide FIFO behavior
  without provisioning one physical cloud queue per tuple.

## Current direction

The proposed system is an MIT-licensed Lightroom publish provider plus a hosted
API, database, immediate worker trigger, and nightly scheduler. Authentication
and large-file upload boundaries remain open and require prototypes.

See the repository README and linked documents for the maintained project
record. Future sessions should update the relevant document and project log when
research or decisions change.
