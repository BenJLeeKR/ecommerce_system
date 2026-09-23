import unittest
from unittest.mock import Mock, call

from orchestrator.models import TaskContract, ApprovalEvidence, PathItem
from orchestrator.jules_adapter import JulesSessionResponse, JulesSessionRequest, RealJulesAdapter, JulesHttpTransport, PreGateResult
from orchestrator.dispatch_entrypoint import execute_dispatch_session
from orchestrator.canonicalization import canonicalize_contract, canonicalize_scope

class TestDispatchEntrypoint(unittest.TestCase):
    def setUp(self):
        # Fake HTTP Transport and Real Adapter
        self.mock_transport = Mock(spec=JulesHttpTransport)
        self.fake_api_key = "fake_key_123"

        # 고정 remote main SHA 반환 함수
        def fake_remote_main_sha():
            return "abcd123"

        # RealJulesAdapter를 사용하여 POST Body의 startingBranch, requirePlanApproval를 검증
        self.jules_adapter = RealJulesAdapter(
            api_key=self.fake_api_key,
            transport=self.mock_transport,
            remote_main_sha_fn=fake_remote_main_sha
        )

        # 성공 응답 모의 설정
        self.mock_transport.request.return_value = {
            "name": "sessions/sess-1",
            "workingBranchName": "main"
        }

        self.valid_paths = [PathItem(path="docs", kind="directory_recursive")]
        self.contract = TaskContract(
            task_id="TEST-001",
            contract_version="v1",
            project_profile_id="p1",
            project_profile_version="v1",
            project_profile_reference_path="path",
            goal="Test Goal",
            target_repository="repo",
            base_branch="main",
            base_commit_sha="abcd123",
            execution_agent="jules",
            reference_documents=[],
            allowed_paths=self.valid_paths,
            forbidden_paths=[],
            risk_level="LOW",
            completion_conditions=[],
            idempotency_key="idemp_key",
            plan_approval_required=True,
            cancellation_conditions=[],
            auto_merge=False
        )

        _, self.contract_hash = canonicalize_contract(self.contract)
        _, self.scope_hash = canonicalize_scope(self.contract.allowed_paths, self.contract.forbidden_paths)

        self.evidence = ApprovalEvidence(
            approval_id="appr-1",
            task_id="TEST-001",
            contract_version="v1",
            contract_hash=self.contract_hash,
            approved_scope_hash=self.scope_hash,
            approver="user",
            approval_time_utc="2026-09-23T12:00:00Z",
            status="ACTIVE"
        )

        self.source_name = "sources/github/owner/repo"
        self.actual_base_sha = "abcd123"

    def test_success_path_with_real_adapter(self):
        """정상 경로에서 RealJulesAdapter를 통해 POST 요청의 startingBranch, requirePlanApproval 필드를 검증."""
        response = execute_dispatch_session(
            contract=self.contract,
            approval_evidence=self.evidence,
            source_name=self.source_name,
            jules_adapter=self.jules_adapter,
            actual_base_sha=self.actual_base_sha
        )

        self.assertEqual(response.status, "CREATED")

        # 실제 네트워크 호출은 mock_transport에서 차단되었으므로 인자 검증
        self.mock_transport.request.assert_called_once()
        call_args = self.mock_transport.request.call_args[1]

        self.assertEqual(call_args["method"], "POST")
        self.assertEqual(call_args["path"], "sessions")

        body = call_args["body"]
        # 정책 강제 검증 (sourceContext 구조와 최상위 필드)
        source_context = body.get("sourceContext", {})
        github_context = source_context.get("githubRepoContext", {})
        self.assertEqual(github_context.get("startingBranch"), "main")
        self.assertEqual(source_context.get("source"), self.source_name)
        self.assertTrue(body.get("requirePlanApproval"))

    def test_approval_not_active(self):
        """승인 상태가 ACTIVE가 아니면 중단."""
        self.evidence.status = "WITHDRAWN"
        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, self.jules_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "APPROVAL_NOT_ACTIVE")
        self.assertTrue(response.created_at_utc) # UTC 시간 확인
        self.mock_transport.request.assert_not_called()

    def test_auto_merge_not_allowed(self):
        """auto_merge가 True이면 중단."""
        self.contract.auto_merge = True

        _, self.evidence.contract_hash = canonicalize_contract(self.contract) # 해시 불일치를 막기 위해 갱신

        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, self.jules_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "AUTO_MERGE_NOT_ALLOWED")
        self.mock_transport.request.assert_not_called()

    def test_plan_approval_not_required(self):
        """plan_approval_required가 False이면 중단."""
        self.contract.plan_approval_required = False

        _, self.evidence.contract_hash = canonicalize_contract(self.contract) # 해시 불일치를 막기 위해 갱신

        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, self.jules_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "PLAN_APPROVAL_REQUIRED")
        self.mock_transport.request.assert_not_called()

    def test_contract_hash_mismatch(self):
        """contract hash 불일치 시 중단."""
        self.evidence.contract_hash = "fake-hash"
        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, self.jules_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "CONTRACT_HASH_MISMATCH")
        self.mock_transport.request.assert_not_called()

    def test_scope_hash_mismatch(self):
        """approved scope hash 불일치 시 중단."""
        self.evidence.approved_scope_hash = "fake-hash"
        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, self.jules_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "SCOPE_HASH_MISMATCH")
        self.mock_transport.request.assert_not_called()

    def test_base_sha_mismatch(self):
        """기준 SHA 불일치 시 중단."""
        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, self.jules_adapter, actual_base_sha="diff-sha"
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "BASE_SHA_MISMATCH")
        self.mock_transport.request.assert_not_called()

    def test_invalid_canonicalization(self):
        """정규화 과정에서의 타입/형식 오류 발생 시 예외 없이 NEEDS_HUMAN_REVIEW 처리"""
        # 잘못된 경로 포맷 주입 (절대 경로)
        self.contract.allowed_paths = [PathItem(path="/invalid/path", kind="file")]
        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, self.jules_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "SCOPE_CANONICALIZATION_FAILED")
        self.mock_transport.request.assert_not_called()

if __name__ == '__main__':
    unittest.main()
