# Public snapshot context

This checkout is a publication snapshot. The private architecture-design
repository remains the working source. Do not start private board services or
perform live diagnostic actions merely by opening this public snapshot. Follow
an explicit owner task for any subsequent update. The sanitized original
working agreement is retained below as architecture context.

# FGA engineering working agreement

These instructions apply to the entire repository.

## Design and implementation defaults

1. Choose boring and obvious before clever. Prefer direct control flow,
   explicit state, conventional names, and small understandable components.
2. Integrate existing, mature, well-tested code before inventing a custom
   implementation. Confirm that dependencies are maintained, appropriately
   scoped, and license-compatible before adopting them.
3. Innovate only where existing components do not satisfy an actual FGA
   requirement. Record the unmet requirement and important tradeoffs when a
   custom or unusual design is necessary.
4. Honor the principle of least surprise for an expert developer with more
   than 20 years of experience. Use the ecosystem's idioms and established
   conventions; avoid hidden behavior, unnecessary indirection, speculative
   abstractions, and magic configuration.
5. Prefer one explicit, documented convention over local variation when
   multiple established approaches satisfy the requirements. Apply the chosen
   convention consistently so a returning maintainer can recognize it, adjust
   their mental model once, and predict the rest of the project.
6. Treat simplicity as compatible with rigor. Keep validation, useful error
   handling, observability, security boundaries, and proportionate tests even
   when choosing the simplest design.

When two approaches meet the requirements, prefer the one an experienced
reviewer can understand, verify, operate, and remove most easily.

Terry's standing consistency maxim, recorded 2026-08-28, is: “I don't even care
what standard we pick as long as there is one.” This preference applies only
after correctness, security, interoperability, and actual FGA requirements are
satisfied. Consistency does not justify retaining a convention that fails
those constraints; choose and document a better convention deliberately.

## Architecture pushback and owner overrides

Codex must stop the design discussion and push back before implementing or
recording a proposal that Codex reasonably believes violates the boring-and-
obvious default or the principle of least surprise. State the concern plainly,
identify the conventional alternative, and explain the concrete maintenance,
security, interoperability, or operational cost. Do not silently comply merely
because the owner proposed or previously favored the surprising design.

The pushback is a required decision checkpoint, not an automatic veto. If Terry
understands the objection and explicitly holds his ground, proceed when the
decision remains safe and within scope. In the same turn, record the exception
in the appropriate durable architecture document or ADR and commit it. The
record must include the date, the conventional recommendation Codex made, the
material objection, Terry's stated justification, and the tradeoffs Terry
knowingly accepted. Do not rewrite the record to imply consensus or make the
exception appear accidental; Future Terry must be able to identify the owner
override and judge its original rationale without relying on chat history.

## Private native-storage enforcement

Terry approved the scoped runtime trust model in
[ADR 0051](docs/decisions/0051-trust-private-storage-runtime-with-guarded-writes.md) on 2026-09-11.
For the private single-owner deployment, native storage-owning code is trusted
not to dismantle its SQL guards. Broad D1 or owning Durable Object schema/erase
capability alone does not require RDS or a custom privilege service. Preserve
SQL guards, parameterized fixed operations, permanent suppression, append-only
history, hostile-client protection, atomicity, fencing, and backup/restore.
Ordinary application code must never use that broader capability to clear
protected history; review the exception before public or multi-user operation.

## Native-first service decisions

Terry approved [ADR 0052](docs/decisions/0052-evaluate-paused-native-credential-replacement.md) on 2026-09-11.
AWS services remain available, but the bar for need is high: demonstrate a
concrete unmet private-deployment requirement after considering simpler native
workflows and their actual consequences. Compare the full operational burden;
a missing preferred API or an already-working AWS prototype does not establish
need. Evaluate paused, generation-checked native Flickr credential replacement
first. Accepted safety requirements still need explicit owner amendments, and
native conformance must be proved rather than inferred from that preference.

## Approved private clock and parser boundaries

Terry approved [ADR 0053](docs/decisions/0053-accept-millisecond-private-database-clocks.md) and
[ADR 0054](docs/decisions/0054-accept-early-duplicate-authorization-rejection.md) on 2026-09-11.
Persisted database UTC time may have millisecond source resolution for the
private deployment; explicit sequences/revisions own durable order. Six-digit
formatting is not evidence of finer resolution, and live monotonic preflight
timing is unchanged. A provider's early HTTP 400 for duplicate Authorization
fields may use its own non-JSON response, under the bounded no-data/no-shell/
no-redirect rules. Application-generated authentication responses retain JSON,
no-store and matching Bearer errors. Neither clarification alone requires AWS.

## Cryptographic algorithm terminology

Name SHA algorithms as `SHA1-<bits>`, `SHA2-<bits>`, or `SHA3-<bits>` in code,
documentation, and discussion—for example, `SHA1-160`, `SHA2-256`, and
`SHA3-256`. Do not use ambiguous family-less forms. Preserve a different
spelling only where an external library, command, protocol, or data format
requires that exact identifier.

## Component-qualified FGA terminology

Whenever FGA is the grammatical actor in architecture, design, operations, or
implementation prose, name the acting component rather than writing bare
`FGA`. Use concrete terms such as `FGA LrC plug-in`, `FGA administrative control
plane`, `FGA API backend`, `FGA HTTPS edge`, `FGA refresh worker`, `FGA
group-submission worker`, `FGA database`, or `FGA managed secret store`. Bare
`FGA` remains appropriate when it names the product, project, credential or user
namespace, policy as a whole, or another non-acting concept. The reader must be
able to identify the trust, process, and persistence boundary without inferring
it from surrounding paragraphs.

## Component-qualified Lightroom terminology

