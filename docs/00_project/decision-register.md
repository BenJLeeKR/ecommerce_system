# 결정 레지스터 (Decision Register)

- 상태: Draft
- 최초 작성일: 2026-09-19 (KST)
- 근거 분석 문서: `docs/04_analysis/AN-0006-2026-09-10-sensitive-domain-policy-decision-options.md`, `docs/04_analysis/AN-0007-2026-09-19-user-decision-and-document-alignment-inventory.md`
- 관련 정합화 작업일지: `docs/05_worklog/WL-0014-2026-09-10-approved-baseline-alignment.md`, `docs/05_worklog/WL-0019-2026-09-10-sensitive-policy-design-alignment.md`, `docs/05_worklog/WL-0024-2026-09-19-user-decision-inventory.md`, `docs/05_worklog/WL-0025-2026-09-19-decision-register-foundation.md`

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|---|---|---|
| 2026-09-19 | v0.1 | 최초 작성: 승인 완료 항목 및 미결(사용자 결정 대기) 항목 인벤토리 이관 및 분리 관리 기반 마련 (Draft) |
| 2026-09-19 | v0.2 | 결정 레지스터 표 보완: 추적 칼럼(결정 ID, 상태, 승인일, 내용, 근거, 영향·반영 문서, 재검토/후속) 세분화 반영 |

## 1. 개요 및 목적
본 문서는 프로젝트 진행 과정에서 의사결정권자(사용자)의 승인을 거쳐 확정된 **승인 완료 결정 사항**과, 향후 의사결정이 필요한 **미결(사용자 결정 대기) 항목**을 단일 문서에서 명확히 분리하여 추적·관리하기 위한 결정 레지스터(Decision Register) 초안이다.

본 문서는 `AN-0006` 및 `AN-0007` 분석 문서의 결과를 바탕으로 작성되었으며, 임의의 신규 정책 수립이나 미결 항목의 승인 확정 전환 없이 기존 승인 상태만을 보존한다.

---

## 2. 승인 완료 결정 레지스터

### 2.1. 핵심 기술 스택 및 DB 기본 규정

| 결정 ID | 결정 상태 | 사용자 승인일 (KST) | 결정 내용 | 근거 문서 | 영향·반영 문서 | 재검토 조건 또는 후속 처리 |
|---|---|---|---|---|---|---|
| DEC-001 | Approved | 기록 미확인 | Next.js (Frontend), NestJS + Prisma (Backend), TypeScript, PostgreSQL | `docs/04_analysis/AN-0007-2026-09-19-user-decision-and-document-alignment-inventory.md` | `docs/00_project/tech-stack-decision.md`, `docs/02_design/01_architecture/architecture-overview.md` | 아키텍처 재검토 요구 또는 플랫폼 대규모 전환 시 사용자 재승인 |
| DEC-002 | Approved | 기록 미확인 | 접두어 없는 복수형 소문자 뱀표기법 (`plural snake_case`, 예: `users`, `orders`, `inventory`) | `docs/04_analysis/AN-0007-2026-09-19-user-decision-and-document-alignment-inventory.md` | `docs/02_design/04_database/naming-conventions.md`, `docs/02_design/04_database/database-design.md` | 신규 스키마 확장 또는 DB 이관 시 표준 명명 규칙 준수 재검증 |
| DEC-003 | Approved | 기록 미확인 | 공용 PostgreSQL 인스턴스 내 프로젝트 전용 DB 구축 및 전용 최소 권한 계정 사용 | `docs/04_analysis/AN-0007-2026-09-19-user-decision-and-document-alignment-inventory.md` | `docs/02_design/01_architecture/architecture-overview.md`, `docs/02_design/04_database/database-design.md` | 멀티테넌시 도입 또는 인프라 격리 수준 변경 요구 시 |

### 2.2. 민감 도메인 핵심 정책 (8건)

