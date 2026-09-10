# Codex–Jules Thin Orchestrator 실행 계획

> 목적: Codex가 전체 개발 흐름을 관리하고, Jules가 실행 에이전트로 동작하며, 그 사이를 **얇은 Orchestrator**가 자동 연결하도록 구현한다.

---

## 1. 목표

현재의 수동 흐름:

```text
Codex에서 작업 프롬프트 작성
        ↓
사람이 Copy & Paste
        ↓
Jules에 작업 전달
        ↓
Jules 실행
        ↓
사람이 결과 확인
        ↓
Codex에 다시 전달하여 검증
```

목표 흐름:

```text
                     ┌────────────────────┐
                     │       Codex        │
                     │ Architect / Lead   │
                     └─────────┬──────────┘
                               │
                        Task Contract 생성
                               │
                               ▼
                     ┌────────────────────┐
                     │ Thin Orchestrator  │
                     │                    │
                     │ Dispatch           │
                     │ State Tracking     │
                     │ Retry / Timeout    │
                     │ Result Collection  │
                     └─────────┬──────────┘
                               │
                         Jules REST API
                               │
                               ▼
                     ┌────────────────────┐
                     │       Jules        │
                     │ Execution Agent    │
                     └─────────┬──────────┘
                               │
                           PR / Result
                               │
                               ▼
                         GitHub Actions
                               │
                               ▼
                     ┌────────────────────┐
                     │       Codex        │
                     │ Review / Validate  │
                     └────────────────────┘
```

핵심 원칙은 다음과 같다.

1. Codex가 **무엇을 할지** 결정한다.
2. Jules가 **어떻게 구현할지** 실행한다.
3. Orchestrator는 **판단하지 않는다.**
4. Orchestrator는 전달, 상태관리, 제한, 감사 로그만 담당한다.
5. 최종 품질 판단은 Codex와 CI가 담당한다.

---

# 2. Orchestrator를 "얇게" 유지해야 하는 이유

Orchestrator가 다음 영역까지 맡기 시작하면 안 된다.

```text
요구사항 분석
아키텍처 판단
구현 전략 결정
코드 리뷰
PR 승인 여부 판단
```

이 역할은 Codex에 남긴다.

Orchestrator의 책임은 아래로 제한한다.

```text
Task Contract 읽기
        ↓
유효성 검증
        ↓
Jules Session 생성
        ↓
Session ID 저장
        ↓
진행 상태 조회
        ↓
완료 결과 수집
        ↓
PR / Branch 정보 기록
        ↓
CI 상태 확인
        ↓
Codex Review Queue에 전달
```

따라서 Orchestrator는 가능한 한 **Deterministic Control Program**이어야 한다.

---

# 3. 권장 기술 스택

초기 버전은 Python으로 구현하는 것을 권장한다.

```text
Python 3.12+
FastAPI              선택 사항 - REST 관리 API 제공 시
Pydantic             Task Contract 검증
httpx                Jules REST API 호출
PyYAML                YAML Task Contract
SQLAlchemy            상태 DB 사용 시
SQLite                초기 상태 저장
PostgreSQL            운영 단계 전환 시
GitHub CLI / API      PR / CI 상태 확인
APScheduler / cron    Polling 실행
```

MVP에서는 다음 조합이면 충분하다.

```text
Python
+ Pydantic
+ httpx
+ YAML
+ SQLite
```

FastAPI는 운영 UI 또는 외부 API가 필요해지는 Phase 2 이후 도입한다.

---

# 4. Repository 구조

권장 구조:

```text
project-root/
│
├── AGENTS.md
├── ARCHITECTURE.md
├── DEVELOPMENT_GUIDE.md
│
├── docs/
│   ├── requirements/
│   ├── adr/
│   └── architecture/
│
├── .agent/
│   ├── tasks/
│   │   ├── pending/
│   │   ├── running/
│   │   ├── completed/
│   │   ├── failed/
│   │   └── review/
│   │
│   ├── results/
│   └── logs/
│
├── orchestrator/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── dispatcher.py
│   ├── jules_client.py
│   ├── github_client.py
│   ├── state_store.py
│   ├── validator.py
│   ├── monitor.py
│   └── retry_policy.py
│
├── orchestrator.db
│
└── src/
```

