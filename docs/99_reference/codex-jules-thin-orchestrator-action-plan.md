# Codex–Jules Thin Orchestrator Action Plan (임시)

- 상태: Draft
- 작성일: 2026-09-10
- 임시 위치: `/workspace/ecommerce/docs/99_reference/`
- 최종 이전 대상: `/workspace/orchestrator/` 저장소의 `docs/03_planning/`
- 관련 이커머스 Backlog: `BL-0004`
- 참고 계획: `docs/99_reference/codex_jules_thin_orchestrator_execution_plan.md`

> 이 문서는 별도 Orchestrator 프로젝트를 만들기 전의 임시 Action Plan이다. 이커머스 애플리케이션의 구현·배포 기준을 직접 변경하거나, 자동 병합·자동 배포를 승인하지 않는다. 별도 저장소가 생성되면 이 문서를 그 저장소의 `docs/03_planning/`으로 이동하고, 현재 문서는 이동 안내 문서로 대체한다.

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|---|---|---|
| 2026-09-10 | v0.1 | Task Contract 기반의 프롬프트 자동화와 구현 지원 확장 계획을 최초 작성 |

## 1. 목적

Codex가 작성한 작업 지시와 Jules의 완료 보고를 사람이 반복해서 복사·붙여넣기 하는 경로를 줄인다. Codex는 작업 계약과 결과 검토를 담당하고, Jules는 GitHub 브랜치·PR 작업을 실행하며, Thin Orchestrator는 판단 없이 전달·상태 추적·결과 수집만 수행한다.

## 2. 공통 원칙과 경계

- Orchestrator는 요구사항·아키텍처·우선순위·PR 병합 여부를 판단하거나 변경하지 않는다.
- `main` 병합, 테스트계 배포, 운영계 승격은 계속 사용자 명시 승인으로만 수행한다.
- Jules API 키, GitHub 토큰, SQLite 상태 DB, 실행 로그는 `/workspace/ecommerce`와 분리된 `/workspace/orchestrator/` 제어 저장소의 Git 제외 경로에서만 관리한다.
- 이커머스 저장소에는 Task ID, PR 번호, Worklog 등 추적 가능한 근거만 남기며 실행 상태·비밀값·제어 로그는 저장하지 않는다.
- 기준 브랜치는 현재 Git 규칙에 따라 `main`이다. Jules가 생성하는 실제 브랜치명에 의존하지 않고 Task ID·Jules 세션 ID·PR 번호·커밋 SHA를 연결한다.
- 모든 사용자용 기록은 한국어와 KST 기준으로 작성한다. 상태 저장소의 시각은 시간대 정보를 보존하는 UTC 기반 형식으로 저장하고 표시 시 KST로 변환한다.
- 주문·결제·재고·인증·권한·DB 마이그레이션·운영 인프라는 CRITICAL 또는 HIGH 위험도로 취급하며 자동 실행 범위에서 제외한다.

## 3. 목표 흐름

```text
Codex → Task Contract 생성 → Orchestrator → Jules API 세션 생성
      → Jules PR 생성 → Orchestrator 결과 수집 → Codex 검토 대기
      → 사용자 단문 검토 요청 → Codex PR 검토 → 사용자 병합 승인
```

초기 목표는 사용자가 긴 프롬프트와 Jules 완료 보고 전체를 복사·붙여넣지 않는 것이다. Codex 검토의 자동 시작과 병합은 초기 범위에 포함하지 않는다.

## 4. 1단계 — Task Contract 및 프롬프트 자동화

### 4.1 범위

- Task Contract v0.1 형식 정의 및 문법 검증
- 승인된 Contract를 Jules API 세션 생성 요청으로 변환
- Jules 세션 ID, URL, 실제 브랜치명, PR 번호·URL, 변경 파일, 실행 검증, 미해결 사항 수집
- Task ID별 결과 패키지와 Codex 검토 대기 상태 기록
- LOW 위험 문서 작업 1건으로 종단간 POC 수행

### 4.2 Task Contract 필수 항목

| 항목 | 기준 |
|---|---|
| Task ID | 저장소 내·외부 추적에 사용하는 고유 식별자 |
| 작업 목표 | Codex가 정리한 한 개 PR 단위의 목표 |
| 대상 저장소·기준 브랜치 | 이커머스 저장소와 `main` |
| 실행 에이전트 | Jules |
| 기준 문서 | 요구사항·설계·거버넌스 참조 목록 |
| 허용·금지 경로 | 작업 범위 강제와 충돌 검사 기준 |
| 완료 조건 | 테스트·문서 링크·검수 기준 |
| 위험도·승인 상태 | LOW/MEDIUM/HIGH/CRITICAL 및 사용자 승인 여부 |
| 계획 승인 필요 여부 | Jules 계획을 명시적으로 검토해야 하는지 여부 |
| 병합 설정 | 항상 `auto_merge: false` |

