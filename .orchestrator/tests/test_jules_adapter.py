"""FakeJulesAdapter 및 RealJulesAdapter, JulesHttpTransport 단위 테스트."""

import json
import unittest
from unittest.mock import MagicMock, patch
from typing import Any, Dict, Optional, List
from orchestrator.jules_adapter import (
    FakeJulesAdapter,
    RealJulesAdapter,
    JulesHttpTransport,
    UrllibJulesHttpTransport,
    TransportError,
    JulesSessionRequest,
    PreGateResult,
    ActivitySummary,
    validate_reason_code,
    validate_source_name,
)


from orchestrator.models import PathItem


SAMPLE_ALLOWED_PATHS = [PathItem(path="src/main", kind="directory_recursive")]
SAMPLE_FORBIDDEN_PATHS = [PathItem(path="src/main/secret", kind="directory_recursive")]

class MockJulesHttpTransport(JulesHttpTransport):
    """가짜/목 HTTP 전송 계층 (외부 네트워크 접속 없음)."""

    def __init__(self) -> None:
        self.requests: List[Dict[str, Any]] = []
        self.response_to_return: Optional[Dict[str, Any]] = None
        self.error_to_raise: Optional[TransportError] = None

    def request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        self.requests.append({
            "method": method,
            "path": path,
            "headers": headers,
            "body": body,
            "timeout": timeout,
        })
        if self.error_to_raise:
            raise self.error_to_raise
        return self.response_to_return if self.response_to_return is not None else {}


class TestJulesSessionRequestPromptMasking(unittest.TestCase):
    """JulesSessionRequest 프롬프트 및 source_name repr 차단 검증 테스트."""

    def test_prompt_and_source_name_excluded_from_repr(self) -> None:
        """repr(JulesSessionRequest) 실행 시 프롬프트와 source_name 원문이 포함되지 않음을 검증."""
        secret_prompt = "비밀_프롬프트_원문_12345_SECRET"
        secret_source = "sources/github/owner/secret-repo"
        req = JulesSessionRequest(
            task_id="TEST-TASK-001",
            contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
            base_sha="7f782c0a6ab295bb9db4d45971dc0d74c7e247e9",
            allowed_paths=SAMPLE_ALLOWED_PATHS,
            forbidden_paths=SAMPLE_FORBIDDEN_PATHS,
            source_name=secret_source,
            prompt=secret_prompt,
        )
        repr_str = repr(req)
        self.assertNotIn(secret_prompt, repr_str)
        self.assertNotIn(secret_source, repr_str)
        self.assertEqual(req.prompt, secret_prompt)  # 데이터 속성은 정상 유지
        self.assertEqual(req.source_name, secret_source)


