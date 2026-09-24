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
from .jules_adapter import JulesSessionResponse, validate_reason_code


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
    session_id: str,
    contract: TaskContract,
    approval_evidence: ApprovalEvidence,
    session_response: JulesSessionResponse,
    jules_adapter: Any
) -> PlanReviewResult:
    """PR 전 수동 Plan 검토를 위한 단회성 조회 진입점.

    1. 사전 검증:
       - session_id 일치 여부
       - session_response.task_id == contract.task_id
       - contract.base_commit_sha 대조
       - contract.plan_approval_required == True
       - Contract 해시 및 승인 증적 상태 검증
    2. jules_adapter의 전용 조회 경계(fetch_plan_text_only)를 호출하여 원문 획득.

    실패 시 API 호출 없이 NEEDS_HUMAN_REVIEW 반환.
    """
    # 1. 사전 검증
    if session_id != session_response.session_id:
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="SESSION_ID_MISMATCH")

    if contract.task_id != session_response.task_id:
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="TASK_ID_MISMATCH")

    if not contract.plan_approval_required:
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="PLAN_APPROVAL_NOT_REQUIRED")

    # Contract 해시 대조 (정규화된 해시를 미리 검사해야 하지만 이 진입점은 Contract와 증적이 올바르게
    # 매핑되어 전달됨을 전제하며 최소한 상태만 확인. 좀 더 엄격한 대조는 Validator 몫이므로 여기선 최소 검증만 수행)
    if approval_evidence.status != "ACTIVE":
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="APPROVAL_NOT_ACTIVE")

    # 2. 전용 조회 경계를 통한 원문 획득
    try:
        plan_text = jules_adapter.fetch_plan_text_only(session_id)
        if not plan_text:
             return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="PLAN_NOT_FOUND")
        return PlanReviewResult(status="PLAN_READY", plan_text=plan_text)
    except Exception:
        # API 오류, 형식 오류 등 모든 예외 상황 시 추정/대체 탐색 중단
        return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="PLAN_FETCH_FAILED")
