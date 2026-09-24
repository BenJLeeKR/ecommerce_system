"""Jules 세션 생성 어댑터, 세션 바인딩 및 상태 전이 관리 모듈."""

import json
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable
from .models import PathItem
from .canonicalization import canonicalize_scope, ScopeCanonicalizationError


REASON_CODE_REGEX = re.compile(r"^[A-Z0-9_]{1,64}$")
# sources/ 뒤 하나 이상의 안전한 경로 세그먼트(영문자·숫자·_·-)만 허용
SOURCE_NAME_REGEX = re.compile(r"^sources/([a-zA-Z0-9_\-]+)(/[a-zA-Z0-9_\-]+)*$")


def validate_reason_code(code: Optional[str]) -> bool:
    """구조화 사유 코드가 1~64자의 대문자, 숫자, 언더스코어만 포함하는지 검증합니다."""
    if code is None:
        return True
    return bool(REASON_CODE_REGEX.match(code))


def validate_source_name(source_name: Optional[str]) -> bool:
    """소스 리소스 이름이 'sources/<id>' 또는 'sources/<segment1>/<segment2>/...' 형식인지 검증합니다.

    - sources/ 뒤 하나 이상의 영문, 숫자, _, - 세그먼트 허용
    - traversal(., ..), 역슬래시, 공백, 빈 세그먼트, 잘못된 접두어 거부
    """
    if not source_name or not isinstance(source_name, str):
        return False
    return bool(SOURCE_NAME_REGEX.match(source_name))


def current_utc_iso8601() -> str:
    """현재 시각을 UTC ISO 8601 형식(시간대 포함)으로 반환합니다."""
    return datetime.now(timezone.utc).isoformat()


def default_remote_main_sha_fn() -> Optional[str]:
    """원격 origin/main을 갱신하고 현재 SHA를 반환합니다."""
    try:
        subprocess.run(["git", "fetch", "origin", "main"], check=True, capture_output=True)
        res = subprocess.run(["git", "rev-parse", "origin/main"], check=True, capture_output=True, text=True)
        return res.stdout.strip()
    except Exception:
        return None


@dataclass
class ActivitySummary:
    """비민감 구조화 활동 요약 데이터 모델."""
    total_count: int
    activity_types: List[str]
    is_completed: bool
    is_failed: bool
    is_temporal_order_reliable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_count": self.total_count,
            "activity_types": self.activity_types,
            "is_completed": self.is_completed,
            "is_failed": self.is_failed,
            "is_temporal_order_reliable": self.is_temporal_order_reliable,
        }

    def __repr__(self) -> str:
        return (
            f"ActivitySummary(total_count={self.total_count}, "
            f"activity_types={self.activity_types!r}, "
            f"is_completed={self.is_completed}, is_failed={self.is_failed}, "
            f"is_temporal_order_reliable={self.is_temporal_order_reliable})"
        )


@dataclass
class PreGateResult:
    """외부에서 전달된 사전 게이트(Pre-gate) 검증 결과 데이터 모델."""
    is_valid: bool
    is_dispatch_eligible: bool
    is_session_creation_authorized: bool
    status: str
    task_id: str
    contract_hash: str
    approved_scope_hash: str
    idempotency_key: str
    base_sha: str


@dataclass
class JulesSessionRequest:
    """Jules 세션 생성 요청 데이터 모델."""
    task_id: str
    contract_hash: str
    approved_scope_hash: str
    idempotency_key: str
    base_sha: str
    allowed_paths: List[PathItem]
    forbidden_paths: List[PathItem]
    source_name: str = field(repr=False) # 형식: 'sources/<id>' 또는 'sources/github/<owner>/<repo>' (명시적 주입 필수)
    prompt: Optional[str] = field(default="", repr=False)


@dataclass
class JulesSessionResponse:
    """Jules 세션 응답 데이터 모델."""
    session_id: str
    task_id: str
    branch_name: Optional[str]
    pr_number: Optional[int]
    status: str  # e.g., 'CREATED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'NEEDS_HUMAN_REVIEW'
    reason_code: Optional[str]
    created_at_utc: str
    updated_at_utc: str

    def to_dict(self) -> Dict[str, Optional[object]]:
        return {
            "session_id": self.session_id,
            "task_id": self.task_id,
            "branch_name": self.branch_name,
            "pr_number": self.pr_number,
            "status": self.status,
            "reason_code": self.reason_code,
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
        }

    def __repr__(self) -> str:
        # 안전한 repr: 민감정보 배제
        return (
            f"JulesSessionResponse(session_id={self.session_id!r}, task_id={self.task_id!r}, "
            f"branch_name={self.branch_name!r}, pr_number={self.pr_number!r}, "
            f"status={self.status!r}, reason_code={self.reason_code!r})"
        )


