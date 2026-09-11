# Vendored Lightroom dependencies

## dkjson 2.11

- Upstream: <https://dkolf.de/dkjson-lua/>
- Source: <https://dkolf.de/dkjson-lua/dkjson-2.11.lua>
- Released: 2026-07-27
- SHA2-256: `197cb50834c642f84b4cf99fe724932c50e6d9c92faec7ad89aa25e91df4d481`
- License: MIT; the complete copyright, permission, and warranty notice is
  retained in `dkjson.lua` and reproduced in the repository's
  `THIRD_PARTY_NOTICES.md`
- Local changes: none

The unmodified source is installed at the toolkit root as `../dkjson.lua`.
Lightroom's toolkit `require` function loads script names from that root and
does not resolve Lua modules inside subdirectories.

dkjson is a single-file, dependency-free JSON encoder/decoder supporting Lua
5.1 through 5.5. It replaces FGA's initial diagnostic-only JSON encoder and is
intended for both manifest output and future Flickr/service JSON responses.
