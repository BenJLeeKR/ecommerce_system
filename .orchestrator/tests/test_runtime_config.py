"""Orchestrator 런타임 설정 로더 단위 테스트."""

import tempfile
import unittest
from pathlib import Path

from orchestrator.runtime_config import (
    RuntimeConfigError,
    get_default_env_file_path,
    load_jules_runtime_config,
    load_orchestrator_jules_state_dir,
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

    def test_package_public_api_export(self) -> None:
        import orchestrator
        self.assertTrue(hasattr(orchestrator, "load_orchestrator_jules_state_dir"))
        self.assertIn("load_orchestrator_jules_state_dir", orchestrator.__all__)

    def test_loads_state_dir_successfully_and_does_not_create_directory(self) -> None:
        # 1. 절대 경로 2. Repo 외부(root(/) 테스트용)
        env_path = self._write_env("ORCHESTRATOR_JULES_STATE_DIR=/tmp/test-state-dir\n")

        state_dir = load_orchestrator_jules_state_dir(env_path)

        self.assertEqual(str(state_dir), "/tmp/test-state-dir")
        self.assertFalse(state_dir.exists(), "로더는 실제 디렉터리를 생성해서는 안 됩니다.")

    def test_rejects_missing_state_dir(self) -> None:
        env_path = self._write_env("JULES_API_KEY=key\n")

        with self.assertRaises(RuntimeConfigError) as raised:
            load_orchestrator_jules_state_dir(env_path)

        self.assertIn("ORCHESTRATOR_JULES_STATE_DIR", str(raised.exception))

    def test_rejects_relative_state_dir(self) -> None:
        env_path = self._write_env("ORCHESTRATOR_JULES_STATE_DIR=relative/path\n")

        with self.assertRaises(RuntimeConfigError) as raised:
            load_orchestrator_jules_state_dir(env_path)

        self.assertIn("절대 경로", str(raised.exception))

    def test_rejects_state_dir_inside_repo(self) -> None:
        repo_root = get_default_env_file_path().parent.parent.resolve()
        test_path = repo_root / ".orchestrator" / "test-dir"

        env_path = self._write_env(f"ORCHESTRATOR_JULES_STATE_DIR={test_path}\n")

        with self.assertRaises(RuntimeConfigError) as raised:
            load_orchestrator_jules_state_dir(env_path)

        self.assertIn("Git 리포지토리 외부 경로여야 합니다", str(raised.exception))