Whenever Lightroom is the grammatical actor in architecture, design,
operations, or implementation prose, identify the component that actually acts.
Use terms such as `FGA LrC plug-in`, `Lightroom Classic host`, `Lightroom Classic
publish-service runtime`, `Lightroom Classic rendering engine`, `Lightroom
Classic catalog`, `Lightroom SDK API`, or `Lightroom Classic host networking
stack`. Default to `FGA LrC plug-in` for behavior implemented or initiated by
plug-in code; Lightroom Classic itself does little without a user, plug-in, SDK
callback, or named host subsystem directing the action. Bare `Lightroom` or
`Lightroom Classic` remains appropriate when naming the application, product,
version target, UI location, or another non-acting context. Do not attribute a
plug-in responsibility to Lightroom Classic merely because the plug-in runs
inside its process.

Terry's standing terminology, issued 2026-08-24, distinguishes the two publish
providers unambiguously. When Terry says `Flickr plug-in`, he means Adobe's
maintained Lightroom Classic Flickr publish service that ships with Lightroom
Classic. When Terry says `FGA plug-in`, he means our code; render that term as
`FGA LrC plug-in` in component-qualified project prose. Never use `Flickr
plug-in` to refer to FGA code.

## Tooling output hygiene

Do not repeatedly expose known-benign permission warnings. Fix or suppress the
cause at the command boundary, while preserving meaningful failures.

In the current Windows Codex sandbox, Git sees the repository as owned by a
different Windows identity and cannot read the conventional global ignore file
under the user's `.config` directory even though its Windows ACL is healthy.
For every sandboxed, read-only Git command run from the repository root, pass
both `-c safe.directory=C:/Projects/FGA/architecture-design` and
`-c core.excludesFile=.git/info/exclude` on the first invocation. The repository
`.gitignore` still applies. Git mutations already run outside the sandbox and
do not need these overrides.

## Script implementation language

Prefer Python for repository scripts because Terry can read and maintain it
natively. Apply this test to every script regardless of its existing language,
not merely to PowerShell: when Python and another language are roughly a coin
flip, choose or port to Python. Use another language only when a concrete
runtime requirement or native integration makes it materially simpler, safer,
or more reliable than Python. Make that decision separately for every script
and document the specific reason the benefit justifies Terry being unable to
audit the implementation fluently. Convenience, existing shell context, or the
project running on Windows is not by itself sufficient justification. Reapply
the test whenever an existing script is materially changed.

Terry reiterated this as a standing order on 2026-08-23: when Python and
PowerShell are a coin flip, every repository script **MUST** be Python. A
Windows-native operation invoked by a Python script does not justify moving the
orchestration, validation, or error handling into PowerShell.

## Python workflow

Astral `uv` is the sole Python environment, dependency, lock, and command
workflow. `pyproject.toml` is the single dependency, Ruff, formatter, and
Pyright configuration source; `uv.lock` is committed. Run repository Python
tools and scripts as `uv run --frozen ...` so a command cannot mutate or
silently re-resolve the accepted environment. Use direct `.venv` executable
paths only when diagnosing `uv` itself or when an external tool requires one.

Use the latest stable CPython release for project environments and Python code.
Never choose an end-of-life Python release. If a required dependency cannot run
on the latest stable release, document the blocker and rationale, pin the newest
supported non-EOL release only as a temporary exception, and track removal of
that exception.

In the current Windows Codex sandbox, use the permission profile's writable
system-temp root for repository uv commands when the normal user-profile cache
is inaccessible. The trusted project `.codex/config.toml` injects
`UV_CACHE_DIR=C:\Users\TDO-XPS15-2024\AppData\Local\Temp\localswim-uv-cache`
at the spawned-command boundary, so ordinary repository commands do not repeat
an environment assignment. `$env:TEMP\localswim-uv-cache` is the equivalent
manual fallback only when diagnosing the config layer or running from an
untrusted context where Codex ignores project configuration. Do not add the
separate `C:\Temp` tree to the sandbox merely for repository validation. Terry
has designated both locations as transient storage, so do not place durable
project state there or treat anything there as recoverable. Detached localswim
lifecycle processes continue to explicitly replace the inherited value with
their documented `C:\Temp` paths outside the sandbox. Continue to request an
approved outside-sandbox invocation when uv must write durable user-level state
such as its tool installation directory; do not fall back to a different Python
environment merely to bypass the sandbox.

## Local localswim coordination

Use the machine-local localswim service as FGA's human/agent work board. The
localswim source checkout is `C:\Projects\localswim`. The private state-store
checkout is `C:\Projects\localswim-state-store`, cloned from
`https://github.com/TerryOtt/localswim-state-store`, and the authoritative FGA
board is `flickgroupaddr/fga-localswim.json` in that checkout. Ensure the
state-store checkout exists at that exact location before starting the service.
The private state-store board is the sole authoritative snapshot.

Terry's standing order, issued 2026-08-25, gives the localswim inception board
board-level priority over the FGA board. Before starting or resuming FGA work,
inspect the inception board and work every Bot-actionable inception ticket to
its review or other legitimate handoff boundary. This precedence applies before
comparing individual ticket priorities: an actionable inception P3 outranks an
FGA P1. Backlog, Blocked, Needs Terry, Ready for review, and Completed are not
Bot-actionable merely because they exist; continue to honor each lane's policy.
If actionable inception work arrives during FGA work, leave the current FGA
operation in a safe state and switch at the next safe boundary.

Immediately before every transition from localswim inception work to FGA work,
run this authoritative handoff barrier from the FGA repository root:

```console
uv run --frozen python scripts/check_localswim_priority.py
```

