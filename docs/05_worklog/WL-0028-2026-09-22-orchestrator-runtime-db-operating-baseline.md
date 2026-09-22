# WL-0028: Orchestrator Runtime DB Operating Baseline (문서화 작업)

## 1. 메타데이터

- **작업 ID**: `WL-0028-2026-09-22-orchestrator-runtime-db-operating-baseline`
- **관련 Task ID**: `ORCHESTRATOR-RUNTIME-DB-OPERATING-BASELINE-001`
- **연결 Backlog**: `BL-0005`
- **연결 Planning**: 없음
- **연결 Analysis**: 없음
- **작업자**: Jules (실행 에이전트)
- **생성 일시 (KST)**: 2026-09-22
- **수정 일시 (KST)**: 2026-09-22
- **상태**: Completed

## 2. 작업 목적

- Thin Orchestrator의 상태와 기록을 저장하는 SQLite Runtime DB에 대한 외부 저장 원칙, 접근 권한 통제, 백업 및 복구 기준을 문서화.
- 현재의 코드 레벨 주입(Injection) 방식과 향후 이관될 목표 경로(`/workspace/runtime/`)를 명확히 구분.
- 실제 인프라 및 설정 작업(디렉터리/DB 파일 생성, 권한 부여, 크론탭 수정 등)은 배제하고, 사용자 결정이 필요한 미결 사항들을 Backlog에 등록하여 향후 과제로 분리함.

## 3. 작업 내용

### 3.1. 거버넌스 기준 수립 및 문서 작성
- `docs/01_governance/orchestrator-runtime-db-operations.md` 작성 완료.
  - DB의 Git 커밋 금지 및 독립된 외부 저장 원칙 명시.
  - 현재 상태(호출자 주입 방식 유지)와 목표 상태(`/workspace/runtime/` 이관) 정의.
  - 보안 통제 사항(API 키, 토큰, 프롬프트, 활동 로그, SQLite DB 내용의 기록 금지) 명시.
- `docs/01_governance/README.md`에 새 문서 링크 추가.

### 3.2. 미결 사용자 결정 사항 Backlog 등록
- `docs/06_backlog/BL-0005-orchestrator-runtime-db-operating-baseline.md` 작성 완료.
  - 결정 필요 항목 기재: 실행 계정(Execution Account), 실제 이관 시점(Target Migration Date), 백업 정책(주기/보존 기간), 복구 목표(RPO/RTO).
- `docs/06_backlog/README.md` 인덱스에 BL-0005 추가.

### 3.3. 통제 준수 사항 확인
- 자동 병합, 자동 배포, 자동 재시도, 자동 재작업은 전혀 수행되지 않음.
- 실제 디렉터리, DB 파일, 백업/복구 스케줄러, 권한 설정, 환경 변수 변경, 운영 경로 접근은 일절 수행하지 않았음 (문서 작업으로 한정).
- 1:1:1 결속 규칙 준수 예정 (작업 종료 후 단일 브랜치, 단일 PR 생성).

## 4. 참조

- [Orchestrator Runtime DB 운영 기준](../01_governance/orchestrator-runtime-db-operations.md)
- [BL-0005: Orchestrator Runtime DB 실제 운영 기준 확립 및 이관](../06_backlog/BL-0005-orchestrator-runtime-db-operating-baseline.md)
