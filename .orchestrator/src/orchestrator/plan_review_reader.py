import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

from .jules_adapter import JulesAdapter, TransportError
from .models import TaskContract, PersistentSessionBinding

logger = logging.getLogger(__name__)

class PlanReviewReaderError(Exception):
    pass

@dataclass
class PlanReviewResult:
    """Plan 원문을 포함하는 반환 타입. 비영속·비직렬화·비로그 경계를 강제합니다."""
    _plan_text: str
    status: str
    reason: Optional[str] = None

    @property
    def plan_text(self) -> str:
        return self._plan_text

    def __repr__(self) -> str:
        return f"PlanReviewResult(status={self.status!r}, reason={self.reason!r}, _plan_text='<REDACTED>')"

    def __str__(self) -> str:
        return self.__repr__()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "_plan_text": "<REDACTED>"
        }


def read_latest_plan_review(
    adapter: JulesAdapter,
    session_id: str,
    task_contract: TaskContract,
    binding: PersistentSessionBinding,
) -> PlanReviewResult:
    """
    지정된 세션에서 가장 최근에 생성된 planGenerated 이벤트의 원문을 조회합니다.
    """

    if not session_id or not session_id.startswith("sessions/"):
        return PlanReviewResult(_plan_text="", status="NEEDS_HUMAN_REVIEW", reason="INVALID_SESSION_ID")

    if not task_contract or not binding:
        return PlanReviewResult(_plan_text="", status="NEEDS_HUMAN_REVIEW", reason="MISSING_BINDING_OR_CONTRACT")

    if binding.session_id != session_id or binding.task_id != task_contract.task_id:
        return PlanReviewResult(_plan_text="", status="NEEDS_HUMAN_REVIEW", reason="BINDING_MISMATCH")

    try:
        plan_text = adapter.get_latest_plan_text(session_id)
        if plan_text is None:
            return PlanReviewResult(_plan_text="", status="NEEDS_HUMAN_REVIEW", reason="NO_PLAN_FOUND_OR_INVALID_FORMAT")

        return PlanReviewResult(_plan_text=plan_text, status="SUCCESS")

    except TransportError:
         return PlanReviewResult(_plan_text="", status="NEEDS_HUMAN_REVIEW", reason="API_ERROR")
    except Exception:
         return PlanReviewResult(_plan_text="", status="NEEDS_HUMAN_REVIEW", reason="INTERNAL_ERROR")
