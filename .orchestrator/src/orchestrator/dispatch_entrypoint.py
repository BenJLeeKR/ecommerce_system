"""Orchestrator 최상위 디스패치 인계 진입점 모듈.

이 모듈은 Dispatcher 책임과 의존성 주입 방식을 정의합니다.
TaskContract 및 ApprovalEvidence에서 canonical scope hash 등을 정규화하고
승인 결속, SHA 등을 검증하여 이상이 없으면 세션을 생성합니다.
"""

from typing import Any, Optional, Dict, Tuple
from datetime import datetime, timezone
from .models import TaskContract, ApprovalEvidence, PathItem
from .canonicalization import canonicalize_contract, canonicalize_scope, ScopeCanonicalizationError
from .jules_adapter import JulesSessionRequest, JulesSessionResponse, PreGateResult, validate_source_name
from .policy import evaluate_dispatch_policy
from .plan_session_registration import register_plan_session
from .repository import StateRepository

def execute_dispatch_session(
    contract: TaskContract,
    approval_evidence: ApprovalEvidence,
    source_name: str,
    prompt: str,
    is_session_creation_authorized: bool,
    jules_adapter: Any,
    actual_base_sha: str,
    plan_session_repository: Optional[StateRepository] = None,
) -> JulesSessionResponse:
    """디스패치 진입점 함수.

    contract 및 evidence를 검증하고 실패 시 API 호출 없이 즉시 NEEDS_HUMAN_REVIEW 반환.
    성공 시 jules_adapter.create_session 호출.

    주의: source_name은 JulesSessionRequest 구성에만 전달되며 기록되지 않습니다.
    """
    now = datetime.now(timezone.utc).isoformat()
    error_response = JulesSessionResponse(
        session_id="",
        task_id=contract.task_id,
        branch_name=None,
        pr_number=None,
        status="NEEDS_HUMAN_REVIEW",
        reason_code="PRE_DISPATCH_VALIDATION_FAILED",
        created_at_utc=now,
        updated_at_utc=now
    )

    # 사전 검증 1: task_id 및 contract_version 대조, 명시적 권한 및 source_name 검증
    if contract.task_id != approval_evidence.task_id:
        error_response.reason_code = "TASK_ID_MISMATCH"
        return error_response

    if contract.contract_version != approval_evidence.contract_version:
        error_response.reason_code = "CONTRACT_VERSION_MISMATCH"
        return error_response

    if not is_session_creation_authorized:
        error_response.reason_code = "SESSION_CREATION_NOT_AUTHORIZED"
        return error_response

    if not validate_source_name(source_name):
        error_response.reason_code = "INVALID_SOURCE_NAME"
        return error_response

    # 하드 블록 정책: 승인 증적 ACTIVE 여부, auto_merge, plan_approval_required
    if approval_evidence.status != "ACTIVE":
        error_response.reason_code = "APPROVAL_NOT_ACTIVE"
        return error_response

    if contract.auto_merge:
        error_response.reason_code = "AUTO_MERGE_NOT_ALLOWED"
        return error_response

    if not contract.plan_approval_required:
        error_response.reason_code = "PLAN_APPROVAL_REQUIRED"
        return error_response

    # 사전 검증 2: 해시 정규화 및 대조
    try:
        _, calculated_contract_hash = canonicalize_contract(contract)
        _, calculated_scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
    except (ScopeCanonicalizationError, TypeError, ValueError, AttributeError):
        error_response.reason_code = "SCOPE_CANONICALIZATION_FAILED"
        return error_response

    if calculated_contract_hash != approval_evidence.contract_hash:
        error_response.reason_code = "CONTRACT_HASH_MISMATCH"
        return error_response

    if calculated_scope_hash != approval_evidence.approved_scope_hash:
        error_response.reason_code = "SCOPE_HASH_MISMATCH"
        return error_response

    # 사전 검증 3: 동적 정책 평가 (evaluate_dispatch_policy)
    # is_eligible 값은 PreGateResult에 보존되어 전달되며,
    # 명시적 세션 생성 권한(is_session_creation_authorized)이 있으므로 이 값으로 차단하지 않음.
    is_eligible, _ = evaluate_dispatch_policy(
        contract, calculated_contract_hash, calculated_scope_hash, approval_evidence
    )

    # 사전 검증 4: 기준 SHA 대조
    if contract.base_commit_sha != actual_base_sha:
        error_response.reason_code = "BASE_SHA_MISMATCH"
        return error_response

    # 검증 성공 시 세션 생성
    request = JulesSessionRequest(
        task_id=contract.task_id,
        contract_hash=calculated_contract_hash,
        approved_scope_hash=calculated_scope_hash,
        idempotency_key=contract.idempotency_key,
        base_sha=contract.base_commit_sha,
        allowed_paths=contract.allowed_paths,
        forbidden_paths=contract.forbidden_paths,
        source_name=source_name,
        prompt=prompt
    )

    # 검증 통과 기록을 PreGateResult로 구성하여 실제 어댑터에 전달
    pre_gate_result = PreGateResult(
        is_valid=True,
        is_dispatch_eligible=is_eligible,
        is_session_creation_authorized=is_session_creation_authorized,
        status="APPROVED",
        task_id=contract.task_id,
        contract_hash=calculated_contract_hash,
        approved_scope_hash=calculated_scope_hash,
        idempotency_key=contract.idempotency_key,
        base_sha=contract.base_commit_sha
    )

    # 어댑터 호출: main 브랜치 시작 및 planApprovalRequired=True 정책은
    # RealJulesAdapter 내부에서 HTTP 요청 생성 시 강제/보존됨
    session_response = jules_adapter.create_session(
        request=request,
        pre_gate_result=pre_gate_result
    )

    # Plan 단계 등록은 명시적으로 주입된 저장소와 성공 생성 응답이 있을 때만 수행한다.
    # 등록 실패는 세션 생성 API를 재호출하지 않고 안전 상태로 전이한다.
    if plan_session_repository is None or session_response.status != "CREATED":
        return session_response

    registration_result = register_plan_session(
        repository=plan_session_repository,
        contract=contract,
        approval_evidence=approval_evidence,
        session_response=session_response,
    )
    if registration_result.status == "REGISTERED":
        return session_response

    return JulesSessionResponse(
        session_id=session_response.session_id,
        task_id=session_response.task_id,
        branch_name=session_response.branch_name,
        pr_number=session_response.pr_number,
        status="NEEDS_HUMAN_REVIEW",
        reason_code=registration_result.reason_code or "PLAN_SESSION_REGISTRATION_FAILED",
        created_at_utc=session_response.created_at_utc,
        updated_at_utc=datetime.now(timezone.utc).isoformat(),
    )