| 결정 ID | 결정 상태 | 사용자 승인일 (KST) | 결정 내용 | 근거 문서 | 영향·반영 문서 | 재검토 조건 또는 후속 처리 |
|---|---|---|---|---|---|---|
| DEC-004 | Approved | 2026-09-10 | 재고 예약 TTL 15분 (`Asia/Seoul` 기준, UTC로 DB 저장) | `docs/04_analysis/AN-0006-2026-09-10-sensitive-domain-policy-decision-options.md` | `docs/02_design/01_architecture/architecture-overview.md`, `docs/02_design/04_database/database-design.md` | 오버셀링 비율 급증 또는 결제 이탈률 변화 시 정책 재검토 |
| DEC-005 | Approved | 2026-09-10 | 조건부 원자 갱신 (`UPDATE inventory SET quantity = quantity - X WHERE quantity >= X`) 재고 동시성 제어 | `docs/04_analysis/AN-0006-2026-09-10-sensitive-domain-policy-decision-options.md` | `docs/02_design/01_architecture/architecture-overview.md`, `docs/02_design/04_database/database-design.md` | DB 트래픽 병목 심화 또는 분산 락(Redis 등) 도입 검토 시 |
| DEC-006 | Approved | 2026-09-10 | PG 결제 호출은 DB 트랜잭션 외부 수행. [주문 생성 + 재고 예약] 1개 트랜잭션, [PG 콜백 처리 + 결제 상태 갱신 + 재고 확정] 1개 트랜잭션 분리 | `docs/04_analysis/AN-0006-2026-09-10-sensitive-domain-policy-decision-options.md` | `docs/02_design/01_architecture/architecture-overview.md`, `docs/02_design/04_database/database-design.md` | 분산 트랜잭션 요구 또는 결제 흐름 전면 개편 시 |
| DEC-007 | Approved | 2026-09-10 | 재고 만료 스케줄러 1분 주기 실행 | `docs/04_analysis/AN-0006-2026-09-10-sensitive-domain-policy-decision-options.md` | `docs/02_design/01_architecture/architecture-overview.md` | DB 부하 과다 발생 또는 스케줄러 정밀도 조정 요구 시 |
| DEC-008 | Approved | 2026-09-10 | 결제 시도별 고유 멱등키(`idempotency_key`) + 상태전이 조건(`REQUESTED`) 결합 복합 결제 PG 멱등성 정책 | `docs/04_analysis/AN-0006-2026-09-10-sensitive-domain-policy-decision-options.md` | `docs/02_design/01_architecture/architecture-overview.md`, `docs/02_design/04_database/database-design.md` | PG사 연동 규격 변경 또는 중복 결제 오류 발생 시 |
| DEC-009 | Approved | 2026-09-10 | `pg_transaction_id`에 Unique 제약 부여 | `docs/04_analysis/AN-0006-2026-09-10-sensitive-domain-policy-decision-options.md` | `docs/02_design/04_database/database-design.md` | 다중 PG사 도입 또는 거래 식별자 구조 변경 시 |
| DEC-010 | Approved | 2026-09-10 | 지연/역순 등 예외 콜백 수신 시 모니터링 알림(민감정보 제외) 후 운영팀 수동 대사 처리 연계 | `docs/04_analysis/AN-0006-2026-09-10-sensitive-domain-policy-decision-options.md` | `docs/02_design/01_architecture/architecture-overview.md` | 자동 대사 시스템 도입 요구 또는 이상 콜백 빈도 급증 시 |
| DEC-011 | Approved | 2026-09-10 | 동일 주문 결제 실패 3회 누적 시 재결제 차단 및 재고 복구 | `docs/04_analysis/AN-0006-2026-09-10-sensitive-domain-policy-decision-options.md` | `docs/02_design/01_architecture/architecture-overview.md`, `docs/02_design/02_domain/domain-model.md` | 결제 실패율 모니터링 결과에 따른 시도 횟수 조정 요구 시 |

### 2.3. 승인된 초기 인프라 기준

| 결정 ID | 결정 상태 | 사용자 승인일 (KST) | 결정 내용 | 근거 문서 | 영향·반영 문서 | 재검토 조건 또는 후속 처리 |
|---|---|---|---|---|---|---|
| DEC-012 | Approved | 2026-09-10 | 매일 03:00 KST 전체 자동 백업, 일간 31개, 월간 12개 보존 | `docs/04_analysis/AN-0006-2026-09-10-sensitive-domain-policy-decision-options.md` | `docs/02_design/01_architecture/architecture-overview.md` | 백업 용량 초과 또는 컴플라이언스 기준 변경 시 |
| DEC-013 | Approved | 2026-09-10 | RPO 24시간, RTO 4시간 목표 설정 | `docs/04_analysis/AN-0006-2026-09-10-sensitive-domain-policy-decision-options.md` | `docs/02_design/01_architecture/architecture-overview.md` | 서비스 가용성 SLA 격상 요구 시 |
| DEC-014 | Approved | 2026-09-10 | 운영 담당자가 복구 및 장애 대응 책임을 맡으며 별도 비상 연락망 미두음. 전용 DB 생성 후 최초 복구 테스트 수행 | `docs/04_analysis/AN-0006-2026-09-10-sensitive-domain-policy-decision-options.md` | `docs/02_design/01_architecture/architecture-overview.md` | 전용 DB 구축 완료 시 최초 복구 테스트 수행 및 결과 기록 |

---

## 3. 미결 (사용자 결정 대기) 레지스터

아래 항목들은 사용자 승인이 완료되지 않은 미결 상태이며, 임의로 결정하거나 반영하지 않고 현 상태를 보존한다.