초기에는 별도의 중앙 서버를 만들지 않고 **프로젝트 Repository 내부에서 Orchestrator를 실행**하는 것이 가장 단순하다.

---

# 5. Task Contract 설계

Codex가 Jules에게 직접 긴 자연어 Prompt를 보내지 않는다.

Codex는 먼저 표준 Task Contract 파일을 만든다.

예:

```yaml
version: "1.0"

id: TASK-0231

title: 주문 취소 API 구현

executor: jules

repository:
  name: ecommerce-backend
  base_branch: develop

requirement_refs:
  - REQ-ORDER-017

architecture_refs:
  - docs/architecture/order.md

adr_refs:
  - docs/adr/ADR-012-outbox.md

objective: |
  CONFIRMED 상태의 주문을 취소할 수 있도록 주문 취소 API를 구현한다.

requirements:
  - CONFIRMED 상태의 주문만 취소 가능하다.
  - 이미 CANCELLED 상태인 경우 HTTP 409를 반환한다.
  - 주문 취소 시 재고 복원 이벤트를 생성한다.
  - ORDER_CANCELLED 이벤트는 Outbox Pattern을 사용한다.

scope:
  allowed_paths:
    - src/order/**
    - src/inventory/event/**
    - tests/order/**

  denied_paths:
    - src/security/**
    - infra/**
    - .github/**
    - db/migration/**

acceptance_criteria:
  - 기존 Unit Test 전체 통과
  - 신규 Unit Test 추가
  - 신규 Integration Test 추가
  - API Response Schema 변경 없음
  - Build 성공

risk:
  level: MEDIUM

execution:
  require_plan_approval: true
  max_iterations: 3
  timeout_minutes: 90

review:
  reviewer: codex
  auto_merge: false
```

---

# 6. Task Contract의 필수 필드

MVP에서는 최소 다음 항목을 강제한다.

| 필드 | 설명 |
|---|---|
| id | 고유 작업 ID |
| title | 작업명 |
| objective | 작업 목적 |
| repository | 대상 Repository |
| base_branch | 기준 Branch |
| requirement_refs | 원 요구사항 |
| allowed_paths | 수정 허용 범위 |
| denied_paths | 수정 금지 범위 |
| acceptance_criteria | 완료 조건 |
| risk.level | 위험도 |
| max_iterations | 최대 재시도 수 |
| timeout_minutes | 작업 제한시간 |

Task Contract가 유효하지 않으면 **Jules를 호출하지 않는다.**

---

# 7. 상태 모델

Task의 상태는 단순한 State Machine으로 관리한다.

```text
CREATED
   │
   ▼
VALIDATED
   │
   ▼
DISPATCHED
   │
   ▼
PLANNING
   │
   ▼
PLAN_REVIEW
   │
   ├──── REJECTED ────> REPLAN
   │                      │
   │                      └──> PLAN_REVIEW
   │
   ▼
RUNNING
   │
   ▼
PR_CREATED
   │
   ▼
CI_RUNNING
   │
   ├──── FAIL ────> REWORK
   │                 │
   │                 └──> RUNNING
   │
   ▼
CODEX_REVIEW
   │
   ├──── FAIL ────> REWORK
   │
   ▼
COMPLETED
```

예외 상태:

```text
TIMEOUT
FAILED
CANCELLED
NEEDS_HUMAN_REVIEW
```

---

# 8. SQLite 상태 테이블

초기에는 SQLite로 충분하다.

예시 스키마:

```sql
CREATE TABLE agent_task (
    task_id             TEXT PRIMARY KEY,
    title               TEXT NOT NULL,
    status              TEXT NOT NULL,
    executor            TEXT NOT NULL,
    risk_level          TEXT NOT NULL,

    jules_session_id    TEXT,
    branch_name         TEXT,
    pull_request_url    TEXT,

    iteration_count     INTEGER DEFAULT 0,

    created_at          TIMESTAMP NOT NULL,
    dispatched_at       TIMESTAMP,
    completed_at        TIMESTAMP,

    last_error          TEXT
);
```

