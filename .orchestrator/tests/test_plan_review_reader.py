import unittest
import copy
from orchestrator.plan_review_reader import execute_manual_plan_review_reader, PlanReviewResult
from orchestrator.models import TaskContract, ApprovalEvidence
from orchestrator.jules_adapter import JulesSessionResponse

class DummyAdapter:
    def __init__(self, plan_text=None, should_fail=False):
        self.plan_text = plan_text
        self.should_fail = should_fail
        self.call_count = 0

    def fetch_plan_text_only(self, session_id: str):
        self.call_count += 1
        if self.should_fail:
            raise Exception("API error")
        return self.plan_text

class TestPlanReviewReader(unittest.TestCase):
    def setUp(self):
        self.contract = TaskContract(
            task_id="TASK-001",
            contract_version="v1",
            project_profile_id="P-001",
            project_profile_version="v1",
            project_profile_reference_path="path",
            goal="Goal",
            target_repository="repo",
            base_branch="main",
            base_commit_sha="77b26149d24b9620615b9b52cfc9606cc41cd9ee",
            execution_agent="Jules",
            reference_documents=[],
            allowed_paths=[],
            forbidden_paths=[],
            risk_level="MEDIUM",
            completion_conditions=[],
            idempotency_key="idem-v1",
            plan_approval_required=True,
            cancellation_conditions=[],
            auto_merge=False
        )
        self.evidence = ApprovalEvidence(
            approval_id="APV-001",
            task_id="TASK-001",
            contract_version="v1",
            contract_hash="hash1",
            approved_scope_hash="hash2",
            approver="user",
            approval_time_utc="2023-01-01T00:00:00Z",
            status="ACTIVE"
        )
        self.session_res = JulesSessionResponse(
            session_id="SES-001",
            task_id="TASK-001",
            branch_name=None,
            pr_number=None,
            status="RUNNING",
            reason_code=None,
            created_at_utc="2023-01-01T00:00:00Z",
            updated_at_utc="2023-01-01T00:00:00Z"
        )
        self.adapter = DummyAdapter(plan_text="My Plan Text")

    def test_success(self):
        res = execute_manual_plan_review_reader(
            session_id="SES-001",
            contract=self.contract,
            approval_evidence=self.evidence,
            session_response=self.session_res,
            jules_adapter=self.adapter
        )
        self.assertEqual(res.status, "PLAN_READY")
        self.assertEqual(res.plan_text, "My Plan Text")
        self.assertEqual(self.adapter.call_count, 1)

    def test_fail_session_id_mismatch(self):
        res = execute_manual_plan_review_reader(
            session_id="SES-002",
            contract=self.contract,
            approval_evidence=self.evidence,
            session_response=self.session_res,
            jules_adapter=self.adapter
        )
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason_code, "SESSION_ID_MISMATCH")
        self.assertEqual(self.adapter.call_count, 0)

    def test_fail_task_id_mismatch(self):
        mod_res = copy.deepcopy(self.session_res)
        mod_res.task_id = "TASK-002"
        res = execute_manual_plan_review_reader(
            session_id="SES-001",
            contract=self.contract,
            approval_evidence=self.evidence,
            session_response=mod_res,
            jules_adapter=self.adapter
        )
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason_code, "TASK_ID_MISMATCH")
        self.assertEqual(self.adapter.call_count, 0)

    def test_fail_plan_approval_not_required(self):
        mod_contract = copy.deepcopy(self.contract)
        mod_contract.plan_approval_required = False
        res = execute_manual_plan_review_reader(
            session_id="SES-001",
            contract=mod_contract,
            approval_evidence=self.evidence,
            session_response=self.session_res,
            jules_adapter=self.adapter
        )
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason_code, "PLAN_APPROVAL_NOT_REQUIRED")
        self.assertEqual(self.adapter.call_count, 0)

    def test_fail_approval_not_active(self):
        mod_ev = copy.deepcopy(self.evidence)
        mod_ev.status = "EXPIRED"
        res = execute_manual_plan_review_reader(
            session_id="SES-001",
            contract=self.contract,
            approval_evidence=mod_ev,
            session_response=self.session_res,
            jules_adapter=self.adapter
        )
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason_code, "APPROVAL_NOT_ACTIVE")
        self.assertEqual(self.adapter.call_count, 0)

    def test_fail_plan_fetch_api_error(self):
        bad_adapter = DummyAdapter(should_fail=True)
        res = execute_manual_plan_review_reader(
            session_id="SES-001",
            contract=self.contract,
            approval_evidence=self.evidence,
            session_response=self.session_res,
            jules_adapter=bad_adapter
        )
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason_code, "PLAN_FETCH_FAILED")

    def test_fail_plan_not_found(self):
        empty_adapter = DummyAdapter(plan_text=None)
        res = execute_manual_plan_review_reader(
            session_id="SES-001",
            contract=self.contract,
            approval_evidence=self.evidence,
            session_response=self.session_res,
            jules_adapter=empty_adapter
        )
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason_code, "PLAN_NOT_FOUND")

    def test_redaction_in_repr_and_dict(self):
        res = PlanReviewResult(status="PLAN_READY", plan_text="Super Secret Plan")
        self.assertNotIn("Super Secret Plan", repr(res))
        self.assertNotIn("Super Secret Plan", str(res))
        self.assertEqual(res.to_dict()["plan_text"], "<REDACTED>")

if __name__ == '__main__':
    unittest.main()
