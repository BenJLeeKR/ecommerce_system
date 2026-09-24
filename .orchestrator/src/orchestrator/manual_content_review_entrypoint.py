from typing import Any, Dict, Protocol

from .canonicalization import canonicalize_scope, canonicalize_contract
from .jules_adapter import JulesSessionResponse
from .validator import ApprovalEvidence, TaskContract
from .models import PersistentSessionBinding

class AdapterProtocol(Protocol):
    def fetch_raw_activities_for_content_review(self, session_id: str) -> Any:
        ...

def execute_manual_content_review_reader(
    session_id: str,
    contract: TaskContract,
    evidence: ApprovalEvidence,
    session_response: JulesSessionResponse,
    binding: PersistentSessionBinding,
    adapter: AdapterProtocol
) -> Dict[str, Any]:
    def _fail() -> Dict[str, Any]:
        return {"status": "NEEDS_HUMAN_REVIEW"}

    if session_id != session_response.session_id:
        return _fail()
    if contract.task_id != session_response.task_id:
        return _fail()
    if evidence.task_id != contract.task_id:
        return _fail()
    if binding.session_id != session_response.session_id:
        return _fail()
    if binding.task_id != contract.task_id:
        return _fail()

    if hasattr(session_response, "branch_name") and binding.branch_name != getattr(session_response, "branch_name"):
        return _fail()
    if hasattr(session_response, "pr_number") and binding.pr_number != getattr(session_response, "pr_number"):
        return _fail()

    try:
        _, computed_contract_hash = canonicalize_contract(contract)
        _, computed_scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
    except Exception:
        return _fail()

    if evidence.contract_hash != computed_contract_hash:
        return _fail()
    if evidence.approved_scope_hash != computed_scope_hash:
        return _fail()

    if binding.contract_hash != computed_contract_hash:
        return _fail()
    if binding.approved_scope_hash != computed_scope_hash:
        return _fail()
    if evidence.status != "ACTIVE":
        return _fail()
    if getattr(contract, "plan_approval_required", False) is False:
        return _fail()
    if getattr(contract, "auto_merge", True) is True:
        return _fail()

    if not hasattr(adapter, "fetch_raw_activities_for_content_review"):
        return _fail()

    # To avoid double fetching since existing fetch_content_review_activities does it,
    # We shouldn't call it here. We just delegate directly to fetch_content_review_activities.
    from .jules_content_review_reader import fetch_content_review_activities

    # We call the existing reader with the adapter to actually fetch and parse
    # The existing reader will validate the conditions again, but that's fine.
    # However, to decouple the existing reader from doing raw fetch again, we could directly parse
    # But the instruction says "정상 경로에서만 기존 Reader를 정확히 한 번 호출하고"
    # The existing fetch_content_review_activities in jules_content_review_reader.py expects adapter, session_id, contract, evidence, session_response.

    result = fetch_content_review_activities(
        adapter=adapter,
        session_id=session_id,
        contract=contract,
        evidence=evidence,
        session_response=session_response
    )

    if result.get("status") != "SUCCESS":
        return _fail()

    return result
