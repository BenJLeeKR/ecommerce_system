"""Phase 1 Orchestrator를 위한 정책 평가 모듈."""

from typing import Tuple, List
from .models import TaskContract, ApprovalEvidence


def evaluate_dispatch_policy(
    contract: TaskContract,
    computed_contract_hash: str,
    computed_scope_hash: str,
    approval_evidence: ApprovalEvidence
) -> Tuple[bool, List[str]]:
    """문법상 유효한 Contract 및 승인 증적에 대해 Phase 1 자동 Dispatch 적격성을 평가합니다.

    반환값:
        (is_dispatch_eligible: bool, reasons: List[str])
    """
    reasons = []

    # 1. 위험도 검사: Phase 1 자동 Dispatch는 오직 LOW 위험도만 허용
    risk = contract.risk_level.strip().upper()
    if risk != "LOW":
        reasons.append(f"위험도 '{contract.risk_level}'은 Phase 1 자동 Dispatch 대상이 아닙니다 (LOW만 허용).")

    # 2. auto_merge 검사: 반드시 false여야 함
    if contract.auto_merge:
        reasons.append("auto_merge=true 설정은 금지되어 있어 자동 Dispatch 부적격입니다.")

    # 3. 승인 증적 상태 검사: 반드시 ACTIVE여야 함
    if approval_evidence.status != "ACTIVE":
        reasons.append(f"승인 증적 상태가 '{approval_evidence.status}'입니다 (ACTIVE 상태만 허용).")

    is_eligible = (len(reasons) == 0)
    return is_eligible, reasons
