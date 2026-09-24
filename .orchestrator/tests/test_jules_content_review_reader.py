import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from orchestrator.jules_adapter import JulesSessionResponse, TransportError, RealJulesAdapter
from orchestrator.validator import ApprovalEvidence, TaskContract
from orchestrator.jules_content_review_reader import ReviewActivity, fetch_content_review_activities

class FakeHttpTransport:
    def __init__(self, response_data=None, error=None):
        self.response_data = response_data
        self.error = error
        self.call_count = 0

    def request(self, method, path, headers, body=None, timeout=30.0):
        self.call_count += 1
        if self.error:
            raise self.error
        return self.response_data


def default_contract():
    return TaskContract(
        contract_version="1.0",
        task_id="TASK-123",
        project_profile_id="PROFILE-1",
        project_profile_version="1.0",
        project_profile_reference_path="path/to/profile",
        goal="Test goal",
        target_repository="owner/repo",
        base_branch="main",
        base_commit_sha="abcd123",
        execution_agent="JULES",
        reference_documents=[],
        allowed_paths=[],
        forbidden_paths=[],
        risk_level="HIGH",
        completion_conditions=[],
        plan_approval_required=True,
        auto_merge=False,
        idempotency_key="idemp-key-1",
        cancellation_conditions=[]
    )


def default_evidence():
    return ApprovalEvidence(
        approval_id="APP-1",
        task_id="TASK-123",
        contract_version="1.0",
        contract_hash="e80c6b3a2b6e85891e7bda52ca61ed04935f5f706b24a6e5ccd3de1910eb40ac",
        approved_scope_hash="a111896298b55d0a9e9e02bfe8598fe1e47cf1f72b42860953deae762baa1c21",
        approver="user1",
        approval_time_utc="2026-09-24T00:00:00Z",
        status="ACTIVE",
    )


def default_session_resp():
    return JulesSessionResponse(
        session_id="sessions/test-1",
        task_id="TASK-123",
        branch_name=None,
        pr_number=None,
        status="CREATED",
        reason_code=None,
        created_at_utc="2026-09-24T00:00:00Z",
        updated_at_utc="2026-09-24T00:00:00Z"
    )

