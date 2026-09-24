# Orchestrator Manual Plan Review Reader Design

## 1. 개요
Codex가 Jules 세션의 최신 Plan 원문을 정확히 일회 조회하여 검토하기 위한 단회성 수동 진입점(`plan_review_reader.py`)의 설계 원칙입니다.

## 2. 주요 책임 및 제약 사항
- **조회 전용 및 자동화 배제**: 수동 Plan 검토 조회 인터페이스로서, 어떠한 자동 승인, 자동 병합, 자동 배포 로직도 포함하지 않습니다.
- **단일 책임(Single Responsibility)**: 기존 `jules_adapter.py`의 `get_activities` 및 `ActivitySummary`는 비민감 요약 상태용으로 유지되며, Plan 원문은 `plan_review_reader`만이 호출하는 전용의 좁은 조회 경계(`fetch_plan_text_only`)를 통해서만 획득됩니다.

## 3. PR 이전 단계 검증 및 1:1:1 결속 유예
- **최종 결속 유예**: PR 생성 이전 단계에서 호출되므로, 최종 1:1:1 결속(Session:Branch:PR) 확인은 유예됩니다 (PR이 없으므로 검증 불가).
- **사전 검증 항목**:
  - 외부에서 주입된 세션 ID와 `JulesSessionResponse` 내 `session_id`의 일치 여부
  - `JulesSessionResponse` 내 `task_id`와 Contract의 `task_id` 일치 여부
  - Contract의 `base_commit_sha` 검증
  - Contract의 `plan_approval_required == True` 설정 확인
  - 승인 증적 상태 검증
- **오류 처리**: 위 조건 중 하나라도 충족하지 못하면 외부 API 조회 없이 즉시 `NEEDS_HUMAN_REVIEW`를 반환합니다.

## 4. 단일 Plan 이벤트 키 확정 원칙
- **정확한 키 매핑**: API 응답 내 `planGenerated` 이벤트 중 정확히 `plan`이라는 단일 키에서만 원문을 추출합니다. (`content` 등 타 키 추정 및 대체 탐색 금지).
- **엄격한 포맷 및 시간 검사**: `plan` 키가 없거나, 파싱 실패, 시간 순서 신뢰 불가(중복 시각, 포맷 오류 등) 상황 시 원문 반환 없이 `NEEDS_HUMAN_REVIEW`로 처리하여 구현 추정을 원천 차단합니다.

## 5. 비영속 및 비로그 경계
- Plan 원문은 반환 객체(`PlanReviewResult`)의 `plan_text`에만 임시로 존재하며, 일회성 반환용으로만 사용됩니다.
- 반환 객체의 `__repr__`, `__str__`, `to_dict` 메서드는 오버라이드되어 원문 텍스트를 `<REDACTED>`로 마스킹합니다.
- Git, PR, 마크다운 문서, SQLite DB, 예외 메시지, 로깅(콘솔 및 파일) 등 어떠한 영구 저장소나 로그에도 원문 데이터가 기록되거나 노출되지 않도록 설계 및 테스트됩니다.
