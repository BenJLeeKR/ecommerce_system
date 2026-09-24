"""Plan 단계 비민감 세션 등록 경계 단위 테스트."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from orchestrator.canonicalization import canonicalize_contract, canonicalize_scope
from orchestrator.jules_adapter import JulesSessionResponse
from orchestrator.models import ApprovalEvidence, PathItem, TaskContract, TaskRecord
from orchestrator.plan_session_registration import (
    get_plan_session_registration,
    register_plan_session,
)
from orchestrator.repository import StateRepository


class TestPlanSessionRegistration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = StateRepository(Path(self.temp_dir.name) / "state.db")
        self.contract = TaskContract(
            task_id="ORCHESTRATOR-PLAN-SESSION-REGISTRATION-FOUNDATION-001",
            contract_version="v1",
            project_profile_id="profile",
            project_profile_version="v1",
            project_profile_reference_path="docs/01_governance/roles.md",
            goal="비민감 Plan 세션 등록",
            target_repository="repo",
            base_branch="main",
            base_commit_sha="5d11a46f23d9a48005be1135c66c877f08628e2b",
            execution_agent="Codex",
            reference_documents=[],
            allowed_paths=[PathItem(path=".orchestrator/src/orchestrator/models.py", kind="file")],
            forbidden_paths=[PathItem(path=".env", kind="file")],
            risk_level="HIGH",
            completion_conditions=[],
            idempotency_key="plan-session-registration-v1",
            plan_approval_required=True,
            cancellation_conditions=[],
            auto_merge=False,
        )
        _, self.contract_hash = canonicalize_contract(self.contract)
        _, self.scope_hash = canonicalize_scope(
            self.contract.allowed_paths, self.contract.forbidden_paths
        )
        self.evidence = ApprovalEvidence(
            approval_id="APV-PLAN-REG-001",
            task_id=self.contract.task_id,
            contract_version=self.contract.contract_version,
            contract_hash=self.contract_hash,
            approved_scope_hash=self.scope_hash,
            approver="user",
            approval_time_utc="2026-09-24T00:00:00Z",
            status="ACTIVE",
        )
        self.repo.save_task(TaskRecord(
            task_id=self.contract.task_id,
            base_commit_sha=self.contract.base_commit_sha,
            contract_hash=self.contract_hash,
            approved_scope_hash=self.scope_hash,
            idempotency_key=self.contract.idempotency_key,
            status="APPROVED",
            created_at_utc="2026-09-24T00:00:00Z",
            updated_at_utc="2026-09-24T00:00:00Z",
        ))
        self.repo.save_approval_evidence(self.evidence)
        self.response = JulesSessionResponse(
            session_id="sessions/plan-registration-001",
            task_id=self.contract.task_id,
            branch_name=None,
            pr_number=None,
            status="CREATED",
            reason_code=None,
            created_at_utc="2026-09-24T00:00:00Z",
            updated_at_utc="2026-09-24T00:00:00Z",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_register_and_query_success_with_masking(self):
        result = register_plan_session(
            repository=self.repo,
            contract=self.contract,
            approval_evidence=self.evidence,
            session_response=self.response,
            registered_at_utc="2026-09-24T00:00:01Z",
        )
        self.assertEqual(result.status, "REGISTERED")
        self.assertEqual(result.registration.session_id, self.response.session_id)
        self.assertNotIn(self.response.session_id, repr(result))
        self.assertNotIn(self.response.session_id, str(result.to_dict()))

        queried = get_plan_session_registration(
            repository=self.repo, task_id=self.contract.task_id
        )
        self.assertEqual(queried.status, "REGISTERED")
        self.assertEqual(queried.registration.session_id, self.response.session_id)

    def test_prevalidation_failure_performs_no_registration_write(self):
        self.evidence.status = "WITHDRAWN"
        with patch.object(self.repo, "save_plan_session_registration") as save:
            result = register_plan_session(
                repository=self.repo,
                contract=self.contract,
                approval_evidence=self.evidence,
                session_response=self.response,
            )
        self.assertEqual(result.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(result.reason_code, "APPROVAL_NOT_ACTIVE")
        save.assert_not_called()

    def test_hash_mismatch_and_session_outputs_are_blocked(self):
        self.evidence.contract_hash = "different"
        with patch.object(self.repo, "save_plan_session_registration") as save:
            mismatch = register_plan_session(
                repository=self.repo,
                contract=self.contract,
                approval_evidence=self.evidence,
                session_response=self.response,
            )
        self.assertEqual(mismatch.reason_code, "CONTRACT_HASH_MISMATCH")
        save.assert_not_called()

        self.evidence.contract_hash = self.contract_hash
        self.response.branch_name = "unexpected-branch"
        with patch.object(self.repo, "save_plan_session_registration") as save:
            outputs = register_plan_session(
                repository=self.repo,
                contract=self.contract,
                approval_evidence=self.evidence,
                session_response=self.response,
            )
        self.assertEqual(outputs.reason_code, "PLAN_SESSION_OUTPUTS_NOT_ALLOWED")
        save.assert_not_called()

    def test_duplicate_and_unregistered_inputs_are_safely_handled(self):
        first = register_plan_session(
            repository=self.repo,
            contract=self.contract,
            approval_evidence=self.evidence,
            session_response=self.response,
            registered_at_utc="2026-09-24T00:00:01Z",
        )
        self.assertEqual(first.status, "REGISTERED")

        conflicting_response = JulesSessionResponse(
            session_id="sessions/another",
            task_id=self.contract.task_id,
            branch_name=None,
            pr_number=None,
            status="CREATED",
            reason_code=None,
            created_at_utc="2026-09-24T00:00:00Z",
            updated_at_utc="2026-09-24T00:00:00Z",
        )
        conflict = register_plan_session(
            repository=self.repo,
            contract=self.contract,
            approval_evidence=self.evidence,
            session_response=conflicting_response,
            registered_at_utc="2026-09-24T00:00:02Z",
        )
        self.assertEqual(conflict.reason_code, "PLAN_SESSION_REGISTRATION_CONFLICT")

        missing = get_plan_session_registration(repository=self.repo, task_id="UNKNOWN")
        self.assertEqual(missing.reason_code, "PLAN_SESSION_NOT_REGISTERED")


    def test_stored_task_and_evidence_mismatches_perform_no_registration_write(self):
        isolated = StateRepository(Path(self.temp_dir.name) / "isolated.db")
        isolated.save_task(TaskRecord(
            task_id=self.contract.task_id,
            base_commit_sha="different-base-sha",
            contract_hash=self.contract_hash,
            approved_scope_hash=self.scope_hash,
            idempotency_key=self.contract.idempotency_key,
            status="APPROVED",
            created_at_utc="2026-09-24T00:00:00Z",
            updated_at_utc="2026-09-24T00:00:00Z",
        ))
        isolated.save_approval_evidence(self.evidence)
        with patch.object(isolated, "save_plan_session_registration") as save:
            task_mismatch = register_plan_session(
                repository=isolated,
                contract=self.contract,
                approval_evidence=self.evidence,
                session_response=self.response,
            )
        self.assertEqual(task_mismatch.reason_code, "TASK_RECORD_MISMATCH")
        save.assert_not_called()

        evidence_repo = StateRepository(Path(self.temp_dir.name) / "evidence.db")
        evidence_repo.save_task(TaskRecord(
            task_id=self.contract.task_id,
            base_commit_sha=self.contract.base_commit_sha,
            contract_hash=self.contract_hash,
            approved_scope_hash=self.scope_hash,
            idempotency_key=self.contract.idempotency_key,
            status="APPROVED",
            created_at_utc="2026-09-24T00:00:00Z",
            updated_at_utc="2026-09-24T00:00:00Z",
        ))
        stored_evidence = ApprovalEvidence(
            approval_id=self.evidence.approval_id,
            task_id=self.evidence.task_id,
            contract_version=self.evidence.contract_version,
            contract_hash=self.evidence.contract_hash,
            approved_scope_hash=self.evidence.approved_scope_hash,
            approver="different-user",
            approval_time_utc=self.evidence.approval_time_utc,
            status=self.evidence.status,
        )
        evidence_repo.save_approval_evidence(stored_evidence)
        with patch.object(evidence_repo, "save_plan_session_registration") as save:
            evidence_mismatch = register_plan_session(
                repository=evidence_repo,
                contract=self.contract,
                approval_evidence=self.evidence,
                session_response=self.response,
            )
        self.assertEqual(evidence_mismatch.reason_code, "APPROVAL_EVIDENCE_MISMATCH")
        save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