class JulesAdapter(ABC):
    """Jules 세션 어댑터의 최소 추상 인터페이스."""

    @abstractmethod
    def create_session(
        self, request: JulesSessionRequest, pre_gate_result: PreGateResult
    ) -> JulesSessionResponse:
        """사전 게이트 결과를 확인하고 새 Jules 세션을 생성합니다."""
        pass

    @abstractmethod
    def get_session_status(self, session_id: str) -> JulesSessionResponse:
        """세션 ID에 대한 현재 상태를 조회합니다."""
        pass

    @abstractmethod
    def bind_session_outputs(self, session_id: str, branch_name: str, pr_number: int) -> JulesSessionResponse:
        """세션에 Jules가 생성한 실제 작업 브랜치와 PR 번호를 사후 결속합니다."""
        pass

    @abstractmethod
    def transition_session_status(
        self, session_id: str, to_status: str, reason_code: Optional[str] = None
    ) -> JulesSessionResponse:
        """세션의 상태를 전이합니다."""
        pass

    @abstractmethod
    def cancel_session(
        self, session_id: str, reason_code: str = "SESSION_CANCELLED"
    ) -> JulesSessionResponse:
        """세션을 명시적으로 취소 상태로 전이합니다."""
        pass


class FakeJulesAdapter(JulesAdapter):
    """결정론적 가짜(Fake) Jules 어댑터.

    네트워크, 실제 Jules API, 환경 변수, 비밀값에 접근하지 않는 테스트 대역입니다.
    `clock_fn`을 주입받아 완전한 시간 결정론성을 보장할 수 있습니다.
    """

    def __init__(
        self,
        clock_fn: Optional[Callable[[], str]] = None,
        remote_main_sha_fn: Optional[Callable[[], Optional[str]]] = None
    ) -> None:
        self._sessions: Dict[str, JulesSessionResponse] = {}
        # 1:1:1 바인딩 인덱스
        self._branch_to_session: Dict[str, str] = {}
        self._pr_to_session: Dict[int, str] = {}
        self._task_to_session: Dict[str, str] = {}
        self._session_counter = 0
        self._clock_fn = clock_fn or current_utc_iso8601
        self._remote_main_sha_fn = remote_main_sha_fn or default_remote_main_sha_fn

    def _now(self) -> str:
        return self._clock_fn()

    def create_session(
        self, request: JulesSessionRequest, pre_gate_result: PreGateResult
    ) -> JulesSessionResponse:
        now = self._now()

        # 0. Canonical Scope Hash 사전 검증
        try:
            _, computed_scope_hash = canonicalize_scope(request.allowed_paths, request.forbidden_paths)
            if computed_scope_hash != request.approved_scope_hash:
                return JulesSessionResponse(
                    session_id="",
                    task_id=request.task_id,
                    branch_name=None,
                    pr_number=None,
                    status="NEEDS_HUMAN_REVIEW",
                    reason_code="SCOPE_HASH_MISMATCH",
                    created_at_utc=now,
                    updated_at_utc=now,
                )
        except Exception:
            return JulesSessionResponse(
                session_id="",
                task_id=request.task_id,
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="SCOPE_LOCK_CANONICALIZATION_FAILED",
                created_at_utc=now,
                updated_at_utc=now,
            )

        # 1. 사전 게이트 검증 (is_valid=True, is_session_creation_authorized=True, status="APPROVED" 요구)
        if (
            not pre_gate_result.is_valid
            or not pre_gate_result.is_session_creation_authorized
            or pre_gate_result.status != "APPROVED"
        ):
            return JulesSessionResponse(
                session_id="",
                task_id=request.task_id,
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="PREGATE_VALIDATION_FAILED",
                created_at_utc=now,
                updated_at_utc=now,
            )

        # 2. 실행 바인딩 및 Contract 기준 SHA 일치 검증
        if (
            request.task_id != pre_gate_result.task_id
            or request.contract_hash != pre_gate_result.contract_hash
            or request.approved_scope_hash != pre_gate_result.approved_scope_hash
            or request.idempotency_key != pre_gate_result.idempotency_key
            or request.base_sha != pre_gate_result.base_sha
        ):
            return JulesSessionResponse(
                session_id="",
                task_id=request.task_id,
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="BINDING_MISMATCH",
                created_at_utc=now,
                updated_at_utc=now,
            )

        # 3. 원격 origin/main 대조 및 SHA 확인
        actual_sha = self._remote_main_sha_fn()
        if not actual_sha or actual_sha != request.base_sha:
            return JulesSessionResponse(
                session_id="",
                task_id=request.task_id,
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="BASE_SHA_MISMATCH",
                created_at_utc=now,
                updated_at_utc=now,
            )

        # 3. source_name 검증 (추정 기본값 배제)
        if not validate_source_name(getattr(request, "source_name", None)):
            return JulesSessionResponse(
                session_id="",
                task_id=request.task_id,
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="INVALID_SOURCE_NAME",
                created_at_utc=now,
                updated_at_utc=now,
            )

        # 4. 1:1:1 바인딩 중복 및 상충 검사
        if request.task_id in self._task_to_session:
            existing_sid = self._task_to_session[request.task_id]
            return JulesSessionResponse(
                session_id=existing_sid,
                task_id=request.task_id,
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="DUPLICATE_BINDING_CONFLICT",
                created_at_utc=now,
                updated_at_utc=now,
            )

        # 결정론적 세션 ID 생성
        self._session_counter += 1
        session_id = f"SES-{request.task_id}-{self._session_counter:03d}"

        response = JulesSessionResponse(
            session_id=session_id,
            task_id=request.task_id,
            branch_name=None,
            pr_number=None,
            status="CREATED",
            reason_code=None,
            created_at_utc=now,
            updated_at_utc=now,
        )

        self._sessions[session_id] = response
        self._task_to_session[request.task_id] = session_id

        return response

    def get_session_status(self, session_id: str) -> JulesSessionResponse:
        now = self._now()
        if session_id not in self._sessions:
            return JulesSessionResponse(
                session_id=session_id,
                task_id="",
                branch_name="",
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="SESSION_NOT_FOUND",
                created_at_utc=now,
                updated_at_utc=now,
            )
        return self._sessions[session_id]

    def bind_session_outputs(self, session_id: str, branch_name: str, pr_number: int) -> JulesSessionResponse:
        now = self._now()
        if session_id not in self._sessions:
            return JulesSessionResponse(
                session_id=session_id,
                task_id="",
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="SESSION_NOT_FOUND",
                created_at_utc=now,
                updated_at_utc=now,
            )

        session = self._sessions[session_id]

        # PR 1:1 바인딩 검증
        if pr_number in self._pr_to_session and self._pr_to_session[pr_number] != session_id:
            session.status = "NEEDS_HUMAN_REVIEW"
            session.reason_code = "DUPLICATE_BINDING_CONFLICT"
            session.updated_at_utc = now
            return session

        # Branch 1:1 바인딩 검증
        if branch_name in self._branch_to_session and self._branch_to_session[branch_name] != session_id:
            session.status = "NEEDS_HUMAN_REVIEW"
            session.reason_code = "DUPLICATE_BINDING_CONFLICT"
            session.updated_at_utc = now
            return session

        if session.pr_number is not None and session.pr_number != pr_number:
            session.status = "NEEDS_HUMAN_REVIEW"
            session.reason_code = "BINDING_MISMATCH"
            session.updated_at_utc = now
            return session

        if session.branch_name is not None and session.branch_name != branch_name:
            session.status = "NEEDS_HUMAN_REVIEW"
            session.reason_code = "BINDING_MISMATCH"
            session.updated_at_utc = now
            return session

        session.branch_name = branch_name
        session.pr_number = pr_number
        session.updated_at_utc = now
        self._pr_to_session[pr_number] = session_id
        self._branch_to_session[branch_name] = session_id
        return session

    def transition_session_status(
        self, session_id: str, to_status: str, reason_code: Optional[str] = None
    ) -> JulesSessionResponse:
        now = self._now()
        if session_id not in self._sessions:
            return JulesSessionResponse(
                session_id=session_id,
                task_id="",
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="SESSION_NOT_FOUND",
                created_at_utc=now,
                updated_at_utc=now,
            )

        session = self._sessions[session_id]

        if reason_code and not validate_reason_code(reason_code):
            session.status = "NEEDS_HUMAN_REVIEW"
            session.reason_code = "INVALID_REASON_CODE"
            session.updated_at_utc = now
            return session

        # 유효한 상태 전이 확인
        valid_statuses = {"CREATED", "RUNNING", "COMPLETED", "FAILED", "CANCELLED", "NEEDS_HUMAN_REVIEW"}
        if to_status not in valid_statuses:
            session.status = "NEEDS_HUMAN_REVIEW"
            session.reason_code = "INVALID_STATE_TRANSITION"
            session.updated_at_utc = now
            return session

        # 이미 최종 상태인 경우 변경 금지
        if session.status in {"COMPLETED", "FAILED", "CANCELLED"}:
            session.status = "NEEDS_HUMAN_REVIEW"
            session.reason_code = "INVALID_STATE_TRANSITION"
            session.updated_at_utc = now
            return session

        session.status = to_status
        if reason_code:
            session.reason_code = reason_code
        session.updated_at_utc = now
        return session

    def cancel_session(
        self, session_id: str, reason_code: str = "SESSION_CANCELLED"
    ) -> JulesSessionResponse:
        return self.transition_session_status(
            session_id=session_id,
            to_status="CANCELLED",
            reason_code=reason_code,
        )


