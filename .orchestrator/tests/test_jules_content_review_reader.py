import unittest
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from orchestrator.models import TaskContract, ApprovalEvidence, PathItem
from orchestrator.jules_adapter import JulesSessionResponse, RealJulesAdapter
from orchestrator.jules_content_review_reader import (
    execute_content_handoff,
    ContentReviewRequest,
    ContentReviewResult,
)

class FakeTransport:
    def __init__(self, response_data: Dict[str, Any]):
        self.response_data = response_data
        self.last_path = None

    def request(self, method: str, path: str, headers: Dict[str, str], body: Optional[Dict[str, Any]] = None, timeout: float = 30.0):
        self.last_path = path
        return self.response_data

class TestJulesContentReviewReader(unittest.TestCase):
    def setUp(self):
        self.task_id = "TASK-123"
        self.session_id = "sessions/SES-123"
        self.approval_id = "APP-456"
        self.contract_hash = "fake_contract_hash"
        self.scope_hash = "fake_scope_hash"

        self.contract = TaskContract(
            task_id=self.task_id,
            contract_version="v1",
            project_profile_id="proj",
            project_profile_version="1",
            project_profile_reference_path="path",
            goal="Test",
            target_repository="repo",
            base_branch="main",
            base_commit_sha="sha",
            execution_agent="jules",
            reference_documents=[],
            allowed_paths=[PathItem(path="src", kind="directory_recursive")],
            forbidden_paths=[],
            risk_level="LOW",
            completion_conditions=[],
            idempotency_key="key",
            plan_approval_required=True,
            cancellation_conditions=[],
            auto_merge=False
        )

        # 수동으로 해시 세팅 (canonicalization 모킹 대신 직접 계산 결과를 가정하여 우회 또는 단순 모킹)
        # 본 테스트에서는 canonicalize_contract와 canonicalize_scope의 실제 로직에 의존.
        from orchestrator.canonicalization import canonicalize_contract, canonicalize_scope
        _, self.actual_contract_hash = canonicalize_contract(self.contract)
        _, self.actual_scope_hash = canonicalize_scope(self.contract.allowed_paths, self.contract.forbidden_paths)

        self.review_request = ContentReviewRequest(
            session_id=self.session_id,
            task_id=self.task_id,
            approval_id=self.approval_id,
            contract_hash=self.actual_contract_hash,
            approved_scope_hash=self.actual_scope_hash
        )

        self.approval_evidence = ApprovalEvidence(
            approval_id=self.approval_id,
            task_id=self.task_id,
            contract_version="v1",
            contract_hash=self.actual_contract_hash,
            approved_scope_hash=self.actual_scope_hash,
            approver="test_user",
            approval_time_utc="2024-01-01T00:00:00Z",
            status="ACTIVE"
        )

        self.session_response = JulesSessionResponse(
            session_id=self.session_id,
            task_id=self.task_id,
            branch_name="branch",
            pr_number=1,
            status="COMPLETED",
            reason_code=None,
            created_at_utc="2024-01-01T00:00:00Z",
            updated_at_utc="2024-01-01T00:00:00Z"
        )

    def _get_adapter(self, activities_data: list):
        transport = FakeTransport({"activities": activities_data})
        return RealJulesAdapter(api_key="test_key", transport=transport)

    def test_execute_content_handoff_success(self):
        # 모든 허용 유형 정상 추출 테스트
        activities = [
            {"createTime": "2024-01-01T01:00:00Z", "planGenerated": {"plan": {"steps": [{"title": "Step 1", "description": "Desc 1"}]}}},
            {"createTime": "2024-01-01T02:00:00Z", "agentMessaged": {"message": "Agent says hi"}},
            {"createTime": "2024-01-01T03:00:00Z", "progressUpdated": {"message": "Progress 50%"}},
            {"createTime": "2024-01-01T04:00:00Z", "sessionCompleted": {"summary": "All done"}},
            {"createTime": "2024-01-01T05:00:00Z", "sessionFailed": {"failureReason": "Oops"}}
        ]
        adapter = self._get_adapter(activities)

        res = execute_content_handoff(
            self.review_request, self.contract, self.approval_evidence, self.session_response, adapter
        )

        self.assertEqual(res.status, "CONTENT_READY")
        self.assertIn("[PLAN_GENERATED]\nStep 1\nDesc 1", res.content_text)
        self.assertIn("[AGENT_MESSAGED]\nAgent says hi", res.content_text)
        self.assertIn("[PROGRESS_UPDATED]\nProgress 50%", res.content_text)
        self.assertIn("[SESSION_COMPLETED]\nAll done", res.content_text)
        self.assertIn("[SESSION_FAILED]\nOops", res.content_text)

    def test_execute_content_handoff_user_messaged_excluded(self):
        # userMessaged 등 민감 데이터 제외 검증
        activities = [
            {"createTime": "2024-01-01T01:00:00Z", "userMessaged": {"message": "Secret Prompt"}},
            {"createTime": "2024-01-01T02:00:00Z", "agentMessaged": {"message": "Agent reply"}}
        ]
        adapter = self._get_adapter(activities)

        res = execute_content_handoff(
            self.review_request, self.contract, self.approval_evidence, self.session_response, adapter
        )

        self.assertEqual(res.status, "CONTENT_READY")
        self.assertNotIn("Secret Prompt", res.content_text)
        self.assertIn("Agent reply", res.content_text)

    def test_execute_content_handoff_invalid_type_halts(self):
        # 미확인 유형 존재 시 중단 및 NEEDS_HUMAN_REVIEW 반환 검증
        activities = [
            {"createTime": "2024-01-01T01:00:00Z", "agentMessaged": {"message": "Agent reply"}},
            {"createTime": "2024-01-01T02:00:00Z", "unknownType": {"data": "foo"}}
        ]
        adapter = self._get_adapter(activities)

        res = execute_content_handoff(
            self.review_request, self.contract, self.approval_evidence, self.session_response, adapter
        )

        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason_code, "CONTENT_NOT_FOUND")
        self.assertIsNone(res.content_text)

    def test_execute_content_handoff_validation_failure(self):
        # 세션 ID 불일치 등 검증 실패 시 호출 안 함
        bad_req = ContentReviewRequest(
            session_id="sessions/OTHER-123",
            task_id=self.task_id,
            approval_id=self.approval_id,
            contract_hash=self.actual_contract_hash,
            approved_scope_hash=self.actual_scope_hash
        )
        adapter = self._get_adapter([]) # Should not be called

        res = execute_content_handoff(
            bad_req, self.contract, self.approval_evidence, self.session_response, adapter
        )
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason_code, "SESSION_ID_MISMATCH")

    def test_masking_boundary(self):
        # 비영속/비로그 마스킹 경계(repr, to_dict 등) 확인
        req = ContentReviewRequest(
            session_id="s", task_id="t", approval_id="a", contract_hash="c", approved_scope_hash="s"
        )
        self.assertIn("<REDACTED>", repr(req))
        self.assertIn("<REDACTED>", str(req))
        self.assertIn("<REDACTED>", req.to_dict()["review_request"])

        res = ContentReviewResult(status="CONTENT_READY", content_text="Secret Content")
        self.assertIn("<REDACTED>", repr(res))
        self.assertIn("<REDACTED>", str(res))
        self.assertEqual(res.to_dict()["content_text"], "<REDACTED>")
        self.assertNotIn("Secret Content", repr(res))
        self.assertNotIn("Secret Content", str(res))

    def test_time_ordering_failure(self):
         # 시간 순서 중복/오류 시 즉시 중단 검증
         activities = [
            {"createTime": "2024-01-01T01:00:00Z", "agentMessaged": {"message": "Msg 1"}},
            {"createTime": "2024-01-01T01:00:00Z", "agentMessaged": {"message": "Msg 2 (Dup Time)"}}
         ]
         adapter = self._get_adapter(activities)

         res = execute_content_handoff(
            self.review_request, self.contract, self.approval_evidence, self.session_response, adapter
         )
         self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
         self.assertIsNone(res.content_text)

if __name__ == '__main__':
    unittest.main()
