import unittest
from orchestrator.status_bridge import map_session_status, map_direction_confirmation_signal, BridgeSignal
from orchestrator.jules_adapter import ActivitySummary

class TestStatusBridge(unittest.TestCase):

    def test_binding_invalid(self):
        """바인딩 불일치 시 활동 내역과 무관하게 항상 NEEDS_HUMAN_REVIEW 반환 검증."""
        # 세션 완료, 실패 등 여러 플래그가 있어도 무조건 바인딩 불일치 우선
        activities = ActivitySummary(
            total_count=3,
            activity_types=["SESSION_COMPLETED", "PLAN_GENERATED"],
            is_completed=True,
            is_failed=False
        )
        signal = map_session_status(is_binding_valid=False, activities=activities)
        self.assertEqual(signal.status_signal, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(signal.reason_code, "BINDING_INVALID")

    def test_session_failed_priority(self):
        """바인딩이 유효할 때 SESSION_FAILED가 최우선으로 검출되는지 검증."""
        # 완료나 계획 생성 등 다른 상태가 함께 포함되어도 실패 상태를 먼저 잡아야 함
        activities = ActivitySummary(
            total_count=2,
            activity_types=["SESSION_COMPLETED", "SESSION_FAILED"],
            is_completed=True,
            is_failed=True
        )
        signal = map_session_status(is_binding_valid=True, activities=activities)
        self.assertEqual(signal.status_signal, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(signal.reason_code, "SESSION_FAILED")

    def test_session_completed_priority(self):
        """실패가 없고 완료가 있을 때, 계획 생성보다 완료 상태가 우선 검출되는지 검증."""
        activities = ActivitySummary(
            total_count=2,
            activity_types=["PLAN_GENERATED", "SESSION_COMPLETED"],
            is_completed=True,
            is_failed=False
        )
        signal = map_session_status(is_binding_valid=True, activities=activities)
        self.assertEqual(signal.status_signal, "READY_FOR_REVIEW")
        self.assertEqual(signal.reason_code, "SESSION_COMPLETED")

    def test_plan_generated_priority(self):
        """완료, 실패가 없고 계획 생성만 있을 때 PLAN_REVIEW_REQUIRED 반환 검증."""
        activities = ActivitySummary(
            total_count=1,
            activity_types=["PLAN_GENERATED"],
            is_completed=False,
            is_failed=False
        )
        signal = map_session_status(is_binding_valid=True, activities=activities)
        self.assertEqual(signal.status_signal, "PLAN_REVIEW_REQUIRED")
        self.assertEqual(signal.reason_code, "PLAN_GENERATED")

    def test_no_recognizable_activity(self):
        """인식 가능한 활동이 없거나 알 수 없는 활동만 있을 때 안전한 기본값 반환 검증."""
        activities = ActivitySummary(
            total_count=0,
            activity_types=[],
            is_completed=False,
            is_failed=False
        )
        signal = map_session_status(is_binding_valid=True, activities=activities)
        self.assertEqual(signal.status_signal, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(signal.reason_code, "NO_RECOGNIZABLE_ACTIVITY")

        # 알 수 없는 활동만 있는 경우
        activities_unknown = ActivitySummary(
            total_count=1,
            activity_types=["UNKNOWN_ACTIVITY"],
            is_completed=False,
            is_failed=False
        )
        signal_unknown = map_session_status(is_binding_valid=True, activities=activities_unknown)
        self.assertEqual(signal_unknown.status_signal, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(signal_unknown.reason_code, "NO_RECOGNIZABLE_ACTIVITY")

    def test_direction_confirmation_binding_invalid(self):
        """방향 확인 신호 매핑: 바인딩 불일치 시 대기 상태와 무관하게 NEEDS_HUMAN_REVIEW 반환 검증."""
        # 대기 상태임
        signal1 = map_direction_confirmation_signal(is_binding_valid=False, is_direction_confirmation_pending=True)
        self.assertIsNotNone(signal1)
        self.assertEqual(signal1.status_signal, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(signal1.reason_code, "BINDING_INVALID")

        # 대기 상태 아님
        signal2 = map_direction_confirmation_signal(is_binding_valid=False, is_direction_confirmation_pending=False)
        self.assertIsNotNone(signal2)
        self.assertEqual(signal2.status_signal, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(signal2.reason_code, "BINDING_INVALID")

    def test_direction_confirmation_pending(self):
        """방향 확인 신호 매핑: 바인딩이 유효하고 대기 중일 때 DIRECTION_CONFIRMATION_REQUIRED 반환 검증."""
        signal = map_direction_confirmation_signal(is_binding_valid=True, is_direction_confirmation_pending=True)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.status_signal, "DIRECTION_CONFIRMATION_REQUIRED")
        self.assertEqual(signal.reason_code, "DIRECTION_CONFIRMATION_PENDING")

    def test_direction_confirmation_not_pending(self):
        """방향 확인 신호 매핑: 바인딩이 유효하고 대기 중이 아닐 때 None 반환 검증."""
        signal = map_direction_confirmation_signal(is_binding_valid=True, is_direction_confirmation_pending=False)
        self.assertIsNone(signal)

if __name__ == '__main__':
    unittest.main()
