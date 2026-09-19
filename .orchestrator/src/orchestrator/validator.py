"""Task Contract 및 승인 증적을 위한 검증 모듈."""

import re
import unicodedata
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from .models import TaskContract, ApprovalEvidence, ApprovalHistoryItem, ValidationResult, PathItem, ScopeValidationResult
from .markdown_parser import parse_task_contract_markdown, MarkdownParseError
from .canonicalization import canonicalize_scope, canonicalize_contract, ScopeCanonicalizationError, normalize_path_list
from .policy import evaluate_dispatch_policy

ALLOWED_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
UTC_ISO8601_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|\+00:00)$")


def _contains_control_chars_or_whitespace(s: str) -> bool:
    """문자열에 제어문자 또는 공백이 포함되어 있는지 확인합니다."""
    for ch in s:
        if ch.isspace() or unicodedata.category(ch).startswith("C"):
            return True
    return False


def validate_approval_id(approval_id: str, expected_task_id: str) -> Tuple[bool, Optional[str]]:
    """approval_id 형식을 APV-<TASK_ID>-<YYYYMMDD>-<NNN> 규격에 맞춰 검증합니다."""
    if not approval_id:
        return False, "approval_id가 비어 있습니다."

    if _contains_control_chars_or_whitespace(approval_id):
        return False, f"approval_id에 제어문자 또는 공백이 포함되어 있습니다: '{approval_id}'"

    prefix = f"APV-{expected_task_id}-"
    if not approval_id.startswith(prefix):
        return False, f"approval_id가 기대하는 접두어 '{prefix}'로 시작하지 않습니다: '{approval_id}'"

    rest = approval_id[len(prefix):]
    m = re.match(r"^(\d{8})-(\d{3})$", rest)
    if not m:
        return False, f"approval_id 후미 형식이 '<YYYYMMDD>-<NNN>' 규격과 일치하지 않습니다: '{rest}'"

    date_str, seq_str = m.group(1), m.group(2)
    try:
        datetime.strptime(date_str, "%Y%m%d")
    except ValueError:
        return False, f"approval_id의 날짜 부분('{date_str}')이 유효한 달력 날짜가 아닙니다."

    return True, None


def validate_utc_iso8601(timestamp_str: str) -> Tuple[bool, Optional[str]]:
    """시간대가 있는 UTC ISO 8601 형식과 타임스탬프 유효성을 검증합니다."""
    if not timestamp_str:
        return False, "타임스탬프가 비어 있습니다."

    if _contains_control_chars_or_whitespace(timestamp_str):
        return False, f"타임스탬프에 제어문자 또는 공백이 포함되어 있습니다: '{timestamp_str}'"

    if not UTC_ISO8601_REGEX.match(timestamp_str):
        return False, f"유효하지 않은 UTC ISO 8601 형식: '{timestamp_str}'"

    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        if dt.tzinfo is None or dt.utcoffset() != timedelta(0):
            return False, f"유효하지 않은 시간대 (UTC여야 함): '{timestamp_str}'"
    except ValueError as e:
        return False, f"유효하지 않은 타임스탬프: '{timestamp_str}'. {str(e)}"

    return True, None


