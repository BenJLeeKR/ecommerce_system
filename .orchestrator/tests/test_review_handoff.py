"""Orchestrator Review Handoff Module Tests."""

import unittest
from typing import List, Dict, Any, Optional

from orchestrator.models import (
    PathItem,
    ExecutionResultInput,
    CodexReviewResultPackage,
    StateTransition,
    ScopeValidationResult,
)
from orchestrator.jules_adapter import JulesSessionResponse, ActivitySummary, TransportError
from orchestrator.review_handoff import (
    CodexNotificationAdapter,
    execute_review_handoff,
)


class MockCodexAdapter(CodexNotificationAdapter):
    def __init__(self):
        self.notified_packages: List[CodexReviewResultPackage] = []

    def notify_review_ready(self, result_package: CodexReviewResultPackage) -> None:
        self.notified_packages.append(result_package)


class MockJulesAdapter:
    def __init__(self, session_status: JulesSessionResponse, activity_summary: ActivitySummary, throw_error: bool = False):
        self.session_status = session_status
        self.activity_summary = activity_summary
        self.throw_error = throw_error

    def get_session_status(self, session_id: str) -> JulesSessionResponse:
        if self.throw_error:
            raise TransportError("MOCK_TRANSPORT_ERROR")
        if session_id != self.session_status.session_id:
            return JulesSessionResponse(
                session_id=session_id,
                task_id="",
                branch_name="",
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="SESSION_NOT_FOUND",
                created_at_utc="2026-09-17T00:00:00Z",
                updated_at_utc="2026-09-17T00:00:00Z",
            )
        return self.session_status

    def get_activities(self, session_resource_name: str) -> ActivitySummary:
        if self.throw_error:
            raise TransportError("MOCK_TRANSPORT_ERROR")
        return self.activity_summary


