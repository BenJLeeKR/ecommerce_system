"""Jules Interactive Plan 세션의 명시적·비민감 등록 경계."""

from datetime import datetime, timezone
from typing import Optional

from .canonicalization import ScopeCanonicalizationError, canonicalize_contract, canonicalize_scope
from .jules_adapter import JulesSessionResponse
from .models import ApprovalEvidence, PlanSessionRegistration, PlanSessionRegistrationResult, TaskContract
from .repository import RepositoryBindingConflictError, RepositoryError, StateRepository


def _failure(reason_code: str) -> PlanSessionRegistrationResult:
    return PlanSessionRegistrationResult(status="NEEDS_HUMAN_REVIEW", reason_code=reason_code)


def register_plan_session(
    *, repository: StateRepository, contract: TaskContract,
    approval_evidence: ApprovalEvidence, session_response: JulesSessionResponse,
    registered_at_utc: Optional[str] = None,
) -> PlanSessionRegistrationResult:
    """검증된 Plan 단계 세션만 등록합니다. 사전 검증 실패에서는 쓰기를 수행하지 않습니다."""
    if approval_evidence.status != "ACTIVE":
        return _failure("APPROVAL_NOT_ACTIVE")
    if not contract.plan_approval_required:
        return _failure("PLAN_APPROVAL_REQUIRED")
    if contract.auto_merge:
        return _failure("AUTO_MERGE_NOT_ALLOWED")
    if not session_response.session_id:
        return _failure("INVALID_SESSION_ID")
    if session_response.branch_name is not None or session_response.pr_number is not None:
        return _failure("PLAN_SESSION_OUTPUTS_NOT_ALLOWED")
    if session_response.status != "CREATED":
        return _failure("PLAN_SESSION_NOT_CREATED")
    if contract.task_id != approval_evidence.task_id or contract.task_id != session_response.task_id:
        return _failure("TASK_ID_MISMATCH")
    if contract.contract_version != approval_evidence.contract_version:
        return _failure("CONTRACT_VERSION_MISMATCH")

    try:
        _, contract_hash = canonicalize_contract(contract)
        _, scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
    except (ScopeCanonicalizationError, TypeError, ValueError, AttributeError):
        return _failure("SCOPE_CANONICALIZATION_FAILED")

    if contract_hash != approval_evidence.contract_hash:
        return _failure("CONTRACT_HASH_MISMATCH")
    if scope_hash != approval_evidence.approved_scope_hash:
        return _failure("SCOPE_HASH_MISMATCH")

    stored_task = repository.get_task(contract.task_id)
    if stored_task is None:
        return _failure("TASK_NOT_REGISTERED")
    if (
        stored_task.base_commit_sha != contract.base_commit_sha
        or stored_task.contract_hash != contract_hash
        or stored_task.approved_scope_hash != scope_hash
        or stored_task.idempotency_key != contract.idempotency_key
    ):
        return _failure("TASK_RECORD_MISMATCH")

    stored_evidence = repository.get_approval_evidence(approval_evidence.approval_id)
    if stored_evidence is None:
        return _failure("APPROVAL_EVIDENCE_NOT_REGISTERED")
    if stored_evidence != approval_evidence:
        return _failure("APPROVAL_EVIDENCE_MISMATCH")

    registration = PlanSessionRegistration(
        task_id=contract.task_id,
        session_id=session_response.session_id,
        approval_id=approval_evidence.approval_id,
        contract_hash=contract_hash,
        approved_scope_hash=scope_hash,
        created_at_utc=registered_at_utc or datetime.now(timezone.utc).isoformat(),
    )
    try:
        repository.save_plan_session_registration(registration)
    except RepositoryBindingConflictError:
        return _failure("PLAN_SESSION_REGISTRATION_CONFLICT")
    except RepositoryError:
        return _failure("PLAN_SESSION_REGISTRATION_FAILED")
    return PlanSessionRegistrationResult(status="REGISTERED", registration=registration)


def get_plan_session_registration(
    *, repository: StateRepository, task_id: str
) -> PlanSessionRegistrationResult:
    """명시적으로 주입된 저장소에서 Plan 단계 등록만 조회합니다."""
    try:
        registration = repository.get_plan_session_registration(task_id)
    except RepositoryError:
        return _failure("PLAN_SESSION_LOOKUP_FAILED")
    if registration is None:
        return _failure("PLAN_SESSION_NOT_REGISTERED")
    return PlanSessionRegistrationResult(status="REGISTERED", registration=registration)
