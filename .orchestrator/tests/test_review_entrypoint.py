import unittest
from typing import List, Optional

from orchestrator.models import (
    PathItem,
    StateTransition,
    PersistentSessionBinding,
    CodexReviewResultPackage,
)
from orchestrator.jules_adapter import JulesSessionResponse, ActivitySummary
from orchestrator.repository import StateRepository, RepositoryBindingConflictError
from orchestrator.review_handoff import CodexNotificationAdapter
from orchestrator.review_entrypoint import execute_review_handoff_with_repository


class DummyStateRepository(StateRepository):
    def __init__(self, should_fail: bool = False, conflict: bool = False):
        self.should_fail = should_fail
        self.conflict = conflict
        self.saved_bindings: List[PersistentSessionBinding] = []

    def save_persistent_session_binding(self, binding: PersistentSessionBinding) -> None:
        if self.should_fail:
            raise Exception("Mocked save error")
        if self.conflict:
            raise RepositoryBindingConflictError("Mocked conflict error")
        self.saved_bindings.append(binding)

    def is_binding_valid(self, session_id: str, branch_name: str, pr_number: int) -> bool:
        return True


class DummyCodexAdapter(CodexNotificationAdapter):
    def __init__(self):
        self.notified_packages: List[CodexReviewResultPackage] = []

    def notify_review_ready(self, result_package: CodexReviewResultPackage) -> None:
        self.notified_packages.append(result_package)


class DummyJulesAdapter:
    def __init__(self, should_fail: bool = False, is_completed: bool = True):
        self.should_fail = should_fail
        self.is_completed = is_completed

    def get_activities(self, session_id: str) -> ActivitySummary:
        if self.should_fail:
            from orchestrator.jules_adapter import TransportError
            raise TransportError("Mocked transport error")
        return ActivitySummary(
            is_completed=self.is_completed,
            is_failed=not self.is_completed,
            total_count=1,
            activity_types=["test"]
        )


class TestReviewEntrypoint(unittest.TestCase):
    def setUp(self):
        self.valid_task_id = "TASK-001"
        self.valid_session_id = "SES-123"
        self.valid_branch = "feature/test"
        self.valid_pr = "https://github.com/owner/repo/pull/42"
        self.valid_changed_files = ["src/file.py"]
        self.valid_allowed_paths = [PathItem(path="src", kind="directory_recursive")]
        self.expected_hash = "8841f69261561ecbfe650e88ab325f802bc135f3ab0a0eabf7d589994f408380"
        self.valid_session = JulesSessionResponse(
            session_id=self.valid_session_id,
            status="COMPLETED",
            created_at_utc="2023-01-01T00:00:00Z",
            updated_at_utc="2023-01-01T00:00:00Z",
            task_id="TASK-001",
            branch_name="feature/test",
            pr_number=42,
            reason_code=""
        )


        self.codex_adapter = DummyCodexAdapter()
        self.jules_adapter = DummyJulesAdapter()

    def _call_entrypoint(
        self,
        repository: Optional[StateRepository] = None,
        factory=None,
        verified_session=None,
        jules_adapter=None,
    ) -> StateTransition:
        return execute_review_handoff_with_repository(
            task_id=self.valid_task_id,
            session_id=self.valid_session_id,
            branch_name=self.valid_branch,
            pr_identifier=self.valid_pr,
            changed_files=self.valid_changed_files,
            allowed_paths=self.valid_allowed_paths,
            forbidden_paths=[],
            expected_contract_hash=self.expected_hash,
            expected_approved_scope_hash=self.expected_hash,
            expected_idempotency_key="idemp_123",
            expected_approval_id="app_123",
            transition_agent="test_agent",
            jules_adapter=jules_adapter or self.jules_adapter,
            codex_adapter=self.codex_adapter,
            repository=repository,
            jules_state_repository_factory=factory,
            verified_session=verified_session or self.valid_session,
        )

    def test_successful_handoff_with_factory(self):
        """팩토리를 통해 저장소를 생성하고 정상 인계되는지 확인."""
        dummy_repo = DummyStateRepository()
        factory_called = False

        def dummy_factory():
            nonlocal factory_called
            factory_called = True
            return dummy_repo

        transition = self._call_entrypoint(factory=dummy_factory)

        self.assertTrue(factory_called)
        self.assertEqual(transition.to_status, "REVIEW_READY_DETECTED")
        self.assertEqual(len(dummy_repo.saved_bindings), 1)
        self.assertEqual(dummy_repo.saved_bindings[0].pr_number, 42)
        self.assertEqual(len(self.codex_adapter.notified_packages), 1)

    def test_direct_repository_priority(self):
        """직접 주입된 repository 인자가 팩토리보다 우선하는지 확인."""
        direct_repo = DummyStateRepository()
        factory_called = False

        def dummy_factory():
            nonlocal factory_called
            factory_called = True
            return DummyStateRepository()

        transition = self._call_entrypoint(repository=direct_repo, factory=dummy_factory)

        self.assertFalse(factory_called, "Factory should not be called if repository is provided directly")
        self.assertEqual(transition.to_status, "REVIEW_READY_DETECTED")
        self.assertEqual(len(direct_repo.saved_bindings), 1)

    def test_factory_error(self):
        """팩토리 호출 중 예외(예: RuntimeConfigError)가 발생하면 NEEDS_HUMAN_REVIEW로 전이되는지 확인."""
        def failing_factory():
            from orchestrator.runtime_config import RuntimeConfigError
            raise RuntimeConfigError("Mocked config error")

        transition = self._call_entrypoint(factory=failing_factory)

        self.assertEqual(transition.to_status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(transition.reason, "FACTORY_INIT_ERROR")

    def test_save_error(self):
        """저장소 저장 중 오류가 발생하면 NEEDS_HUMAN_REVIEW로 전이되는지 확인."""
        dummy_repo = DummyStateRepository(should_fail=True)
        transition = self._call_entrypoint(repository=dummy_repo)

        self.assertEqual(transition.to_status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(transition.reason, "BINDING_SAVE_ERROR")

    def test_unsuccessful_result_does_not_call_factory(self):
        """RESULT_COLLECTED가 아니면(예: Scope 에러) 팩토리가 호출되지 않고 지연됨을 확인."""
        factory_called = False

        def dummy_factory():
            nonlocal factory_called
            factory_called = True
            return DummyStateRepository()

        # 변경 파일이 허용 경로 밖인 경우 강제
        invalid_changed_files = ["outside/file.py"]

        transition = execute_review_handoff_with_repository(
            task_id=self.valid_task_id,
            session_id=self.valid_session_id,
            branch_name=self.valid_branch,
            pr_identifier=self.valid_pr,
            changed_files=invalid_changed_files,
            allowed_paths=self.valid_allowed_paths,
            forbidden_paths=[],
            expected_contract_hash=self.expected_hash,
            expected_approved_scope_hash=self.expected_hash,
            expected_idempotency_key="idemp_123",
            expected_approval_id="app_123",
            transition_agent="test_agent",
            jules_adapter=self.jules_adapter,
            codex_adapter=self.codex_adapter,
            jules_state_repository_factory=dummy_factory,
            verified_session=self.valid_session,
        )

        self.assertFalse(factory_called, "Factory should not be called if review handoff is not successful")
        self.assertEqual(transition.to_status, "NEEDS_HUMAN_REVIEW")

if __name__ == '__main__':
    unittest.main()
