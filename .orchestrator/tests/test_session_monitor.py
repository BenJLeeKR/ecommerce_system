import unittest
from unittest.mock import Mock

from orchestrator.jules_adapter import ActivitySummary, TransportError
from orchestrator.status_bridge import BridgeSignal
from orchestrator.session_monitor import check_session_status_once, invoke_session_monitor_once


class TestSessionMonitor(unittest.TestCase):

    def setUp(self):
        self.session_id = "sessions/SES-TEST-001"
        self.mock_fetcher = Mock()

    def test_invalid_binding_does_not_fetch(self):
        """바인딩 무효 시 조회자를 전혀 호출하지 않고 BINDING_INVALID 신호 반환 검증."""
        signal = check_session_status_once(
            is_binding_valid=False,
            session_resource_name=self.session_id,
            activity_fetcher=self.mock_fetcher
        )

        # 콜백 미호출 검증
        self.mock_fetcher.assert_not_called()

        # 신호 검증
        self.assertEqual(signal.status_signal, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(signal.reason_code, "BINDING_INVALID")

    def test_valid_binding_fetches_once_and_maps_completed(self):
        """바인딩 유효 시 정확히 1회 호출하고 SESSION_COMPLETED 정상 매핑 검증."""
        # Mock 반환값 설정
        self.mock_fetcher.return_value = ActivitySummary(
            total_count=3,
            activity_types=["PLAN_GENERATED", "SESSION_COMPLETED"],
            is_completed=True,
            is_failed=False
        )

        signal = check_session_status_once(
            is_binding_valid=True,
            session_resource_name=self.session_id,
            activity_fetcher=self.mock_fetcher
        )

        # 1회 호출 검증
        self.mock_fetcher.assert_called_once_with(self.session_id)

        # 신호 검증 (완료 우선)
        self.assertEqual(signal.status_signal, "READY_FOR_REVIEW")
        self.assertEqual(signal.reason_code, "SESSION_COMPLETED")

    def test_valid_binding_fetches_once_and_maps_plan_generated(self):
        """바인딩 유효 시 PLAN_GENERATED 매핑 검증."""
        self.mock_fetcher.return_value = ActivitySummary(
            total_count=1,
            activity_types=["PLAN_GENERATED"],
            is_completed=False,
            is_failed=False
        )

        signal = check_session_status_once(
            is_binding_valid=True,
            session_resource_name=self.session_id,
            activity_fetcher=self.mock_fetcher
        )

        self.mock_fetcher.assert_called_once_with(self.session_id)

        self.assertEqual(signal.status_signal, "PLAN_REVIEW_REQUIRED")
        self.assertEqual(signal.reason_code, "PLAN_GENERATED")

    def test_valid_binding_fetches_once_and_maps_failed(self):
        """바인딩 유효 시 SESSION_FAILED 매핑 검증."""
        self.mock_fetcher.return_value = ActivitySummary(
            total_count=2,
            activity_types=["PLAN_GENERATED", "SESSION_FAILED"],
            is_completed=False,
            is_failed=True
        )

        signal = check_session_status_once(
            is_binding_valid=True,
            session_resource_name=self.session_id,
            activity_fetcher=self.mock_fetcher
        )

        self.mock_fetcher.assert_called_once_with(self.session_id)

        self.assertEqual(signal.status_signal, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(signal.reason_code, "SESSION_FAILED")

    def test_transport_error_safe_handling(self):
        """TransportError 발생 시 안전하게 ACTIVITY_FETCH_FAILED 신호 반환 검증."""
        self.mock_fetcher.side_effect = TransportError("CONNECTION_TIMEOUT")

        signal = check_session_status_once(
            is_binding_valid=True,
            session_resource_name=self.session_id,
            activity_fetcher=self.mock_fetcher
        )

        self.mock_fetcher.assert_called_once_with(self.session_id)

        self.assertEqual(signal.status_signal, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(signal.reason_code, "ACTIVITY_FETCH_FAILED")

    def test_general_exception_safe_handling(self):
        """일반 Exception 발생 시 안전하게 ACTIVITY_FETCH_FAILED 신호 반환 검증."""
        self.mock_fetcher.side_effect = Exception("Unexpected network drop")

        signal = check_session_status_once(
            is_binding_valid=True,
            session_resource_name=self.session_id,
            activity_fetcher=self.mock_fetcher
        )

        self.mock_fetcher.assert_called_once_with(self.session_id)

        self.assertEqual(signal.status_signal, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(signal.reason_code, "ACTIVITY_FETCH_FAILED")


class TestSessionMonitorFacade(unittest.TestCase):

    def setUp(self):
        self.session_id = "sessions/SES-FACADE-001"
        # ActivityFetcherAdapter Protocol을 만족하는 Mock 어댑터
        self.mock_adapter = Mock()

    def test_invoke_valid_binding_fetches_once(self):
        """Facade: 유효한 바인딩일 때 adapter.get_activities가 1회 호출되는지 검증."""
        self.mock_adapter.get_activities.return_value = ActivitySummary(
            total_count=1,
            activity_types=["PLAN_GENERATED"],
            is_completed=False,
            is_failed=False
        )

        signal = invoke_session_monitor_once(
            adapter=self.mock_adapter,
            session_resource_name=self.session_id,
            is_binding_valid=True
        )

        self.mock_adapter.get_activities.assert_called_once_with(self.session_id)
        self.assertEqual(signal.status_signal, "PLAN_REVIEW_REQUIRED")
        self.assertEqual(signal.reason_code, "PLAN_GENERATED")

    def test_invoke_invalid_binding_no_fetch(self):
        """Facade: 무효 바인딩일 때 adapter.get_activities가 호출되지 않는지 검증."""
        signal = invoke_session_monitor_once(
            adapter=self.mock_adapter,
            session_resource_name=self.session_id,
            is_binding_valid=False
        )

        self.mock_adapter.get_activities.assert_not_called()
        self.assertEqual(signal.status_signal, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(signal.reason_code, "BINDING_INVALID")

    def test_invoke_transport_error_safe_handling(self):
        """Facade: TransportError 예외 발생 시 안전 처리 검증."""
        self.mock_adapter.get_activities.side_effect = TransportError("CONNECTION_TIMEOUT")

        signal = invoke_session_monitor_once(
            adapter=self.mock_adapter,
            session_resource_name=self.session_id,
            is_binding_valid=True
        )

        self.mock_adapter.get_activities.assert_called_once_with(self.session_id)
        self.assertEqual(signal.status_signal, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(signal.reason_code, "ACTIVITY_FETCH_FAILED")


if __name__ == '__main__':
    unittest.main()
