# Claude architecture diagram reveal

On 2026-08-23, after the independent FGA architecture review was complete,
Terry supplied three equivalent exports of a Claude Opus 5 architecture diagram
dated 2026-08-19 in the transient directory `C:\Temp\FGA-Claude`:

| Artifact | SHA2-256 |
| --- | --- |
| `FlickrGroupAddr-Architecture-2026-08-19-8.5x14.drawio` | `E74FF6352D3087AA563D4E568CDBD616975EA675ED53BE8496FDF1FA83DFCF5B` |
| `FlickrGroupAddr-Architecture-2026-08-19-8.5x14.pdf` | `9DB102A6EE4ADE7950BD3375D4D97B54E49125776A1FA3E630F394BBFFD66F01` |
| `FlickrGroupAddr-Architecture-2026-08-19-8.5x14.png` | `AE143094424EF023F8117AE5808642D1A549BAE123EB3ED458F19544F9696AC2` |

The PNG was used for visual inspection and the uncompressed draw.io XML for
exact labels and the 32-step authentication flow. The supplied artifacts were
not copied into this repository. `C:\Temp` is transient, so the hashes identify
the reviewed versions if Terry later supplies a durable source location.

## Architecture stated by the diagram

- An FGA LrC plug-in reads Flickr photo IDs from the Lightroom Classic catalog.
- A single Cloudflare Worker serves device-link, Flickr OAuth, and `/api/v001/*`
  endpoints behind Cloudflare DNS and anycast routing.
- A ten-minute Device Link User Code Durable Object and an approximately
  fifteen-minute Flickr OAuth State Durable Object hold temporary linking and
  OAuth state.
- A browser obtains a cookie-based FGA session through Flickr OAuth, submits the
  user code, and approves the waiting device link. The FGA LrC plug-in polls with
  its device code, receives an FGA session ID, and stores it in the Lightroom
  plug-in credential store.
- Cloudflare D1 holds users, requests, and tokens; Worker Secrets holds Flickr
  application credentials plus token-encryption and session-signing keys.
- A nightly Workers Cron trigger starts retry logic that attempts to flush every
  queue with pending requests and stops a queue at its first throttle status.
- A browser client uses the same API with reduced capability; the diagram says
  ADR-18 ships the browser and plug-in in lockstep.

The diagram names `groups.pools.getGroups`, `photos.getAllContexts`, and
`groups.pools.add`. It shows no Flickr image-upload path. It also does not state
the queue partition key and insertion-order rule, retry timing, ambiguous-add
classification, moderator preflight, permanent pending-submission suppression,
or exact separation between browser-session and plug-in credential authority.
Those omissions may be resolved by the referenced but not-yet-supplied
`docs/architecture/DECISIONS.md`, ADR-18, or other source documents and must not
be treated as confirmed design defects until those sources are reviewed.

## Provisional comparison with the independent baseline

This is not yet an apples-to-apples comparison. The revealed artifact is one
diagram dated before the independent track began, while the independent track
has a complete architecture, ADRs, research evidence, and an owner-reviewed
eight-phase flow. The Claude design's referenced records must be reviewed before
classifying an omission in the diagram as an omission in that design.

The clearest independent convergence is the overall split: an FGA LrC plug-in,
hosted Flickr secrets and OAuth operations, durable hosted state, and background
group submission that continues after the Lightroom Classic host process exits.
Both tracks name documented Flickr group discovery, current-context reads, and
group-pool addition.

The clearest provisional divergences are:

- The Claude diagram devotes steps 1 through 31 to browser-assisted Flickr OAuth
  and device linking, then collapses all application behavior into step 32. The
  independent flow makes private installation activation short and decomposes
  selection, rendering, direct upload, durable handoff, and group submission.
- The Claude diagram appears to consume existing Flickr photo IDs from a
  Lightroom Classic catalog and shows no upload path. The independent FGA LrC
  plug-in is an original publish provider that renders and uploads the image.
- The Claude diagram selects Cloudflare Worker, Durable Objects, D1, Worker
  Secrets, and nightly Cron concretely. The independent baseline specifies
  component and persistence contracts without yet binding every hosted
  component to one provider.
- The Claude device-link flow supports browser-based onboarding and a browser
  client. The independent private MVP deliberately defers public, self-service,
  and browser/device-pairing flows and uses an administratively provisioned
  installation credential.
- The Claude retry worker runs nightly and stops a queue at its first throttle
  status. The independent FGA group-submission worker requests immediate
  progress, preserves independent `(FGA user, Flickr group ID)` FIFO lines, and
  records bounded jittered retry or probe times durably.
- The revealed diagram does not show the independent baseline's exceptionless
  fresh moderation preflight, permanent exact-pair blocks, or explicit
  ambiguous-delivery classification. Supporting Claude records may still define
  equivalent safeguards.

## Questions awaiting Terry or additional Claude sources

Terry supplied <https://github.com/FlickrGroupAddr/backend-api> as the original
Claude design repository and directed the next-session Codex to read every file
in it in full before revisiting this list. That repository was deliberately not
retrieved or inspected in the current session.

1. Is the original Claude repository available, especially
   `docs/architecture/DECISIONS.md`, ADR-18, and any queue or retry contract?
   The repository location is now known; the remaining question is what those
   complete sources establish.
2. Was the Claude design intentionally a group-submission companion to an
   existing Flickr publisher? If so, which published-collection record supplies
   the Flickr photo ID, and through which documented Lightroom SDK API may the
   FGA LrC plug-in read it?
3. Was public or multi-user operation a requirement from the beginning? That
   would explain why device linking and browser-session provisioning dominate
   the architecture.
4. What is the queue partition key and insertion-order rule behind “every
   queue”: user, group, `(user, group)`, or another identity?
5. Which Flickr result is the “first throttle status”; what scope does it pause;
   and how does the design classify pending moderation, unknown application
   codes, and an add response lost after possible delivery?
6. Is the FGA session ID placed in the browser cookie the same bearer credential
   returned to the FGA LrC plug-in, or are they separately scoped credentials
   that share a diagram label? What cookie attributes and API authorities apply?
7. Is `fga.com` shorthand in the numbered flow while
   `flickrgroupaddr.com` is the intended origin?

## Follow-up completed

The repository documentation review was completed on 2026-08-23 against pinned
commit `ea407553704aa7a950c341653b0e7d21073f271f`. A later full-repository review
covered all 152 tracked files and all 473 commits at that pin. Its complete
coverage record, evidence-based comparison, disposition of all seven questions,
and revised question/comment state are in
[`../research/2026-08-23-fresh-eyes-architecture-review.md`](../research/2026-08-23-fresh-eyes-architecture-review.md).

This section preserves the provisional diagram reading as historical evidence;
the linked full-repository review supersedes its questions and tentative
conclusions. The intermediate documentation-only review remains at
[`../research/claude-design-repository-review.md`](../research/claude-design-repository-review.md)
as historical provenance.

The source history was rewritten for privacy on 2026-08-24 under #0013 and
#0014. Commit `26b7070cb1092bb9fbac045ddd845884f6aa9ea4` is the public-safe
successor for every unaffected current-tree blob; the pinned identifier above
remains only as historical review provenance.
