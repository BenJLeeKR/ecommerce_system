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
- `jules_adapter.py`의 `FakeJulesAdapter.create_session` 및 `RealJulesAdapter.create_session` 진입부(사전 게이트 및 외부 API 호출 이전)에 `canonicalize_scope` 검증 로직 추가.
- 일반 Exception 발생 시에도 `SCOPE_LOCK_CANONICALIZATION_FAILED` 처리로 원시 예외 전파 차단.
- 실패 시 `SCOPE_LOCK_CANONICALIZATION_FAILED` 및 `SCOPE_HASH_MISMATCH` 사유 코드로 즉시 `NEEDS_HUMAN_REVIEW` 전이.

## 3. 검증 결과
- 신규 단위 테스트 추가 성공 (Fake 및 Real 어댑터의 Scope Hash Mismatch, Canonicalization Failed, General Exception 차단).
- 해시 불일치 및 정규화 실패 시 Real 어댑터의 실제 외부 HTTP API가 호출되지 않음(`requests == 0`)을 검증 완료.
- 롤백 및 기존 동작(바인딩, requirePlanApproval=True, 실제 main 시작 등)에 대한 비회귀 테스트 및 전체 단위 테스트 155건 통과 확인.
