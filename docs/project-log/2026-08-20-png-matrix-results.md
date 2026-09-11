# Lightroom PNG matrix results

Date: 2026-08-20

The diagnostic plug-in completed its first real Lightroom Classic 15.5 run
against the three representative Canon EOS R5 RAW files. It produced all 21
expected outputs with no errors in 159 seconds and used 2.63 GiB of local disk.

The experiment established a clear local boundary:

- 8-bit PNG ranged from 51.52 to 78.87 MiB and every sample fits Flickr's
  stated 200 MB limit;
- 16-bit PNG ranged from 219.23 to 237.32 MiB and every sample exceeds the
  limit;
- maximum-quality JPEG ranged from 24.03 to 37.37 MiB; and
- the 8-bit sRGB PNG was 2.11–2.26 times its corresponding JPEG size.

ExifTool confirmed full dimensions, requested bit depths, and embedded color
profiles. The portrait input was emitted as 5464×8192 pixels without depending
on an orientation tag. SHA2-256 hashes were recorded for every output.

The provisional default is full-resolution 8-bit sRGB PNG. This is not yet the
final PNG decision: a Flickr API upload, `originalformat` check, authenticated
original download, and hash comparison remain outstanding.

The first analyzer run exposed a Windows path-separator mismatch between
ExifTool's `SourceFile` values and PowerShell's file paths. The analyzer now
normalizes both sides before joining metadata. Local matrix directories and
Lightroom catalog databases are ignored by Git.
