# AN-0005-2026-09-09-design-baseline-consistency-review

- 상태: In Review
- 작성일: 2026-09-09
- 연결 Backlog: BL-0002, BL-0004
- 관련 설계: docs/00_project/project-scope.md, docs/02_design/01_architecture/architecture-overview.md, docs/02_design/04_database/database-design.md, docs/02_design/04_database/naming-conventions.md

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|---|---|---|
| 2026-09-09 | v0.1 | 설계 기준선 정합성 검토 보고서 초안 작성 |

## 1. 현재 설계의 기준 문서와 우선순위
현재 설계의 기준은 `docs/01_governance/document-management-rules.md`를 포함한 **거버넌스 문서**와 `AGENTS.md`, `CLAUDE.md`가 가장 우선순위가 높습니다. 이후 `docs/00_project/project-scope.md` 등의 프로젝트 정의서와 `docs/02_design/` 하위의 아키텍처, 도메인, API, DB 설계 문서가 우선합니다. `docs/99_reference/Enterprise_ecommerce_AI_Backend_Guide.md`는 참고 가이드일 뿐 구현 범위를 강제하거나 확대하지 않습니다.

## 2. MVP 범위와 엔터프라이즈 참고 가이드의 적용/비적용 경계
- **MVP 범위 (적용)**: 단일 직영몰, 고객 회원가입/로그인, 상품 탐색, 장바구니, 주문 생성/결제(PG 샌드박스), 재고 차감, 관리자 수동 배송 상태 변경. 모듈러 모놀리스 백엔드 아키텍처.
- **엔터프라이즈 참고 가이드 (비적용)**: MSA 완전 분리, 카프카 기반 비동기 이벤트, 다중 입점사 정산, 리뷰 도메인, 마이크로서비스 전환 및 복잡한 MSA 보상 트랜잭션 등은 MVP 범위를 벗어나므로 적용하지 않습니다.

## 3. 문서 간 충돌, 누락, Draft·확인 필요 항목 목록
- **핵심 충돌 1**: `architecture-overview.md`에서는 도메인 접두어 테이블명 규칙(`order_*`, `inventory_*` 등)을 명시하고 있으나, `database-design.md`와 `naming-conventions.md`에서는 **접두어 없는 복수형 테이블명 규칙**(`orders`, `inventory` 등)을 채택하고 있어 강한 충돌이 발생합니다.
- **확인 필요 1**: 기술 스택 (안 A: Next.js + NestJS + Prisma)이 `tech-stack-decision.md`에서 권장 상태이나 최종 승인이 누락되었습니다.
- **확인 필요 2**: 공용 PostgreSQL 백업, 복구 절차 및 전용 Database에 대한 접근 권한 발급 방식이 미결정 상태입니다.
- **확인 필요 3**: 주문·결제·재고 영역에서 1) 재고 예약 유효시간(TTL), 2) 결제 반복 실패 시 제한 정책, 3) PG 콜백 멱등성 보장을 위한 락/트랜잭션 세부 처리 방안, 4) 배송 준비 중 취소 허용 여부 등 주요 민감 정책이 미결정(Draft) 상태입니다.

## 4. 사용자 결정이 필요한 항목과 가능한 선택지
1. **DB 네이밍 규칙 충돌 해소**:
   - 선택지 A: `naming-conventions.md` 기준(접두어 없음)으로 확정하고 아키텍처 문서 수정. (현재 최신 프레임워크 생태계 관행에 부합)
   - 선택지 B: `architecture-overview.md` 기준(도메인 접두어 사용)으로 확정하고 DB 설계 문서 수정.
2. **기술 스택 확정**:
   - 안 A(NestJS+Prisma)로 최종 승인 진행.
3. **민감 정책 및 DB 트랜잭션 전략 확정**:
   - 재고 TTL (예: 10분, 15분) 및 락(Lock) 전략(Optimistic vs Pessimistic) 결정.
   - PG 콜백 처리 방안 확정.

## 5. 결정 전에는 프로젝트 골격·Prisma 스키마·구현을 시작하면 안 되는 근거
위의 3번, 4번 항목들이 미결정 상태로 남아있는 한, Prisma Schema 작성 시 테이블 이름, 락 처리를 위한 필드 구성 등을 확정할 수 없습니다. 특히 재고/결제/주문 도메인은 오버셀(초과판매)이나 중복결제를 유발할 수 있는 가장 위험한 영역이므로, 락 정책 및 DB 스키마 네이밍이 완벽하게 정리된 후에야 프로젝트 골격 구축 및 실제 코딩에 돌입할 수 있습니다.

## 6. 설계 문서 갱신과 승인에 대한 권장 순서
1. **DB 네이밍 규칙 결정**: 사용자 승인을 통해 충돌 해소 후 관련 문서(아키텍처 또는 DB 설계서) 갱신.
2. **기술 스택 최종 승인**: `tech-stack-decision.md` 승인 처리.
3. **민감 도메인 정책 확정**: 재고 TTL, 결제 멱등성, 락 정책 등 승인 후 `domain-model.md`, `database-design.md` 갱신.
4. **골격 작업(BL-0002) 착수**: 모든 설계 기반이 확정된 후 Prisma Schema 및 프로젝트 셋업 시작.
