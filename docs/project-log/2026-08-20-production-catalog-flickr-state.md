# Production catalog Flickr-state inspection

Date: 2026-08-20

Publication summary: a read-only schema inspection confirmed that
`AgRemotePhoto.photo` links through `Adobe_images.rootFile` to `AgLibraryFile`,
while `AgRemotePhoto.remoteId` holds the provider identifier. A catalog record
is a candidate-discovery clue, not proof of current public Flickr visibility.

An independently checked public Flickr photo was used for the historical
direct-upload probe. Reimporting a source created a different catalog-record
UUID, confirming that Lightroom photo UUIDs are catalog-local identifiers.
Source filenames, catalog UUIDs and local paths are omitted here. The public
probe requires ignored local configuration and still checks the exact selected
UUID before rendering or network access. The original private evidence remains
in the private architecture repository.
