# WL-0038: Orchestrator 수동 Plan Review Reader 구현

- **작성일**: 2026-09-24 (KST)
- **작성자**: Jules
- **태스크 ID**: ORCHESTRATOR-MANUAL-PLAN-READER-002
- **상태**: 완료

## 1. 개요
Codex가 Jules 세션의 최신 Plan 원문을 일회성으로 조회하고 검토할 수 있는 수동 진입점(`plan_review_reader.py`)을 설계 및 구현함.

## 2. 주요 작업 내용
1. **수동 Plan 검토 진입점 구현 (`plan_review_reader.py`)**
   - PR 생성 전 단계임을 감안하여 최종 1:1:1 결속(Session:Branch:PR) 검증을 유예하고, `JulesSessionResponse` 내 `session_id`, `task_id` 및 Contract의 `plan_approval_required` 등을 사전 검증함.
   - 반환 객체인 `PlanReviewResult`에 `__repr__`, `__str__`, `to_dict` 메서드를 오버라이드하여 Plan 원문을 `<REDACTED>` 처리함으로써 비영속/비로그 원칙을 강제함.

2. **전용 조회 경계 분리 (`jules_adapter.py`)**
   - 기존의 `get_activities`/`ActivitySummary`는 비민감 요약 정보 전용으로 남기고, Plan 원문 조회 전용 메서드인 `fetch_plan_text_only`를 분리 추가.
   - API 응답 중 `planGenerated` 이벤트에서 오직 단일 키 `plan`만을 사용하여 텍스트를 추출하며, 기타 키 추정을 금지함. 오류 시 원문 없이 `None`을 반환하여 차단.

3. **테스트 및 검증 (`test_plan_review_reader.py` 등)**
   - 사전 검증 불일치 시 API 호출이 발생하지 않는지 방어 로직 검증 완료.
   - 단일 키(`plan`) 추출 성공 및 부재/형식 오류 시의 차단 동작 검증 완료.
   - 객체 직렬화 시 원문이 노출되지 않는(마스킹) 비영속 경계 검증 완료.

## 3. 참조 문서
- [orchestrator-manual-plan-review-reader-design.md](../99_reference/orchestrator-manual-plan-review-reader-design.md)
