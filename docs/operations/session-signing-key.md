# FGA API backend framework-signing key contract

Last updated: 2026-08-28

Status: Google Cloud/Django candidate under proposed ADR 0033; no hosting or
managed-secret provider is selected, and hosted implementation is pending

## Scope

This contract preserves one provider-specific candidate for how the FGA API
backend obtains and validates Django's installation-wide `SECRET_KEY` before
serving the private administrative control plane. Django uses that setting for
framework cryptographic signing. The purpose-built FGA browser session accepted
by ADR 0039 does not sign, derive, or verify its opaque token with this key: its
database lookup key is the unsalted `SHA2-256` digest of the complete 256-bit
token. Signed-cookie sessions remain disabled; that does not make an arbitrary
or weak framework key acceptable.

The key is not the administrator's opaque 256-bit session cookie, the
session-bound CSRF value, the source-limiter HMAC key, an installation
credential, or a Flickr/provider secret. Those values remain independently generated,
stored, scoped, and rotated. The FGA group-submission worker receives neither
the administrative signing key nor Secret Manager authority to read it.

Django's [5.2 `SECRET_KEY` and `SECRET_KEY_FALLBACKS`
contract](https://docs.djangoproject.com/en/5.2/ref/settings/#secret-key)
requires a unique unpredictable secret, applies it to non-cache-backed
sessions and signing, refuses an unset key, and provides ordered fallbacks for
rotation. The FGA API backend adds an exact encoding and entropy floor because
Django intentionally accepts general strings and cannot know deployment
provenance.

## Secret generation and representation

Deployment automation generates exactly 32 bytes with Python's `secrets`
module or an equivalent operating-system-backed cryptographically secure random
generator, encodes them as canonical RFC 4648 base64url without padding, and
writes the value directly to the environment-specific Google Secret Manager
secret `fga-django-secret-key`. The canonical payload is therefore exactly 43
ASCII characters matching:

```text
^[A-Za-z0-9_-]{43}$
```

The payload contains only that value: no JSON wrapper, prefix, quote, padding,
line ending, comment, or surrounding whitespace. Production and preview use
different Google Cloud projects, secret versions, and random values. No FGA
component derives this key from a password, phrase, UUID, timestamp, hostname,
deployment ID, another secret, or deterministic seed.

The generator sends the payload to Secret Manager without printing it, writing
it to Terraform state, committing it, retaining a temporary file, or placing it
in a command argument, shell history, build log, Cloud Run environment value,
or CI output. Retained generation evidence contains only the generator/runtime
version, requested byte count, Secret Manager version resource name, UTC time,
and authorized deployment identity—not the value or a digest of it.

Encoding and decoded-length validation establishes a 256-bit capacity and
rejects common configuration mistakes. It cannot prove that the bytes were
random; the reviewed CSPRNG generation path and cloud audit event establish
that separate provenance.

## Exact version configuration

The FGA web Cloud Run revision receives these non-secret configuration values:

| Setting | Contract |
| --- | --- |
| `FGA_DJANGO_SECRET_KEY_VERSION` | Required full resource name ending in `/secrets/fga-django-secret-key/versions/<positive-integer>` |
| `FGA_DJANGO_SECRET_KEY_FALLBACK_VERSION` | Absent normally; during a planned rotation only, one different full resource name for the immediately preceding positive-integer version |

The project number/name in each resource must match the current deployment
environment. `latest`, a version alias, a bare secret name, an empty value, a
cross-project resource, more than one fallback, or the same primary and
fallback version is invalid configuration. Terraform records only these exact
resource names and grants the FGA web service account
`secretmanager.versions.access` on the required versions. The worker service
account has no access.

This follows Google Secret Manager's [production guidance to resolve and bind a
specific version](https://cloud.google.com/secret-manager/docs/rotation-recommendations)
instead of resolving `latest` inside a scaling workload. Adding a new secret
version alone cannot change a running or newly scaled FGA web revision.

## Fail-closed startup validation

Every FGA API backend process performs this work before its application server
accepts a request or reports ready:

1. Parse and validate the exact primary/fallback resource names without reading
   a secret.
2. Access each configured version through the official Secret Manager client
   and the FGA web runtime identity. Verify the response's payload CRC32C before
   parsing the value.
3. Require exactly 43 payload bytes and strict ASCII decoding. Reject any
   whitespace, padding, invalid alphabet byte, or additional content.
4. Append the one required `=` only in memory, perform strict base64url decode,
   and require exactly 32 decoded bytes.
5. Re-encode those bytes without padding and require an exact byte-for-byte
   match with the received payload. This rejects non-canonical encodings.
6. Require different decoded primary/fallback values when a fallback is
   configured.
7. Set Django `SECRET_KEY` to the canonical primary text and
   `SECRET_KEY_FALLBACKS` to either an empty list or a one-item list containing
   the canonical fallback text.
8. Erase mutable temporary byte buffers where the runtime permits, retain only
   the framework settings needed by the process, and expose no secret-derived
   diagnostic value.

A missing setting, access denial, unavailable Secret Manager dependency,
disabled/destroyed/missing version, checksum mismatch, malformed resource,
invalid payload, duplicate key, or unexpected fallback count is a startup
failure. The process emits one sanitized category such as
`session_signing_key_invalid`, never the resource name, payload, encoding
fragment, digest, decoded length, or exception text, and never becomes ready.
It does not generate a replacement, substitute a development default, fall
back to `latest`, retry another version, or defer validation until a request.

An already healthy process may continue with its in-memory exact version during
a transient Secret Manager outage; it does not poll or hot-swap. A new rollout
or cold start that cannot validate its configured versions fails, leaving the
last accepted Cloud Run revision serving traffic. Deployment automation treats
that condition as a failed rollout, not as permission to broaden secret access.

Development and tests use explicitly named, generated test keys that pass the
same parser. Production settings refuse placeholder literals, but no production
key-strength rule depends on a blacklist of example strings.

## Rotation and compromise

There is no calendar-only rotation requirement. Rotate for a concrete exposure,
personnel/authority change, algorithm/framework requirement, or tested
operational decision. Rotation never changes a version in place.

For a planned non-compromise rotation:

1. Generate and validate a new exact Secret Manager version in preview.
2. Deploy a candidate FGA web revision with the new version as primary and the
   immediately preceding version as the sole fallback. Prove a pre-cutover
   administrative session still validates and newly written session data uses
   the primary.
3. Promote that exact configuration to production, wait for the new revision
   to own all traffic, and prevent the old revision from creating more values
   under the old primary.
4. After the 24-hour absolute administrative-session lifetime plus a
   ten-minute rollout/clock margin, deploy with no fallback and prove an old-
   key fixture is rejected while a new session succeeds.
5. Only then disable the old version under the managed-secret retention policy.

At most one fallback exists, and it passes the same exact parser as the primary.
The bounded window follows Django's documented fallback mechanism without
turning old keys into an indefinite compatibility set or adding unbounded
signature-check overhead.

For suspected or confirmed key exposure, do not configure the exposed key as a
fallback. Generate and deploy a new primary, revoke every administrative
session in the FGA database, stop traffic to old revisions, and prove every
old-key/session fixture fails. Secret disablement and destruction follow the
incident and evidence-retention process; availability does not justify keeping
a compromised validation key.

## Required implementation evidence

The hosted implementation must supply build-bound tests and sanitized evidence
for:

- valid primary-only and primary-plus-one-fallback startup;
- exact numeric version binding and environment/project matching;
- missing/empty, access-denied, unavailable, disabled, destroyed, and checksum-
  mismatched Secret Manager responses;
- 31-byte and 33-byte decoded values; 42- and 44-character payloads; invalid
  ASCII/alphabet; padding; leading/trailing/interior whitespace; quotes; line
  endings; JSON; and non-canonical encodings;
- `latest`, named aliases, bare/cross-project resources, duplicate versions,
  duplicate decoded values, and multiple fallbacks;
- refusal to listen/report ready for every invalid case, with sanitized logs and
  no secret value, fragment, digest, resource name, or exception leakage;
- stable behavior across two independently started FGA API backend instances
  bound to the same exact version;
- planned rotation, fallback expiry/removal, and immediate compromise rotation;
- rejection of the prior signed/session fixtures after their applicable
  boundary; and
- denied worker-identity access to the signing-key secret.

Evidence is bound to the immutable FGA web image digest, dependency lock,
Django version, Terraform plan/apply identifiers, exact non-secret version
references, test manifest, and provider export. This architecture repository
contains none of those hosted artifacts and therefore records no executable
pass.
