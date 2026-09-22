"""Orchestrator Phase 1 데이터 모델."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union


@dataclass
class PathItem:
    path: str
    kind: str  # 'file' 또는 'directory_recursive'

    def to_dict(self) -> Dict[str, str]:
        return {
            "path": self.path,
            "kind": self.kind
        }


@dataclass
class TaskContract:
    task_id: str
    contract_version: str
    project_profile_id: str
    project_profile_version: str
    project_profile_reference_path: str
    goal: str
    target_repository: str
    base_branch: str
    base_commit_sha: str
    execution_agent: str
    reference_documents: List[str]
    allowed_paths: List[PathItem]
    forbidden_paths: List[PathItem]
    risk_level: str
    completion_conditions: List[str]
    idempotency_key: str
    plan_approval_required: bool
    cancellation_conditions: List[str]
    auto_merge: bool
    raw_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApprovalEvidence:
    approval_id: str
    task_id: str
    contract_version: str
    contract_hash: str
    approved_scope_hash: str
    approver: str
    approval_time_utc: str
    status: str  # 예: 'ACTIVE', 'WITHDRAWN', 'MODIFIED', 'EXPIRED'


@dataclass
class ApprovalHistoryItem:
    approval_id: str
    task_id: str
    contract_hash: str
    approved_scope_hash: str
    status: str  # 예: 'ACTIVE', 'WITHDRAWN', 'MODIFIED', 'EXPIRED'
    recorded_at_utc: str


@dataclass
class TaskRecord:
    task_id: str
    base_commit_sha: str
    contract_hash: str
    approved_scope_hash: str
    idempotency_key: str
    status: str
    created_at_utc: str
    updated_at_utc: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "base_commit_sha": self.base_commit_sha,
            "contract_hash": self.contract_hash,
            "approved_scope_hash": self.approved_scope_hash,
            "idempotency_key": self.idempotency_key,
            "status": self.status,
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
        }


@dataclass
class ExecutionRecord:
    execution_id: str
    task_id: str
    execution_agent: str
    status: str  # e.g., 'DISPATCHED', 'RUNNING', 'COMPLETED', 'FAILED'
    started_at_utc: str
    ended_at_utc: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "execution_agent": self.execution_agent,
            "status": self.status,
            "started_at_utc": self.started_at_utc,
            "ended_at_utc": self.ended_at_utc,
        }


@dataclass
class StateTransition:
    transition_id: str
    task_id: str
    from_status: str
    to_status: str
    transition_agent: str
    recorded_at_utc: str
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "task_id": self.task_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "transition_agent": self.transition_agent,
            "recorded_at_utc": self.recorded_at_utc,
            "reason": self.reason,
        }


@dataclass
class ScopeValidationRecord:
    validation_id: str
    task_id: str
    contract_hash: str
    approved_scope_hash: str
    is_valid: bool
    status: str
    checked_at_utc: str
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "validation_id": self.validation_id,
            "task_id": self.task_id,
            "contract_hash": self.contract_hash,
            "approved_scope_hash": self.approved_scope_hash,
            "is_valid": self.is_valid,
            "status": self.status,
            "checked_at_utc": self.checked_at_utc,
            "reasons": self.reasons,
        }


@dataclass
class ScopeValidationResult:
    is_valid: bool
    reasons: List[str] = field(default_factory=list)
    approved_scope_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "reasons": self.reasons,
            "approved_scope_hash": self.approved_scope_hash,
        }


@dataclass
class ValidationResult:
    is_valid: bool
    is_dispatch_eligible: bool
    status: str
    reasons: List[str] = field(default_factory=list)
    contract_hash: Optional[str] = None
    approved_scope_hash: Optional[str] = None
    contract: Optional[TaskContract] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "is_dispatch_eligible": self.is_dispatch_eligible,
            "status": self.status,
            "reasons": self.reasons,
            "contract_hash": self.contract_hash,
            "approved_scope_hash": self.approved_scope_hash
        }


@dataclass
class ExecutionResultInput:
    """Jules 실행 결과 및 바인딩 정보를 포함하는 외부 주입 DTO."""
    task_id: str
    session_id: str
    branch_name: str
    pr_identifier: Optional[Any]  # int (PR 번호) 또는 str (https PR URL)
    status: str
    changed_files: List[str]
    verification_summary_codes: List[str]
    scope_validation_result: Optional[ScopeValidationResult]
    contract_hash: str
    approved_scope_hash: str
    idempotency_key: str
    approval_id: str


@dataclass
class PersistentSessionBinding:
    """Jules 세션과 실제 Git 브랜치, PR 번호를 1:1:1로 영속 결속하는 데이터 모델."""
    task_id: str
    session_id: str
    branch_name: str
    pr_number: int
    contract_hash: str
    approved_scope_hash: str
    recorded_at_utc: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "branch_name": self.branch_name,
            "pr_number": self.pr_number,
            "contract_hash": self.contract_hash,
            "approved_scope_hash": self.approved_scope_hash,
            "recorded_at_utc": self.recorded_at_utc,
        }


@dataclass
class CodexReviewResultPackage:
    """Codex 검토 대기용 구조화 결과 패키지 데이터 모델.

    주의: 본 패키지 모델은 승인(APPROVED), 종료(CLOSED), 자동 dispatch 적격성(is_dispatch_eligible),
    병합 가능 여부(is_mergeable) 등 어떠한 권한/결정 필드도 포함하지 않으며,
    자유 문자열(원시 로그, 프롬프트, 비밀값 등)을 보존하지 않습니다.
    """
    task_id: str
    session_id: str
    branch_name: str
    pr_identifier: Any
    status: str  # 'RESULT_COLLECTED' 또는 'NEEDS_HUMAN_REVIEW'
    changed_files: List[str]
    verification_summary_codes: List[str]
    scope_validation_result: Optional[ScopeValidationResult]
    contract_hash: str
    approved_scope_hash: str
    idempotency_key: str
    approval_id: str
    reason_codes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "branch_name": self.branch_name,
            "pr_identifier": self.pr_identifier,
            "status": self.status,
            "changed_files": self.changed_files,
            "verification_summary_codes": self.verification_summary_codes,
            "scope_validation_result": (
                self.scope_validation_result.to_dict()
                if self.scope_validation_result
                else None
            ),
            "contract_hash": self.contract_hash,
            "approved_scope_hash": self.approved_scope_hash,
            "idempotency_key": self.idempotency_key,
            "approval_id": self.approval_id,
            "reason_codes": self.reason_codes,
        }
