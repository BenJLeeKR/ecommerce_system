import unittest
from unittest.mock import patch, MagicMock

from orchestrator.models import TaskContract, ApprovalEvidence, PathItem, PlanSessionRegistration, PlanSessionRegistrationResult
from orchestrator.jules_adapter import JulesSessionResponse
from orchestrator.manual_registered_content_review_entrypoint import (
    ManualRegisteredContentReviewRequest,
    execute_manual_registered_content_review,
)

class TestManualRegisteredContentReviewEntrypoint(unittest.TestCase):
    def setUp(self):
        self.repository = MagicMock()
        self.jules_adapter = MagicMock()

        self.contract = TaskContract(
            project_profile_id="PRJ-1",
            project_profile_version="v1",
            project_profile_reference_path="docs/profile.md",
            task_id="task-123",
            goal="Test goal",
            target_repository="repo",
            base_branch="main",
            base_commit_sha="abcdef123456",
            execution_agent="Jules",
            allowed_paths=[PathItem(path="src/", kind="directory_recursive")],
            forbidden_paths=[],
            reference_documents=[],
            risk_level="HIGH",
            completion_conditions=[],
            cancellation_conditions=[],
            idempotency_key="idemp-key-001",
            plan_approval_required=True,
            auto_merge=False,
            contract_version="v1"
        )
        self.contract_hash = "6eb5db32766dc855fc6235bdf8e9846b02a28189cda631ed97cf2b48956903f6"
        # Dummy scope hash based on canonicalization
        from orchestrator.canonicalization import canonicalize_scope, canonicalize_contract
        _, self.contract_hash = canonicalize_contract(self.contract)
        _, self.scope_hash = canonicalize_scope(self.contract.allowed_paths, self.contract.forbidden_paths)

        self.approval_evidence = ApprovalEvidence(
            approval_id="approval-456",
            task_id="task-123",
            contract_hash=self.contract_hash,
            approved_scope_hash=self.scope_hash,
            status="ACTIVE",
            contract_version="v1",
            approver="user1",
            approval_time_utc="2023-10-27T10:00:00Z"
        )

        self.review_request = ManualRegisteredContentReviewRequest(
            task_id="task-123",
            approval_id="approval-456",
            contract_hash=self.contract_hash,
            approved_scope_hash=self.scope_hash,
            session_id="sessions/session-789"
        )

        self.registration = PlanSessionRegistration(
            task_id="task-123",
            session_id="sessions/session-789",
            approval_id="approval-456",
            contract_hash=self.contract_hash,
            approved_scope_hash=self.scope_hash,
            created_at_utc="2023-10-27T10:00:00Z"
        )
        self.valid_registration_result = PlanSessionRegistrationResult(
            status="REGISTERED",
            registration=self.registration
        )

    def test_request_object_redaction(self):
        self.assertEqual(repr(self.review_request), "<ManualRegisteredContentReviewRequest: <REDACTED>>")
        self.assertEqual(str(self.review_request), "<ManualRegisteredContentReviewRequest: <REDACTED>>")
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

    @patch("orchestrator.manual_registered_content_review_entrypoint.get_plan_session_registration")
    @patch("orchestrator.jules_content_review_reader.fetch_content_review_activities")
    def test_policy_failure_not_active(self, mock_reader, mock_get_reg):
        self.approval_evidence.status = "REVOKED"
        result = execute_manual_registered_content_review(
            repository=self.repository,
            jules_adapter=self.jules_adapter,
            contract=self.contract,
            approval_evidence=self.approval_evidence,
            review_request=self.review_request,
        )
        self.assertEqual(result["status"], "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result["reason_code"], "APPROVAL_NOT_ACTIVE")
        mock_get_reg.assert_not_called()
        mock_reader.assert_not_called()

    @patch("orchestrator.manual_registered_content_review_entrypoint.get_plan_session_registration")
    @patch("orchestrator.jules_content_review_reader.fetch_content_review_activities")
    def test_missing_registration(self, mock_reader, mock_get_reg):
        mock_get_reg.return_value = PlanSessionRegistrationResult(
            status="NEEDS_HUMAN_REVIEW", reason_code="PLAN_SESSION_NOT_REGISTERED"
        )
        result = execute_manual_registered_content_review(
            repository=self.repository,
            jules_adapter=self.jules_adapter,
            contract=self.contract,
            approval_evidence=self.approval_evidence,
            review_request=self.review_request,
        )
        self.assertEqual(result["status"], "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result["reason_code"], "PLAN_SESSION_NOT_REGISTERED")
        mock_get_reg.assert_called_once_with(repository=self.repository, task_id="task-123")
        mock_reader.assert_not_called()

    @patch("orchestrator.manual_registered_content_review_entrypoint.get_plan_session_registration")
    @patch("orchestrator.jules_content_review_reader.fetch_content_review_activities")
    def test_happy_path(self, mock_reader, mock_get_reg):
        mock_get_reg.return_value = self.valid_registration_result
        mock_reader.return_value = {"status": "SUCCESS", "activities": ["dummy"]}

        result = execute_manual_registered_content_review(
            repository=self.repository,
            jules_adapter=self.jules_adapter,
            contract=self.contract,
            approval_evidence=self.approval_evidence,
            review_request=self.review_request,
        )

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["activities"], ["dummy"])
        mock_get_reg.assert_called_once_with(repository=self.repository, task_id="task-123")

        args, kwargs = mock_reader.call_args
        self.assertEqual(kwargs["session_id"], "sessions/session-789")
        self.assertEqual(kwargs["adapter"], self.jules_adapter)
        self.assertEqual(kwargs["contract"], self.contract)
        self.assertEqual(kwargs["evidence"], self.approval_evidence)
        self.assertEqual(kwargs["session_response"].session_id, "sessions/session-789")
        self.assertEqual(kwargs["session_response"].status, "CREATED")

    @patch("orchestrator.manual_registered_content_review_entrypoint.get_plan_session_registration")
    def test_happy_path_real_reader_integration(self, mock_get_reg):
        mock_get_reg.return_value = self.valid_registration_result

        class FakeAdapter:
            def fetch_raw_activities_for_content_review(self, session_id):
                self.called = True
                from datetime import datetime, timezone
                dt = datetime.now(timezone.utc)
                return [(dt, {"sessionCompleted": {}})]

        fake_adapter = FakeAdapter()
        fake_adapter.called = False

        result = execute_manual_registered_content_review(
            repository=self.repository,
            jules_adapter=fake_adapter,
            contract=self.contract,
            approval_evidence=self.approval_evidence,
            review_request=self.review_request,
        )

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(len(result["activities"]), 1)
        self.assertEqual(result["activities"][0].activity_type, "SESSION_COMPLETED")
        self.assertTrue(fake_adapter.called)

if __name__ == '__main__':
    unittest.main()
