import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

from orchestrator.models import TaskContract, ApprovalEvidence, PathItem, TaskRecord
from orchestrator.jules_adapter import JulesSessionResponse, JulesSessionRequest, RealJulesAdapter, JulesHttpTransport, PreGateResult
from orchestrator.dispatch_entrypoint import execute_dispatch_session
from orchestrator.canonicalization import canonicalize_contract, canonicalize_scope
from orchestrator.repository import StateRepository

class TestDispatchEntrypoint(unittest.TestCase):
    def setUp(self):
        # Fake HTTP Transport and Real Adapter
        self.mock_transport = Mock(spec=JulesHttpTransport)
        self.fake_api_key = "fake_key_123"

        # 고정 remote main SHA 반환 함수
        def fake_remote_main_sha():
            return "abcd123"

        # RealJulesAdapter를 사용하여 POST Body의 startingBranch, requirePlanApproval를 검증
        self.jules_adapter = RealJulesAdapter(
            api_key=self.fake_api_key,
            transport=self.mock_transport,
            remote_main_sha_fn=fake_remote_main_sha
        )

        # 성공 응답 모의 설정
        self.mock_transport.request.return_value = {
            "name": "sessions/sess-1",
            "workingBranchName": "main"
        }

        self.valid_paths = [PathItem(path="docs", kind="directory_recursive")]
        self.contract = TaskContract(
            task_id="TEST-001",
            contract_version="v1",
            project_profile_id="p1",
            project_profile_version="v1",
            project_profile_reference_path="path",
            goal="Test Goal",
            target_repository="repo",
            base_branch="main",
            base_commit_sha="abcd123",
            execution_agent="jules",
            reference_documents=[],
            allowed_paths=self.valid_paths,
            forbidden_paths=[],
            risk_level="LOW",
            completion_conditions=[],
            idempotency_key="idemp_key",
            plan_approval_required=True,
            cancellation_conditions=[],
            auto_merge=False
        )

        _, self.contract_hash = canonicalize_contract(self.contract)
        _, self.scope_hash = canonicalize_scope(self.contract.allowed_paths, self.contract.forbidden_paths)

        self.evidence = ApprovalEvidence(
            approval_id="appr-1",
            task_id="TEST-001",
            contract_version="v1",
            contract_hash=self.contract_hash,
            approved_scope_hash=self.scope_hash,
            approver="user",
            approval_time_utc="2026-09-23T12:00:00Z",
            status="ACTIVE"
        )

        self.source_name = "sources/github/owner/repo"
        self.actual_base_sha = "abcd123"

    def test_success_path_with_real_adapter(self):
        """정상 경로에서 RealJulesAdapter를 통해 POST 요청의 startingBranch, requirePlanApproval 필드 및 prompt 전달을 검증."""
        dummy_prompt = "Dummy prompt for testing"
        response = execute_dispatch_session(
            contract=self.contract,
            approval_evidence=self.evidence,
            source_name=self.source_name,
            prompt=dummy_prompt,
            is_session_creation_authorized=True,
            jules_adapter=self.jules_adapter,
            actual_base_sha=self.actual_base_sha
        )

        self.assertEqual(response.status, "CREATED")

        # 실제 네트워크 호출은 mock_transport에서 차단되었으므로 인자 검증
        self.mock_transport.request.assert_called_once()
        call_args = self.mock_transport.request.call_args[1]

        self.assertEqual(call_args["method"], "POST")
        self.assertEqual(call_args["path"], "sessions")

        body = call_args["body"]
        # 정책 강제 검증 (sourceContext 구조와 최상위 필드)
        source_context = body.get("sourceContext", {})
        github_context = source_context.get("githubRepoContext", {})
        self.assertEqual(github_context.get("startingBranch"), "main")
        self.assertEqual(source_context.get("source"), self.source_name)
        self.assertTrue(body.get("requirePlanApproval"))
        self.assertEqual(body.get("prompt"), dummy_prompt)

    def test_task_id_mismatch(self):
        """Task ID 불일치 시 API 호출 없이 중단."""
        self.evidence.task_id = "DIFF-TASK-ID"
        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, "dummy", True, self.jules_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "TASK_ID_MISMATCH")
        self.mock_transport.request.assert_not_called()

    def test_contract_version_mismatch(self):
        """Contract Version 불일치 시 API 호출 없이 중단."""
        self.evidence.contract_version = "v2"
        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, "dummy", True, self.jules_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "CONTRACT_VERSION_MISMATCH")
        self.mock_transport.request.assert_not_called()

    def test_not_authorized(self):
        """세션 생성 명시적 권한이 없는 경우 API 호출 없이 중단."""
        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, "dummy", False, self.jules_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "SESSION_CREATION_NOT_AUTHORIZED")
        self.mock_transport.request.assert_not_called()

    def test_invalid_source_name(self):
        """source_name 검증 실패 시 API 호출 없이 중단."""
        invalid_source_name = "invalid_name" # 'sources/' 로 시작하지 않음
        response = execute_dispatch_session(
            self.contract, self.evidence, invalid_source_name, "dummy", True, self.jules_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "INVALID_SOURCE_NAME")
        self.mock_transport.request.assert_not_called()

    def test_approval_not_active(self):
        """승인 상태가 ACTIVE가 아니면 하드 블록 중단."""
        self.evidence.status = "WITHDRAWN"
        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, "dummy", True, self.jules_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "APPROVAL_NOT_ACTIVE")
        self.assertTrue(response.created_at_utc) # UTC 시간 확인
        self.mock_transport.request.assert_not_called()

    def test_auto_merge_not_allowed(self):
        """auto_merge가 True이면 하드 블록 중단."""
        self.contract.auto_merge = True

        _, self.evidence.contract_hash = canonicalize_contract(self.contract) # 해시 불일치를 막기 위해 갱신

        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, "dummy", True, self.jules_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "AUTO_MERGE_NOT_ALLOWED")
        self.mock_transport.request.assert_not_called()

    def test_plan_approval_not_required(self):
        """plan_approval_required가 False이면 중단."""
        self.contract.plan_approval_required = False

        _, self.evidence.contract_hash = canonicalize_contract(self.contract) # 해시 불일치를 막기 위해 갱신

        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, "dummy", True, self.jules_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "PLAN_APPROVAL_REQUIRED")
        self.mock_transport.request.assert_not_called()

    def test_contract_hash_mismatch(self):
        """contract hash 불일치 시 중단."""
        self.evidence.contract_hash = "fake-hash"
        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, "dummy", True, self.jules_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "CONTRACT_HASH_MISMATCH")
        self.mock_transport.request.assert_not_called()

    def test_scope_hash_mismatch(self):
        """approved scope hash 불일치 시 중단."""
        self.evidence.approved_scope_hash = "fake-hash"
        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, "dummy", True, self.jules_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "SCOPE_HASH_MISMATCH")
        self.mock_transport.request.assert_not_called()

    def test_base_sha_mismatch(self):
        """기준 SHA 불일치 시 중단."""
        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, "dummy", True, self.jules_adapter, actual_base_sha="diff-sha"
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "BASE_SHA_MISMATCH")
        self.mock_transport.request.assert_not_called()

    def test_invalid_canonicalization(self):
        """정규화 과정에서의 타입/형식 오류 발생 시 예외 없이 NEEDS_HUMAN_REVIEW 처리"""
        # 잘못된 경로 포맷 주입 (절대 경로)
        self.contract.allowed_paths = [PathItem(path="/invalid/path", kind="file")]
        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, "dummy", True, self.jules_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "SCOPE_CANONICALIZATION_FAILED")
        self.mock_transport.request.assert_not_called()

    def test_medium_risk_with_authorization_success(self):
        """MEDIUM 위험도라도 명시적 권한이 있으면 세션 생성 진행 (is_eligible=False 전달)."""
        self.contract.risk_level = "MEDIUM"
        _, self.evidence.contract_hash = canonicalize_contract(self.contract)

        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, "dummy", True, self.jules_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "CREATED")

        # 어댑터에 전달된 PreGateResult 검증 (단위 테스트에서 접근 불가한 내부 변수이므로 mock transport body의 전달 여부를 통해 우회/혹은 어댑터 반환 여부 확인)
        # HTTP Transport는 호출되었어야 함.
        self.mock_transport.request.assert_called_once()

    def test_medium_risk_without_authorization_blocked(self):
        """MEDIUM 위험도이고 명시적 권한이 없으면 세션 생성 차단."""
        self.contract.risk_level = "MEDIUM"
        _, self.evidence.contract_hash = canonicalize_contract(self.contract)

        response = execute_dispatch_session(
            self.contract, self.evidence, self.source_name, "dummy", False, self.jules_adapter, self.actual_base_sha
        )
        self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(response.reason_code, "SESSION_CREATION_NOT_AUTHORIZED")
        self.mock_transport.request.assert_not_called()


    def _plan_session_response(self):
        return JulesSessionResponse(
            session_id="sessions/dispatch-plan-001",
            task_id=self.contract.task_id,
            branch_name=None,
            pr_number=None,
            status="CREATED",
            reason_code=None,
            created_at_utc="2026-09-25T00:00:00Z",
            updated_at_utc="2026-09-25T00:00:00Z",
        )

    def _seed_plan_session_repository(self, repository):
        repository.save_task(TaskRecord(
            task_id=self.contract.task_id,
            base_commit_sha=self.contract.base_commit_sha,
            contract_hash=self.contract_hash,
            approved_scope_hash=self.scope_hash,
            idempotency_key=self.contract.idempotency_key,
            status="APPROVED",
            created_at_utc="2026-09-25T00:00:00Z",
            updated_at_utc="2026-09-25T00:00:00Z",
        ))
        repository.save_approval_evidence(self.evidence)

    def test_created_session_registers_once_when_repository_is_injected(self):
        """정상 생성 세션은 명시적 저장소 주입 시 등록을 정확히 한 번 수행한다."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = StateRepository(Path(temp_dir) / "state.db")
            self._seed_plan_session_repository(repository)
            adapter = Mock()
            adapter.create_session.return_value = self._plan_session_response()

            response = execute_dispatch_session(
                self.contract, self.evidence, self.source_name, "dummy", True,
                adapter, self.actual_base_sha, plan_session_repository=repository,
            )

            self.assertEqual(response.status, "CREATED")
            adapter.create_session.assert_called_once()
            registration = repository.get_plan_session_registration(self.contract.task_id)
            self.assertIsNotNone(registration)
            self.assertEqual(registration.session_id, "sessions/dispatch-plan-001")

    def test_registration_failure_does_not_retry_session_creation(self):
        """등록 실패는 API 재호출 없이 고정 사유 코드의 안전 상태로 전이한다."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = StateRepository(Path(temp_dir) / "state.db")
            adapter = Mock()
            adapter.create_session.return_value = self._plan_session_response()

            response = execute_dispatch_session(
                self.contract, self.evidence, self.source_name, "dummy", True,
                adapter, self.actual_base_sha, plan_session_repository=repository,
            )

            self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
            self.assertEqual(response.reason_code, "TASK_NOT_REGISTERED")
            adapter.create_session.assert_called_once()
            self.assertIsNone(repository.get_plan_session_registration(self.contract.task_id))

    def test_prevalidation_failure_calls_neither_adapter_nor_registration(self):
        """사전 검증 실패 시 API와 Plan 등록 호출은 모두 0회다."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = StateRepository(Path(temp_dir) / "state.db")
            adapter = Mock()
            with patch("orchestrator.dispatch_entrypoint.register_plan_session") as registration:
                response = execute_dispatch_session(
                    self.contract, self.evidence, self.source_name, "dummy", False,
                    adapter, self.actual_base_sha, plan_session_repository=repository,
                )

            self.assertEqual(response.reason_code, "SESSION_CREATION_NOT_AUTHORIZED")
            adapter.create_session.assert_not_called()
            registration.assert_not_called()


    def test_non_created_response_skips_registration(self):
        """세션 생성 성공 전 상태는 저장소가 주입돼도 등록하지 않는다."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = StateRepository(Path(temp_dir) / "state.db")
            adapter = Mock()
            pending = self._plan_session_response()
            pending.status = "NEEDS_HUMAN_REVIEW"
            pending.reason_code = "REMOTE_CREATE_FAILED"
            adapter.create_session.return_value = pending

            response = execute_dispatch_session(
                self.contract, self.evidence, self.source_name, "dummy", True,
                adapter, self.actual_base_sha, plan_session_repository=repository,
            )

            self.assertEqual(response.status, "NEEDS_HUMAN_REVIEW")
            self.assertEqual(response.reason_code, "REMOTE_CREATE_FAILED")
            adapter.create_session.assert_called_once()
            self.assertIsNone(repository.get_plan_session_registration(self.contract.task_id))


    def test_real_adapter_created_response_registers_plan_session(self):
        """RealJulesAdapter의 생성 응답도 Plan 단계 등록 조건과 호환된다."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = StateRepository(Path(temp_dir) / "state.db")
            self._seed_plan_session_repository(repository)

            response = execute_dispatch_session(
                self.contract, self.evidence, self.source_name, "dummy", True,
                self.jules_adapter, self.actual_base_sha,
                plan_session_repository=repository,
            )

            self.assertEqual(response.status, "CREATED")
            self.assertIsNone(response.branch_name)
            self.assertIsNone(response.pr_number)
            self.mock_transport.request.assert_called_once()
            self.assertIsNotNone(
                repository.get_plan_session_registration(self.contract.task_id)
            )

if __name__ == '__main__':
    unittest.main()