추가로 이벤트 로그를 별도 관리한다.

```sql
CREATE TABLE agent_task_event (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id       TEXT NOT NULL,
    event_type    TEXT NOT NULL,
    message       TEXT,
    created_at    TIMESTAMP NOT NULL
);
```

---

# 9. Orchestrator 핵심 모듈

## 9.1 validator.py

Task Contract의 문법과 정책을 검증한다.

검증 항목:

```text
Task ID 존재 여부
Repository 존재 여부
base_branch 존재 여부
allowed_paths 존재 여부
allowed / denied path 충돌 여부
Acceptance Criteria 존재 여부
Risk Level 유효성
max_iterations 범위
Timeout 범위
```

검증 실패 시:

```text
status = FAILED_VALIDATION
Jules 호출 금지
```

---

## 9.2 jules_client.py

Jules API 호출만 담당한다.

역할:

```text
create_session()
get_session()
approve_plan()
send_message()
cancel_session()
get_outputs()
```

중요 원칙:

**비즈니스 판단을 넣지 않는다.**

예:

```python
class JulesClient:

    async def create_session(self, task):
        ...

    async def get_session(self, session_id):
        ...

    async def approve_plan(self, session_id):
        ...
```

---

# 10. Prompt Builder

Task Contract를 Jules가 읽기 좋은 Prompt로 변환한다.

예:

```text
You are executing TASK-0231.

Read and follow:
- AGENTS.md
- docs/architecture/order.md
- docs/adr/ADR-012-outbox.md

Objective
---------
CONFIRMED 상태의 주문을 취소할 수 있도록 주문 취소 API를 구현한다.

Requirements
------------
1. CONFIRMED 상태의 주문만 취소 가능하다.
2. CANCELLED 상태인 경우 HTTP 409를 반환한다.
3. 재고 복원 이벤트를 생성한다.
4. Outbox Pattern을 사용한다.

Allowed Paths
-------------
- src/order/**
- src/inventory/event/**
- tests/order/**

Denied Paths
------------
- src/security/**
- infra/**
- .github/**
- db/migration/**

Acceptance Criteria
-------------------
- Existing tests pass.
- Add unit tests.
- Add integration tests.
- API response schema must not change.
- Build must succeed.

Do not make changes outside the declared scope.
```

Prompt 자체는 `.agent/results/TASK-0231-prompt.txt`에 보관해 감사 추적이 가능하도록 한다.

---

# 11. Codex와 Orchestrator 연결 방식

초기에는 가장 단순한 **파일 기반 Queue**를 권장한다.

Codex는:

```text
.agent/tasks/pending/TASK-0231.yaml
```

파일을 생성한다.

Orchestrator는 일정 주기로 `pending/`을 읽는다.

```text
pending/
   ↓
validate
   ↓
running/
   ↓
Jules dispatch
```

장점:

- 별도 Message Queue 불필요
- 사람이 파일로 바로 확인 가능
- Git으로 이력 추적 가능
- 디버깅 용이
- Codex가 쉽게 생성 가능

초기에는 Kafka, RabbitMQ, Redis Queue 등을 도입하지 않는다.

---

# 12. Codex용 작업 명령 패턴

Codex에게 다음 역할만 부여한다.

```text
1. 요구사항과 Architecture를 분석한다.
2. 하나의 PR로 완료 가능한 Work Package로 분해한다.
3. .agent/tasks/pending/ 아래에 Task YAML을 작성한다.
4. Task Contract 규격을 준수한다.
5. Orchestrator 코드를 직접 수정하지 않는다.
6. 실행은 Orchestrator에 맡긴다.
```

중요:

Codex가 Jules API Key를 직접 사용하지 않도록 한다.

---

# 13. Secret 관리

API Key는 Repository에 저장하지 않는다.

예:

```text
.env
```

```bash
JULES_API_KEY=...
GITHUB_TOKEN=...
```

`.gitignore`:

```text
.env
orchestrator.db
.agent/logs/
```

운영에서는:

```text
GitHub Actions Secret
Vault
AWS Secrets Manager
GCP Secret Manager
```

등으로 이전할 수 있다.

---

# 14. 권한 분리

