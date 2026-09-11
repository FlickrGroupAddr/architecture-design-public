# Lightroom diagnostic and Lua toolchain

Date: 2026-08-20

FGA gained its first executable project code: an original, development-only
Lightroom Classic plug-in that renders the selected-photo PNG/JPEG test matrix.
This is intentionally separate from the eventual Flickr publish provider.

The plug-in:

- reads the active catalog's target photos;
- asks for an output parent directory and confirms the potentially large job;
- renders six PNG combinations (8/16 bits per channel across sRGB, Adobe RGB,
  and ProPhoto RGB) plus a quality-100 sRGB JPEG baseline;
- does not resize, sharpen, watermark, upload, modify, or delete photos;
- records render timing, paths, sizes, errors, and source metadata in JSON; and
- can be canceled between renditions.

A companion PowerShell analyzer computes streaming SHA2-256 hashes and uses
ExifTool, when installed, to record image/profile metadata without asking
Lightroom's Lua runtime to hold complete PNG files in memory.

The intended Lightroom machine is a 64 GB travel laptop and the project is
expected to have one user. Low desktop memory consumption is therefore not a
design priority; future plug-in work should favor simplicity over elaborate
streaming or buffering schemes. Hashing remains in the companion analyzer
because Lightroom's SDK only provides MD5 over an in-memory string, whereas
PowerShell provides SHA2-256 directly. Reduced Lua memory use is merely a side
benefit of that choice.

Lua Language Server 3.18.2 and the official Luacheck 0.23.0 Windows executable
were installed per-user. The repository now carries strict Lua 5.1 settings and
a single check script that runs LuaLS, Luacheck, and Adobe's SDK compiler. The
initial implementation passed with zero LuaLS diagnostics, zero Luacheck
warnings/errors, and clean Adobe Lua 5.1 syntax compilation.
