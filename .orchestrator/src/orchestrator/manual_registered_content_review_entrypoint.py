"""Jules Interactive Session 명시적 Pre-PR 수동 콘텐츠 검토 진입점.

외부 StateRepository에 등록된 세션을 Contract/ApprovalEvidence와
대조하여 검증한 후, 기존의 Content Review Reader로 위임합니다.
"""

from dataclasses import dataclass
from typing import Any, Dict

from .models import TaskContract, ApprovalEvidence
from .canonicalization import canonicalize_contract, canonicalize_scope, ScopeCanonicalizationError
from .repository import StateRepository, RepositoryError
from .jules_adapter import JulesSessionResponse
from .plan_session_registration import get_plan_session_registration

@dataclass(frozen=True)
class ManualRegisteredContentReviewRequest:
    """수동 콘텐츠 검토를 위한 비영속적 명시적 요청 객체."""
    task_id: str
    approval_id: str
    contract_hash: str
    approved_scope_hash: str
    session_id: str

    def __repr__(self) -> str:
        return "<ManualRegisteredContentReviewRequest: <REDACTED>>"

    def __str__(self) -> str:
        return "<ManualRegisteredContentReviewRequest: <REDACTED>>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": "<REDACTED>",
            "approval_id": "<REDACTED>",
            "contract_hash": "<REDACTED>",
            "approved_scope_hash": "<REDACTED>",
            "session_id": "<REDACTED>",
        }

def _failure(reason_code: str) -> Dict[str, Any]:
    return {"status": "NEEDS_HUMAN_REVIEW", "reason_code": reason_code}

def execute_manual_registered_content_review(
    *,
    repository: StateRepository,
    jules_adapter: Any,
    contract: TaskContract,
    approval_evidence: ApprovalEvidence,
    review_request: ManualRegisteredContentReviewRequest,
) -> Dict[str, Any]:
    """등록된 세션을 검증한 후, 수동 콘텐츠 검토 Reader로 위임합니다.

    이 진입점은 Pre-PR 단계이므로 최종 Session-Branch-PR 1:1:1 결속 검사를 유예하지만,
    StateRepository에 저장된 TaskRecord 및 ApprovalEvidence와의 일치 여부를 엄격히 대조합니다.
    """
    if approval_evidence.status != "ACTIVE":
        return _failure("APPROVAL_NOT_ACTIVE")
    if not contract.plan_approval_required:
        return _failure("PLAN_APPROVAL_REQUIRED")
    if contract.auto_merge:
        return _failure("AUTO_MERGE_NOT_ALLOWED")

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

    contract_version = getattr(contract, "contract_version", None)
    if contract_version is not None and approval_evidence.contract_version != contract_version:
         return _failure("EVIDENCE_CONTRACT_VERSION_MISMATCH")

    # StateRepository의 TaskRecord 대조 검증
    try:
        stored_task = repository.get_task(contract.task_id)
    except Exception:
        return _failure("REPOSITORY_FETCH_FAILED")

    if stored_task is None:
        return _failure("TASK_NOT_REGISTERED")
    if (
        stored_task.task_id != contract.task_id
        or stored_task.base_commit_sha != contract.base_commit_sha
        or stored_task.contract_hash != contract_hash
        or stored_task.approved_scope_hash != scope_hash
        or stored_task.idempotency_key != contract.idempotency_key
    ):
        return _failure("TASK_RECORD_MISMATCH")

    # StateRepository의 ApprovalEvidence 대조 검증
    try:
        stored_evidence = repository.get_approval_evidence(approval_evidence.approval_id)
    except Exception:
        return _failure("REPOSITORY_FETCH_FAILED")

    if stored_evidence is None:
        return _failure("APPROVAL_EVIDENCE_NOT_REGISTERED")
    if (
        stored_evidence.approval_id != approval_evidence.approval_id
        or stored_evidence.task_id != contract.task_id
        or stored_evidence.status != "ACTIVE"
        or stored_evidence.contract_version != contract.contract_version
        or stored_evidence.contract_hash != contract_hash
        or stored_evidence.approved_scope_hash != scope_hash
    ):
         return _failure("APPROVAL_EVIDENCE_MISMATCH")

    try:
        registration_result = get_plan_session_registration(repository=repository, task_id=contract.task_id)
    except Exception:
        return _failure("REPOSITORY_FETCH_FAILED")

    if registration_result.status != "REGISTERED" or registration_result.registration is None:
        return _failure(registration_result.reason_code or "PLAN_SESSION_NOT_REGISTERED")

    registration = registration_result.registration

    if (registration.task_id != review_request.task_id or
        registration.approval_id != review_request.approval_id or
        registration.contract_hash != review_request.contract_hash or
        registration.approved_scope_hash != review_request.approved_scope_hash or
        registration.session_id != review_request.session_id):
        return _failure("REGISTRATION_MISMATCH")

    session_response = JulesSessionResponse(
        status="CREATED",
        session_id=registration.session_id,
        task_id=registration.task_id,
        branch_name=None,
        pr_number=None,
        reason_code=None,
        created_at_utc=registration.created_at_utc,
        updated_at_utc=registration.created_at_utc,
    )

    from .jules_content_review_reader import fetch_content_review_activities
    result = fetch_content_review_activities(
        adapter=jules_adapter,
        session_id=review_request.session_id,
        contract=contract,
        evidence=approval_evidence,
        session_response=session_response
    )

    if result.get("status") != "SUCCESS":
        return _failure(result.get("reason_code", "UNKNOWN_READER_ERROR"))

    return result