class TestJulesContentReviewReader(unittest.TestCase):

    def test_pre_gate_validation_failures_yield_zero_api_calls(self):
        """사전 검증 실패 시 API 호출은 0회이고 NEEDS_HUMAN_REVIEW를 반환해야 함"""
        cases = [
            ("evidence.status != ACTIVE", default_evidence, lambda e: setattr(e, "status", "EXPIRED")),
            ("plan_approval_required = False", default_contract, lambda c: setattr(c, "plan_approval_required", False)),
            ("auto_merge = True", default_contract, lambda c: setattr(c, "auto_merge", True)),
            ("task_id mismatch", default_contract, lambda c: setattr(c, "task_id", "TASK-999")),
            ("contract hash mismatch", default_evidence, lambda e: setattr(e, "contract_hash", "wrong")),
            ("scope hash mismatch", default_evidence, lambda e: setattr(e, "approved_scope_hash", "wrong")),
        ]

        for desc, factory, mutator in cases:
            with self.subTest(desc=desc):
                c = default_contract()
                e = default_evidence()
                sr = default_session_resp()

                if factory == default_contract:
                    mutator(c)
                else:
                    mutator(e)

                transport = FakeHttpTransport(response_data={"activities": []})
                adapter = RealJulesAdapter(api_key="fake-key", transport=transport)

                res = fetch_content_review_activities(adapter, "sessions/test-1", c, e, sr)

                self.assertIsNotNone(res)
                self.assertEqual(res.get("status"), "NEEDS_HUMAN_REVIEW")
                self.assertIn("reason_code", res)
                self.assertEqual(transport.call_count, 0)

        # session_id 불일치 케이스
        with self.subTest(desc="session_id mismatch"):
            c = default_contract()
            e = default_evidence()
            sr = default_session_resp()
            transport = FakeHttpTransport(response_data={"activities": []})
            adapter = RealJulesAdapter(api_key="fake-key", transport=transport)

            res = fetch_content_review_activities(adapter, "sessions/other-1", c, e, sr)

            self.assertIsNotNone(res)
            self.assertEqual(res.get("status"), "NEEDS_HUMAN_REVIEW")
            self.assertIn("reason_code", res)
            self.assertEqual(transport.call_count, 0)

    def test_extracts_all_activity_types_correctly(self):
        """정상 유형별 데이터 추출 테스트 (description 생략 허용 및 대응 관계 유지 등)"""
        c = default_contract()
        e = default_evidence()
        sr = default_session_resp()

        response_data = {
            "activities": [
                {
                    "createTime": "2026-09-24T00:01:00Z",
                    "planGenerated": {
                        "plan": {
                            "steps": [
                                {"title": "Step 1", "description": "Desc 1"},
                                {"title": "Step 2"}  # description 없음
                            ]
                        }
                    }
                },
                {
                    "createTime": "2026-09-24T00:02:00Z",
                    "progressUpdated": {
                        "title": "Progress 1",
                        "description": "Desc 1"
                    }
                },
                {
                    "createTime": "2026-09-24T00:03:00Z",
                    "progressUpdated": {
                        "title": "Progress 2" # description 없음
                    }
                },
                {
                    "createTime": "2026-09-24T00:04:00Z",
                    "planApproved": {} # 빈 dict
                },
                {
                    "createTime": "2026-09-24T00:05:00Z",
                    "sessionCompleted": {}
                },
                {
                    "createTime": "2026-09-24T00:06:00Z",
                    "agentMessaged": {
                        "agentMessage": "Hello from agent"
                    }
                }
            ]
        }
        transport = FakeHttpTransport(response_data=response_data)
        adapter = RealJulesAdapter(api_key="fake-key", transport=transport)

        res = fetch_content_review_activities(adapter, "sessions/test-1", c, e, sr)

        self.assertIsNotNone(res)
        self.assertEqual(res.get("status"), "SUCCESS")
        activities = res.get("activities", [])
        self.assertEqual(len(activities), 6)

        # 1. planGenerated 검증 (대응 관계 유지)
        self.assertEqual(activities[0].activity_type, "PLAN_GENERATED")
        self.assertEqual(activities[0].title, "Step 1\nDesc 1\n\nStep 2")
        self.assertIsNone(activities[0].description)

        # 2. progressUpdated 검증
        self.assertEqual(activities[1].activity_type, "PROGRESS_UPDATED")
        self.assertEqual(activities[1].title, "Progress 1")
        self.assertEqual(activities[1].description, "Desc 1")

        # 3. progressUpdated (no desc) 검증
        self.assertEqual(activities[2].activity_type, "PROGRESS_UPDATED")
        self.assertEqual(activities[2].title, "Progress 2")
        self.assertIsNone(activities[2].description)

        # 4. planApproved 검증 (메타데이터 노출 안함)
        self.assertEqual(activities[3].activity_type, "PLAN_APPROVED")
        self.assertIsNone(activities[3].title)
        self.assertIsNone(activities[3].description)

        # 5. sessionCompleted 검증 (메타데이터 노출 안함)
        self.assertEqual(activities[4].activity_type, "SESSION_COMPLETED")
        self.assertIsNone(activities[4].title)

        # 6. agentMessaged 검증
        self.assertEqual(activities[5].activity_type, "AGENT_MESSAGED")
        self.assertEqual(activities[5].agent_message, "Hello from agent")

    def test_aborts_on_user_message(self):
        """사용자 메시지가 포함되어 있으면 대체 탐색 없이 즉시 NEEDS_HUMAN_REVIEW 반환"""
        c = default_contract()
        e = default_evidence()
        sr = default_session_resp()

        response_data = {
            "activities": [
                {
                    "createTime": "2026-09-24T00:01:00Z",
                    "planGenerated": { "plan": { "steps": [{"title": "Step 1"}] } }
                },
                {
                    "createTime": "2026-09-24T00:02:00Z",
                    "userMessaged": { "userMessage": "secret user data" }
                }
            ]
        }
        transport = FakeHttpTransport(response_data=response_data)
        adapter = RealJulesAdapter(api_key="fake-key", transport=transport)

        res = fetch_content_review_activities(adapter, "sessions/test-1", c, e, sr)
        self.assertIsNotNone(res)
        self.assertEqual(res.get("status"), "NEEDS_HUMAN_REVIEW")
        self.assertIn("reason_code", res)

    def test_aborts_on_unverified_or_format_errors(self):
        """형식 오류, 시간 순서 오류, 미확인 이벤트 시 NEEDS_HUMAN_REVIEW 반환"""
        c = default_contract()
        e = default_evidence()
        sr = default_session_resp()

        cases = [
            ("duplicate times", [
                {"createTime": "2026-09-24T00:01:00Z", "planGenerated": {"plan": {"steps": [{"title": "1"}]}}},
                {"createTime": "2026-09-24T00:01:00Z", "planGenerated": {"plan": {"steps": [{"title": "2"}]}}}
            ]),
            ("invalid format time", [
                {"createTime": "invalid-time", "planGenerated": {"plan": {"steps": [{"title": "1"}]}}}
            ]),
            ("unknown event type", [
                {"createTime": "2026-09-24T00:01:00Z", "unknownEvent": {}}
            ]),
            ("multiple union events", [
                {"createTime": "2026-09-24T00:01:00Z", "planGenerated": {"plan": {"steps": [{"title": "1"}]}}, "progressUpdated": {"title": "2"}}
            ]),
            ("sessionFailed with unknown body", [
                {"createTime": "2026-09-24T00:01:00Z", "sessionFailed": {"reason": "unknown"}}
            ]),
            ("missing title in planGenerated step", [
                {"createTime": "2026-09-24T00:01:00Z", "planGenerated": {"plan": {"steps": [{"description": "only desc"}]}}}
            ]),
            ("progressUpdated missing title", [
                {"createTime": "2026-09-24T00:01:00Z", "progressUpdated": {"description": "only desc"}}
            ]),
        ]

        for desc, acts in cases:
            with self.subTest(desc=desc):
                transport = FakeHttpTransport(response_data={"activities": acts})
                adapter = RealJulesAdapter(api_key="fake-key", transport=transport)
                res = fetch_content_review_activities(adapter, "sessions/test-1", c, e, sr)
                self.assertIsNotNone(res)
                self.assertEqual(res.get("status"), "NEEDS_HUMAN_REVIEW")
                self.assertIn("reason_code", res)

    @patch("logging.Logger.info")
    @patch("logging.Logger.error")
    @patch("sqlite3.connect")
    @patch("builtins.open")
    def test_non_persistence_and_no_leakage(self, mock_open, mock_sqlite, mock_log_err, mock_log_info):
        """비영속, 비로그, 비직렬화(민감정보 마스킹) 검증"""
        act = ReviewActivity(
            activity_type="PLAN_GENERATED",
            create_time_utc="2026-09-24T00:01:00Z",
            title="Secret Title",
            description="Secret Desc",
            agent_message="Secret Agent"
        )

        # 1. str, repr 변환 시 REDACTED 여부
        act_str = str(act)
        act_repr = repr(act)

        self.assertNotIn("Secret Title", act_str)
        self.assertNotIn("Secret Desc", act_str)
        self.assertNotIn("Secret Agent", act_str)
        self.assertIn("<REDACTED>", act_str)

        self.assertNotIn("Secret Title", act_repr)
        self.assertNotIn("Secret Desc", act_repr)
        self.assertNotIn("Secret Agent", act_repr)
        self.assertIn("<REDACTED>", act_repr)

        # 2. to_dict 변환 시 REDACTED 여부
        act_dict = act.to_dict()
        self.assertEqual(act_dict["title"], "<REDACTED>")
        self.assertEqual(act_dict["description"], "<REDACTED>")
        self.assertEqual(act_dict["agent_message"], "<REDACTED>")
        self.assertEqual(act_dict["activity_type"], "PLAN_GENERATED")

        # 3. 로깅 및 파일/DB 접근 모의객체가 호출되지 않았는지 검증
        mock_log_info.assert_not_called()
        mock_log_err.assert_not_called()
        mock_sqlite.assert_not_called()
        mock_open.assert_not_called()


if __name__ == '__main__':
    unittest.main()
