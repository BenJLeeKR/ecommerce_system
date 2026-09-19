"""Orchestrator Phase 2 - Manual Session Monitor Entrypoint.

이 모듈은 기존 Session Monitor를 외부(Codex 등)에서 단회성으로 직접 호출할 수 있도록
최소한의 명시적 진입점을 제공합니다.

자동 폴링, 세션 생성, 내부 데이터베이스 조회를 배제하며,
호출자가 전달한 명시적 바인딩 확인 신호(`is_binding_valid`), API 키,
세션 식별자만을 바탕으로 상태를 확인하여 비민감 신호로 매핑합니다.
"""

import logging
from typing import Callable, Optional
from .session_monitor import ActivityFetcherAdapter, invoke_session_monitor_once
from .status_bridge import BridgeSignal
from .jules_adapter import RealJulesAdapter
from .runtime_config import RuntimeConfigError, load_jules_api_key

logger = logging.getLogger(__name__)


def execute_manual_session_monitor(
    api_key: Optional[str],
    session_resource_name: str,
    is_binding_valid: bool,
    adapter_factory: Callable[[str], ActivityFetcherAdapter] = lambda key: RealJulesAdapter(api_key=key),
) -> BridgeSignal:
    """수동 호출을 위한 단회성 세션 모니터 진입점.

    호출자는 1:1:1 바인딩 유효성을 외부에서 판단하여 `is_binding_valid` 플래그로 전달해야 합니다.
    바인딩이 무효한 경우, 어댑터를 생성하거나 조회 API를 호출하지 않고
    즉시 `NEEDS_HUMAN_REVIEW` 신호를 반환합니다.
    API 키를 `None`으로 전달하면 `.orchestrator/.env`에서 키만 읽습니다.

    Args:
        api_key: 주입할 Jules API 키. (로그나 응답에 노출되지 않도록 엄격히 관리해야 함)
        session_resource_name: 조회할 세션의 리소스 이름 (예: 'sessions/SES-123-001').
        is_binding_valid: 외부(호출자)에서 확인한 1:1:1 바인딩 유효 여부.
        adapter_factory: (api_key: str)를 인자로 받아 ActivityFetcherAdapter를 생성하는 함수.
                         기본값으로 RealJulesAdapter를 반환합니다.

    Returns:
        조회 결과를 매핑한 비민감 상태 신호를 담은 BridgeSignal 객체.
    """
    if not is_binding_valid:
        # 바인딩이 무효한 경우: 어댑터 생성(factory 호출) 및 활동 조회 모두 생략
        return BridgeSignal(
            status_signal="NEEDS_HUMAN_REVIEW",
            reason_code="BINDING_INVALID",
        )

    if api_key is None:
        try:
            api_key = load_jules_api_key()
        except RuntimeConfigError:
            return BridgeSignal(
                status_signal="NEEDS_HUMAN_REVIEW",
                reason_code="RUNTIME_CONFIG_INVALID",
            )

    try:
        adapter = adapter_factory(api_key)
    except Exception:
        # 어댑터 초기화 실패 (예: 잘못된 키 형식 등)
        # 예외 상세 내용을 캡처/기록/반환하지 않음으로써 API 키나 내부 오류 노출을 방지
        return BridgeSignal(
            status_signal="NEEDS_HUMAN_REVIEW",
            reason_code="ADAPTER_INIT_FAILED",
        )

    # 어댑터 생성이 성공하면 기존 session monitor를 호출하여 단 1회 조회를 위임
    return invoke_session_monitor_once(
        adapter=adapter,
        session_resource_name=session_resource_name,
        is_binding_valid=True,
    )
