import unittest
from unittest.mock import patch
from orchestrator.manual_entrypoint import execute_manual_session_monitor
from orchestrator.status_bridge import BridgeSignal
from orchestrator.jules_adapter import ActivitySummary, TransportError
from orchestrator.session_monitor import ActivityFetcherAdapter

class FakeAdapter(ActivityFetcherAdapter):
    def __init__(self, activities: ActivitySummary):
        self.activities = activities
        self.fetch_called = False

    def get_activities(self, session_resource_name: str) -> ActivitySummary:
        self.fetch_called = True
        return self.activities

class ExceptionAdapter(ActivityFetcherAdapter):
    def __init__(self, exception_to_raise: Exception):
        self.exception_to_raise = exception_to_raise
        self.fetch_called = False

    def get_activities(self, session_resource_name: str) -> ActivitySummary:
        self.fetch_called = True
        raise self.exception_to_raise

class TestManualEntrypoint(unittest.TestCase):
    def setUp(self):
        self.api_key = "fake_api_key"
        self.session_resource_name = "sessions/SES-123-001"
        self.default_activities = ActivitySummary(
            total_count=1,
            activity_types=["SESSION_COMPLETED"],
            is_completed=True,
            is_failed=False
        )

    def test_invalid_binding_short_circuit(self):
        # 바인딩 무효 시 factory와 fetcher가 모두 호출되지 않아야 함
        factory_called = False
        def fake_factory(key: str) -> ActivityFetcherAdapter:
            nonlocal factory_called
            factory_called = True
            return FakeAdapter(self.default_activities)

        result = execute_manual_session_monitor(
            api_key=self.api_key,
            session_resource_name=self.session_resource_name,
            is_binding_valid=False,
            adapter_factory=fake_factory
        )

        self.assertEqual(result.status_signal, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result.reason_code, "BINDING_INVALID")
        self.assertFalse(factory_called)

    def test_adapter_init_failure_safe_mapping(self):
        # 어댑터 초기화 실패 시 안전하게 ADAPTER_INIT_FAILED 반환
        def raising_factory(key: str) -> ActivityFetcherAdapter:
            raise ValueError("Invalid API Key Format")

        result = execute_manual_session_monitor(
            api_key=self.api_key,
            session_resource_name=self.session_resource_name,
            is_binding_valid=True,
            adapter_factory=raising_factory
        )

        self.assertEqual(result.status_signal, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result.reason_code, "ADAPTER_INIT_FAILED")

    def test_activity_fetch_transport_error_mapping(self):
        # 활동 조회 시 TransportError 발생 시 ACTIVITY_FETCH_FAILED 반환
        adapter = ExceptionAdapter(TransportError("HTTP_CONNECTION_FAILED"))
        def fake_factory(key: str) -> ActivityFetcherAdapter:
            return adapter

        result = execute_manual_session_monitor(
            api_key=self.api_key,
            session_resource_name=self.session_resource_name,
            is_binding_valid=True,
            adapter_factory=fake_factory
        )

        self.assertTrue(adapter.fetch_called)
        self.assertEqual(result.status_signal, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result.reason_code, "ACTIVITY_FETCH_FAILED")

    def test_activity_fetch_general_exception_mapping(self):
        # 활동 조회 시 일반 예외 발생 시 ACTIVITY_FETCH_FAILED 반환
        adapter = ExceptionAdapter(Exception("Unexpected Error"))
        def fake_factory(key: str) -> ActivityFetcherAdapter:
            return adapter

        result = execute_manual_session_monitor(
            api_key=self.api_key,
            session_resource_name=self.session_resource_name,
            is_binding_valid=True,
            adapter_factory=fake_factory
        )

        self.assertTrue(adapter.fetch_called)
        self.assertEqual(result.status_signal, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result.reason_code, "ACTIVITY_FETCH_FAILED")

    def test_normal_activity_fetch_mapping(self):
        # 정상 조회 및 신호 매핑
        adapter = FakeAdapter(self.default_activities)
        def fake_factory(key: str) -> ActivityFetcherAdapter:
            return adapter

        result = execute_manual_session_monitor(
            api_key=self.api_key,
            session_resource_name=self.session_resource_name,
            is_binding_valid=True,
            adapter_factory=fake_factory
        )

        self.assertTrue(adapter.fetch_called)
        self.assertEqual(result.status_signal, "READY_FOR_REVIEW")
        self.assertEqual(result.reason_code, "SESSION_COMPLETED")

    @patch("orchestrator.manual_entrypoint.load_jules_api_key")
    def test_loads_api_key_from_env_when_not_injected(self, mock_load_key):
        mock_load_key.return_value = self.api_key
        received_key = None

        def fake_factory(key: str) -> ActivityFetcherAdapter:
            nonlocal received_key
            received_key = key
            return FakeAdapter(self.default_activities)

        result = execute_manual_session_monitor(
            api_key=None,
            session_resource_name=self.session_resource_name,
            is_binding_valid=True,
            adapter_factory=fake_factory,
        )

        self.assertEqual(result.status_signal, "READY_FOR_REVIEW")
        self.assertEqual(received_key, self.api_key)
        mock_load_key.assert_called_once_with()

    @patch("orchestrator.manual_entrypoint.load_jules_api_key")
    def test_invalid_env_configuration_is_safely_mapped(self, mock_load_key):
        from orchestrator.runtime_config import RuntimeConfigError

        mock_load_key.side_effect = RuntimeConfigError("설정 오류")

        result = execute_manual_session_monitor(
            api_key=None,
            session_resource_name=self.session_resource_name,
            is_binding_valid=True,
            adapter_factory=lambda _: FakeAdapter(self.default_activities),
        )

        self.assertEqual(result.status_signal, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result.reason_code, "RUNTIME_CONFIG_INVALID")

if __name__ == "__main__":
    unittest.main()
