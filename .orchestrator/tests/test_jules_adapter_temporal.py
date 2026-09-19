import unittest
import json
from unittest.mock import MagicMock
from orchestrator.jules_adapter import RealJulesAdapter, UrllibJulesHttpTransport, ActivitySummary

class TestJulesAdapterTemporal(unittest.TestCase):
    def setUp(self):
        self.mock_transport = MagicMock(spec=UrllibJulesHttpTransport)
        self.adapter = RealJulesAdapter(api_key="dummy_key", transport=self.mock_transport)

    def test_get_activities_temporal_order(self):
        """시간 순서가 명확할 때 activity_types가 올바르게 정렬되는지 확인"""
        self.mock_transport.request.return_value = {
            "activities": [
                {"createTime": "2023-01-01T10:00:00Z", "planApproved": {}},
                {"createTime": "2023-01-01T09:00:00Z", "planGenerated": {}},
                {"createTime": "2023-01-01T08:00:00Z", "agentMessaged": {}}
            ]
        }

        summary = self.adapter.get_activities("sessions/ses-123")
        self.assertTrue(summary.is_temporal_order_reliable)
        # 08:00 -> 09:00 -> 10:00 순서여야 함
        self.assertEqual(summary.activity_types, ["AGENT_MESSAGED", "PLAN_GENERATED", "PLAN_APPROVED"])

    def test_get_activities_temporal_order_unreliable_missing(self):
        """시간 정보 누락 시 is_temporal_order_reliable = False로 설정되는지 확인"""
        self.mock_transport.request.return_value = {
            "activities": [
                {"createTime": "2023-01-01T10:00:00Z", "planApproved": {}},
                {"planGenerated": {}} # 시간 정보 없음
            ]
        }

        summary = self.adapter.get_activities("sessions/ses-123")
        self.assertFalse(summary.is_temporal_order_reliable)

    def test_get_activities_temporal_order_unreliable_duplicate(self):
        """시간 정보 중복 시 is_temporal_order_reliable = False로 설정되는지 확인"""
        self.mock_transport.request.return_value = {
            "activities": [
                {"createTime": "2023-01-01T10:00:00Z", "planApproved": {}},
                {"createTime": "2023-01-01T10:00:00Z", "planGenerated": {}} # 중복 시각
            ]
        }

        summary = self.adapter.get_activities("sessions/ses-123")
        self.assertFalse(summary.is_temporal_order_reliable)

    def test_get_activities_temporal_order_unreliable_format(self):
        """시간 정보 형식 오류 시 is_temporal_order_reliable = False로 설정되는지 확인"""
        self.mock_transport.request.return_value = {
            "activities": [
                {"createTime": "invalid-time", "planGenerated": {}}
            ]
        }

        summary = self.adapter.get_activities("sessions/ses-123")
        self.assertFalse(summary.is_temporal_order_reliable)

if __name__ == '__main__':
    unittest.main()
