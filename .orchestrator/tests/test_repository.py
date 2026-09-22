"""StateRepository 단위 테스트."""

import os
import tempfile
import unittest
from pathlib import Path
from orchestrator.models import (
    TaskRecord,
    ApprovalEvidence,
    ApprovalHistoryItem,
    ExecutionRecord,
    StateTransition,
    ScopeValidationRecord,
    PersistentSessionBinding,
)
from orchestrator.repository import (
    StateRepository,
    RepositoryError,
    RepositoryBindingConflictError,
)


class TestStateRepository(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "orchestrator_state.db"
        self.repo = StateRepository(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_init_and_schema_creation(self):
        """임시 경로 기반 저장소 초기화 및 테이블 생성 검증."""
        self.assertTrue(self.db_path.exists())
        repo2 = StateRepository(self.db_path)
        self.assertIsNotNone(repo2)

    def test_task_save_and_get(self):
        """TaskRecord 저장, 조회 및 상태 업데이트 검증."""
        task = TaskRecord(
            task_id="TASK-TEST-001",
            base_commit_sha="09774a68f4668aa5f75c3fd513591c3333e6c940",
            contract_hash="hash_contract_123",
            approved_scope_hash="hash_scope_123",
            idempotency_key="idem-v1:test_key",
            status="DRAFT",
            created_at_utc="2026-09-17T10:00:00Z",
            updated_at_utc="2026-09-17T10:00:00Z",
        )
        self.repo.save_task(task)

        retrieved = self.repo.get_task("TASK-TEST-001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.task_id, "TASK-TEST-001")
        self.assertEqual(retrieved.status, "DRAFT")

        updated_task = TaskRecord(
            task_id="TASK-TEST-001",
            base_commit_sha="09774a68f4668aa5f75c3fd513591c3333e6c940",
            contract_hash="hash_contract_123",
            approved_scope_hash="hash_scope_123",
            idempotency_key="idem-v1:test_key",
            status="APPROVED",
            created_at_utc="2026-09-17T10:00:00Z",
            updated_at_utc="2026-09-17T10:05:00Z",
        )
        self.repo.save_task(updated_task)
        retrieved_updated = self.repo.get_task("TASK-TEST-001")
        self.assertEqual(retrieved_updated.status, "APPROVED")

    def test_task_binding_conflict_error(self):
        """Task 결속 정보 변경 시 RepositoryBindingConflictError 발생 검증."""
        task = TaskRecord(
            task_id="TASK-TEST-001",
            base_commit_sha="09774a68f4668aa5f75c3fd513591c3333e6c940",
            contract_hash="hash_contract_123",
            approved_scope_hash="hash_scope_123",
            idempotency_key="idem-v1:test_key",
            status="DRAFT",
            created_at_utc="2026-09-17T10:00:00Z",
            updated_at_utc="2026-09-17T10:00:00Z",
        )
        self.repo.save_task(task)

        conflict_task = TaskRecord(
            task_id="TASK-TEST-001",
            base_commit_sha="09774a68f4668aa5f75c3fd513591c3333e6c940",
            contract_hash="hash_contract_DIFFERENT",
            approved_scope_hash="hash_scope_123",
            idempotency_key="idem-v1:test_key",
            status="APPROVED",
            created_at_utc="2026-09-17T10:00:00Z",
            updated_at_utc="2026-09-17T10:05:00Z",
        )
        with self.assertRaises(RepositoryBindingConflictError):
            self.repo.save_task(conflict_task)

    def test_approval_evidence_immutability(self):
        """ApprovalEvidence 불변성 및 동일 객체 멱등 저장 검증."""
        evidence = ApprovalEvidence(
            approval_id="APV-TASK-TEST-001-20260917-001",
            task_id="TASK-TEST-001",
            contract_version="v0.1",
            contract_hash="hash_contract_123",
            approved_scope_hash="hash_scope_123",
            approver="user_reviewer",
            approval_time_utc="2026-09-17T10:00:00Z",
            status="ACTIVE",
        )
        self.repo.save_approval_evidence(evidence)

        # 동일 증적 재저장 시 성공 (멱등)
        self.repo.save_approval_evidence(evidence)

        # 필드(예: status) 변경 시 거부
        modified_evidence = ApprovalEvidence(
            approval_id="APV-TASK-TEST-001-20260917-001",
            task_id="TASK-TEST-001",
            contract_version="v0.1",
            contract_hash="hash_contract_123",
            approved_scope_hash="hash_scope_123",
            approver="user_reviewer",
            approval_time_utc="2026-09-17T10:00:00Z",
            status="WITHDRAWN",
        )
        with self.assertRaises(RepositoryBindingConflictError):
            self.repo.save_approval_evidence(modified_evidence)

    def test_approval_history_append_only_and_ordering(self):
        """ApprovalHistoryItem append-only 보존 및 시간순 조회 검증."""
        item1 = ApprovalHistoryItem(
            approval_id="APV-TASK-TEST-001-20260917-001",
            task_id="TASK-TEST-001",
            contract_hash="hash_contract_123",
            approved_scope_hash="hash_scope_123",
            status="ACTIVE",
            recorded_at_utc="2026-09-17T10:00:00Z",
        )
        item2 = ApprovalHistoryItem(
            approval_id="APV-TASK-TEST-001-20260917-001",
            task_id="TASK-TEST-001",
            contract_hash="hash_contract_123",
            approved_scope_hash="hash_scope_123",
            status="WITHDRAWN",
            recorded_at_utc="2026-09-17T11:00:00Z",
        )

        self.repo.save_approval_history_item(item1)
        self.repo.save_approval_history_item(item2)

        history = self.repo.get_approval_history("TASK-TEST-001")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].status, "ACTIVE")
        self.assertEqual(history[0].recorded_at_utc, "2026-09-17T10:00:00Z")
        self.assertEqual(history[1].status, "WITHDRAWN")
        self.assertEqual(history[1].recorded_at_utc, "2026-09-17T11:00:00Z")

    def test_approval_history_idempotency_and_conflict(self):
        """완전 동일 이력 멱등 처리 및 동일 시각 상충 이력 거부 검증."""
        item = ApprovalHistoryItem(
            approval_id="APV-TASK-TEST-001-20260917-001",
            task_id="TASK-TEST-001",
            contract_hash="hash_contract_123",
            approved_scope_hash="hash_scope_123",
            status="ACTIVE",
            recorded_at_utc="2026-09-17T10:00:00Z",
        )
        self.repo.save_approval_history_item(item)
        # 완전 동일 레코드 재저장 (멱등 무시)
        self.repo.save_approval_history_item(item)

        history = self.repo.get_approval_history("TASK-TEST-001")
        self.assertEqual(len(history), 1)

        # 동일 시각 상충 상태 이력 저장 시 거부
        conflicting_item = ApprovalHistoryItem(
            approval_id="APV-TASK-TEST-001-20260917-001",
            task_id="TASK-TEST-001",
            contract_hash="hash_contract_123",
            approved_scope_hash="hash_scope_123",
            status="WITHDRAWN",
            recorded_at_utc="2026-09-17T10:00:00Z",
        )
        with self.assertRaises(RepositoryBindingConflictError):
            self.repo.save_approval_history_item(conflicting_item)

    def test_reason_code_validation(self):
        """자유 텍스트, 제어문자, 공백, 과도한 길이에 대한 사유 코드 거부 검증."""
        valid_transition = StateTransition(
            transition_id="TRANS-001",
            task_id="TASK-TEST-001",
            from_status="DRAFT",
            to_status="APPROVED",
            transition_agent="user_approver",
            recorded_at_utc="2026-09-17T10:00:00Z",
            reason="USER_APPROVED",
        )
        self.repo.save_state_transition(valid_transition)

        # 1. 자유 텍스트 (소문자 포함) 거부
        bad_reason1 = StateTransition(
            transition_id="TRANS-002",
            task_id="TASK-TEST-001",
            from_status="DRAFT",
            to_status="APPROVED",
            transition_agent="user_approver",
            recorded_at_utc="2026-09-17T10:01:00Z",
            reason="User approved manually",
        )
        with self.assertRaises(RepositoryError):
            self.repo.save_state_transition(bad_reason1)

        # 2. 제어문자 포함 거부
        bad_reason2 = StateTransition(
            transition_id="TRANS-003",
            task_id="TASK-TEST-001",
            from_status="DRAFT",
            to_status="APPROVED",
            transition_agent="user_approver",
            recorded_at_utc="2026-09-17T10:02:00Z",
            reason="USER_APPROVED\n",
        )
        with self.assertRaises(RepositoryError):
            self.repo.save_state_transition(bad_reason2)

        # 3. 과도한 길이 (64자 초과) 거부
        bad_reason3 = StateTransition(
            transition_id="TRANS-004",
            task_id="TASK-TEST-001",
            from_status="DRAFT",
            to_status="APPROVED",
            transition_agent="user_approver",
            recorded_at_utc="2026-09-17T10:03:00Z",
            reason="A" * 65,
        )
        with self.assertRaises(RepositoryError):
            self.repo.save_state_transition(bad_reason3)

        # ScopeValidationRecord 사유 검증
        valid_scope_val = ScopeValidationRecord(
            validation_id="VAL-001",
            task_id="TASK-TEST-001",
            contract_hash="hash_contract_123",
            approved_scope_hash="hash_scope_123",
            is_valid=False,
            status="NEEDS_HUMAN_REVIEW",
            checked_at_utc="2026-09-17T10:00:00Z",
            reasons=["SCOPE_LOCK_FAILED", "BINDING_CONFLICT"],
        )
        self.repo.save_scope_validation(valid_scope_val)

        bad_scope_val = ScopeValidationRecord(
            validation_id="VAL-002",
            task_id="TASK-TEST-001",
            contract_hash="hash_contract_123",
            approved_scope_hash="hash_scope_123",
            is_valid=False,
            status="NEEDS_HUMAN_REVIEW",
            checked_at_utc="2026-09-17T10:01:00Z",
            reasons=["Scope lock failed due to mismatch"],
        )
        with self.assertRaises(RepositoryError):
            self.repo.save_scope_validation(bad_scope_val)

    def test_execution_record(self):
        """ExecutionRecord 저장 및 조회 검증."""
        execution = ExecutionRecord(
            execution_id="EXEC-001",
            task_id="TASK-TEST-001",
            execution_agent="jules",
            status="RUNNING",
            started_at_utc="2026-09-17T10:10:00Z",
        )
        self.repo.save_execution(execution)

        executions = self.repo.get_executions("TASK-TEST-001")
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0].status, "RUNNING")
        self.assertIsNone(executions[0].ended_at_utc)

        updated_exec = ExecutionRecord(
            execution_id="EXEC-001",
            task_id="TASK-TEST-001",
            execution_agent="jules",
            status="COMPLETED",
            started_at_utc="2026-09-17T10:10:00Z",
            ended_at_utc="2026-09-17T10:15:00Z",
        )
        self.repo.save_execution(updated_exec)
        executions_updated = self.repo.get_executions("TASK-TEST-001")
        self.assertEqual(executions_updated[0].status, "COMPLETED")
        self.assertEqual(executions_updated[0].ended_at_utc, "2026-09-17T10:15:00Z")

    def test_invalid_timestamps_rejected(self):
        """유효하지 않은 UTC ISO 8601 타임스탬프 거부 검증."""
        task = TaskRecord(
            task_id="TASK-TEST-BAD-TIME",
            base_commit_sha="09774a68f4668aa5f75c3fd513591c3333e6c940",
            contract_hash="hash_contract_123",
            approved_scope_hash="hash_scope_123",
            idempotency_key="idem-v1:test_key",
            status="DRAFT",
            created_at_utc="INVALID_TIMESTAMP",
            updated_at_utc="2026-09-17T10:00:00Z",
        )
        with self.assertRaises(RepositoryError):
            self.repo.save_task(task)

    def test_persistent_session_binding_save_and_get(self):
        """PersistentSessionBinding 정상 저장 및 조회 검증."""
        binding = PersistentSessionBinding(
            task_id="TASK-TEST-001",
            session_id="sess_12345",
            branch_name="jules-sess_12345",
            pr_number=10,
            contract_hash="hash_contract_123",
            approved_scope_hash="hash_scope_123",
            recorded_at_utc="2026-09-17T10:00:00Z"
        )
        self.repo.save_persistent_session_binding(binding)

        retrieved = self.repo.get_persistent_session_binding("sess_12345")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.task_id, "TASK-TEST-001")
        self.assertEqual(retrieved.branch_name, "jules-sess_12345")
        self.assertEqual(retrieved.pr_number, 10)

        # 멱등성 검증 (동일 데이터 재입력 시 무시)
        self.repo.save_persistent_session_binding(binding)

    def test_persistent_session_binding_conflicts(self):
        """PersistentSessionBinding 상충(중복) 시 예외 발생 검증."""
        binding1 = PersistentSessionBinding(
            task_id="TASK-TEST-001",
            session_id="sess_12345",
            branch_name="jules-sess_12345",
            pr_number=10,
            contract_hash="hash_contract_123",
            approved_scope_hash="hash_scope_123",
            recorded_at_utc="2026-09-17T10:00:00Z"
        )
        self.repo.save_persistent_session_binding(binding1)

        # 1. 동일 세션이지만 결속 정보 다름
        binding2_conflict = PersistentSessionBinding(
            task_id="TASK-TEST-002",
            session_id="sess_12345",
            branch_name="jules-sess_12345",
            pr_number=10,
            contract_hash="hash_contract_123",
            approved_scope_hash="hash_scope_123",
            recorded_at_utc="2026-09-17T10:05:00Z"
        )
        with self.assertRaises(RepositoryBindingConflictError):
            self.repo.save_persistent_session_binding(binding2_conflict)

        # 2. 다른 세션이지만 브랜치명 중복
        binding3_branch_conflict = PersistentSessionBinding(
            task_id="TASK-TEST-001",
            session_id="sess_67890",
            branch_name="jules-sess_12345",
            pr_number=11,
            contract_hash="hash_contract_123",
            approved_scope_hash="hash_scope_123",
            recorded_at_utc="2026-09-17T10:10:00Z"
        )
        with self.assertRaises(RepositoryBindingConflictError):
            self.repo.save_persistent_session_binding(binding3_branch_conflict)

        # 3. 다른 세션이지만 PR 번호 중복
        binding4_pr_conflict = PersistentSessionBinding(
            task_id="TASK-TEST-001",
            session_id="sess_abcde",
            branch_name="jules-sess_abcde",
            pr_number=10,
            contract_hash="hash_contract_123",
            approved_scope_hash="hash_scope_123",
            recorded_at_utc="2026-09-17T10:15:00Z"
        )
        with self.assertRaises(RepositoryBindingConflictError):
            self.repo.save_persistent_session_binding(binding4_pr_conflict)

    def test_orchestrator_state_dir_env_not_accessed(self):
        """실제 ORCHESTRATOR_STATE_DIR 환경변수를 접근하지 않는지 검증."""
        old_env = os.environ.get("ORCHESTRATOR_STATE_DIR")
        try:
            os.environ["ORCHESTRATOR_STATE_DIR"] = "/nonexistent/path/that/should/not/be/used"
            local_db = Path(self.temp_dir.name) / "local_test.db"
            repo = StateRepository(local_db)
            self.assertTrue(local_db.exists())
            self.assertFalse(Path("/nonexistent/path/that/should/not/be/used").exists())
        finally:
            if old_env is None:
                os.environ.pop("ORCHESTRATOR_STATE_DIR", None)
            else:
                os.environ["ORCHESTRATOR_STATE_DIR"] = old_env


if __name__ == "__main__":
    unittest.main()
