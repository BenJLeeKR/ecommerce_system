"""Codex 검토 대기용 결과 패키지 생성기 단위 테스트."""

import unittest
from orchestrator.models import (
    ExecutionResultInput,
    CodexReviewResultPackage,
    ScopeValidationResult,
)
from orchestrator.jules_adapter import JulesSessionResponse
from orchestrator.result_package import (
    generate_result_package,
    validate_reason_code_format,
)


class TestResultPackageGenerator(unittest.TestCase):
    def setUp(self) -> None:
        self.task_id = "ORCH-BL-PH1-006-IMPLEMENT-001"
        self.session_id = "SES-ORCH-BL-PH1-006-IMPLEMENT-001-001"
        self.branch_name = "jules-3624698495886694371-658e1530"
        self.pr_identifier = 41
        self.pr_url = "https://github.com/BenJLeeKR/orchestrator_jules/pull/41"
        self.contract_hash = "ac3530dda96df70e8381832299fa09b2acffcd67e93f5d1391d698d2880f59ed"
        self.approved_scope_hash = "748e6e7273e86125f9a11658817340f8fde4971e3c2fffbfdec297f00bc2626a"
        self.idempotency_key = "idem-v1:54a174384a294046a3978f25305c27a628bad0273c16a47a222a6ed6e1a5c2f4"
        self.approval_id = "APV-ORCH-BL-PH1-006-IMPLEMENT-001-20260917-001"

        self.valid_scope_result = ScopeValidationResult(
            is_valid=True,
            reasons=[],
            approved_scope_hash=self.approved_scope_hash,
        )

        self.valid_input = ExecutionResultInput(
            task_id=self.task_id,
            session_id=self.session_id,
            branch_name=self.branch_name,
            pr_identifier=self.pr_identifier,
            status="COMPLETED",
            changed_files=["src/orchestrator/result_package.py"],
            verification_summary_codes=["TESTS_PASSED", "VERIFICATION_SUCCESSFUL"],
            scope_validation_result=self.valid_scope_result,
            contract_hash=self.contract_hash,
            approved_scope_hash=self.approved_scope_hash,
            idempotency_key=self.idempotency_key,
            approval_id=self.approval_id,
        )

        self.existing_session = JulesSessionResponse(
            session_id=self.session_id,
            task_id=self.task_id,
            branch_name=self.branch_name,
            pr_number=self.pr_identifier,
            status="RUNNING",
            reason_code=None,
            created_at_utc="2026-09-17T00:00:00Z",
            updated_at_utc="2026-09-17T00:00:00Z",
        )

    def test_successful_package_generation(self) -> None:
        """모든 조건이 만족될 때 RESULT_COLLECTED 패키지가 올바르게 생성되는지 검증."""
        pkg = generate_result_package(
            input_data=self.valid_input,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
            existing_session=self.existing_session,
        )

        self.assertEqual(pkg.status, "RESULT_COLLECTED")
        self.assertEqual(pkg.reason_codes, [])
        self.assertEqual(pkg.task_id, self.task_id)
        self.assertEqual(pkg.session_id, self.session_id)
        self.assertEqual(pkg.branch_name, self.branch_name)
        self.assertEqual(pkg.pr_identifier, self.pr_identifier)
        self.assertEqual(pkg.verification_summary_codes, ["TESTS_PASSED", "VERIFICATION_SUCCESSFUL"])

    def test_verification_summary_codes_invalid_cases(self) -> None:
        """verification_summary_codes가 빈 목록, 유효하지 않은 규격, 원시 로그 포함 시 VERIFICATION_SUMMARY_INVALID 처리 검증."""
        # 1. 빈 목록
        empty_input = ExecutionResultInput(
            task_id=self.task_id,
            session_id=self.session_id,
            branch_name=self.branch_name,
            pr_identifier=self.pr_identifier,
            status="COMPLETED",
            changed_files=[],
            verification_summary_codes=[],
            scope_validation_result=self.valid_scope_result,
            contract_hash=self.contract_hash,
            approved_scope_hash=self.approved_scope_hash,
            idempotency_key=self.idempotency_key,
            approval_id=self.approval_id,
        )
        pkg_empty = generate_result_package(
            input_data=empty_input,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
        )
        self.assertEqual(pkg_empty.status, "NEEDS_HUMAN_REVIEW")
        self.assertIn("VERIFICATION_SUMMARY_INVALID", pkg_empty.reason_codes)

        # 2. 유효하지 않은 코드/원시 로그/비밀값 포함 목록
        invalid_codes_input = ExecutionResultInput(
            task_id=self.task_id,
            session_id=self.session_id,
            branch_name=self.branch_name,
            pr_identifier=self.pr_identifier,
            status="COMPLETED",
            changed_files=[],
            verification_summary_codes=["TESTS_PASSED", "raw log trace containing secret token: sk_12345"],
            scope_validation_result=self.valid_scope_result,
            contract_hash=self.contract_hash,
            approved_scope_hash=self.approved_scope_hash,
            idempotency_key=self.idempotency_key,
            approval_id=self.approval_id,
        )
        pkg_invalid = generate_result_package(
            input_data=invalid_codes_input,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
        )
        self.assertEqual(pkg_invalid.status, "NEEDS_HUMAN_REVIEW")
        self.assertIn("VERIFICATION_SUMMARY_INVALID", pkg_invalid.reason_codes)

        # 원시 입력이 결과 패키지 및 to_dict()에 보존되지 않음을 확인
        pkg_str = str(pkg_invalid.to_dict())
        self.assertNotIn("sk_12345", pkg_str)
        self.assertNotIn("raw log trace", pkg_str)

    def test_pr_url_strict_format_and_session_matching(self) -> None:
        """PR URL의 엄격한 규격(https://<host>/<owner>/<repo>/pull/<양의 정수>) 및 세션 번호 일치 검증."""
        # 1. 올바른 PR URL
        valid_url_input = ExecutionResultInput(
            task_id=self.task_id,
            session_id=self.session_id,
            branch_name=self.branch_name,
            pr_identifier="https://github.com/BenJLeeKR/orchestrator_jules/pull/41",
            status="COMPLETED",
            changed_files=[],
            verification_summary_codes=["TESTS_PASSED"],
            scope_validation_result=self.valid_scope_result,
            contract_hash=self.contract_hash,
            approved_scope_hash=self.approved_scope_hash,
            idempotency_key=self.idempotency_key,
            approval_id=self.approval_id,
        )
        pkg_valid_url = generate_result_package(
            input_data=valid_url_input,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
            existing_session=self.existing_session,
        )
        self.assertEqual(pkg_valid_url.status, "RESULT_COLLECTED")

        # 2. pull 경로 없는 URL 거부
        no_pull_input = ExecutionResultInput(
            task_id=self.task_id,
            session_id=self.session_id,
            branch_name=self.branch_name,
            pr_identifier="https://github.com",
            status="COMPLETED",
            changed_files=[],
            verification_summary_codes=["TESTS_PASSED"],
            scope_validation_result=self.valid_scope_result,
            contract_hash=self.contract_hash,
            approved_scope_hash=self.approved_scope_hash,
            idempotency_key=self.idempotency_key,
            approval_id=self.approval_id,
        )
        pkg_no_pull = generate_result_package(
            input_data=no_pull_input,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
        )
        self.assertEqual(pkg_no_pull.status, "NEEDS_HUMAN_REVIEW")
        self.assertIn("MISSING_REQUIRED_FIELD", pkg_no_pull.reason_codes)

        # 3. 0, 음수, 비정수 PR 번호 URL 거부
        bad_num_input = ExecutionResultInput(
            task_id=self.task_id,
            session_id=self.session_id,
            branch_name=self.branch_name,
            pr_identifier="https://github.com/BenJLeeKR/orchestrator_jules/pull/0",
            status="COMPLETED",
            changed_files=[],
            verification_summary_codes=["TESTS_PASSED"],
            scope_validation_result=self.valid_scope_result,
            contract_hash=self.contract_hash,
            approved_scope_hash=self.approved_scope_hash,
            idempotency_key=self.idempotency_key,
            approval_id=self.approval_id,
        )
        pkg_bad_num = generate_result_package(
            input_data=bad_num_input,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
        )
        self.assertEqual(pkg_bad_num.status, "NEEDS_HUMAN_REVIEW")
        self.assertIn("MISSING_REQUIRED_FIELD", pkg_bad_num.reason_codes)

        # 4. trailing path가 붙은 URL 거부
        trailing_input = ExecutionResultInput(
            task_id=self.task_id,
            session_id=self.session_id,
            branch_name=self.branch_name,
            pr_identifier="https://github.com/BenJLeeKR/orchestrator_jules/pull/41/files",
            status="COMPLETED",
            changed_files=[],
            verification_summary_codes=["TESTS_PASSED"],
            scope_validation_result=self.valid_scope_result,
            contract_hash=self.contract_hash,
            approved_scope_hash=self.approved_scope_hash,
            idempotency_key=self.idempotency_key,
            approval_id=self.approval_id,
        )
        pkg_trailing = generate_result_package(
            input_data=trailing_input,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
        )
        self.assertEqual(pkg_trailing.status, "NEEDS_HUMAN_REVIEW")
        self.assertIn("MISSING_REQUIRED_FIELD", pkg_trailing.reason_codes)

        # 5. 세션 PR 번호와 URL 경로의 PR 번호 불일치 검증
        mismatched_url_input = ExecutionResultInput(
            task_id=self.task_id,
            session_id=self.session_id,
            branch_name=self.branch_name,
            pr_identifier="https://github.com/BenJLeeKR/orchestrator_jules/pull/99",
            status="COMPLETED",
            changed_files=[],
            verification_summary_codes=["TESTS_PASSED"],
            scope_validation_result=self.valid_scope_result,
            contract_hash=self.contract_hash,
            approved_scope_hash=self.approved_scope_hash,
            idempotency_key=self.idempotency_key,
            approval_id=self.approval_id,
        )
        pkg_mismatch_url = generate_result_package(
            input_data=mismatched_url_input,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
            existing_session=self.existing_session,  # existing_session.pr_number = 41
        )
        self.assertEqual(pkg_mismatch_url.status, "NEEDS_HUMAN_REVIEW")
        self.assertIn("PR_BINDING_MISMATCH", pkg_mismatch_url.reason_codes)

    def test_scope_validation_strict_hash_check(self) -> None:
        """is_valid=True여도 approved_scope_hash가 비어있거나 기대 Scope 해시와 다르면 SCOPE_VALIDATION_FAILED 발생 검증."""
        empty_scope_result = ScopeValidationResult(
            is_valid=True,
            reasons=[],
            approved_scope_hash=None,
        )
        input_empty_scope = ExecutionResultInput(
            task_id=self.task_id,
            session_id=self.session_id,
            branch_name=self.branch_name,
            pr_identifier=self.pr_identifier,
            status="COMPLETED",
            changed_files=["src/orchestrator/result_package.py"],
            verification_summary_codes=["TESTS_PASSED"],
            scope_validation_result=empty_scope_result,
            contract_hash=self.contract_hash,
            approved_scope_hash=self.approved_scope_hash,
            idempotency_key=self.idempotency_key,
            approval_id=self.approval_id,
        )
        pkg_empty = generate_result_package(
            input_data=input_empty_scope,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
        )
        self.assertEqual(pkg_empty.status, "NEEDS_HUMAN_REVIEW")
        self.assertIn("SCOPE_VALIDATION_FAILED", pkg_empty.reason_codes)

    def test_existing_session_task_id_mismatch(self) -> None:
        """기존 세션의 task_id와 입력 task_id 불일치 시 SESSION_BINDING_MISMATCH 처리 검증."""
        mismatched_session = JulesSessionResponse(
            session_id=self.session_id,
            task_id="OTHER-TASK-ID-999",
            branch_name=self.branch_name,
            pr_number=self.pr_identifier,
            status="RUNNING",
            reason_code=None,
            created_at_utc="2026-09-17T00:00:00Z",
            updated_at_utc="2026-09-17T00:00:00Z",
        )

        pkg = generate_result_package(
            input_data=self.valid_input,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
            existing_session=mismatched_session,
        )

        self.assertEqual(pkg.status, "NEEDS_HUMAN_REVIEW")
        self.assertIn("SESSION_BINDING_MISMATCH", pkg.reason_codes)

    def test_absence_of_sensitive_and_authority_fields(self) -> None:
        """패키지 및 to_dict() 결과에 승인/병합 판단 필드 및 민감 정보가 존재하지 않는지 검증."""
        pkg = generate_result_package(
            input_data=self.valid_input,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
        )

        d = pkg.to_dict()

        # 승인/병합/자동실행 권한 판단 필드 부재 확인
        forbidden_fields = ["APPROVED", "CLOSED", "is_dispatch_eligible", "is_mergeable", "auto_merge"]
        for field in forbidden_fields:
            self.assertNotIn(field, d)
            self.assertFalse(hasattr(pkg, field))

        # 민감 키/토큰/로그 필드 부재 확인
        sensitive_fields = ["api_key", "token", "secret", "raw_logs", "prompt_text"]
        for field in sensitive_fields:
            self.assertNotIn(field, d)
            self.assertFalse(hasattr(pkg, field))

    def test_reason_code_format_validation(self) -> None:
        """사유 코드 규격 validation 함수 테스트."""
        self.assertTrue(validate_reason_code_format("VALID_REASON_123"))
        self.assertFalse(validate_reason_code_format("invalid_lowercase"))
        self.assertFalse(validate_reason_code_format("INVALID REASON"))
        self.assertFalse(validate_reason_code_format("A" * 65))
        self.assertFalse(validate_reason_code_format(""))



    def test_existing_session_pr_missing(self) -> None:
        """기존 세션의 pr_number가 None인 경우 PR_BINDING_MISSING 사유 코드가 반환되는지 검증."""
        session_no_pr = JulesSessionResponse(
            session_id=self.session_id,
            task_id=self.task_id,
            branch_name=self.branch_name,
            pr_number=None,
            status="COMPLETED",
            reason_code=None,
            created_at_utc="2026-09-17T00:00:00Z",
            updated_at_utc="2026-09-17T00:00:00Z",
        )

        pkg = generate_result_package(
            input_data=self.valid_input,
            expected_contract_hash=self.contract_hash,
            expected_approved_scope_hash=self.approved_scope_hash,
            expected_idempotency_key=self.idempotency_key,
            expected_approval_id=self.approval_id,
            existing_session=session_no_pr,
        )

        self.assertEqual(pkg.status, "NEEDS_HUMAN_REVIEW")
        self.assertIn("PR_BINDING_MISSING", pkg.reason_codes)

if __name__ == "__main__":
    unittest.main()
