# Development environment

Last updated: 2026-08-26

## Lightroom Classic version

The installed application is Lightroom Classic 15.5, build
`202607291506-b8869fa7`, with Camera Raw 18.5. FGA targets the latest production
Lightroom Classic release rather than maintaining compatibility with older
versions. Adobe's newest downloadable SDK currently remains 15.3; use the
newest SDK Adobe publishes even when it trails the application minor release.
Terry reaffirmed on 2026-08-26 that keeping the installed application on the
latest stable release is an owner responsibility and supported-operation
requirement.

Adobe's developer console identifies a Lightroom Classic **App Version** by
product year, while Lightroom's About dialog reports the numeric application
version. A useful, non-absolute mapping from the console's product year to the
SDK/application major is `product year - 2011`; selecting App Version 2026
therefore exposes the 15.x SDK series, while the installed application reports
15.5. Always verify the installed application and published SDK instead of
treating that heuristic as a compatibility contract.

The observed SDK cadence labels the coming product year with a `.0` release
around October, then publishes minor SDK updates during that product year:

| Product year | Observed SDK releases |
| --- | --- |
| 2024 | 13.0 (Oct 2023), 13.2 (Feb 2024), 13.3 (May 2024), 13.5 (Aug 2024) |
| 2025 | 14.0 (Oct 2024), 14.1 (Dec 2024), 14.2 (Feb 2025), 14.3 (Apr 2025) |
| 2026 | 15.0 (Oct 2025), 15.1 (Dec 2025), 15.2 (Feb 2026), 15.3 (Apr 2026) |

These are observations from Adobe's SDK download selector, not a promised
schedule. Application minor releases can move ahead of the latest downloadable
SDK; target the installed application while coding against the newest published
SDK contract. The actual release event, not the assumed month, triggers the
[development and operations diligence cadence](development-and-operations-cadence.md).

The durable client target is the latest production Lightroom Classic release
offered through Adobe Creative Cloud on the latest production/stable Windows
release adopted by the owner. The owner normally adopts a new Windows major
release after its first major servicing/feature update has shaken out early
defects; once adopted, it replaces the prior Windows release as FGA's required
client target. Windows 11 is the current environment, not a permanent
compatibility constraint.

## Workspace

The repository was moved from a NAS share to the local SSD at:

```text
C:\Projects\FGA\architecture-design
```

This avoids the sandbox/elevation problems encountered while the project was
on a network share.

## Shell

PowerShell 7.4.19 is installed at:

```text
C:\Program Files\PowerShell\7\pwsh.exe
```

It runs successfully from a standard, non-administrator shell. Administrator
PowerShell is not required for normal repository work. It remains useful as an
interactive Windows shell and appears in historical project-log commands, but
the repository has no active PowerShell script after the 2026-08-21 script-
language audit.

## Script language audit

The 2026-08-21 audit applied the repository's "coin flip goes to Python" rule
to every active script, regardless of its starting language:

- all operational files under `scripts/` are Python;
- all automated tests are Python;
- the former PowerShell PNG analyzer, Lua quality gate, and Python quality gate
  were straightforward filesystem/subprocess orchestration and were ported to
  Python without losing behavior; and
- no active PowerShell, shell, JavaScript, or other general-purpose script
  remains.

The files inside `lightroom/FGA Diagnostics.lrdevplugin/` remain Lua because
Lightroom Classic's plug-in runtime executes Lua 5.1, not Python. Porting
`Info.lua`, the command entry points, or the plug-in implementation would make
them unloadable and therefore fails the functionality test decisively.
`dkjson.lua` likewise remains Lua because it is the plug-in's vendored runtime
JSON implementation. Reapply the language test when any script is materially
changed or a new script is proposed; do not assume that a historical language
choice remains justified forever.

## Codex localswim session hook