| 결정 ID | 결정 상태 | 사용자 승인일 (KST) | 결정 내용 (미결 항목명) | 근거 문서 | 영향·반영 문서 | 재검토 조건 또는 후속 처리 |
|---|---|---|---|---|---|---|
| PEND-001 | Pending | 해당 없음 | Primary Key 채택 방식 (UUID vs BigInt Auto-increment) | `docs/04_analysis/AN-0007-2026-09-19-user-decision-and-document-alignment-inventory.md` | `docs/02_design/04_database/database-design.md` | 사용자 결정 후 새 Task Contract·승인·PR로 반영 |
| PEND-002 | Pending | 해당 없음 | Enum 데이터 타입 처리 방식 (DB Enum vs String/Varchar) | `docs/04_analysis/AN-0007-2026-09-19-user-decision-and-document-alignment-inventory.md` | `docs/02_design/04_database/database-design.md` | 사용자 결정 후 새 Task Contract·승인·PR로 반영 |
| PEND-003 | Pending | 해당 없음 | 토큰 만료 시간 및 로그인 실패 잠금 임계값 | `docs/04_analysis/AN-0007-2026-09-19-user-decision-and-document-alignment-inventory.md` | `docs/02_design/01_architecture/architecture-overview.md`, `docs/02_design/03_api/api-list.md` | 사용자 결정 후 새 Task Contract·승인·PR로 반영 |
| PEND-004 | Pending | 해당 없음 | API Rate Limiting 및 비밀번호 재설정 횟수 제한 | `docs/04_analysis/AN-0007-2026-09-19-user-decision-and-document-alignment-inventory.md` | `docs/02_design/01_architecture/architecture-overview.md`, `docs/02_design/03_api/api-list.md` | 사용자 결정 후 새 Task Contract·승인·PR로 반영 |
| PEND-005 | Pending | 해당 없음 | 카테고리 삭제 시 소속 상품 처리 방안 | `docs/04_analysis/AN-0007-2026-09-19-user-decision-and-document-alignment-inventory.md` | `docs/02_design/02_domain/domain-model.md` | 사용자 결정 후 새 Task Contract·승인·PR로 반영 |
| PEND-006 | Pending | 해당 없음 | 회원 탈퇴 시 진행 중 주문 제한 규칙 | `docs/04_analysis/AN-0007-2026-09-19-user-decision-and-document-alignment-inventory.md` | `docs/02_design/02_domain/domain-model.md` | 사용자 결정 후 새 Task Contract·승인·PR로 반영 |
| PEND-007 | Pending | 해당 없음 | 회원당 기본 배송지 Unique 처리 방식 | `docs/04_analysis/AN-0007-2026-09-19-user-decision-and-document-alignment-inventory.md` | `docs/02_design/02_domain/domain-model.md`, `docs/02_design/04_database/database-design.md` | 사용자 결정 후 새 Task Contract·승인·PR로 반영 |
| PEND-008 | Pending | 해당 없음 | 장바구니 품절 상품 처리 UX 및 대시보드 통계 기준 | `docs/04_analysis/AN-0007-2026-09-19-user-decision-and-document-alignment-inventory.md` | `docs/02_design/05_screen/screen-spec.md` | 사용자 결정 후 새 Task Contract·승인·PR로 반영 |
| PEND-009 | Pending | 해당 없음 | 관리자 재고 조정 입력 방식 (증감 vs 절대값) | `docs/04_analysis/AN-0007-2026-09-19-user-decision-and-document-alignment-inventory.md` | `docs/02_design/05_screen/screen-spec.md` | 사용자 결정 후 새 Task Contract·승인·PR로 반영 |
| PEND-010 | Pending | 해당 없음 | 비밀번호 재설정 모달 또는 별도 화면 분리 여부 | `docs/04_analysis/AN-0005-2026-09-09-design-baseline-consistency-review.md`, `docs/04_analysis/AN-0007-2026-09-19-user-decision-and-document-alignment-inventory.md` | `docs/02_design/05_screen/screen-spec.md` | 사용자 결정 후 새 Task Contract·승인·PR로 반영 |
| PEND-011 | Pending | 해당 없음 | 관리자 회원 상세 화면 신설 여부 | `docs/04_analysis/AN-0005-2026-09-09-design-baseline-consistency-review.md`, `docs/04_analysis/AN-0007-2026-09-19-user-decision-and-document-alignment-inventory.md` | `docs/02_design/05_screen/screen-spec.md` | 사용자 결정 후 새 Task Contract·승인·PR로 반영 |
| PEND-012 | Pending | 해당 없음 | 결제 결과 화면의 폴링 방식 | `docs/04_analysis/AN-0005-2026-09-09-design-baseline-consistency-review.md`, `docs/04_analysis/AN-0007-2026-09-19-user-decision-and-document-alignment-inventory.md` | `docs/02_design/05_screen/screen-spec.md` | 사용자 결정 후 새 Task Contract·승인·PR로 반영 |

---

## 4. 향후 관리 및 정합화 계획
1. **문서 상태 관리**: 결정 레지스터 문서 상태는 `Draft`로 시작하며, 이번 작업 범위에서는 문서 상태를 변경하지 않는다.
2. **미결 사항 승인 시 반영 절차**: 향후 미결 사항(`PEND-001`~`PEND-012`)에 대해 사용자의 결정이 완료되면, `AN-0007`에서 제시된 후속 PR 분할안(DB/도메인, 인증/보안, 화면/UX)에 따라 변경 범위를 최소화하여 새 Task Contract, 승인 및 PR로 반영 절차를 진행한다.