The barrier queries `Ready for work` and `In progress` through
`localswim-cli <board> card next`. A nonzero exit identifies sanitized actionable
inception work that **MUST** be worked before the FGA transition, or an operational
failure that also refuses the transition. Only exit status `0` permits FGA work.
Board-write monitor messages are advisory next-turn notifications: `codex queue`
does not acknowledge delivery to the turn active when the write occurred, so
alerts never replace this board query.

Terry's standing order, issued 2026-08-23, is that every FGA work session
**MUST** ensure both the FGA board and the localswim inception board have healthy
detached services and board-specific detached monitors targeted at the active
Codex thread. The inception board is
`C:\Projects\localswim-state-store\localswim\localswim.json`; read and follow
`C:\Projects\localswim\AGENTS.md` completely for its current port, log, status,
target, and lock paths before operating it. Reuse each healthy service and
retarget each existing monitor through its documented launch command. Launch a
missing service or monitor only with PowerShell `Start-Process -WindowStyle
Hidden`, redirected standard output and error, and the documented working
directory and environment. Every launcher command **MUST** return normally after
health is verified; never leave a foreground uv process, `Start-Job`, PTY,
recurring wait, or Codex exec session attached to either daemon. A normal
Ctrl+C or context replacement must not stop either healthy service or monitor.

Terry changed the `/exit` contract on 2026-08-23: a clean Codex `/exit` **MUST**
run the project `SessionEnd` hook with the documented three-second maximum
timeout. The hook runs `scripts/trigger_localswim_shutdown.py`, which starts one
hidden, detached `scripts/stop_localswim_session.py` coordinator and returns
without waiting for cleanup to finish. Codex can exit while that independent
coordinator is still working; `/exit` guarantees that graceful teardown is
initiated, not that all four processes exit before Codex does.

The shutdown coordinator owns
`C:\Temp\FGA-localswim-session-lifecycle.lock`, asks each exact monitor PID to
stop after its paired service becomes unavailable, and invokes
`localswim-cli <board> board shutdown` for both boards. Each localswim service
**MUST** quiesce mutations, complete one final autopush, close its request
threads, and remove its service descriptor before the CLI reports success. A
failed final push **MUST** refuse service shutdown; the coordinator **MUST NOT**
replace this protocol with `Stop-Process`, `taskkill`, or another forced
termination. A later `SessionStart` **MUST** acquire the same lifecycle lock
before ensuring services and monitors and **MUST** also treat the handoff's
`launching` and `stopping` states as active before attempting the lock. The
pre-lock handoff check closes the interval between the trigger returning and
the detached coordinator acquiring its lock, so startup cannot race an earlier
shutdown. Treat `C:\Temp\FGA-localswim-session-end-hook-status.json` as the
coordinator's sanitized `launching`, `stopping`, `stopped`, or `error` handoff.
Closing the Codex window is not a guaranteed lifecycle boundary; Terry's
supported habit is to type `/exit`.

The trusted project-local `SessionStart` hook in `.codex/hooks.json` is the
normal startup path. On `startup`, `resume`, and `clear`, it runs
`scripts/start_localswim_session.py`, which reads both embedded board ports,
reuses or launches both services in dependency order, confirms each autopush
state is `ok`, and launches or retargets both monitors before returning. Codex
requires a one-time `/hooks` review whenever the hook definition changes; do not
bypass that trust checkpoint persistently. The launcher is Python. It invokes
one fixed inline PowerShell command only at the Windows-native process boundary
where this agreement explicitly requires `Start-Process -WindowStyle Hidden`.
The hook payload's `session_id` is authoritative over an inherited
`CODEX_THREAD_ID`, so a nested session targets itself rather than its parent.
Treat `C:\Temp\FGA-localswim-session-hook-status.json` as the launcher's
sanitized success-or-error handoff.

Terry's standing order, issued 2026-08-23, is that each Codex process launch
opens one visible Google Chrome window for each board after both services and
monitors are healthy, whether the conversation receives a `startup` or `resume`
event. Use each board's embedded port and `http://127.0.0.1:<port>/`. Do not
open more browser windows for `clear` or `compact`; those events still ensure
and retarget the four detached background components. Browser windows are
explicitly user-visible and are not launched with `-WindowStyle Hidden`.
Place the FGA board in the left half and the localswim inception board in the
right half of Windows display 1's work area through documented Win32 window
positioning APIs. This reproduces the desired layout but does not claim to
create a native Windows Snap Group; Terry can snap-group the positioned windows
manually when useful.

Treat the state-store repository as a private safe-space boundary. Terry's
standing order, issued 2026-08-22, is that
`TerryOtt/localswim-state-store` **MUST** retain GitHub visibility `PRIVATE` at
all times. Its visibility was checked and corrected on 2026-08-22. Routine
service startup, reuse, board access, and monitor alerts do not require another
GitHub visibility query. Reverify only after an operation intended to change
repository visibility or ownership, or if there is concrete evidence that the
repository may no longer be private. If GitHub reports another visibility,
immediately use the standing authorization to change it to private and verify
the result before continuing. If the correction fails, stop the exact process
serving this board and treat privacy as an operational blocker.

The state-store repository **MUST NOT** be made public, publicly mirrored or
forked, exposed through GitHub Pages, or copied into public repositories,
issues, pull requests, build logs, or other publicly accessible artifacts.
Preserve only sanitized conclusions elsewhere when FGA's durable-memory rule
requires them; never reproduce private board language or discussion.

At the beginning of each Codex run, read the board's `port` value (currently
`8793`) and request `http://127.0.0.1:<port>/api/v001/status`. Reuse a
healthy service and MUST NOT launch a duplicate. If it is unavailable, ensure
the two console commands are installed with the active local source by running:

