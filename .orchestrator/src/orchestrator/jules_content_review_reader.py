"""수동 Jules 콘텐츠 인계 진입점 모듈.

Codex가 Jules 세션의 생성 활동 원문을 비영속/비로그 방식으로
수동 조회하기 위한 단회성 진입점입니다.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from .models import TaskContract, ApprovalEvidence
from .jules_adapter import JulesSessionResponse, RealJulesAdapter
from .canonicalization import canonicalize_contract, canonicalize_scope, ScopeCanonicalizationError

@dataclass
class ContentReviewRequest:
    """Codex의 명시적 콘텐츠 수동 검토 권한 입력을 담는 비영속/비로그 객체."""
    session_id: str
    task_id: str
    approval_id: str
    contract_hash: str
    approved_scope_hash: str

    def __repr__(self) -> str:
        return "ContentReviewRequest(<REDACTED>)"

    def __str__(self) -> str:
        return self.__repr__()

    def to_dict(self) -> Dict[str, Any]:
        return {"review_request": "<REDACTED>"}

@dataclass
class ContentReviewResult:
    """단회성 콘텐츠 검토 조회 결과를 담는 반환 객체.

    비영속/비로그 원칙을 위해 원문 노출을 방지하는 메서드(마스킹)를 포함합니다.
    """
    status: str
    reason_code: Optional[str] = None
    content_text: Optional[str] = None

    def __repr__(self) -> str:
        return f"ContentReviewResult(status='{self.status}', reason_code={repr(self.reason_code)}, content_text='<REDACTED>')"

    def __str__(self) -> str:
        return self.__repr__()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "reason_code": self.reason_code,
            "content_text": "<REDACTED>" if self.content_text else None
        }

def execute_content_handoff(
    review_request: ContentReviewRequest,
    contract: TaskContract,
    approval_evidence: ApprovalEvidence,
    session_response: JulesSessionResponse,
    jules_adapter: Any
) -> ContentReviewResult:
    """API 호출 전 Contract, 증적, 세션 정보를 검증하고 원문을 조회하는 진입점.

    1. 사전 검증: 세션 ID, Task ID, Approval ID 불일치 및 증적 ACTIVE 확인, 해시 대조.
    2. 어댑터 호출: jules_adapter.fetch_activities_content_only() 호출하여 원문 추출.
    실패 시 API 호출 없이(또는 호출 중단 후) NEEDS_HUMAN_REVIEW 반환.
    """
    # 1. 사전 검증
    if not RealJulesAdapter.validate_session_resource_name(review_request.session_id):
        return ContentReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="INVALID_SESSION_ID_FORMAT")
    if not RealJulesAdapter.validate_session_resource_name(session_response.session_id):
        return ContentReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="INVALID_SESSION_ID_FORMAT")
    if review_request.session_id != session_response.session_id:
        return ContentReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="SESSION_ID_MISMATCH")

    if review_request.task_id != contract.task_id:
        return ContentReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="TASK_ID_MISMATCH")
    if contract.task_id != session_response.task_id:
        return ContentReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="TASK_ID_MISMATCH")
    if contract.task_id != approval_evidence.task_id:
        return ContentReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="TASK_ID_MISMATCH")

    if review_request.approval_id != approval_evidence.approval_id:
        return ContentReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="APPROVAL_ID_MISMATCH")

    if contract.contract_version != approval_evidence.contract_version:
        return ContentReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="CONTRACT_VERSION_MISMATCH")
    if approval_evidence.status != "ACTIVE":
        return ContentReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="APPROVAL_NOT_ACTIVE")

    try:
        _, computed_contract_hash = canonicalize_contract(contract)
        _, computed_scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
    except (ScopeCanonicalizationError, TypeError, ValueError, AttributeError):
        return ContentReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="SCOPE_CANONICALIZATION_FAILED")

    if review_request.contract_hash != computed_contract_hash:
        return ContentReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="CONTRACT_HASH_MISMATCH")
    if computed_contract_hash != approval_evidence.contract_hash:
        return ContentReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="CONTRACT_HASH_MISMATCH")

    if review_request.approved_scope_hash != computed_scope_hash:
        return ContentReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="SCOPE_HASH_MISMATCH")
    if computed_scope_hash != approval_evidence.approved_scope_hash:
        return ContentReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="SCOPE_HASH_MISMATCH")

    # 2. 어댑터를 통한 원문 조회
    try:
        content_text = jules_adapter.fetch_activities_content_only(review_request.session_id)
        if not isinstance(content_text, str) or not content_text:
            return ContentReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="CONTENT_NOT_FOUND")
        return ContentReviewResult(status="CONTENT_READY", content_text=content_text)
    except Exception:
        return ContentReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code="CONTENT_FETCH_FAILED")
