import unittest
from unittest.mock import Mock, call

from orchestrator.models import TaskContract, ApprovalEvidence, PathItem
from orchestrator.jules_adapter import JulesSessionResponse, JulesSessionRequest
from orchestrator.dispatch_entrypoint import execute_dispatch_session

class TestDispatchEntrypoint(unittest.TestCase):
    def setUp(self):
        self.mock_adapter = Mock()
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

        from orchestrator.canonicalization import canonicalize_contract, canonicalize_scope
        self.contract_hash = canonicalize_contract(self.contract)
        self.scope_hash = canonicalize_scope(self.contract.allowed_paths, self.contract.forbidden_paths)

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

        # 기본 성공 응답
        self.success_response = JulesSessionResponse(
            session_id="sess-1",
            task_id="TEST-001",
            branch_name="main",
            pr_number=None,
            status="CREATED",
            reason_code=None,
            created_at_utc="2026-09-23T12:00:00Z",
            updated_at_utc="2026-09-23T12:00:00Z"
        )
        self.mock_adapter.create_session.return_value = self.success_response

    def test_success_path(self):
        """정상 경로에서 create_session이 main 브랜치와 plan_approval_required=True로 호출되는지 검증."""
        response = execute_dispatch_session(
            contract=self.contract,
            approval_evidence=self.evidence,
            source_name=self.source_name,
            jules_adapter=self.mock_adapter,
            actual_base_sha=self.actual_base_sha
        )

        self.assertEqual(response.status, "CREATED")

        # 어댑터 호출 검증
        self.mock_adapter.create_session.assert_called_once()
        call_args = self.mock_adapter.create_session.call_args[1]

        self.assertEqual(call_args["start_branch_name"], "main")
        self.assertTrue(call_args["plan_approval_required"])

        request: JulesSessionRequest = call_args["request"]
        self.assertEqual(request.source_name, self.source_name)
        self.assertEqual(request.contract_hash, self.contract_hash)
        self.assertEqual(request.approved_scope_hash, self.scope_hash)

    def test_approval_not_active(self):
        """승인 상태가 ACTIVE가 아니면 중단."""
        self.evidence.status = "WITHDRAWN"
        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, self.mock_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "APPROVAL_NOT_ACTIVE")
        self.mock_adapter.create_session.assert_not_called()

    def test_auto_merge_not_allowed(self):
        """auto_merge가 True이면 중단."""
        self.contract.auto_merge = True

        from orchestrator.canonicalization import canonicalize_contract
        self.evidence.contract_hash = canonicalize_contract(self.contract) # 해시 불일치를 막기 위해 갱신

        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, self.mock_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "AUTO_MERGE_NOT_ALLOWED")
        self.mock_adapter.create_session.assert_not_called()

    def test_plan_approval_not_required(self):
        """plan_approval_required가 False이면 중단."""
        self.contract.plan_approval_required = False

        from orchestrator.canonicalization import canonicalize_contract
        self.evidence.contract_hash = canonicalize_contract(self.contract) # 해시 불일치를 막기 위해 갱신

        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, self.mock_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "PLAN_APPROVAL_REQUIRED")
        self.mock_adapter.create_session.assert_not_called()

    def test_contract_hash_mismatch(self):
        """contract hash 불일치 시 중단."""
        self.evidence.contract_hash = "fake-hash"
        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, self.mock_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "CONTRACT_HASH_MISMATCH")
        self.mock_adapter.create_session.assert_not_called()

    def test_scope_hash_mismatch(self):
        """approved scope hash 불일치 시 중단."""
        self.evidence.approved_scope_hash = "fake-hash"
        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, self.mock_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "SCOPE_HASH_MISMATCH")
        self.mock_adapter.create_session.assert_not_called()

    def test_base_sha_mismatch(self):
        """기준 SHA 불일치 시 중단."""
        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, self.mock_adapter, actual_base_sha="diff-sha"
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "BASE_SHA_MISMATCH")
        self.mock_adapter.create_session.assert_not_called()

if __name__ == '__main__':
    unittest.main()