def validate_task_contract(
    markdown_content: str,
    approval_evidence: Optional[ApprovalEvidence] = None,
    approval_history: Optional[List[ApprovalHistoryItem]] = None
) -> ValidationResult:
    """Task Contract Markdown 내용과 승인 증적을 검증합니다."""
    reasons: List[str] = []

    # 1. Markdown 파싱
    try:
        contract = parse_task_contract_markdown(markdown_content)
    except MarkdownParseError as e:
        return ValidationResult(
            is_valid=False,
            is_dispatch_eligible=False,
            status="NEEDS_HUMAN_REVIEW",
            reasons=[f"Markdown 파싱 오류: {str(e)}"]
        )

    # 2. 필수 필드 존재 여부 및 버전 검증
    if not contract.contract_version:
        reasons.append("필수 필드 누락/형식 오류: Contract 버전 (예: # Task Contract v0.1)")
    elif contract.contract_version != "v0.1":
        reasons.append(f"지원되지 않는 Contract 버전: '{contract.contract_version}'. v0.1만 지원됩니다.")

    if not contract.task_id:
        reasons.append("필수 필드 누락: Task ID")
    if not contract.goal:
        reasons.append("필수 필드 누락: 작업 목표")
    if not contract.target_repository:
        reasons.append("필수 필드 누락: 대상 저장소")
    if not contract.base_branch:
        reasons.append("필수 필드 누락: 기준 브랜치")
    if not contract.base_commit_sha:
        reasons.append("필수 필드 누락: 기준 커밋 SHA")
    if not contract.execution_agent:
        reasons.append("필수 필드 누락: 실행 에이전트")
    if not contract.reference_documents:
        reasons.append("필수 필드 누락: 기준 문서")
    if not contract.allowed_paths:
        reasons.append("필수 필드 누락: 허용 경로")
    if not contract.forbidden_paths:
        reasons.append("필수 필드 누락: 금지 경로")
    if not contract.raw_fields.get("on_path_violation"):
        reasons.append("필수 필드 누락: 허용 경로 검증 실패 시 처리 기준")
    if not contract.completion_conditions:
        reasons.append("필수 필드 누락: 완료 조건")
    if not contract.idempotency_key:
        reasons.append("필수 필드 누락: 중복 실행 방지 기준")
    if not contract.risk_level:
        reasons.append("필수 필드 누락: 위험도")
    if not contract.raw_fields.get("has_auto_merge_key"):
        reasons.append("필수 필드 누락: 병합 설정")
    if not contract.raw_fields.get("has_plan_approval_key"):
        reasons.append("필수 필드 누락: 계획 승인 필요 여부")
    if not contract.cancellation_conditions:
        reasons.append("필수 필드 누락: 취소 조건")
    if not contract.raw_fields.get("approval_status"):
        reasons.append("필수 필드 누락: 승인 상태")
    if not contract.raw_fields.get("approval_evidence_id"):
        reasons.append("필수 필드 누락: 승인 증적 식별자")

    # 3. 형식 유효성 검증
    if contract.risk_level and contract.risk_level.upper() not in ALLOWED_RISK_LEVELS:
        reasons.append(f"유효하지 않은 위험도 형식: '{contract.risk_level}'. LOW|MEDIUM|HIGH|CRITICAL 중 하나여야 합니다.")

    if contract.base_commit_sha and not re.match(r"^[0-9a-f]{40}$", contract.base_commit_sha):
        reasons.append(f"유효하지 않은 기준 커밋 SHA 형식: '{contract.base_commit_sha}'. 40자리 소문자 16진수여야 합니다.")

    auto_merge_raw = contract.raw_fields.get("auto_merge_raw", "")
    if contract.raw_fields.get("has_auto_merge_key") and auto_merge_raw not in ("true", "false"):
        reasons.append(f"유효하지 않은 auto_merge 형식: '{auto_merge_raw}'. 명시적인 true 또는 false여야 합니다.")

    plan_approval_raw = contract.raw_fields.get("plan_approval_raw", "")
    if contract.raw_fields.get("has_plan_approval_key") and plan_approval_raw not in ("true", "false"):
        reasons.append(f"유효하지 않은 plan_approval_required 형식: '{plan_approval_raw}'. 명시적인 true 또는 false여야 합니다.")

    # 4. Scope 및 Contract 정규화 (경로 포맷 검사)
    computed_scope_hash = None
    computed_contract_hash = None

    if contract.allowed_paths or contract.forbidden_paths:
        try:
            _, computed_scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
        except ScopeCanonicalizationError as e:
            reasons.append(f"Scope 정규화 오류: {str(e)}")

    if computed_scope_hash and len(reasons) == 0:
        try:
            _, computed_contract_hash = canonicalize_contract(contract)
        except Exception as e:
            reasons.append(f"Contract 정규화 오류: {str(e)}")

    if reasons:
        return ValidationResult(
            is_valid=False,
            is_dispatch_eligible=False,
            status="NEEDS_HUMAN_REVIEW",
            reasons=reasons,
            contract_hash=computed_contract_hash,
            approved_scope_hash=computed_scope_hash,
            contract=contract
        )

    # 5. 승인 증적 검증 (무결성 및 포맷 검사)
    if approval_evidence is None:
        return ValidationResult(
            is_valid=True,
            is_dispatch_eligible=False,
            status="NEEDS_HUMAN_REVIEW",
            reasons=["승인 증적이 누락되었습니다."],
            contract_hash=computed_contract_hash,
            approved_scope_hash=computed_scope_hash,
            contract=contract
        )

    # 승인 증적 필수 필드 검사
    evidence_reasons = []
    if not approval_evidence.approval_id:
        evidence_reasons.append("승인 증적 필수 필드 누락: approval_id")
    if not approval_evidence.task_id:
        evidence_reasons.append("승인 증적 필수 필드 누락: task_id")
    if not approval_evidence.contract_version:
        evidence_reasons.append("승인 증적 필수 필드 누락: contract_version")
    if not approval_evidence.contract_hash:
        evidence_reasons.append("승인 증적 필수 필드 누락: contract_hash")
    if not approval_evidence.approved_scope_hash:
        evidence_reasons.append("승인 증적 필수 필드 누락: approved_scope_hash")
    if not approval_evidence.approver:
        evidence_reasons.append("승인 증적 필수 필드 누락: approver")
    if not approval_evidence.approval_time_utc:
        evidence_reasons.append("승인 증적 필수 필드 누락: approval_time_utc")
    if not approval_evidence.status:
        evidence_reasons.append("승인 증적 필수 필드 누락: status")

    if approval_evidence.contract_version and approval_evidence.contract_version != contract.contract_version:
        evidence_reasons.append(f"승인 증적 contract_version 불일치. 기대값 '{contract.contract_version}', 실제값 '{approval_evidence.contract_version}'.")

    if approval_evidence.task_id and approval_evidence.task_id != contract.task_id:
        evidence_reasons.append(f"승인 증적 task_id 불일치. 기대값 '{contract.task_id}', 실제값 '{approval_evidence.task_id}'.")

    # approval_id 검증 (APV-<TASK_ID>-<YYYYMMDD>-<NNN>)
    if approval_evidence.approval_id and contract.task_id:
        apv_valid, apv_msg = validate_approval_id(approval_evidence.approval_id, contract.task_id)
        if not apv_valid and apv_msg:
            evidence_reasons.append(apv_msg)
    elif not approval_evidence.approval_id:
        evidence_reasons.append("승인 증적 approval_id가 비어 있습니다.")

    # approval_time_utc 검증
    if approval_evidence.approval_time_utc:
        time_valid, time_msg = validate_utc_iso8601(approval_evidence.approval_time_utc)
        if not time_valid and time_msg:
            evidence_reasons.append(f"approval_time_utc 오류: {time_msg}")

    # 무결성 검사 (해시 일치 확인)
    if approval_evidence.contract_hash != computed_contract_hash:
        evidence_reasons.append(f"승인 증적 contract_hash 불일치 (무결성 실패). 기대값 '{computed_contract_hash}', 실제값 '{approval_evidence.contract_hash}'.")

    if approval_evidence.approved_scope_hash != computed_scope_hash:
        evidence_reasons.append(f"승인 증적 approved_scope_hash 불일치 (무결성 실패). 기대값 '{computed_scope_hash}', 실제값 '{approval_evidence.approved_scope_hash}'.")

    if evidence_reasons:
        return ValidationResult(
            is_valid=False,
            is_dispatch_eligible=False,
            status="NEEDS_HUMAN_REVIEW",
            reasons=evidence_reasons,
            contract_hash=computed_contract_hash,
            approved_scope_hash=computed_scope_hash,
            contract=contract
        )

    # 6. 외부 주입 이력 검증 (BL-PH1-002)
    history_policy_reasons = []

    if approval_history is not None:
        # 특정 approval_id 관련 이력만 필터링하거나 전체 이력을 대상으로 바인딩/시간 검증
        relevant_history = [
            item for item in approval_history
            if item.approval_id == approval_evidence.approval_id
        ] if approval_evidence.approval_id else approval_history

        if not relevant_history:
            history_policy_reasons.append(
                f"승인 식별자 '{approval_evidence.approval_id}'에 해당하는 승인 이력이 존재하지 않습니다."
            )
        else:
            # 1) 이력 항목 필수 필드 및 형식 검증 & 동일 레코드 중복 제거
            unique_records = set()
            for idx, item in enumerate(relevant_history):
                # 필수 필출 존재 여부
                if not item.approval_id or not item.task_id or not item.contract_hash or not item.approved_scope_hash or not item.status or not item.recorded_at_utc:
                    return ValidationResult(
                        is_valid=False,
                        is_dispatch_eligible=False,
                        status="NEEDS_HUMAN_REVIEW",
                        reasons=[f"승인 이력 항목({idx}) 필수 필드 누락"],
                        contract_hash=computed_contract_hash,
                        approved_scope_hash=computed_scope_hash,
                        contract=contract
                    )

                # recorded_at_utc 검증
                time_valid, time_msg = validate_utc_iso8601(item.recorded_at_utc)
                if not time_valid:
                    return ValidationResult(
                        is_valid=False,
                        is_dispatch_eligible=False,
                        status="NEEDS_HUMAN_REVIEW",
                        reasons=[f"승인 이력 recorded_at_utc 오류: {time_msg}"],
                        contract_hash=computed_contract_hash,
                        approved_scope_hash=computed_scope_hash,
                        contract=contract
                    )

                # 바인딩 검증 (task_id, contract_hash, approved_scope_hash가 기대값/Contract/Scope와 일치해야 함)
                if item.task_id != contract.task_id or item.contract_hash != computed_contract_hash or item.approved_scope_hash != computed_scope_hash:
                    return ValidationResult(
                        is_valid=False,
                        is_dispatch_eligible=False,
                        status="NEEDS_HUMAN_REVIEW",
                        reasons=[
                            f"승인 이력 바인딩 불일치 (approval_id: '{item.approval_id}'). "
                            f"기대 Task ID '{contract.task_id}', 실제 '{item.task_id}'; "
                            f"기대 Contract Hash '{computed_contract_hash}', 실제 '{item.contract_hash}'; "
                            f"기대 Scope Hash '{computed_scope_hash}', 실제 '{item.approved_scope_hash}'."
                        ],
                        contract_hash=computed_contract_hash,
                        approved_scope_hash=computed_scope_hash,
                        contract=contract
                    )

                # approval_id 형식 검증
                apv_valid, apv_msg = validate_approval_id(item.approval_id, contract.task_id)
                if not apv_valid:
                    return ValidationResult(
                        is_valid=False,
                        is_dispatch_eligible=False,
                        status="NEEDS_HUMAN_REVIEW",
                        reasons=[f"승인 이력 approval_id 형식 오류: {apv_msg}"],
                        contract_hash=computed_contract_hash,
                        approved_scope_hash=computed_scope_hash,
                        contract=contract
                    )

                record_tuple = (item.approval_id, item.task_id, item.contract_hash, item.approved_scope_hash, item.status, item.recorded_at_utc)
                unique_records.add(record_tuple)

            # 2) 동일 시각 상충 검사: 동일 (approval_id, recorded_at_utc)를 가지면서 record_tuple이 다른 상충 이력 확인
            time_map = {}
            for rec in unique_records:
                app_id, t_id, c_hash, s_hash, st, rec_time = rec
                if rec_time in time_map:
                    # 동일 시각에 서로 다른 상태나 결속 존재 -> 상충 이력
                    return ValidationResult(
                        is_valid=False,
                        is_dispatch_eligible=False,
                        status="NEEDS_HUMAN_REVIEW",
                        reasons=[
                            f"동일 승인 식별자 '{app_id}' 및 동일 UTC 시각 '{rec_time}'에 상충되는 승인 이력이 존재합니다."
                        ],
                        contract_hash=computed_contract_hash,
                        approved_scope_hash=computed_scope_hash,
                        contract=contract
                    )
                time_map[rec_time] = rec

            # 3) 최신 상태 확인 (ISO 8601 문자열 정렬 또는 datetime 비교)
            # recorded_at_utc 기준 정렬하여 가장 최근 기록 확인
            sorted_history = sorted(
                relevant_history,
                key=lambda x: datetime.fromisoformat(x.recorded_at_utc.replace("Z", "+00:00"))
            )
            latest_item = sorted_history[-1]

            if latest_item.status != "ACTIVE":
                if latest_item.status in ("WITHDRAWN", "MODIFIED", "EXPIRED"):
                    history_policy_reasons.append(
                        f"최신 승인 이력 상태가 '{latest_item.status}'입니다 (ACTIVE만 허용)."
                    )
                else:
                    history_policy_reasons.append(
                        f"알 수 없는 승인 이력 상태 '{latest_item.status}'입니다."
                    )

    # 7. Dispatch 정책 평가
    is_dispatch_eligible, policy_reasons = evaluate_dispatch_policy(
        contract=contract,
        computed_contract_hash=computed_contract_hash,
        computed_scope_hash=computed_scope_hash,
        approval_evidence=approval_evidence
    )

    all_policy_reasons = policy_reasons + history_policy_reasons
    final_dispatch_eligible = is_dispatch_eligible and (len(history_policy_reasons) == 0)

    status = "APPROVED" if final_dispatch_eligible else "NEEDS_HUMAN_REVIEW"

    return ValidationResult(
        is_valid=True,
        is_dispatch_eligible=final_dispatch_eligible,
        status=status,
        reasons=all_policy_reasons,
        contract_hash=computed_contract_hash,
        approved_scope_hash=computed_scope_hash,
        contract=contract
    )


