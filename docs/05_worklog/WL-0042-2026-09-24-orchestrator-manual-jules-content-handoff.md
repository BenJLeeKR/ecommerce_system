# WL-0042: Orchestrator 수동 리뷰(Content Handoff) 리더 구현

**작성일**: 2026-09-24 (KST)
**태스크 ID**: ORCHESTRATOR-MANUAL-JULES-CONTENT-HANDOFF-002
**상태**: 완료

## 1. 개요
Jules 세션에 저장된 활동 이벤트(특히 `planGenerated` 등)의 원시 텍스트를 사용자가 수동으로 검토할 수 있도록 안전하게 추출하는 전용 Reader(`jules_content_review_reader.py`)를 신규 구현함.

## 2. 주요 변경 사항
1. **수동 조회용 모듈 추가**: `.orchestrator/src/orchestrator/jules_content_review_reader.py` 생성.
   - 사전 검증(`ACTIVE`, `plan_approval_required=True`, `auto_merge=False` 등)을 철저히 수행하고, 실패 시 어댑터/API 호출 0회를 보장함.
   - `planGenerated`, `agentMessaged`, `progressUpdated` 이벤트에서 허용된 필드만 추출하며 `description` 누락을 허용함.
   - 텍스트가 없는 `planApproved`, `sessionCompleted`는 메타데이터 없이 활동 표식만 반환. 미확인 이벤트 및 형식 오류 발견 시 즉각 조회를 차단(NEEDS_HUMAN_REVIEW)함.
2. **어댑터 기능 추가**: `.orchestrator/src/orchestrator/jules_adapter.py`
   - `fetch_raw_activities_for_content_review()` 메서드를 추가하여 안전한 원문 데이터 전달 경계를 확보함. 기존 `ActivitySummary`에는 영향을 주지 않음.
3. **보안 및 정책 준수**:
   - 추출된 데이터 객체(`ReviewActivity`)는 `to_dict`, `__str__`, `__repr__` 시 원문을 `<REDACTED>` 처리하여 로깅 및 영속화를 방지함.
   - 자동 승인, 자동 리뷰, 자동 병합 기능 없이 순수하게 수동 조회를 위한 구현만 반영.
4. **테스트 및 설계 문서 추가**:
   - `test_jules_content_review_reader.py`를 통해 모든 비영속(API 호출 검증 및 로깅 금지) 및 추출 테스트를 완료함.
   - `docs/99_reference/orchestrator-manual-jules-content-handoff-design.md` 신규 등록.
