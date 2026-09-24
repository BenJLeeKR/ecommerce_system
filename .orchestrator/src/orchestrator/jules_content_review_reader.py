"""Jules Content Handoff Reader.

사용자 수동 검토(Human Review) 요청에 대해 Jules 세션의 활동 기록 원문을 안전하게 읽어오는 전용 경계(Reader)입니다.
- 자동 검토, 자동 Plan 승인, 자동 병합 기능은 일절 제공하지 않습니다.
- 반환된 원문 객체(ReviewActivity)는 메모리에서만 사용되어야 하며 직렬화, 로깅, DB 저장이 금지됩니다.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .jules_adapter import JulesAdapter, JulesSessionResponse
from .validator import ApprovalEvidence, TaskContract


@dataclass
class ReviewActivity:
    """수동 검토를 위해 추출된 단일 활동 원문 데이터 클래스.

    모든 로깅, 직렬화(to_dict), 문자열 변환(__str__, __repr__) 시
    실제 민감 원문 내용을 <REDACTED> 처리하여 유출을 방지합니다.
    """
    activity_type: str
    create_time_utc: str
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
) -> Optional[List[ReviewActivity]]:
    """사전 검증 후 Jules 세션의 수동 검토용 원문 활동 목록을 조회합니다.

    [검증 규칙]
    - evidence.status == 'ACTIVE'
    - contract.plan_approval_required == True
    - contract.auto_merge == False
    - contract.task_id == session_response.task_id
    - 요청된 session_id == session_response.session_id (리소스 네임 일치 여부)

    검증 실패 시 API 호출은 0회이며 즉시 None을 반환(상위에서 NEEDS_HUMAN_REVIEW 처리)합니다.
    """
    if evidence.status != "ACTIVE":
        return None
    if not getattr(contract, "plan_approval_required", False):
        return None
    if getattr(contract, "auto_merge", True):
        return None
    if contract.task_id != session_response.task_id:
        return None
    if session_id != session_response.session_id:
        return None

    # 사전 검증 통과 후 Adapter의 전용 메서드를 통해 원시 액티비티를 안전하게 조회
    # (일반 summary 조회나 전제 조건 없는 API 호출을 방지)
    if not hasattr(adapter, "fetch_raw_activities_for_content_review"):
        return None

    raw_activities = adapter.fetch_raw_activities_for_content_review(session_id)
    if raw_activities is None:
        return None

    parsed_activities = []

    for dt, act in raw_activities:
        create_time_utc = dt.isoformat()

        # 1. agentMessaged
        if "agentMessaged" in act:
            agent_data = act["agentMessaged"]
            if not isinstance(agent_data, dict):
                return None
            msg = agent_data.get("agentMessage")
            if not isinstance(msg, str):
                return None
            parsed_activities.append(ReviewActivity(
                activity_type="AGENT_MESSAGED",
                create_time_utc=create_time_utc,
                agent_message=msg
            ))
            continue

        # 2. planGenerated
        if "planGenerated" in act:
            plan_gen_data = act["planGenerated"]
            if not isinstance(plan_gen_data, dict) or "plan" not in plan_gen_data:
                return None
            plan_data = plan_gen_data["plan"]
            if not isinstance(plan_data, dict) or "steps" not in plan_data:
                return None
            steps = plan_data["steps"]
            if not isinstance(steps, list) or len(steps) == 0:
                return None

            # steps의 모든 title(필수), description(선택) 추출
            # 하나의 planGenerated에 대해 step들을 묶어서 텍스트화하거나 각각을 저장 (여기선 텍스트 결합 방식 사용)
            combined_titles = []
            combined_descs = []
            is_valid = True
            for step in steps:
                if not isinstance(step, dict):
                    is_valid = False
                    break
                title = step.get("title")
                if not isinstance(title, str):
                    is_valid = False
                    break
                desc = step.get("description", "")
                if desc is not None and not isinstance(desc, str):
                    is_valid = False
                    break

                combined_titles.append(title)
                if desc:
                    combined_descs.append(desc)

            if not is_valid:
                return None

            parsed_activities.append(ReviewActivity(
                activity_type="PLAN_GENERATED",
                create_time_utc=create_time_utc,
                title="\n".join(combined_titles),
                description="\n".join(combined_descs) if combined_descs else None
            ))
            continue

        # 3. progressUpdated
        if "progressUpdated" in act:
            prog_data = act["progressUpdated"]
            if not isinstance(prog_data, dict):
                return None
            title = prog_data.get("title")
            if not isinstance(title, str):
                return None
            desc = prog_data.get("description")
            if desc is not None and not isinstance(desc, str):
                return None

            parsed_activities.append(ReviewActivity(
                activity_type="PROGRESS_UPDATED",
                create_time_utc=create_time_utc,
                title=title,
                description=desc
            ))
            continue

        # 4. planApproved (텍스트 없는 유형 표식만)
        if "planApproved" in act:
            # 원시 데이터가 dict인지 확인하지만 그 안의 세부 필드는 추출하지 않음
            if not isinstance(act["planApproved"], dict):
                return None
            parsed_activities.append(ReviewActivity(
                activity_type="PLAN_APPROVED",
                create_time_utc=create_time_utc
            ))
            continue

        # 5. sessionCompleted (텍스트 없는 유형 표식만)
        if "sessionCompleted" in act:
            if not isinstance(act["sessionCompleted"], dict):
                return None
            parsed_activities.append(ReviewActivity(
                activity_type="SESSION_COMPLETED",
                create_time_utc=create_time_utc
            ))
            continue

        # 그 외 식별되지 않은 이벤트(sessionFailed, userMessaged 등)나 형식이 불일치하는 경우
        # (userMessaged는 민감 정보 노출 우려로 반환 거부, sessionFailed 등 미확인 필드는 추정 금지)
        return None

    return parsed_activities
