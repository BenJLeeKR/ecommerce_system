import unittest
import copy
from orchestrator.plan_review_reader import execute_manual_plan_review_reader, PlanReviewResult, ManualReviewRequest
from orchestrator.models import TaskContract, ApprovalEvidence
from orchestrator.jules_adapter import JulesSessionResponse
from orchestrator.canonicalization import canonicalize_contract, canonicalize_scope

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
        _, self.expected_contract_hash = canonicalize_contract(self.contract)
        _, self.expected_scope_hash = canonicalize_scope(self.contract.allowed_paths, self.contract.forbidden_paths)

        self.evidence = ApprovalEvidence(
            approval_id="APV-001",
            task_id="TASK-001",
            contract_version="v1",
            contract_hash=self.expected_contract_hash,
            approved_scope_hash=self.expected_scope_hash,
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
        self.request = ManualReviewRequest(
            session_id="SES-001",
            task_id="TASK-001",
            approval_id="APV-001",
            contract_hash=self.expected_contract_hash,
            approved_scope_hash=self.expected_scope_hash
        )
        self.adapter = DummyAdapter(plan_text="My Plan Text")

    def test_success(self):
        res = execute_manual_plan_review_reader(
            review_request=self.request,
            contract=self.contract,
            approval_evidence=self.evidence,
            session_response=self.session_res,
            jules_adapter=self.adapter
        )
        self.assertEqual(res.status, "PLAN_READY")
        self.assertEqual(res.plan_text, "My Plan Text")
        self.assertEqual(self.adapter.call_count, 1)

    def test_fail_session_id_mismatch(self):
        mod_req = copy.deepcopy(self.request)
        mod_req.session_id = "SES-002"
        res = execute_manual_plan_review_reader(
            review_request=mod_req,
            contract=self.contract,
            approval_evidence=self.evidence,
            session_response=self.session_res,
            jules_adapter=self.adapter
        )
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason_code, "SESSION_ID_MISMATCH")
        self.assertEqual(self.adapter.call_count, 0)

    def test_fail_task_id_mismatch(self):
        mod_req = copy.deepcopy(self.request)
        mod_req.task_id = "TASK-002"
        res = execute_manual_plan_review_reader(
            review_request=mod_req,
            contract=self.contract,
            approval_evidence=self.evidence,
            session_response=self.session_res,
            jules_adapter=self.adapter
        )
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason_code, "TASK_ID_MISMATCH")
        self.assertEqual(self.adapter.call_count, 0)

    def test_fail_contract_hash_mismatch(self):
        mod_req = copy.deepcopy(self.request)
        mod_req.contract_hash = "wrong_hash"
        res = execute_manual_plan_review_reader(
            review_request=mod_req,
            contract=self.contract,
            approval_evidence=self.evidence,
            session_response=self.session_res,
            jules_adapter=self.adapter
        )
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason_code, "CONTRACT_HASH_MISMATCH")
        self.assertEqual(self.adapter.call_count, 0)

    def test_fail_plan_approval_not_required(self):
        mod_contract = copy.deepcopy(self.contract)
        mod_contract.plan_approval_required = False
        _, mod_hash = canonicalize_contract(mod_contract)
        mod_req = copy.deepcopy(self.request)
        mod_req.contract_hash = mod_hash
        mod_ev = copy.deepcopy(self.evidence)
        mod_ev.contract_hash = mod_hash

        res = execute_manual_plan_review_reader(
            review_request=mod_req,
            contract=mod_contract,
            approval_evidence=mod_ev,
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
            review_request=self.request,
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
            review_request=self.request,
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
            review_request=self.request,
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

        req = ManualReviewRequest("sess", "task", "app", "chash", "shash")
        self.assertNotIn("sess", repr(req))
        self.assertNotIn("sess", str(req))
        self.assertEqual(req.to_dict()["review_request"], "<REDACTED>")

if __name__ == '__main__':
    unittest.main()

from typing import Dict, Optional, Any
from orchestrator.jules_adapter import JulesHttpTransport, RealJulesAdapter, TransportError

class FakeJulesHttpTransportForPlan(JulesHttpTransport):
    def __init__(self):
        self.responses = {}
    def request(self, method: str, path: str, headers: Dict[str, str], body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        key = f"{method} {path}"
        if key in self.responses:
            return self.responses[key]
        return {}

class TestJulesAdapterFetchPlanTextOnly(unittest.TestCase):
    def setUp(self) -> None:
        self.transport = FakeJulesHttpTransportForPlan()
        self.adapter = RealJulesAdapter(api_key="test-key", transport=self.transport)

    def test_fetch_plan_text_only_success(self):
        """정상적인 문자열 plan 반환 케이스"""
        self.transport.responses = {
            "GET sessions/ses-1/activities": {
                "activities": [
                    {
                        "createTime": "2023-01-01T09:00:00Z",
                        "planGenerated": {"plan": "My Original Plan Text"}
                    }
                ]
            }
        }
        res = self.adapter.fetch_plan_text_only("sessions/ses-1")
        self.assertEqual(res, "My Original Plan Text")

    def test_fetch_plan_text_only_dict_type_rejected(self):
        """plan 값이 dict 타입인 경우 거부 (None 반환)"""
        self.transport.responses = {
            "GET sessions/ses-1/activities": {
                "activities": [
                    {
                        "createTime": "2023-01-01T09:00:00Z",
                        "planGenerated": {"plan": {"title": "dict plan"}}
                    }
                ]
            }
        }
        res = self.adapter.fetch_plan_text_only("sessions/ses-1")
        self.assertIsNone(res)

    def test_fetch_plan_text_only_key_missing(self):
        """plan 키가 없는 경우 거부"""
        self.transport.responses = {
            "GET sessions/ses-1/activities": {
                "activities": [
                    {
                        "createTime": "2023-01-01T09:00:00Z",
                        "planGenerated": {"content": "wrong key"}
                    }
                ]
            }
        }
        res = self.adapter.fetch_plan_text_only("sessions/ses-1")
        self.assertIsNone(res)

    def test_fetch_plan_text_only_time_conflict(self):
        """시간 중복으로 정렬 신뢰 불가 시 거부"""
        self.transport.responses = {
            "GET sessions/ses-1/activities": {
                "activities": [
                    {
                        "createTime": "2023-01-01T09:00:00Z",
                        "planGenerated": {"plan": "plan 1"}
                    },
                    {
                        "createTime": "2023-01-01T09:00:00Z",
                        "planGenerated": {"plan": "plan 2"}
                    }
                ]
            }
        }
        res = self.adapter.fetch_plan_text_only("sessions/ses-1")
        self.assertIsNone(res)

    def test_fetch_plan_text_only_transport_error(self):
        """API 응답 실패 시 거부"""
        def error_req(*args, **kwargs):
            raise TransportError("API Error")
        self.transport.request = error_req
        res = self.adapter.fetch_plan_text_only("sessions/ses-1")
        self.assertIsNone(res)
