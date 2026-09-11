# ADR 0048: Return the Flickr authorization target as JSON

Date: 2026-09-05

Status: Proposed

Review boundary: FGA localswim ticket #0097

## Context

The accepted administrative control-plane contract currently says that
`POST /api/v001/admin/flickr-connection/authorization` requires a JSON
request, an authenticated browser session, exact-origin validation, and the
session's `X-CSRF-Token` header, then returns `303 See Other` to Flickr.

Those requirements do not compose in an ordinary browser:

- an HTML navigation or form submission can follow a `303`, but cannot set the
  required custom header and does not submit the required JSON media type;
- a same-origin `fetch` can set the header and JSON body, but following the
  response attempts a cross-origin subresource fetch rather than a top-level
  navigation; and
- Fetch's `manual` redirect mode exposes an `opaqueredirect` response with
  status zero, no headers, and no body. Browser code therefore cannot safely
  read the `Location` value and initiate the required navigation.

This is an interoperability defect in an otherwise accepted contract. It must
be corrected before the operation's OpenAPI schema is closed; a hidden
browser-specific workaround would violate the principle of least surprise.

Flickr's OAuth documentation requires the application to present
`https://www.flickr.com/services/oauth/authorize` with the temporary request
token. It does not require the preceding application request to be an HTTP
redirect.

## Proposed decision

1. Retain
   `POST /api/v001/admin/flickr-connection/authorization`, its authenticated
   FGA browser session, recent Google reauthentication, exact-origin check,
   session-bound `X-CSRF-Token`, JSON request, five-minute single-use
   transaction, and all existing managed-secret and audit requirements.
2. Replace the `303` response from this API operation with `201 Created`,
   `Cache-Control: no-store`, and this closed JSON representation:

   ```json
   {
     "schemaVersion": 1,
     "authorizationTransactionId": "opaque-transaction-id",
     "authorizationUrl": "https://www.flickr.com/services/oauth/authorize?oauth_token=...",
     "expiresAt": "2026-09-06T00:00:00.000000Z"
   }
   ```

3. The request body contains only `schemaVersion: 1` and
   `expectedRevision` for the current Flickr-link representation. The server
   supplies owner, permission, callback, consumer-key, and transaction values.
4. Before top-level navigation, the FGA User UI parses the returned URL and
   requires exact scheme `https`, host `www.flickr.com`, port 443, path
   `/services/oauth/authorize`, no user information or fragment, and only the
   expected `oauth_token` query value. It then uses an ordinary top-level
   navigation. It never inserts the value as HTML or sends it to a third-party
   script.
5. The FGA API backend and FGA User UI treat the authorization URL as transient
   OAuth protocol data: no browser storage, service worker, analytics,
   telemetry, response-body capture, or arbitrary redirect target. Expiry,
   navigation, logout, or failure clears the in-memory reference.
6. The Flickr callback remains
   `GET /admin/flickr-oauth/callback`. Its successful or failed browser
   response may retain the existing `303` to a fixed same-origin review
   destination because that request is an actual top-level OAuth navigation,
   not a JSON `fetch`.
7. This decision narrowly amends the start-response requirement in the
   administrative control-plane and OAuth/account-lifecycle contracts. It does
   not change the callback, owner verification, permission check, staged-secret
   activation, or gate-resume boundaries.

## Consequences

- The unsafe API call uses ordinary same-origin JSON and CSRF protections.
- Cross-origin movement happens only as an explicit top-level navigation.
- The browser validates a small allowlisted URL shape instead of consuming an
  arbitrary server redirect.
- The authorization target briefly exists in JavaScript memory. It already
  exists in browser navigation and Flickr's OAuth URL; the no-store,
  no-third-party, and nonlogging boundaries remain required.
- The OpenAPI operation gains a truthful response schema and no longer models a
  redirect that the intended client cannot use.

## Alternatives considered

- **Submit an HTML form and follow the `303`:** rejected because a form cannot
  set `X-CSRF-Token` and would require a second CSRF/media-type convention for
  one operation.
- **Use `fetch` with automatic redirect following:** rejected because it is a
  resource fetch, not top-level browser navigation, and Flickr does not opt
  into FGA's CORS request.
- **Read `Location` from a manual redirect:** rejected because the Fetch
  standard exposes an opaque-redirect response without the header.
- **Open a server-selected arbitrary URL:** rejected because the UI can enforce
  Flickr's exact documented authorization origin and path before navigation.

## References

- [Fetch Standard: redirect modes and opaque-redirect responses](https://fetch.spec.whatwg.org/#concept-request-redirect-mode)
- [Flickr OAuth authorization flow](https://www.flickr.com/services/api/auth.oauth.html)

