---
작성일: 2026-09-23T10:00:00+09:00
작성자: Jules
태스크 ID: ORCHESTRATOR-CANONICAL-SCOPE-HASH-GUARD-001
상태: 완료
---

# 작업 내역: Canonical Scope Hash Guard 적용

## 1. 개요
Jules 세션 생성 전 `allowed_paths` 및 `forbidden_paths`에 대한 정규화 해시를 선제적으로 산출 및 대조하여, 불일치 또는 정규화 실패 시 세션 생성을 원천 차단하고 즉각 `NEEDS_HUMAN_REVIEW`로 전환하도록 로직을 구현함.

## 2. 세부 변경 사항
- `JulesSessionRequest`에 `allowed_paths`, `forbidden_paths` 필수 필드 추가.
- `jules_adapter.py`의 `FakeJulesAdapter.create_session` 및 `RealJulesAdapter.create_session` 진입부(사전 게이트 통과 후 API/세션 생성 전)에 `canonicalize_scope` 검증 로직 추가.
- 실패 시 `SCOPE_LOCK_CANONICALIZATION_FAILED` 및 `SCOPE_HASH_MISMATCH` 처리.

## 3. 검증 결과
- 신규 테스트 케이스 `test_create_session_scope_canonicalization_failed`, `test_create_session_scope_hash_mismatch` 성공.
- 전체 단위 테스트 153개 통과 확인.
