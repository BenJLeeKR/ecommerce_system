"""Jules Interactive Plan 단일 수동 검토 진입점.

외부 StateRepository에 비민감하게 등록된 Plan 세션을 Contract/ApprovalEvidence와
대조하여 검증한 후, 단일 책임의 기존 Plan 원문 조회 Reader로 위임합니다.
"""

from dataclasses import dataclass
from typing import Any, Dict

from .models import TaskContract, ApprovalEvidence
from .canonicalization import canonicalize_contract, canonicalize_scope, ScopeCanonicalizationError
from .repository import StateRepository, RepositoryError
from .jules_adapter import JulesHttpTransport
from .plan_review_reader import (
    ManualReviewRequest,
    PlanReviewResult,
    execute_manual_plan_review_reader,
)
from .plan_session_registration import get_plan_session_registration

@dataclass(frozen=True)
class ManualPlanReviewRequest:
    """수동 Plan 검토를 위한 비영속적 명시적 요청 객체."""
    task_id: str
    approval_id: str
    contract_hash: str
    approved_scope_hash: str
    session_id: str

    def __repr__(self) -> str:
        return "<ManualPlanReviewRequest: <REDACTED>>"

    def __str__(self) -> str:
        return "<ManualPlanReviewRequest: <REDACTED>>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": "<REDACTED>",
            "approval_id": "<REDACTED>",
            "contract_hash": "<REDACTED>",
            "approved_scope_hash": "<REDACTED>",
            "session_id": "<REDACTED>",
        }


def _failure(reason_code: str) -> PlanReviewResult:
    return PlanReviewResult(status="NEEDS_HUMAN_REVIEW", reason_code=reason_code)


def execute_manual_registered_plan_review(
    *,
    repository: StateRepository,
    transport: JulesHttpTransport,
    contract: TaskContract,
    approval_evidence: ApprovalEvidence,
    review_request: ManualPlanReviewRequest,
) -> PlanReviewResult:
    """등록된 Plan 세션을 검증한 후, 수동 Plan 검토 Reader로 위임합니다.

    주의: 이 진입점은 Pre-PR 단계이므로 최종 Session-Branch-PR 1:1:1 결속
    검사는 유예합니다. 이는 기존 최종 결속의 의미를 변경하지 않습니다.
    """
    # 1. 사전 정책 검증 (Pre-validation)
    if approval_evidence.status != "ACTIVE":
        return _failure("APPROVAL_NOT_ACTIVE")
    if not contract.plan_approval_required:
        return _failure("PLAN_APPROVAL_REQUIRED")
    if contract.auto_merge:
        return _failure("AUTO_MERGE_NOT_ALLOWED")

    # 2. 계약 및 승인 해시 검증
    if contract.task_id != review_request.task_id or contract.task_id != approval_evidence.task_id:
        return _failure("TASK_ID_MISMATCH")
    if approval_evidence.approval_id != review_request.approval_id:
        return _failure("APPROVAL_ID_MISMATCH")

    try:
        _, contract_hash = canonicalize_contract(contract)
        _, scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
    except (ScopeCanonicalizationError, TypeError, ValueError, AttributeError):
        return _failure("SCOPE_CANONICALIZATION_FAILED")

    if contract_hash != review_request.contract_hash or contract_hash != approval_evidence.contract_hash:
        return _failure("CONTRACT_HASH_MISMATCH")

    if scope_hash != review_request.approved_scope_hash or scope_hash != approval_evidence.approved_scope_hash:
        return _failure("SCOPE_HASH_MISMATCH")

    # 3. 저장소에서 Plan-session registration(등록) 정확히 1회 조회
    registration_result = get_plan_session_registration(repository=repository, task_id=contract.task_id)
    if registration_result.status != "REGISTERED" or registration_result.registration is None:
        return _failure(registration_result.reason_code or "PLAN_SESSION_NOT_REGISTERED")

    registration = registration_result.registration

    # 4. 조회된 등록 정보와 요청 정보 대조
    if (registration.task_id != review_request.task_id or
        registration.approval_id != review_request.approval_id or
        registration.contract_hash != review_request.contract_hash or
        registration.approved_scope_hash != review_request.approved_scope_hash or
        registration.session_id != review_request.session_id):
        return _failure("REGISTRATION_MISMATCH")

    # 5. 기존 Reader로 위임
    # ManualReviewRequest 생성 후 execute_manual_plan_review_reader 호출
    reader_request = ManualReviewRequest(
        task_id=review_request.task_id,
        approval_id=review_request.approval_id,
        contract_hash=review_request.contract_hash,
        approved_scope_hash=review_request.approved_scope_hash,
        session_id=review_request.session_id,
    )

    return execute_manual_plan_review_reader(
        transport=transport,
        contract=contract,
        approval_evidence=approval_evidence,
        review_request=reader_request,
    )