```console
uv tool install --cache-dir C:\Temp\localswim-uv-cache --python 3.14.7 --editable C:\Projects\localswim
```

This is a machine-level development tool; MUST NOT add localswim to FGA's
project dependencies. If the sandbox blocks uv's user-local tool directory,
request an approved outside-sandbox invocation as described above.

Launch the following as a hidden background process with the FGA repository
root as its working directory:

```powershell
$env:PYTHONIOENCODING = "utf-8"
localswim --autopush C:\Projects\localswim-state-store\flickgroupaddr\fga-localswim.json
```

Redirect standard output to `C:\Temp\FGA-localswim.out.log` and standard error
to `C:\Temp\FGA-localswim.err.log`. The child process MUST inherit
`PYTHONIOENCODING=utf-8`; redirected Windows output otherwise uses a legacy
encoding that cannot represent localswim's Unicode move arrow and can terminate
an HTTP request after its board mutation has already committed. Poll the status
endpoint until it is healthy and confirm that `push.state` is `ok` before using
the board. If the installed executable is not yet visible on `PATH`, resolve
the tool executable directory with `uv tool dir --bin`; do not bypass uv with
a repository `.venv` path.

Terry's standing order, issued 2026-08-24, is that neither required board
service may retain a Build ID ending in `-dirty` after the localswim source
checkout can safely be clean. Treat a stale suffix as an operational defect and
remove it as soon as safe. First inspect the checkout and preserve unknown or
unrelated edits. Complete, verify, commit, and push authorized localswim work;
never hide, override, or spoof a truthful dirty state. Once the checkout is clean,
poll both status endpoints first: a service whose loaded Python sources still match
disk automatically replaces its stale dirty identity during status polling. If the
loaded source changed or the automatic refresh does not converge, use localswim's
supported graceful shutdown/restart or hot-re-exec boundary, never forced termination.
Confirm both status endpoints report clean Build IDs and `push.state` `ok` after
remediation.

Use the following command for board reads and mutations:

```console
localswim-cli C:\Projects\localswim-state-store\flickgroupaddr\fga-localswim.json
```

Prefer `localswim-cli` for every board inspection. If reading the authoritative
board JSON directly is useful or necessary, use `jq`; do not inspect it through
PowerShell JSON conversion, Python, an editor, or an unstructured text dump.
`jq` is acceptable only for read-only inspection and does not relax the rule
against directly editing the JSON.

When `localswim-cli` cannot answer a board question efficiently, tell Terry in
the same turn which capability is missing and why the fallback was necessary;
do not silently normalize a repeated `jq` workaround. Treat the gap as a
candidate localswim CLI enhancement so a small productivity fix can compound
across later human and agent work. The first concrete gap, alert attribution,
was resolved on 2026-08-23: the installed CLI exposes `activity since` and
`activity between`, which return sanitized ticket ID, event kind, time, actor,
and move endpoints without comment text. Prefer those options for bounded board
activity inspection.

Terry's standing order, issued 2026-08-24, is that Codex **MUST** create an
individual Ready-for-work ticket on the localswim inception board whenever a
localswim enhancement would materially improve human or agent efficiency. Check
for an existing ticket first, keep the proposed capability narrowly scoped, and
raise the new or existing ticket with Terry in the same turn. This is standing
authorization to create the qualifying ticket directly in `ready_for_work`; do
not place it on the FGA board merely because FGA work exposed the gap.

Work expected to span more than one agent turn SHOULD have a localswim ticket so
status, ownership, and handoff survive context replacement. Work that reasonably fits
inside one turn MAY proceed without a ticket. Apply this as a judgment rule, not a
process quota: ticketing exists to preserve multi-turn coordination, not to create
administrative work for its own sake.

Use the FGA board's workflow lanes as work-eligibility states, not dependency
states. Terry's standing order, issued 2026-08-23, is:

- **Backlog** means Codex cannot start the card because Terry is deliberately
  withholding it or because the card is not sufficiently scoped for Codex to do
  meaningful work.
- **Ready for work** means Codex is authorized and the card is sufficiently
  scoped to start. A card stays eligible for this lane even when another ticket
  blocks its eventual completion; express that execution constraint with the
  board's dependency relationship instead of leaving the card in Backlog.
- **Blocked** means neither Terry nor Codex can advance the card because an
  external condition must change, such as ordered hardware arriving. A ticket
  dependency alone does not put an otherwise actionable card in this lane.
- **Needs Terry** means Codex's next meaningful step requires Terry's input or
  judgment. It does not mean that an external factor blocks both Terry and
  Codex.

This standing order is explicit permission to promote each card that actually
meets the Ready-for-work definition. Move a card whose next meaningful step is
solely a Terry judgment to Needs Terry. Do not use Ready for work to imply that
a declared dependency has been resolved, or use Blocked for an ordinary ticket
dependency.

Terry's standing preference, issued 2026-08-23, is that actionable architecture
or design questions, concerns, and follow-up work discovered during a review become
individual FGA localswim tickets instead of an unowned task backlog in a public
Markdown document. A review document **MAY** retain the evidence, conclusion,
reconciliation category, and ticket ID needed to make the review independently
auditable, but it **MUST NOT** reproduce private board prose. Use the board's
Backlog lane for newly identified work unless its current policy and Terry's
authorization support another lane; a large healthy backlog is preferable to
hiding work in prose.

