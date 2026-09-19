import unittest
from orchestrator.jules_adapter import ActivitySummary
from orchestrator.status_bridge import map_session_status

class TestStatusBridgeTemporal(unittest.TestCase):

    def test_map_session_status_temporal_unreliable(self):
        """시간 정보 누락/동일/오류 시 NEEDS_HUMAN_REVIEW로 안전 매핑되는지 확인"""
        activities = ActivitySummary(
            total_count=2,
            activity_types=["PLAN_GENERATED", "PLAN_APPROVED"],
            is_completed=False,
            is_failed=False
        )
        activities.is_temporal_order_reliable = False

        signal = map_session_status(True, activities)
        self.assertEqual(signal.status_signal, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(signal.reason_code, "TEMPORAL_ORDER_UNRELIABLE")

    def test_map_session_status_in_progress(self):
        """PLAN_GENERATED 이후 PLAN_APPROVED 존재 시 IN_PROGRESS 매핑 확인"""
        activities = ActivitySummary(
            total_count=2,
            activity_types=["PLAN_GENERATED", "PLAN_APPROVED"],
            is_completed=False,
            is_failed=False
        )
        # default is True

        signal = map_session_status(True, activities)
        self.assertEqual(signal.status_signal, "IN_PROGRESS")
        self.assertEqual(signal.reason_code, "ACTIVITY_IN_PROGRESS")

    def test_map_session_status_in_progress_progress_updated(self):
        """PLAN_GENERATED 이후 PROGRESS_UPDATED 존재 시 IN_PROGRESS 매핑 확인"""
        activities = ActivitySummary(
            total_count=2,
            activity_types=["PLAN_GENERATED", "PROGRESS_UPDATED"],
            is_completed=False,
            is_failed=False
        )

        signal = map_session_status(True, activities)
        self.assertEqual(signal.status_signal, "IN_PROGRESS")
        self.assertEqual(signal.reason_code, "ACTIVITY_IN_PROGRESS")

    def test_map_session_status_ignore_messages(self):
        """PLAN_GENERATED 이후 AGENT_MESSAGED/USER_MESSAGED만 있으면 PLAN_REVIEW_REQUIRED 유지"""
        activities = ActivitySummary(
            total_count=3,
            activity_types=["PLAN_GENERATED", "AGENT_MESSAGED", "USER_MESSAGED"],
            is_completed=False,
            is_failed=False
        )

        signal = map_session_status(True, activities)
        self.assertEqual(signal.status_signal, "PLAN_REVIEW_REQUIRED")
        self.assertEqual(signal.reason_code, "PLAN_GENERATED")

    def test_map_session_status_in_progress_multiple_generates(self):
        """PLAN_GENERATED가 여러번 있고 마지막 이후에 APPROVED 존재 시 IN_PROGRESS 매핑 확인"""
        activities = ActivitySummary(
            total_count=3,
            activity_types=["PLAN_GENERATED", "PLAN_APPROVED", "PLAN_GENERATED"],
            is_completed=False,
            is_failed=False
        )

        # 마지막 PLAN_GENERATED 뒤에 아무 진행 상태가 없음 -> PLAN_REVIEW_REQUIRED 이어야 함.
        signal = map_session_status(True, activities)
        self.assertEqual(signal.status_signal, "PLAN_REVIEW_REQUIRED")
        self.assertEqual(signal.reason_code, "PLAN_GENERATED")

        # 만약 그 뒤에 APPROVED가 있다면
        activities2 = ActivitySummary(
            total_count=4,
            activity_types=["PLAN_GENERATED", "PLAN_APPROVED", "PLAN_GENERATED", "PLAN_APPROVED"],
            is_completed=False,
            is_failed=False
        )
        signal2 = map_session_status(True, activities2)
        self.assertEqual(signal2.status_signal, "IN_PROGRESS")
        self.assertEqual(signal2.reason_code, "ACTIVITY_IN_PROGRESS")

    def test_map_session_status_priority(self):
        """SESSION_COMPLETED 혹은 FAILED가 IN_PROGRESS보다 우선 적용되는지 확인"""
        activities = ActivitySummary(
            total_count=3,
            activity_types=["PLAN_GENERATED", "PLAN_APPROVED", "SESSION_COMPLETED"],
            is_completed=True,
            is_failed=False
        )

        signal = map_session_status(True, activities)
        self.assertEqual(signal.status_signal, "READY_FOR_REVIEW")
        self.assertEqual(signal.reason_code, "SESSION_COMPLETED")

if __name__ == '__main__':
    unittest.main()
