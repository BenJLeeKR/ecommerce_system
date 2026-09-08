# DB 명명 규칙 및 Enum 정의 (Naming Conventions)

> 상태: 초안 (Draft) — 설계 승인자(기획자) 검토 필요
> 관련 문서: `docs/02_design/01_architecture/architecture-overview.md` (5장 DB 구조), `docs/02_design/02_domain/domain-model.md`
> 목적: 실제 테이블 설계(`docs/02_design/04_database/database-design.md`, 다음 단계)에 들어가기 전에, 모든 테이블/컬럼/상태값에 **일관되게 적용할 규칙**을 먼저 확정한다. 이 문서 확정 후에는 모든 테이블 설계가 이 규칙을 예외 없이 따른다.

## 이번에 확정한 결정

| 항목 | 결정 |
|---|---|
| 테이블명 표기 | **복수형** (`orders`, `order_items`) — PostgreSQL/Rails 관례 |
| 도메인 접두어 사용 여부 | **미사용** — 테이블명은 접두어 없이 단순하게 (`users`, `orders`, `payments` 등). 도메인 경계는 테이블명이 아니라 문서(`architecture-overview.md`, `domain-model.md`)와 코드 규칙("ID 참조만, JOIN 금지")으로 관리 |
| PK(기본키) 타입 | **UUID** — 추측 불가능, 보안에 유리 (특히 주문/결제 ID 순번 노출 방지) |
| 상태값(Enum) 저장 방식 | **문자열(String)로 저장 + 애플리케이션 레이어에서 검증** (Postgres 네이티브 enum 타입 미사용) |

> 도메인 접두어는 검토 과정에서 한국 SI/공공기관 관례(`ORD_`, `PAY_` 등 업무코드 접두어 + 대문자 + `PK_`/`FK_`류 제약조건 명명)와 최신 서비스 기업 관례(접두어 없는 단순한 `snake_case`)를 함께 검토했다. 이 프로젝트는 Prisma·NestJS 등 후자의 생태계를 기반으로 하므로, 접두어 없는 단순한 방식으로 확정했다.

---

## 1. 테이블 명명 규칙

### 1-1. 기본 표기법

- `snake_case` + **복수형**을 사용한다. (예: `orders`, `order_items`, `product_options`)
- 두 단어 이상 조합 시 언더스코어(`_`)로 구분한다.

### 1-2. 도메인 접두어를 사용하지 않는 이유

초기 검토 단계에서는 "도메인 접두어를 테이블명에 붙이는 방식"(`order_orders`, `payment_payments` 등)을 고려했으나, 아래 이유로 **사용하지 않기로 최종 확정**했다.

- 한국 IT 업계에는 크게 두 갈래의 관례가 있다.
  1. **전통적 SI/공공기관 관례**: 업무영역 코드 접두어(`ORD_`, `PAY_` 등) + 대문자 표기 + `PK_`/`FK_`/`IDX_` 류 제약조건 명명. 주로 Oracle + MyBatis 조합에서 자리잡은 방식이다.
  2. **최신 서비스 기업/스타트업 관례**: 접두어 없는 단순한 `snake_case`, PK는 `id`, FK는 `{참조테이블}_id`. Node/Spring Boot + ORM(JPA, Prisma 등) 조합에서 널리 쓰인다.
- 이 프로젝트는 Next.js + NestJS + **Prisma**를 사용하기로 확정했으므로(2번 계열), 접두어만 1번 관례에서 가져오면 나머지(대문자 표기, `PK_`/`FK_` 명명 등)와 어울리지 않는 어중간한 혼합이 된다.
- **도메인 경계는 테이블명이 아니라 다음 두 가지로 관리한다.**
  1. 문서: `architecture-overview.md`(모듈 구조), `domain-model.md`(도메인별 정의)에 각 테이블이 어느 도메인 소속인지 명시
  2. 코드 규칙: 주문/결제/재고/검색 도메인과 관련된 FK는 ID 참조만 사용하고 DB 제약을 걸지 않으며, 도메인 간 JOIN을 하지 않는다 (2장 참고)

