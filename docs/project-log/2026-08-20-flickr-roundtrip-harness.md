# Flickr round-trip harness

Date: 2026-08-20

The project owner offered an existing Flickr application key and secret for
end-to-end API testing. The values must remain in the ignored local file
`.secrets/flickr.json`; OAuth tokens are stored beneath `.secrets/` as well.

Rather than implement OAuth 1.0a and multipart request signing, the spike uses
the mature `flickrapi` 2.4.0 package in an uv-managed, fully pinned virtual
environment. The harness:

- requests only OAuth `write` permission;
- verifies the authenticated account resolves to the authorized public profile
  before changing Flickr state;
- uploads one PNG as private, safe, and hidden from search;
- checks `flickr.photos.getInfo` for `originalformat="png"`;
- obtains the authenticated Original URL with `flickr.photos.getSizes`;
- downloads and hashes the original without storing a second local copy; and
- writes a local ignored report with byte counts and SHA2-256 values.

The dedicated Flickr upload endpoint retains its native XML-style response.
All ordinary Flickr REST calls use parsed JSON, matching the project owner's
preference and the likely hosted-service interface.

The harness does not request OAuth `delete` permission, publish the test image,
or add it to a group. The private photo remains for deliberate manual cleanup.
This follows least privilege and ensures an upload that partially succeeds is
not made difficult to find.
