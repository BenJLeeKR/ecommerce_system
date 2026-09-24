"""수동 Plan 검토 조회 인터페이스.

Codex가 Jules 세션의 최신 Plan 원문을 정확히 일회 조회하여 검토하기 위한
단회성(One-shot) 수동 진입점입니다. 자동화(승인/병합 등) 기능은 배제되며,
PR 생성 이전이므로 1:1:1 결속(Session:Branch:PR)은 유예하고 실제 세션 생성
결과와 Contract/증적만을 엄격히 대조합니다.

비영속 및 비로그 원칙에 따라 조회된 Plan 원문은 오직 반환 객체에만 담기며,
__repr__, __str__, to_dict 호출 시 마스킹되어 로그, DB, 문서 등에 노출되지 않습니다.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from .models import TaskContract, ApprovalEvidence
from .jules_adapter import JulesSessionResponse, RealJulesAdapter
from .canonicalization import canonicalize_contract, canonicalize_scope, ScopeCanonicalizationError

@dataclass
class ManualReviewRequest:
    """Codex의 명시적 수동 검토 권한 입력을 담는 비영속/비로그 객체.

    이 객체의 데이터는 로그나 영구 저장소에 기록되지 않아야 하며,
    검증 시에만 사용됩니다.
    """
    session_id: str
    task_id: str
    approval_id: str
    contract_hash: str
    approved_scope_hash: str

    def __repr__(self) -> str:
        return "ManualReviewRequest(<REDACTED>)"

    def __str__(self) -> str:
        return self.__repr__()

    def to_dict(self) -> Dict[str, Any]:
        return {"review_request": "<REDACTED>"}

@dataclass
class PlanReviewResult:
    """단회성 Plan 검토 조회 결과를 담는 반환 객체.

    비영속/비로그 원칙을 위해 원문 노출을 방지하는 메서드(마스킹)를 포함합니다.
    """
    status: str
    reason_code: Optional[str] = None
    plan_text: Optional[str] = None

    def __repr__(self) -> str:
        return f"PlanReviewResult(status='{self.status}', reason_code={repr(self.reason_code)}, plan_text='<REDACTED>')"

    def __str__(self) -> str:
        return self.__repr__()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "reason_code": self.reason_code,
            "plan_text": "<REDACTED>" if self.plan_text else None
        }


def execute_manual_plan_review_reader(
    review_request: ManualReviewRequest,
    contract: TaskContract,
    approval_evidence: ApprovalEvidence,
    session_response: JulesSessionResponse,
    jules_adapter: Any
) -> PlanReviewResult:
    """PR 전 수동 Plan 검토를 위한 단회성 조회 진입점.

    1. 사전 검증:
       - review_request 세션 ID == session_response.session_id
       - review_request.task_id == contract.task_id == session_response.task_id == approval_evidence.task_id
       - review_request.approval_id == approval_evidence.approval_id
       - contract.plan_approval_required == True
       - contract.contract_version == approval_evidence.contract_version
       - ApprovalEvidence.status == "ACTIVE"
       - 계산된 contract/scope 해시가 review_request 및 approval_evidence의 값과 정확히 일치
    2. jules_adapter의 전용 조회 경계(fetch_plan_text_only)를 호출하여 원문 획득.

    실패 시 API 호출 없이 NEEDS_HUMAN_REVIEW 반환.
    """
    # 1. 사전 검증
    # a. 세션 ID 형식 및 대조
    if not RealJulesAdapter.validate_session_resource_name(review_request.session_id):
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="INVALID_SESSION_ID_FORMAT")
    if not RealJulesAdapter.validate_session_resource_name(session_response.session_id):
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="INVALID_SESSION_ID_FORMAT")
    if review_request.session_id != session_response.session_id:
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="SESSION_ID_MISMATCH")

    # b. Task ID 대조
    if review_request.task_id != contract.task_id:
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="TASK_ID_MISMATCH")
    if contract.task_id != session_response.task_id:
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="TASK_ID_MISMATCH")
    if contract.task_id != approval_evidence.task_id:
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="TASK_ID_MISMATCH")

    # c. Approval ID 대조
    if review_request.approval_id != approval_evidence.approval_id:
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="APPROVAL_ID_MISMATCH")

    # d. Contract Version 및 Evidence 상태 검증
    if contract.contract_version != approval_evidence.contract_version:
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="CONTRACT_VERSION_MISMATCH")
    if approval_evidence.status != "ACTIVE":
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="APPROVAL_NOT_ACTIVE")

    if not contract.plan_approval_required:
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="PLAN_APPROVAL_NOT_REQUIRED")
    if contract.auto_merge:
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="AUTO_MERGE_NOT_ALLOWED")

    # e. 정규화 및 해시 대조
    try:
        _, computed_contract_hash = canonicalize_contract(contract)
        _, computed_scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
    except (ScopeCanonicalizationError, TypeError, ValueError, AttributeError):
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="SCOPE_CANONICALIZATION_FAILED")

    if review_request.contract_hash != computed_contract_hash:
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="CONTRACT_HASH_MISMATCH")
    if computed_contract_hash != approval_evidence.contract_hash:
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="CONTRACT_HASH_MISMATCH")

    if review_request.approved_scope_hash != computed_scope_hash:
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="SCOPE_HASH_MISMATCH")
    if computed_scope_hash != approval_evidence.approved_scope_hash:
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="SCOPE_HASH_MISMATCH")

    # 2. 전용 조회 경계를 통한 원문 획득
    try:
        plan_text = jules_adapter.fetch_plan_text_only(review_request.session_id)
        if not isinstance(plan_text, str) or not plan_text:
             return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="PLAN_NOT_FOUND")
        return PlanReviewResult(status="PLAN_READY", plan_text=plan_text)
    except Exception:
        # API 오류, 형식 오류 등 모든 예외 상황 시 추정/대체 탐색 중단
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="PLAN_FETCH_FAILED")
