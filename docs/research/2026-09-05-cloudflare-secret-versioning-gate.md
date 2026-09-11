# Cloudflare immutable-secret-version gate

Date: 2026-09-05

Status: Complete provider-gate evidence for FGA localswim ticket #0104

Authority: Evidence and recommendation, not an architecture decision. Accepted
[ADR 0017](../decisions/0017-explicit-oauth-and-account-lifecycle.md) remains
authoritative unless Terry explicitly amends it.

Current direction update, 2026-09-06:
[ADR 0050](../decisions/0050-select-cloudflare-and-evaluate-native-storage-first.md)
records Cloudflare as selected and Durable Objects/D1 as the first storage
evaluation, with RDS PostgreSQL as
fallback. The dated findings and recommendations below remain evidence, not a
current provider-selection veto. Accepted
[ADR 0052](../decisions/0052-evaluate-paused-native-credential-replacement.md) on 2026-09-11
now permits evaluating a paused native bundle with an application generation
and repair after interruption. The selector finding below remains correct for
the original exact-provider-version contract; it does not prove the amended
candidate impossible or supply a native hosted pass.

Bounded proof update, 2026-09-11: the [paused native lifecycle](https://github.com/FlickrGroupAddr/api-cloudflare/blob/8d2cd48a7417caca3c3a6e66d8c3ff3e427398c9/docs/research/2026-09-11-native-secret-lifecycle-proof.md)
passed 29 hosted cases with all fixture cleanup confirmed. Its application
generation checks and correlated retirement implement the accepted alternative
under ADR 0052; they do not add a provider VersionId selector. The historical
result below remains about the original provider-versioned contract.

## Result

Cloudflare Secrets Store does not satisfy the accepted Flickr credential
lifecycle. The documented Cloudflare interface binds a Worker to a secret by
`store_id` and mutable `secret_name`; runtime code can only call `get()` on that
binding. It exposes no immutable secret-version identifier that the FGA
database can store and later ask the FGA API backend or FGA group-submission
worker to retrieve exactly.

This is a failed mandatory Cloudflare gate, not a failed live deployment test.
No Cloudflare account, Worker, secret, AWS resource, RDS instance, or production
data was mutated. A live spike cannot prove a selector that is absent from the
complete documented management, binding, and runtime surfaces.

The absence conclusion is an inference from those documented surfaces. It
should be reconsidered if Cloudflare adds an immutable version resource and a
runtime API that retrieves an exact version chosen at request time.

## Required lifecycle versus the native interface

| Accepted requirement | Cloudflare Secrets Store evidence | Gate result |
| --- | --- | --- |
| Stage a new immutable Flickr token/token-secret version before activation | Creating a distinct secret creates a distinct object, but editing a secret replaces its value for every consuming service. There is no documented subordinate version resource. | Not met natively |
| Store one exact inactive or active version reference in the FGA database | A secret has an object ID, but a Worker binding names `store_id` and `secret_name`, not the object ID or a version ID. | Not met |
| Retrieve exactly the FGA-database-selected version at runtime | The bound value exposes parameterless `get()`. Runtime code cannot supply a secret ID or version ID. | Not met |
| Activate with an FGA-database compare-and-set after validation | A new secret name must first be added as a deployed Worker binding. Secret creation, Worker-version creation/deployment, and the FGA database compare-and-set are separate control-plane operations. | Requires a custom deployment coordinator |
| Keep the old version addressable until the activation outcome is known, then delete it | A distinct old secret object can be retained, but only bindings already included in a deployed Worker version are addressable to that runtime. | Not met for dynamic relink without deployment |
| Give the FGA API backend and FGA group-submission worker separate least-privilege identities | Separate Worker services can receive different bindings and database authority. | Feasible, but it does not repair version selection |

Cloudflare's documented edit operation is especially incompatible with the
contract: replacing a value affects every service using that secret. Treating a
mutable name as “current” would move credential authority out of the FGA
database and recreate the forbidden `latest` lookup.

Primary Cloudflare sources, retrieved 2026-09-05:

- [Workers integration and binding shape](https://developers.cloudflare.com/secrets-store/integrations/workers/)
- [Secret creation, duplication, replacement, and deletion](https://developers.cloudflare.com/secrets-store/manage-secrets/how-to/)
- [Secrets Store API](https://developers.cloudflare.com/api/resources/secrets_store/)
- [Workers binding API types](https://developers.cloudflare.com/api/typescript/resources/workers/)
- [Secrets Store access control](https://developers.cloudflare.com/secrets-store/access-control/)

## Why the apparent workarounds do not pass

### One new secret name per credential revision

This can preserve old bytes, but the new name is not available to running code
until a binding for that name is saved in a Worker version and deployed. An
OAuth relink would therefore need an administration service with Secrets Store
write and Workers script/deployment authority, plus custom recovery across
secret creation, Worker deployment, and the FGA database compare-and-set. That
is a self-modifying deployment system, not a native secret-version lifecycle.
It also turns every credential change into an application deployment.

### One Worker version per credential revision

A Worker version captures code, assets, bindings, and configuration. A
deployment chooses which Worker version receives traffic; an FGA database row
cannot select a historical Worker version's secret during a request. Traffic
rollout is therefore not an exact secret lookup, and it couples credential
activation to application release and rollback.

### Encrypt credentials in D1 or RDS

The legacy Cloudflare prototype at commit
`64a900faecb3cde303c8b0441164e91982a2691f` chose this route. It encrypts Flickr
tokens with application-owned AES-GCM code in `src/crypto/tokens.ts` and stores
the ciphertext in D1. Its key-rotation document proposes a timestamped JSON
keyring in Worker secrets but states that the keyring is not implemented. It
explicitly rejected per-user Secrets Store objects because of the 100-secret
account limit.

That prototype is useful negative evidence, not a conforming implementation.
Adopting it would reopen ADR 0017 and make the FGA hosted components responsible
for cryptographic key storage, key rotation, re-encryption, partial-failure
recovery, and old-key retirement. Ticket #0104 explicitly excludes that custom
application-encryption bridge from the Cloudflare acceptance gate.

Prototype sources:

- [Legacy credential decision](https://github.com/FlickrGroupAddr/backend-api/blob/64a900faecb3cde303c8b0441164e91982a2691f/docs/architecture/DECISIONS.md)
- [Legacy key-rotation design](https://github.com/FlickrGroupAddr/backend-api/blob/64a900faecb3cde303c8b0441164e91982a2691f/docs/architecture/KEY-ROTATION-NOTES.md)
- [Legacy AES-GCM implementation](https://github.com/FlickrGroupAddr/backend-api/blob/64a900faecb3cde303c8b0441164e91982a2691f/src/crypto/tokens.ts)

## Conventional conforming comparison

AWS Secrets Manager creates versions when a secret value changes and returns
the exact version requested through `GetSecretValue.VersionId`. Staging labels
support current, pending, previous, and project-defined lifecycle states. The
FGA database can remain authoritative by storing an exact `VersionId`, while
separate Lambda execution roles receive only the secrets and actions each
component needs.

The implementation must deliberately retain every still-referenced version:
AWS can eventually remove sufficiently old, unlabeled versions after a secret
has more than 100 versions. FGA's accepted flow already bounds that set by
staging one candidate, activating it with an FGA-database compare-and-set, and
deleting the replaced version after the outcome is durable. Labels or an
equivalent retention check must protect every version during that interval.

Primary AWS sources, retrieved 2026-09-05:

- [Secrets and immutable versions](https://docs.aws.amazon.com/secretsmanager/latest/userguide/whats-in-a-secret.html)
- [`GetSecretValue` exact `VersionId` retrieval](https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html)
- [Rollback by moving staging labels](https://docs.aws.amazon.com/secretsmanager/latest/userguide/roll-back-secret.html)

Google Secret Manager also documents exact numbered-version access, but placing
the hosted compute on Google Cloud while retaining RDS would preserve the
cross-provider network and operational costs already identified in the hosted
compute comparison.

## Recommendation and decision boundary

Keep ADR 0017's managed, exact-version contract. Mark Cloudflare Workers plus
either RDS or D1 nonconforming for the current private MVP, and promote AWS
Lambda plus the existing RDS PostgreSQL 18.6 instance to the leading conforming
candidate. This recommendation does not itself select AWS.

There are two legitimate owner choices:

1. retain the accepted credential contract and continue the provider decision
   with AWS as the lead; or
2. explicitly reopen ADR 0017 and accept application cryptography or a custom
   deployment/secret broker as the price of Cloudflare hosting.

The second choice is the materially more surprising design. It adds security-
critical code and operational recovery solely to compensate for a provider
capability gap, so it requires the owner-override record defined by the FGA
engineering working agreement.
