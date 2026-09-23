# WL-0036: Orchestrator Dispatch Entrypoint Implementation

- **작성일**: 2026-09-23 (KST)
- **작성자**: Jules
- **태스크 ID**: ORCHESTRATOR-DISPATCH-ENTRYPOINT-001
- **상태**: 완료

## 1. 개요
Orchestrator의 Dispatch 과정에서 세션 생성을 위한 최상위 진입점인 `execute_dispatch_session` 모듈을 신규로 구현하고 검증을 완료함.

## 2. 작업 내용

### 2.1 신규 모듈 및 진입점 구현 (`dispatch_entrypoint.py`)
- **책임 및 의존성 주입**:
  - `TaskContract`와 `ApprovalEvidence`를 주입받아 처리함.
  - 외부 어댑터(`jules_adapter`) 및 `source_name`은 명시적으로 주입(DI)받아 외부 Runtime DB 접근이나 불필요한 환경 변수 읽기를 원천 차단함.
  - `JulesSessionRequest` 구성 시 `source_name`을 안전하게 전달하고, 로깅이나 반환값 등에서 노출하지 않음.
- **사전 검증(Pre-Dispatch Validation)**:
  - 승인 상태가 `ACTIVE`인지 확인.
  - 자동 병합(`auto_merge=False`) 및 플랜 승인 필수(`plan_approval_required=True`) 정책 확인.
  - `canonicalize_contract`로 생성한 `contract hash`와 `canonicalize_scope`로 생성한 `approved scope hash`를 승인 증적 데이터와 대조.
  - 기준 SHA(`base_commit_sha`)와 실제 SHA 대조.
  - 위 조건 중 하나라도 불일치하면 **실제 API 호출 없이** 즉시 `NEEDS_HUMAN_REVIEW` 중단 처리.
- **정상 세션 생성**:
  - 검증 성공 시 `main` 브랜치 기준 및 `requirePlanApproval=True` 강제 적용 상태로 세션 생성 요청 전달.

### 2.2 테스트 작성 (`test_dispatch_entrypoint.py`)
- 실제 API나 외부 DB 접근 없이 순수 Mock/Fake 환경에서 단위 테스트 작성.
- 해시, SHA, 상태 불일치 시의 중단 로직 검증 (API 호출 0회 확인).
- 정상 처리 시 `create_session` 호출 및 파라미터 전달 여부 검증.

### 2.3 거버넌스 및 백로그 갱신
- `docs/01_governance/orchestrator-runtime-db-operations.md`: Dispatch 진입점의 API/DB 미접근 안전 경계 추가.
- `docs/06_backlog/BL-0005-orchestrator-runtime-db-operating-baseline.md`: Dispatch 진입점 통합 완료 진행 상황 갱신.

## 3. 후속 작업 (Follow-up Actions)
- 없음. 본 태스크는 성공적으로 완료됨. 후속 결속 기록 활성화는 별도 백로그(BL-0005)를 통해 추적.