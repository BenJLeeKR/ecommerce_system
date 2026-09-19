"""Orchestrator Review Handoff Module.

Jules 작업 완료 감지, 1:1:1 바인딩 재확인, Scope Lock 재검증을 수행하고,
결과가 정상이면 RESULT_COLLECTED 이후 REVIEW_READY_DETECTED 이벤트를 생성하여
주입된 Codex 어댑터로 검토를 인계합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone

from .models import (
    PathItem,
    ExecutionResultInput,
    CodexReviewResultPackage,
    StateTransition,
)
from .jules_adapter import JulesSessionResponse, ActivitySummary, TransportError
from .validator import validate_changed_files_against_scope_lock
from .result_package import generate_result_package


class CodexNotificationAdapter(ABC):
    """Codex 검토 알림을 위한 주입 가능한 어댑터 인터페이스."""

    @abstractmethod
    def notify_review_ready(self, result_package: CodexReviewResultPackage) -> None:
        """구조화된 결과 패키지를 받아 Codex에 검토 준비 완료를 알립니다."""
        pass


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def execute_review_handoff(
    task_id: str,
    session_id: str,
    branch_name: str,
    pr_identifier: Any,
    changed_files: List[str],
    allowed_paths: List[PathItem],
    forbidden_paths: List[PathItem],
    expected_contract_hash: str,
    expected_approved_scope_hash: str,
    expected_idempotency_key: str,
    expected_approval_id: str,
    transition_agent: str,
    jules_adapter: Any,  # RealJulesAdapter 또는 Test Double
    codex_adapter: CodexNotificationAdapter,
    verified_session: Optional[JulesSessionResponse] = None,
) -> StateTransition:
    """Jules 완료 감지부터 검토 인계까지의 흐름을 실행합니다.

    1. Jules 세션 상태 및 활동 내역 조회 (정상 완료 여부 확인).
    2. 변경 파일 목록에 대한 Scope Lock 재검증.
    3. 세션/브랜치/PR 1:1:1 결속 및 승인 바인딩 확인을 위한 결과 패키지 생성.
    4. 패키지 상태가 RESULT_COLLECTED인 경우 Codex 어댑터에 알림 및 REVIEW_READY_DETECTED 전이 반환.
    5. 실패 시 NEEDS_HUMAN_REVIEW 전이 반환.
    """
    now_utc = _now_utc_iso()

    # 1. 명시적 주입된 세션 검증
    if verified_session is None:
        return StateTransition(
            transition_id=f"trans-{_now_utc_iso()}",
            task_id=task_id,
            from_status="UNKNOWN",
            to_status="NEEDS_HUMAN_REVIEW",
            transition_agent=transition_agent,
            recorded_at_utc=now_utc,
            reason="SESSION_NOT_FOUND"
        )

    session_info = verified_session

    # 2. Jules 활동 내역 조회
    try:
        activities: ActivitySummary = jules_adapter.get_activities(session_id)
    except TransportError:
        return StateTransition(
            transition_id=f"trans-{_now_utc_iso()}",
            task_id=task_id,
            from_status=session_info.status,
            to_status="NEEDS_HUMAN_REVIEW",
            transition_agent=transition_agent,
            recorded_at_utc=now_utc,
            reason="TRANSPORT_ERROR"
        )
    except Exception:
        return StateTransition(
            transition_id=f"trans-{_now_utc_iso()}",
            task_id=task_id,
            from_status=session_info.status,
            to_status="NEEDS_HUMAN_REVIEW",
            transition_agent=transition_agent,
            recorded_at_utc=now_utc,
            reason="UNKNOWN_ERROR"
        )

    # 활동 내역에 SESSION_COMPLETED가 없으면 인계 불가
    if not activities.is_completed:
        reason = "SESSION_FAILED" if activities.is_failed else "SESSION_NOT_COMPLETED"
        return StateTransition(
            transition_id=f"trans-{_now_utc_iso()}",
            task_id=task_id,
            from_status=session_info.status,
            to_status="NEEDS_HUMAN_REVIEW",
            transition_agent=transition_agent,
            recorded_at_utc=now_utc,
            reason=reason
        )

    # 3. Scope Lock 재검증
    scope_result = validate_changed_files_against_scope_lock(
        changed_files=changed_files,
        allowed_paths=allowed_paths,
        forbidden_paths=forbidden_paths,
        expected_approved_scope_hash=expected_approved_scope_hash
    )

    # 4. 결과 패키지 생성을 통한 1:1:1 결속 및 바인딩 최종 확인
    # (여기서는 임의로 SUCCESS 코드를 포함하며, 실환경에서는 구체적인 검증 요약 코드가 외부에서 주입됨)
    verification_codes = ["JULES_COMPLETED"] if scope_result.is_valid else ["SCOPE_VALIDATION_FAILED"]

    input_data = ExecutionResultInput(
        task_id=task_id,
        session_id=session_id,
        branch_name=branch_name,
        pr_identifier=pr_identifier,
        status="COMPLETED",
        changed_files=changed_files,
        verification_summary_codes=verification_codes,
        scope_validation_result=scope_result,
        contract_hash=expected_contract_hash,
        approved_scope_hash=expected_approved_scope_hash,
        idempotency_key=expected_idempotency_key,
        approval_id=expected_approval_id,
    )

    result_package = generate_result_package(
        input_data=input_data,
        expected_contract_hash=expected_contract_hash,
        expected_approved_scope_hash=expected_approved_scope_hash,
        expected_idempotency_key=expected_idempotency_key,
        expected_approval_id=expected_approval_id,
        existing_session=session_info
    )

    # 5. 판정 및 상태 전이 반환
    if result_package.status == "RESULT_COLLECTED":
        # 검토 준비 완료 알림 전송 (비민감 패키지 전달)
        codex_adapter.notify_review_ready(result_package)

        return StateTransition(
            transition_id=f"trans-{_now_utc_iso()}",
            task_id=task_id,
            from_status="RESULT_COLLECTED",
            to_status="REVIEW_READY_DETECTED",
            transition_agent=transition_agent,
            recorded_at_utc=now_utc,
            reason=None
        )
    else:
        # 실패 사유 코드를 결합하여 하나로 표시 (최대 64자 제한에 주의)
        reason_str = "_AND_".join(result_package.reason_codes)
        if len(reason_str) > 64:
            reason_str = "MULTIPLE_FAILURES_DETECTED"

        return StateTransition(
            transition_id=f"trans-{_now_utc_iso()}",
            task_id=task_id,
            from_status="COMPLETED",  # Jules는 완료되었으나 오케스트레이터 관점 전이
            to_status="NEEDS_HUMAN_REVIEW",
            transition_agent=transition_agent,
            recorded_at_utc=now_utc,
            reason=reason_str or "VERIFICATION_FAILED"
        )
