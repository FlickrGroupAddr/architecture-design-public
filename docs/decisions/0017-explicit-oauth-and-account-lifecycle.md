# ADR 0017: Separate local disconnect, Flickr permission removal, and retained safety state

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-31; private replacement availability and
provider-version requirements amended by [ADR 0052](0052-evaluate-paused-native-credential-replacement.md)
on 2026-09-11

## Context

The private deployment gives the FGA API backend an OAuth 1.0a token and token
secret with Flickr `write` permission. That authority is broader than one group
addition. A complete lifecycle must stop future use, repair a revoked grant,
dispose of local secret material, tell Terry what remains authorized at Flickr,
and preserve the records that prevent repeated moderated submissions.

As checked on 2026-08-26, Flickr's OAuth documentation defines request-token, authorization,
access-token, and token-check operations. The current official API method index
does not list an application-side access-token revocation method. Flickr's
privacy policy instead directs the account owner to remove an application's
permission from Sharing & Extending settings. Calling local secret deletion
“OAuth revocation” would therefore overstate what the FGA administrative
control plane proved.

The browser control plane also creates server-side FGA sessions. Terry needs a
way to see and terminate those sessions without conflating them with Flickr,
Google Account session, or FGA installation credentials.

## Decision

The FGA database maintains one revisioned Flickr-link record with exhaustive
`unlinked`, `linked`, `relink_required`, `disconnecting`, and `disconnected`
states. Only a current `linked` revision with no replacement pause may resolve
its exact active managed-secret generation. The provider-versioned path uses
an exact provider version; ADR 0052's private native candidate instead checks
the generation inside the returned token-pair bundle against durable authority.
Unknown states, historical generations, provider object names, and cached values
grant no authority.

Link or relink requires recent owner authentication, one single-use Flickr
OAuth transaction, a fresh documented token check, the immutable expected
Flickr owner NSID, and at least `write` permission. In the provider-versioned
path, stage a new version before database activation and then delete the old
version. ADR 0052 permits the private native candidate to pause new operations,
replace one bundle, and activate only its matching generation; interruption may
require repair or another relink rather than automatic rollback to the old
grant. Relinking never changes Flickr identity, clears safety history, or
automatically resumes ADR 0013's write gate.

A definitive Flickr result `98` or `99` changes the still-current link to
`relink_required`, removes active local authority, and pauses its user gate. A
transient or malformed result is not proof of revocation. A stale in-flight
result cannot disable a concurrently activated revision.

Explicit disconnect requires recent authentication, CSRF/origin checks, the
expected link revision, and confirmation of the exact Flickr owner NSID. One
database transaction pauses the user gate, removes active secret authority,
sets `disconnecting`, invalidates outstanding Flickr authorization
transactions, and appends the audit evidence. Managed-secret deletion then
moves the exact revision to `disconnected`; deletion failure remains visibly
fail-closed in `disconnecting` and retries without restoring authority.

The UI reports local credential deletion, stopped FGA operations, and Flickr
permission as three independent facts. In the current contract it directs
Terry to Flickr's Sharing & Extending settings for **Remove Permission** and
reports `owner_action_required`. It never screen-scrapes Flickr or claims remote
revocation. A future `confirmed_removed` state requires a newly documented and
tested Flickr proof.

The FGA administrative control plane provides bounded session inventory,
recent-authenticated revocation of one other session, atomic revocation of all
other sessions against a session-set revision, and logout of the current
session. These operations revoke only FGA server-side sessions; confirmations
state that Google Account sessions, the Flickr grant, and installation
credentials are separate.

The private MVP exposes no self-service FGA account-deletion route. Disconnect,
relink, and every credential/session revocation retain permanent exact-pair
submission blocks, dispatch/ambiguity evidence, intent history, upload
bindings, gate events, and administrative audit. Whole-deployment erasure is a
decommissioning operation whose confirmation must warn that deleting the FGA
database destroys its moderator-protection memory. Public/multi-user account
deletion requires a separate accepted privacy and abuse design before launch.

The detailed route, sequencing, concurrency, UI, and conformance requirements
are in the
[OAuth grant, administrative-session, and account lifecycle](../oauth-and-account-lifecycle.md).

## Consequences

- The FGA administrative control plane can immediately disconnect official
  hosted components and delete their local secret without pretending Flickr
  has removed its grant.
- Credential replacement is atomic from the FGA database's perspective and an
  old failure cannot race a new grant into `relink_required`.
- Terry must complete a second owner-controlled action at Flickr. This is less
  convenient than a one-click claim, but it matches the documented interface.
- Permanent moderator-protection evidence survives credential churn and
  prevents same-owner relink from becoming resubmission amnesty.
- Session inventory and revocation add a small database read/mutation surface
  but avoid a custom browser/device identity system.
- The private deployment does not offer routine account erasure. Its explicit
  decommissioning boundary avoids silently weakening retained safety state.

## Alternatives considered

- **Call local secret deletion “revoke”:** rejected because it proves only
  loss of local capability, not Flickr-side permission removal.
- **Screen-scrape Flickr's account page:** rejected because it would rely on an
  undocumented UI contract, mishandle Terry's Flickr session, and violate the
  documented API boundary.
- **Treat any Flickr failure as external revocation:** rejected because
  transport, temporary, and malformed results do not prove the grant changed.
- **Automatically resume the write gate after relink:** rejected because a
  grant replacement does not prove that every cause of the paused revision was
  repaired.
- **Delete intent and suppression history on disconnect:** rejected because a
  later same-owner relink could repeat a submission that a moderator already
  rejected or whose prior delivery was ambiguous.
- **Add private-MVP web account deletion:** rejected because there is no
  self-signup account, and safe full erasure is a deployment decommissioning
  workflow rather than a routine application mutation.
