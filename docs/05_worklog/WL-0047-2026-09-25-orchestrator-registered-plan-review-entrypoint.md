# Worklog: 수동 Plan 검토 단일 진입점 구현

* 작성일: 2026-09-25 (KST)
* 작성자: Jules
* 태스크 ID: ORCHESTRATOR-REGISTERED-PLAN-REVIEW-ENTRYPOINT-001
* 상태: 완료

## 목적
외부 StateRepository에 비민감하게 등록된 Plan 세션을 검증하고, 명시적 수동 요청 시 단회성으로 기존 Plan Reader에 위임하는 단일 진입점을 구축합니다. PR 생성 전(Pre-PR) 상태의 Plan 세션을 처리하기 위해 1:1:1 결속 유예가 적용되며, 이로 인해 최종 결속 기준이 변경되지는 않습니다.

## 변경 내용
- `.orchestrator/src/orchestrator/manual_plan_review_entrypoint.py` 생성: `ManualPlanReviewRequest` DTO 정의(repr, str, to_dict 오버라이드로 식별자/해시 마스킹). `execute_manual_registered_plan_review` 함수 구현 (사전 정책 검증 -> 저장소 1회 조회 -> 기존 Plan Reader 단 1회 위임).
- `.orchestrator/src/orchestrator/__init__.py` 익스포트 목록에 새로운 진입점과 요청 DTO 추가.
- `.orchestrator/tests/test_manual_plan_review_entrypoint.py` 테스트 케이스 작성: Mock 객체를 통한 어댑터 위임 횟수 검증(실패 시 0회, 정상 시 1회), 외부 파일/로깅 쓰기 없음, 객체 마스킹 기능 통과 확인 완료.
- 거버넌스 및 설계 문서 갱신: PR 전 1:1:1 결속 검증 유예 방침과 단 1회 위임 원칙을 기록.

## 검증 결과
- 모든 단위 테스트 정상 통과 (수정된 시그니처 위임 테스트를 포함한 해당 모듈 테스트 9건 및 전체 회귀 테스트 247건 통과 확인).
- `git diff --name-only` 점검 결과 지정된 파일 7개 범위 내에만 변경사항 위치함.
- 마크다운 링크 및 포맷팅 이상 없음.

## 롤백 정책
- 미병합 PR의 경우 수동 닫기, 병합 후 이슈 발생 시 해당 merge commit만 수동 revert 처리. 자동 병합이나 자동 롤백 스크립트는 존재하지 않음.