class TestReviewHandoff(unittest.TestCase):
    def setUp(self) -> None:
        self.task_id = "TASK-001"
        self.session_id = "sessions/123"
        self.branch_name = "jules/TASK-001"
        self.pr_identifier = "https://github.com/owner/repo/pull/42"
        self.contract_hash = "fakecontracthash"
        self.approved_scope_hash = "fakescopehash"
        self.idempotency_key = "fake-idem-key"
        self.approval_id = "APV-TASK-001-20260918-001"
        self.transition_agent = "orchestrator"

        self.allowed_paths = [PathItem(path="src/", kind="directory_recursive")]
        self.forbidden_paths = [PathItem(path="docs/", kind="directory_recursive")]

        # _validate_single_changed_path_format() 검증 통과를 위해,
        # 정규화된 Scope Lock 결과와 동일한 해시를 만드는 것은 실제 canonicalize 함수를 통하므로
        # TestReviewHandoff에서는 validator의 canonicalize_scope 로직에 맞도록
        # 미리 기대 해시를 세팅해두거나 테스트 내에서 재계산하도록 할 수 있지만,
        # 단위 테스트의 격리를 위해 validation 로직은 result_package 및 validator에 의존합니다.
        # 여기서는 올바른 해시를 얻기 위해 직접 canonicalize_scope를 호출하여 세팅합니다.
        from orchestrator.canonicalization import canonicalize_scope
        _, computed_scope_hash = canonicalize_scope(self.allowed_paths, self.forbidden_paths)
        self.approved_scope_hash = computed_scope_hash

        self.valid_session = JulesSessionResponse(
            session_id=self.session_id,
            task_id=self.task_id,
            branch_name=self.branch_name,
            pr_number=42,
            status="COMPLETED",
            reason_code=None,
            created_at_utc="2026-09-17T00:00:00Z",
            updated_at_utc="2026-09-17T01:00:00Z",
        )

        self.completed_activities = ActivitySummary(
            total_count=3,
            activity_types=["AGENT_MESSAGED", "PLAN_GENERATED", "SESSION_COMPLETED"],
            is_completed=True,
            is_failed=False,
        )

        self.codex_adapter = MockCodexAdapter()

    def test_successful_review_handoff(self):
        jules_adapter = MockJulesAdapter(self.valid_session, self.completed_activities)

        changed_files = ["src/main.py", "src/utils.py"]

        transition = execute_review_handoff(
            task_id=self.task_id,
            session_id=self.session_id,
            branch_name=self.branch_name,
            pr_identifier=self.pr_identifier,
            changed_files=changed_files,
            allowed_paths=self.allowed_paths,
            forbidden_paths=self.forbidden_paths,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
            transition_agent=self.transition_agent,
            jules_adapter=jules_adapter,
            codex_adapter=self.codex_adapter,
            verified_session=self.valid_session,
        )

        self.assertEqual(transition.to_status, "REVIEW_READY_DETECTED")
        self.assertEqual(len(self.codex_adapter.notified_packages), 1)

        pkg = self.codex_adapter.notified_packages[0]
        self.assertEqual(pkg.status, "RESULT_COLLECTED")
        self.assertEqual(pkg.session_id, self.session_id)

        # 권한 관련 속성 부재 확인
        self.assertFalse(hasattr(pkg, "is_mergeable"))
        self.assertFalse(hasattr(pkg, "raw_logs"))

    def test_session_not_completed(self):
        running_activities = ActivitySummary(
            total_count=2,
            activity_types=["AGENT_MESSAGED", "PLAN_GENERATED"],
            is_completed=False,
            is_failed=False,
        )
        jules_adapter = MockJulesAdapter(self.valid_session, running_activities)
        changed_files = ["src/main.py"]

        transition = execute_review_handoff(
            task_id=self.task_id,
            session_id=self.session_id,
            branch_name=self.branch_name,
            pr_identifier=self.pr_identifier,
            changed_files=changed_files,
            allowed_paths=self.allowed_paths,
            forbidden_paths=self.forbidden_paths,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
            transition_agent=self.transition_agent,
            jules_adapter=jules_adapter,
            codex_adapter=self.codex_adapter,
            verified_session=self.valid_session,
        )

        self.assertEqual(transition.to_status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(transition.reason, "SESSION_NOT_COMPLETED")
        self.assertEqual(len(self.codex_adapter.notified_packages), 0)

    def test_scope_validation_failure(self):
        jules_adapter = MockJulesAdapter(self.valid_session, self.completed_activities)
        # 금지 경로인 docs/ 수정 시도
        changed_files = ["src/main.py", "docs/readme.md"]

        transition = execute_review_handoff(
            task_id=self.task_id,
            session_id=self.session_id,
            branch_name=self.branch_name,
            pr_identifier=self.pr_identifier,
            changed_files=changed_files,
            allowed_paths=self.allowed_paths,
            forbidden_paths=self.forbidden_paths,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
            transition_agent=self.transition_agent,
            jules_adapter=jules_adapter,
            codex_adapter=self.codex_adapter,
            verified_session=self.valid_session,
        )

        self.assertEqual(transition.to_status, "NEEDS_HUMAN_REVIEW")
        self.assertIn("SCOPE_VALIDATION_FAILED", transition.reason)
        self.assertEqual(len(self.codex_adapter.notified_packages), 0)

    def test_binding_mismatch(self):
        # jules 세션은 task-001인데, 인계 요청은 task-002
        jules_adapter = MockJulesAdapter(self.valid_session, self.completed_activities)
        changed_files = ["src/main.py"]

        transition = execute_review_handoff(
            task_id="TASK-002",
            session_id=self.session_id,
            branch_name=self.branch_name,
            pr_identifier=self.pr_identifier,
            changed_files=changed_files,
            allowed_paths=self.allowed_paths,
            forbidden_paths=self.forbidden_paths,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
            transition_agent=self.transition_agent,
            jules_adapter=jules_adapter,
            codex_adapter=self.codex_adapter,
            verified_session=self.valid_session,
        )

        self.assertEqual(transition.to_status, "NEEDS_HUMAN_REVIEW")
        self.assertIn("SESSION_BINDING_MISMATCH", transition.reason)
        self.assertEqual(len(self.codex_adapter.notified_packages), 0)

    def test_transport_error(self):
        jules_adapter = MockJulesAdapter(self.valid_session, self.completed_activities, throw_error=True)
        changed_files = ["src/main.py"]

        transition = execute_review_handoff(
            task_id=self.task_id,
            session_id=self.session_id,
            branch_name=self.branch_name,
            pr_identifier=self.pr_identifier,
            changed_files=changed_files,
            allowed_paths=self.allowed_paths,
            forbidden_paths=self.forbidden_paths,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
            transition_agent=self.transition_agent,
            jules_adapter=jules_adapter,
            codex_adapter=self.codex_adapter,
            verified_session=self.valid_session,
        )

        self.assertEqual(transition.to_status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(transition.reason, "TRANSPORT_ERROR")
        self.assertEqual(len(self.codex_adapter.notified_packages), 0)



    def test_missing_verified_session(self):
        """verified_session이 None으로 주입된 경우 (세션 조회 불가 / 프로세스 메모리 부재)
        NEEDS_HUMAN_REVIEW로 전이되고 알림이 없는지 검증합니다.
        """
        jules_adapter = MockJulesAdapter(self.valid_session, self.completed_activities)
        changed_files = ["src/main.py"]

        # execute_review_handoff 호출 시 verified_session을 None으로 주입
        # test_review_handoff.py 패치로 인해 원래 인자가 수정되었으므로 주의해야 하나
        # 수동으로 호출을 새로 만듦.
        transition = execute_review_handoff(
            task_id=self.task_id,
            session_id=self.session_id,
            branch_name=self.branch_name,
            pr_identifier=self.pr_identifier,
            changed_files=changed_files,
            allowed_paths=self.allowed_paths,
            forbidden_paths=self.forbidden_paths,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
            transition_agent=self.transition_agent,
            jules_adapter=jules_adapter,
            codex_adapter=self.codex_adapter,
            verified_session=None,
        )

        self.assertEqual(transition.to_status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(transition.reason, "SESSION_NOT_FOUND")
        self.assertEqual(transition.from_status, "UNKNOWN")
        self.assertEqual(len(self.codex_adapter.notified_packages), 0)

    def test_pr_binding_missing(self):
        """existing_session.pr_number가 None일 때 PR_BINDING_MISSING 사유 코드로
        NEEDS_HUMAN_REVIEW가 되는지 검증합니다.
        """
        session_no_pr = JulesSessionResponse(
            session_id=self.session_id,
            task_id=self.task_id,
            branch_name=self.branch_name,
            pr_number=None,
            status="COMPLETED",
            reason_code=None,
            created_at_utc="2026-09-17T00:00:00Z",
            updated_at_utc="2026-09-17T01:00:00Z",
        )
        jules_adapter = MockJulesAdapter(session_no_pr, self.completed_activities)
        changed_files = ["src/main.py"]

        transition = execute_review_handoff(
            task_id=self.task_id,
            session_id=self.session_id,
            branch_name=self.branch_name,
            pr_identifier=self.pr_identifier,
            changed_files=changed_files,
            allowed_paths=self.allowed_paths,
            forbidden_paths=self.forbidden_paths,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
            transition_agent=self.transition_agent,
            jules_adapter=jules_adapter,
            codex_adapter=self.codex_adapter,
            verified_session=session_no_pr,
        )

        self.assertEqual(transition.to_status, "NEEDS_HUMAN_REVIEW")
        self.assertIn("PR_BINDING_MISSING", transition.reason)
        self.assertEqual(len(self.codex_adapter.notified_packages), 0)

    def test_pr_binding_mismatch(self):
        """PR 식별자 불일치 시 PR_BINDING_MISMATCH 사유 코드로
        NEEDS_HUMAN_REVIEW가 되는지 검증합니다.
        """
        # 세션의 PR 번호는 42, 그러나 식별자는 pull/99
        jules_adapter = MockJulesAdapter(self.valid_session, self.completed_activities)
        changed_files = ["src/main.py"]

        transition = execute_review_handoff(
            task_id=self.task_id,
            session_id=self.session_id,
            branch_name=self.branch_name,
            pr_identifier="https://github.com/owner/repo/pull/99",
            changed_files=changed_files,
            allowed_paths=self.allowed_paths,
            forbidden_paths=self.forbidden_paths,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
            transition_agent=self.transition_agent,
            jules_adapter=jules_adapter,
            codex_adapter=self.codex_adapter,
            verified_session=self.valid_session,
        )

        self.assertEqual(transition.to_status, "NEEDS_HUMAN_REVIEW")
        self.assertIn("PR_BINDING_MISMATCH", transition.reason)
        self.assertEqual(len(self.codex_adapter.notified_packages), 0)

if __name__ == "__main__":
    unittest.main()
