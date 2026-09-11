# ADR 0013: Pause Flickr writes at durable account and deployment fault gates

Date: 2026-08-26

Status: Accepted by Terry on 2026-08-26

## Context

The FGA group-submission worker processes independent `(FGA user, Flickr group
ID)` FIFO partitions. A terminal result normally removes only the affected
intent from active FIFO membership so unrelated partitions can continue. That
is correct for photo-, group-, and pair-specific failures.

Some Flickr results instead identify a fault shared by many partitions. A
revoked OAuth grant affects every Flickr operation for one linked user. An
invalid application key, broken shared signing configuration, or unsupported
request format can affect the entire deployment. Treating each observation as
an independent terminal intent would consume many partition heads, create
repetitive alerts, and hide the one repair actually required.

A process-local circuit breaker would not survive a worker restart and could
disagree across concurrent workers. A counter-based breaker would also make a
definitive credential or configuration failure consume several more requests
before reaching an arbitrary threshold.

## Decision

### Fault scopes and trip results

The FGA database **MUST** maintain durable Flickr write gates at two scopes:

- one `user` gate for each linked FGA user and Flickr OAuth grant; and
- one `deployment` gate for the Flickr application key, consumer secret,
  shared signing implementation, REST endpoint, request format, and method
  configuration used by the deployment.

`enabled` and `paused` are the only gate states. The names deliberately avoid
the inverted “open means stopped” terminology commonly associated with circuit
breakers.

One complete, parseable Flickr result is sufficient to pause the narrowest
definitive scope:

| Flickr result | Durable gate action |
| --- | --- |
| Login failed or invalid OAuth token (`98`) | Pause that linked user's gate |
| User not logged in or insufficient permission (`99`) | Pause that linked user's gate |
| SSL required (`95`), invalid signature (`96`), missing signature (`97`), or invalid/expired API key (`100`) | Pause the deployment gate; `96` is deployment-scoped because the response does not distinguish a shared signing defect from a token-secret defect |
| Requested format/method or protocol defect (`111`, `112`, `114`, `115`) | Pause the deployment gate |
| Unknown numeric Flickr application code | Pause the deployment gate because the deployed classifier is incomplete |

Bad URL (`116`) remains a request-policy result because Flickr documents it in
terms of a particular URL argument. Photo-, group-, and pair-specific results
remain local to their existing intent or partition. Explicit temporary results
`105` and `106` keep their bounded-backoff behavior and do not pause a gate.
The first version has no error-count threshold and no time-based trip rule.

A durable gate row **MUST** have a stable scope key, state, monotonically
increasing revision, first and most recent observation times, sanitized reason
class, Flickr result code when present, source correlation or attempt ID, and
the actor and evidence associated with a later resume. An append-only gate
event records each pause, failed repair check, and successful resume. OAuth
tokens, token secrets, consumer secrets, signatures, and Flickr response bodies
**MUST NOT** appear in either record.

The first transaction that observes a definitive trip result **MUST** move the
gate to `paused` and create one alertable pause event. Later observations while
the same revision remains paused update sanitized diagnostic counts and the
most recent observation time without emitting a fresh page for every affected
intent. A narrower user pause and a deployment pause may coexist; work proceeds
only when both applicable gates are enabled.

### Worker and intent behavior

The FGA group-submission worker **MUST** check both applicable gates after it
acquires a partition lease and again in the transaction that would commit
`dispatch_started`. If either gate is paused, it sends no Flickr request,
releases the lease, and leaves the active head, enqueue order, attempt count,
and due time unchanged. Scheduler queries **MUST** exclude paused scopes so a
pause cannot consume partition heads or churn leases.

If a definitive scoped failure occurs during the read-only moderation
preflight, no add POST was sent. The worker pauses the gate, records the failed
preflight, and retains the intent at the active FIFO head for possible progress
after repair. If the result follows a group-add POST, the current intent keeps
its existing result policy: a documented authentication or configuration
failure becomes terminal `needs_attention`; an unknown application code
creates the permanent exact-pair submission block and terminal
`delivery_uncertain`. Pausing the broader gate does not rewrite that already-
attempted intent or weaken ADR 0007.

The FGA API backend **MUST** consult the same gates before issuing a new signed
direct-upload authorization or initiating another hosted Flickr write. A group-
submission batch may still durably accept new intents while a gate is paused;
those intents remain visible and queued without starting Flickr work. Ordinary
read-only status and repair surfaces remain available. An authenticated Flickr
read that exists only to validate a repair is the sole intentional bypass of a
paused operation gate; it cannot dispatch a Flickr write.

