# Orchestrator Plan 단계 세션 등록 설계

**작성일**: 2026-09-24 (KST)
**상태**: 등록 기반 및 Dispatch 연결 구현 완료

## 목적

브랜치와 PR이 아직 없는 Jules Interactive Plan 세션을 비민감 식별·승인 결속 정보로 등록한다. 이후 Codex의 명시적 수동 조회·메시지 작업이 정확한 세션을 참조할 수 있게 하되, 최종 1:1:1 영구 결속은 대체하지 않는다.

## 저장 경계

등록 레코드는 Task ID, Session ID, 승인 증적 식별값, Contract/Scope 해시, UTC 시각만 보유한다. 원문 Plan·활동·프롬프트·source resource name·비밀값·브랜치·PR·SQLite 파일 내용은 기록하지 않는다. 표현 및 직렬화 경계에서는 Session ID를 마스킹한다.

## 검증 순서

1. 승인 증적 ACTIVE, Plan 승인 필수, 자동 병합 금지를 확인한다.
2. Task ID·Contract 버전·정규화 Contract/Scope 해시를 대조한다.
3. 저장된 Task·ApprovalEvidence와 대조한다.
4. 세션 생성 결과가 CREATED 상태이며 브랜치·PR 미생성 상태인지 확인한다.
5. 모두 통과한 경우에만 등록한다. 실패·중복은 저장 없이 `NEEDS_HUMAN_REVIEW`를 반환한다.

## 최종 결속 및 자동화 경계

Plan 단계 등록과 기존 PersistentSessionBinding은 서로 분리된다. 브랜치와 PR이 생성된 뒤에만 기존 절차로 최종 1:1:1 결속을 검증한다. 자동 승인·검토·메시지 전송·병합·배포·재시도·재작업은 이 설계의 범위가 아니다.


## Dispatch 연결 지점

execute_dispatch_session은 기존 사전 검증을 모두 통과한 뒤 세션 생성 API를 정확히 한 번 호출한다. 호출자가 Plan 세션 저장소를 명시적으로 주입하고 생성 응답이 CREATED인 경우에만 등록 함수를 호출한다.

저장소 미주입은 기존 동작을 유지한다. 등록이 실패하면 세션 생성 API를 재호출하지 않고 원문 없는 NEEDS_HUMAN_REVIEW와 고정 사유 코드만 반환한다. 이 연결은 최종 영구 결속·원문 조회·메시지 전송 또는 자동화 기능을 추가하지 않는다.


## 수동 Plan 검토 진입점
1. **명시적 1회 위임 원칙**: 외부 진입점(수동 Plan 검토)에서는 `ManualPlanReviewRequest`와 같이 민감 정보가 마스킹된 DTO를 수신한다. 진입점 내에서 외부 저장소 등록 조회(상태 확인)를 정확히 1회 수행하여 식별자 및 해시를 대조한 후, 일치할 경우 기존 Reader(어댑터)에 1회 위임한다.
2. **사전 검증(Pre-validation) 및 1:1:1 유예**: ACTIVE, plan_approval_required, auto_merge=False 조건을 검증한다. 이 단계는 PR 생성 전(Pre-PR) 단계이므로 최종 'Session-Branch-PR' 1:1:1 결속 검사가 일시적으로 유예되지만, 이는 최종 결속 단계에서의 엄격성을 절대 변경하지 않는다.

## 롤백

미병합 시 PR을 수동 종료하고, 병합 후 문제가 확인되면 해당 merge commit을 수동 revert한다.
