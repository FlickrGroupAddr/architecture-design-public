# Flickr PNG round-trip procedure

This procedure validates the final unresolved PNG assumption against the
authorized public test profile at <https://www.flickr.com/photos/terryott/>.
It uses the mature `flickrapi` library rather than implementing OAuth 1.0a or
Flickr's multipart-upload signature rules in project code. Ordinary Flickr
REST responses are requested as parsed JSON; only the dedicated upload endpoint
retains its native XML-style response.

The test requests OAuth `write` permission, uploads one photo privately, checks
that Flickr reports `originalformat="png"`, downloads the authenticated
Original size, and compares byte count and SHA2-256 hash with the local file.
It does not add the photo to groups or make it public.

## Local setup

The actual credential and OAuth-token files are ignored by Git. Put the Flickr
application values in `.secrets/flickr.json`:

```json
{
  "api_key": "...",
  "api_secret": "..."
}
```

Never paste either value into chat, source, command-line arguments, screenshots,
or a tracked file. The repository contains only
`config/flickr.example.json`.

Create or synchronize the locked Python environment when needed:

```powershell
uv python install
uv sync --locked
```

## Execute

Use the smallest representative 8-bit sRGB export first:

```powershell
uv run --frozen python scripts\flickr-roundtrip.py `
  --image '<approved-local-export.png>'
```

On first use, the library opens Flickr in the browser and requests `write`
authorization. The script verifies the authorized account's profile URL before
uploading. A sanitized local report is written beneath `artifacts/`, which is
also ignored by Git.

The private photo is deliberately retained after verification. Flickr requires
the broader OAuth `delete` permission for API deletion, and this test does not
request more authority than it needs. Record sanitized results in the research
document, then remove the photo manually or perform a separately authorized
cleanup.

## Direct-upload signing probe

The companion probe separates OAuth signing from image transmission, then
checks exact-request replay and changed metadata:

```powershell
uv run --frozen python scripts\flickr-signed-upload-probe.py `
  --config .secrets\flickr.json `
  --image '<approved-local-export.png>'
```

The valid case creates one private Flickr photo. Replay and tamper cases omit
the image bytes and cannot create additional photos. The probe never prints or
records Flickr credentials, OAuth tokens, or the signed authorization header.

## Lightroom multipart probe

The Lightroom probe uses a one-request HTTP signer bound only to IPv4 loopback.
The signer holds the Flickr credentials, validates the authorized profile, and
returns an upload URL, exact private-upload metadata, and OAuth authorization
header in memory. It never receives image bytes.

Start it from the repository root:

```powershell
uv run --frozen python scripts\flickr-signing-probe-server.py `
  --config .secrets\flickr.json
```

Wait for the `Ready for one Lightroom signing request` message. The process
handles one request and then stops, minimizing the lifetime of the unauthenticated
development-only loopback endpoint.

Configure the ignored `DirectUpload.local.json` as described in the diagnostic
plug-in README. The command checks the exact configured photo UUID. Independently
verify the public page without Flickr authentication before configuring it;
source filenames and catalog UUIDs belong only in the ignored local file.
Select that photo and choose **Library → Plug-in Extras → Test Direct Flickr
Upload from Public Photo**. This historical procedure does not authorize a new
live upload.

The FGA Diagnostics plug-in asks the Lightroom Classic rendering engine for a
temporary full-resolution 8-bit sRGB PNG and streams the resulting file directly
to Flickr with `LrHttp.postMultipart`. Success produces one private,
search-hidden Flickr duplicate and displays the returned Flickr photo ID. The
temporary render is deleted after the command; the private Flickr duplicate is
retained for manual cleanup because the token has `write`, not `delete`,
permission.
