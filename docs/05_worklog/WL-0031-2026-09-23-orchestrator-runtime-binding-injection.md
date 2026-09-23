# WL-0031: Orchestrator 런타임 결속 주입

- **작성일:** 2026-09-23 (KST)
- **작성자:** Jules
- **태스크 ID:** JULES-RUNTIME-BINDING-INJECTION-001
- **상태:** 완료

## 1. 작업 개요
본 작업은 Orchestrator의 완료 결과 검토 인계 과정(`execute_review_handoff`)에 Jules 상태 저장소 팩토리 주입 지점을 신설하여, 1:1:1 세션 결속(Session:Branch:PR) 정보가 영속화될 수 있는 통합 지점을 마련하는 데 목적이 있습니다. 실제 `.env` 변경이나 외부 DB 초기화는 수행하지 않으며, 기존 직접 `repository` 주입과 미주입 시의 동작은 그대로 보존합니다.

## 2. 주요 변경 사항
- **`.orchestrator/src/orchestrator/review_handoff.py` 변경**
  - `execute_review_handoff` 파라미터에 `jules_state_repository_factory` 추가.
  - 패키지 상태가 `RESULT_COLLECTED`로 판정된 이후에만 팩토리를 지연 호출하도록 변경.
  - 기존에 직접 주입된 `repository`가 있는 경우, 팩토리보다 우선하여 적용되도록 우선순위 로직 구현.
  - 팩토리 초기화 실패 또는 저장 오류 발생 시, 원시 오류를 노출하거나 알림을 전송하지 않고 무저장 상태로 즉각 `NEEDS_HUMAN_REVIEW`(`FACTORY_INIT_ERROR` 또는 `BINDING_SAVE_ERROR`)로 전이하도록 구현.

- **비회귀 및 신규 동작 검증 (`.orchestrator/tests/test_review_handoff.py`)**
  - **직접 `repository` 주입 우선순위**: 직접 주입된 `repository`와 팩토리를 함께 전달 시 팩토리가 호출되지 않고 직접 `repository`가 사용됨을 검증.
  - **하위 호환성 검증**: 둘 다 전달되지 않은 경우 영속 저장 없이 기존처럼 정상적으로 검토 인계가 진행됨을 검증.
  - **팩토리 주입 동작**: `repository` 없이 팩토리만 주입된 경우 팩토리가 호출되어 영구 결속이 정상 저장됨을 검증.
  - **오류 처리**: 팩토리 내부에서 예외 발생 시 `NEEDS_HUMAN_REVIEW` 전이 반환 검증.

- **문서 갱신**
  - `docs/01_governance/orchestrator-runtime-db-operations.md`: 상태 저장소 인계 통합 지점의 지연 초기화, 의존성 주입 우선순위 규칙 및 예외 처리 원칙 문서화.
  - `docs/06_backlog/BL-0005-orchestrator-runtime-db-operating-baseline.md`: `execute_review_handoff` 내 통합 지점 구현 완료 사실 갱신.

## 3. 결과 및 검증
모든 코드는 테스트 대역과 임시 디렉터리 기반으로 작성되었으며, 실제 DB 환경 접근 없이 성공적으로 `pytest` 테스트 검증을 마쳤습니다. 결속 충돌이나 팩토리 초기화 실패 시에도 안전하게 수동 개입 상태로 전환됨을 확인하였습니다.