def _is_path_matching(file_path: str, item_path: str, kind: str) -> bool:
    """단일 변경 파일 경로가 PathItem(path, kind) 범위에 매칭되는지 확인합니다.

    kind가 'file'인 경우: file_path == item_path
    kind가 'directory_recursive'인 경우: file_path == item_path 또는 file_path.startswith(item_path + "/")
    """
    if kind == "file":
        return file_path == item_path
    elif kind == "directory_recursive":
        return file_path == item_path or file_path.startswith(item_path + "/")
    return False


def _validate_single_changed_path_format(file_path: str) -> bool:
    """변경 파일 경로 단건의 문자열 형식을 검증합니다.

    거부 대상:
    - 비어 있거나 타입이 str이 아님
    - 앞뒤 공백 존재 (strip 전후가 다름)
    - 제어문자 포함
    - 절대 경로 ('/' 또는 '\'로 시작)
    - 윈도우 역슬래시 ('\' 포함)
    - '.' 또는 '..' 세그먼트 포함
    """
    if not isinstance(file_path, str) or not file_path:
        return False
    if file_path.strip() != file_path:
        return False
    if _contains_control_chars_or_whitespace(file_path):
        return False
    if file_path.startswith("/") or file_path.startswith("\\"):
        return False
    if "\\" in file_path:
        return False
    segments = file_path.split("/")
    for seg in segments:
        if seg == "." or seg == "..":
            return False
    return True