Whenever the FGA localswim service is running, a board-write monitor **MUST**
also be running and targeted at the active Codex thread. Launch
`scripts/watch_localswim.py` through `uv run --frozen python` as a hidden background
process after the service is healthy, passing the authoritative board path and
`$env:CODEX_THREAD_ID`.
Redirect its standard output to `C:\Temp\FGA-localswim-monitor.out.log` and
standard error to `C:\Temp\FGA-localswim-monitor.err.log`. The script uses an
exclusive byte-range lock, so invoking it again retargets the existing monitor
instead of creating a duplicate. Treat
`C:\Temp\FGA-localswim-monitor-status.json` as its sanitized health handoff.

The uv project pins `watchfiles` 1.2.0, verified on 2026-08-22 as an active,
MIT-licensed project compatible with Python 3.14. The dependency supplies
native Windows filesystem notifications without custom platform bindings. The
monitor **MUST NOT** read or log board content. It **MUST** apply a trailing-edge
15-second quiet window and coalesce all board writes in that window into one
sanitized next-turn message containing only the write count, first/last observation
times, a delivery-semantics notice, and explicit activity-query bounds. Each later
write **MUST** restart the quiet window. The lower activity bound **MUST** be the
time when the monitor last
established the preceding board signature, not the later time when it first
observed the new write. Both bounds **MUST** retain localswim's persisted
microsecond event precision, so they can be passed directly to
`localswim-cli <board> activity between` without manual rounding. First/last observation
times remain diagnostic timestamps and are not activity bounds. The awakened
agent must prefer `localswim-cli` with the supplied activity bounds to inspect new
activity; read-only `jq` inspection is acceptable when useful. The agent must
never edit the JSON directly. Routine alerts **MUST NOT** trigger a GitHub
visibility query.

Whole-second audit entries written by localswim builds before inception ticket
#0010 remain valid history. After the coordinated service and monitor restart,
new events and monitor cursors use six fractional digits. Do not floor those
bounds: truncation recreates the inclusive-lower-bound overlap that #0010 removed.

MUST NOT directly edit the board JSON while the service is running. Terry gave
standing authorization on 2026-08-22 to commit and autopush this board through
the state-store repository, so every FGA service launch MUST include
`--autopush`. The FGA board's embedded policy requires the bot user ID `bot`;
the board presents that identity with the display label `Bot`. Keep the board's
`cliUser` and `defaultOwner` aligned with that ID.

## Python data modeling

When a Python dataclass and another internal record representation are roughly
a coin flip, choose the dataclass. Prefer its explicit fields, generated
initialization, readable representation, equality behavior, and straightforward
typing over positional tuples, ad hoc dictionaries, named tuples, or hand-
written container boilerplate. This is a preference, not a prohibition:
serializer-ready mappings, dynamic third-party payloads, and genuine mapping
semantics should remain dictionaries or `TypedDict`s when that boundary is
materially clearer. Reconsider the choice per type instead of forcing
dataclasses onto data that is naturally not a record.

## Lightroom probe output handoff

Every distinct loadable build of an FGA LrC plug-in **MUST** increment the
`VERSION` table in its `Info.lua` before Terry is asked to reload or test it.
Treat a change to runtime Lua, the manifest, or a bundled runtime asset as a new
build. Increment the `build` field for iterative probe changes and reserve the
major, minor, and revision fields for intentional release milestones. Never ask
Terry to test materially different plug-in code under a version he has already
seen, and name the exact new version in the handoff.

When Terry and Codex are actively testing an FGA LrC plug-in or Lightroom
Classic host probe, prefer a sanitized machine-readable JSON result at one
documented, probe-specific path under `C:\Temp`. Write the result after every
meaningful command, callback, success, cancellation, and caught failure so
Codex can monitor the exact path and inspect host evidence without asking Terry
to transcribe a dialog. Include a schema version, probe and phase identifiers,
write time, relevant catalog or host observations, and sanitized error details.
Never include credentials, OAuth material, authorization headers, private photo
metadata, or unrelated catalog state. Use a distinct filename per probe and
replace the file only after the complete JSON document has been closed. Before
asking Terry to perform a visible host step, Codex should launch or retarget a
bounded file monitor for that output path and analyze the new document as soon
as the monitor reports it. Use text or XML only when JSON would make the probe
materially harder to implement or inspect.

## Public test publication avoidance

Terry's standing order, issued 2026-08-27, is that FGA test, diagnostic, and
support workflows **MUST** keep purpose-built fixtures private whenever a
private resource can answer the actual requirement. Public publication is not
justified by convenience, easier observation, or catalog-only behavior. Before
creating any public test photo, identify the exact behavior that cannot be
tested privately and obtain Terry's explicit approval immediately before the
upload after disclosing likely follower/feed exposure, the shortest necessary
public interval, and the cleanup plan.

Never choose retained-public as a probe's default final state. Make an
unavoidably public fixture private immediately after the public-only evidence is
captured and verify that an unauthenticated request can no longer access it.
Delete the exact synthetic resource when Terry directs, using the narrowest
safe authority available; do not broaden a long-lived Flickr OAuth grant to
delete scope when Terry can safely delete one already-private fixture through
Flickr's own UI. A separately accepted test whose subject is inherently public
or group-visible remains an explicit exception only to the minimum extent its
requirement cannot be exercised with an existing or private fixture.

## Lightroom entropy boundary

Never use Lua `math.random`, timestamps, clocks, machine identifiers, catalog
object identifiers, or similar predictable values for credentials, secrets,
OAuth nonces, pairing codes, or other security-sensitive values. The Lightroom
Classic SDK has no documented secure-random source or general-purpose UUID
generator; `LrPasswords` securely stores values but does not generate them.

Generate every security-sensitive random value in the appropriate FGA hosted
component using the runtime or operating system's cryptographically secure
random generator. Send only the resulting scoped value to the FGA LrC plug-in
over HTTPS and store long-lived plug-in credentials with `LrPasswords`. Stable
Lightroom identifiers may be used for non-secret identity and deterministic
idempotency inputs, never as proof of authorization or entropy.