# --- Jules REST API v1alpha 전송 계층 및 실제 어댑터 구현 ---


class JulesHttpTransport(ABC):
    """Jules HTTP 전송 계층 추상 인터페이스."""

    @abstractmethod
    def request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """HTTP 요청을 수행하고 JSON 구조화 응답 딕셔너리를 반환합니다.

        오류 발생 시 구조화 사유 코드를 포함한 TransportError 예외를 발생시킵니다.
        """
        pass


class TransportError(Exception):
    """HTTP 전송 계층 연동 예외."""

    def __init__(self, reason_code: str, message: str = ""):
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.message = message

    def __str__(self) -> str:
        # 안전한 예외 메시지 (비밀값/원시 내용 노출 배제)
        return f"TransportError(reason_code={self.reason_code})"


class UrllibJulesHttpTransport(JulesHttpTransport):
    """urllib.request 기반의 주입 가능한 HTTP 전송 계층.

    Python 표준 라이브러리만 사용합니다.
    """

    def __init__(self, base_url: str = "https://jules.googleapis.com/v1alpha") -> None:
        self.base_url = base_url.rstrip("/")

    def request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        data = None
        req_headers = dict(headers)

        if body is not None:
            data = json.dumps(body).encode("utf-8")
            req_headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=req_headers, method=method.upper())

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                resp_bytes = response.read()
                if not resp_bytes:
                    return {}
                try:
                    res_json = json.loads(resp_bytes.decode("utf-8"))
                    if not isinstance(res_json, dict):
                        raise TransportError("INVALID_RESPONSE_FORMAT")
                    return res_json
                except (json.JSONDecodeError, UnicodeDecodeError):
                    raise TransportError("INVALID_RESPONSE_FORMAT")
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise TransportError("AUTHENTICATION_FAILED")
            elif e.code in (400, 422, 404, 500, 502, 503, 504):
                # HTTP 상태 코드 에러
                raise TransportError("HTTP_CONNECTION_FAILED")
            else:
                raise TransportError("HTTP_CONNECTION_FAILED")
        except urllib.error.URLError as e:
            if isinstance(e.reason, TimeoutError) or "timed out" in str(e.reason).lower():
                raise TransportError("TIMEOUT_EXCEEDED")
            raise TransportError("HTTP_CONNECTION_FAILED")
        except TimeoutError:
            raise TransportError("TIMEOUT_EXCEEDED")
        except TransportError:
            raise
        except Exception:
            raise TransportError("HTTP_CONNECTION_FAILED")


