"""Orchestrator 런타임 설정 로더 단위 테스트."""

import tempfile
import unittest
from pathlib import Path

from orchestrator.runtime_config import (
    RuntimeConfigError,
    get_default_env_file_path,
    load_jules_runtime_config,
)


class TestJulesRuntimeConfig(unittest.TestCase):
    def _write_env(self, content: str) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        env_path = Path(temp_dir.name) / ".env"
        env_path.write_text(content, encoding="utf-8")
        return env_path

    def test_loads_required_values_from_explicit_env_file(self) -> None:
        env_path = self._write_env(
            "JULES_API_KEY=test-api-key\n"
            "JULES_SOURCE_RESOURCE_NAME=sources/test-fixture\n"
        )

        config = load_jules_runtime_config(env_path)

        self.assertEqual(config.api_key, "test-api-key")
        self.assertEqual(config.source_resource_name, "sources/test-fixture")
        self.assertNotIn("test-api-key", repr(config))
        self.assertNotIn("sources/test-fixture", repr(config))

    def test_rejects_missing_required_values_without_echoing_value(self) -> None:
        env_path = self._write_env("JULES_API_KEY=\n")

        with self.assertRaises(RuntimeConfigError) as raised:
            load_jules_runtime_config(env_path)

        self.assertIn("JULES_API_KEY", str(raised.exception))
        self.assertIn("JULES_SOURCE_RESOURCE_NAME", str(raised.exception))

    def test_rejects_malformed_or_duplicate_key(self) -> None:
        malformed_path = self._write_env("INVALID KEY=value\n")
        with self.assertRaises(RuntimeConfigError):
            load_jules_runtime_config(malformed_path)

        duplicate_path = self._write_env("JULES_API_KEY=a\nJULES_API_KEY=b\n")
        with self.assertRaises(RuntimeConfigError) as raised:
            load_jules_runtime_config(duplicate_path)

        self.assertNotIn("=b", str(raised.exception))

    def test_default_env_path_is_orchestrator_local_file(self) -> None:
        default_path = get_default_env_file_path()

        self.assertEqual(default_path.name, ".env")
        self.assertEqual(default_path.parent.name, ".orchestrator")
