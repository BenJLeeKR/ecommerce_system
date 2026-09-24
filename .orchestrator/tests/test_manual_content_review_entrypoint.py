import unittest
from unittest.mock import Mock, patch

from orchestrator.models import PersistentSessionBinding, PathItem
from orchestrator.validator import TaskContract, ApprovalEvidence
from orchestrator.jules_adapter import JulesSessionResponse
from orchestrator.jules_content_review_reader import ReviewActivity
from orchestrator.manual_content_review_entrypoint import execute_manual_content_review_reader
from orchestrator.canonicalization import canonicalize_contract, canonicalize_scope


class TestManualContentReviewEntrypoint(unittest.TestCase):
    def setUp(self):
        self.session_id = "sessions/123"
        self.task_id = "task-123"

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

        _, scope_hash = canonicalize_scope(self.contract.allowed_paths, self.contract.forbidden_paths)
        _, contract_hash = canonicalize_contract(self.contract)

        self.evidence = ApprovalEvidence(
            approval_id="app-123",
            task_id=self.task_id,
            contract_hash=contract_hash,
            approved_scope_hash=scope_hash,
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
            contract_hash=contract_hash,
            approved_scope_hash=scope_hash,
            recorded_at_utc="2024-01-01T00:00:00Z"
        )

        from datetime import datetime, timezone
        self.mock_adapter = Mock()
        self.mock_adapter.fetch_raw_activities_for_content_review.return_value = [
            (datetime.now(timezone.utc), {"sessionCompleted": {}})
        ]

    def test_success_path_exactly_one_call(self):
        result = execute_manual_content_review_reader(
            self.session_id,
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

    def test_fail_session_id_mismatch(self):
        result = execute_manual_content_review_reader(
            "sessions/other", self.contract, self.evidence, self.session_response, self.binding, self.mock_adapter
        )
        self.assertEqual(result["status"], "NEEDS_HUMAN_REVIEW")
        self.assertEqual(self.mock_adapter.fetch_raw_activities_for_content_review.call_count, 0)

    def test_fail_task_id_mismatch(self):
        contract_mismatch = TaskContract(
            task_id="task-other",
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
        result = execute_manual_content_review_reader(
            self.session_id, contract_mismatch, self.evidence, self.session_response, self.binding, self.mock_adapter
        )
        self.assertEqual(result["status"], "NEEDS_HUMAN_REVIEW")
        self.assertEqual(self.mock_adapter.fetch_raw_activities_for_content_review.call_count, 0)

    def test_fail_not_active(self):
        self.evidence.status = "REVOKED"
        result = execute_manual_content_review_reader(
            self.session_id, self.contract, self.evidence, self.session_response, self.binding, self.mock_adapter
        )
        self.assertEqual(result["status"], "NEEDS_HUMAN_REVIEW")
        self.assertEqual(self.mock_adapter.fetch_raw_activities_for_content_review.call_count, 0)

    def test_fail_auto_merge_true(self):
        self.contract.auto_merge = True
        result = execute_manual_content_review_reader(
            self.session_id, self.contract, self.evidence, self.session_response, self.binding, self.mock_adapter
        )
        self.assertEqual(result["status"], "NEEDS_HUMAN_REVIEW")
        self.assertEqual(self.mock_adapter.fetch_raw_activities_for_content_review.call_count, 0)

    @patch('builtins.open')
    @patch('logging.Logger.info')
    @patch('sqlite3.connect')
    def test_non_persistence_and_no_leak(self, mock_sqlite, mock_log, mock_open):
        from datetime import datetime, timezone
        self.mock_adapter.fetch_raw_activities_for_content_review.return_value = [
            (datetime.now(timezone.utc), {"agentMessaged": {"agentMessage": "secret prompt text"}})
        ]

        result = execute_manual_content_review_reader(
            self.session_id, self.contract, self.evidence, self.session_response, self.binding, self.mock_adapter
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