권장 권한 구조:

```text
Codex
 ├─ Repository Read/Write
 ├─ Task Contract 생성
 └─ Review

Orchestrator
 ├─ Jules API 호출
 ├─ GitHub API 조회
 └─ State DB 접근

Jules
 ├─ Task Branch 수정
 ├─ Commit
 └─ PR 생성

GitHub Actions
 └─ Build/Test/Security Validation
```

특히 Codex에 Jules API Credential까지 직접 제공하지 않는 것이 좋다.

---

# 15. Branch 전략

Jules 작업은 항상 별도 Branch에서 수행한다.

규칙:

```text
agent/{task-id}
```

예:

```text
agent/TASK-0231
```

Base Branch:

```text
develop
```

금지:

```text
main 직접 수정
release 직접 수정
production branch 직접 수정
```

---

# 16. PR 규칙

PR 제목:

```text
[TASK-0231] 주문 취소 API 구현
```

PR 설명에는 자동으로 다음 정보를 포함한다.

```text
Task ID
Requirement References
Architecture References
Jules Session ID
Changed Files
Tests Executed
Acceptance Criteria
Known Issues
```

---

# 17. CI 검증

Jules 작업 완료를 곧바로 Codex Review로 보내지 않는다.

먼저 Deterministic Validation을 통과시킨다.

권장 순서:

```text
Compile
  ↓
Unit Test
  ↓
Integration Test
  ↓
Lint / Formatter
  ↓
Static Analysis
  ↓
Security Scan
  ↓
Architecture Test
```

CI가 PASS한 경우에만 Codex Review로 이동한다.

---

# 18. Architecture Test 도입

대형 시스템에서는 단순 Unit Test만으로 부족하다.

예:

```text
Controller가 Repository를 직접 호출하지 않는지
Domain Layer가 Infrastructure Layer를 참조하지 않는지
Order Service가 Payment Repository에 직접 접근하지 않는지
```

Java라면 ArchUnit 같은 도구를 사용하는 것을 권장한다.

AI Agent의 Architecture Drift를 막는 데 특히 효과적이다.

---

# 19. Codex Review 단계

Codex는 단순 Diff Review만 하지 않는다.

다음 5가지 기준으로 검증한다.

```text
1. Requirement Compliance
2. Architecture Compliance
3. Scope Compliance
4. Test Adequacy
5. Regression Risk
```

Codex Review 결과는 구조화한다.

예:

```yaml
review:
  task_id: TASK-0231
  result: FAIL

  issues:
    - severity: HIGH
      type: ARCHITECTURE
      description: OrderService가 InventoryService를 직접 호출함

    - severity: MEDIUM
      type: TEST
      description: CANCELLED 재호출 409 테스트 누락

  action: REWORK
```

---

# 20. 재작업 루프

Review 실패 시 Orchestrator는 새로운 Task를 만들지 않는다.

동일 Task ID의 iteration을 증가시킨다.

```text
TASK-0231
iteration 1
    ↓ FAIL
iteration 2
    ↓ FAIL
iteration 3
```

`max_iterations` 도달 시:

```text
NEEDS_HUMAN_REVIEW
```

상태로 종료한다.

기본 권장값:

```text
max_iterations = 3
```

---

# 21. Timeout 정책

에이전트가 무한히 실행되지 않도록 제한한다.

예:

| Risk | Timeout |
|---|---:|
| LOW | 30분 |
| MEDIUM | 90분 |
| HIGH | 180분 |
| CRITICAL | 자동 실행 금지 |

Timeout 발생 시 자동 재실행하지 않는다.

```text
TIMEOUT
   ↓
Codex 분석
   ↓
Task 재분해
```

를 기본으로 한다.

---

# 22. Risk Level 정책

## LOW

예:

```text
테스트 추가
문서 수정
단순 DTO 추가
```

정책:

```text
자동 Dispatch
자동 Jules 실행
자동 CI
Codex Review
```

---

## MEDIUM

예:

```text
CRUD
일반 Business Logic
Controller / Service 수정
```

정책:

```text
Jules Plan 필요
Codex Plan Review
실행
CI
Codex Review
```

---

## HIGH