### 1-3. 관계(조인) 테이블

다대다 관계를 표현하는 테이블은 `{A}_{B}` 형태로 명명한다. (MVP 범위에는 해당 사례가 많지 않으며, 발생 시 이 규칙을 따른다)

---

## 2. 컬럼 명명 규칙

| 구분 | 규칙 | 예시 |
|---|---|---|
| 기본 키(PK) | 항상 `id`, **타입은 UUID** (자동증가 정수 대신 사용 — 추측 불가능, 보안에 유리) | `id` |
| 외래 키(FK, 같은 도메인 내) | `{참조테이블 단수형}_id` | `order_id`, `product_option_id` |
| 외래 키(주문/결제/재고/검색이 관련된 참조) | 동일하게 `{참조대상 단수형}_id`로 표기하되, **DB 외래키 제약(FK constraint)은 걸지 않는다** (ID 참조만, `architecture-overview.md` 5장 및 `domain-model.md` 12장 원칙). 이 네 도메인이 아닌 조합끼리는 일반 FK 제약을 사용해도 된다 | `order_items.product_option_id` (Order↔Catalog, FK 제약 없음) |
| 생성 시각 | `created_at` | `created_at` |
| 수정 시각 | `updated_at` | `updated_at` |
| 소프트 삭제 시각 (삭제 표시가 필요한 테이블만) | `deleted_at` (NULL이면 미삭제) | `deleted_at` |
| 불리언(참/거짓) | `is_` 또는 `has_` 접두어 | `is_active`, `has_option` |
| 상태값(Enum) 컬럼 | `status` (테이블에 상태가 하나뿐일 때) 또는 `{대상}_status` (여러 상태가 있을 때) | `status`, `payment_status` |
| 금액 | `_amount` 접미사, **정수(원 단위)로 저장** (소수점 오차 방지) | `total_amount`, `discount_amount` |
| 수량 | `_quantity` 또는 `_count` | `available_quantity`, `reserved_quantity` |

---

## 3. Enum(상태값) 정의 규칙

### 3-1. 저장 방식

- 상태값은 Postgres 네이티브 enum 타입을 사용하지 않고, **문자열(String) 컬럼**에 저장한다.
- 이유: 네이티브 enum은 값 추가/삭제/이름변경 시 DB 마이그레이션이 까다로운 편이라, 서비스 성장 단계에서 상태값이 자주 조정될 수 있는 이번 프로젝트 특성상 **문자열 저장 + 애플리케이션 레이어 검증**이 더 유연하다.
- 대신 값의 정합성은 애플리케이션 코드(TypeScript)에서 강제한다. (Prisma 스키마의 `enum` 키워드는 네이티브 DB enum을 생성하므로 사용하지 않고, 상태 컬럼은 `String` 타입으로 선언한 뒤 주석으로 허용값을 명시한다)

### 3-2. 표기 규칙

- Enum 값은 **대문자 스네이크케이스(UPPER_SNAKE_CASE)**로 표기한다. (예: `PENDING`, `PAYMENT_FAILED`)
- `docs/02_design/02_domain/domain-model.md`에 정의된 상태값 이름을 그대로 사용한다 (새로 만들지 않음).

### 3-3. 단일 진실 공급원 (Single Source of Truth)

- 모든 Enum 값은 프론트엔드·백엔드가 공유하는 `packages/types` 안에 TypeScript 상수/유니온 타입으로 한 곳에만 정의한다.
- 백엔드(NestJS)와 프론트엔드(Next.js)는 이 공용 정의를 가져다 쓰며, 각자 임의로 같은 의미의 값을 중복 정의하지 않는다.

### 3-4. 변경 정책

- **값 추가**: 비교적 자유롭게 가능하나, 사전에 관련 도메인 문서(`domain-model.md`)를 함께 갱신한다.
- **값 삭제/이름변경**: 기존 데이터에 영향을 주므로 DB 원칙(`docs/01_governance/rules-db-migration.md`)에 따라 사전 보고 및 데이터 마이그레이션 계획을 함께 제시해야 한다.
- Claude Code는 이 문서와 `domain-model.md`에 없는 상태값을 임의로 추가하지 않는다.

