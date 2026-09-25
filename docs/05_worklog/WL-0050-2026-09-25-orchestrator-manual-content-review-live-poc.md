---
작성일: 2026-09-25
작성자: Jules
상태: 완료
관련_Task: [비민감 식별자 마스킹됨]
---

# Pre-PR 수동 콘텐츠 검토 진입점 추가 및 저장소 증적 무결성 검증

## 1. 개요
Codex가 Jules 세션의 등록된 Plan의 활동 원문을 읽어 콘텐츠 검토를 수행할 수 있도록, Pre-PR 단계의 명시적 수동 진입점(`manual_registered_content_review_entrypoint.py`)을 추가하였습니다.

## 2. 주요 변경 사항
- **Pre-PR 진입점 추가**: `.orchestrator/src/orchestrator/manual_registered_content_review_entrypoint.py`
  - 비영속적, 비로그 목적의 객체 `ManualRegisteredContentReviewRequest` 설계 및 `<REDACTED>` 마스킹 적용.
  - Contract, `ApprovalEvidence`(ACTIVE), 및 등록된 Plan 정보(세션 ID 등) 간의 상호 대조 수행.
  - **저장소 명시적 대조 보강**: `StateRepository`를 통해 저장된 `TaskRecord`와 `ApprovalEvidence`를 직접 조회하여, 요청된 Contract 및 승인 상태와 `task_id`, `base_commit_sha`, `contract_hash`, `approved_scope_hash`, `idempotency_key`, `contract_version`, `approval_id`, ACTIVE 상태가 모두 완벽히 일치하는지 엄격히 대조합니다.
  - **예외 차단**: 조회 과정(`get_task`, `get_approval_evidence`, `get_plan_session_registration`)에서 예외 발생 시 메시지 전파 없이 즉시 `NEEDS_HUMAN_REVIEW`(`REPOSITORY_FETCH_FAILED`)로 차단합니다.
  - 검증 실패 시: 외부 API 통신 및 Reader 위임 없이 즉시 `NEEDS_HUMAN_REVIEW` 반환 (0회 호출 보장).
  - 검증 성공 시: 기존 `fetch_content_review_activities` 리더를 수정 없이 호출하여 정확히 1회 위임 처리.
- **기존 Post-PR 경로 보존**: `.orchestrator/src/orchestrator/manual_content_review_entrypoint.py` 및 관련 Reader는 절대 수정하지 않음으로써 기존 1:1:1 결속 검증이 약화되지 않도록 유지.
- **테스트 추가**: `.orchestrator/tests/test_manual_registered_content_review_entrypoint.py`
  - 저장소 증적 불일치(`TaskRecord`, `ApprovalEvidence` 불일치), 해시 불일치, 세션 등록 불일치, 그리고 저장소 예외 발생 시나리오에 대해 각각 0회 호출을 명시적으로 검증.
  - 정상 경로에서는 Reader가 정확히 1회 호출됨을 명시적으로 단언.
- **모듈 익스포트**: `.orchestrator/src/orchestrator/__init__.py`에 신규 진입점 익스포트 추가.

## 3. 롤백 정책
- 단일 PR 원칙을 준수하여 본 작업은 단일 커밋 및 PR로 제출됩니다.
- 문제가 발생할 경우 자동 롤백이나 재작업이 아닌, **병합 전 PR 닫기** 또는 **병합 후 Revert Commit**을 통해 수동 롤백을 수행합니다.

## 4. 검증 결과
- 모든 단위 테스트 통과 (저장소 예외 및 증적 대조 신규 테스트 포함).
- `git diff --check`를 통한 포맷팅 확인 완료.
- 실제 API 통신이나 DB 기록 없이 Fake/Mock 어댑터를 통해 위임 횟수 검증 완료.