class TestUrllibJulesHttpTransport(unittest.TestCase):
    """UrllibJulesHttpTransport 비객체 JSON 응답 안전 거부 검증 테스트."""

    def setUp(self) -> None:
        self.transport = UrllibJulesHttpTransport(base_url="https://jules.googleapis.com/v1alpha")

    @patch("urllib.request.urlopen")
    def test_non_dict_json_responses_raise_invalid_response_format(self, mock_urlopen: MagicMock) -> None:
        """JSON 배열, 문자열, 숫자, 불리언 응답 수신 시 INVALID_RESPONSE_FORMAT 예외 발생 검증."""
        non_dict_payloads = [
            b"[1, 2, 3]",
            b'"just a string"',
            b"12345",
            b"true",
            b"false",
        ]

        for payload in non_dict_payloads:
            with self.subTest(payload=payload):
                mock_resp = MagicMock()
                mock_resp.read.return_value = payload
                mock_resp.__enter__.return_value = mock_resp
                mock_urlopen.return_value = mock_resp

                with self.assertRaises(TransportError) as ctx:
                    self.transport.request(method="GET", path="sources", headers={})
                self.assertEqual(ctx.exception.reason_code, "INVALID_RESPONSE_FORMAT")

    @patch("urllib.request.urlopen")
    def test_empty_http_response_returns_empty_dict(self, mock_urlopen: MagicMock) -> None:
        """0바이트 빈 HTTP 응답은 sendMessage 등의 정상 응답으로 {} 반환 검증."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = b""
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = self.transport.request(method="POST", path="sessions/ses-1:sendMessage", headers={})
        self.assertEqual(res, {})


class TestValidateSourceName(unittest.TestCase):
    """validate_source_name 다중 세그먼트 및 거부 조건 검증 테스트."""

    def test_valid_single_and_multi_segment_sources(self) -> None:
        """단일 세그먼트 및 공식 GitHub 다중 세그먼트 sources 허용 검증."""
        valid_cases = [
            "sources/default",
            "sources/src-123",
            "sources/github/test-owner/test-repository",
            "sources/github/owner-name/repo_name-123",
            "sources/a/b/c/d/e",
        ]
        for src in valid_cases:
            with self.subTest(source_name=src):
                self.assertTrue(validate_source_name(src))

    def test_invalid_source_names_rejected(self) -> None:
        """traversal, 역슬래시, 공백, 제어문자, 빈 세그먼트, 잘못된 접두어 거부 검증."""
        invalid_cases = [
            "sources/..",
            "sources/../secret",
            "sources/./a",
            "sources/a/../b",
            "sources/github\\owner\\repo",
            "sources/github/owner /repo",
            "sources/github/owner\n/repo",
            "sources//repo",
            "sources/",
            "sources",
            "invalid_prefix/a/b",
            "",
            "   ",
            None,
        ]
        for src in invalid_cases:
            with self.subTest(source_name=src):
                self.assertFalse(validate_source_name(src))


class TestFakeJulesAdapter(unittest.TestCase):
    def test_create_session_scope_canonicalization_failed(self):
        adapter = FakeJulesAdapter()
        # Invalid paths to cause ScopeCanonicalizationError
        invalid_paths = [PathItem(path="/absolute/path", kind="file")]

        req = JulesSessionRequest(
            task_id="TSK-111",
            contract_hash="hash_c",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idemp_1",
            base_sha="sha_base",
            allowed_paths=invalid_paths,
            forbidden_paths=SAMPLE_FORBIDDEN_PATHS,
            source_name="sources/github/owner/repo"
        )

        gate_res = PreGateResult(
            is_valid=True,
            is_dispatch_eligible=False,
            is_session_creation_authorized=True,
            status="APPROVED",
            task_id="TSK-111",
            contract_hash="hash_c",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idemp_1",
            base_sha="sha_base",
        )

        resp = adapter.create_session(req, gate_res)
        self.assertEqual(resp.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(resp.reason_code, "SCOPE_LOCK_CANONICALIZATION_FAILED")
        self.assertEqual(adapter._session_counter, 0)

    def test_create_session_scope_hash_mismatch(self):
        adapter = FakeJulesAdapter()

        req = JulesSessionRequest(
            task_id="TSK-111",
            contract_hash="hash_c",
            approved_scope_hash="hash_s_wrong", # mismatched hash
            idempotency_key="idemp_1",
            base_sha="sha_base",
            allowed_paths=SAMPLE_ALLOWED_PATHS,
            forbidden_paths=SAMPLE_FORBIDDEN_PATHS,
            source_name="sources/github/owner/repo"
        )

        gate_res = PreGateResult(
            is_valid=True,
            is_dispatch_eligible=False,
            is_session_creation_authorized=True,
            status="APPROVED",
            task_id="TSK-111",
            contract_hash="hash_c",
            approved_scope_hash="hash_s_wrong",
            idempotency_key="idemp_1",
            base_sha="sha_base",
        )

        resp = adapter.create_session(req, gate_res)
        self.assertEqual(resp.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(resp.reason_code, "SCOPE_HASH_MISMATCH")
        self.assertEqual(adapter._session_counter, 0)

    """FakeJulesAdapter 기능 테스트 모음."""

    def setUp(self) -> None:
        self.fixed_timestamp = "2026-09-17T12:00:00.000000+00:00"
        self.base_sha = "7f782c0a6ab295bb9db4d45971dc0d74c7e247e9"
        self.adapter = FakeJulesAdapter(
            clock_fn=lambda: self.fixed_timestamp,
            remote_main_sha_fn=lambda: self.base_sha
        )
        self.valid_pre_gate = PreGateResult(
            is_valid=True,
            is_dispatch_eligible=True,
            is_session_creation_authorized=True,
            status="APPROVED",
            task_id="TEST-TASK-001",
            contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
            base_sha=self.base_sha,
        )
        self.valid_request = JulesSessionRequest(
            task_id="TEST-TASK-001",
            contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
            base_sha=self.base_sha,
            allowed_paths=SAMPLE_ALLOWED_PATHS,
            forbidden_paths=SAMPLE_FORBIDDEN_PATHS,
            source_name="sources/github/test-owner/test-repository",
            prompt="테스트 프롬프트",
        )

    def test_successful_session_creation_and_state_transition(self) -> None:
        """정상 사전 게이트 및 요청을 통한 세션 생성 및 상태 전이 테스트."""
        res = self.adapter.create_session(self.valid_request, self.valid_pre_gate)
        self.assertEqual(res.status, "CREATED")
        self.assertTrue(res.session_id.startswith("SES-TEST-TASK-001-"))
        self.assertIsNone(res.reason_code)
        self.assertEqual(res.task_id, "TEST-TASK-001")
        self.assertIsNone(res.branch_name) # 초기엔 None
        self.assertEqual(res.created_at_utc, self.fixed_timestamp)

        # RUNNING 상태 전이
        running_res = self.adapter.transition_session_status(res.session_id, "RUNNING")
        self.assertEqual(running_res.status, "RUNNING")

        # 브랜치 및 PR 사후 바인딩
        bind_res = self.adapter.bind_session_outputs(res.session_id, "feat/real-work", 101)
        self.assertEqual(bind_res.branch_name, "feat/real-work")
        self.assertEqual(bind_res.pr_number, 101)

        # COMPLETED 상태 전이
        completed_res = self.adapter.transition_session_status(
            res.session_id, "COMPLETED", reason_code="TASK_COMPLETED_SUCCESS"
        )
        self.assertEqual(completed_res.status, "COMPLETED")
        self.assertEqual(completed_res.reason_code, "TASK_COMPLETED_SUCCESS")

    def test_invalid_source_name_fails(self) -> None:
        """source_name 누락, 빈값, 잘못된 포맷 시 INVALID_SOURCE_NAME 거부 검증."""
        bad_sources = ["", "  ", "default", "invalid_prefix/123", "sources/..", None]
        for bad_src in bad_sources:
            with self.subTest(source_name=bad_src):
                req = JulesSessionRequest(
                    task_id="TEST-TASK-001",
                    contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
                    approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
                    idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
                    base_sha=self.base_sha,
            allowed_paths=SAMPLE_ALLOWED_PATHS,
            forbidden_paths=SAMPLE_FORBIDDEN_PATHS,
                    source_name=bad_src,
                )
                res = self.adapter.create_session(req, self.valid_pre_gate)
                self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
                self.assertEqual(res.reason_code, "INVALID_SOURCE_NAME")

    def test_medium_risk_manual_authorization_session_creation(self) -> None:
        """MEDIUM 위험도 및 자동 Dispatch 부적격(is_dispatch_eligible=False)이지만 명시적 세션 생성 권한이 있고 status=APPROVED인 경우 생성 가능 검증."""
        medium_pre_gate = PreGateResult(
            is_valid=True,
            is_dispatch_eligible=False,
            is_session_creation_authorized=True,
            status="APPROVED",
            task_id="TEST-TASK-001",
            contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
            base_sha=self.base_sha,
        )
        res = self.adapter.create_session(self.valid_request, medium_pre_gate)
        self.assertEqual(res.status, "CREATED")
        self.assertTrue(res.session_id.startswith("SES-TEST-TASK-001-"))

    def test_non_approved_status_fails_even_if_authorized(self) -> None:
        """WITHDRAWN 또는 EXPIRED 등 APPROVED가 아닌 상태일 경우 is_valid=True, is_session_creation_authorized=True여도 NEEDS_HUMAN_REVIEW 처리 검증."""
        for non_approved_status in ["WITHDRAWN", "EXPIRED", "MODIFIED", "NEEDS_HUMAN_REVIEW"]:
            with self.subTest(status=non_approved_status):
                pre_gate = PreGateResult(
                    is_valid=True,
                    is_dispatch_eligible=False,
                    is_session_creation_authorized=True,
                    status=non_approved_status,
                    task_id="TEST-TASK-001",
                    contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
                    approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
                    idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
                    base_sha=self.base_sha,
                )
                res = self.adapter.create_session(self.valid_request, pre_gate)
                self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
                self.assertEqual(res.reason_code, "PREGATE_VALIDATION_FAILED")

    def test_unauthorized_session_creation_fails(self) -> None:
        """명시적 세션 생성 권한이 없을 경우 (is_session_creation_authorized=False) NEEDS_HUMAN_REVIEW 처리 검증."""
        unauthorized_pre_gate = PreGateResult(
            is_valid=True,
            is_dispatch_eligible=False,
            is_session_creation_authorized=False,
            status="NEEDS_HUMAN_REVIEW",
            task_id="TEST-TASK-001",
            contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
            base_sha=self.base_sha,
        )
        res = self.adapter.create_session(self.valid_request, unauthorized_pre_gate)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason_code, "PREGATE_VALIDATION_FAILED")

    def test_determinism_with_fixed_clock(self) -> None:
        """동일 입력 및 초기 상태에서 타임스탬프를 포함한 세션 생성 응답이 완전 결정론적인지 검증."""
        adapter1 = FakeJulesAdapter(
            clock_fn=lambda: "2026-09-17T12:00:00.000000+00:00",
            remote_main_sha_fn=lambda: self.base_sha
        )
        adapter2 = FakeJulesAdapter(
            clock_fn=lambda: "2026-09-17T12:00:00.000000+00:00",
            remote_main_sha_fn=lambda: self.base_sha
        )

        res1 = adapter1.create_session(self.valid_request, self.valid_pre_gate)
        res2 = adapter2.create_session(self.valid_request, self.valid_pre_gate)

        self.assertEqual(res1.to_dict(), res2.to_dict())
        self.assertEqual(res1.session_id, res2.session_id)
        self.assertEqual(res1.created_at_utc, "2026-09-17T12:00:00.000000+00:00")
        self.assertEqual(res2.created_at_utc, "2026-09-17T12:00:00.000000+00:00")

    def test_explicit_cancellation(self) -> None:
        """세션 명시적 취소 테스트."""
        res = self.adapter.create_session(self.valid_request, self.valid_pre_gate)
        self.assertEqual(res.status, "CREATED")

        cancel_res = self.adapter.cancel_session(res.session_id, reason_code="USER_REQUESTED_CANCEL")
        self.assertEqual(cancel_res.status, "CANCELLED")
        self.assertEqual(cancel_res.reason_code, "USER_REQUESTED_CANCEL")

    def test_pregate_failure_handling(self) -> None:
        """사전 게이트 미통과 시 NEEDS_HUMAN_REVIEW 처리 테스트."""
        invalid_pre_gate = PreGateResult(
            is_valid=False,
            is_dispatch_eligible=False,
            is_session_creation_authorized=False,
            status="NEEDS_HUMAN_REVIEW",
            task_id="TEST-TASK-001",
            contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
            base_sha=self.base_sha,
        )
        res = self.adapter.create_session(self.valid_request, invalid_pre_gate)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason_code, "PREGATE_VALIDATION_FAILED")
        self.assertEqual(res.session_id, "")

    def test_base_sha_mismatch(self) -> None:
        """요청 base_sha와 원격 main SHA 불일치 시 NEEDS_HUMAN_REVIEW (API 호출 방지)."""
        bad_request = JulesSessionRequest(
            task_id="TEST-TASK-001",
            contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
            base_sha="badbadbadbadbadbadbadbadbadbadbadbadbadb",
            allowed_paths=SAMPLE_ALLOWED_PATHS,
            forbidden_paths=SAMPLE_FORBIDDEN_PATHS,
            source_name="sources/github/owner/repo",
        )
        # Contract의 SHA도 요청과 같게 맞춤 (그래야 Contract 불일치가 아닌 원격 불일치로 통과)
        bad_pre_gate = PreGateResult(
            is_valid=True,
            is_dispatch_eligible=True,
            is_session_creation_authorized=True,
            status="APPROVED",
            task_id="TEST-TASK-001",
            contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
            base_sha="badbadbadbadbadbadbadbadbadbadbadbadbadb",
        )
        res = self.adapter.create_session(bad_request, bad_pre_gate)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason_code, "BASE_SHA_MISMATCH")

    def test_binding_mismatch_handling(self) -> None:
        """요청 바인딩과 사전 게이트 바인딩 불일치 시 NEEDS_HUMAN_REVIEW 처리 테스트."""
        mismatched_request = JulesSessionRequest(
            task_id="TEST-TASK-001",
            contract_hash="9999999999999999999999999999999999999999999999999999999999999999",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
            base_sha=self.base_sha,
            allowed_paths=SAMPLE_ALLOWED_PATHS,
            forbidden_paths=SAMPLE_FORBIDDEN_PATHS,
            source_name="sources/src-test-001",
        )
        res = self.adapter.create_session(mismatched_request, self.valid_pre_gate)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason_code, "BINDING_MISMATCH")
        self.assertEqual(res.session_id, "")

    def test_duplicate_branch_or_task_binding_conflict(self) -> None:
        """동일 Task ID에 대한 중복 세션 생성 거부 (이제 Branch는 사후 결속) 테스트."""
        res1 = self.adapter.create_session(self.valid_request, self.valid_pre_gate)
        self.assertEqual(res1.status, "CREATED")

        dup_request = JulesSessionRequest(
            task_id="TEST-TASK-001",
            contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
            base_sha=self.base_sha,
            allowed_paths=SAMPLE_ALLOWED_PATHS,
            forbidden_paths=SAMPLE_FORBIDDEN_PATHS,
            source_name="sources/src-test-001",
        )
        dup_pre_gate = PreGateResult(
            is_valid=True,
            is_dispatch_eligible=True,
            is_session_creation_authorized=True,
            status="APPROVED",
            task_id="TEST-TASK-001",
            contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
            base_sha=self.base_sha,
        )
        res2 = self.adapter.create_session(dup_request, dup_pre_gate)
        self.assertEqual(res2.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res2.reason_code, "DUPLICATE_BINDING_CONFLICT")

    def test_duplicate_binding_conflict_on_outputs(self) -> None:
        """동일한 PR 번호 또는 Branch를 다른 세션에 중복 바인딩 시도 시 상충 거부 테스트."""
        res1 = self.adapter.create_session(self.valid_request, self.valid_pre_gate)
        self.adapter.bind_session_outputs(res1.session_id, "feat/branch-1", 100)

        req2 = JulesSessionRequest(
            task_id="TEST-TASK-002",
            contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idem-v1:4444444444444444444444444444444444444444444444444444444444444444",
            base_sha=self.base_sha,
            allowed_paths=SAMPLE_ALLOWED_PATHS,
            forbidden_paths=SAMPLE_FORBIDDEN_PATHS,
            source_name="sources/src-test-001",
        )
        pg2 = PreGateResult(
            is_valid=True,
            is_dispatch_eligible=True,
            is_session_creation_authorized=True,
            status="APPROVED",
            task_id="TEST-TASK-002",
            contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idem-v1:4444444444444444444444444444444444444444444444444444444444444444",
            base_sha=self.base_sha,
        )
        res2 = self.adapter.create_session(req2, pg2)

        # PR 충돌
        bind_res2_pr = self.adapter.bind_session_outputs(res2.session_id, "feat/branch-2", 100)
        self.assertEqual(bind_res2_pr.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(bind_res2_pr.reason_code, "DUPLICATE_BINDING_CONFLICT")

        # 브랜치 충돌
        bind_res2_br = self.adapter.bind_session_outputs(res2.session_id, "feat/branch-1", 101)
        self.assertEqual(bind_res2_br.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(bind_res2_br.reason_code, "DUPLICATE_BINDING_CONFLICT")

    def test_reason_code_validation(self) -> None:
        """구조화 사유 코드 형식 검증 및 거부 테스트."""
        self.assertTrue(validate_reason_code("BINDING_MISMATCH"))
        self.assertTrue(validate_reason_code("REASON_123"))
        self.assertFalse(validate_reason_code("lower_case_reason"))
        self.assertFalse(validate_reason_code("INVALID-HYPHEN"))
        self.assertFalse(validate_reason_code("FREE TEXT WITH SPACES"))
        self.assertFalse(validate_reason_code("A" * 65))

        res = self.adapter.create_session(self.valid_request, self.valid_pre_gate)
        trans_res = self.adapter.transition_session_status(
            res.session_id, "RUNNING", reason_code="invalid-code"
        )
        self.assertEqual(trans_res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(trans_res.reason_code, "INVALID_REASON_CODE")


class TestRealJulesAdapter(unittest.TestCase):
    """RealJulesAdapter 및 가짜 전송 계층 연동 기능 단위 테스트."""

    def setUp(self) -> None:
        self.api_key = "test-secret-api-key-12345"
        self.mock_transport = MockJulesHttpTransport()
        self.fixed_timestamp = "2026-09-18T10:00:00.000000+00:00"
        self.base_sha = "7f782c0a6ab295bb9db4d45971dc0d74c7e247e9"
        self.adapter = RealJulesAdapter(
            api_key=self.api_key,
            transport=self.mock_transport,
            clock_fn=lambda: self.fixed_timestamp,
            remote_main_sha_fn=lambda: self.base_sha
        )
        self.valid_pre_gate = PreGateResult(
            is_valid=True,
            is_dispatch_eligible=False,
            is_session_creation_authorized=True,
            status="APPROVED",
            task_id="REAL-TASK-001",
            contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
            base_sha=self.base_sha,
        )
        self.valid_request = JulesSessionRequest(
            task_id="REAL-TASK-001",
            contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
            base_sha=self.base_sha,
            allowed_paths=SAMPLE_ALLOWED_PATHS,
            forbidden_paths=SAMPLE_FORBIDDEN_PATHS,
            source_name="sources/github/test-owner/test-repository",
            prompt="실제 어댑터 테스트 프롬프트",
        )

    def test_init_without_api_key_raises_value_error(self) -> None:
        """API 키 없이 객체 생성 시 ValueError 발생 검증."""
        with self.assertRaises(ValueError):
            RealJulesAdapter(api_key="", transport=self.mock_transport)
        with self.assertRaises(ValueError):
            RealJulesAdapter(api_key="   ", transport=self.mock_transport)

    def test_list_sources_filters_and_returns_only_source_names(self) -> None:
        """GET /sources 연동 시 메타데이터 배제하고 sources/<id> 리소스 이름만 추출 반환 검증."""
        self.mock_transport.response_to_return = {
            "sources": [
                {"name": "sources/github/test-owner/test-repository", "displayName": "테스트 소스", "extraMeta": "secret"},
                {"name": "invalid_source_format", "displayName": "Invalid"},
                "sources/src-my-repo-002",
            ]
        }
        sources = self.adapter.list_sources()

        self.assertEqual(len(self.mock_transport.requests), 1)
        req = self.mock_transport.requests[0]
        self.assertEqual(req["method"], "GET")
        self.assertEqual(req["path"], "sources")
        self.assertEqual(req["headers"]["X-Goog-Api-Key"], self.api_key)

        # 원시 메타데이터가 제외되고 sources 리소스 이름만 추출됨 확인
        self.assertEqual(sources, {"sources": ["sources/github/test-owner/test-repository", "sources/src-my-repo-002"]})

    def test_create_session_request_body_and_source_injection(self) -> None:
        """POST /sessions 세션 생성 요청 바디 형성 및 source_name 주입 검증."""
        self.mock_transport.response_to_return = {
            "name": "sessions/ses-real-001",
            "state": "CREATED",
        }

        resp = self.adapter.create_session(self.valid_request, self.valid_pre_gate)

        self.assertEqual(resp.status, "CREATED")
        self.assertEqual(resp.session_id, "sessions/ses-real-001")
        self.assertEqual(len(self.mock_transport.requests), 1)

        req = self.mock_transport.requests[0]
        self.assertEqual(req["method"], "POST")
        self.assertEqual(req["path"], "sessions")
        self.assertEqual(req["headers"]["X-Goog-Api-Key"], self.api_key)

        body = req["body"]
        self.assertEqual(body["prompt"], "실제 어댑터 테스트 프롬프트")
        self.assertEqual(body["sourceContext"]["source"], "sources/github/test-owner/test-repository")
        self.assertEqual(body["sourceContext"]["githubRepoContext"]["startingBranch"], "main")
        self.assertEqual(body["automationMode"], "AUTO_CREATE_PR")
        self.assertTrue(body["requirePlanApproval"])

    def test_base_sha_mismatch_prevents_api_call(self) -> None:
        """원격 SHA 불일치 시 HTTP 호출 없이 NEEDS_HUMAN_REVIEW 반환 검증."""
        bad_request = JulesSessionRequest(
            task_id="REAL-TASK-001",
            contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
            base_sha="badbadbadbadbadbadbadbadbadbadbadbadbadb",
            allowed_paths=SAMPLE_ALLOWED_PATHS,
            forbidden_paths=SAMPLE_FORBIDDEN_PATHS,
            source_name="sources/github/test-owner/test-repository",
        )
        # Contract의 SHA도 요청과 같게 맞춤 (그래야 Contract 불일치가 아닌 원격 불일치로 통과)
        bad_pre_gate = PreGateResult(
            is_valid=True,
            is_dispatch_eligible=False,
            is_session_creation_authorized=True,
            status="APPROVED",
            task_id="REAL-TASK-001",
            contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
            base_sha="badbadbadbadbadbadbadbadbadbadbadbadbadb",
        )
        res = self.adapter.create_session(bad_request, bad_pre_gate)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason_code, "BASE_SHA_MISMATCH")
        self.assertEqual(len(self.mock_transport.requests), 0)

    def test_contract_base_sha_mismatch_prevents_api_call(self) -> None:
        """요청 SHA가 원격과 같더라도 사전 게이트(Contract) SHA와 다르면 HTTP 호출 없이 NEEDS_HUMAN_REVIEW 반환 검증."""
        mismatched_pre_gate = PreGateResult(
            is_valid=True,
            is_dispatch_eligible=False,
            is_session_creation_authorized=True,
            status="APPROVED",
            task_id="REAL-TASK-001",
            contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
            approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
            idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
            base_sha="different_approved_sha_from_contract_123",
        )
        res = self.adapter.create_session(self.valid_request, mismatched_pre_gate)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason_code, "BINDING_MISMATCH")
        self.assertEqual(len(self.mock_transport.requests), 0)

    def test_create_session_invalid_source_name_rejection(self) -> None:
        """sources/default 등 하드코딩이나 빈값/잘못된 포맷의 source_name 전달 시 INVALID_SOURCE_NAME 거부."""
        bad_sources = ["", "  ", "default", "sources/", "invalid_prefix/123", "sources/..", "sources/a\\b", None]
        for bad_src in bad_sources:
            with self.subTest(source_name=bad_src):
                req = JulesSessionRequest(
                    task_id="REAL-TASK-001",
                    contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
                    approved_scope_hash="53215c72aacaba4c01f67e3c60da49dee4e7289674168a269034b7fc4c587111",
                    idempotency_key="idem-v1:3333333333333333333333333333333333333333333333333333333333333333",
                    base_sha=self.base_sha,
            allowed_paths=SAMPLE_ALLOWED_PATHS,
            forbidden_paths=SAMPLE_FORBIDDEN_PATHS,
                    source_name=bad_src,
                )
                res = self.adapter.create_session(req, self.valid_pre_gate)
                self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
                self.assertEqual(res.reason_code, "INVALID_SOURCE_NAME")

    def test_get_activities_returns_official_union_summary_without_raw_payloads(self) -> None:
        """GET /sessions/{id}/activities 연동시 공식 Activity union 필드 존재 여부로만 요약되며 원시 민감 패이로드가 절대 남지 않음을 검증."""
        # 공식 union 필드(userMessaged, agentMessaged, planGenerated, planApproved, progressUpdated, sessionCompleted, sessionFailed) 구조의 가짜 응답
        raw_sensitive_official_activity_response = {
            "activities": [
                {
                    "name": "sessions/ses-real-001/activities/act-1",
                    "userMessaged": {
                        "userMessage": "민감한 사용자 메시지 secret-pass-999"
                    },
                },
                {
                    "name": "sessions/ses-real-001/activities/act-2",
                    "agentMessaged": {
                        "agentMessage": "에이전트 메시지 원문",
                        "patch": "diff --git a/file.py b/file.py\n+SECRET='xyz'"
                    },
                },
                {
                    "name": "sessions/ses-real-001/activities/act-3",
                    "planGenerated": {
                        "plan": {"title": "비밀 계획 원문", "steps": ["step1", "step2"]}
                    },
                },
                {
                    "name": "sessions/ses-real-001/activities/act-4",
                    "planApproved": {},
                },
                {
                    "name": "sessions/ses-real-001/activities/act-5",
                    "progressUpdated": {
                        "bashOutput": "Executing command... SECRET_TOKEN=abc"
                    },
                },
                {
                    "name": "sessions/ses-real-001/activities/act-6",
                    "sessionCompleted": {},
                },
                {
                    "name": "sessions/ses-real-001/activities/act-7",
                    "unknownField": "알 수 없는 필드",
                },
            ]
        }
        self.mock_transport.response_to_return = raw_sensitive_official_activity_response

        summary = self.adapter.get_activities("sessions/ses-real-001")

        self.assertIsInstance(summary, ActivitySummary)
        self.assertEqual(summary.total_count, 7)
        self.assertEqual(
            summary.activity_types,
            [
                "USER_MESSAGED",
                "AGENT_MESSAGED",
                "PLAN_GENERATED",
                "PLAN_APPROVED",
                "PROGRESS_UPDATED",
                "SESSION_COMPLETED",
                "UNKNOWN_ACTIVITY",
            ],
        )
        self.assertTrue(summary.is_completed)
        self.assertFalse(summary.is_failed)

        # 요약 결과 딕셔너리, repr, str 검사: 원시 민감 텍스트가 절대 포함되지 않는지 확인
        summary_dict_str = str(summary.to_dict())
        summary_repr_str = repr(summary)

        sensitive_tokens = [
            "secret-pass-999",
            "에이전트 메시지 원문",
            "diff --git",
            "SECRET='xyz'",
            "비밀 계획 원문",
            "bashOutput",
            "SECRET_TOKEN=abc",
            "userMessaged",
            "agentMessaged",
            "planGenerated",
            "progressUpdated",
        ]
        for token in sensitive_tokens:
            self.assertNotIn(token, summary_dict_str)
            self.assertNotIn(token, summary_repr_str)

    def test_get_activities_invalid_session_resource_name(self) -> None:
        """잘못된 세션 리소스 이름으로 get_activities() 호출 시 TransportError 발생 검증."""
        with self.assertRaises(TransportError) as ctx:
            self.adapter.get_activities("invalid-session-name")
        self.assertEqual(ctx.exception.reason_code, "INVALID_RESPONSE_FORMAT")

    def test_send_message_uses_prompt_key_and_handles_empty_dict_response(self) -> None:
        """POST /sessions/{id}:sendMessage 연동시 'prompt' 키만 사용하며 빈 응답 {}도 정상 처리함을 검증."""
        # 1. 정상 구조 응답 테스트
        self.mock_transport.response_to_return = {"name": "activities/act-message-1"}
        res = self.adapter.send_message("sessions/ses-real-001", "사용자 승인된 Codex 응답 메시지")
        self.assertEqual(res["name"], "activities/act-message-1")

        req = self.mock_transport.requests[0]
        self.assertEqual(req["method"], "POST")
        self.assertEqual(req["path"], "sessions/ses-real-001:sendMessage")
        self.assertIn("prompt", req["body"])
        self.assertNotIn("message", req["body"])
        self.assertEqual(req["body"]["prompt"], "사용자 승인된 Codex 응답 메시지")

        # 2. 빈 딕셔너리 응답 {} 정상 처리 검증
        self.mock_transport.requests.clear()
        self.mock_transport.response_to_return = {}
        res_empty = self.adapter.send_message("sessions/ses-real-001", "추가 메시지")
        self.assertEqual(res_empty, {})
        self.assertEqual(len(self.mock_transport.requests), 1)
        self.assertEqual(self.mock_transport.requests[0]["body"]["prompt"], "추가 메시지")

    def test_remote_cancel_unsupported_returns_needs_human_review(self) -> None:
        """cancel_session 호출 시 원격 호출 없이 REMOTE_CANCEL_UNSUPPORTED 및 NEEDS_HUMAN_REVIEW 반환."""
        res = self.adapter.cancel_session("sessions/ses-real-001")
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertEqual(res.reason_code, "REMOTE_CANCEL_UNSUPPORTED")
        self.assertEqual(len(self.mock_transport.requests), 0)

    def test_transport_error_code_mapping(self) -> None:
        """HTTP 연결/인증/응답/타임아웃 에러를 구조화 사유 코드로 매핑하여 NEEDS_HUMAN_REVIEW 처리 검증."""
        error_cases = [
            ("AUTHENTICATION_FAILED", "AUTHENTICATION_FAILED"),
            ("HTTP_CONNECTION_FAILED", "HTTP_CONNECTION_FAILED"),
            ("TIMEOUT_EXCEEDED", "TIMEOUT_EXCEEDED"),
            ("INVALID_RESPONSE_FORMAT", "INVALID_RESPONSE_FORMAT"),
        ]

        for err_code, expected_reason in error_cases:
            with self.subTest(err_code=err_code):
                self.mock_transport.error_to_raise = TransportError(err_code)
                resp = self.adapter.create_session(self.valid_request, self.valid_pre_gate)
                self.assertEqual(resp.status, "NEEDS_HUMAN_REVIEW")
                self.assertEqual(resp.reason_code, expected_reason)

    def test_secret_and_prompt_masking_in_repr(self) -> None:
        """__repr__ 및 로그/오류 출력에서 API 키 및 민감정보 비노출 통제 검증."""
        repr_str = repr(self.adapter)
        self.assertNotIn(self.api_key, repr_str)
        self.assertIn("api_key='***'", repr_str)

        transport_err = TransportError("AUTHENTICATION_FAILED", "비밀 메시지")
        err_str = str(transport_err)
        self.assertNotIn("비밀 메시지", err_str)
        self.assertIn("AUTHENTICATION_FAILED", err_str)


if __name__ == "__main__":
    unittest.main()