예:

```text
Transaction
DB Schema
Event Architecture
Shared Framework
```

정책:

```text
Codex Plan
Human Approval
Jules 실행
CI
Codex Review
Human Merge
```

---

## CRITICAL

예:

```text
Security
Authentication
Authorization
Payment
Production Infrastructure
Secret 관리
```

초기 시스템에서는 자동 Jules Dispatch를 금지한다.

---

# 23. 감사 로그

모든 단계는 로그로 남긴다.

예:

```text
2026-09-10 10:01 TASK-0231 CREATED
2026-09-10 10:01 TASK-0231 VALIDATED
2026-09-10 10:02 TASK-0231 DISPATCHED session=abc123
2026-09-10 10:05 TASK-0231 PLAN_RECEIVED
2026-09-10 10:08 TASK-0231 PLAN_APPROVED
2026-09-10 10:35 TASK-0231 PR_CREATED #481
2026-09-10 10:41 TASK-0231 CI_PASS
2026-09-10 10:55 TASK-0231 CODEX_REVIEW_PASS
2026-09-10 10:56 TASK-0231 COMPLETED
```

이 로그는 향후 Agent 성능 평가에도 사용할 수 있다.

---

# 24. 실패 처리 정책

## Jules API 오류

```text
HTTP 5xx
429 Rate Limit
Network Timeout
```

정책:

```text
Exponential Backoff
최대 3회
```

예:

```text
1분
5분
15분
```

---

## Task 자체 실패

코드 구현 실패와 API 오류를 구분한다.

```text
TECHNICAL_RETRY
```

과

```text
IMPLEMENTATION_REWORK
```

를 별도 관리한다.

---

# 25. 동시 실행 제한

초기에는 병렬 Worker를 많이 사용하지 않는다.

권장:

```text
MAX_CONCURRENT_JULES_TASKS=2
```

안정화 후:

```text
2
→ 3
→ 5
```

단계적으로 확장한다.

동일 모듈 수정 Task는 동시에 실행하지 않는다.

예:

```text
TASK-A → src/order/**
TASK-B → src/order/**
```

이면 하나만 실행한다.

---

# 26. Scope Lock

Orchestrator는 실행 전에 다른 Running Task와 Scope가 겹치는지 검사한다.

개념:

```text
TASK-A
allowed_paths:
src/order/**

TASK-B
allowed_paths:
src/payment/**

→ 병렬 실행 가능
```

```text
TASK-A
src/order/**

TASK-C
src/order/cancel/**

→ Scope 충돌
→ Queue 대기
```

MVP에서는 단순 경로 prefix 비교로 구현한다.

---

# 27. Orchestrator Main Loop

MVP의 핵심 루프는 매우 단순하게 유지한다.

Pseudo Code:

```python
while True:

    tasks = load_pending_tasks()

    for task in tasks:

        validate(task)

        if scope_locked(task):
            continue

        if concurrency_limit_reached():
            continue

        session = jules.create_session(task)

        save_session(task, session)

        move_task_to_running(task)

    monitor_running_tasks()

    sleep(30)
```

이 정도가 초기 Orchestrator의 핵심이다.

---

# 28. Phase별 구현 계획

## Phase 0 — 준비

목표:

```text
Agent 작업 규칙 표준화
```

작업:

- AGENTS.md 작성
- ARCHITECTURE.md 정리
- Coding Rules 정리
- Task Contract v1.0 확정
- Risk Level 정의

완료 기준:

```text
Codex가 Task YAML을 일관되게 생성할 수 있음
```

---

# 29. Phase 1 — 최소 Orchestrator MVP

목표:

```text
Codex → Task File → Jules
```

구현:

```text
Task YAML Loader
Pydantic Validator
Prompt Builder
Jules REST Client
SQLite State Store
File Queue
```

지원 상태:

```text
CREATED
VALIDATED
DISPATCHED
RUNNING
COMPLETED
FAILED
```

아직 구현하지 않는 것:

```text
자동 Codex Review
Plan Approval 자동화
GitHub CI 연동
Retry Loop
Web UI
```

완료 기준:

```text
Codex가 YAML 생성
→ Orchestrator 자동 감지
→ Jules Session 자동 생성
```