## Lightroom documented-API boundary

Use only Lightroom SDK interfaces documented in the newest Adobe-published SDK
API Reference. An importable or runtime-visible module, function, or symbol is
not a supported contract. Do not depend on undocumented interfaces such as
`LrUUID`, even if experimentation shows that they currently work. Reconsider an
interface only after Adobe documents it; record the new contract and remove any
superseded workaround deliberately.

## Flickr moderator protection boundary

FGA's Flickr group-pool behavior is add-only. It **MAY** read current group-pool
membership and **MAY** call `flickr.groups.pools.add` under the safeguards below,
but it **MUST NOT** call `flickr.groups.pools.remove`, expose a group-removal
control, or interpret deselection as a removal request. Current memberships are
read-only in FGA. A user who wants to remove a photo from a group does so through
Flickr or another non-FGA client.

Treat Flickr, not FGA intent history or cache, as authoritative for current pool
membership. Each time the FGA LrC plug-in opens group selection for a photo
previously published through FGA, the FGA API backend **MUST** obtain a fresh
documented Flickr `flickr.photos.getAllContexts` result and distinguish its pool
entries from locally selected additions. A failed or incomplete read **MUST
NOT** be presented as an empty membership set. The observation is advisory and
timestamped because external actors can add or remove membership again
immediately after the response.

Treat volunteer moderator courtesy as a safety boundary under FGA's
**fail-polite** rule. Before every individual
`flickr.groups.pools.add` attempt, the FGA group-submission worker **MUST**
successfully call `flickr.groups.getInfo` for that group and durably record the
returned `ispoolmoderated` value and observation time. A cached observation
never satisfies this write precondition. If the read fails or its moderation
value is not interpretable, send no add request. This rule has no automatic,
manual, administrative, recovery, or testing exception. Any future component
capable of invoking `pools.add` **MUST** enforce the same fresh preflight.

The FGA group-submission worker **MUST** use a monotonic clock to enforce its
freshness window and **MUST** begin dispatching the add POST less than 1,000
milliseconds after it receives the successful `getInfo` response. If the
observation reaches that age before dispatch begins, discard it and perform
another preflight. Do not claim this makes the Flickr operations atomic or
bounds Flickr's network and server-side processing interval.

Within one attempt, that `getInfo` read **MUST** be the FGA group-submission
worker's immediately preceding Flickr API operation for the add; no unrelated
Flickr call may intervene on that attempt. Concurrent workers may independently
preflight their own attempts. Reserve global Flickr rate-limit capacity for both
the GET and possible POST before starting the preflight; never wait for a
rate-limit token between them.

Flickr's “photo added to the pool's pending queue” status (code `6`) and “photo
already in the pool's pending queue” status (code `7`) are terminal for the
exact `(Flickr photo ID, Flickr group ID)` pair. The FGA group-submission
worker **MUST** create a permanent do-not-resubmit record in the FGA database,
**MUST NOT** automatically call the add method for that pair again, and **MUST
NOT** infer rejection from continued absence in the group. The same permanent
suppression applies when a durable `dispatch_started` marker exists, no durable
record proves that zero add-POST request bytes could have left the FGA
group-submission worker, and no definitive documented Flickr result was durably
committed, or when Flickr returns an unknown application code whose side effects
are not documented. Ordinary
retries, manual retry-now actions, crash recovery, reconciliation,
cancellation, and history retention must honor the block.

The block **MUST** also survive every future moderated-to-unmoderated-to-
moderated cycle, regardless of how many months or years pass. A volunteer may
take a long break, the group may become unmoderated during that break, and the
same volunteer may later return after moderation is restored and remember
rejecting the same photo. Never treat a current
`ispoolmoderated="0"` observation, an elapsed retention period, or a moderator's
absence and return as amnesty for a pair that ever entered a moderation queue.

The FGA API backend and FGA LrC plug-in **MUST NOT** expose a force-resubmit path
for a blocked pair. If Terry chooses to submit that photo again, he does so
manually through Flickr's own UI; no FGA component automates or facilitates the
repeat submission.

Enforce these rules in the FGA API backend, FGA group-submission worker, and FGA
database, never only in the FGA LrC plug-in UI or another client. Treat a client
as potentially buggy, modified, or hostile: it cannot supply an authoritative
moderation observation, clear a submission block, or select a bypass. Design
the boundary to protect any future Flickr moderator, including Terry as the
system's creator.

Do not overclaim what the exact-pair block proves. It does not stop a hostile
user from creating many distinct Flickr photo IDs, and an MIT-licensed fork can
remove safeguards while using infrastructure outside FGA's control. Public or
multi-user operation **MUST NOT** launch until a separate abuse threat model
defines conservative per-user/group admission and rate limits, re-registration
resistance, monitoring, suspension, and appeal/repair procedures for the
official FGA API backend, FGA worker deployment, and Flickr API key.

Group moderation is dynamic. The mandatory `getInfo` observation can become
stale between its GET and the add POST; it is context, not an atomic guarantee
or retry authorization. A “photo added to the pool's pending queue” status
(code `6`) following `ispoolmoderated="0"` is recorded as a race or upstream
inconsistency and receives the same permanent block.
Never use undocumented Flickr moderation methods or screen scraping to infer a
pending or rejected state. See ADR 0007 for the full state and retention rules.

## Photography data privacy boundary

Treat `[private catalog root omitted]`, its catalogs, previews, catalog metadata,
source paths, and every referenced photo as highly sensitive and private to
Terry and Sol by default. Access that directory read-only unless the user
explicitly authorizes a specific mutation.

