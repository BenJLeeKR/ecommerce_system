"""contract-c14n-v1 및 scope-c14n-v1 정규화 및 SHA-256 해시 유틸리티."""

import hashlib
import json
from typing import List, Dict, Any, Tuple
from .models import PathItem, TaskContract


class ScopeCanonicalizationError(Exception):
    """Scope 정규화 실패 시 발생하는 예외 클래스 (예: 유효하지 않은 경로 포맷)."""
    pass


def validate_and_normalize_path_item(item: PathItem) -> Dict[str, str]:
    """scope-c14n-v1 경로 항목 단건을 검증하고 정규화합니다.

    거부 대상:
    - 절대 경로 ('/'로 시작)
    - 빈 경로
    - '.' 또는 '..' 경로 세그먼트 포함
    - 윈도우 역슬래시 (POSIX 경로 규칙 준수)
    """
    raw_path = item.path.strip()
    kind = item.kind.strip()

    if not raw_path:
        raise ScopeCanonicalizationError("경로는 비어 있을 수 없습니다.")

    if raw_path.startswith("/") or raw_path.startswith("\\"):
        raise ScopeCanonicalizationError(f"절대 경로는 거부됩니다: '{raw_path}'")

    if "\\" in raw_path:
        raise ScopeCanonicalizationError(f"윈도우 경로 역슬래시는 거부됩니다: '{raw_path}'")

    # 세그먼트 분할 및 '.' / '..' 검사
    segments = [seg for seg in raw_path.split("/") if seg]
    for seg in raw_path.split("/"):
        if seg == "." or seg == "..":
            raise ScopeCanonicalizationError(f"'.' 또는 '..' 세그먼트를 포함한 경로는 거부됩니다: '{raw_path}'")

    if not segments:
        raise ScopeCanonicalizationError(f"유효하지 않은 경로 구조입니다: '{raw_path}'")

    normalized_path = "/".join(segments)

    if kind not in ("file", "directory_recursive"):
        raise ScopeCanonicalizationError(f"유효하지 않은 경로 종류입니다: '{kind}'. 'file' 또는 'directory_recursive'여야 합니다.")

    return {
        "path": normalized_path,
        "kind": kind
    }


def normalize_path_list(path_items: List[PathItem]) -> List[Dict[str, str]]:
    """PathItem 목록을 정규화, 중복 제거 및 정렬합니다."""
    normalized_dict_map = {}
    for item in path_items:
        norm = validate_and_normalize_path_item(item)
        key = (norm["path"], norm["kind"])
        normalized_dict_map[key] = norm

    # 경로 문자열 유니코드 코드 포인트 오름차순 정렬 후 kind 정렬
    sorted_keys = sorted(normalized_dict_map.keys(), key=lambda x: (x[0], x[1]))
    return [normalized_dict_map[k] for k in sorted_keys]


def canonicalize_scope(allowed_paths: List[PathItem], forbidden_paths: List[PathItem]) -> Tuple[str, str]:
    """scope-c14n-v1 정규 JSON 문자열과 SHA-256 해시를 산출합니다."""
    norm_allowed = normalize_path_list(allowed_paths)
    norm_forbidden = normalize_path_list(forbidden_paths)

    scope_dict = {
        "version": "scope-c14n-v1",
        "allowed": norm_allowed,
        "forbidden": norm_forbidden
    }

    # 공백 없이 UTF-8 JSON 직렬화
    json_str = json.dumps(scope_dict, ensure_ascii=False, separators=(',', ':'))
    sha256_hash = hashlib.sha256(json_str.encode('utf-8')).hexdigest().lower()

    return json_str, sha256_hash


def _normalize_string_list(items: List[str]) -> List[str]:
    """문자열 목록의 공백 제거, 중복 제거 및 유니코드 오름차순 정렬을 수행합니다."""
    cleaned = [item.strip() for item in items if item.strip()]
    unique = sorted(list(set(cleaned)))
    return unique


def canonicalize_contract(contract: TaskContract) -> Tuple[str, str]:
    """20개 최상위 고정 키 순서를 준수하여 contract-c14n-v1 JSON 문자열과 SHA-256 해시를 산출합니다."""
    norm_allowed = normalize_path_list(contract.allowed_paths)
    norm_forbidden = normalize_path_list(contract.forbidden_paths)

    # 20개 최상위 고정 키 순서
    contract_dict = {
        "version": "contract-c14n-v1",
        "contract_version": contract.contract_version.strip(),
        "task_id": contract.task_id.strip(),
        "project_profile_id": contract.project_profile_id.strip(),
        "project_profile_version": contract.project_profile_version.strip(),
        "project_profile_reference_path": contract.project_profile_reference_path.strip(),
        "goal": contract.goal.strip(),
        "target_repository": contract.target_repository.strip(),
        "base_branch": contract.base_branch.strip(),
        "base_commit_sha": contract.base_commit_sha.strip(),
        "execution_agent": contract.execution_agent.strip(),
        "reference_documents": _normalize_string_list(contract.reference_documents),
        "allowed_paths": norm_allowed,
        "forbidden_paths": norm_forbidden,
        "risk_level": contract.risk_level.strip(),
        "completion_conditions": _normalize_string_list(contract.completion_conditions),
        "idempotency_key": contract.idempotency_key.strip(),
        "plan_approval_required": bool(contract.plan_approval_required),
        "cancellation_conditions": _normalize_string_list(contract.cancellation_conditions),
        "auto_merge": bool(contract.auto_merge)
    }

    json_str = json.dumps(contract_dict, ensure_ascii=False, separators=(',', ':'))
    sha256_hash = hashlib.sha256(json_str.encode('utf-8')).hexdigest().lower()

    return json_str, sha256_hash