사람 Copy/Paste 제거.

---

# 30. Phase 2 — GitHub 연동

목표:

```text
Jules 결과를 GitHub PR까지 추적
```

구현:

```text
GitHub API Client
PR 탐지
Branch 추적
CI 상태 조회
```

상태 추가:

```text
PR_CREATED
CI_RUNNING
CI_PASS
CI_FAILED
```

완료 기준:

```text
Task
→ Jules
→ PR
→ CI 결과
```

전체 상태를 Orchestrator가 자동 추적.

---

# 31. Phase 3 — Codex Review 자동 연결

목표:

```text
CI PASS 후 Codex Review 자동 요청
```

Codex Review용 Input을 자동 생성한다.

예:

```text
.agent/review/TASK-0231.yaml
```

내용:

```yaml
task_id: TASK-0231
pull_request: 481
requirement_refs:
  - REQ-ORDER-017
architecture_refs:
  - ADR-012
review_checklist:
  - requirement
  - architecture
  - scope
  - tests
  - regression
```

Codex가 Review 결과 파일 생성:

```text
.agent/results/TASK-0231-review.yaml
```

완료 기준:

```text
CI PASS
→ Codex Review Queue
→ Review Result
```

자동 연결.

---

# 32. Phase 4 — Rework Loop

목표:

```text
Codex FAIL → Jules 수정
```

구현:

```text
Review Result Parser
Rework Prompt Builder
Iteration Counter
max_iterations
```

흐름:

```text
Codex FAIL
   ↓
Orchestrator
   ↓
Jules Session에 Review Feedback 전달
   ↓
Jules 수정
   ↓
CI
   ↓
Codex Review
```

완료 기준:

```text
최대 3회 자동 수정 Loop
```

---

# 33. Phase 5 — Plan Approval Loop

목표:

MEDIUM 이상 Risk Task에서:

```text
Jules Plan
   ↓
Codex Review
   ↓
Approve / Reject
```

을 자동화한다.

완료 기준:

```text
Plan Approval 없이 코드 수정이 시작되지 않음
```

---

# 34. Phase 6 — 운영 안정화

추가 기능:

```text
FastAPI Admin API
Task Dashboard
Metrics
Alert
PostgreSQL
Central Logging
```

이 단계 전에는 UI 개발을 하지 않는 것을 권장한다.

---

# 35. 구현 우선순위

가장 중요한 순서:

```text
1. Task Contract
2. Validator
3. Jules API Client
4. State Store
5. File Queue
6. GitHub Client
7. CI Tracking
8. Codex Review Queue
9. Rework Loop
10. Plan Approval
```

UI는 마지막이다.

---

# 36. MVP 예상 파일

최소 구현 파일:

```text
orchestrator/
├── main.py
├── config.py
├── models.py
├── validator.py
├── prompt_builder.py
├── dispatcher.py
├── jules_client.py
├── monitor.py
└── state_store.py
```

약 8~10개 Python 파일이면 첫 버전을 충분히 만들 수 있다.

---

# 37. 설정 파일

예:

```yaml
orchestrator:
  poll_interval_seconds: 30
  max_concurrent_tasks: 2

jules:
  timeout_seconds: 30
  api_retry_count: 3

execution:
  default_max_iterations: 3
  default_timeout_minutes: 90

review:
  codex_required: true
  auto_merge: false
```

---

# 38. 절대 하지 않을 것

초기 버전에서는 다음을 구현하지 않는다.

```text
AI가 Task 우선순위 자동 결정
AI가 Requirement 자동 변경
AI가 Architecture Rule 자동 변경
자동 Production Deploy
자동 main Merge
무제한 Agent Retry
Agent가 Orchestrator 설정 수정
```

이것들이 Orchestrator를 "얇게" 유지하는 핵심이다.

---

# 39. 가장 중요한 Guardrail

다음 규칙은 코드 수준에서 강제한다.

## Rule 1

Task Contract 없는 Agent 실행 금지.

## Rule 2

Task ID 없는 PR 금지.

## Rule 3

allowed_paths 밖 변경 시 Review FAIL.

## Rule 4