Adobe Flickr publish state or a stored Flickr photo ID identifies only a
candidate public photo. Consider photo content or metadata safe for a public
repository only after independently confirming that its exact photopage under
`https://www.flickr.com/photos/terryott/<Flickr photo ID>/` is accessible as an
unauthenticated guest. A private or search-hidden Flickr test upload does not
qualify. Record the public URL and verification date for any asset admitted as
public test data.

Terry established a standing exception on 2026-08-24 for a photo already
published publicly through his Flickr account. After the exact photopage passes
the unauthenticated-guest check above, Codex **MAY** reference, download,
reproduce, and commit the Flickr-delivered public rendition and metadata that
the same guest page exposes without requesting case-by-case privacy approval.
This exception does not extend to a Lightroom source original, another local
rendition, source path, unpublished edit, catalog-only metadata, or any private
or search-hidden Flickr item. Verify the exact photo ID at the time of use and
retain the public URL and verification date with the admitted asset or fixture.

Never commit a Lightroom catalog, previews, unverified photo content, or
metadata derived from an unverified photo. Keep intermediate catalog query
results ignored and minimize command output so unverified filenames, paths,
captions, people, locations, and thumbnails are not exposed in logs or chat.

## Lightroom version target

Target the latest production release of Lightroom Classic. The owner is
contractually required to remain on the latest release and does not need FGA to
preserve compatibility with older Lightroom versions. Use the newest Lightroom
Classic SDK Adobe has published even when its minor version lags the installed
application. Do not add old-version compatibility code unless a concrete
current dependency requires it and the exception is documented.

## Flickr Pro account target

Terry **MUST** maintain Flickr Pro membership for FGA's supported lifetime.
Treat Flickr Pro as the sole required Flickr account tier;
FGA components do not need a free-tier compatibility path or fallback for Pro
features such as documented photo replacement. Runtime entitlement checks and
Flickr errors must still fail honestly and safely rather than assuming a paid
feature is available during an outage, account problem, or upstream policy
change.

## Publishing consistency boundary

Treat every multi-photo FGA LrC plug-in publish run as eventually consistent,
not atomic or ordered. Terry's binding liveness requirement is that every
requested photo “has to get there”; relative order is immaterial. Each photo
**MUST** progress and report status independently, and an ambiguous, failed,
blocked, or slow photo **MUST NOT** stop an otherwise healthy photo merely to
preserve Lightroom Classic selection, render, upload, or callback order.

No FGA component **MUST** silently drop a photo or group intent, reserve a
group-queue position before durable intent creation, or promise that photos
reach Flickr or Flickr groups in their Lightroom Classic publish-run order.
Each unit of work **MUST** continue toward its intended result or reach a
durable, truthful state explaining why safe automatic progress is impossible.
This is a liveness and accountability requirement, not a guarantee that Flickr
will accept every external write.

The internal FIFO invariant remains for active intents already accepted into
one `(FGA user, Flickr group ID)` partition. That ordering is based only on
durable insertion and is a worker scheduling and moderator-courtesy rule, not a
cross-photo publication-order guarantee. Eventually consistent processing
never authorizes an unsafe retry, hides an ambiguous outcome, or weakens the
permanent suppression rules in ADR 0007. See ADR 0009.

Every FGA published collection **MUST** correspond one-to-one with one Flickr
album, and every photo published from that collection **MUST** eventually be
attached to its corresponding album. Album attachment is part of the photo's
accountable publish outcome, but it is not atomic with Flickr upload and creates
no cross-photo ordering guarantee. Album-binding creation, durable Flickr album
ID storage, idempotency, rename/removal semantics, and repair behavior remain
the explicit architecture work tracked by FGA localswim ticket #0060.

The FGA LrC plug-in **MUST** allow a new photo to be published with zero Flickr
group additions. Flickr publication and album attachment are required photo
outcomes; group submissions are optional, add-only intents. For the normal
single-photo interaction, present **No group additions** as an explicit choice.
In a multi-photo publish callback, a zero-group photo **MUST NOT** block another
photo or trigger serial per-photo modal dialogs. An empty selection creates no
group-submission intent or queue work and **MUST NOT** be sent as a fake empty
group-submission batch. See ADR 0010.

Treat Terry's complete current Adobe Flickr publish-service workflow as a
required capability baseline, not as a UI or architecture constraint. Every job
Terry performs today is in FGA scope, but no Adobe menu, click sequence, state
presentation, implementation choice, or limitation is binding merely because
the shipped provider uses it. FGA exists to make this workflow materially more
efficient.

Codex is explicitly directed to challenge the current workflow and proposed FGA
experience as hard as useful. Identify avoidable clicks, context switches,
duplicate choices, hidden state, serial waits, and recovery friction; propose a
simpler or faster documented-SDK alternative when it improves Terry's actual
loop. Preserve familiar Lightroom Classic behavior when it is already the best
fit, not by default. Do not duplicate native UI without a concrete benefit, but
do not reject a better FGA interaction merely because it differs from Adobe's.
Track the complete capability inventory and optimization review on FGA
localswim ticket #0065.

Flickr's documented `flickr.photosets.create` method requires a primary Flickr
photo ID, so creating an empty Lightroom album cannot immediately create its
remote Flickr album. Do not upload a placeholder or borrow an unrelated photo
to bypass that contract. The first real published photo is the conventional
primary-photo candidate; FGA localswim tickets #0061 and #0062 track remote
materialization and ambiguous-write repair before implementation.

## Windows version target

Target the latest production/stable Windows major release adopted by the owner.
The owner normally adopts a new Windows major release after its first major
servicing/feature update has shaken out early defects; once adopted, it replaces
the prior Windows release as FGA's sole required Windows client target. Validate
FGA using that Windows target and the latest production Lightroom Classic
release offered through Adobe Creative Cloud. Do not preserve compatibility
with older Windows releases unless a concrete current dependency requires a
documented exception.

