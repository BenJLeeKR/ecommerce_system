"""Orchestrator Phase 2 - Session Monitor MVP.

이 모듈은 외부에서 유효성이 판단된 바인딩 상태(`is_binding_valid`)를 입력받아,
유효한 경우에만 주입된 조회자(fetcher)를 단 1회 호출하여 세션의 상태 신호(`BridgeSignal`)를
반환하는 단회성(One-shot) 최소 모니터입니다.

외부 상태 저장, 무한 폴링, 웹훅, 데몬, 자동 생성 및 병합 기능은 포함하지 않습니다.
예외 발생 시 원시 데이터를 노출하지 않고 구조화된 에러 신호로 매핑합니다.
"""

import logging
from typing import Callable, Protocol
from .jules_adapter import ActivitySummary, TransportError
from .status_bridge import BridgeSignal, map_session_status

logger = logging.getLogger(__name__)


class ActivityFetcherAdapter(Protocol):
    """세션 활동 조회 기능만 요구하는 최소 어댑터 Protocol.

    RealJulesAdapter 등 이 시그니처를 만족하는 어댑터를 주입받아 사용할 수 있습니다.
    """
    def get_activities(self, session_resource_name: str) -> ActivitySummary:
        ...


def invoke_session_monitor_once(
    adapter: ActivityFetcherAdapter,
    session_resource_name: str,
    is_binding_valid: bool
) -> BridgeSignal:
    """주입된 어댑터를 사용하여 단회성 세션 모니터를 호출하는 Facade.

    이 함수는 어댑터의 get_activities 메서드를 check_session_status_once에 전달하여
    바인딩 검증, 조회 및 상태 매핑을 위임합니다.
    호출부는 API 키나 환경 변수, 바인딩 판단 로직을 직접 다루지 않습니다.

    Args:
        adapter: get_activities 메서드를 제공하는 어댑터 인스턴스.
        session_resource_name: 조회할 대상 세션의 리소스 이름.
        is_binding_valid: 외부에서 확인한 1:1:1 바인딩 유효 여부.

    Returns:
        비민감 상태 신호를 담은 BridgeSignal 객체.
    """
    return check_session_status_once(
        is_binding_valid=is_binding_valid,
        session_resource_name=session_resource_name,
        activity_fetcher=adapter.get_activities
    )


def check_session_status_once(
    is_binding_valid: bool,
    session_resource_name: str,
    activity_fetcher: Callable[[str], ActivitySummary]
) -> BridgeSignal:
    """단회성 세션 상태 조회 및 브리지 신호 매핑을 수행합니다.

    Args:
        is_binding_valid: 외부(호출자)에서 확인한 1:1:1 바인딩 유효 여부.
        session_resource_name: 조회할 대상 세션의 리소스 이름 (예: 'sessions/SES-123-001').
        activity_fetcher: session_resource_name을 입력받아 ActivitySummary를 반환하는 콜러백.

    Returns:
        비민감 상태 신호를 담은 BridgeSignal 객체.
    """
    if not is_binding_valid:
        # 바인딩이 무효하면 조회자를 절대 호출하지 않음
        return BridgeSignal(
            status_signal="NEEDS_HUMAN_REVIEW",
            reason_code="BINDING_INVALID"
        )

    try:
        # 유효한 바인딩인 경우 정확히 1회 호출
        activities = activity_fetcher(session_resource_name)
    except TransportError:
        # 통신 및 포맷 에러 시 안전 처리 (원시 데이터 미노출)
        return BridgeSignal(
            status_signal="NEEDS_HUMAN_REVIEW",
            reason_code="ACTIVITY_FETCH_FAILED"
        )
    except Exception:
        # 예상치 못한 일반 예외 시 안전 처리 (원시 에러 로깅 제외/최소화 및 노출 금지)
        return BridgeSignal(
            status_signal="NEEDS_HUMAN_REVIEW",
            reason_code="ACTIVITY_FETCH_FAILED"
        )

    # 정상 조회 시 상태 신호 결정
    return map_session_status(
        is_binding_valid=True,
        activities=activities
    )
