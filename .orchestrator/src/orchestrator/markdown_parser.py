"""Task Contract v0.1을 위한 Markdown 파서."""

import re
from typing import Dict, Any, List, Optional
from .models import TaskContract, PathItem


class MarkdownParseError(Exception):
    """Markdown 파싱 실패 시 발생하는 예외 클래스."""
    pass


def parse_task_contract_markdown(content: str) -> TaskContract:
    """Task Contract v0.1 Markdown 본문을 읽어 TaskContract 객체로 파싱합니다."""

    # 1. 헤더에서 Contract 버전 추출 (예: # Task Contract v0.1 또는 # Task Contract v0.1 — ORCH-...)
    contract_version = ""
    header_match = re.search(r"^#\s+Task\s+Contract\s+([^\n—\-]+)", content, re.MULTILINE | re.IGNORECASE)
    if header_match:
        version_str = header_match.group(1).strip()
        if version_str:
            contract_version = version_str

    # 2. 키-값 쌍 추출 (- **키**: 값)
    raw_fields: Dict[str, Any] = {}

    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 키-값 불렛 라인 검사: - **키**: 값
        kv_match = re.match(r"^\-\s+\*\*([^*]+)\*\*\s*:\s*(.*)$", line)
        if kv_match:
            key = kv_match.group(1).strip()
            val = kv_match.group(2).strip()

            # 하위 불렛 항목이 이어지는지 검사
            sub_items = []
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                sub_match = re.match(r"^\s{2,}\-\s+(.*)$", next_line)
                if sub_match:
                    sub_items.append(sub_match.group(1).strip())
                    j += 1
                else:
                    break

            if sub_items:
                if val:
                    raw_fields[key] = [val] + sub_items
                else:
                    raw_fields[key] = sub_items
                i = j - 1
            else:
                raw_fields[key] = val

        i += 1

    def _strip_code(val: str) -> str:
        val = val.strip()
        while val.startswith("`") and val.endswith("`") and len(val) >= 2:
            val = val[1:-1].strip()
        return val

    def _get_raw(key_aliases: List[str]) -> Any:
        for k in key_aliases:
            if k in raw_fields:
                return raw_fields[k]
        return None

    def _get_str(key_aliases: List[str]) -> str:
        val = _get_raw(key_aliases)
        if isinstance(val, str):
            return _strip_code(val)
        elif isinstance(val, list) and val:
            return _strip_code(val[0])
        return ""

    def _get_list(key_aliases: List[str]) -> List[str]:
        val = _get_raw(key_aliases)
        if isinstance(val, list):
            return [item.strip() for item in val if item.strip()]
        elif isinstance(val, str) and val:
            if val.strip():
                return [val.strip()]
        return []

    # 필드 매핑
    task_id = _get_str(["Task ID"])
    project_profile_id = _get_str(["적용 Project Profile ID", "Project Profile ID"])
    project_profile_version = _get_str(["적용 Project Profile 버전", "Project Profile 버전"])
    project_profile_ref = _get_str(["적용 Profile 참조 경로", "Profile 참조 경로"])
    goal = _get_str(["작업 목표"])
    execution_agent = _get_str(["실행 에이전트"])
    risk_level = _get_str(["위험도"])

    target_repo = _get_str(["대상 저장소"])
    base_branch = _get_str(["기준 브랜치"])
    base_commit_sha = _get_str(["기준 커밋 SHA"])

    ref_docs = [_strip_code(item) for item in _get_list(["기준 문서"]) if _strip_code(item)]

    raw_allowed = _get_list(["허용 경로"])
    raw_forbidden = _get_list(["금지 경로"])

    on_path_violation = _get_str(["허용 경로 검증 실패 시 처리 기준"])

    auto_merge_str = _get_str(["병합 설정"])
    if "auto_merge:" in auto_merge_str:
        auto_merge_str = auto_merge_str.split("auto_merge:")[-1].strip()
    auto_merge_raw = _strip_code(auto_merge_str)
    auto_merge = auto_merge_raw.lower() == "true"

    plan_approval_str = _get_str(["계획 승인 필요 여부"])
    plan_approval_raw = _strip_code(plan_approval_str)
    plan_approval_required = plan_approval_raw.lower() == "true"

    approval_status = _get_str(["승인 상태"])
    approval_evidence_id = _get_str(["승인 증적 식별자"])

    # 중복 실행 방지 키 추출
    idempotency_raw = _get_raw(["중복 실행 방지 기준"])
    def _extract_idempotency_key(raw_val: Any) -> str:
        if not raw_val:
            return ""
        candidates = [str(x) for x in raw_val] if isinstance(raw_val, list) else [str(raw_val)]
        for cand in candidates:
            m = re.search(r"(idem\-v1:[^\s`\"']+)", cand)
            if m:
                return m.group(1).strip()
        for cand in candidates:
            m = re.search(r"`(idem\-v1[^`]*)`", cand)
            if m:
                return m.group(1).strip()
        for cand in candidates:
            cleaned = _strip_code(cand)
            if cleaned:
                return cleaned
        return ""

    idempotency_key = _extract_idempotency_key(idempotency_raw)
    cancel_conds = [_strip_code(item) for item in _get_list(["취소 조건"]) if _strip_code(item)]
    completion_conds = [_strip_code(item) for item in _get_list(["완료 조건"]) if _strip_code(item)]

    def _parse_path_items(items: List[str]) -> List[PathItem]:
        res = []
        for item in items:
            match = re.search(r"`?path`?:\s*`?([^`,]+)`?\s*,\s*`?kind`?:\s*`?([^`,]+)`?", item, re.IGNORECASE)
            if match:
                p = _strip_code(match.group(1).strip())
                k = _strip_code(match.group(2).strip())
                res.append(PathItem(path=p, kind=k))
            else:
                p = _strip_code(item)
                if p:
                    k = "directory_recursive" if p.endswith("/") else "file"
                    res.append(PathItem(path=p, kind=k))
        return res

    allowed_paths = _parse_path_items(raw_allowed)
    forbidden_paths = _parse_path_items(raw_forbidden)

    raw_fields["on_path_violation"] = on_path_violation
    raw_fields["auto_merge_raw"] = auto_merge_raw
    raw_fields["plan_approval_raw"] = plan_approval_raw
    raw_fields["has_auto_merge_key"] = ("병합 설정" in raw_fields)
    raw_fields["has_plan_approval_key"] = ("계획 승인 필요 여부" in raw_fields)
    raw_fields["approval_status"] = approval_status
    raw_fields["approval_evidence_id"] = approval_evidence_id

    return TaskContract(
        task_id=task_id,
        contract_version=contract_version,
        project_profile_id=project_profile_id,
        project_profile_version=project_profile_version,
        project_profile_reference_path=project_profile_ref,
        goal=goal,
        target_repository=target_repo,
        base_branch=base_branch,
        base_commit_sha=base_commit_sha,
        execution_agent=execution_agent,
        reference_documents=ref_docs,
        allowed_paths=allowed_paths,
        forbidden_paths=forbidden_paths,
        risk_level=risk_level,
        completion_conditions=completion_conds,
        idempotency_key=idempotency_key,
        plan_approval_required=plan_approval_required,
        cancellation_conditions=cancel_conds,
        auto_merge=auto_merge,
        raw_fields=raw_fields
    )
