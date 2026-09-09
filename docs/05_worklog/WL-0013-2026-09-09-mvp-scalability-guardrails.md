# WL-0013-2026-09-09-mvp-scalability-guardrails

- 상태: Completed
- 작업일: 2026-09-09
- 연결 Backlog: 없음 — AN-0005 결과 기반 신규 계획
- 연결 Planning: `PL-0008`
- 연결 Analysis: `AN-0005`
- 관련 설계: `docs/02_design/01_architecture/architecture-overview.md`, `docs/02_design/04_database/database-design.md`

## 1. 목적

AN-0005-2026-09-09-design-baseline-consistency-review.md의 분석 결과를 바탕으로, 프로젝트 구현 착수 전 반드시 확립해야 할 모듈러 모놀리스 아키텍처의 가드레일을 수립한다. 확장성, 모듈 분리, 도메인 데이터 소유권 및 허용 의존성에 대한 원칙을 문서화하여 이후 설계 및 코드 구현 시 기준점으로 삼고자 한다.

## 2. 수행 내용

- **가드레일 문서 작성**: `docs/03_planning/PL-0008-2026-09-09-mvp-scalability-guardrails.md`를 신규 작성하여 모듈 경계, 분리 트리거, 데이터 소유권, 선결 조건을 명시함.
- **인덱스 추가**: `docs/03_planning/README.md` 및 `docs/05_worklog/README.md`에 새 문서 내역을 추가함.
- **사용자 승인 대기 항목 명시**: 재고 TTL, 결제 멱등성, 락(Lock) 전략, 백업 복구 절차 등 섣불리 확정하지 않아야 할 주요 항목들을 선결 조건으로 분리 작성함.

## 3. 판단 및 결정

- FK 제약 규칙은 신규로 생성하지 않고, 기존 `architecture-overview.md` 및 `database-design.md`의 규칙(분리 후보 도메인은 ID만 참조하고 FK 제약 제외)을 따르도록 가드레일에 명시함.
- MSA 전환에 대한 분리 트리거는 일반적인 트래픽/가용성 관점과, 각 핵심 도메인(주문, 재고, 결제)별 특성을 고려하여 서술함. 수치화된 임계값은 추후 관측 후 결정하도록 함.


- **사용자 승인 완료 정책 기록**: 사용자의 리뷰 피드백을 통해 다음 항목들이 확정되었음을 문서에 기록함:
  - 기술 스택: A안 (Next.js, NestJS, TypeScript, Prisma, PostgreSQL)
  - DB 명명 규칙: 접두어 없는 복수형 snake_case
  - DB 환경: 공용 PostgreSQL 내 프로젝트 전용 DB 및 최소 권한 계정
  - 리뷰 도메인: MVP 제외 및 DB 스키마 선반영 금지
- 위 항목을 제외한 재고 TTL, 락/트랜잭션 전략, PG 콜백 멱등성 보장, 백업/복구 절차만 결정 대기 항목으로 유지함.

## 4. 변경 파일

- `docs/03_planning/PL-0008-2026-09-09-mvp-scalability-guardrails.md` (신규 파일 작성)
- `docs/03_planning/README.md` (PL-0008 인덱스 추가)
- `docs/05_worklog/WL-0013-2026-09-09-mvp-scalability-guardrails.md` (본 작업 기록 신규 작성)
- `docs/05_worklog/README.md` (WL-0013 인덱스 추가)

## 5. 검증 결과

- 최신 `main` 브랜치로 Rebase 완료 및 충돌 없음 확인.
- `git diff --name-status`를 통해 정확히 4개의 파일만 생성 및 변경되었음을 검증.
- `git diff --check` 명령어를 통해 공백이나 포맷팅 오류가 없음을 확인함.

## 6. 후속 작업

- PL-0008 내 명시된 "7. 민감 영역 선결 조건 (유예 및 사용자 승인 항목)"에 대한 사용자의 명시적 의사 결정 수합.
- 확정된 의사 결정을 바탕으로 한 아키텍처 및 데이터베이스 설계 문서(`docs/02_design/` 하위) 갱신 (별도 PR/이슈).
