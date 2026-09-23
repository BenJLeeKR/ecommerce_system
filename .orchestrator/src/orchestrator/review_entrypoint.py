"""Orchestrator Review Handoff Entrypoint.

외부 호출자를 위해 Review Handoff 절차를 단일 함수로 노출하는 최상위 진입점입니다.
이 모듈은 `execute_review_handoff`에 런타임 저장소 팩토리(`get_jules_state_repository`)를
명시적으로 주입하여, 정상 완료된 세션에 한해 1:1:1 결속 영속화를 지연 실행하도록 돕습니다.
"""

from typing import List, Optional, Any, Callable

from .models import PathItem, StateTransition
from .jules_adapter import JulesSessionResponse
from .repository import StateRepository
from .runtime_config import get_jules_state_repository
from .review_handoff import execute_review_handoff, CodexNotificationAdapter


def execute_review_handoff_with_repository(
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
    jules_adapter: Any,
    codex_adapter: CodexNotificationAdapter,
    repository: Optional[StateRepository] = None,
    jules_state_repository_factory: Optional[Callable[[], StateRepository]] = get_jules_state_repository,
    verified_session: Optional[JulesSessionResponse] = None,
) -> StateTransition:
    """리뷰 인계 절차를 수행하며 1:1:1 결속 데이터를 영속화하는 최상위 진입점.

    내부적으로 `execute_review_handoff`를 호출하며, 기본적으로
    `get_jules_state_repository`를 팩토리로 전달합니다. 저장소 초기화는
    검증이 성공하여 RESULT_COLLECTED 상태가 된 경우에만 지연 호출됩니다.
    만약 직접 `repository` 객체가 전달되면 팩토리는 호출되지 않습니다.
    """
    return execute_review_handoff(
        task_id=task_id,
        session_id=session_id,
        branch_name=branch_name,
        pr_identifier=pr_identifier,
        changed_files=changed_files,
        allowed_paths=allowed_paths,
        forbidden_paths=forbidden_paths,
        expected_contract_hash=expected_contract_hash,
        expected_approved_scope_hash=expected_approved_scope_hash,
        expected_idempotency_key=expected_idempotency_key,
        expected_approval_id=expected_approval_id,
        transition_agent=transition_agent,
        jules_adapter=jules_adapter,
        codex_adapter=codex_adapter,
        repository=repository,
        jules_state_repository_factory=jules_state_repository_factory,
        verified_session=verified_session,
    )
