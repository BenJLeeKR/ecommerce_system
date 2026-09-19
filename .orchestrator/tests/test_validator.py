"""Orchestrator 검증기, 파서, 정규화(c14n), 정책 모듈을 위한 단위 테스트."""

import json
import hashlib
import unittest
from orchestrator.models import ApprovalEvidence, ApprovalHistoryItem, TaskContract, PathItem
from orchestrator.markdown_parser import parse_task_contract_markdown
from orchestrator.canonicalization import canonicalize_scope, canonicalize_contract, ScopeCanonicalizationError
from orchestrator.validator import (
    validate_task_contract,
    validate_approval_id,
    validate_scope_lock_pre_dispatch,
    validate_changed_files_against_scope_lock,
)


SAMPLE_VALID_CONTRACT_FIXTURE = """# Task Contract v0.1 — SAMPLE-TASK-001

## 1. 기본 정보

- **Task ID**: SAMPLE-TASK-001
- **적용 Project Profile ID**: ORCHESTRATOR-PROFILE-001
- **적용 Project Profile 버전**: v0.1
- **적용 Profile 참조 경로**: `docs/03_planning/project-profile-orchestrator-v0.1.md`
- **작업 목표**: Task Contract 파서 및 c14n 구현
- **실행 에이전트**: Jules
- **위험도**: LOW

## 2. 작업 대상 및 환경

- **대상 저장소**: `example/orchestrator_jules`
- **기준 브랜치**: `main`
- **기준 커밋 SHA**: `63bc13fc3c0fcdc427a7958ce1208614b37af9d3`
- **기준 문서**:
  - `AGENTS.md`
  - `CLAUDE.md`

## 3. 작업 범위 및 규칙

- **허용 경로**:
  - `path`: `src/orchestrator`, `kind`: `directory_recursive`
  - `path`: `tests`, `kind`: `directory_recursive`
- **금지 경로**:
  - `path`: `docs`, `kind`: `directory_recursive`
  - `path`: `AGENTS.md`, `kind`: `file`
- **허용 경로 검증 실패 시 처리 기준**: 실패 시 진행 중단 및 `NEEDS_HUMAN_REVIEW` 전환

## 4. 제어 및 상태

- **병합 설정**: `auto_merge: false`
- **계획 승인 필요 여부**: true
- **중복 실행 방지 기준**: 비순환 idempotency `idem-v1` 규칙 적용
  - `idempotency_key = "idem-v1:4cc924b2d3306313bac2ba8481c547eebd9a2af1b38f502fbebf7a5c0148f7ca"`
- **취소 조건**:
  - 커밋 SHA 변경 시

## 5. 완료 및 검증

- **완료 조건**:
  - unittest 통과

## 6. 승인 상태 및 증적

- **승인 상태**: APPROVED
- **승인 증적 식별자**: APV-SAMPLE-TASK-001-20260916-001
- **승인 내역**:
  - **승인자**: User
  - **승인 범위**: `src/orchestrator`
  - **승인 시각**: `2026-09-16T00:00:00Z` / `2026-09-16 09:00:00 KST`
  - **철회/만료 규칙**: 허용 경로 외 파일 수정 시 철회
"""