A gate prevents new operation starts. It cannot recall a Flickr request that
another worker or the Lightroom Classic host networking stack already
dispatched. Every in-flight operation still follows its normal durable result
and ambiguity rules. Implementations **MUST NOT** claim atomic cancellation
across the FGA database and Flickr.

### Alert, repair, and safe resume

The FGA administrative control plane **MUST** show the paused scope, pause time,
sanitized reason, latest check outcome, affected queued-intent count, oldest
affected enqueue time, and a correlation ID. A user-scoped pause requires
reauthorization or permission repair for that linked Flickr account. A
deployment pause requires operator repair and, for request-builder or classifier
defects, a corrected deployment that passed the relevant conformance tests.
The FGA LrC plug-in may display the pause and required action but **MUST NOT**
clear or bypass it.

There is no timeout, automatic half-open probe, process-restart reset, or
ordinary retry-now bypass. Resume is an explicit FGA administrative control-
plane operation against an expected gate revision. Immediately before closing
that revision, the FGA API backend **MUST** make a freshly signed, non-mutating
`flickr.auth.oauth.checkToken` call with the exact repaired application
configuration and OAuth grant that future work will use. It **MUST** require a
complete successful result containing the expected Flickr owner NSID and at
least `write` permission. A deployment-scoped repair may use any intended
active linked account; a user-scoped repair uses that exact account.

For codes `111`, `112`, `114`, `115`, or an unknown application code, the
successful token check is necessary but not sufficient: the repaired artifact
must also have passed the conformance test for the corrected REST method,
format, protocol, or result classifier. If any check fails, the same revision
remains paused and the failure is recorded without starting ordinary work.

After all checks succeed, one compare-and-set transaction **MUST** record the
repair evidence and actor, change only the expected revision to `enabled`, and
append the resume event. A concurrent new pause defeats the compare-and-set and
requires another repair check. Due work then becomes eligible through the
normal bounded scheduler and global Flickr rate limiter; resume performs no
bulk intent-state rewrite and preserves each partition's FIFO order.

The [administrative control-plane contract](../administrative-control-plane-contract.md)
defines the allowlisted Google-authenticated administrator and
`POST /api/v001/admin/flickr-write-gates/{gateId}/resume`. That route does not
weaken the gate revision, verification, or audit requirements in this decision.

Official Flickr contracts used by the repair check:

- [`flickr.auth.oauth.checkToken`](https://www.flickr.com/services/api/flickr.auth.oauth.checkToken.htm)
- [Flickr OAuth](https://www.flickr.com/services/api/auth.oauth.html)

## Consequences

- One revoked grant pauses only the linked user; one shared application or
  protocol defect pauses the deployment before workers consume more queue
  heads.
- Durable gates converge across workers and survive restarts, deployments, and
  scheduler handoffs.
- The design adds two small database records—a current gate and append-only
  event history—instead of a distributed breaker service or process-local
  counters.
- Explicit repair may keep healthy queued work waiting longer than an automatic
  probe would. That delay is preferable to silently resuming writes without
  proving the repaired identity and permission.
- A few already-dispatched operations can finish after the first trip result;
  their ordinary result and ambiguity rules remain authoritative.
- The intent that first reveals a post-dispatch fault may remain terminal even
  after the broader gate resumes. The breaker prevents systemic damage; it does
  not reinterpret a completed Flickr result as safely retryable.

## Alternatives considered

- **Trip after several matching failures:** rejected because definitive
  credential and deployment failures need no sampling threshold, and the
  threshold would consume additional partition heads.
- **Keep one breaker in each worker process:** rejected because concurrent
  workers and restarts would disagree and lose repair history.
- **Pause every failure at deployment scope:** rejected because photo-, group-,
  pair-, and linked-user failures have narrower established meanings and should
  not stop unrelated work.
- **Automatically probe and resume after a timeout:** rejected because time does
  not repair a revoked grant, invalid key, broken signer, or unknown result
  classifier.
- **Move all queued intents to a paused intent state:** rejected because the
  fault belongs to a shared operation gate, not to each intent; bulk rewrites
  would add churn and obscure FIFO state.
- **Allow a manual bypass:** rejected because it would make the ordinary worker
  guard optional precisely when credentials or shared request construction are
  known to be defective.
