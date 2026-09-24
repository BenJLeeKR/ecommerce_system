"""Jules Content Handoff Reader.

사용자 수동 검토(Human Review) 요청에 대해 Jules 세션의 활동 기록 원문을 안전하게 읽어오는 전용 경계(Reader)입니다.
- 자동 검토, 자동 Plan 승인, 자동 병합 기능은 일절 제공하지 않습니다.
- 반환된 원문 객체(ReviewActivity)는 메모리에서만 사용되어야 하며 직렬화, 로깅, DB 저장이 금지됩니다.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .canonicalization import canonicalize_scope, canonicalize_contract, ScopeCanonicalizationError
from .jules_adapter import JulesAdapter, JulesSessionResponse
from .validator import ApprovalEvidence, TaskContract


@dataclass
class ReviewActivity:
    """수동 검토를 위해 추출된 단일 활동 원문 데이터 클래스.

    모든 로깅, 직렬화(to_dict), 문자열 변환(__str__, __repr__) 시
    실제 민감 원문 내용을 <REDACTED> 처리하여 유출을 방지합니다.
    """
    activity_type: str
    create_time_utc: Optional[str] = field(default=None)
    # 텍스트가 없는 완료/승인 이벤트 등은 None
    title: Optional[str] = field(default=None)
    description: Optional[str] = field(default=None)

    # agentMessage 원문용 (planGenerated 등과 분리 또는 통일 가능, 여기서는 통합하여 title/description에 넣거나 별도 필드 사용)
    agent_message: Optional[str] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "activity_type": self.activity_type,
            "create_time_utc": self.create_time_utc,
            "title": "<REDACTED>" if self.title is not None else None,
            "description": "<REDACTED>" if self.description is not None else None,
            "agent_message": "<REDACTED>" if self.agent_message is not None else None,
        }

    def __str__(self) -> str:
        return (
            f"ReviewActivity(activity_type={self.activity_type!r}, "
            f"create_time_utc={self.create_time_utc!r}, "
            f"title={'<REDACTED>' if self.title is not None else None}, "
            f"description={'<REDACTED>' if self.description is not None else None}, "
            f"agent_message={'<REDACTED>' if self.agent_message is not None else None})"
        )

    def __repr__(self) -> str:
        return self.__str__()


def fetch_content_review_activities(
    adapter: JulesAdapter,
    session_id: str,
    contract: TaskContract,
    evidence: ApprovalEvidence,
    session_response: JulesSessionResponse
) -> Dict[str, Any]:
    """사전 검증 후 Jules 세션의 수동 검토용 원문 활동 목록을 조회합니다.

    [검증 규칙]
    - evidence.status == 'ACTIVE'
    - contract.plan_approval_required == True
    - contract.auto_merge == False
    - contract.task_id == session_response.task_id
    - 요청된 session_id == session_response.session_id (리소스 네임 일치 여부)

    검증 실패 시 API 호출은 0회이며 즉시 None을 반환(상위에서 NEEDS_HUMAN_REVIEW 처리)합니다.
    """
    def _fail(reason: str) -> Dict[str, Any]:
        return {"status": "NEEDS_HUMAN_REVIEW", "reason_code": reason}

    try:
        _, computed_scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
        _, computed_contract_hash = canonicalize_contract(contract)
    except Exception:
        return _fail("CANONICALIZATION_FAILED")

    if evidence.status != "ACTIVE":
        return _fail("EVIDENCE_NOT_ACTIVE")
    if evidence.task_id != contract.task_id:
        return _fail("EVIDENCE_TASK_ID_MISMATCH")
    if evidence.contract_version != getattr(contract, "contract_version", None):
        return _fail("EVIDENCE_CONTRACT_VERSION_MISMATCH")
    if evidence.contract_hash != computed_contract_hash:
        return _fail("EVIDENCE_CONTRACT_HASH_MISMATCH")
    if evidence.approved_scope_hash != computed_scope_hash:
        return _fail("EVIDENCE_SCOPE_HASH_MISMATCH")

    if not getattr(contract, "plan_approval_required", False):
        return _fail("PLAN_APPROVAL_NOT_REQUIRED")
    if getattr(contract, "auto_merge", True):
        return _fail("AUTO_MERGE_ENABLED")
    if contract.task_id != session_response.task_id:
        return _fail("SESSION_TASK_ID_MISMATCH")
    if session_id != session_response.session_id:
        return _fail("SESSION_ID_MISMATCH")

    # 진입점에서 전달받은 어댑터(Protocol/Mock 등)를 통해 원시 액티비티를 단 1회 위임 조회
    if not hasattr(adapter, "fetch_raw_activities_for_content_review"):
        return _fail("UNSUPPORTED_ADAPTER")

    raw_activities = adapter.fetch_raw_activities_for_content_review(session_id)
    if raw_activities is None:
        return _fail("RAW_ACTIVITIES_FETCH_FAILED")

    parsed_activities = []

    for dt, act in raw_activities:
        create_time_utc = dt.isoformat()

        union_keys = [k for k in act.keys() if k not in ("createTime", "name", "id", "metadata")]
        if len(union_keys) != 1:
            return _fail("MULTIPLE_OR_ZERO_UNION_EVENTS")

        event_type = union_keys[0]
        event_data = act[event_type]

        if not isinstance(event_data, dict):
            return _fail("INVALID_EVENT_FORMAT")

        if event_type == "agentMessaged":
            msg = event_data.get("agentMessage")
            if not isinstance(msg, str):
                return _fail("INVALID_AGENT_MESSAGE")
            parsed_activities.append(ReviewActivity(
                activity_type="AGENT_MESSAGED",
                create_time_utc=create_time_utc,
                agent_message=msg
            ))

        elif event_type == "planGenerated":
            if "plan" not in event_data:
                return _fail("INVALID_PLAN_GENERATED_FORMAT")
            plan_data = event_data["plan"]
            if not isinstance(plan_data, dict) or "steps" not in plan_data:
                return _fail("INVALID_PLAN_GENERATED_FORMAT")
            steps = plan_data["steps"]
            if not isinstance(steps, list) or len(steps) == 0:
                return _fail("INVALID_PLAN_GENERATED_FORMAT")

            # title과 description 대응 관계 유지 (독립 결합 금지)
            formatted_steps = []
            for step in steps:
                if not isinstance(step, dict):
                    return _fail("INVALID_PLAN_GENERATED_FORMAT")
                title = step.get("title")
                if not isinstance(title, str):
                    return _fail("INVALID_PLAN_GENERATED_FORMAT")
                desc = step.get("description")
                if desc is not None and not isinstance(desc, str):
                    return _fail("INVALID_PLAN_GENERATED_FORMAT")

                if desc:
                    formatted_steps.append(f"{title}\n{desc}")
                else:
                    formatted_steps.append(title)

            parsed_activities.append(ReviewActivity(
                activity_type="PLAN_GENERATED",
                create_time_utc=create_time_utc,
                title="\n\n".join(formatted_steps),
            ))

        elif event_type == "progressUpdated":
            title = event_data.get("title")
            if not isinstance(title, str):
                return _fail("INVALID_PROGRESS_UPDATED_FORMAT")
            desc = event_data.get("description")
            if desc is not None and not isinstance(desc, str):
                return _fail("INVALID_PROGRESS_UPDATED_FORMAT")

            parsed_activities.append(ReviewActivity(
                activity_type="PROGRESS_UPDATED",
                create_time_utc=create_time_utc,
                title=title,
                description=desc
            ))

        elif event_type == "planApproved":
            parsed_activities.append(ReviewActivity(
                activity_type="PLAN_APPROVED"
                # create_time_utc 등 메타데이터 미포함
            ))

        elif event_type == "sessionCompleted":
            parsed_activities.append(ReviewActivity(
                activity_type="SESSION_COMPLETED"
                # create_time_utc 등 메타데이터 미포함
            ))

        else:
            return _fail("UNSUPPORTED_OR_FORBIDDEN_EVENT")

    return {"status": "SUCCESS", "activities": parsed_activities}
