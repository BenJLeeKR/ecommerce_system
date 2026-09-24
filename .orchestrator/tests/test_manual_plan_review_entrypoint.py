import unittest
from unittest.mock import Mock, patch

from orchestrator.models import TaskContract, ApprovalEvidence, PlanSessionRegistration, PathItem
from orchestrator.canonicalization import canonicalize_contract, canonicalize_scope
from orchestrator.manual_plan_review_entrypoint import (
    ManualPlanReviewRequest,
    execute_manual_registered_plan_review,
)
from orchestrator.plan_session_registration import PlanSessionRegistrationResult
from orchestrator.plan_review_reader import PlanReviewResult

class TestManualPlanReviewEntrypoint(unittest.TestCase):
    def setUp(self):
        self.repository = Mock()
        self.transport = Mock()

        # Valid Contract
        self.contract = TaskContract(
            task_id="task-123",
            contract_version="1.0",
            project_profile_id="proj-1",
            project_profile_version="1.0",
            project_profile_reference_path="docs/",
            goal="Test",
            target_repository="repo",
            base_branch="main",
            base_commit_sha="abcdef123456",
            execution_agent="jules",
            reference_documents=[],
            risk_level="LOW",
            plan_approval_required=True,
            auto_merge=False,
            completion_conditions=[],
            cancellation_conditions=[],
            allowed_paths=[PathItem(path="src/", kind="directory_recursive")],
            forbidden_paths=[PathItem(path="src/secret.py", kind="file")],
            idempotency_key="idemp-key-1"
        )
        _, self.contract_hash = canonicalize_contract(self.contract)
        _, self.scope_hash = canonicalize_scope(self.contract.allowed_paths, self.contract.forbidden_paths)

        # Valid ApprovalEvidence
        self.approval_evidence = ApprovalEvidence(
            approval_id="approval-456",
            task_id="task-123",
            contract_version="1.0",
            contract_hash=self.contract_hash,
            approved_scope_hash=self.scope_hash,
            status="ACTIVE",
            approver="admin",
            approval_time_utc="2023-10-27T10:00:00Z"
        )

        # Valid Request
        self.review_request = ManualPlanReviewRequest(
            task_id="task-123",
            approval_id="approval-456",
            contract_hash=self.contract_hash,
            approved_scope_hash=self.scope_hash,
            session_id="session-789"
        )

        # Valid Registration
        self.registration = PlanSessionRegistration(
            task_id="task-123",
            session_id="session-789",
            approval_id="approval-456",
            contract_hash=self.contract_hash,
            approved_scope_hash=self.scope_hash,
            created_at_utc="2023-10-27T10:00:00Z"
        )

        self.valid_registration_result = PlanSessionRegistrationResult(
            status="REGISTERED",
            registration=self.registration
        )

    def test_request_object_masking(self):
        """요청 객체의 민감 정보 마스킹 검증"""
        self.assertEqual(repr(self.review_request), "<ManualPlanReviewRequest: <REDACTED>>")
        self.assertEqual(str(self.review_request), "<ManualPlanReviewRequest: <REDACTED>>")
        self.assertEqual(
            self.review_request.to_dict(),
            {
                "task_id": "<REDACTED>",
                "approval_id": "<REDACTED>",
                "contract_hash": "<REDACTED>",
                "approved_scope_hash": "<REDACTED>",
                "session_id": "<REDACTED>",
            }
        )

    @patch("orchestrator.manual_plan_review_entrypoint.get_plan_session_registration")
    @patch("orchestrator.manual_plan_review_entrypoint.execute_manual_plan_review_reader")
    def test_policy_failure_not_active(self, mock_reader, mock_get_reg):
        """정책 조건 실패 (ACTIVE 아님) - 조회 0회, 위임 0회"""
        self.approval_evidence.status = "REVOKED"

        result = execute_manual_registered_plan_review(
            repository=self.repository,
            transport=self.transport,
            contract=self.contract,
            approval_evidence=self.approval_evidence,
            review_request=self.review_request,
        )

        self.assertEqual(result.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result.reason_code, "APPROVAL_NOT_ACTIVE")
        mock_get_reg.assert_not_called()
        mock_reader.assert_not_called()

    @patch("orchestrator.manual_plan_review_entrypoint.get_plan_session_registration")
    @patch("orchestrator.manual_plan_review_entrypoint.execute_manual_plan_review_reader")
    def test_policy_failure_plan_approval_not_required(self, mock_reader, mock_get_reg):
        """정책 조건 실패 (plan_approval_required=False) - 조회 0회, 위임 0회"""
        self.contract.plan_approval_required = False

        result = execute_manual_registered_plan_review(
            repository=self.repository,
            transport=self.transport,
            contract=self.contract,
            approval_evidence=self.approval_evidence,
            review_request=self.review_request,
        )

        self.assertEqual(result.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result.reason_code, "PLAN_APPROVAL_REQUIRED")
        mock_get_reg.assert_not_called()
        mock_reader.assert_not_called()

    @patch("orchestrator.manual_plan_review_entrypoint.get_plan_session_registration")
    @patch("orchestrator.manual_plan_review_entrypoint.execute_manual_plan_review_reader")
    def test_policy_failure_auto_merge_true(self, mock_reader, mock_get_reg):
        """정책 조건 실패 (auto_merge=True) - 조회 0회, 위임 0회"""
        self.contract.auto_merge = True

        result = execute_manual_registered_plan_review(
            repository=self.repository,
            transport=self.transport,
            contract=self.contract,
            approval_evidence=self.approval_evidence,
            review_request=self.review_request,
        )

        self.assertEqual(result.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result.reason_code, "AUTO_MERGE_NOT_ALLOWED")
        mock_get_reg.assert_not_called()
        mock_reader.assert_not_called()

    @patch("orchestrator.manual_plan_review_entrypoint.get_plan_session_registration")
    @patch("orchestrator.manual_plan_review_entrypoint.execute_manual_plan_review_reader")
    def test_missing_registration(self, mock_reader, mock_get_reg):
        """등록 누락 시 - 위임 0회"""
        mock_get_reg.return_value = PlanSessionRegistrationResult(
            status="NEEDS_HUMAN_REVIEW", reason_code="PLAN_SESSION_NOT_REGISTERED"
        )

        result = execute_manual_registered_plan_review(
            repository=self.repository,
            transport=self.transport,
            contract=self.contract,
            approval_evidence=self.approval_evidence,
            review_request=self.review_request,
        )

        self.assertEqual(result.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result.reason_code, "PLAN_SESSION_NOT_REGISTERED")
        mock_get_reg.assert_called_once_with(repository=self.repository, task_id="task-123")
        mock_reader.assert_not_called()

    @patch("orchestrator.manual_plan_review_entrypoint.get_plan_session_registration")
    @patch("orchestrator.manual_plan_review_entrypoint.execute_manual_plan_review_reader")
    def test_registration_mismatch(self, mock_reader, mock_get_reg):
        """세션 정보 불일치 시 - 위임 0회"""
        self.registration.session_id = "different-session"
        mock_get_reg.return_value = PlanSessionRegistrationResult(
            status="REGISTERED", registration=self.registration
        )

        result = execute_manual_registered_plan_review(
            repository=self.repository,
            transport=self.transport,
            contract=self.contract,
            approval_evidence=self.approval_evidence,
            review_request=self.review_request,
        )

        self.assertEqual(result.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result.reason_code, "REGISTRATION_MISMATCH")
        mock_get_reg.assert_called_once_with(repository=self.repository, task_id="task-123")
        mock_reader.assert_not_called()

    @patch("orchestrator.manual_plan_review_entrypoint.get_plan_session_registration")
    @patch("orchestrator.manual_plan_review_entrypoint.execute_manual_plan_review_reader")
    def test_repository_exception(self, mock_reader, mock_get_reg):
        """Repository 조회 실패 시 - 위임 0회"""
        mock_get_reg.return_value = PlanSessionRegistrationResult(
            status="NEEDS_HUMAN_REVIEW", reason_code="PLAN_SESSION_LOOKUP_FAILED"
        )

        result = execute_manual_registered_plan_review(
            repository=self.repository,
            transport=self.transport,
            contract=self.contract,
            approval_evidence=self.approval_evidence,
            review_request=self.review_request,
        )

        self.assertEqual(result.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result.reason_code, "PLAN_SESSION_LOOKUP_FAILED")
        mock_get_reg.assert_called_once_with(repository=self.repository, task_id="task-123")
        mock_reader.assert_not_called()

    @patch("orchestrator.manual_plan_review_entrypoint.get_plan_session_registration")
    @patch("orchestrator.manual_plan_review_entrypoint.execute_manual_plan_review_reader")
    @patch("builtins.open")
    @patch("logging.Logger.info")
    def test_happy_path(self, mock_log_info, mock_open, mock_reader, mock_get_reg):
        """정상 경로 - 조회 1회, 위임 1회 및 파일/로그 쓰기 0회"""
        mock_get_reg.return_value = self.valid_registration_result
        mock_reader.return_value = PlanReviewResult(
            status="NEEDS_HUMAN_REVIEW",
            reason_code="PLAN_NEEDS_REVIEW",
            plan_text="Plan Content"
        )

        result = execute_manual_registered_plan_review(
            repository=self.repository,
            transport=self.transport,
            contract=self.contract,
            approval_evidence=self.approval_evidence,
            review_request=self.review_request,
        )

        self.assertEqual(result.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result.reason_code, "PLAN_NEEDS_REVIEW")

        # Verify get_plan_session_registration called exactly once
        mock_get_reg.assert_called_once_with(repository=self.repository, task_id="task-123")

        # Verify execute_manual_plan_review_reader called exactly once
        mock_reader.assert_called_once()

        # Verify file/logging not called
        mock_open.assert_not_called()
        mock_log_info.assert_not_called()


if __name__ == '__main__':
    unittest.main()
