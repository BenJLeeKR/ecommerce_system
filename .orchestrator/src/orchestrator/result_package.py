"""Codex 검토 대기용 결과 패키지 생성기."""

import re
from typing import List, Optional, Any, Tuple
from urllib.parse import urlparse
from .models import (
    ExecutionResultInput,
    CodexReviewResultPackage,
    ScopeValidationResult,
)
from .jules_adapter import JulesSessionResponse

REASON_CODE_REGEX = re.compile(r"^[A-Z0-9_]{1,64}$")


def validate_reason_code_format(code: str) -> bool:
    """사유 코드가 1~64자 대문자, 숫자, 언더스코어 규격을 준수하는지 확인합니다."""
    if not code or not isinstance(code, str):
        return False
    return bool(REASON_CODE_REGEX.match(code))


def _extract_and_validate_pr_url(pr_url: str) -> Tuple[bool, Optional[int]]:
    """PR URL이 https://<host>/<owner>/<repo>/pull/<양의 정수> 형식인지 확인하고 PR 번호를 반환합니다."""
    if not isinstance(pr_url, str):
        return False, None
    s = pr_url.strip()
    if not s.startswith("https://"):
        return False, None

    try:
        parsed = urlparse(s)
        if parsed.scheme != "https" or not parsed.netloc:
            return False, None

        # path: /<owner>/<repo>/pull/<number>
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) != 4:
            return False, None

        owner, repo, pull_keyword, num_str = parts
        if pull_keyword != "pull":
            return False, None

        if not num_str.isdigit():
            return False, None

        pr_num = int(num_str)
        if pr_num <= 0:
            return False, None

        return True, pr_num
    except Exception:
        return False, None


def _is_valid_pr_identifier(pr_id: Any) -> Tuple[bool, Optional[int]]:
    """PR 식별자가 양의 정수 또는 https://<host>/<owner>/<repo>/pull/<양의 정수> PR URL인지 검증합니다."""
    if pr_id is None:
        return False, None
    if isinstance(pr_id, int):
        if pr_id > 0:
            return True, pr_id
        return False, None
    if isinstance(pr_id, str):
        return _extract_and_validate_pr_url(pr_id)
    return False, None


def _is_empty_str(val: Optional[str]) -> bool:
    if val is None:
        return True
    if isinstance(val, str):
        return len(val.strip()) == 0
    return False


def _sanitize_reason_codes(raw_reasons: List[str]) -> Tuple[List[str], bool]:
    """사유 코드를 ^[A-Z0-9_]{1,64}$ 검증하여 정규화 및 중복제거/정렬하고, 무효한 사유 코드가 존재했는지 여부를 반환합니다."""
    valid_reasons = []
    seen = set()
    has_invalid = False
    for r in raw_reasons:
        if isinstance(r, str) and validate_reason_code_format(r):
            if r not in seen:
                seen.add(r)
                valid_reasons.append(r)
        else:
            has_invalid = True
    valid_reasons.sort()
    return valid_reasons, has_invalid


