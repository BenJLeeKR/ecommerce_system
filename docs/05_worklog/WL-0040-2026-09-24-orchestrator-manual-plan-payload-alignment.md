# WL-0040: Orchestrator 수동 Plan 페이로드 정합화

- **작성일**: 2026-09-24 (KST)
- **작성자**: Jules
- **태스크 ID**: ORCHESTRATOR-MANUAL-PLAN-PAYLOAD-ALIGNMENT-001
- **상태**: 완료

## 1. 개요
Codex가 Jules 세션의 최신 Plan을 확인할 때, 기존 문자열 포맷 대신 승인된 실제 객체형 페이로드(`planGenerated.plan.steps`)에 맞게 추출 논리를 엄격하게 정합화함.

## 2. 주요 작업 내용
1. **페이로드 정합화 (`jules_adapter.py`)**
   - `fetch_plan_text_only` 메서드에서 `planGenerated.plan`이 객체이고 내부에 `steps` 배열을 가지는지 검증하도록 수정.
   - `steps` 배열의 각 단계가 객체이며, `title`과 `description`이 문자열인지 엄격히 검증. 이 외의 형식(문자열형 plan, 빈 배열, 누락, 타입 불일치)일 경우 `None`을 반환하여 즉시 차단(NEEDS_HUMAN_REVIEW).

2. **기존 단회성 조회 로직 유지 (`plan_review_reader.py`)**
   - Adapter 변경만으로 안전한 문자열 변환 및 차단이 달성되므로 `plan_review_reader.py` 내부 로직은 유지.
   - 반환 시 로그/DB 노출을 막는 기존의 비영속화 및 마스킹 처리 유지 검증.

3. **단위 테스트 업데이트 (`test_plan_review_reader.py`)**
   - `TestJulesAdapterFetchPlanTextOnly` 클래스에서 변경된 객체형 페이로드 구조를 성공적으로 처리하는 케이스 추가.
   - 기존 문자열형, 빈 배열, 잘못된 타입의 단계 항목 등 예외 케이스에서 `None`으로 거부하는 동작 검증.

4. **설계 문서 현행화**
   - `docs/99_reference/orchestrator-manual-plan-review-reader-design.md`에 단일 이벤트 키가 단일 문자열 대신 객체 배열(`steps`)의 형식을 엄격히 따라야 함을 명시.

## 3. 관련 문서
- `docs/99_reference/orchestrator-manual-plan-review-reader-design.md`