def validate_scope_lock_pre_dispatch(
    allowed_paths: List[PathItem],
    forbidden_paths: List[PathItem],
    expected_approved_scope_hash: str
) -> ScopeValidationResult:
    """Dispatch 전 Task Contract의 허용/금지 경로를 Scope Lock으로 정규화 및 해시 검증합니다.

    실패 사유 코드:
    - SCOPE_LOCK_CANONICALIZATION_FAILED: 경로 형식 오류 또는 정규화 실패
    - SCOPE_HASH_MISMATCH: 정규화 산출 해시와 승인된 Scope 해시 불일치 (누락, 빈값, 불일치)
    """
    try:
        _, computed_scope_hash = canonicalize_scope(allowed_paths, forbidden_paths)
    except ScopeCanonicalizationError:
        return ScopeValidationResult(
            is_valid=False,
            reasons=["SCOPE_LOCK_CANONICALIZATION_FAILED"],
            approved_scope_hash=None
        )

    if not expected_approved_scope_hash or expected_approved_scope_hash != computed_scope_hash:
        return ScopeValidationResult(
            is_valid=False,
            reasons=["SCOPE_HASH_MISMATCH"],
            approved_scope_hash=computed_scope_hash
        )

    return ScopeValidationResult(
        is_valid=True,
        reasons=[],
        approved_scope_hash=computed_scope_hash
    )


