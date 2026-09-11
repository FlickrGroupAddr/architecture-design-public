# PNG size and fidelity experiment

Status: Complete historical experiment; public summary

Date: 2026-08-20

The FGA LrC diagnostic plug-in compared full-resolution PNG bit-depth/color-space
variants with a maximum-quality JPEG baseline. The tested 8-bit sRGB PNGs fit
the configured Flickr upload limit; the tested 16-bit variants did not. This
sample is not a guarantee about another image. Every actual render must be
checked against the configured byte limit before upload authorization.

The private Flickr round trip confirmed that the tested PNG Original was
retained byte-for-byte. Credentials, private photo IDs, original URLs, hashes,
source filenames, archive locations, capture metadata and per-photo observations
are omitted from this public summary and retained only in the private record.
No photo, preview, catalog or private probe report is included in this snapshot.

[ADR 0002](../decisions/0002-lossless-png-output.md) records the accepted
full-resolution 8-bit sRGB PNG decision. The
[diagnostic plug-in](../../lightroom/FGA%20Diagnostics.lrdevplugin/README.md) and
[round-trip procedure](../operations/flickr-roundtrip.md) preserve the tooling.
Historical probe authorization does not authorize another upload.
