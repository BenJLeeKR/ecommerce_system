import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from orchestrator.models import PersistentSessionBinding, PathItem
from orchestrator.validator import TaskContract, ApprovalEvidence
from orchestrator.jules_adapter import JulesSessionResponse
from orchestrator.jules_content_review_reader import ReviewActivity
from orchestrator.manual_content_review_entrypoint import execute_manual_content_review_reader, ManualContentReviewRequest
from orchestrator.canonicalization import canonicalize_contract, canonicalize_scope


class TestManualContentReviewEntrypoint(unittest.TestCase):
    def setUp(self):
        self.session_id = "sessions/123"
        self.task_id = "task-123"
        self.approval_id = "app-123"

        self.contract = TaskContract(
            task_id=self.task_id,
            contract_version="v1",
            project_profile_id="p1",
            project_profile_version="v1",
            project_profile_reference_path="path",
            goal="goal",
            target_repository="repo",
            base_branch="main",
            base_commit_sha="sha",
            execution_agent="agent",
            reference_documents=[],
            allowed_paths=[PathItem(path="test", kind="file")],
            forbidden_paths=[],
            risk_level="HIGH",
            completion_conditions=[],
            idempotency_key="key",
            plan_approval_required=True,
            cancellation_conditions=[],
            auto_merge=False
        )

        _, self.scope_hash = canonicalize_scope(self.contract.allowed_paths, self.contract.forbidden_paths)
        _, self.contract_hash = canonicalize_contract(self.contract)

        self.evidence = ApprovalEvidence(
            approval_id=self.approval_id,
            task_id=self.task_id,
            contract_hash=self.contract_hash,
            approved_scope_hash=self.scope_hash,
            status="ACTIVE",
            approver="test_user",
            approval_time_utc="2024-01-01T00:00:00Z",
            contract_version="v1"
        )

        self.session_response = JulesSessionResponse(
            session_id=self.session_id,
            task_id=self.task_id,
            branch_name="feature/test",
            pr_number=1,
            status="COMPLETED",
            reason_code=None,
            created_at_utc="2024-01-01T00:00:00Z",
            updated_at_utc="2024-01-01T00:00:00Z"
        )

        self.binding = PersistentSessionBinding(
            session_id=self.session_id,
            task_id=self.task_id,
            branch_name="feature/test",
            pr_number=1,
            contract_hash=self.contract_hash,
            approved_scope_hash=self.scope_hash,
            recorded_at_utc="2024-01-01T00:00:00Z"
        )

        self.request = ManualContentReviewRequest(
            session_id=self.session_id,
            task_id=self.task_id,
            approval_id=self.approval_id,
            contract_hash=self.contract_hash,
            approved_scope_hash=self.scope_hash
        )

        self.mock_adapter = Mock()
        self.mock_adapter.fetch_raw_activities_for_content_review.return_value = [
            (datetime.now(timezone.utc), {"sessionCompleted": {}})
        ]

    def test_success_path_exactly_one_call(self):
        result = execute_manual_content_review_reader(
            self.request,
            self.contract,
            self.evidence,
            self.session_response,
            self.binding,
            self.mock_adapter
        )
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(len(result["activities"]), 1)
        self.assertEqual(result["activities"][0].activity_type, "SESSION_COMPLETED")
        self.assertEqual(self.mock_adapter.fetch_raw_activities_for_content_review.call_count, 1)

    def test_fail_request_session_id_mismatch(self):
        self.request.session_id = "sessions/other"
        result = execute_manual_content_review_reader(
            self.request, self.contract, self.evidence, self.session_response, self.binding, self.mock_adapter
        )
        self.assertEqual(result["status"], "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result["reason_code"], "SESSION_ID_MISMATCH")
        self.assertEqual(self.mock_adapter.fetch_raw_activities_for_content_review.call_count, 0)

    def test_fail_request_task_id_mismatch(self):
        self.request.task_id = "task-other"
        result = execute_manual_content_review_reader(
            self.request, self.contract, self.evidence, self.session_response, self.binding, self.mock_adapter
        )
        self.assertEqual(result["status"], "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result["reason_code"], "TASK_ID_MISMATCH")
        self.assertEqual(self.mock_adapter.fetch_raw_activities_for_content_review.call_count, 0)

    def test_fail_request_approval_id_mismatch(self):
        self.request.approval_id = "app-other"
        result = execute_manual_content_review_reader(
            self.request, self.contract, self.evidence, self.session_response, self.binding, self.mock_adapter
        )
        self.assertEqual(result["status"], "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result["reason_code"], "APPROVAL_ID_MISMATCH")
        self.assertEqual(self.mock_adapter.fetch_raw_activities_for_content_review.call_count, 0)

    def test_fail_request_contract_hash_mismatch(self):
        self.request.contract_hash = "other-hash"
        result = execute_manual_content_review_reader(
            self.request, self.contract, self.evidence, self.session_response, self.binding, self.mock_adapter
        )
        self.assertEqual(result["status"], "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result["reason_code"], "REQUEST_CONTRACT_HASH_MISMATCH")
        self.assertEqual(self.mock_adapter.fetch_raw_activities_for_content_review.call_count, 0)

    def test_fail_request_scope_hash_mismatch(self):
        self.request.approved_scope_hash = "other-hash"
        result = execute_manual_content_review_reader(
            self.request, self.contract, self.evidence, self.session_response, self.binding, self.mock_adapter
        )
        self.assertEqual(result["status"], "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result["reason_code"], "REQUEST_SCOPE_HASH_MISMATCH")
        self.assertEqual(self.mock_adapter.fetch_raw_activities_for_content_review.call_count, 0)

    def test_fail_evidence_version_mismatch(self):
        self.evidence.contract_version = "v2"
        result = execute_manual_content_review_reader(
            self.request, self.contract, self.evidence, self.session_response, self.binding, self.mock_adapter
        )
        self.assertEqual(result["status"], "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result["reason_code"], "EVIDENCE_CONTRACT_VERSION_MISMATCH")
        self.assertEqual(self.mock_adapter.fetch_raw_activities_for_content_review.call_count, 0)

    def test_fail_binding_branch_mismatch(self):
        self.binding.branch_name = "feature/other"
        result = execute_manual_content_review_reader(
            self.request, self.contract, self.evidence, self.session_response, self.binding, self.mock_adapter
        )
        self.assertEqual(result["status"], "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result["reason_code"], "BINDING_BRANCH_MISMATCH")
        self.assertEqual(self.mock_adapter.fetch_raw_activities_for_content_review.call_count, 0)

    def test_fail_binding_pr_mismatch(self):
        self.binding.pr_number = 999
        result = execute_manual_content_review_reader(
            self.request, self.contract, self.evidence, self.session_response, self.binding, self.mock_adapter
        )
        self.assertEqual(result["status"], "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result["reason_code"], "BINDING_PR_MISMATCH")
        self.assertEqual(self.mock_adapter.fetch_raw_activities_for_content_review.call_count, 0)

    def test_fail_binding_contract_hash_mismatch(self):
        self.binding.contract_hash = "other-hash"
        result = execute_manual_content_review_reader(
            self.request, self.contract, self.evidence, self.session_response, self.binding, self.mock_adapter
        )
        self.assertEqual(result["status"], "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result["reason_code"], "BINDING_CONTRACT_HASH_MISMATCH")
        self.assertEqual(self.mock_adapter.fetch_raw_activities_for_content_review.call_count, 0)

    def test_fail_plan_approval_not_required(self):
        self.contract.plan_approval_required = False
        _, new_contract_hash = canonicalize_contract(self.contract)
        self.request.contract_hash = new_contract_hash
        self.evidence.contract_hash = new_contract_hash
        self.binding.contract_hash = new_contract_hash
        result = execute_manual_content_review_reader(
            self.request, self.contract, self.evidence, self.session_response, self.binding, self.mock_adapter
        )
        self.assertEqual(result["status"], "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result["reason_code"], "PLAN_APPROVAL_NOT_REQUIRED")
        self.assertEqual(self.mock_adapter.fetch_raw_activities_for_content_review.call_count, 0)

    def test_fail_reader_fetch_failed(self):
        self.mock_adapter.fetch_raw_activities_for_content_review.return_value = None
        result = execute_manual_content_review_reader(
            self.request, self.contract, self.evidence, self.session_response, self.binding, self.mock_adapter
        )
        self.assertEqual(result["status"], "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result["reason_code"], "RAW_ACTIVITIES_FETCH_FAILED")
        self.assertEqual(self.mock_adapter.fetch_raw_activities_for_content_review.call_count, 1)

    @patch('builtins.open')
    @patch('logging.Logger.info')
    @patch('sqlite3.connect')
    def test_non_persistence_and_no_leak(self, mock_sqlite, mock_log, mock_open):
        self.mock_adapter.fetch_raw_activities_for_content_review.return_value = [
            (datetime.now(timezone.utc), {"agentMessaged": {"agentMessage": "secret prompt text"}})
        ]

        result = execute_manual_content_review_reader(
            self.request, self.contract, self.evidence, self.session_response, self.binding, self.mock_adapter
        )
        self.assertEqual(result["status"], "SUCCESS")

        activity = result["activities"][0]
        self.assertIn("<REDACTED>", repr(activity))
        self.assertIn("<REDACTED>", str(activity))
        self.assertEqual(activity.to_dict()["agent_message"], "<REDACTED>")

        mock_sqlite.assert_not_called()
        mock_open.assert_not_called()

if __name__ == '__main__':
    unittest.main()
