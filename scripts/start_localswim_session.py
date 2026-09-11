"""Ensure both localswim services, monitors, and launch-time board windows.

All orchestration stays in Python. A fixed inline PowerShell command is the
required Windows process-creation boundary because the operating contract
mandates ``Start-Process -WindowStyle Hidden`` for detached children.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import msvcrt
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import uuid
from contextlib import suppress
from ctypes import wintypes
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

if __package__:
    from .watch_localswim import acquire_lock, release_lock
else:
    from watch_localswim import acquire_lock, release_lock

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import IO, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_STORE_ROOT = Path(r"C:\Projects\localswim-state-store")
LOCALSWIM_SOURCE_ROOT = Path(r"C:\Projects\localswim")
UV_CACHE = Path(r"C:\Temp\localswim-uv-cache")
POWERSHELL = Path(r"C:\Program Files\PowerShell\7\pwsh.exe")
MONITOR_SCRIPT = PROJECT_ROOT / "scripts" / "watch_localswim.py"
HOOK_STATUS = Path(r"C:\Temp\FGA-localswim-session-hook-status.json")
SESSION_END_STATUS = Path(r"C:\Temp\FGA-localswim-session-end-hook-status.json")
SESSION_LIFECYCLE_LOCK = Path(r"C:\Temp\FGA-localswim-session-lifecycle.lock")
CHROME_CANDIDATES = (
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
)
MAX_PORT = 65535
POLL_ATTEMPTS = 80
BROWSER_WINDOW_POLL_ATTEMPTS = 100
LIFECYCLE_LOCK_WAIT_SECONDS = 110.0
CHROME_WINDOW_CLASS_PREFIX = "Chrome_WidgetWin_"
TARGET_MONITOR_DEVICE = r"\\.\DISPLAY1"
SW_RESTORE = 9
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
PER_MONITOR_DPI_AWARE = 2
DWMWA_EXTENDED_FRAME_BOUNDS = 9

START_PROCESS_COMMAND = """
$ErrorActionPreference = 'Stop'
$childArguments = @((ConvertFrom-Json -InputObject $env:FGA_LS_CHILD_ARGUMENTS_JSON))
$env:PYTHONIOENCODING = 'utf-8'
$env:UV_CACHE_DIR = $env:FGA_LS_UV_CACHE
Start-Process -FilePath $env:FGA_LS_CHILD_EXECUTABLE `
    -ArgumentList $childArguments `
    -WorkingDirectory $env:FGA_LS_CHILD_WORKING_DIRECTORY `
    -RedirectStandardOutput $env:FGA_LS_CHILD_STDOUT `
    -RedirectStandardError $env:FGA_LS_CHILD_STDERR `
    -WindowStyle Hidden | Out-Null
"""


@dataclass(frozen=True)
class BoardConfig:
    """Paths and labels for one board service and monitor."""

    name: str
    board: Path
    board_label: str
    service_working_directory: Path
    service_stdout: Path
    service_stderr: Path
    monitor_status: Path
    monitor_target: Path
    monitor_lock: Path
    monitor_stdout: Path
    monitor_stderr: Path


@dataclass(frozen=True)
class ServiceStatus:
    """Sanitized loopback service state."""

    reachable: bool
    healthy: bool
    push_state: str | None


@dataclass(frozen=True)
class DesktopRect:
    """One rectangle in virtual-desktop coordinates."""

    left: int
    top: int
    right: int
    bottom: int


@dataclass(frozen=True)
class WindowPlacement:
    """One top-level window position and size."""

    x: int
    y: int
    width: int
    height: int


class MonitorInfo(ctypes.Structure):
    """Windows ``MONITORINFOEXW`` structure."""

    _fields_ = (
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", ctypes.c_wchar * 32),
    )


BOARDS = (
    BoardConfig(
        "FGA",
        STATE_STORE_ROOT / "flickgroupaddr" / "fga-localswim.json",
        "FGA localswim",
        PROJECT_ROOT,
        Path(r"C:\Temp\FGA-localswim.out.log"),
        Path(r"C:\Temp\FGA-localswim.err.log"),
        Path(r"C:\Temp\FGA-localswim-monitor-status.json"),
        Path(r"C:\Temp\FGA-localswim-monitor-target.json"),
        Path(r"C:\Temp\FGA-localswim-monitor.lock"),
        Path(r"C:\Temp\FGA-localswim-monitor.out.log"),
        Path(r"C:\Temp\FGA-localswim-monitor.err.log"),
    ),
    BoardConfig(
        "localswim inception",
        STATE_STORE_ROOT / "localswim" / "localswim.json",
        "localswim inception",
        LOCALSWIM_SOURCE_ROOT,
        Path(r"C:\Temp\localswim-inception.out.log"),
        Path(r"C:\Temp\localswim-inception.err.log"),
        Path(r"C:\Temp\localswim-inception-monitor-status.json"),
        Path(r"C:\Temp\localswim-inception-monitor-target.json"),
        Path(r"C:\Temp\localswim-inception-monitor.lock"),
        Path(r"C:\Temp\localswim-inception-monitor.out.log"),
        Path(r"C:\Temp\localswim-inception-monitor.err.log"),
    ),
)


def parse_hook_input(hook_input_text: str) -> dict[str, object]:
    """Parse one SessionStart input object, or return an empty manual input."""

    if not hook_input_text.strip():
        return {}
    value = cast("object", json.loads(hook_input_text))
    if not isinstance(value, dict):
        raise TypeError("SessionStart input must be a JSON object")
    return cast("dict[str, object]", value)


def resolve_thread_id(
    explicit: str | None,
    hook_input_text: str,
    environment: Mapping[str, str],
) -> str:
    """Return the first valid UUID from explicit, hook, or environment input."""

    raw_session_id = parse_hook_input(hook_input_text).get("session_id")
    session_id = raw_session_id if isinstance(raw_session_id, str) else None
    candidates = [explicit, session_id, environment.get("CODEX_THREAD_ID")]
    for candidate in candidates:
        if candidate:
            try:
                return str(uuid.UUID(candidate))
            except ValueError:
                continue
    raise ValueError("SessionStart supplied no usable UUID Codex thread ID")


def session_start_source(hook_input_text: str) -> str | None:
    """Return the SessionStart source when invoked as a Codex hook."""

    source = parse_hook_input(hook_input_text).get("source")
    if source is None:
        return None
    if not isinstance(source, str):
        raise TypeError("SessionStart source must be a string")
    return source


def should_open_board_browsers(source: str | None) -> bool:
    """Return whether this Codex launch should open both board windows."""

    return source in {"startup", "resume"}


def write_hook_status(
    state: str,
    *,
    thread_id: str | None = None,
    browser_windows_launched: int | None = None,
    error: Exception | None = None,
) -> None:
    """Atomically publish a sanitized SessionStart health handoff."""

    payload: dict[str, object] = {
        "schema": 1,
        "state": state,
        "updatedAt": datetime.now(UTC).isoformat(),
    }
    if thread_id is not None:
        payload["threadId"] = thread_id
    if browser_windows_launched is not None:
        payload["browserWindowsLaunched"] = browser_windows_launched
    if error is not None:
        payload["errorCategory"] = type(error).__name__
        payload["detail"] = str(error)
    temporary = HOOK_STATUS.with_name(f".{HOOK_STATUS.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, separators=(",", ":")),
            encoding="utf-8",
        )
        temporary.replace(HOOK_STATUS)
    finally:
        temporary.unlink(missing_ok=True)


def required_command(name: str) -> Path:
    """Resolve one required application from PATH."""

    resolved = shutil.which(name)
    if resolved is None:
        raise RuntimeError(f"required command is unavailable: {name}")
    return Path(resolved).resolve()


def resolve_chrome(environment: Mapping[str, str]) -> Path:
    """Resolve Google Chrome from PATH or its conventional install locations."""

    candidates: list[Path] = []
    resolved = shutil.which("chrome.exe") or shutil.which("chrome")
    if resolved is not None:
        candidates.append(Path(resolved))
    candidates.extend(CHROME_CANDIDATES)
    local_app_data = environment.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "Google" / "Chrome" / "Application" / "chrome.exe")
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise RuntimeError("Google Chrome is unavailable")


def chrome_board_arguments(port: int) -> tuple[str, str]:
    """Build one visible Chrome-window request for a loopback board."""

    return "--new-window", f"http://127.0.0.1:{port}/"


def split_work_area(work_area: DesktopRect) -> tuple[WindowPlacement, WindowPlacement]:
    """Split one monitor work area into left and right window placements."""

    width = work_area.right - work_area.left
    height = work_area.bottom - work_area.top
    if width <= 0 or height <= 0:
        raise ValueError("monitor work area must have positive width and height")
    left_width = width // 2
    return (
        WindowPlacement(work_area.left, work_area.top, left_width, height),
        WindowPlacement(
            work_area.left + left_width,
            work_area.top,
            width - left_width,
            height,
        ),
    )


def enable_physical_pixel_coordinates() -> None:
    """Use physical monitor pixels for this process's Win32 calls."""

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    set_process_dpi_awareness = user32.SetProcessDpiAwarenessContext
    set_process_dpi_awareness.argtypes = (wintypes.HANDLE,)
    set_process_dpi_awareness.restype = wintypes.BOOL
    if set_process_dpi_awareness(ctypes.c_void_p(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)):
        return
    get_thread_context = user32.GetThreadDpiAwarenessContext
    get_thread_context.restype = wintypes.HANDLE
    get_awareness = user32.GetAwarenessFromDpiAwarenessContext
    get_awareness.argtypes = (wintypes.HANDLE,)
    get_awareness.restype = ctypes.c_int
    if get_awareness(get_thread_context()) == PER_MONITOR_DPI_AWARE:
        return
    raise OSError(
        f"SetProcessDpiAwarenessContext failed with Win32 error {ctypes.get_last_error()}"
    )


def visible_chrome_windows() -> set[int]:
    """Return visible top-level Google Chrome window handles."""

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    enum_callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    enum_windows = user32.EnumWindows
    enum_windows.argtypes = (enum_callback, wintypes.LPARAM)
    enum_windows.restype = wintypes.BOOL
    is_window_visible = user32.IsWindowVisible
    is_window_visible.argtypes = (wintypes.HWND,)
    is_window_visible.restype = wintypes.BOOL
    get_class_name = user32.GetClassNameW
    get_class_name.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
    get_class_name.restype = ctypes.c_int
    handles: set[int] = set()

    def collect_window(hwnd: int, _parameter: int) -> bool:
        if not is_window_visible(hwnd):
            return True
        class_name = ctypes.create_unicode_buffer(256)
        if get_class_name(hwnd, class_name, len(class_name)) <= 0:
            return True
        if class_name.value.startswith(CHROME_WINDOW_CLASS_PREFIX):
            handles.add(hwnd)
        return True

    if not enum_windows(enum_callback(collect_window), 0):
        raise OSError(f"EnumWindows failed with Win32 error {ctypes.get_last_error()}")
    return handles


def monitor_bounds(device_name: str) -> DesktopRect:
    """Return the physical bounds of one Windows display device."""

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    monitor_callback = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HMONITOR,
        wintypes.HDC,
        ctypes.POINTER(wintypes.RECT),
        wintypes.LPARAM,
    )
    enum_display_monitors = user32.EnumDisplayMonitors
    enum_display_monitors.argtypes = (
        wintypes.HDC,
        ctypes.POINTER(wintypes.RECT),
        monitor_callback,
        wintypes.LPARAM,
    )
    enum_display_monitors.restype = wintypes.BOOL
    get_monitor_info = user32.GetMonitorInfoW
    get_monitor_info.argtypes = (wintypes.HMONITOR, ctypes.POINTER(MonitorInfo))
    get_monitor_info.restype = wintypes.BOOL
    monitor_handles: list[int] = []

    def collect_monitor(
        monitor: int,
        _device_context: int,
        _monitor_rect: object,
        _parameter: int,
    ) -> bool:
        monitor_handles.append(monitor)
        return True

    if not enum_display_monitors(None, None, monitor_callback(collect_monitor), 0):
        raise OSError(f"EnumDisplayMonitors failed with Win32 error {ctypes.get_last_error()}")
    for monitor in monitor_handles:
        info = MonitorInfo()
        info.cbSize = ctypes.sizeof(MonitorInfo)
        if not get_monitor_info(monitor, ctypes.byref(info)):
            raise OSError(f"GetMonitorInfoW failed with Win32 error {ctypes.get_last_error()}")
        if info.szDevice == device_name:
            return DesktopRect(
                info.rcMonitor.left,
                info.rcMonitor.top,
                info.rcMonitor.right,
                info.rcMonitor.bottom,
            )
    raise RuntimeError(f"Windows display is unavailable: {device_name}")


def window_bounds(handle: int) -> DesktopRect:
    """Return one top-level window's outer Win32 bounds."""

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    get_window_rect = user32.GetWindowRect
    get_window_rect.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.RECT))
    get_window_rect.restype = wintypes.BOOL
    rect = wintypes.RECT()
    if not get_window_rect(handle, ctypes.byref(rect)):
        raise OSError(f"GetWindowRect failed with Win32 error {ctypes.get_last_error()}")
    return DesktopRect(rect.left, rect.top, rect.right, rect.bottom)


def visible_window_bounds(handle: int) -> DesktopRect:
    """Return one top-level window's visible DWM frame bounds."""

    dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)
    get_window_attribute = dwmapi.DwmGetWindowAttribute
    get_window_attribute.argtypes = (
        wintypes.HWND,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    get_window_attribute.restype = ctypes.c_long
    rect = wintypes.RECT()
    result = get_window_attribute(
        handle,
        DWMWA_EXTENDED_FRAME_BOUNDS,
        ctypes.byref(rect),
        ctypes.sizeof(rect),
    )
    if result != 0:
        raise OSError(f"DwmGetWindowAttribute failed with HRESULT 0x{result & 0xFFFFFFFF:08X}")
    return DesktopRect(rect.left, rect.top, rect.right, rect.bottom)


def compensate_window_frame(
    placement: WindowPlacement,
    outer: DesktopRect,
    visible: DesktopRect,
) -> WindowPlacement:
    """Expand an outer placement so its visible DWM frame matches the target."""

    left_margin = visible.left - outer.left
    top_margin = visible.top - outer.top
    right_margin = outer.right - visible.right
    bottom_margin = outer.bottom - visible.bottom
    return WindowPlacement(
        placement.x - left_margin,
        placement.y - top_margin,
        placement.width + left_margin + right_margin,
        placement.height + top_margin + bottom_margin,
    )


def place_window(handle: int, placement: WindowPlacement) -> None:
    """Restore and position one top-level window through supported Win32 APIs."""

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    show_window = user32.ShowWindow
    show_window.argtypes = (wintypes.HWND, ctypes.c_int)
    show_window.restype = wintypes.BOOL
    set_window_pos = user32.SetWindowPos
    set_window_pos.argtypes = (
        wintypes.HWND,
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    )
    set_window_pos.restype = wintypes.BOOL
    show_window(handle, SW_RESTORE)
    outer_placement = placement
    for _attempt in range(2):
        if not set_window_pos(
            handle,
            None,
            outer_placement.x,
            outer_placement.y,
            outer_placement.width,
            outer_placement.height,
            SWP_NOZORDER | SWP_NOACTIVATE,
        ):
            raise OSError(f"SetWindowPos failed with Win32 error {ctypes.get_last_error()}")
        visible = visible_window_bounds(handle)
        if visible == DesktopRect(
            placement.x,
            placement.y,
            placement.x + placement.width,
            placement.y + placement.height,
        ):
            return
        outer_placement = compensate_window_frame(placement, window_bounds(handle), visible)
    raise RuntimeError("Chrome visible frame did not reach its requested bounds")


def wait_for_new_chrome_window(previous_handles: set[int]) -> int:
    """Return the handle of a newly visible Chrome window."""

    for _attempt in range(BROWSER_WINDOW_POLL_ATTEMPTS):
        new_handles = visible_chrome_windows() - previous_handles
        if new_handles:
            return min(new_handles)
        time.sleep(0.1)
    raise RuntimeError("new Google Chrome window did not become visible")


def launch_board_browsers(chrome: Path, ports: Mapping[str, int]) -> int:
    """Launch and place one visible Chrome window for each healthy board."""

    enable_physical_pixel_coordinates()
    creation_flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    observed_handles = visible_chrome_windows()
    launched_handles: list[int] = []
    for config in BOARDS:
        process = subprocess.Popen(  # noqa: S603 -- resolved Chrome GUI executable
            (str(chrome), *chrome_board_arguments(ports[config.name])),
            cwd=PROJECT_ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
        time.sleep(0.5)
        return_code = process.poll()
        if return_code not in (None, 0):
            raise RuntimeError(f"Chrome window launch failed with exit code {return_code}")
        window_handle = wait_for_new_chrome_window(observed_handles)
        launched_handles.append(window_handle)
        observed_handles.add(window_handle)
    placements = split_work_area(monitor_bounds(TARGET_MONITOR_DEVICE))
    for handle, placement in zip(launched_handles, placements, strict=True):
        place_window(handle, placement)
    return len(launched_handles)


def run_checked(arguments: Sequence[str], *, timeout: int) -> str:
    """Run one resolved executable and return its UTF-8 output."""

    completed = subprocess.run(  # noqa: S603 -- callers resolve each executable
        arguments,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "no diagnostic output").splitlines()[0]
        raise RuntimeError(f"command failed: {detail[:300]}")
    return completed.stdout.strip()


def install_localswim_if_missing(uv: Path) -> Path:
    """Ensure both editable localswim console commands are installed."""

    service = shutil.which("localswim")
    client = shutil.which("localswim-cli")
    if service is not None and client is not None:
        return Path(service).resolve()
    run_checked(
        (
            str(uv),
            "tool",
            "install",
            "--cache-dir",
            str(UV_CACHE),
            "--python",
            "3.14.7",
            "--editable",
            str(LOCALSWIM_SOURCE_ROOT),
        ),
        timeout=120,
    )
    tool_directory = Path(run_checked((str(uv), "tool", "dir", "--bin"), timeout=30))
    service_path = tool_directory / "localswim.exe"
    if not service_path.is_file() or not service_path.with_name("localswim-cli.exe").is_file():
        raise RuntimeError("editable localswim install did not provide both console commands")
    return service_path


def read_board_port(board: Path, jq: Path) -> int:
    """Read only the embedded board port through jq."""

    board.resolve(strict=True)
    text = run_checked((str(jq), "-r", ".port", str(board)), timeout=10)
    try:
        port = int(text)
    except ValueError as exc:
        raise ValueError(f"board has an invalid embedded port: {board}") from exc
    if not 1 <= port <= MAX_PORT:
        raise ValueError(f"board has an invalid embedded port: {board}")
    return port


def interpret_service_status(value: object) -> ServiceStatus:
    """Validate the status fields needed by this launcher."""

    if not isinstance(value, dict):
        return ServiceStatus(reachable=True, healthy=False, push_state=None)
    status = cast("dict[str, object]", value)
    push = status.get("push")
    push_state = None
    if isinstance(push, dict):
        possible_state = cast("dict[str, object]", push).get("state")
        push_state = possible_state if isinstance(possible_state, str) else None
    return ServiceStatus(
        reachable=True,
        healthy=status.get("ok") is True and push_state == "ok",
        push_state=push_state,
    )


def get_service_status(port: int) -> ServiceStatus:
    """Read sanitized loopback health without reading board content."""

    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/v001/status",
            timeout=2,
        ) as response:
            return interpret_service_status(cast("object", json.load(response)))
    except OSError, TimeoutError, ValueError:
        return ServiceStatus(reachable=False, healthy=False, push_state=None)


def launch_hidden(
    executable: Path,
    arguments: Sequence[str],
    working_directory: Path,
    stdout_path: Path,
    stderr_path: Path,
) -> None:
    """Launch one child through the required Windows-native boundary."""

    POWERSHELL.resolve(strict=True)
    child_environment = os.environ.copy()
    child_environment.update(
        {
            "FGA_LS_CHILD_EXECUTABLE": str(executable),
            "FGA_LS_CHILD_ARGUMENTS_JSON": json.dumps(list(arguments)),
            "FGA_LS_CHILD_WORKING_DIRECTORY": str(working_directory),
            "FGA_LS_CHILD_STDOUT": str(stdout_path),
            "FGA_LS_CHILD_STDERR": str(stderr_path),
            "FGA_LS_UV_CACHE": str(UV_CACHE),
            "PYTHONIOENCODING": "utf-8",
            "UV_CACHE_DIR": str(UV_CACHE),
        }
    )
    process = subprocess.Popen(  # noqa: S603 -- fixed PowerShell launch boundary
        (str(POWERSHELL), "-NoProfile", "-Command", START_PROCESS_COMMAND),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=child_environment,
    )
    try:
        return_code = process.wait(timeout=30)
    except subprocess.TimeoutExpired as exc:
        process.kill()
        process.wait()
        raise RuntimeError("hidden child launcher timed out") from exc
    if return_code != 0:
        try:
            stdout, stderr = process.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            stdout = stderr = ""
        detail = (stderr or stdout or "no diagnostic output").splitlines()[0]
        raise RuntimeError(f"hidden child launch failed: {detail[:300]}")
    for stream in (process.stdout, process.stderr):
        if stream is not None:
            stream.close()


def wait_for_healthy_service(config: BoardConfig, port: int) -> None:
    """Wait for loopback health and successful autopush state."""

    for _attempt in range(POLL_ATTEMPTS):
        if get_service_status(port).healthy:
            return
        time.sleep(0.25)
    status = get_service_status(port)
    if status.reachable:
        raise RuntimeError(f"{config.name} service is reachable but push.state is not ok")
    raise RuntimeError(f"{config.name} service did not become reachable")


def ensure_service(config: BoardConfig, service: Path, port: int) -> None:
    """Reuse one healthy service or launch one unavailable service."""

    status = get_service_status(port)
    if status.healthy:
        return
    if not status.reachable:
        launch_hidden(
            service,
            ("--autopush", str(config.board)),
            config.service_working_directory,
            config.service_stdout,
            config.service_stderr,
        )
    wait_for_healthy_service(config, port)


def read_json_object(path: Path) -> dict[str, Any]:
    """Read one sanitized monitor-owned handoff."""

    value = cast("object", json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(value, dict):
        raise TypeError(f"expected a JSON object in {path}")
    return cast("dict[str, Any]", value)


def monitor_lock_is_held(path: Path) -> bool:
    """Report whether a live monitor owns its byte-range lock."""

    try:
        handle = path.open("a+b")
    except OSError:
        return False
    with handle:
        if handle.seek(0, os.SEEK_END) == 0:
            return False
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            return True
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    return False


def shutdown_is_pending() -> bool:
    """Report whether a SessionEnd trigger or coordinator is still active."""

    try:
        status = read_json_object(SESSION_END_STATUS)
    except OSError, TypeError, ValueError:
        return False
    return status.get("state") in {"launching", "stopping"}


def wait_for_lifecycle_lock() -> IO[bytes]:
    """Serialize startup behind any detached SessionEnd coordinator."""

    deadline = time.monotonic() + LIFECYCLE_LOCK_WAIT_SECONDS
    while time.monotonic() < deadline:
        if shutdown_is_pending():
            time.sleep(0.1)
            continue
        lock = acquire_lock(SESSION_LIFECYCLE_LOCK)
        if lock is not None:
            if not shutdown_is_pending():
                return lock
            release_lock(lock)
        time.sleep(0.1)
    raise RuntimeError("the previous localswim shutdown coordinator is still running")


def monitor_is_healthy(config: BoardConfig, thread_id: str) -> bool:
    """Validate handoffs and the live lock for one monitor."""

    try:
        status = read_json_object(config.monitor_status)
        target = read_json_object(config.monitor_target)
    except OSError, TypeError, ValueError:
        return False
    observed_board = status.get("board")
    return (
        status.get("state") == "running"
        and isinstance(observed_board, str)
        and Path(observed_board).resolve() == config.board.resolve()
        and target.get("threadId") == thread_id
        and monitor_lock_is_held(config.monitor_lock)
    )


def ensure_monitor(config: BoardConfig, uv: Path, port: int, thread_id: str) -> None:
    """Launch or retarget one monitor, then verify it."""

    arguments = (
        "run",
        "--frozen",
        "python",
        str(MONITOR_SCRIPT),
        "--board-path",
        str(config.board),
        "--board-label",
        f'"{config.board_label}"',
        "--thread-id",
        thread_id,
        "--port",
        str(port),
        "--status-path",
        str(config.monitor_status),
        "--target-path",
        str(config.monitor_target),
        "--lock-path",
        str(config.monitor_lock),
    )
    launch_hidden(
        uv,
        arguments,
        PROJECT_ROOT,
        config.monitor_stdout,
        config.monitor_stderr,
    )
    for _attempt in range(POLL_ATTEMPTS):
        if monitor_is_healthy(config, thread_id):
            return
        time.sleep(0.25)
    raise RuntimeError(f"{config.name} monitor did not become healthy and thread-targeted")


def run(thread_id: str, *, open_board_browsers: bool = False) -> int:
    """Ensure services and monitors, then optionally open both board windows."""

    lifecycle_lock = wait_for_lifecycle_lock()
    try:
        STATE_STORE_ROOT.resolve(strict=True)
        LOCALSWIM_SOURCE_ROOT.resolve(strict=True)
        jq = required_command("jq")
        uv = required_command("uv")
        service = install_localswim_if_missing(uv)
        ports = {config.name: read_board_port(config.board, jq) for config in BOARDS}
        for config in BOARDS:
            ensure_service(config, service, ports[config.name])
        for config in BOARDS:
            ensure_monitor(config, uv, ports[config.name], thread_id)
        if open_board_browsers:
            return launch_board_browsers(resolve_chrome(os.environ), ports)
        return 0
    finally:
        release_lock(lifecycle_lock)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the optional manual-test thread override."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--thread-id")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the hook with concise JSON success or stderr failure output."""

    args = parse_args(argv)
    hook_input = "" if args.thread_id else sys.stdin.read()
    try:
        source = session_start_source(hook_input)
        thread_id = resolve_thread_id(args.thread_id, hook_input, os.environ)
        browser_windows_launched = run(
            thread_id,
            open_board_browsers=should_open_board_browsers(source),
        )
    except Exception as exc:  # noqa: BLE001 -- final hook boundary
        with suppress(OSError):
            write_hook_status("error", error=exc)
        print(f"localswim SessionStart hook failed: {exc}", file=sys.stderr, flush=True)
        return 1
    with suppress(OSError):
        write_hook_status(
            "ok",
            thread_id=thread_id,
            browser_windows_launched=browser_windows_launched,
        )
    browser_context = ""
    if browser_windows_launched:
        browser_context = " One visible Chrome window was launched for each board."
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": (
                        "Both required localswim services are healthy with autopush enabled, and "
                        "both board-write monitors are running and targeted at this Codex thread."
                        f"{browser_context}"
                    ),
                }
            },
            separators=(",", ":"),
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