### 3-5. 도메인별 Enum 목록 (현재까지 정의된 것)

| 도메인 | 컬럼 | 허용값 |
|---|---|---|
| User | status | `ACTIVE`, `DORMANT`, `WITHDRAWN` |
| Product | status | `ON_SALE`, `HIDDEN`, `DISCONTINUED` |
| ProductOption | status | `ACTIVE`, `SOLD_OUT`, `HIDDEN` |
| Order | status | `PENDING`, `PAID`, `PAYMENT_FAILED`, `PREPARING`, `SHIPPING`, `DELIVERED`, `CANCELED` |
| Payment | status | `REQUESTED`, `APPROVED`, `FAILED`, `CANCELED` |
| Inventory 예약 건 (`inventory_reservations`) | status | `HELD`, `CONFIRMED`, `RELEASED` |
| Shipment | status | `PREPARING`, `SHIPPING`, `DELIVERED` |
| AdminUser | status | `ACTIVE`, `DISABLED` |

---

## 4. Prisma 모델 ↔ 실제 DB 매핑 규칙

Prisma 스키마 파일(`schema.prisma`)은 비개발자가 봐도 읽기 쉬운 형태를 유지하고, 실제 DB에는 위 규칙(스네이크케이스, 복수형, UUID PK)이 적용되도록 매핑한다.

- Prisma 모델명: **PascalCase 단수형** (예: `model Order`) — 코드에서 읽기 쉬운 이름 유지
- 실제 테이블명: `@@map("orders")`로 매핑 (접두어 없음)
- Prisma 필드명: **camelCase** (예: `createdAt`) — 코드 관례 유지
- 실제 컬럼명: `@map("created_at")`로 매핑
- PK 필드: `id String @id @default(uuid()) @db.Uuid`
- 상태값 필드: Prisma 스키마에서도 `enum`이 아닌 `String` 타입으로 선언 (네이티브 DB enum 회피, 3-1 원칙과 동일)

이 매핑 규칙 덕분에, 코드를 보는 개발자(및 Claude Code)는 익숙한 표기(PascalCase/camelCase)를 그대로 사용하고, DB를 직접 들여다보는 사람(기획자가 DB 도구로 확인할 때 등)은 일관된 스네이크케이스 테이블/컬럼명을 보게 된다.

---

## 5. 이 규칙이 적용된 예시 (미리보기, 확정 아님)

```
orders
├── id                   (UUID)
├── user_id              (User 참조, FK 제약 없음)
├── status               (문자열: PENDING / PAID / ...)
├── total_amount
├── created_at
├── updated_at

order_items
├── id                   (UUID)
├── order_id             (같은 도메인, FK 제약 있음)
├── product_option_id    (Catalog 참조, FK 제약 없음)
├── quantity
├── unit_price_amount    (주문시점 단가 스냅샷)
├── subtotal_amount

payments
├── id                   (UUID)
├── order_id             (Order 참조, FK 제약 없음)
├── status               (문자열: REQUESTED / APPROVED / ...)
├── amount
├── pg_transaction_id
├── idempotency_key
├── requested_at
├── approved_at
```

> 위 예시는 규칙 적용 방식을 보여주기 위한 미리보기이며, 실제 테이블의 전체 컬럼 목록은 다음 단계인 `db-schema.md`에서 확정한다.

---

## 6. 승인 체크리스트

- [x] 테이블명 표기(복수형) 확정
- [x] 도메인 접두어 미사용 확정 (SI 관례 vs 서비스기업 관례 검토 결과 반영)
- [x] PK 타입(UUID) 확정
- [x] 상태값 저장 방식(문자열 + 앱 검증) 확정
- [ ] 컬럼 명명 규칙 승인
- [ ] Prisma ↔ DB 매핑 규칙 승인
- [ ] 다음 단계(`docs/02_design/04_database/database-design.md`, 전체 테이블/컬럼 설계) 진행 승인

> 승인 전까지는 초안(Draft) 상태이며, 코드는 작성하지 않는다.