class RealJulesAdapter(JulesAdapter):
    """Jules REST API v1alpha용 실제 전송 어댑터.

    - API 키는 명시적 생성자 주입만 사용합니다 (환경 변수 직접 읽기 금지).
    - API 키, 프롬프트 원문, 원시 로그, 원시 활동 본문, 비밀값은 to_dict, __repr__, 예외 메시지, 결과에 노출되지 않도록 엄격 통제됩니다.
    - requirePlanApproval: true 및 automationMode: AUTO_CREATE_PR 적용 (approvePlan 미구현).
    - 모든 실패는 자동 재시도 없이 NEEDS_HUMAN_REVIEW 및 구조화 사유 코드로 처리합니다.
    """

    RESOURCE_NAME_REGEX = re.compile(r"^sessions/[a-zA-Z0-9_\-]+$")

    def __init__(
        self,
        api_key: str,
        transport: Optional[JulesHttpTransport] = None,
        clock_fn: Optional[Callable[[], str]] = None,
        remote_main_sha_fn: Optional[Callable[[], Optional[str]]] = None,
        base_url: str = "https://jules.googleapis.com/v1alpha",
    ) -> None:
        if not api_key or not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("유효한 API 키가 명시적으로 주입되어야 합니다.")
        self._api_key = api_key.strip()
        self._transport = transport or UrllibJulesHttpTransport(base_url=base_url)
        self._clock_fn = clock_fn or current_utc_iso8601
        self._remote_main_sha_fn = remote_main_sha_fn or default_remote_main_sha_fn
        self._sessions: Dict[str, JulesSessionResponse] = {}
        # 1:1:1 바인딩 인덱스 (로컬)
        self._branch_to_session: Dict[str, str] = {}
        self._pr_to_session: Dict[int, str] = {}
        self._task_to_session: Dict[str, str] = {}

    def _now(self) -> str:
        return self._clock_fn()

    def _get_headers(self) -> Dict[str, str]:
        return {
            "X-Goog-Api-Key": self._api_key,
            "Accept": "application/json",
        }

    def __repr__(self) -> str:
        return "RealJulesAdapter(api_key='***', transport=...)"

    @classmethod
    def validate_session_resource_name(cls, session_resource_name: str) -> bool:
        """세션 리소스 이름이 'sessions/<id>' 형식인지 검증합니다."""
        if not session_resource_name or not isinstance(session_resource_name, str):
            return False
        return bool(cls.RESOURCE_NAME_REGEX.match(session_resource_name))

    def list_sources(self) -> Dict[str, List[str]]:
        """GET /sources 연동 (Jules 연결 소스 목록 조회).

        원시 데이터 전체가 아닌 세션 생성에 필요한 'sources/<id>' 또는 'sources/<segment1>/<segment2>' 리소스 이름 목록만 추출하여 반환합니다.
        """
        try:
            res = self._transport.request(
                method="GET",
                path="sources",
                headers=self._get_headers(),
            )
            if not isinstance(res, dict):
                raise TransportError("INVALID_RESPONSE_FORMAT")

            raw_sources = res.get("sources", [])
            valid_source_names: List[str] = []

            if isinstance(raw_sources, list):
                for item in raw_sources:
                    name = None
                    if isinstance(item, dict):
                        name = item.get("name")
                    elif isinstance(item, str):
                        name = item

                    if name and validate_source_name(name):
                        valid_source_names.append(name)

            return {"sources": valid_source_names}
        except TransportError:
            raise

    def create_session(
        self, request: JulesSessionRequest, pre_gate_result: PreGateResult
    ) -> JulesSessionResponse:
        now = self._now()

        # 0. Canonical Scope Hash 사전 검증
        try:
            _, computed_scope_hash = canonicalize_scope(request.allowed_paths, request.forbidden_paths)
            if computed_scope_hash != request.approved_scope_hash:
                return JulesSessionResponse(
                    session_id="",
                    task_id=request.task_id,
                    branch_name=None,
                    pr_number=None,
                    status="NEEDS_HUMAN_REVIEW",
                    reason_code="SCOPE_HASH_MISMATCH",
                    created_at_utc=now,
                    updated_at_utc=now,
                )
        except Exception:
            return JulesSessionResponse(
                session_id="",
                task_id=request.task_id,
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="SCOPE_LOCK_CANONICALIZATION_FAILED",
                created_at_utc=now,
                updated_at_utc=now,
            )

        # 1. 사전 게이트 검증
        if (
            not pre_gate_result.is_valid
            or not pre_gate_result.is_session_creation_authorized
            or pre_gate_result.status != "APPROVED"
        ):
            return JulesSessionResponse(
                session_id="",
                task_id=request.task_id,
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="PREGATE_VALIDATION_FAILED",
                created_at_utc=now,
                updated_at_utc=now,
            )

        # 2. 실행 바인딩 및 Contract 기준 SHA 일치 검증
        if (
            request.task_id != pre_gate_result.task_id
            or request.contract_hash != pre_gate_result.contract_hash
            or request.approved_scope_hash != pre_gate_result.approved_scope_hash
            or request.idempotency_key != pre_gate_result.idempotency_key
            or request.base_sha != pre_gate_result.base_sha
        ):
            return JulesSessionResponse(
                session_id="",
                task_id=request.task_id,
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="BINDING_MISMATCH",
                created_at_utc=now,
                updated_at_utc=now,
            )

        # 3. 원격 origin/main 대조 및 SHA 확인
        actual_sha = self._remote_main_sha_fn()
        if not actual_sha or actual_sha != request.base_sha:
            return JulesSessionResponse(
                session_id="",
                task_id=request.task_id,
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="BASE_SHA_MISMATCH",
                created_at_utc=now,
                updated_at_utc=now,
            )

        # 3. source_name 명시적 검증 (sources/default 등 하드코딩 및 추정 기본값 사용 금지)
        if not validate_source_name(getattr(request, "source_name", None)):
            return JulesSessionResponse(
                session_id="",
                task_id=request.task_id,
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="INVALID_SOURCE_NAME",
                created_at_utc=now,
                updated_at_utc=now,
            )

        # 4. 1:1:1 로컬 바인딩 중복/상충 검증
        if request.task_id in self._task_to_session:
            return JulesSessionResponse(
                session_id=self._task_to_session[request.task_id],
                task_id=request.task_id,
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="DUPLICATE_BINDING_CONFLICT",
                created_at_utc=now,
                updated_at_utc=now,
            )

        # 5. HTTP 요청 형성 및 전송
        body = {
            "prompt": request.prompt or "",
            "sourceContext": {
                "source": request.source_name,
                "githubRepoContext": {
                    "startingBranch": "main",
                },
            },
            "automationMode": "AUTO_CREATE_PR",
            "requirePlanApproval": True,
        }

        try:
            resp_data = self._transport.request(
                method="POST",
                path="sessions",
                headers=self._get_headers(),
                body=body,
            )
        except TransportError as err:
            return JulesSessionResponse(
                session_id="",
                task_id=request.task_id,
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code=err.reason_code,
                created_at_utc=now,
                updated_at_utc=now,
            )

        # 6. 구조화 응답 검증 및 추출
        if not isinstance(resp_data, dict):
            return JulesSessionResponse(
                session_id="",
                task_id=request.task_id,
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="INVALID_RESPONSE_FORMAT",
                created_at_utc=now,
                updated_at_utc=now,
            )

        raw_name = resp_data.get("name") or resp_data.get("sessionId") or resp_data.get("id")
        if not raw_name or not isinstance(raw_name, str):
            return JulesSessionResponse(
                session_id="",
                task_id=request.task_id,
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="INVALID_RESPONSE_FORMAT",
                created_at_utc=now,
                updated_at_utc=now,
            )

        session_resource_name = raw_name if raw_name.startswith("sessions/") else f"sessions/{raw_name}"

        if not self.validate_session_resource_name(session_resource_name):
            return JulesSessionResponse(
                session_id="",
                task_id=request.task_id,
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="INVALID_RESPONSE_FORMAT",
                created_at_utc=now,
                updated_at_utc=now,
            )

        response = JulesSessionResponse(
            session_id=session_resource_name,
            task_id=request.task_id,
            branch_name=None,
            pr_number=None,
            status="CREATED",
            reason_code=None,
            created_at_utc=now,
            updated_at_utc=now,
        )

        self._sessions[session_resource_name] = response
        self._task_to_session[request.task_id] = session_resource_name

        return response

    def fetch_activities_content_only(self, session_resource_name: str) -> Optional[str]:
        """GET /sessions/{session_resource_name}/activities 연동 (허용된 활동의 원문 전용 조회).

        이 메서드는 jules_content_review_reader 전용 좁은 경계로서,
        명시적으로 허용된 이벤트 유형(agentMessaged, planGenerated, progressUpdated, sessionCompleted, sessionFailed)의
        단일 확인 필드만 추출하여 반환합니다.
        userMessaged, 자격 증명, Source Resource Name 등의 메타데이터는 철저히 배제됩니다.
        시간 순서 신뢰 불가, 미확인 유형/필드 구조, 파싱 실패 등의 불확실한 상황에서는
        안전하게 None을 반환하여 상위에서 NEEDS_HUMAN_REVIEW 처리되도록 합니다.
        """
        if not self.validate_session_resource_name(session_resource_name):
            return None

        try:
            res = self._transport.request(
                method="GET",
                path=f"{session_resource_name}/activities",
                headers=self._get_headers(),
            )
            if not isinstance(res, dict):
                return None

            raw_activities = res.get("activities", [])
            if not isinstance(raw_activities, list):
                return None

            # 시간 정렬 검증 (get_activities와 동일한 기준 적용)
            parsed_activities = []
            for act in raw_activities:
                if not isinstance(act, dict):
                    return None

                create_time_str = act.get("createTime")
                if not create_time_str or not isinstance(create_time_str, str):
                    return None

                try:
                    dt = datetime.fromisoformat(create_time_str.replace('Z', '+00:00'))
                    parsed_activities.append((dt, act))
                except (ValueError, TypeError):
                    return None

            times = [dt for dt, _ in parsed_activities]
            if len(times) != len(set(times)):
                return None

            parsed_activities.sort(key=lambda x: x[0])

            content_lines = []
            for dt, act in parsed_activities:
                # 명시적 Allowlist 검사 및 추출
                if "agentMessaged" in act:
                    val = act["agentMessaged"]
                    if not isinstance(val, dict) or "message" not in val or not isinstance(val["message"], str):
                        return None
                    content_lines.append(f"[AGENT_MESSAGED]\n{val['message']}")
                elif "planGenerated" in act:
                    val = act["planGenerated"]
                    if not isinstance(val, dict) or "plan" not in val:
                        return None
                    plan_data = val["plan"]
                    if isinstance(plan_data, dict) and "steps" in plan_data:
                        steps = plan_data["steps"]
                        if isinstance(steps, list) and len(steps) > 0:
                            valid_steps = []
                            is_valid = True
                            for step in steps:
                                if not isinstance(step, dict):
                                    is_valid = False
                                    break
                                title = step.get("title")
                                desc = step.get("description")
                                if not isinstance(title, str) or not isinstance(desc, str):
                                    is_valid = False
                                    break
                                valid_steps.append(f"{title}\n{desc}")
                            if is_valid:
                                content_lines.append(f"[PLAN_GENERATED]\n" + "\n\n".join(valid_steps))
                            else:
                                return None
                        else:
                            return None
                    else:
                        return None
                elif "progressUpdated" in act:
                    val = act["progressUpdated"]
                    if not isinstance(val, dict) or "message" not in val or not isinstance(val["message"], str):
                        return None
                    content_lines.append(f"[PROGRESS_UPDATED]\n{val['message']}")
                elif "sessionCompleted" in act:
                    val = act["sessionCompleted"]
                    if not isinstance(val, dict) or "summary" not in val or not isinstance(val["summary"], str):
                        return None
                    content_lines.append(f"[SESSION_COMPLETED]\n{val['summary']}")
                elif "sessionFailed" in act:
                    val = act["sessionFailed"]
                    if not isinstance(val, dict) or "failureReason" not in val or not isinstance(val["failureReason"], str):
                        return None
                    content_lines.append(f"[SESSION_FAILED]\n{val['failureReason']}")
                elif "userMessaged" in act:
                    # userMessaged는 의도적으로 내용 배제 (무시)
                    pass
                elif "planApproved" in act:
                    # 구조가 없으므로 무시
                    pass
                else:
                    # 미확인 유형 발생 시 실패(None 반환)
                    return None

            if not content_lines:
                return None

            return "\n\n---\n\n".join(content_lines)

        except Exception:
            return None

    def fetch_plan_text_only(self, session_resource_name: str) -> Optional[str]:
        """GET /sessions/{session_resource_name}/activities 연동 (Plan 원문 전용 조회).

        이 메서드는 plan_review_reader 전용 좁은 경계로서, 최신 planGenerated 이벤트의
        'plan' 객체의 'steps' 배열 내의 제목과 설명만을 반환합니다.
        일반적인 ActivitySummary나 구조화 결과에는 포함되지 않으며, 비영속/비로그 호출을 전제로 설계되었습니다.
        'steps' 배열 형식이 아니거나, 제목/설명이 문자열이 아닌 등 불확실한 경우(파싱 실패, 시간 순서 신뢰 불가 등)
        None을 반환하여 상위에서 NEEDS_HUMAN_REVIEW 처리하도록 합니다.
        """
        if not self.validate_session_resource_name(session_resource_name):
            return None

        try:
            res = self._transport.request(
                method="GET",
                path=f"{session_resource_name}/activities",
                headers=self._get_headers(),
            )
            if not isinstance(res, dict):
                return None

            raw_activities = res.get("activities", [])
            if not isinstance(raw_activities, list):
                return None

            # 시간 정렬 검증 (get_activities와 동일한 기준 적용)
            parsed_activities = []
            for act in raw_activities:
                if not isinstance(act, dict):
                    return None

                create_time_str = act.get("createTime")
                if not create_time_str or not isinstance(create_time_str, str):
                    return None

                try:
                    dt = datetime.fromisoformat(create_time_str.replace('Z', '+00:00'))
                    parsed_activities.append((dt, act))
                except (ValueError, TypeError):
                    return None

            times = [dt for dt, _ in parsed_activities]
            if len(times) != len(set(times)):
                return None

            parsed_activities.sort(key=lambda x: x[0])

            # 최신 planGenerated 이벤트 찾기 (뒤에서부터 탐색)
            latest_plan_text = None
            for _, act in reversed(parsed_activities):
                if "planGenerated" in act:
                    plan_gen_data = act["planGenerated"]
                    if not isinstance(plan_gen_data, dict):
                        return None
                    # 정확한 단일 키 'plan' 확인. (다른 키 추정 금지)
                    if "plan" in plan_gen_data:
                        plan_data = plan_gen_data["plan"]
                        if isinstance(plan_data, dict) and "steps" in plan_data:
                            steps = plan_data["steps"]
                            if isinstance(steps, list) and len(steps) > 0:
                                valid_steps = []
                                is_valid = True
                                for step in steps:
                                    if not isinstance(step, dict):
                                        is_valid = False
                                        break
                                    title = step.get("title")
                                    desc = step.get("description")
                                    if not isinstance(title, str) or not isinstance(desc, str):
                                        is_valid = False
                                        break
                                    valid_steps.append(f"{title}\n{desc}")

                                if is_valid:
                                    latest_plan_text = "\n\n".join(valid_steps)
                    break

            return latest_plan_text

        except Exception:
            return None

    def get_activities(self, session_resource_name: str) -> ActivitySummary:
        """GET /sessions/{session_resource_name}/activities 연동.

        공식 Activity union 필드(agentMessaged, userMessaged, planGenerated, planApproved,
        progressUpdated, sessionCompleted, sessionFailed) 존재 여부만 검사하여
        고정된 비민감 열거형 코드 목록과 완료/실패 여부를 요약 반환합니다.
        """
        if not self.validate_session_resource_name(session_resource_name):
            raise TransportError("INVALID_RESPONSE_FORMAT")

        try:
            res = self._transport.request(
                method="GET",
                path=f"{session_resource_name}/activities",
                headers=self._get_headers(),
            )
            if not isinstance(res, dict):
                raise TransportError("INVALID_RESPONSE_FORMAT")

            raw_activities = res.get("activities", [])
            if not isinstance(raw_activities, list):
                raw_activities = []

            total_count = len(raw_activities)

            # 시간 정렬 검증을 위한 임시 목록
            parsed_activities = []
            is_temporal_order_reliable = True

            for act in raw_activities:
                if not isinstance(act, dict):
                    parsed_activities.append((None, act))
                    is_temporal_order_reliable = False
                    continue

                create_time_str = act.get("createTime")
                if not create_time_str or not isinstance(create_time_str, str):
                    parsed_activities.append((None, act))
                    is_temporal_order_reliable = False
                    continue

                try:
                    # ISO 8601 파싱 (기본적인 파싱 지원: 파이썬 3.7+ fromisoformat은 'Z' 처리 불가하므로 replace 필요)
                    dt = datetime.fromisoformat(create_time_str.replace('Z', '+00:00'))
                    parsed_activities.append((dt, act))
                except (ValueError, TypeError):
                    parsed_activities.append((None, act))
                    is_temporal_order_reliable = False

            # 중복 시각 검사
            if is_temporal_order_reliable:
                times = [dt for dt, _ in parsed_activities]
                if len(times) != len(set(times)):
                    is_temporal_order_reliable = False

            # 시간 기반 정렬 (순서가 신뢰 가능할 때만 정렬 적용, 아닐 경우 원본 순서 유지)
            if is_temporal_order_reliable:
                parsed_activities.sort(key=lambda x: x[0])

            activity_types: List[str] = []
            is_completed = False
            is_failed = False

            for _, act in parsed_activities:
                if not isinstance(act, dict):
                    activity_types.append("UNKNOWN_ACTIVITY")
                    continue

                matched = False
                if "agentMessaged" in act:
                    activity_types.append("AGENT_MESSAGED")
                    matched = True
                elif "userMessaged" in act:
                    activity_types.append("USER_MESSAGED")
                    matched = True
                elif "planGenerated" in act:
                    activity_types.append("PLAN_GENERATED")
                    matched = True
                elif "planApproved" in act:
                    activity_types.append("PLAN_APPROVED")
                    matched = True
                elif "progressUpdated" in act:
                    activity_types.append("PROGRESS_UPDATED")
                    matched = True
                elif "sessionCompleted" in act:
                    activity_types.append("SESSION_COMPLETED")
                    is_completed = True
                    matched = True
                elif "sessionFailed" in act:
                    activity_types.append("SESSION_FAILED")
                    is_failed = True
                    matched = True

                if not matched:
                    activity_types.append("UNKNOWN_ACTIVITY")

            return ActivitySummary(
                total_count=total_count,
                activity_types=activity_types,
                is_completed=is_completed,
                is_failed=is_failed,
                is_temporal_order_reliable=is_temporal_order_reliable,
            )
        except TransportError:
            raise

    def send_message(self, session_resource_name: str, message_text: str) -> Dict[str, Any]:
        """POST /sessions/{session_resource_name}:sendMessage 연동 (승인된 Codex 응답 전달 전송 인터페이스).

        요청 본문은 {"prompt": message_text} 구조만 사용하며 빈 응답 {}도 정상 처리합니다.
        """
        if not self.validate_session_resource_name(session_resource_name):
            raise TransportError("INVALID_RESPONSE_FORMAT")

        body = {
            "prompt": message_text or "",
        }

        try:
            res = self._transport.request(
                method="POST",
                path=f"{session_resource_name}:sendMessage",
                headers=self._get_headers(),
                body=body,
            )
            if not isinstance(res, dict):
                raise TransportError("INVALID_RESPONSE_FORMAT")
            return res
        except TransportError:
            raise

    def get_session_status(self, session_id: str) -> JulesSessionResponse:
        now = self._now()
        if session_id in self._sessions:
            return self._sessions[session_id]

        if not self.validate_session_resource_name(session_id):
            return JulesSessionResponse(
                session_id=session_id,
                task_id="",
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="SESSION_NOT_FOUND",
                created_at_utc=now,
                updated_at_utc=now,
            )

        return JulesSessionResponse(
            session_id=session_id,
            task_id="",
            branch_name=None,
            pr_number=None,
            status="NEEDS_HUMAN_REVIEW",
            reason_code="SESSION_NOT_FOUND",
            created_at_utc=now,
            updated_at_utc=now,
        )

    def bind_session_outputs(self, session_id: str, branch_name: str, pr_number: int) -> JulesSessionResponse:
        now = self._now()
        if session_id not in self._sessions:
            return JulesSessionResponse(
                session_id=session_id,
                task_id="",
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="SESSION_NOT_FOUND",
                created_at_utc=now,
                updated_at_utc=now,
            )

        session = self._sessions[session_id]

        # PR 1:1 바인딩 검증
        if pr_number in self._pr_to_session and self._pr_to_session[pr_number] != session_id:
            session.status = "NEEDS_HUMAN_REVIEW"
            session.reason_code = "DUPLICATE_BINDING_CONFLICT"
            session.updated_at_utc = now
            return session

        # Branch 1:1 바인딩 검증
        if branch_name in self._branch_to_session and self._branch_to_session[branch_name] != session_id:
            session.status = "NEEDS_HUMAN_REVIEW"
            session.reason_code = "DUPLICATE_BINDING_CONFLICT"
            session.updated_at_utc = now
            return session

        if session.pr_number is not None and session.pr_number != pr_number:
            session.status = "NEEDS_HUMAN_REVIEW"
            session.reason_code = "BINDING_MISMATCH"
            session.updated_at_utc = now
            return session

        if session.branch_name is not None and session.branch_name != branch_name:
            session.status = "NEEDS_HUMAN_REVIEW"
            session.reason_code = "BINDING_MISMATCH"
            session.updated_at_utc = now
            return session

        session.branch_name = branch_name
        session.pr_number = pr_number
        session.updated_at_utc = now
        self._pr_to_session[pr_number] = session_id
        self._branch_to_session[branch_name] = session_id
        return session

    def transition_session_status(
        self, session_id: str, to_status: str, reason_code: Optional[str] = None
    ) -> JulesSessionResponse:
        now = self._now()
        if session_id not in self._sessions:
            return JulesSessionResponse(
                session_id=session_id,
                task_id="",
                branch_name=None,
                pr_number=None,
                status="NEEDS_HUMAN_REVIEW",
                reason_code="SESSION_NOT_FOUND",
                created_at_utc=now,
                updated_at_utc=now,
            )

        session = self._sessions[session_id]

        if reason_code and not validate_reason_code(reason_code):
            session.status = "NEEDS_HUMAN_REVIEW"
            session.reason_code = "INVALID_REASON_CODE"
            session.updated_at_utc = now
            return session

        valid_statuses = {"CREATED", "RUNNING", "COMPLETED", "FAILED", "CANCELLED", "NEEDS_HUMAN_REVIEW"}
        if to_status not in valid_statuses:
            session.status = "NEEDS_HUMAN_REVIEW"
            session.reason_code = "INVALID_STATE_TRANSITION"
            session.updated_at_utc = now
            return session

        if session.status in {"COMPLETED", "FAILED", "CANCELLED"}:
            session.status = "NEEDS_HUMAN_REVIEW"
            session.reason_code = "INVALID_STATE_TRANSITION"
            session.updated_at_utc = now
            return session

        session.status = to_status
        if reason_code:
            session.reason_code = reason_code
        session.updated_at_utc = now
        return session

    def cancel_session(
        self, session_id: str, reason_code: str = "SESSION_CANCELLED"
    ) -> JulesSessionResponse:
        """원격 취소를 추정 호출하지 않으며 REMOTE_CANCEL_UNSUPPORTED 사유 코드로 NEEDS_HUMAN_REVIEW 반환."""
        now = self._now()
        if session_id in self._sessions:
            session = self._sessions[session_id]
            session.status = "NEEDS_HUMAN_REVIEW"
            session.reason_code = "REMOTE_CANCEL_UNSUPPORTED"
            session.updated_at_utc = now
            return session

        return JulesSessionResponse(
            session_id=session_id,
            task_id="",
            branch_name=None,
            pr_number=None,
            status="NEEDS_HUMAN_REVIEW",
            reason_code="REMOTE_CANCEL_UNSUPPORTED",
            created_at_utc=now,
            updated_at_utc=now,
        )