### 4.3 승인·실행 규칙

- LOW 위험 문서 작업만 사용자 시작 승인 후 자동 Dispatch를 허용한다.
- MEDIUM 이상은 Contract 생성 후 계획 검토·승인 절차를 유지한다.
- HIGH·CRITICAL은 자동 Dispatch하지 않으며, 기존 민감 영역·DB·배포 규칙을 우선 적용한다.
- API 오류·시간 초과는 상태를 기록하고 사용자 또는 Codex 검토 대상으로 전환한다. 자동 재시도·자동 재작업은 구현하지 않는다.

### 4.4 완료 기준

- Task Contract 하나로 Jules 세션이 생성되고, 수동 프롬프트 복사·붙여넣기가 필요 없다.
- Jules 결과·PR 정보를 Task ID로 조회할 수 있고, 완료 보고 전체를 Codex에 수동 전달할 필요가 없다.
- 실행 결과에 `Task ID`, `Jules 세션 ID`, `PR 번호`, `변경 파일`, `검증 결과`, `미해결 사항`이 남는다.
- 자동 병합·배포·민감 영역 실행이 발생하지 않는다.

## 5. 2단계 — 일반 구현 작업 지원 확장

### 5.1 진입 조건

- 1단계 POC와 추가 LOW 위험 작업이 안정적으로 완료되어 세션·PR 연결과 실패 기록 방식이 검증됨
- 이커머스 프로젝트 골격, 포맷·린트·타입 검사·단위 테스트·빌드의 기본 CI가 구성됨
- 일반 구현 작업의 테스트·검수 기준과 모듈 경계가 설계 문서에서 승인됨

### 5.2 범위

- 일반 코드 작업의 Task Contract, Jules 계획 승인, PR·CI 결과 추적
- CI 통과 여부를 Codex 검토 대기 조건으로 사용
- 허용 경로 기반의 단순 Scope Lock 및 동시에 실행 가능한 작업 수 제한
- Task ID 기반 Codex 검토 패키지 생성

### 5.3 제외 범위

- 자동 main 병합, 자동 테스트계·운영계 배포, 자동 릴리스 태그 생성
- Codex 검토 결과를 즉시 자동으로 Jules에 전달하는 재작업 루프
- 주문·결제·재고·인증·권한·DB 마이그레이션·운영 인프라의 자동 Dispatch
- 다중 Worker 확장, 대시보드, 중앙 관측성 플랫폼

### 5.4 완료 기준

- 일반 구현 작업에서 Contract → Jules 계획 → 사용자 승인 → PR·CI 수집 → Codex 검토 대기의 추적 흐름이 작동한다.
- CI 실패, 범위 위반, 시간 초과는 자동 병합 없이 명확한 실패 상태로 기록된다.
- 사용자에게는 작업 시작·Codex 검토 시작·병합 승인이라는 최소 승인 지점만 남는다.

## 6. 별도 프로젝트 이전 계획

1. `/workspace/orchestrator/`에 별도 Git 저장소와 기본 문서 구조를 만든다.
2. 이 문서를 새 저장소의 `docs/03_planning/`으로 이동하고, 연결 문서·상대 링크를 갱신한다.
3. 현재 문서는 이동 대상 경로와 이전 커밋을 안내하는 `Superseded` 문서로 전환한다.
4. API 키·토큰·런타임 상태는 새 저장소의 Git 제외 제어 경로에만 배치한다.
5. 별도 프로젝트의 `AGENTS.md`와 거버넌스에 이커머스의 사용자 승인·자동 병합 금지·민감 영역 보호 원칙을 연결한다.

## 7. 위험과 대응

| 위험 | 대응 |
|---|---|
| Jules API 알파 변경 | API 호출부를 교체 가능한 어댑터로 분리하고 버전·오류를 기록 |
| 브랜치명 자동 생성·재사용 | 브랜치명이 아닌 Task ID·세션 ID·PR 번호·SHA를 상태 기준으로 사용 |
| 비밀값 유출 | 저장소·PR·로그에 비밀값을 남기지 않고 제어 환경의 비밀 관리만 사용 |
| 자동화가 승인 경계를 우회 | `auto_merge: false`, HIGH·CRITICAL 자동 Dispatch 금지, 사용자 병합 승인 유지 |
| Jules 실패·시간 초과 | 자동 재시도 대신 `NEEDS_HUMAN_REVIEW` 상태로 전환 |

## 8. 검증 및 롤백

- 1단계 POC는 이커머스 저장소의 LOW 위험 문서 작업 1건만 대상으로 한다.
