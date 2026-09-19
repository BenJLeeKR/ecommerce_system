"""Orchestrator Phase 2 - Session Status Bridge MVP.

이 모듈은 외부에서 유효하게 확인된 세션을 명시적으로 단회 조회한 결과(ActivitySummary)를
입력받아, Codex의 최종 판단(수용/병합)을 수행하지 않고 오직 비민감 상태 신호만을
결정론적으로 매핑하여 반환하는 순수 함수(Pure Function)의 역할을 합니다.
"""

from dataclasses import dataclass
from typing import Optional
from .jules_adapter import ActivitySummary


@dataclass
class BridgeSignal:
    status_signal: str
    reason_code: str


def map_direction_confirmation_signal(is_binding_valid: bool, is_direction_confirmation_pending: bool) -> Optional[BridgeSignal]:
    """Codex가 명시적으로 제공한 방향 확인 대기 상태를 비민감 신호로 매핑합니다.

    우선순위:
    1. 바인딩 불일치 (is_binding_valid == False) -> NEEDS_HUMAN_REVIEW
    2. 방향 확인 대기 (is_direction_confirmation_pending == True) -> DIRECTION_CONFIRMATION_REQUIRED
    3. 대기 아님 (is_direction_confirmation_pending == False) -> None (알림 생성 안 함)
    """
    if not is_binding_valid:
        return BridgeSignal(
            status_signal="NEEDS_HUMAN_REVIEW",
            reason_code="BINDING_INVALID"
        )

    if is_direction_confirmation_pending:
        return BridgeSignal(
            status_signal="DIRECTION_CONFIRMATION_REQUIRED",
            reason_code="DIRECTION_CONFIRMATION_PENDING"
        )

    return None


def map_session_status(is_binding_valid: bool, activities: ActivitySummary) -> BridgeSignal:
    """바인딩 유효 여부와 활동 요약을 기반으로 상태 신호를 결정합니다.

    우선순위:
    1. 바인딩 불일치 (is_binding_valid == False) -> NEEDS_HUMAN_REVIEW
    2. SESSION_FAILED -> NEEDS_HUMAN_REVIEW
    3. SESSION_COMPLETED -> READY_FOR_REVIEW
    4. 시간 순서 불확실 시 -> NEEDS_HUMAN_REVIEW
    5. PLAN_GENERATED 이후 승인/명시적 진행 활동(PLAN_APPROVED, PROGRESS_UPDATED) 존재 여부에 따라 IN_PROGRESS(비작동 상태) 또는 PLAN_REVIEW_REQUIRED 반환
    6. 기타/인식 가능한 활동 없음 -> NEEDS_HUMAN_REVIEW
    """
    if not is_binding_valid:
        return BridgeSignal(
            status_signal="NEEDS_HUMAN_REVIEW",
            reason_code="BINDING_INVALID"
        )

    # ActivitySummary에는 is_failed, is_completed 필드와 activity_types 배열이 포함됨.
    if activities.is_failed or "SESSION_FAILED" in activities.activity_types:
        return BridgeSignal(
            status_signal="NEEDS_HUMAN_REVIEW",
            reason_code="SESSION_FAILED"
        )

    if activities.is_completed or "SESSION_COMPLETED" in activities.activity_types:
        return BridgeSignal(
            status_signal="READY_FOR_REVIEW",
            reason_code="SESSION_COMPLETED"
        )

    # 하위 호환성을 위해 getattr 사용
    is_reliable = getattr(activities, "is_temporal_order_reliable", True)
    if not is_reliable:
        return BridgeSignal(
            status_signal="NEEDS_HUMAN_REVIEW",
            reason_code="TEMPORAL_ORDER_UNRELIABLE"
        )

    if "PLAN_GENERATED" in activities.activity_types:
        # PLAN_GENERATED의 마지막 등장 인덱스
        plan_gen_idx = len(activities.activity_types) - 1 - activities.activity_types[::-1].index("PLAN_GENERATED")

        # PLAN_GENERATED 이후에 승인이나 진행 상태가 있는지 확인 (AGENT_MESSAGED, USER_MESSAGED 제외)
        post_gen_activities = activities.activity_types[plan_gen_idx + 1:]
        progress_indicators = {"PLAN_APPROVED", "PROGRESS_UPDATED"}

        if any(act in progress_indicators for act in post_gen_activities):
            return BridgeSignal(
                status_signal="IN_PROGRESS",
                reason_code="ACTIVITY_IN_PROGRESS"
            )

        return BridgeSignal(
            status_signal="PLAN_REVIEW_REQUIRED",
            reason_code="PLAN_GENERATED"
        )

    # 유효한 활동을 인식할 수 없는 경우 안전하게 검토 필요 상태로 전이
    return BridgeSignal(
        status_signal="NEEDS_HUMAN_REVIEW",
        reason_code="NO_RECOGNIZABLE_ACTIVITY"
    )
