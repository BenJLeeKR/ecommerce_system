# WL-0029: Orchestrator Jules State Dir 설정 도입

## 1. 메타데이터

- **작업 ID**: `WL-0029-2026-09-23-orchestrator-jules-state-dir`
- **관련 Task ID**: `ORCHESTRATOR-JULES-STATE-DIR-002`
- **연결 Backlog**: `BL-0005`
- **연결 Planning**: 없음
- **연결 Analysis**: 없음
- **작업자**: Jules (실행 에이전트)
- **생성 일시 (KST)**: 2026-09-23
- **수정 일시 (KST)**: 2026-09-23
- **상태**: Completed

## 2. 작업 목적

- Orchestrator의 상태와 기록을 관리하는 SQLite DB의 외부 경로를 `ORCHESTRATOR_JULES_STATE_DIR` 환경 변수를 통해 안전하게 로드하고 주입하기 위함.
- 절대 경로 및 Git 작업 트리 외부 위치를 검증하는 로직을 추가하여 보안과 독립성 강화.
- 실제 시스템 환경에 개입하지 않고 로더만 구현하여 거버넌스 및 백로그 문서에 정합성 반영.

## 3. 작업 내용

### 3.1. 로더 및 테스트 구현
- `.orchestrator/src/orchestrator/runtime_config.py`에 `load_orchestrator_jules_state_dir` 함수 추가:
  - 절대 경로 확인 및 Git 리포지토리 루트 하위 여부 검증 추가 (`RuntimeConfigError` 예외 발생).
- `.orchestrator/tests/test_runtime_config.py`에 정상/실패 단위 테스트 작성 및 기존 회귀 방지.
- `.orchestrator/.env.example`에 템플릿 변수 추가.

### 3.2. 문서 정합성 갱신
- `docs/01_governance/orchestrator-runtime-db-operations.md`를 갱신하여 환경 변수를 통한 주입과 검증 요건을 반영.
- `docs/06_backlog/BL-0005-orchestrator-runtime-db-operating-baseline.md`의 목표와 변경 이력을 업데이트.
- 이 Worklog를 작성하고 `docs/05_worklog/README.md`에 인덱스 링크 추가.

### 3.3. 통제 준수 사항 확인
- 이번 PR은 검증된 상태 디렉터리 경로를 호출자가 주입할 수 있도록 로더를 제공하는 단계로 한정됨.
- 실제 `.env` 설정, 기존 Runtime DB 호출부 연결, 실제 디렉터리 및 DB 생성은 수행되지 않았으며 별도 승인 대상으로 남김.
- 실제 시스템 환경(`.env`, DB 생성/이동, 권한/백업 설정 등) 변경 전혀 없음.
- API 키, 실제 식별자, 원시 데이터 및 민감 정보는 코드, 로그, 문서 어디에도 기록되지 않음.
- 단일 브랜치와 PR을 통해 1:1:1 결속 규칙 준수.

## 4. 참조

- [Orchestrator Runtime DB 운영 기준](../01_governance/orchestrator-runtime-db-operations.md)
- [BL-0005: Orchestrator Runtime DB 실제 운영 기준 확립 및 이관](../06_backlog/BL-0005-orchestrator-runtime-db-operating-baseline.md)