max_iterations 초과 시 자동 중단.

## Rule 5

CI FAIL 상태에서 Codex 최종 Review 금지.

## Rule 6

Codex Review PASS 없이 자동 Merge 금지.

## Rule 7

HIGH 이상 Risk는 Human Gate 적용.

## Rule 8

Orchestrator는 Requirement와 Architecture를 수정하지 않는다.

---

# 40. 운영 지표

향후 다음 Metrics를 수집한다.

```text
Task 성공률
First Attempt 성공률
평균 Iteration 수
평균 Jules 실행시간
CI 실패율
Codex Review 실패율
Human Escalation 비율
Task별 Token/API 비용
Agent별 성공률
```

예:

```text
Agent Task Success Rate      87%
First Attempt Success        68%
Average Iterations           1.4
Codex Review Reject Rate     21%
Human Escalation              6%
```

이 데이터를 기반으로 자동화 수준을 확대한다.

---

# 41. 도입 단계 권장안

실제 프로젝트에서는 다음처럼 점진적으로 적용한다.

### Stage 1

```text
LOW Risk Task만 자동화
```

2~4주간 안정성 확인.

### Stage 2

```text
MEDIUM Risk Task 추가
+ Plan Approval
```

### Stage 3

```text
병렬 Jules Worker 2~3개
```

### Stage 4

```text
자동 Rework Loop
```

### Stage 5

```text
HIGH Risk 일부 자동화
```

CRITICAL 영역은 계속 Human Gate 유지.

---

# 42. 최종 목표 Architecture

```text
                           USER
                            │
                            ▼
                     ┌───────────────┐
                     │     Codex     │
                     │ Master Agent  │
                     └───────┬───────┘
                             │
                       Task Contract
                             │
                             ▼
                  ┌────────────────────┐
                  │ Thin Orchestrator  │
                  │                    │
                  │ Validate           │
                  │ Dispatch           │
                  │ Track              │
                  │ Retry              │
                  │ Audit              │
                  └─────────┬──────────┘
                            │
                     Jules REST API
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
          Jules #1       Jules #2       Jules #3
             │              │              │
             └──────────────┼──────────────┘
                            │
                         GitHub
                            │
                            ▼
                    GitHub Actions
                            │
                            ▼
                         Codex
                    Independent Review
                            │
                    ┌───────┴────────┐
                    │                │
                  PASS             FAIL
                    │                │
                  Merge        Rework Loop
```

---

# 43. 최종 판단

이 구조에서 핵심은 Orchestrator 자체를 또 하나의 "AI Agent"로 만들지 않는 것이다.

Orchestrator는 다음 네 가지 역할이면 충분하다.

```text
ROUTE
TRACK
CONTROL
AUDIT
```

즉:

```text
Codex = 판단
Jules = 실행
CI    = 기계적 검증
Codex = 최종 AI 검증
Human = 고위험 의사결정
```

으로 역할을 명확히 분리한다.

이렇게 구현하면 현재 사람이 수행하는:

```text
Prompt Copy
Prompt Paste
Jules 실행 확인
결과 Copy
Codex 전달
```

과정을 대부분 제거하면서도, Agent 간 직접 연결에서 발생할 수 있는 과도한 자율성은 억제할 수 있다.

---

# 44. 바로 시작할 첫 번째 개발 Sprint

첫 Sprint에서는 아래 7개 항목만 구현한다.

```text
[01] Task Contract v1.0 정의

[02] Pydantic Task Model 구현

[03] pending/ File Queue 구현

[04] Jules REST API Client 구현

[05] SQLite Task State 구현

[06] Dispatcher / Monitor 구현

[07] Codex → Task YAML → Jules 자동 실행 End-to-End 테스트
```

첫 Sprint 완료 기준은 단 하나다.

> **Codex가 `.agent/tasks/pending/TASK-XXXX.yaml` 파일을 생성하면 사람의 Copy/Paste 없이 Jules 작업이 자동 시작된다.**

이 지점까지 먼저 완성한 후 GitHub PR 추적, CI, Codex Review 자동화를 순차적으로 추가하는 것이 가장 안전하고 실용적인 구현 순서다.
