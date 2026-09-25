---
작성일: 2026-09-25
작성자: Jules
상태: 완료
관련_Task: [비민감 식별자 마스킹됨]
---

# Pre-PR 수동 콘텐츠 검토 진입점 추가

## 1. 개요
Codex가 Jules 세션의 등록된 Plan의 활동 원문을 읽어 콘텐츠 검토를 수행할 수 있도록, Pre-PR 단계의 명시적 수동 진입점(`manual_registered_content_review_entrypoint.py`)을 추가하였습니다.

## 2. 주요 변경 사항
- **Pre-PR 진입점 추가**: `.orchestrator/src/orchestrator/manual_registered_content_review_entrypoint.py`
  - 비영속적, 비로그 목적의 객체 `ManualRegisteredContentReviewRequest` 설계 및 `<REDACTED>` 마스킹 적용.
  - Contract, `ApprovalEvidence`(ACTIVE), 및 등록된 Plan 정보(세션 ID 등) 간의 상호 대조 및 정규화 해시 무결성 검증 추가.
  - 검증 실패 시: 외부 API 통신 및 Reader 위임 없이 즉시 `NEEDS_HUMAN_REVIEW` 반환(0회 호출 보장).
  - 검증 성공 시: 기존 `fetch_content_review_activities` 리더를 수정 없이 호출하여 정확히 1회 위임 처리.
- **기존 Post-PR 경로 보존**: `.orchestrator/src/orchestrator/manual_content_review_entrypoint.py`는 절대 수정하지 않음으로써 최종 Session-Branch-PR 결속 검증이 약화되지 않도록 유지.
- **테스트 추가**: 성공/실패 시나리오(API 0회/1회 호출 검증 등)에 대한 단위 및 통합 테스트(`.orchestrator/tests/test_manual_registered_content_review_entrypoint.py`) 구현.
- **모듈 익스포트**: `.orchestrator/src/orchestrator/__init__.py`에 신규 진입점 익스포트 추가.

## 3. 롤백 정책
- 단일 PR 원칙을 준수하여 본 작업은 단일 커밋 및 PR로 제출됩니다.
- 문제가 발생할 경우 자동 롤백이나 재작업이 아닌, **병합 전 PR 닫기** 또는 **병합 후 Revert Commit**을 통해 수동 롤백을 수행합니다.

## 4. 검증 결과
- 모든 단위 테스트 통과 (총 254개).
- `git diff --check`를 통한 포맷팅 확인 완료.
- 실제 API 통신이나 DB 기록 없이 Fake/Mock 어댑터를 통해 위임 횟수 검증 완료.