## Lightroom diagnostic handoff

Development-only Lightroom plug-ins may write sanitized status or diagnostic
files beneath `C:\Temp` so Codex can monitor long-running Lightroom work. Prefer
a stable, FGA-specific filename or directory and replace the file on each run;
these files are ephemeral and must remain outside Git.

The dedicated FGA Diligence plug-in uses
`C:\Temp\FGA-diligence-status.json` as its stable machine-readable handoff.
Publish each complete JSON state through a temporary sibling file so a monitor
does not mistake a partially written document for a completed update. Treat
only a schema-valid document from the current run with a terminal state as the
run result.

Never write credentials, OAuth headers, access tokens, private Flickr photo
IDs, or unverified photo filenames, paths, captions, locations, or other
metadata to that handoff. Record stages, timings, byte counts, and sanitized
error categories instead. Codex may monitor these files read-only while
Lightroom runs.

## Durable project memory

Treat every LLM context window as disposable cattle, never as a durable project
record. Terry may replace or discard the active context without warning. Chat
history, agent summaries, plans, and uncommitted working state are caches, not
sources of truth.

Within the repository's scope, any fact, decision, rationale, constraint,
procedure, source, artifact location, test result, unresolved issue, or handoff
state that an agent learns and might need in a future turn **MUST** be written
to the appropriate Git-tracked canonical document and committed in that same
turn. Important project knowledge **MUST NOT** exist only in an LLM context
window. Update an existing canonical document when one exists; otherwise use an
ADR for a decision, a research note for evidence, an operations document for a
repeatable procedure, a project log for dated experimental results, or
`AGENTS.md` for a standing engineering instruction.

Record enough provenance, date, rationale, and outcome for a cold-start agent
to recover the knowledge without chat history. Before ending each turn, check
whether any reusable project knowledge still exists only in context; if it
does, persist and commit it before responding. This durability rule does not
weaken privacy, licensing, or secret-handling boundaries: never commit a secret,
private photography data, licensed source material, or other prohibited
content. Persist a sanitized conclusion, provenance pointer, or retrieval
procedure instead.

## Git workflow

Finish every turn that changes repository files by validating the in-scope
work and committing it to the current branch, unless the user explicitly asks
to leave the changes uncommitted. Incremental corrections and design pivots may
remain visible in `main`; do not rewrite otherwise useful history merely to
hide them. Preserve unrelated user changes and do not include them in a commit
without confirming that they belong to the same task.

Terry gave Codex standing authorization on 2026-08-22 to commit and push
in-scope FGA and localswim changes required to keep this project's localswim
integration healthy and reproducible. That authorization includes building and
reinstalling local wheels. On 2026-09-06, Terry expanded the authorization to
all remote pushes of validated, in-scope project work. Commit and push the
current branch without asking again. This does not authorize force-pushing,
changing repository visibility, publishing packages or GitHub releases, or
including unrelated user changes.

## Subagent sidebar names

Terry revised subagent naming on 2026-10-17 because the sidebar normalizes case
and removes punctuation. Use a plain-word model/effort prefix:
`[version, only if not latest for the family] [luna|sol|astra] [light|medium|high]`.
For ticket work, follow the prefix with the four-digit, zero-padded ticket number and a short task
description. Examples: `Sol Medium 0039 Implement`, `Sol High 0065 Review`,
`Luna Light 0144 Check`, and `5.6 Sol Medium 0124 Docs`. For non-ticket work,
use a clear scope label instead of inventing a ticket number.

Omit the version for the latest release of its family. At this update,
`Sol Medium` and `Sol High` mean GPT-6.1 Sol; `Luna Light` means GPT-6 Luna.
Render API effort `low` as `Light`. Reassess the latest-family mapping when
releases change. This naming rule does not authorize new models or efforts;
Astra Medium still requires Terry's explicit approval for each turn.

When the spawn tool requires lowercase letters, digits and underscores, use
`sol_medium_0039_implement`, `sol_high_0065_review`, `luna_light_0144_check`, or
`5_6_sol_medium_0124_docs`. Underscores are tool separators, not a meaningful
part of the display. Accept app-controlled capitalization rather than relying
on punctuation or uppercase initials. Existing agents can be renamed only
through a supported rename capability; do not claim they changed otherwise.

Keep full explicit model and reasoning-effort spawn arguments. In delegation
updates, the plain-word name already identifies the model/effort; do not add a
redundant second pair. Reused agents must keep names matching their actual
configuration. This supersedes the 2026-10-16 compact letter tags for new names,
while preserving ticket-before-description order and concurrency limits.

Terry confirmed the actual sidebar rendering on 2026-10-17: `sol_high_0105_review`
appears as `Sol high 0105 review`, preserving the four-digit ticket. Full words
remain legible after punctuation/case normalization; compact letter tags do not.

## In Progress before ticket work

Terry made this a mandatory execution gate on 2026-10-17:

- Move a ticket to **In Progress before any work on that ticket**, including
  design, implementation, documentation, acceptance recording, tests,
  verification and independent review.
- Move the card before spawning or resuming an agent assigned to it. Recheck
  its lane when resuming work; never begin first and update the board later.
- Keep it In Progress throughout implementation and review. Move to a handoff
  lane only when that work stops. Preserve owner-controlled Completed cards;
  do not silently reopen or continue work on them.

The sequence is: select an eligible card, move it to In Progress, then work or
delegate. A Ready for Work card may retain prerequisites, but the prerequisite
and In Progress gates still govern execution.
