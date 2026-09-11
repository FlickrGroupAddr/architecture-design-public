"""Tests for the project-local Codex uv-cache boundary."""

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CODEX_CONFIG = REPOSITORY_ROOT / ".codex" / "config.toml"
DEVELOPMENT_ENVIRONMENT = REPOSITORY_ROOT / "docs" / "operations" / "development-environment.md"
EXPECTED_SANDBOX_CACHE = r"C:\Users\TDO-XPS15-2024\AppData\Local\Temp\localswim-uv-cache"
EXPECTED_DETACHED_CACHE = r"C:\Temp\localswim-uv-cache"


class CodexUvCacheConfigTests(unittest.TestCase):
    def test_project_config_injects_only_the_sandbox_cache_value(self) -> None:
        with CODEX_CONFIG.open("rb") as stream:
            config = tomllib.load(stream)

        self.assertEqual(
            config,
            {"shell_environment_policy": {"set": {"UV_CACHE_DIR": EXPECTED_SANDBOX_CACHE}}},
        )

    def test_detached_lifecycle_launchers_keep_their_explicit_cache(self) -> None:
        start_script = (REPOSITORY_ROOT / "scripts" / "start_localswim_session.py").read_text(
            encoding="utf-8"
        )
        trigger_script = (REPOSITORY_ROOT / "scripts" / "trigger_localswim_shutdown.py").read_text(
            encoding="utf-8"
        )

        for script in (start_script, trigger_script):
            self.assertIn(f'UV_CACHE = Path(r"{EXPECTED_DETACHED_CACHE}")', script)
            self.assertIn('"UV_CACHE_DIR": str(UV_CACHE)', script)

    def test_durable_contract_records_policy_not_acl_bypass(self) -> None:
        text = DEVELOPMENT_ENVIRONMENT.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        for marker in (
            "`shell_environment_policy.set`",
            EXPECTED_SANDBOX_CACHE,
            "not a Windows ACL defect",
            "Codex filesystem policy still refuses the path",
            "fresh `codex sandbox --permission-profile :workspace` process",
            "no manual `UV_CACHE_DIR` assignment",
            "Do not grant the sandbox write access to `C:\\Temp`",
            "untrusted project context",
        ):
            self.assertIn(marker, normalized)


if __name__ == "__main__":
    unittest.main()
