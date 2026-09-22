"""SQLite 기반 Orchestrator 상태 저장소 구현."""

import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import List, Optional, Union
from .models import (
    TaskRecord,
    ApprovalEvidence,
    ApprovalHistoryItem,
    ExecutionRecord,
    StateTransition,
    ScopeValidationRecord,
    PersistentSessionBinding,
)
from .validator import validate_utc_iso8601

REASON_CODE_REGEX = re.compile(r"^[A-Z0-9_]{1,64}$")


def validate_reason_code(code: str) -> None:
    """원시 로그 비저장 경계 강제: 사유 코드는 1~64자의 대문자, 숫자, 언더스코어만 허용합니다.

    자유 텍스트, 제어문자, 공백, 과도한 길이는 RepositoryError로 거부됩니다.
    """
    if not code or not isinstance(code, str):
        raise RepositoryError("사유 코드는 비어 있을 수 없습니다.")

    # 제어문자 또는 공백 포함 여부 검사
    for ch in code:
        if ch.isspace() or unicodedata.category(ch).startswith("C"):
            raise RepositoryError(f"사유 코드에 제어문자 또는 공백이 포함될 수 없습니다: '{code}'")

    if not REASON_CODE_REGEX.match(code):
        raise RepositoryError(
            f"유효하지 않은 사유 코드 형식: '{code}'. 1~64자의 대문자, 숫자, 언더스코어만 허용됩니다."
        )


class RepositoryError(Exception):
    """상태 저장소 기본 예외 클래스."""

    pass


class RepositoryBindingConflictError(RepositoryError):
    """결속(Binding) 상충 시 발생시키는 예외 클래스."""

    pass


