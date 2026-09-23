"""Orchestrator 최상위 디스패치 인계 진입점 모듈.

이 모듈은 Dispatcher 책임과 의존성 주입 방식을 정의합니다.
TaskContract 및 ApprovalEvidence에서 canonical scope hash 등을 정규화하고
승인 결속, SHA 등을 검증하여 이상이 없으면 세션을 생성합니다.
"""

from typing import Any, Optional, Dict, Tuple
from .models import TaskContract, ApprovalEvidence, PathItem
from .canonicalization import canonicalize_contract, canonicalize_scope, ScopeCanonicalizationError
from .jules_adapter import JulesSessionRequest, JulesSessionResponse

def execute_dispatch_session(
    contract: TaskContract,
    approval_evidence: ApprovalEvidence,
    source_name: str,
    jules_adapter: Any,
    actual_base_sha: str
) -> JulesSessionResponse:
    """디스패치 진입점 함수.

    contract 및 evidence를 검증하고 실패 시 API 호출 없이 즉시 NEEDS_HUMAN_REVIEW 반환.
    성공 시 jules_adapter.create_session 호출.

    주의: source_name은 JulesSessionRequest 구성에만 전달되며 기록되지 않습니다.
    """
    error_response = JulesSessionResponse(
        session_id="",
        task_id=contract.task_id,
        branch_name=None,
        pr_number=None,
        status="NEEDS_HUMAN_REVIEW",
        reason_code="PRE_DISPATCH_VALIDATION_FAILED",
        created_at_utc="",  # 실제 어댑터에서는 now를 쓰지만 여기서는 에러용 빈값 또는 모의값
        updated_at_utc=""
    )

    # 사전 검증 1: 승인 상태 및 정책
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
        calculated_contract_hash = canonicalize_contract(contract)
        calculated_scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
    except ScopeCanonicalizationError:
        error_response.reason_code = "SCOPE_CANONICALIZATION_FAILED"
        return error_response

    if calculated_contract_hash != approval_evidence.contract_hash:
        error_response.reason_code = "CONTRACT_HASH_MISMATCH"
        return error_response

    if calculated_scope_hash != approval_evidence.approved_scope_hash:
        error_response.reason_code = "SCOPE_HASH_MISMATCH"
        return error_response

    # 사전 검증 3: 기준 SHA 대조
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
        prompt=""
    )

    # RealJulesAdapter 또는 Mock Adapter를 통한 호출
    # 시작 브랜치는 main, planApprovalRequired는 True로 강제/보존됨을 가정
    return jules_adapter.create_session(
        request=request,
        start_branch_name="main",
        plan_approval_required=True
    )
