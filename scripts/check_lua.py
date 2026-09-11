"""Run the complete FGA Lua quality gate."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_ROOT = REPOSITORY_ROOT / "lightroom"
TEMPORARY_ROOT = REPOSITORY_ROOT / ".tmp" / "lua-check"
ADOBE_COMPILER = (
    REPOSITORY_ROOT / "vendor" / "LrC SDK" / "15.3" / "Lua Compiler" / "win" / "luac.exe"
)


def local_app_data_path(*parts: str) -> Path | None:
    """Return a path beneath LOCALAPPDATA when the variable is available."""

    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return None
    return Path(local_app_data, *parts)


def resolve_tool(command_name: str, fallback: Path | None) -> Path:
    """Resolve a tool from PATH and then its documented Windows fallback."""

    command = shutil.which(command_name)
    if command:
        return Path(command)
    if fallback and fallback.is_file():
        return fallback
    message = (
        f"Required tool '{command_name}' was not found. "
        "See docs/operations/development-environment.md."
    )
    raise RuntimeError(message)


def run_tool(label: str, command: list[str]) -> None:
    """Run one resolved local quality tool and stop on failure."""

    print(label, flush=True)
    completed = subprocess.run(  # noqa: S603 - executable paths are resolved locally
        command,
        cwd=REPOSITORY_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        message = f"{label} failed with exit code {completed.returncode}."
        raise RuntimeError(message)


def main() -> None:
    """Run Luacheck, Adobe syntax compilation, and LuaLS diagnostics."""

    lua_files = sorted(PLUGIN_ROOT.rglob("*.lua"))
    if not lua_files:
        message = f"No Lua files found under '{PLUGIN_ROOT}'."
        raise RuntimeError(message)

    luacheck = resolve_tool(
        "luacheck",
        local_app_data_path("Programs", "Luacheck", "luacheck.exe"),
    )
    lua_language_server = resolve_tool(
        "lua-language-server",
        local_app_data_path(
            "Microsoft",
            "WinGet",
            "Packages",
            "LuaLS.lua-language-server_Microsoft.Winget.Source_8wekyb3d8bbwe",
            "bin",
            "lua-language-server.exe",
        ),
    )

    run_tool(
        "Luacheck",
        [
            str(luacheck),
            "--config",
            str(REPOSITORY_ROOT / ".luacheckrc"),
            str(PLUGIN_ROOT),
        ],
    )

    if ADOBE_COMPILER.is_file():
        print("Adobe Lua 5.1 syntax compiler", flush=True)
        for lua_file in lua_files:
            run_tool(
                f"Adobe syntax: {lua_file.relative_to(REPOSITORY_ROOT)}",
                [str(ADOBE_COMPILER), "-p", str(lua_file)],
            )
    else:
        print(
            "Adobe Lua compiler not found; syntax compilation skipped. "
            "Install the licensed SDK locally.",
            file=sys.stderr,
        )

    TEMPORARY_ROOT.mkdir(parents=True, exist_ok=True)
    run_tool(
        "Lua Language Server workspace diagnostics",
        [
            str(lua_language_server),
            f"--check={REPOSITORY_ROOT}",
            "--checklevel=Warning",
            "--check_format=pretty",
            f"--configpath={REPOSITORY_ROOT / '.luarc.json'}",
            f"--logpath={TEMPORARY_ROOT}",
        ],
    )
    print(f"Validated {len(lua_files)} Lua file(s).")


if __name__ == "__main__":
    main()