def generate_result_package(
    input_data: ExecutionResultInput,
    expected_contract_hash: str,
    expected_approved_scope_hash: str,
    expected_idempotency_key: str,
    expected_approval_id: str,
    existing_session: Optional[JulesSessionResponse] = None,
) -> CodexReviewResultPackage:
    """외부 주입 실행 결과 데이터를 검증하고 Codex 검토 대기용 패키지를 생성합니다.

    - 필수 입력 누락 시: 'MISSING_REQUIRED_FIELD'
    - 검증 요약 코드 입력 무효 시: 'VERIFICATION_SUMMARY_INVALID'
    - 세션/브랜치/PR 결속 불일치 시: 'SESSION_BINDING_MISMATCH', 'BRANCH_BINDING_MISMATCH', 'PR_BINDING_MISMATCH'
    - 승인 바인딩 불일치 시: 'BINDING_MISMATCH'
    - Scope 검증 실패 시: 'SCOPE_VALIDATION_FAILED'
    - 정상 결과 시: status = 'RESULT_COLLECTED'
    - 실패 결과 시: status = 'NEEDS_HUMAN_REVIEW' 및 구조화 사유 코드 포함
    """
    reasons: List[str] = []

    # 1. 필수 입력 검증
    is_valid_pr, extracted_pr_num = _is_valid_pr_identifier(input_data.pr_identifier)

    if (
        _is_empty_str(input_data.task_id)
        or _is_empty_str(input_data.session_id)
        or _is_empty_str(input_data.branch_name)
        or not is_valid_pr
        or _is_empty_str(input_data.status)
        or input_data.verification_summary_codes is None
        or input_data.scope_validation_result is None
        or _is_empty_str(input_data.contract_hash)
        or _is_empty_str(input_data.approved_scope_hash)
        or _is_empty_str(input_data.idempotency_key)
        or _is_empty_str(input_data.approval_id)
    ):
        reasons.append("MISSING_REQUIRED_FIELD")

    # 2. 검증 요약 코드(verification_summary_codes) 검증
    sanitized_v_codes = []
    if not isinstance(input_data.verification_summary_codes, list) or len(input_data.verification_summary_codes) == 0:
        reasons.append("VERIFICATION_SUMMARY_INVALID")
    else:
        v_codes_clean, v_has_invalid = _sanitize_reason_codes(input_data.verification_summary_codes)
        if v_has_invalid or len(v_codes_clean) == 0:
            reasons.append("VERIFICATION_SUMMARY_INVALID")
        else:
            sanitized_v_codes = v_codes_clean

    # 3. 세션, 브랜치, PR 바인딩 검증 (existing_session 이 제공된 경우)
    if existing_session is not None:
        if existing_session.task_id and existing_session.task_id != input_data.task_id:
            reasons.append("SESSION_BINDING_MISMATCH")

        if existing_session.session_id and existing_session.session_id != input_data.session_id:
            reasons.append("SESSION_BINDING_MISMATCH")

        if existing_session.branch_name and existing_session.branch_name != input_data.branch_name:
            reasons.append("BRANCH_BINDING_MISMATCH")

        if existing_session.pr_number is None:
            reasons.append("PR_BINDING_MISSING")
        else:
            if not is_valid_pr or extracted_pr_num != existing_session.pr_number:
                reasons.append("PR_BINDING_MISMATCH")

    # 4. 승인 바인딩 검증
    if (
        input_data.contract_hash != expected_contract_hash
        or input_data.approved_scope_hash != expected_approved_scope_hash
        or input_data.idempotency_key != expected_idempotency_key
        or input_data.approval_id != expected_approval_id
    ):
        reasons.append("BINDING_MISMATCH")

    # 5. Scope Lock 검증 결과 확인
    sanitized_scope_validation_result: Optional[ScopeValidationResult] = None

    if input_data.scope_validation_result is None:
        if "MISSING_REQUIRED_FIELD" not in reasons:
            reasons.append("MISSING_REQUIRED_FIELD")
    else:
        scope_res = input_data.scope_validation_result
        scope_reasons_clean, scope_has_invalid = _sanitize_reason_codes(scope_res.reasons or [])

        # Scope 성공 조건:
        # is_valid=True 여도 approved_scope_hash 가 비어있거나 기대 해시와 다르면 SCOPE_VALIDATION_FAILED
        if (
            not scope_res.is_valid
            or not scope_res.approved_scope_hash
            or scope_res.approved_scope_hash != expected_approved_scope_hash
            or scope_has_invalid
        ):
            reasons.append("SCOPE_VALIDATION_FAILED")
            sanitized_scope_validation_result = ScopeValidationResult(
                is_valid=False,
                reasons=scope_reasons_clean,
                approved_scope_hash=scope_res.approved_scope_hash,
            )
        else:
            sanitized_scope_validation_result = ScopeValidationResult(
                is_valid=True,
                reasons=scope_reasons_clean,
                approved_scope_hash=scope_res.approved_scope_hash,
            )

    # 6. 사유 코드 정규화, 중복 제거 및 정렬
    valid_reasons, _ = _sanitize_reason_codes(reasons)

    # 7. 최종 상태 결정
    if valid_reasons:
        package_status = "NEEDS_HUMAN_REVIEW"
    else:
        package_status = "RESULT_COLLECTED"

    return CodexReviewResultPackage(
        task_id=input_data.task_id or "",
        session_id=input_data.session_id or "",
        branch_name=input_data.branch_name or "",
        pr_identifier=input_data.pr_identifier,
        status=package_status,
        changed_files=input_data.changed_files or [],
        verification_summary_codes=sanitized_v_codes,
        scope_validation_result=sanitized_scope_validation_result,
        contract_hash=input_data.contract_hash or "",
        approved_scope_hash=input_data.approved_scope_hash or "",
        idempotency_key=input_data.idempotency_key or "",
        approval_id=input_data.approval_id or "",
        reason_codes=valid_reasons,
    )