def validate_changed_files_against_scope_lock(
    changed_files: List[str],
    allowed_paths: List[PathItem],
    forbidden_paths: List[PathItem],
    expected_approved_scope_hash: str
) -> ScopeValidationResult:
    """결과 수집 후 외부 주입 변경 파일 경로 목록을 동일 Scope Lock으로 재검증합니다.

    실패 사유 코드:
    - SCOPE_LOCK_CANONICALIZATION_FAILED: Scope Lock 정규화 실패
    - SCOPE_HASH_MISMATCH: 승인 Scope 해시 누락, 빈값, 불일치
    - SCOPE_PATH_FORMAT_INVALID: 절대 경로, 역슬래시, '.', '..', 빈 문자열 등 포맷 오류
    - SCOPE_PATH_FORBIDDEN_VIOLATION: 금지 경로 범위 포함 (금지 경로 우선 판정)
    - SCOPE_PATH_OUT_OF_BOUNDS: 허용 경로 범위 미포함
    """
    reasons: List[str] = []

    # 1. Scope Lock 정규화 및 승인 해시 검증
    try:
        norm_allowed = normalize_path_list(allowed_paths)
        norm_forbidden = normalize_path_list(forbidden_paths)
        _, computed_scope_hash = canonicalize_scope(allowed_paths, forbidden_paths)
    except ScopeCanonicalizationError:
        return ScopeValidationResult(
            is_valid=False,
            reasons=["SCOPE_LOCK_CANONICALIZATION_FAILED"],
            approved_scope_hash=None
        )

    if not expected_approved_scope_hash or computed_scope_hash != expected_approved_scope_hash:
        return ScopeValidationResult(
            is_valid=False,
            reasons=["SCOPE_HASH_MISMATCH"],
            approved_scope_hash=computed_scope_hash
        )

    if changed_files is None or not isinstance(changed_files, list):
        return ScopeValidationResult(
            is_valid=False,
            reasons=["SCOPE_PATH_FORMAT_INVALID"],
            approved_scope_hash=computed_scope_hash
        )

    # 2. 변경 파일 목록 검증
    for file_path in changed_files:
        # 1) 파일 경로 단건 포맷 검증
        if not _validate_single_changed_path_format(file_path):
            if "SCOPE_PATH_FORMAT_INVALID" not in reasons:
                reasons.append("SCOPE_PATH_FORMAT_INVALID")
            continue

        # 2) 금지 경로 검사 (금지 경로 우선 판정)
        is_forbidden = False
        for f_item in norm_forbidden:
            if _is_path_matching(file_path, f_item["path"], f_item["kind"]):
                is_forbidden = True
                break

        if is_forbidden:
            if "SCOPE_PATH_FORBIDDEN_VIOLATION" not in reasons:
                reasons.append("SCOPE_PATH_FORBIDDEN_VIOLATION")
            continue

        # 3) 허용 경로 검사
        is_allowed = False
        for a_item in norm_allowed:
            if _is_path_matching(file_path, a_item["path"], a_item["kind"]):
                is_allowed = True
                break

        if not is_allowed:
            if "SCOPE_PATH_OUT_OF_BOUNDS" not in reasons:
                reasons.append("SCOPE_PATH_OUT_OF_BOUNDS")

    if reasons:
        return ScopeValidationResult(
            is_valid=False,
            reasons=reasons,
            approved_scope_hash=computed_scope_hash
        )

    return ScopeValidationResult(
        is_valid=True,
        reasons=[],
        approved_scope_hash=computed_scope_hash
    )
