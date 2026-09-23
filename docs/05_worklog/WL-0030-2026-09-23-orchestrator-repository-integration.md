# WL-0030: Orchestrator 상태 저장소 연동

- **Date**: 2026-09-23 (KST)
- **Status**: Completed
- **Author**: Jules

## Task Description
JULES-STATE-REPOSITORY-INTEGRATION-001 작업 계약에 따라, `ORCHESTRATOR_JULES_STATE_DIR` 환경 변수를 활용하여 검증된 외부 경로에 Jules 전용 상태 저장소를 생성하고 연결할 수 있도록 팩토리 함수를 도입하고 테스트를 구성함. 실제 환경 구축 및 초기화는 보류(Deferred)하고, 테스트 가능한 연동 준비 상태만 완수함.

## Key Changes
- `runtime_config.py`에 Jules 전용 DB 파일명(`jules_orchestrator_state.db`) 반환 및 `get_jules_state_repository()` 팩토리 함수 추가.
- `__init__.py`에 `get_jules_state_repository`를 공개 API로 export.
- 임시 디렉터리 및 임시 `.env` 주입 방식을 사용하여 팩토리의 절대 경로 검증, 저장소 외부 경로 강제, 정상 생성 여부를 단위 테스트(`test_runtime_config.py`)로 확인.
- 명시적 경로 주입으로 동작하는 기존 `StateRepository` 생성 방식과 테스트가 호환되도록 비회귀(Non-regression) 상태 보존.

## Decisions Made
- 실제 `ORCHESTRATOR_JULES_STATE_DIR` 디렉터리 생성 및 DB 초기화 작업은 이번 작업에 포함하지 않음. 이는 팩토리 함수가 명시적으로 호출될 때만 이뤄지도록 구현되었으며, 실제 운영 환경에서의 호출 및 설정은 사용자 추가 승인 후 `BL-0005`에 의해 후속 진행됨.
- `ORCHESTRATOR_JULES_STATE_DIR` 환경 변수 파싱 및 로더 동작 모킹은 도입하지 않고, 기존 설계 사상대로 실제 텍스트 형태의 임시 `.env` 파일을 테스트에 주입하여 동작을 검증함.

## Impact & Next Steps
- Orchestrator 상태 DB가 안전한 외부 경로와 Jules 전용 파일명으로 연결될 수 있는 구조적 팩토리 기반이 마련됨.
- 후속 단계(`BL-0005` 등)에서 사용자의 결정에 따라 운영 환경의 실행 계정 지정, 백업 정책 설정, 실제 경로 이관, 및 Orchestrator 호출부에 팩토리를 주입하는 작업이 요구됨.