class TestOrchestratorValidator(unittest.TestCase):

    def test_sample_valid_contract_fixture_parsing(self):
        """표준 경로 포맷 및 중복 실행 방지 하위 불렛이 포함된 검증 픽스처 파싱 테스트."""
        contract = parse_task_contract_markdown(SAMPLE_VALID_CONTRACT_FIXTURE)
        self.assertEqual(contract.task_id, "SAMPLE-TASK-001")
        self.assertEqual(contract.risk_level, "LOW")
        self.assertEqual(contract.base_commit_sha, "63bc13fc3c0fcdc427a7958ce1208614b37af9d3")
        self.assertEqual(contract.idempotency_key, "idem-v1:4cc924b2d3306313bac2ba8481c547eebd9a2af1b38f502fbebf7a5c0148f7ca")

        self.assertEqual(len(contract.allowed_paths), 2)
        self.assertEqual(contract.allowed_paths[0].path, "src/orchestrator")
        self.assertEqual(contract.allowed_paths[0].kind, "directory_recursive")
        self.assertEqual(contract.allowed_paths[1].path, "tests")
        self.assertEqual(contract.allowed_paths[1].kind, "directory_recursive")

        self.assertEqual(len(contract.forbidden_paths), 2)
        self.assertEqual(contract.forbidden_paths[0].path, "docs")
        self.assertEqual(contract.forbidden_paths[0].kind, "directory_recursive")
        self.assertEqual(contract.forbidden_paths[1].path, "AGENTS.md")
        self.assertEqual(contract.forbidden_paths[1].kind, "file")

    def test_contract_c14n_fixed_keys_sequence_and_expected_hash(self):
        """contract-c14n-v1 직렬화 JSON의 20개 최상위 고정 키 순서 및 기대 SHA-256 해시 단언 테스트."""
        contract = parse_task_contract_markdown(SAMPLE_VALID_CONTRACT_FIXTURE)
        json_str, contract_hash = canonicalize_contract(contract)

        # 1. 20개 최상위 키 순서 검증
        parsed_obj = json.loads(json_str)
        expected_keys = [
            "version",
            "contract_version",
            "task_id",
            "project_profile_id",
            "project_profile_version",
            "project_profile_reference_path",
            "goal",
            "target_repository",
            "base_branch",
            "base_commit_sha",
            "execution_agent",
            "reference_documents",
            "allowed_paths",
            "forbidden_paths",
            "risk_level",
            "completion_conditions",
            "idempotency_key",
            "plan_approval_required",
            "cancellation_conditions",
            "auto_merge"
        ]
        self.assertEqual(list(parsed_obj.keys()), expected_keys)

        # 2. 직렬화 문자열에 대한 SHA-256 직접 산출 단언
        expected_hash = hashlib.sha256(json_str.encode('utf-8')).hexdigest().lower()
        self.assertEqual(contract_hash, expected_hash)

        # 3. 기대하는 정확한 JSON 직렬화 결과 단언
        expected_json = (
            '{"version":"contract-c14n-v1",'
            '"contract_version":"v0.1",'
            '"task_id":"SAMPLE-TASK-001",'
            '"project_profile_id":"ORCHESTRATOR-PROFILE-001",'
            '"project_profile_version":"v0.1",'
            '"project_profile_reference_path":"docs/03_planning/project-profile-orchestrator-v0.1.md",'
            '"goal":"Task Contract 파서 및 c14n 구현",'
            '"target_repository":"example/orchestrator_jules",'
            '"base_branch":"main",'
            '"base_commit_sha":"63bc13fc3c0fcdc427a7958ce1208614b37af9d3",'
            '"execution_agent":"Jules",'
            '"reference_documents":["AGENTS.md","CLAUDE.md"],'
            '"allowed_paths":[{"path":"src/orchestrator","kind":"directory_recursive"},{"path":"tests","kind":"directory_recursive"}],'
            '"forbidden_paths":[{"path":"AGENTS.md","kind":"file"},{"path":"docs","kind":"directory_recursive"}],'
            '"risk_level":"LOW",'
            '"completion_conditions":["unittest 통과"],'
            '"idempotency_key":"idem-v1:4cc924b2d3306313bac2ba8481c547eebd9a2af1b38f502fbebf7a5c0148f7ca",'
            '"plan_approval_required":true,'
            '"cancellation_conditions":["커밋 SHA 변경 시"],'
            '"auto_merge":false}'
        )
        self.assertEqual(json_str, expected_json)

    def test_valid_low_contract_and_active_evidence(self):
        """유효한 LOW Contract 및 ACTIVE 승인 증적에 대한 자동 Dispatch 적격 테스트."""
        contract = parse_task_contract_markdown(SAMPLE_VALID_CONTRACT_FIXTURE)
        _, scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
        _, contract_hash = canonicalize_contract(contract)

        evidence = ApprovalEvidence(
            approval_id="APV-SAMPLE-TASK-001-20260916-001",
            task_id="SAMPLE-TASK-001",
            contract_version="v0.1",
            contract_hash=contract_hash,
            approved_scope_hash=scope_hash,
            approver="User",
            approval_time_utc="2026-09-16T00:00:00Z",
            status="ACTIVE"
        )

        res = validate_task_contract(SAMPLE_VALID_CONTRACT_FIXTURE, evidence)
        self.assertTrue(res.is_valid)
        self.assertTrue(res.is_dispatch_eligible)
        self.assertEqual(res.status, "APPROVED")

    def test_auto_merge_true_valid_syntax_but_ineligible(self):
        """auto_merge: true는 문법상 유효(is_valid=True)하나 자동 Dispatch 부적격(is_dispatch_eligible=False) 테스트."""
        md_auto_merge = SAMPLE_VALID_CONTRACT_FIXTURE.replace("`auto_merge: false`", "`auto_merge: true`")
        contract = parse_task_contract_markdown(md_auto_merge)
        _, scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
        _, contract_hash = canonicalize_contract(contract)

        evidence = ApprovalEvidence(
            approval_id="APV-SAMPLE-TASK-001-20260916-001",
            task_id="SAMPLE-TASK-001",
            contract_version="v0.1",
            contract_hash=contract_hash,
            approved_scope_hash=scope_hash,
            approver="User",
            approval_time_utc="2026-09-16T00:00:00Z",
            status="ACTIVE"
        )

        res = validate_task_contract(md_auto_merge, evidence)
        self.assertTrue(res.is_valid)
        self.assertFalse(res.is_dispatch_eligible)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")

    def test_contract_version_v0_2_rejection(self):
        """contract_version != 'v0.1' (예: v0.2) 입력 시 is_valid=False 및 NEEDS_HUMAN_REVIEW 처리 테스트."""
        md_v0_2 = SAMPLE_VALID_CONTRACT_FIXTURE.replace("# Task Contract v0.1", "# Task Contract v0.2")
        res = validate_task_contract(md_v0_2, None)
        self.assertFalse(res.is_valid)
        self.assertFalse(res.is_dispatch_eligible)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertTrue(any("v0.1만 지원됩니다" in r for r in res.reasons))

    def test_approval_evidence_contract_version_mismatch(self):
        """승인 증적 contract_version 불일치 시 is_valid=False 및 NEEDS_HUMAN_REVIEW 처리 테스트."""
        contract = parse_task_contract_markdown(SAMPLE_VALID_CONTRACT_FIXTURE)
        _, scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
        _, contract_hash = canonicalize_contract(contract)

        evidence = ApprovalEvidence(
            approval_id="APV-SAMPLE-TASK-001-20260916-001",
            task_id="SAMPLE-TASK-001",
            contract_version="v0.2",
            contract_hash=contract_hash,
            approved_scope_hash=scope_hash,
            approver="User",
            approval_time_utc="2026-09-16T00:00:00Z",
            status="ACTIVE"
        )

        res = validate_task_contract(SAMPLE_VALID_CONTRACT_FIXTURE, evidence)
        self.assertFalse(res.is_valid)
        self.assertFalse(res.is_dispatch_eligible)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertTrue(any("contract_version 불일치" in r for r in res.reasons))

    def test_non_existent_utc_date_time_rejection(self):
        """존재하지 않는 UTC 날짜/시각 (예: 2026-02-30T25:60:60Z) 입력 거부 테스트."""
        contract = parse_task_contract_markdown(SAMPLE_VALID_CONTRACT_FIXTURE)
        _, scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
        _, contract_hash = canonicalize_contract(contract)

        evidence = ApprovalEvidence(
            approval_id="APV-SAMPLE-TASK-001-20260916-001",
            task_id="SAMPLE-TASK-001",
            contract_version="v0.1",
            contract_hash=contract_hash,
            approved_scope_hash=scope_hash,
            approver="User",
            approval_time_utc="2026-02-30T25:60:60Z",
            status="ACTIVE"
        )

        res = validate_task_contract(SAMPLE_VALID_CONTRACT_FIXTURE, evidence)
        self.assertFalse(res.is_valid)
        self.assertFalse(res.is_dispatch_eligible)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertTrue(any("approval_time_utc" in r for r in res.reasons))

    def test_missing_required_fields(self):
        """필수 필드 누락 시 is_valid=False 및 NEEDS_HUMAN_REVIEW 반환 테스트."""
        incomplete_md = """# Task Contract v0.1 — INCOMPLETE

## 1. 기본 정보

- **Task ID**: INCOMPLETE-001
- **위험도**: LOW
"""
        res = validate_task_contract(incomplete_md, None)
        self.assertFalse(res.is_valid)
        self.assertFalse(res.is_dispatch_eligible)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertTrue(any("필수 필드 누락" in r for r in res.reasons))

    def test_rejection_of_absolute_and_parent_paths(self):
        """절대 경로 및 '..' 경로 세그먼트 거부 테스트."""
        md_abs = SAMPLE_VALID_CONTRACT_FIXTURE.replace(
            "`path`: `src/orchestrator`, `kind`: `directory_recursive`",
            "`path`: `/etc/passwd`, `kind`: `file`"
        )
        res_abs = validate_task_contract(md_abs, None)
        self.assertFalse(res_abs.is_valid)
        self.assertTrue(any("절대 경로는 거부됩니다" in r for r in res_abs.reasons))

        md_parent = SAMPLE_VALID_CONTRACT_FIXTURE.replace(
            "`path`: `src/orchestrator`, `kind`: `directory_recursive`",
            "`path`: `../src`, `kind`: `directory_recursive`"
        )
        res_parent = validate_task_contract(md_parent, None)
        self.assertFalse(res_parent.is_valid)
        self.assertTrue(any("'.' 또는 '..' 세그먼트를 포함한 경로는 거부됩니다" in r for r in res_parent.reasons))

    def test_scope_sorting_and_deduplication_consistency(self):
        """Scope 경로 정렬 및 중복 제거에 따른 해시 일관성 검증 테스트."""
        paths_unordered_dup = [
            PathItem(path="tests", kind="directory_recursive"),
            PathItem(path="src/orchestrator", kind="directory_recursive"),
            PathItem(path="src/orchestrator", kind="directory_recursive")
        ]
        paths_clean = [
            PathItem(path="src/orchestrator", kind="directory_recursive"),
            PathItem(path="tests", kind="directory_recursive")
        ]

        json1, hash1 = canonicalize_scope(paths_unordered_dup, [])
        json2, hash2 = canonicalize_scope(paths_clean, [])

        self.assertEqual(json1, json2)
        self.assertEqual(hash1, hash2)

    def test_approved_scope_hash_mismatch_yields_integrity_failure(self):
        """approved_scope_hash 불일치 시 무결성 실패(is_valid=False 및 NEEDS_HUMAN_REVIEW) 반환 테스트."""
        contract = parse_task_contract_markdown(SAMPLE_VALID_CONTRACT_FIXTURE)
        _, scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
        _, contract_hash = canonicalize_contract(contract)

        evidence = ApprovalEvidence(
            approval_id="APV-SAMPLE-TASK-001-20260916-001",
            task_id="SAMPLE-TASK-001",
            contract_version="v0.1",
            contract_hash=contract_hash,
            approved_scope_hash="0000000000000000000000000000000000000000000000000000000000000000",
            approver="User",
            approval_time_utc="2026-09-16T00:00:00Z",
            status="ACTIVE"
        )

        res = validate_task_contract(SAMPLE_VALID_CONTRACT_FIXTURE, evidence)
        self.assertFalse(res.is_valid)
        self.assertFalse(res.is_dispatch_eligible)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertTrue(any("approved_scope_hash 불일치" in r for r in res.reasons))

    def test_contract_hash_mismatch_yields_integrity_failure(self):
        """contract_hash 불일치 시 무결성 실패(is_valid=False 및 NEEDS_HUMAN_REVIEW) 반환 테스트."""
        contract = parse_task_contract_markdown(SAMPLE_VALID_CONTRACT_FIXTURE)
        _, scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)

        evidence = ApprovalEvidence(
            approval_id="APV-SAMPLE-TASK-001-20260916-001",
            task_id="SAMPLE-TASK-001",
            contract_version="v0.1",
            contract_hash="1111111111111111111111111111111111111111111111111111111111111111",
            approved_scope_hash=scope_hash,
            approver="User",
            approval_time_utc="2026-09-16T00:00:00Z",
            status="ACTIVE"
        )

        res = validate_task_contract(SAMPLE_VALID_CONTRACT_FIXTURE, evidence)
        self.assertFalse(res.is_valid)
        self.assertFalse(res.is_dispatch_eligible)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertTrue(any("contract_hash 불일치" in r for r in res.reasons))

    def test_medium_high_critical_risk_levels_ineligible(self):
        """MEDIUM, HIGH, CRITICAL 위험도에 대해 자동 Dispatch 부적격 판정 테스트."""
        for risk in ["MEDIUM", "HIGH", "CRITICAL"]:
            md_risk = SAMPLE_VALID_CONTRACT_FIXTURE.replace("- **위험도**: LOW", f"- **위험도**: {risk}")
            contract = parse_task_contract_markdown(md_risk)
            _, scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
            _, contract_hash = canonicalize_contract(contract)

            evidence = ApprovalEvidence(
                approval_id="APV-SAMPLE-TASK-001-20260916-001",
                task_id="SAMPLE-TASK-001",
                contract_version="v0.1",
                contract_hash=contract_hash,
                approved_scope_hash=scope_hash,
                approver="User",
                approval_time_utc="2026-09-16T00:00:00Z",
                status="ACTIVE"
            )

            res = validate_task_contract(md_risk, evidence)
            self.assertTrue(res.is_valid)
            self.assertFalse(res.is_dispatch_eligible)
            self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
            self.assertTrue(any("Phase 1 자동 Dispatch 대상이 아닙니다" in r for r in res.reasons))

    def test_approval_evidence_non_active_statuses(self):
        """WITHDRAWN, MODIFIED, EXPIRED 승인 상태에 대해 자동 Dispatch 부적격 판정 테스트."""
        contract = parse_task_contract_markdown(SAMPLE_VALID_CONTRACT_FIXTURE)
        _, scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
        _, contract_hash = canonicalize_contract(contract)

        for status in ["WITHDRAWN", "MODIFIED", "EXPIRED"]:
            evidence = ApprovalEvidence(
                approval_id="APV-SAMPLE-TASK-001-20260916-001",
                task_id="SAMPLE-TASK-001",
                contract_version="v0.1",
                contract_hash=contract_hash,
                approved_scope_hash=scope_hash,
                approver="User",
                approval_time_utc="2026-09-16T00:00:00Z",
                status=status
            )

            res = validate_task_contract(SAMPLE_VALID_CONTRACT_FIXTURE, evidence)
            self.assertTrue(res.is_valid)
            self.assertFalse(res.is_dispatch_eligible)
            self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
            self.assertTrue(any("승인 증적 상태가" in r for r in res.reasons))

    def test_missing_plan_approval_and_cancellation_conditions(self):
        """계획 승인 필요 여부, 취소 조건 필드 누락/형식 오류 시 is_valid=False 검증."""
        # 1. 계획 승인 필요 여부 누락
        md_no_plan = SAMPLE_VALID_CONTRACT_FIXTURE.replace("- **계획 승인 필요 여부**: true\n", "")
        res1 = validate_task_contract(md_no_plan, None)
        self.assertFalse(res1.is_valid)
        self.assertTrue(any("계획 승인 필요 여부" in r for r in res1.reasons))

        # 2. 계획 승인 필요 여부 형식 오류 (true|false 이외의 값)
        md_bad_plan = SAMPLE_VALID_CONTRACT_FIXTURE.replace("- **계획 승인 필요 여부**: true", "- **계획 승인 필요 여부**: invalid_bool")
        res2 = validate_task_contract(md_bad_plan, None)
        self.assertFalse(res2.is_valid)
        self.assertTrue(any("유효하지 않은 plan_approval_required 형식" in r for r in res2.reasons))

        # 3. 취소 조건 누락
        md_no_cancel = SAMPLE_VALID_CONTRACT_FIXTURE.replace("- **취소 조건**:\n  - 커밋 SHA 변경 시\n", "")
        res3 = validate_task_contract(md_no_cancel, None)
        self.assertFalse(res3.is_valid)
        self.assertTrue(any("취소 조건" in r for r in res3.reasons))

    def test_missing_approval_status_and_evidence_id(self):
        """승인 상태 및 승인 증적 식별자 누락 시 is_valid=False 검증."""
        # 1. 승인 상태 누락
        md_no_status = SAMPLE_VALID_CONTRACT_FIXTURE.replace("- **승인 상태**: APPROVED\n", "")
        res1 = validate_task_contract(md_no_status, None)
        self.assertFalse(res1.is_valid)
        self.assertTrue(any("승인 상태" in r for r in res1.reasons))

        # 2. 승인 증적 식별자 누락
        md_no_id = SAMPLE_VALID_CONTRACT_FIXTURE.replace("- **승인 증적 식별자**: APV-SAMPLE-TASK-001-20260916-001\n", "")
        res2 = validate_task_contract(md_no_id, None)
        self.assertFalse(res2.is_valid)
        self.assertTrue(any("승인 증적 식별자" in r for r in res2.reasons))

    def test_missing_or_invalid_contract_header_version(self):
        """Contract 헤더가 없거나 # Task Contract v0.1 형식이 아닐 때 is_valid=False 및 NEEDS_HUMAN_REVIEW 검증."""
        # 1. 헤더 아예 없음
        md_no_header = SAMPLE_VALID_CONTRACT_FIXTURE.replace("# Task Contract v0.1 — SAMPLE-TASK-001", "## 1. 기본 정보")
        res1 = validate_task_contract(md_no_header, None)
        self.assertFalse(res1.is_valid)
        self.assertEqual(res1.status, "NEEDS_HUMAN_REVIEW")
        self.assertTrue(any("Contract 버전" in r for r in res1.reasons))

        # 2. 헤더 포맷 잘못됨
        md_bad_header = SAMPLE_VALID_CONTRACT_FIXTURE.replace("# Task Contract v0.1 — SAMPLE-TASK-001", "# Random Document Header")
        res2 = validate_task_contract(md_bad_header, None)
        self.assertFalse(res2.is_valid)
        self.assertEqual(res2.status, "NEEDS_HUMAN_REVIEW")
        self.assertTrue(any("Contract 버전" in r for r in res2.reasons))

    # --- BL-PH1-002 추가 검증 테스트 ---

    def test_approval_id_format_validation(self):
        """approval_id 검증 함수(validate_approval_id) 유효성 및 오류 제어 테스트."""
        # 1. 정상 형식
        valid, msg = validate_approval_id("APV-SAMPLE-TASK-001-20260916-001", "SAMPLE-TASK-001")
        self.assertTrue(valid)
        self.assertIsNone(msg)

        # 2. 접두어 불일치
        valid, msg = validate_approval_id("APV-WRONG-TASK-20260916-001", "SAMPLE-TASK-001")
        self.assertFalse(valid)
        self.assertIn("접두어", msg)

        # 3. 날짜 오류 (존재하지 않는 날짜 02월 30일)
        valid, msg = validate_approval_id("APV-SAMPLE-TASK-001-20260230-001", "SAMPLE-TASK-001")
        self.assertFalse(valid)
        self.assertIn("유효한 달력 날짜가 아닙니다", msg)

        # 4. 순번 NNN 오류 (2자리 숫자)
        valid, msg = validate_approval_id("APV-SAMPLE-TASK-001-20260916-01", "SAMPLE-TASK-001")
        self.assertFalse(valid)
        self.assertIn("규격과 일치하지 않습니다", msg)

        # 5. 제어문자 및 공백 포함
        valid, msg = validate_approval_id("APV-SAMPLE-TASK-001-20260916-001\n", "SAMPLE-TASK-001")
        self.assertFalse(valid)
        self.assertIn("제어문자 또는 공백이 포함되어 있습니다", msg)

        # 6. 빈 문자열
        valid, msg = validate_approval_id("", "SAMPLE-TASK-001")
        self.assertFalse(valid)
        self.assertIn("비어 있습니다", msg)

    def test_approval_history_valid_active(self):
        """정상 ACTIVE 승인 이력이 존재하는 경우 검증 통과 및 APPROVED 상태 판정 테스트."""
        contract = parse_task_contract_markdown(SAMPLE_VALID_CONTRACT_FIXTURE)
        _, scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
        _, contract_hash = canonicalize_contract(contract)

        evidence = ApprovalEvidence(
            approval_id="APV-SAMPLE-TASK-001-20260916-001",
            task_id="SAMPLE-TASK-001",
            contract_version="v0.1",
            contract_hash=contract_hash,
            approved_scope_hash=scope_hash,
            approver="User",
            approval_time_utc="2026-09-16T00:00:00Z",
            status="ACTIVE"
        )

        history = [
            ApprovalHistoryItem(
                approval_id="APV-SAMPLE-TASK-001-20260916-001",
                task_id="SAMPLE-TASK-001",
                contract_hash=contract_hash,
                approved_scope_hash=scope_hash,
                status="ACTIVE",
                recorded_at_utc="2026-09-16T00:00:00Z"
            )
        ]

        res = validate_task_contract(SAMPLE_VALID_CONTRACT_FIXTURE, evidence, history)
        self.assertTrue(res.is_valid)
        self.assertTrue(res.is_dispatch_eligible)
        self.assertEqual(res.status, "APPROVED")

    def test_approval_history_binding_mismatch(self):
        """승인 이력의 Task/Contract/Scope 결속 불일치 시 is_valid=False 및 NEEDS_HUMAN_REVIEW 처리 테스트."""
        contract = parse_task_contract_markdown(SAMPLE_VALID_CONTRACT_FIXTURE)
        _, scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
        _, contract_hash = canonicalize_contract(contract)

        evidence = ApprovalEvidence(
            approval_id="APV-SAMPLE-TASK-001-20260916-001",
            task_id="SAMPLE-TASK-001",
            contract_version="v0.1",
            contract_hash=contract_hash,
            approved_scope_hash=scope_hash,
            approver="User",
            approval_time_utc="2026-09-16T00:00:00Z",
            status="ACTIVE"
        )

        # contract_hash 불일치 이력
        history_bad_hash = [
            ApprovalHistoryItem(
                approval_id="APV-SAMPLE-TASK-001-20260916-001",
                task_id="SAMPLE-TASK-001",
                contract_hash="0000000000000000000000000000000000000000000000000000000000000000",
                approved_scope_hash=scope_hash,
                status="ACTIVE",
                recorded_at_utc="2026-09-16T00:00:00Z"
            )
        ]

        res = validate_task_contract(SAMPLE_VALID_CONTRACT_FIXTURE, evidence, history_bad_hash)
        self.assertFalse(res.is_valid)
        self.assertFalse(res.is_dispatch_eligible)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertTrue(any("승인 이력 바인딩 불일치" in r for r in res.reasons))

    def test_approval_history_same_time_conflict(self):
        """동일 approval_id 및 동일 recorded_at_utc 시각에 상충되는 상태 이력 존재 시 is_valid=False 처리 테스트."""
        contract = parse_task_contract_markdown(SAMPLE_VALID_CONTRACT_FIXTURE)
        _, scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
        _, contract_hash = canonicalize_contract(contract)

        evidence = ApprovalEvidence(
            approval_id="APV-SAMPLE-TASK-001-20260916-001",
            task_id="SAMPLE-TASK-001",
            contract_version="v0.1",
            contract_hash=contract_hash,
            approved_scope_hash=scope_hash,
            approver="User",
            approval_time_utc="2026-09-16T00:00:00Z",
            status="ACTIVE"
        )

        history_conflict = [
            ApprovalHistoryItem(
                approval_id="APV-SAMPLE-TASK-001-20260916-001",
                task_id="SAMPLE-TASK-001",
                contract_hash=contract_hash,
                approved_scope_hash=scope_hash,
                status="ACTIVE",
                recorded_at_utc="2026-09-16T00:00:00Z"
            ),
            ApprovalHistoryItem(
                approval_id="APV-SAMPLE-TASK-001-20260916-001",
                task_id="SAMPLE-TASK-001",
                contract_hash=contract_hash,
                approved_scope_hash=scope_hash,
                status="WITHDRAWN",
                recorded_at_utc="2026-09-16T00:00:00Z"
            )
        ]

        res = validate_task_contract(SAMPLE_VALID_CONTRACT_FIXTURE, evidence, history_conflict)
        self.assertFalse(res.is_valid)
        self.assertFalse(res.is_dispatch_eligible)
        self.assertEqual(res.status, "NEEDS_HUMAN_REVIEW")
        self.assertTrue(any("상충되는 승인 이력이 존재합니다" in r for r in res.reasons))

    def test_approval_history_identical_record_deduplication(self):
        """동일 시각에 완벽히 동등한 레코드가 중복 존재하는 경우 안전하게 중복 제거/검증 통과 테스트."""
        contract = parse_task_contract_markdown(SAMPLE_VALID_CONTRACT_FIXTURE)
        _, scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
        _, contract_hash = canonicalize_contract(contract)

        evidence = ApprovalEvidence(
            approval_id="APV-SAMPLE-TASK-001-20260916-001",
            task_id="SAMPLE-TASK-001",
            contract_version="v0.1",
            contract_hash=contract_hash,
            approved_scope_hash=scope_hash,
            approver="User",
            approval_time_utc="2026-09-16T00:00:00Z",
            status="ACTIVE"
        )

        item = ApprovalHistoryItem(
            approval_id="APV-SAMPLE-TASK-001-20260916-001",
            task_id="SAMPLE-TASK-001",
            contract_hash=contract_hash,
            approved_scope_hash=scope_hash,
            status="ACTIVE",
            recorded_at_utc="2026-09-16T00:00:00Z"
        )
        history_dup = [item, item]

        res = validate_task_contract(SAMPLE_VALID_CONTRACT_FIXTURE, evidence, history_dup)
        self.assertTrue(res.is_valid)
        self.assertTrue(res.is_dispatch_eligible)
        self.assertEqual(res.status, "APPROVED")

    def test_approval_history_missing_and_non_active_statuses(self):
        """이력 부재 및 최신 이력 비활성(WITHDRAWN, MODIFIED, EXPIRED) 또는 알 수 없는 상태 시 is_valid=True 유지 및 is_dispatch_eligible=False 테스트."""
        contract = parse_task_contract_markdown(SAMPLE_VALID_CONTRACT_FIXTURE)
        _, scope_hash = canonicalize_scope(contract.allowed_paths, contract.forbidden_paths)
        _, contract_hash = canonicalize_contract(contract)

        evidence = ApprovalEvidence(
            approval_id="APV-SAMPLE-TASK-001-20260916-001",
            task_id="SAMPLE-TASK-001",
            contract_version="v0.1",
            contract_hash=contract_hash,
            approved_scope_hash=scope_hash,
            approver="User",
            approval_time_utc="2026-09-16T00:00:00Z",
            status="ACTIVE"
        )

        # 1. 이력 부재 (empty history)
        res_empty = validate_task_contract(SAMPLE_VALID_CONTRACT_FIXTURE, evidence, [])
        self.assertTrue(res_empty.is_valid)
        self.assertFalse(res_empty.is_dispatch_eligible)
        self.assertEqual(res_empty.status, "NEEDS_HUMAN_REVIEW")
        self.assertTrue(any("존재하지 않습니다" in r for r in res_empty.reasons))

        # 2. 비활성 및 알 수 없는 상태
        for st in ["WITHDRAWN", "MODIFIED", "EXPIRED", "UNKNOWN_STATUS"]:
            history_st = [
                ApprovalHistoryItem(
                    approval_id="APV-SAMPLE-TASK-001-20260916-001",
                    task_id="SAMPLE-TASK-001",
                    contract_hash=contract_hash,
                    approved_scope_hash=scope_hash,
                    status=st,
                    recorded_at_utc="2026-09-16T00:00:00Z"
                )
            ]
            res_st = validate_task_contract(SAMPLE_VALID_CONTRACT_FIXTURE, evidence, history_st)
            self.assertTrue(res_st.is_valid)
            self.assertFalse(res_st.is_dispatch_eligible)
            self.assertEqual(res_st.status, "NEEDS_HUMAN_REVIEW")

    # --- BL-PH1-005 Scope Lock 추가 검증 테스트 ---

    def test_scope_lock_pre_dispatch_validation(self):
        """Dispatch 전 Scope Lock 정규화 및 해시 검증 테스트."""
        allowed = [
            PathItem("src/orchestrator", "directory_recursive"),
            PathItem("tests", "directory_recursive"),
        ]
        forbidden = [
            PathItem("docs", "directory_recursive"),
            PathItem("AGENTS.md", "file"),
        ]
        _, expected_hash = canonicalize_scope(allowed, forbidden)

        # 1. 정상 검증 성공
        res_ok = validate_scope_lock_pre_dispatch(allowed, forbidden, expected_hash)
        self.assertTrue(res_ok.is_valid)
        self.assertEqual(res_ok.reasons, [])
        self.assertEqual(res_ok.approved_scope_hash, expected_hash)

        # 2. 해시 불일치
        res_hash_mismatch = validate_scope_lock_pre_dispatch(allowed, forbidden, "0000000000000000000000000000000000000000000000000000000000000000")
        self.assertFalse(res_hash_mismatch.is_valid)
        self.assertEqual(res_hash_mismatch.reasons, ["SCOPE_HASH_MISMATCH"])

        # 3. 해시 누락/빈문자열
        res_hash_empty = validate_scope_lock_pre_dispatch(allowed, forbidden, "")
        self.assertFalse(res_hash_empty.is_valid)
        self.assertEqual(res_hash_empty.reasons, ["SCOPE_HASH_MISMATCH"])

        # 4. 경로 정규화 실패 (절대 경로)
        invalid_allowed = [PathItem("/abs/path", "directory_recursive")]
        res_canon_fail = validate_scope_lock_pre_dispatch(invalid_allowed, forbidden, expected_hash)
        self.assertFalse(res_canon_fail.is_valid)
        self.assertEqual(res_canon_fail.reasons, ["SCOPE_LOCK_CANONICALIZATION_FAILED"])

    def test_changed_files_against_scope_lock_valid_and_empty(self):
        """결과 수집 후 정상 변경 파일 및 빈 변경 목록 검증 테스트."""
        allowed = [
            PathItem("src/orchestrator", "directory_recursive"),
            PathItem("tests", "directory_recursive"),
        ]
        forbidden = [
            PathItem("docs", "directory_recursive"),
            PathItem("AGENTS.md", "file"),
        ]
        _, expected_hash = canonicalize_scope(allowed, forbidden)

        # 1. 허용 범위 내 유효한 변경 파일 목록
        changed = ["src/orchestrator/validator.py", "tests/test_validator.py"]
        res_ok = validate_changed_files_against_scope_lock(changed, allowed, forbidden, expected_hash)
        self.assertTrue(res_ok.is_valid)
        self.assertEqual(res_ok.reasons, [])
        self.assertEqual(res_ok.approved_scope_hash, expected_hash)

        # 2. 빈 목록 ("변경 없음") 유효성 처리
        res_empty = validate_changed_files_against_scope_lock([], allowed, forbidden, expected_hash)
        self.assertTrue(res_empty.is_valid)
        self.assertEqual(res_empty.reasons, [])

    def test_changed_files_scope_hash_mismatch_and_missing(self):
        """결과 수집 후 승인 Scope 해시 불일치, 빈 문자열, None 전달시 실패 테스트."""
        allowed = [PathItem("src/orchestrator", "directory_recursive")]
        forbidden = [PathItem("docs", "directory_recursive")]
        _, expected_hash = canonicalize_scope(allowed, forbidden)
        changed = ["src/orchestrator/validator.py"]

        # 1. 해시 불일치
        res_mismatch = validate_changed_files_against_scope_lock(changed, allowed, forbidden, "0000000000000000000000000000000000000000000000000000000000000000")
        self.assertFalse(res_mismatch.is_valid)
        self.assertEqual(res_mismatch.reasons, ["SCOPE_HASH_MISMATCH"])

        # 2. 빈 문자열
        res_empty = validate_changed_files_against_scope_lock(changed, allowed, forbidden, "")
        self.assertFalse(res_empty.is_valid)
        self.assertEqual(res_empty.reasons, ["SCOPE_HASH_MISMATCH"])

        # 3. None
        res_none = validate_changed_files_against_scope_lock(changed, allowed, forbidden, None)
        self.assertFalse(res_none.is_valid)
        self.assertEqual(res_none.reasons, ["SCOPE_HASH_MISMATCH"])

    def test_changed_files_format_invalid_rejections(self):
        """절대 경로, 역슬래시, '.', '..', 빈 문자열 등 포맷 오류 거부 테스트."""
        allowed = [PathItem("src/orchestrator", "directory_recursive")]
        forbidden = [PathItem("docs", "directory_recursive")]
        _, expected_hash = canonicalize_scope(allowed, forbidden)

        bad_format_cases = [
            ["/src/orchestrator/file.py"],          # 절대 경로
            ["src\\orchestrator\\file.py"],          # 역슬래시
            ["src/orchestrator/../src/file.py"],    # '..' 세그먼트
            ["src/orchestrator/./file.py"],          # '.' 세그먼트
            [""],                                     # 빈 문자열
            ["   "],                                  # 공백 문자열
            [None],                                   # None 항목
        ]

        for bad_case in bad_format_cases:
            res = validate_changed_files_against_scope_lock(bad_case, allowed, forbidden, expected_hash)
            self.assertFalse(res.is_valid)
            self.assertIn("SCOPE_PATH_FORMAT_INVALID", res.reasons)

    def test_changed_files_forbidden_and_out_of_bounds_violations(self):
        """금지 경로 위반 및 허용 범위 밖 변경 거부 테스트."""
        allowed = [
            PathItem("src/orchestrator", "directory_recursive"),
            PathItem("tests", "directory_recursive"),
        ]
        forbidden = [
            PathItem("docs", "directory_recursive"),
            PathItem("AGENTS.md", "file"),
        ]
        _, expected_hash = canonicalize_scope(allowed, forbidden)

        # 1. 금지 경로 디렉터리 위반
        res_forb_dir = validate_changed_files_against_scope_lock(["docs/README.md"], allowed, forbidden, expected_hash)
        self.assertFalse(res_forb_dir.is_valid)
        self.assertEqual(res_forb_dir.reasons, ["SCOPE_PATH_FORBIDDEN_VIOLATION"])

        # 2. 금지 경로 단일 파일 위반
        res_forb_file = validate_changed_files_against_scope_lock(["AGENTS.md"], allowed, forbidden, expected_hash)
        self.assertFalse(res_forb_file.is_valid)
        self.assertEqual(res_forb_file.reasons, ["SCOPE_PATH_FORBIDDEN_VIOLATION"])

        # 3. 허용 범위 밖 파일
        res_oob = validate_changed_files_against_scope_lock(["random_script.py"], allowed, forbidden, expected_hash)
        self.assertFalse(res_oob.is_valid)
        self.assertEqual(res_oob.reasons, ["SCOPE_PATH_OUT_OF_BOUNDS"])

        # 4. 접두어 유사 경계 불일치 (src/orchestrator2 는 src/orchestrator 에 매칭되지 않아야 함)
        res_prefix_mismatch = validate_changed_files_against_scope_lock(["src/orchestrator2/file.py"], allowed, forbidden, expected_hash)
        self.assertFalse(res_prefix_mismatch.is_valid)
        self.assertEqual(res_prefix_mismatch.reasons, ["SCOPE_PATH_OUT_OF_BOUNDS"])

    def test_forbidden_path_priority_over_allowed_path(self):
        """금지 경로 판정이 허용 경로 판정보다 우선 적용되는지 테스트."""
        allowed = [PathItem("docs", "directory_recursive")]
        forbidden = [PathItem("docs/private", "directory_recursive")]
        _, expected_hash = canonicalize_scope(allowed, forbidden)

        # docs/private/secret.txt 는 allowed(docs)에도 속하지만 forbidden(docs/private)에도 속하므로 FORBIDDEN_VIOLATION 우선
        res = validate_changed_files_against_scope_lock(["docs/private/secret.txt"], allowed, forbidden, expected_hash)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.reasons, ["SCOPE_PATH_FORBIDDEN_VIOLATION"])


if __name__ == "__main__":
    unittest.main()
