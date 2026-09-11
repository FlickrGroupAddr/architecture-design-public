# Photography test-data handling

Last updated: 2026-08-27

## Source catalog

The owner's working Lightroom Classic catalog and all referenced photographs
are private, read-only research inputs. Its location and inventory are kept
outside this public snapshot. Never copy a catalog, preview or private image
into Git or treat it as generally available test data.

## Default classification

Everything in the catalog is highly sensitive and private to Terry and Sol by
default, including previews, filenames, filesystem paths, titles, captions,
keywords, people, locations, capture data, and the image content itself.

An Adobe Flickr publish record or stored Flickr photo ID is evidence only that
a photo may have been published. It is not sufficient evidence that the photo
is currently public.

## Public verification rule

A catalog photo may be used as public test data only when all of these are true:

1. The catalog associates it with a Flickr photo ID.
2. The exact photopage at
   `https://www.flickr.com/photos/terryott/<Flickr photo ID>/` is accessible
   without Flickr authentication.
3. The returned public page identifies the same photo, rather than a redirect,
   missing-photo response, private-photo response, or unrelated asset.
4. The public URL and verification date are recorded with the admitted test
   artifact.

Private or search-hidden photos created by FGA probes do not satisfy this rule.

A purpose-built synthetic image generated without reading the catalog or a
personal photograph is a separate disposable test class. It may be made public
only for an explicitly authorized, bounded Flickr integration probe whose
procedure records the external mutations, cleanup failure mode, and retained
resource. Synthetic status never authorizes use of a historical or personal
photo and does not make a probe result a Flickr platform guarantee.

Terry tightened this boundary on 2026-08-27 after a public synthetic fixture
reached follower feeds. FGA test, diagnostic, and support workflows keep a
fixture private whenever private visibility can answer the actual requirement.
Public publication requires an exact public-only need and Terry's explicit
approval immediately before upload after disclosure of follower/feed exposure,
the minimum public interval, and cleanup. An unavoidably public fixture becomes
private immediately after evidence capture and is verified inaccessible without
authentication. Retained-public is never the default cleanup choice.

The annual FGA Diligence procedure is one such standing, bounded
authorization. Each invocation may create at most one new purpose-built
synthetic public photo, submit it only to the owner-controlled
[FlickrGroupAddr Diligence](https://www.flickr.com/groups/14968939@N22/) group,
and retain the photo and pool membership indefinitely as operational evidence.
The procedure does not authorize public use of catalog content, another Flickr
group, automated pool removal, or Flickr photo deletion.

Ticket #0067 has a separate one-photo authorization for its disposable-catalog
association spike. The admitted fixture is:

- `lightroom/FGA Diagnostics.lrdevplugin/catalog-association-fixtures/catalog-association-0067.png`;
- a 160 by 120 pixel, 8-bit RGB PNG containing only deterministic geometric
  pixels;
- 398 bytes with SHA2-256
  `a64d5bfa01b27dcb6772b388baaef4e9e6289886bd40f2a8e26c573f65014968`;
  and
- reproducible with
  `uv run --frozen python -m scripts.generate_catalog_association_fixture`.

Terry authorized creation and use of this purpose-built synthetic fixture on
2026-08-26. Ticket #0067 may upload it publicly exactly once through Adobe's
Flickr plug-in in the disposable Lightroom Classic catalog used for the spike.
The upload must be Safe, classified as a photo, and left out of Flickr groups
and albums. It remains public and ungrouped for the duration of the spike so
restart and association behavior can be observed. The ticket must record the
exact Flickr photo ID, photopage URL, upload time, and final retained or private
state before review. This authorization does not permit another upload, a
production-catalog write, pixel replacement, Flickr deletion, or any group or
album mutation.

The authorized upload completed exactly once on 2026-08-27 at
`2026-08-27T15:13:13-04:00`. Flickr assigned photo ID `55491872256` and
photopage `https://www.flickr.com/photos/terryott/55491872256/`. After the final
catalog-only association removal, an unauthenticated request returned HTTP 200
at that exact URL and Flickr's oEmbed response identified a public photo titled
`catalog-association-0067.jpg`. Terry then directed deletion and clarified the
standing private-by-default test boundary. The exact owner/title-verified photo
was immediately changed to private; a subsequent unauthenticated request
returned HTTP 403. The existing integration-test OAuth grant lacks delete
permission and was not broadened. Terry deleted the exact private fixture
through Flickr's UI and confirmed its absence from his logged-in Photostream,
which includes his private uploads. No album or group addition occurred. The
one-upload authorization is consumed and does not permit another copy.

## Handling requirements

- Inspect the catalog read-only and avoid opening it with a second Lightroom
  writer.
- Keep intermediate query results outside Git and delete them when no longer
  needed.
- Do not print or paste unverified filenames, paths, metadata, or image content
  into logs, chat, commits, or issue text.
- Query the minimum fields needed to find Flickr publication candidates.
- Verify public status before copying or transforming candidate image content.
- Commit only the minimum public artifact needed for a reproducible test.