Codex lifecycle-hook behavior was verified against the
[official OpenAI Docs Hooks reference](https://learn.chatgpt.com/codex/hooks)
on 2026-08-23. Project-local hooks live in `.codex/hooks.json`, run only for a
trusted project, and require review through `/hooks` whenever their definition
hash changes. The FGA `SessionStart` hook matches `startup`, `resume`, and
`clear`, but deliberately excludes `compact`: compaction retains the same live
thread and does not justify restarting or retargeting operating processes. The
synchronous `SessionEnd` hook runs for a clean `/exit` and uses Codex's
documented three-second maximum timeout.

The hook runs `scripts/start_localswim_session.py` through the frozen uv
environment. All orchestration, validation, health checking, and error handling
is Python. The launcher uses one fixed inline PowerShell command only for the
required Windows-native `Start-Process -WindowStyle Hidden` call; no PowerShell
script is checked in.

The hook synchronously verifies readiness, then returns normally. The four
long-lived children are hidden and detached:

1. FGA localswim service on the FGA board's embedded port, currently `8793`;
2. localswim inception service on its embedded port, currently `8794`;
3. FGA board-write monitor targeted at the active Codex thread; and
4. localswim inception board-write monitor targeted at the same thread.

The monitors call `codex queue`, whose supported command surface queues a
submission for a later turn rather than acknowledging delivery to an already
running turn. Their messages therefore identify themselves as next-turn alerts.
They are useful diagnostics, but are not the priority enforcement boundary.
Immediately before transitioning from inception work to FGA work, run:

```console
uv run --frozen python scripts/check_localswim_priority.py
```

The command queries both actionable inception lanes through `localswim-cli`.
Exit `0` permits the FGA handoff. Any nonzero exit refuses it and the sanitized
message distinguishes actionable inception work from an operational failure.

For a `startup` or `resume` event, the launcher then starts one visible Google
Chrome window per board with `--new-window` and the board's loopback URL. It
does not open browser windows for `clear`. Chrome launch requests are made from
Python as detached GUI processes; the explicit user-visible browser boundary is
separate from the hidden service and monitor boundary.

The launcher reads only each board's `port` through `jq`. It checks service
health through the loopback status endpoint and monitor health through the
sanitized status and target handoffs. It never reads or logs board content.
Both services use `--autopush`; a reachable service whose push state does not
become `ok` is an error, not a reason to launch a duplicate.

On clean `/exit`, `scripts/trigger_localswim_shutdown.py` starts a hidden,
detached `scripts/stop_localswim_session.py` coordinator and returns promptly.
This split is required because `SessionEnd` cannot delay Codex for more than
three seconds. Codex may exit before cleanup finishes; the detached coordinator
continues independently and records progress in
`C:\Temp\FGA-localswim-session-end-hook-status.json` as `launching`, `stopping`,
`stopped`, or `error`.

The coordinator owns `C:\Temp\FGA-localswim-session-lifecycle.lock` and writes
an exact-PID stop request to each monitor's transient target file. A monitor
remains live while its paired service is healthy, which lets it recover if
shutdown is refused. The coordinator then invokes
`localswim-cli <board> board shutdown` for each service. That authenticated command
quiesces mutations, performs one final autopush, closes request threads, removes
the service descriptor, and reports success only after cleanup. Once the
service becomes unavailable, its monitor records `stopped`, releases its
lifetime lock, and exits normally. The coordinator never uses forced process
termination. A later `SessionStart` treats `launching` and `stopping` as active,
then waits to acquire the same lifecycle lock. The status check covers the brief
interval before the detached coordinator owns the lock, preventing startup from
racing the previous shutdown.

Closing a window is not treated as a guaranteed lifecycle event. Use `/exit`
when clean teardown is required; the next `SessionStart` recreates all four
background processes.

The SessionStart payload's `session_id` takes precedence over an inherited
`CODEX_THREAD_ID`; this matters when a Codex process starts a nested session.
The launcher atomically publishes its sanitized terminal state to
`C:\Temp\FGA-localswim-session-hook-status.json`. An `ok` state includes the
target thread ID. An `error` state includes only the exception category and
operational detail. A successful state also records the number of Chrome window
launch requests completed for that event.

Transient service logs are `C:\Temp\FGA-localswim.out.log`,
`C:\Temp\FGA-localswim.err.log`, `C:\Temp\localswim-inception.out.log`, and
`C:\Temp\localswim-inception.err.log`. Monitor logs and handoffs retain the
board-specific paths in `AGENTS.md` and `C:\Projects\localswim\AGENTS.md`.
None is durable project state.

### Lifecycle test isolation

Repository tests must not address the production board files, service
descriptors, loopback endpoints, lifecycle lock, hook handoffs, monitor
handoffs, targets, or logs. The lifecycle test modules inherit
`tests/lifecycle_test_support.py`, which replaces every mutable lifecycle path
with a unique `TemporaryDirectory` tree before each test method. Both test
boards, their working directories, hook and coordinator state, monitor state,
and all logs are beneath that tree. The test process also points `TEMP` and
`TMP` at a test-owned directory so any accidentally invoked localswim child
would derive its service descriptor there rather than in the live descriptor
directory.

The shared test boundary rejects unstubbed child-process creation and loopback
HTTP requests. A test that examines a subprocess or endpoint interaction must
install its own mock inside that boundary. This makes a missing mock fail the
test before a real `localswim-cli <board> board shutdown`, SessionStart child,
SessionEnd coordinator, or status request can occur. Regression tests assert
that every configured mutable path is test-owned, hook writes are redirected,
and unstubbed shutdown and endpoint attempts fail closed.

The 2026-08-26 audit could not identify a specific unmocked lifecycle call in
the previously passing suite; the tests mocked the obvious subprocesses. It did
identify the structural defect that the tests imported production `BOARDS` and
`C:\Temp` paths and depended on complete mocking for safety. After replacing
that coupling, all 33 focused lifecycle tests and the full 98-test suite passed.
Both live services remained healthy with autopush state `ok`, and the
SHA2-256 digests of every live localswim service descriptor were identical
before and after each run.

Initial acceptance on 2026-08-23 passed Ruff formatting and linting, strict
Pyright, and all 13 Python unit tests. Both the manual thread override and the
real `SessionStart` standard-input shape reused the healthy services, confirmed
both autopush states, and retargeted both live monitor locks successfully.
During that edit session, Codex 0.149.0 recorded an elevated Windows sandbox
provisioning `helper_unknown_error`; Codex Doctor still loaded configuration
successfully and reported the stable `hooks` feature enabled. The acceptance
commands therefore ran through approved outside-sandbox execution. Recheck the
sandbox in a fresh session before treating that helper failure as persistent or
attributing it to the hook.

A live trust-gate check on 2026-08-23 showed the hook as installed and active in
`/hooks`, and a normal interactive startup attempted the hook without a trust
bypass. That check also exposed a Windows command-boundary defect before Python
started: a quoted executable path was not invocable by the PowerShell command
runner without its call operator. The hook command now uses unquoted absolute
paths, all of which contain no spaces. After Terry reviewed and trusted that
exact replacement definition, final live acceptance passed in a fresh normal
Codex session without a trust-bypass flag: the UI reported the `SessionStart`
hook completed, its additional context reached the model, the sanitized hook
handoff was `ok`, both services were healthy with autopush state `ok`, and both
running monitors targeted the fresh session. The disposable session was then
closed and both monitors were retargeted to the active FGA Codex thread.

The startup-browser extension added on 2026-08-23 passed Ruff formatting and
linting, strict Pyright, and all 17 Python unit tests. Its final visible-GUI
acceptance is deliberately the next clean new-session test: begin with both
services and monitors stopped and Chrome closed, submit the first prompt, then
confirm two Chrome windows and a sanitized hook status whose
`browserWindowsLaunched` value is `2`.

## Git ownership in the sandbox

The working tree is owned by the normal Windows user, while commands run in the
sandbox as `CodexSandboxOffline`. Git therefore reports “detected dubious
ownership” unless a safe-directory override is provided.

Use a command-scoped override:

```powershell
git -c safe.directory=C:/Projects/FGA/architecture-design `
    -c core.excludesFile=.git/info/exclude status
```

This avoids modifying global Git configuration and prevents the sandboxed Git
process from reading the normal user's inaccessible global ignore file. The
repository `.gitignore` still applies. Use both overrides on the first
invocation of every sandboxed, read-only Git command from the repository root.

## Licensed SDK

The Lightroom Classic SDK is stored under `vendor/LrC SDK/` but ignored by Git.
See that directory's tracked README for restoration instructions.

## Lua tooling

The Lightroom code targets Lua 5.1. This workstation has:

- Lua Language Server 3.18.2, installed through WinGet;
- Luacheck 0.23.0, the official upstream standalone Windows executable; and
- Adobe's Lua 5.1 compiler from the locally licensed Lightroom Classic SDK.

The project configuration lives in `.luarc.json` and `.luacheckrc`. LuaLS
enables the ambiguity, duplicate, global, redefinition, strict, type-check,
unbalanced, and unused diagnostic groups throughout the workspace. Luacheck
uses its Lua 5.1 standard and keeps its normal unused-variable/argument and
line-length checks. Style-only, coroutine-await, and maximum-strength unknown
type checks are deliberately not forced on: Lightroom's SDK modules are loaded
dynamically through `import`, so those checks would create noise without
finding meaningful defects.

Run all checks from the repository root:

```powershell
uv run --frozen python scripts\check_lua.py
```

The script resolves the tools from `PATH` and falls back to their standard
per-user install locations. It also finds the SDK compiler at
`vendor/LrC SDK/15.3/Lua Compiler/win/luac.exe`. A fresh shell may be needed
before the newly installed Luacheck directory appears in `PATH`.

LuaLS is the current semantic analyzer and language-server implementation.
Luacheck 0.23.0 is older because upstream's newer LuaRocks release needs a
native compiler that is not otherwise required by this project; it remains a
useful independent Lua 5.1 linter. The project check script makes the exact
combination reproducible.

## Python integration-test tooling

uv 0.12.5 manages the repository's project-local Python 3.14 environment.
`.python-version` pins CPython 3.14.7, `pyproject.toml` is the single source for
direct development dependencies and Python analysis configuration, and the
committed `uv.lock` pins the complete transitive environment. `.venv/` is
generated and ignored. This follows localswim's proven uv project layout while
leaving FGA as a non-package project.

Use `uv sync --locked` to create the environment and `uv run --frozen ...` for
repository Python commands. This makes the selected environment explicit and
prevents commands from silently changing the lock. In the Codex Windows
sandbox, the trusted project [`.codex/config.toml`](../../.codex/config.toml)
uses Codex's documented `shell_environment_policy.set` boundary to inject
`UV_CACHE_DIR=C:\Users\TDO-XPS15-2024\AppData\Local\Temp\localswim-uv-cache`
into every spawned repository command. This is the long-path spelling of the
permission profile's writable `$env:TEMP\localswim-uv-cache`; it avoids relying
on each command author to remember an assignment. Official Codex documentation
defines both [trusted project config
layers](https://developers.openai.com/codex/config-reference) and explicit
shell-environment injection.

The older `C:\Temp\localswim-uv-cache` is not a Windows ACL defect: the visible
ACL grants the sandbox identity's groups modify access, but the Codex filesystem
policy still refuses the path. A sandboxed control run on 2026-08-26 reproduced
`os error 5` beneath its `sdists-v9` entry, while the same frozen command using
the configured system-temp path exited successfully. After the project setting
was added, a fresh `codex sandbox --permission-profile :workspace` process with
no manual `UV_CACHE_DIR` assignment observed the exact configured value and
completed `uv run --frozen`. Codex's strict config parser and doctor also loaded
the trusted project layer successfully. Do not grant the sandbox write access
to `C:\Temp`, rewrite inherited ACLs, delete the shared cache, or run routine
validation outside the sandbox to bypass that policy.

The separate `C:\Temp` tree remains the transient location for detached
localswim lifecycle processes and does not become a sandbox workspace root.
The Python lifecycle launchers explicitly set the old cache only for their
outside-sandbox child processes, so the project environment value does not
change that contract. Durable uv user-level writes still require the normal
outside-sandbox approval. In an untrusted project context where Codex correctly
ignores `.codex/config.toml`, set `UV_CACHE_DIR` to
`$env:TEMP\localswim-uv-cache` manually before a repository command.

The spike uses `flickrapi` 2.4.0, which carries the OSI-approved Python license,
for OAuth 1.0a, Flickr REST calls, and Flickr's unusual multipart-upload signing
rule. This dependency is test tooling and does not select Python as the hosted
service implementation language.

Ruff 0.16.3 now uses localswim's `select = ["ALL"]`, formatting rules, 100-column
limit, Python 3.14 target, and documented project-level exceptions. FGA retains
only narrow file-level exceptions justified by test fixtures or explicit
boundary behavior. Pyright 1.1.411 runs in strict, platform-independent mode
and also installs `pyright-langserver`. Only the unknown-value reports caused
by `flickrapi`'s dynamic, untyped response surface are disabled, and only in the
two files that directly cross that boundary.

Pydantic is not currently included. It is a runtime validation library rather
than a linter, and the present signer envelope remains clearer as a dataclass
plus explicit boundary checks. Reconsider it when the hosted service has
substantial request, response, or persisted-data models.

Run the complete Python quality gate from the repository root:

```powershell
uv run --frozen python scripts\check_python.py
```

The gate runs Ruff formatting, Ruff `ALL`, strict Pyright, and the unit tests
inside the frozen uv environment. The first signer regression test captures
the observed `requests-oauthlib` behavior where an OAuth authorization header
can be returned as bytes and verifies that FGA converts it to JSON-safe text.

## Lightroom SDK API comparison tooling

Run `uv run --frozen python scripts/compare_lightroom_sdk_api.py` when Adobe publishes a
new major SDK. It compares the previous and current licensed SDK HTML
documentation for added, removed, and signature/summary-changed calls and
writes the complete local report beneath `C:\Temp`. Keep generated inventories
and Adobe SDK files outside Git. The required interpretation and assumption audit are in the
[development and operations diligence cadence](development-and-operations-cadence.md#annual-lightroom-sdk-call-zoo-review).

## Documentation tooling

The [Eclipse Temurin](https://adoptium.net/temurin/) JRE 25.0.4.1 is installed
through WinGet as
`EclipseAdoptium.Temurin.25.JRE`. It is a local documentation-tool dependency,
not a selected FGA service runtime. Its Java executable is currently:

```text
C:\Program Files\Eclipse Adoptium\jre-25.0.4.101-hotspot\bin\java.exe
```

The official
[PlantUML 1.2026.6](https://github.com/plantuml/plantuml/releases/tag/v1.2026.6)
JAR is deliberately kept outside Git at `C:\Temp\FGA-tools\plantuml.jar`.
Its verified SHA2-256 digest is:

```text
89948f14c93756c7a3fb7b69078ff37e8489fd79dd430c582b931e2f65358690
```

Validate every checked-in PlantUML diagram from the repository root with:

```powershell
$java = 'C:\Program Files\Eclipse Adoptium\jre-25.0.4.101-hotspot\bin\java.exe'
& $java -jar 'C:\Temp\FGA-tools\plantuml.jar' -checkonly 'docs\diagrams\*.puml'
```

PlantUML's standard JAR is GPL-licensed. It remains a local executable tool and
is neither linked into FGA nor distributed in this MIT repository. PlantUML
source is the maintained artifact. Rendered files belong in a temporary output
directory unless the repository later chooses to publish generated
documentation deliberately.

### Local Chrome diagram preview

Google Chrome is installed at:

```text
C:\Program Files\Google\Chrome\Application\chrome.exe
```

Codex can render a PlantUML source as SVG beneath the ignored
`.tmp\rendered-diagrams` directory and launch that local file in Chrome when
Terry requests an interactive preview. Launching a visible desktop application
requires the normal Codex GUI approval; no additional browser integration or
browser extension is required. SVG is preferred for this preview because
Chrome can zoom it without degrading labels or connector lines.
