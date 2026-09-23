import unittest
import logging
from orchestrator.plan_review_reader import read_latest_plan_review, PlanReviewResult
from orchestrator.models import TaskContract, PersistentSessionBinding
from orchestrator.jules_adapter import TransportError

class DummyJulesAdapter:
    def __init__(self, plan_text="dummy plan", raise_error=None):
        self.plan_text = plan_text
        self.raise_error = raise_error
        self.called_with = None

    def get_latest_plan_text(self, session_id: str):
        self.called_with = session_id
        if self.raise_error:
            raise self.raise_error
        return self.plan_text


class TestPlanReviewReader(unittest.TestCase):
    def setUp(self):
        self.contract = TaskContract(
            task_id="TASK-123",
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
            allowed_paths=[],
            forbidden_paths=[],
            risk_level='LOW',
            completion_conditions=[],
            auto_merge=False,
            plan_approval_required=True,
            idempotency_key="key",
            cancellation_conditions=[]
        )
        self.binding = PersistentSessionBinding(
            task_id="TASK-123",
            session_id="sessions/123",
            branch_name="branch",
            pr_number=1,
            contract_hash="hash1",
            approved_scope_hash="hash2",
            recorded_at_utc="utc"
        )

    def test_invalid_session_id(self):
        adapter = DummyJulesAdapter()
        res = read_latest_plan_review(adapter, "invalid_id", self.contract, self.binding)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason, "INVALID_SESSION_ID")
        self.assertEqual(res.plan_text, "")
        self.assertIsNone(adapter.called_with)

    def test_missing_contract_or_binding(self):
        adapter = DummyJulesAdapter()
        res = read_latest_plan_review(adapter, "sessions/123", None, self.binding)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason, "MISSING_BINDING_OR_CONTRACT")

        res2 = read_latest_plan_review(adapter, "sessions/123", self.contract, None)
        self.assertEqual(res2.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res2.reason, "MISSING_BINDING_OR_CONTRACT")

    def test_binding_mismatch(self):
        adapter = DummyJulesAdapter()
        bad_binding = PersistentSessionBinding(
            task_id="TASK-999",
            session_id="sessions/123",
            branch_name="branch",
            pr_number=1,
            contract_hash="hash1",
            approved_scope_hash="hash2",
            recorded_at_utc="utc"
        )
        res = read_latest_plan_review(adapter, "sessions/123", self.contract, bad_binding)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason, "BINDING_MISMATCH")

        bad_binding2 = PersistentSessionBinding(
            task_id="TASK-123",
            session_id="sessions/999",
            branch_name="branch",
            pr_number=1,
            contract_hash="hash1",
            approved_scope_hash="hash2",
            recorded_at_utc="utc"
        )
        res2 = read_latest_plan_review(adapter, "sessions/123", self.contract, bad_binding2)
        self.assertEqual(res2.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res2.reason, "BINDING_MISMATCH")

    def test_missing_plan_text(self):
        adapter = DummyJulesAdapter(plan_text=None)
        res = read_latest_plan_review(adapter, "sessions/123", self.contract, self.binding)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason, "NO_PLAN_FOUND_OR_INVALID_FORMAT")

    def test_success(self):
        adapter = DummyJulesAdapter(plan_text="the plan")
        res = read_latest_plan_review(adapter, "sessions/123", self.contract, self.binding)
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(res.plan_text, "the plan")

    def test_api_error(self):
        adapter = DummyJulesAdapter(raise_error=TransportError("SOME_ERROR"))
        res = read_latest_plan_review(adapter, "sessions/123", self.contract, self.binding)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason, "API_ERROR")

    def test_internal_error(self):
        adapter = DummyJulesAdapter(raise_error=ValueError("Boom"))
        res = read_latest_plan_review(adapter, "sessions/123", self.contract, self.binding)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason, "INTERNAL_ERROR")

    def test_plan_review_result_redaction(self):
        res = PlanReviewResult(_plan_text="SECRET_PLAN", status="SUCCESS")

        rep = repr(res)
        self.assertNotIn("SECRET_PLAN", rep)
        self.assertIn("<REDACTED>", rep)

        s = str(res)
        self.assertNotIn("SECRET_PLAN", s)
        self.assertIn("<REDACTED>", s)

        d = res.to_dict()
        self.assertNotIn("SECRET_PLAN", str(d))
        self.assertEqual(d["_plan_text"], "<REDACTED>")

    def test_no_io_logging_sqlite_calls(self):
        # logging, sqlite3, builtins.open이 절대 호출되지 않음을 엄격히 검증
        from unittest.mock import patch

        adapter = DummyJulesAdapter(plan_text="test plan")
        with patch("logging.Logger.info") as mock_info, \
             patch("logging.Logger.error") as mock_error, \
             patch("logging.Logger.warning") as mock_warning, \
             patch("logging.Logger.debug") as mock_debug, \
             patch("sqlite3.connect") as mock_sqlite, \
             patch("builtins.open") as mock_open:

            res = read_latest_plan_review(adapter, "sessions/123", self.contract, self.binding)

            self.assertEqual(res.status, "SUCCESS")
            self.assertEqual(res.plan_text, "test plan")

            mock_info.assert_not_called()
            mock_error.assert_not_called()
            mock_warning.assert_not_called()
            mock_debug.assert_not_called()
            mock_sqlite.assert_not_called()
            mock_open.assert_not_called()

if __name__ == '__main__':
    unittest.main()