class StateRepository:
    """Git 작업 트리 밖의 SQLite 상태 저장소를 관리하는 최소 저장소 클래스.

    실제 `ORCHESTRATOR_STATE_DIR`이나 환경 변수를 직접 조회하지 않으며,
    호출자로부터 주입된 DB 경로 또는 주입 가능 설정으로 동작합니다.
    """

    def __init__(self, db_path: Union[str, Path]):
        if not db_path:
            raise RepositoryError("DB 경로는 비어 있을 수 없습니다.")

        self.db_path = Path(db_path)
        try:
            if not self.db_path.parent.exists():
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RepositoryError(f"DB 디렉토리 생성 실패: {str(e)}")

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            raise RepositoryError(f"SQLite 데이터베이스 연결 실패: {str(e)}")

    def _init_db(self) -> None:
        """최소 테이블 스키마 생성."""
        schema = """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            base_commit_sha TEXT NOT NULL,
            contract_hash TEXT NOT NULL,
            approved_scope_hash TEXT NOT NULL,
            idempotency_key TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at_utc TEXT NOT NULL,
            updated_at_utc TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS approval_evidences (
            approval_id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            contract_version TEXT NOT NULL,
            contract_hash TEXT NOT NULL,
            approved_scope_hash TEXT NOT NULL,
            approver TEXT NOT NULL,
            approval_time_utc TEXT NOT NULL,
            status TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS approval_histories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            approval_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            contract_hash TEXT NOT NULL,
            approved_scope_hash TEXT NOT NULL,
            status TEXT NOT NULL,
            recorded_at_utc TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS executions (
            execution_id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            execution_agent TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at_utc TEXT NOT NULL,
            ended_at_utc TEXT
        );

        CREATE TABLE IF NOT EXISTS state_transitions (
            transition_id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            from_status TEXT NOT NULL,
            to_status TEXT NOT NULL,
            transition_agent TEXT NOT NULL,
            recorded_at_utc TEXT NOT NULL,
            reason TEXT
        );

        CREATE TABLE IF NOT EXISTS scope_validations (
            validation_id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            contract_hash TEXT NOT NULL,
            approved_scope_hash TEXT NOT NULL,
            is_valid INTEGER NOT NULL,
            status TEXT NOT NULL,
            checked_at_utc TEXT NOT NULL,
            reasons_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS persistent_session_bindings (
            task_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            branch_name TEXT NOT NULL,
            pr_number INTEGER NOT NULL,
            contract_hash TEXT NOT NULL,
            approved_scope_hash TEXT NOT NULL,
            recorded_at_utc TEXT NOT NULL,
            PRIMARY KEY (task_id, session_id),
            UNIQUE (session_id),
            UNIQUE (branch_name),
            UNIQUE (pr_number)
        );
        """
        with self._get_connection() as conn:
            conn.executescript(schema)
            conn.commit()

    # 1. TaskRecord 관리
    def save_task(self, task: TaskRecord) -> None:
        """Task 레코드를 저장하거나 상태를 업데이트합니다.

        동일 task_id에 대해 base_commit_sha, contract_hash, approved_scope_hash,
        idempotency_key가 변경되는 경우 결속 상충(RepositoryBindingConflictError)을 발생시킵니다.
        """
        is_valid, msg = validate_utc_iso8601(task.created_at_utc)
        if not is_valid:
            raise RepositoryError(f"created_at_utc 유효성 오류: {msg}")

        is_valid, msg = validate_utc_iso8601(task.updated_at_utc)
        if not is_valid:
            raise RepositoryError(f"updated_at_utc 유효성 오류: {msg}")

        existing = self.get_task(task.task_id)
        if existing:
            if (
                existing.base_commit_sha != task.base_commit_sha
                or existing.contract_hash != task.contract_hash
                or existing.approved_scope_hash != task.approved_scope_hash
                or existing.idempotency_key != task.idempotency_key
            ):
                raise RepositoryBindingConflictError(
                    f"Task '{task.task_id}'의 식별 결속 정보(base_commit_sha, contract_hash, approved_scope_hash, idempotency_key)는 변경할 수 없습니다."
                )
            query = """
            UPDATE tasks
            SET status = ?, updated_at_utc = ?
            WHERE task_id = ?
            """
            with self._get_connection() as conn:
                conn.execute(query, (task.status, task.updated_at_utc, task.task_id))
                conn.commit()
        else:
            query = """
            INSERT INTO tasks (task_id, base_commit_sha, contract_hash, approved_scope_hash, idempotency_key, status, created_at_utc, updated_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            with self._get_connection() as conn:
                conn.execute(
                    query,
                    (
                        task.task_id,
                        task.base_commit_sha,
                        task.contract_hash,
                        task.approved_scope_hash,
                        task.idempotency_key,
                        task.status,
                        task.created_at_utc,
                        task.updated_at_utc,
                    ),
                )
                conn.commit()

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        query = "SELECT task_id, base_commit_sha, contract_hash, approved_scope_hash, idempotency_key, status, created_at_utc, updated_at_utc FROM tasks WHERE task_id = ?"
        with self._get_connection() as conn:
            cursor = conn.execute(query, (task_id,))
            row = cursor.fetchone()
            if row:
                return TaskRecord(
                    task_id=row["task_id"],
                    base_commit_sha=row["base_commit_sha"],
                    contract_hash=row["contract_hash"],
                    approved_scope_hash=row["approved_scope_hash"],
                    idempotency_key=row["idempotency_key"],
                    status=row["status"],
                    created_at_utc=row["created_at_utc"],
                    updated_at_utc=row["updated_at_utc"],
                )
            return None

    # 2. ApprovalEvidence & ApprovalHistoryItem 관리
    def save_approval_evidence(self, evidence: ApprovalEvidence) -> None:
        """ApprovalEvidence를 불변 저장합니다.

        동일 approval_id 레코드는 결속 정보뿐 아니라 승인자, 승인 시각, 상태도 덮어쓰지 않고 불변 증적으로 관리합니다.
        완전히 동일한 객체 재저장 시 멱등 처리하며, 필드가 다를 경우 RepositoryBindingConflictError를 발생시킵니다.
        """
        is_valid, msg = validate_utc_iso8601(evidence.approval_time_utc)
        if not is_valid:
            raise RepositoryError(f"approval_time_utc 유효성 오류: {msg}")

        existing = self.get_approval_evidence(evidence.approval_id)
        if existing:
            if (
                existing.task_id != evidence.task_id
                or existing.contract_version != evidence.contract_version
                or existing.contract_hash != evidence.contract_hash
                or existing.approved_scope_hash != evidence.approved_scope_hash
                or existing.approver != evidence.approver
                or existing.approval_time_utc != evidence.approval_time_utc
                or existing.status != evidence.status
            ):
                raise RepositoryBindingConflictError(
                    f"ApprovalEvidence '{evidence.approval_id}'는 불변 증적입니다. 기존 정보를 변경/덮어쓸 수 없습니다."
                )
            # 완전히 동일하므로 멱등적으로 성공 무시
            return

        query = """
        INSERT INTO approval_evidences (approval_id, task_id, contract_version, contract_hash, approved_scope_hash, approver, approval_time_utc, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._get_connection() as conn:
            conn.execute(
                query,
                (
                    evidence.approval_id,
                    evidence.task_id,
                    evidence.contract_version,
                    evidence.contract_hash,
                    evidence.approved_scope_hash,
                    evidence.approver,
                    evidence.approval_time_utc,
                    evidence.status,
                ),
            )
            conn.commit()

    def get_approval_evidence(self, approval_id: str) -> Optional[ApprovalEvidence]:
        query = "SELECT approval_id, task_id, contract_version, contract_hash, approved_scope_hash, approver, approval_time_utc, status FROM approval_evidences WHERE approval_id = ?"
        with self._get_connection() as conn:
            cursor = conn.execute(query, (approval_id,))
            row = cursor.fetchone()
            if row:
                return ApprovalEvidence(
                    approval_id=row["approval_id"],
                    task_id=row["task_id"],
                    contract_version=row["contract_version"],
                    contract_hash=row["contract_hash"],
                    approved_scope_hash=row["approved_scope_hash"],
                    approver=row["approver"],
                    approval_time_utc=row["approval_time_utc"],
                    status=row["status"],
                )
            return None

    def save_approval_history_item(self, item: ApprovalHistoryItem) -> None:
        """ApprovalHistoryItem을 append-only 저장합니다.

        - 같은 (approval_id, recorded_at_utc)에 결속(task_id, contract_hash, approved_scope_hash)이나 상태가 다른 레코드가 존재하면 RepositoryBindingConflictError를 발생시킵니다.
        - 완전히 동일한 이력 레코드는 멱등적으로 무시합니다.
        """
        is_valid, msg = validate_utc_iso8601(item.recorded_at_utc)
        if not is_valid:
            raise RepositoryError(f"recorded_at_utc 유효성 오류: {msg}")

        check_query = """
        SELECT approval_id, task_id, contract_hash, approved_scope_hash, status, recorded_at_utc
        FROM approval_histories
        WHERE approval_id = ? AND recorded_at_utc = ?
        """
        with self._get_connection() as conn:
            cursor = conn.execute(check_query, (item.approval_id, item.recorded_at_utc))
            rows = cursor.fetchall()
            for row in rows:
                if (
                    row["task_id"] != item.task_id
                    or row["contract_hash"] != item.contract_hash
                    or row["approved_scope_hash"] != item.approved_scope_hash
                    or row["status"] != item.status
                ):
                    raise RepositoryBindingConflictError(
                        f"동일 승인 식별자 '{item.approval_id}' 및 동일 UTC 시각 '{item.recorded_at_utc}'에 상충되는 이력이 존재합니다."
                    )
                else:
                    # 완전 동일한 레코드가 이미 존재하면 멱등 무시
                    return

            insert_query = """
            INSERT INTO approval_histories (approval_id, task_id, contract_hash, approved_scope_hash, status, recorded_at_utc)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            conn.execute(
                insert_query,
                (
                    item.approval_id,
                    item.task_id,
                    item.contract_hash,
                    item.approved_scope_hash,
                    item.status,
                    item.recorded_at_utc,
                ),
            )
            conn.commit()

    def get_approval_history(self, task_id: str) -> List[ApprovalHistoryItem]:
        """Task ID 기반으로 승인 이력 목록을 recorded_at_utc ASC 시간순으로 반환합니다."""
        query = "SELECT approval_id, task_id, contract_hash, approved_scope_hash, status, recorded_at_utc FROM approval_histories WHERE task_id = ? ORDER BY recorded_at_utc ASC, id ASC"
        with self._get_connection() as conn:
            cursor = conn.execute(query, (task_id,))
            rows = cursor.fetchall()
            return [
                ApprovalHistoryItem(
                    approval_id=row["approval_id"],
                    task_id=row["task_id"],
                    contract_hash=row["contract_hash"],
                    approved_scope_hash=row["approved_scope_hash"],
                    status=row["status"],
                    recorded_at_utc=row["recorded_at_utc"],
                )
                for row in rows
            ]

    # 6. PersistentSessionBinding 관리
    def save_persistent_session_binding(self, binding: PersistentSessionBinding) -> None:
        """PersistentSessionBinding을 저장합니다.

        세션 ID, 브랜치명, PR 번호 중복(UNIQUE 제약 위배) 혹은 동일 PK(task_id, session_id)라도
        결속 해시가 다른 경우 RepositoryBindingConflictError를 발생시켜 중복을 차단합니다.
        동일한 데이터의 재입력은 멱등적으로 성공(무시) 처리합니다.
        """
        is_valid, msg = validate_utc_iso8601(binding.recorded_at_utc)
        if not is_valid:
            raise RepositoryError(f"recorded_at_utc 유효성 오류: {msg}")

        # 기존 동일 세션 레코드 확인 (동일 데이터 멱등성 및 변경/상충 방지)
        existing_query = """
        SELECT task_id, session_id, branch_name, pr_number, contract_hash, approved_scope_hash, recorded_at_utc
        FROM persistent_session_bindings
        WHERE session_id = ?
        """
        with self._get_connection() as conn:
            cursor = conn.execute(existing_query, (binding.session_id,))
            row = cursor.fetchone()
            if row:
                if (
                    row["task_id"] != binding.task_id
                    or row["branch_name"] != binding.branch_name
                    or row["pr_number"] != binding.pr_number
                    or row["contract_hash"] != binding.contract_hash
                    or row["approved_scope_hash"] != binding.approved_scope_hash
                ):
                    raise RepositoryBindingConflictError(
                        f"세션 '{binding.session_id}'에 대해 이미 상충되는 바인딩 정보가 존재합니다."
                    )
                # 완전히 동일한 정보의 재삽입 요청은 멱등성 보장을 위해 무시 (성공)
                return

            # UNIQUE 제약 조건 검증: branch_name, pr_number 중복 확인
            conflict_check_query = """
            SELECT session_id FROM persistent_session_bindings
            WHERE branch_name = ? OR pr_number = ?
            """
            cursor = conn.execute(conflict_check_query, (binding.branch_name, binding.pr_number))
            conflict_row = cursor.fetchone()
            if conflict_row:
                raise RepositoryBindingConflictError(
                    f"브랜치명 '{binding.branch_name}' 또는 PR 번호 '{binding.pr_number}'가 다른 세션에서 이미 사용 중입니다."
                )

            # 새 레코드 추가
            insert_query = """
            INSERT INTO persistent_session_bindings (
                task_id, session_id, branch_name, pr_number, contract_hash, approved_scope_hash, recorded_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            try:
                conn.execute(
                    insert_query,
                    (
                        binding.task_id,
                        binding.session_id,
                        binding.branch_name,
                        binding.pr_number,
                        binding.contract_hash,
                        binding.approved_scope_hash,
                        binding.recorded_at_utc,
                    ),
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                # SQLite UNIQUE / PK 제약 위반 발생 시 포착 (Race condition 등 대응)
                raise RepositoryBindingConflictError(f"데이터베이스 무결성 제약 위반: {str(e)}")

    def get_persistent_session_binding(self, session_id: str) -> Optional[PersistentSessionBinding]:
        """주어진 세션 ID에 대한 바인딩 정보를 반환합니다."""
        query = """
        SELECT task_id, session_id, branch_name, pr_number, contract_hash, approved_scope_hash, recorded_at_utc
        FROM persistent_session_bindings
        WHERE session_id = ?
        """
        with self._get_connection() as conn:
            cursor = conn.execute(query, (session_id,))
            row = cursor.fetchone()
            if row:
                return PersistentSessionBinding(
                    task_id=row["task_id"],
                    session_id=row["session_id"],
                    branch_name=row["branch_name"],
                    pr_number=row["pr_number"],
                    contract_hash=row["contract_hash"],
                    approved_scope_hash=row["approved_scope_hash"],
                    recorded_at_utc=row["recorded_at_utc"],
                )
            return None

    # 3. ExecutionRecord 관리
    def save_execution(self, execution: ExecutionRecord) -> None:
        """ExecutionRecord를 저장하거나 상태/종료시각을 업데이트합니다."""
        is_valid, msg = validate_utc_iso8601(execution.started_at_utc)
        if not is_valid:
            raise RepositoryError(f"started_at_utc 유효성 오류: {msg}")

        if execution.ended_at_utc:
            is_valid, msg = validate_utc_iso8601(execution.ended_at_utc)
            if not is_valid:
                raise RepositoryError(f"ended_at_utc 유효성 오류: {msg}")

        existing_query = "SELECT execution_id, task_id FROM executions WHERE execution_id = ?"
        with self._get_connection() as conn:
            cursor = conn.execute(existing_query, (execution.execution_id,))
            row = cursor.fetchone()
            if row:
                if row["task_id"] != execution.task_id:
                    raise RepositoryBindingConflictError(
                        f"Execution '{execution.execution_id}'의 task_id 결속 정보는 변경할 수 없습니다."
                    )
                query = """
                UPDATE executions
                SET status = ?, ended_at_utc = ?
                WHERE execution_id = ?
                """
                conn.execute(query, (execution.status, execution.ended_at_utc, execution.execution_id))
            else:
                query = """
                INSERT INTO executions (execution_id, task_id, execution_agent, status, started_at_utc, ended_at_utc)
                VALUES (?, ?, ?, ?, ?, ?)
                """
                conn.execute(
                    query,
                    (
                        execution.execution_id,
                        execution.task_id,
                        execution.execution_agent,
                        execution.status,
                        execution.started_at_utc,
                        execution.ended_at_utc,
                    ),
                )
            conn.commit()

    def get_executions(self, task_id: str) -> List[ExecutionRecord]:
        query = "SELECT execution_id, task_id, execution_agent, status, started_at_utc, ended_at_utc FROM executions WHERE task_id = ? ORDER BY started_at_utc ASC"
        with self._get_connection() as conn:
            cursor = conn.execute(query, (task_id,))
            rows = cursor.fetchall()
            return [
                ExecutionRecord(
                    execution_id=row["execution_id"],
                    task_id=row["task_id"],
                    execution_agent=row["execution_agent"],
                    status=row["status"],
                    started_at_utc=row["started_at_utc"],
                    ended_at_utc=row["ended_at_utc"],
                )
                for row in rows
            ]

    # 4. StateTransition 관리 (Append-only)
    def save_state_transition(self, transition: StateTransition) -> None:
        """StateTransition 기록을 추가합니다 (Append-only)."""
        is_valid, msg = validate_utc_iso8601(transition.recorded_at_utc)
        if not is_valid:
            raise RepositoryError(f"recorded_at_utc 유효성 오류: {msg}")

        if transition.reason:
            validate_reason_code(transition.reason)

        existing_query = "SELECT transition_id FROM state_transitions WHERE transition_id = ?"
        with self._get_connection() as conn:
            cursor = conn.execute(existing_query, (transition.transition_id,))
            if cursor.fetchone():
                raise RepositoryError(f"Transition ID '{transition.transition_id}'가 이미 존재합니다. 상태 전이는 append-only입니다.")

            query = """
            INSERT INTO state_transitions (transition_id, task_id, from_status, to_status, transition_agent, recorded_at_utc, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            conn.execute(
                query,
                (
                    transition.transition_id,
                    transition.task_id,
                    transition.from_status,
                    transition.to_status,
                    transition.transition_agent,
                    transition.recorded_at_utc,
                    transition.reason,
                ),
            )
            conn.commit()

    def get_state_transitions(self, task_id: str) -> List[StateTransition]:
        query = "SELECT transition_id, task_id, from_status, to_status, transition_agent, recorded_at_utc, reason FROM state_transitions WHERE task_id = ? ORDER BY recorded_at_utc ASC"
        with self._get_connection() as conn:
            cursor = conn.execute(query, (task_id,))
            rows = cursor.fetchall()
            return [
                StateTransition(
                    transition_id=row["transition_id"],
                    task_id=row["task_id"],
                    from_status=row["from_status"],
                    to_status=row["to_status"],
                    transition_agent=row["transition_agent"],
                    recorded_at_utc=row["recorded_at_utc"],
                    reason=row["reason"],
                )
                for row in rows
            ]

    # 5. ScopeValidationRecord 관리
    def save_scope_validation(self, record: ScopeValidationRecord) -> None:
        """ScopeValidationRecord를 추가합니다."""
        is_valid, msg = validate_utc_iso8601(record.checked_at_utc)
        if not is_valid:
            raise RepositoryError(f"checked_at_utc 유효성 오류: {msg}")

        if record.reasons:
            for reason in record.reasons:
                validate_reason_code(reason)

        existing_query = "SELECT validation_id FROM scope_validations WHERE validation_id = ?"
        with self._get_connection() as conn:
            cursor = conn.execute(existing_query, (record.validation_id,))
            if cursor.fetchone():
                raise RepositoryError(f"Validation ID '{record.validation_id}'가 이미 존재합니다.")

            query = """
            INSERT INTO scope_validations (validation_id, task_id, contract_hash, approved_scope_hash, is_valid, status, checked_at_utc, reasons_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            conn.execute(
                query,
                (
                    record.validation_id,
                    record.task_id,
                    record.contract_hash,
                    record.approved_scope_hash,
                    1 if record.is_valid else 0,
                    record.status,
                    record.checked_at_utc,
                    json.dumps(record.reasons, ensure_ascii=False),
                ),
            )
            conn.commit()

    def get_scope_validations(self, task_id: str) -> List[ScopeValidationRecord]:
        query = "SELECT validation_id, task_id, contract_hash, approved_scope_hash, is_valid, status, checked_at_utc, reasons_json FROM scope_validations WHERE task_id = ? ORDER BY checked_at_utc ASC"
        with self._get_connection() as conn:
            cursor = conn.execute(query, (task_id,))
            rows = cursor.fetchall()
            return [
                ScopeValidationRecord(
                    validation_id=row["validation_id"],
                    task_id=row["task_id"],
                    contract_hash=row["contract_hash"],
                    approved_scope_hash=row["approved_scope_hash"],
                    is_valid=bool(row["is_valid"]),
                    status=row["status"],
                    checked_at_utc=row["checked_at_utc"],
                    reasons=json.loads(row["reasons_json"]),
                )
                for row in rows
            ]
