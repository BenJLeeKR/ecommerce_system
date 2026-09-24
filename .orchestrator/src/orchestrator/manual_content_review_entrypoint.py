from dataclasses import dataclass
from typing import Any, Dict, Protocol, Optional

from .canonicalization import canonicalize_scope, canonicalize_contract
from .jules_adapter import JulesSessionResponse
from .validator import ApprovalEvidence, TaskContract
from .models import PersistentSessionBinding

class AdapterProtocol(Protocol):
    def fetch_raw_activities_for_content_review(self, session_id: str) -> Any:
        ...

@dataclass
class ManualContentReviewRequest:
    """명시적 수동 콘텐츠 검토 요청 객체 (비영속, 비직렬화 전용)"""
    session_id: str
    task_id: str
    approval_id: str
    contract_hash: str
    approved_scope_hash: str

def execute_manual_content_review_reader(
    request: ManualContentReviewRequest,
    contract: TaskContract,
    evidence: ApprovalEvidence,
    session_response: JulesSessionResponse,
    binding: PersistentSessionBinding,
    adapter: AdapterProtocol
) -> Dict[str, Any]:
    def _fail(reason: str) -> Dict[str, Any]:
        return {"status": "NEEDS_HUMAN_REVIEW", "reason_code": reason}

    # 1. 요청 객체와 세션/결속/증거 간 식별자 대조
    if request.session_id != session_response.session_id:
        return _fail("SESSION_ID_MISMATCH")
    if request.task_id != session_response.task_id:
        return _fail("TASK_ID_MISMATCH")
    if request.approval_id != evidence.approval_id:
        return _fail("APPROVAL_ID_MISMATCH")

    # 2. 계약 및 증거 식별자 상호 대조
    if contract.task_id != session_response.task_id:
        return _fail("CONTRACT_TASK_ID_MISMATCH")
    if evidence.task_id != contract.task_id:
        return _fail("EVIDENCE_TASK_ID_MISMATCH")

    # 3. 영속 결속(Binding) 객체 검증
    if binding.session_id != session_response.session_id:
        return _fail("BINDING_SESSION_ID_MISMATCH")
    if binding.task_id != contract.task_id:
        return _fail("BINDING_TASK_ID_MISMATCH")

    if hasattr(session_response, "branch_name") and binding.branch_name != getattr(session_response, "branch_name"):
        return _fail("BINDING_BRANCH_MISMATCH")
    if hasattr(session_response, "pr_number") and binding.pr_number != getattr(session_response, "pr_number"):
        return _fail("BINDING_PR_MISMATCH")

    # 4. 해시 및 버전 대조
    try:
        _, computed_contract_hash = canonicalize_contract(contract)
        _, computed_scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
    except Exception:
        return _fail("CANONICALIZATION_FAILED")

    if request.contract_hash != computed_contract_hash:
        return _fail("REQUEST_CONTRACT_HASH_MISMATCH")
    if request.approved_scope_hash != computed_scope_hash:
        return _fail("REQUEST_SCOPE_HASH_MISMATCH")

    if evidence.contract_hash != computed_contract_hash:
        return _fail("EVIDENCE_CONTRACT_HASH_MISMATCH")
    if evidence.approved_scope_hash != computed_scope_hash:
        return _fail("EVIDENCE_SCOPE_HASH_MISMATCH")

    if binding.contract_hash != computed_contract_hash:
        return _fail("BINDING_CONTRACT_HASH_MISMATCH")
    if binding.approved_scope_hash != computed_scope_hash:
        return _fail("BINDING_SCOPE_HASH_MISMATCH")

    contract_version = getattr(contract, "contract_version", None)
    if contract_version is not None and evidence.contract_version != contract_version:
        return _fail("EVIDENCE_CONTRACT_VERSION_MISMATCH")

    # 5. 정책 조건 검증
    if evidence.status != "ACTIVE":
        return _fail("EVIDENCE_NOT_ACTIVE")
    if getattr(contract, "plan_approval_required", False) is False:
        return _fail("PLAN_APPROVAL_NOT_REQUIRED")
    if getattr(contract, "auto_merge", True) is True:
        return _fail("AUTO_MERGE_ENABLED")

    if not hasattr(adapter, "fetch_raw_activities_for_content_review"):
        return _fail("UNSUPPORTED_ADAPTER")

    # 이중 조회를 피하기 위해 여기서 직접 adapter.fetch_raw_activities_for_content_review 를 호출하지 않고,
    # 기존 리더(fetch_content_review_activities)로 직접 위임합니다.
    from .jules_content_review_reader import fetch_content_review_activities

    result = fetch_content_review_activities(
        adapter=adapter,
        session_id=request.session_id,
        contract=contract,
        evidence=evidence,
        session_response=session_response
    )

    # 기존 리더에서 NEEDS_HUMAN_REVIEW가 발생한 경우 reason_code를 안전하게 보존합니다.
    if result.get("status") != "SUCCESS":
        return _fail(result.get("reason_code", "UNKNOWN_READER_ERROR"))

    return result
