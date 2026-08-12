# 대형 상용 쇼핑몰 AI Agent Coding 구축 가이드

> **목표**  
> 대형 상용 쇼핑몰을 AI 에이전트 코딩 중심으로 설계·구현하되, 각 단계마다 사용자가 확인·승인하면서 빈틈없이 구축할 수 있도록 하는 실전형 개발 가이드.

---

## 1. 핵심 원칙

대형 상용 쇼핑몰을 AI 에이전트 코딩으로 구축할 때 가장 중요한 것은 **AI가 코드를 많이 작성하는 것**이 아니라, **AI가 잘못된 방향으로 대량의 코드를 만들기 전에 설계·검증·승인 지점을 촘촘하게 만드는 것**이다.

특히 사용자가 모든 코드를 직접 리뷰하기 어려운 경우에는 코드 리뷰보다 아래 요소를 사람이 확인하는 구조가 훨씬 중요하다.

- 요구사항
- 화면
- 데이터
- API
- 업무 규칙
- 테스트 결과
- 보안
- 운영 기준

권장 방식은 다음과 같다.

```text
AI 설계
↓
사람 확인
↓
AI 보완
↓
사람 승인
↓
AI 구현
↓
AI 테스트
↓
다른 AI 리뷰
↓
자동 검증
↓
사람 결과 확인
↓
다음 기능
```

---

# 2. 전체 개발 프로세스

대형 쇼핑몰은 다음 **17단계 Gate 방식**으로 관리하는 것이 좋다.

1. 사업 목표와 시스템 범위 정의
2. 도메인 및 업무 기능 정의
3. 요구사항 명세
4. 사용자·권한·업무 시나리오 정의
5. 화면 IA 및 화면설계
6. 비기능 요구사항 정의
7. 전체 시스템 아키텍처 설계
8. 데이터 모델 설계
9. API 및 이벤트 설계
10. 보안·개인정보·감사 설계
11. 개발 표준과 AI Agent 규칙 정의
12. Walking Skeleton 구축
13. MVP 개발
14. 도메인별 본개발
15. 통합·회귀·성능·보안 테스트
16. 운영·배포·장애대응 체계 구축
17. Production 오픈 및 지속 개선

핵심은 **각 단계가 끝날 때 사용자가 승인하기 전에는 다음 단계로 넘어가지 않는 것**이다.

```text
요구사항 승인
→ 화면 승인
→ DB 승인
→ API 승인
→ 아키텍처 승인
→ 개발
```

---

# 3. 기술 선택보다 먼저 해야 할 일

처음부터 다음처럼 시작하면 안 된다.

```text
Next.js + FastAPI + PostgreSQL로 쇼핑몰 만들어줘.
```

대형 시스템에서는 기술보다 먼저 **Project Charter**를 정의해야 한다.

예시:

| 항목 | 예 |
|---|---|
| 시스템 | B2C 종합 쇼핑몰 |
| 목표 사용자 | 일반 고객 / 판매자 / CS / MD / 관리자 |
| 예상 회원 | 500만 |
| DAU | 30만 |
| Peak TPS | 2,000 TPS |
| 상품 수 | 300만 SKU |
| 주문 | 일평균 10만 |
| 결제 | 카드 / 계좌 / 간편결제 |
| 판매형태 | 직매입 + 입점 |
| 채널 | PC Web / Mobile Web / App |
| 해외 | 1차 제외 |
| 다국어 | 1차 제외 |
| 배송 | 택배 중심 |
| 정산 | 판매자 월/주기 정산 |
| 쿠폰 | 상품/장바구니/회원 쿠폰 |
| 운영 목표 | 24×365 |
| 가용성 | 예: 99.95% |

추천 문서 구조:

```text
/docs
  /00_project
      PROJECT_CHARTER.md
      SCOPE.md
      GLOSSARY.md
```

---

# 4. Scope 확정

AI 프로젝트에서 Scope가 명확하지 않으면 AI가 기능을 계속 확장한다.

다음 세 가지를 반드시 구분한다.

| 구분 | 의미 |
|---|---|
| In Scope | 반드시 구현 |
| Out of Scope | 이번 프로젝트에서 제외 |
| Future Scope | 이후 고도화 |

초기 Scope 예시:

```text
회원
상품
전시
검색
장바구니
주문
결제
배송
취소
반품
교환
쿠폰
포인트
리뷰
고객센터
판매자
정산
관리자
```

---

# 5. Domain Map 작성

쇼핑몰을 하나의 거대한 프로그램으로 보지 말고 **업무 도메인별 시스템으로 분해**해야 한다.

| Domain | 주요 기능 |
|---|---|
| IAM | 로그인, 인증, 권한 |
| Member | 회원 |
| Seller | 판매자 |
| Catalog | 상품 |
| Pricing | 가격 |
| Promotion | 쿠폰/프로모션 |
| Inventory | 재고 |
| Exhibition | 기획전/전시 |
| Search | 검색 |
| Cart | 장바구니 |
| Order | 주문 |
| Payment | 결제 |
| Delivery | 배송 |
| Claim | 취소/반품/교환 |
| Point | 포인트 |
| Review | 리뷰 |
| Settlement | 정산 |
| CS | 고객상담 |
| Notification | Email/SMS/Push |
| Admin | 운영관리 |

AI에게 특히 다음을 검증하게 한다.

- 상품 판매가격은 Catalog가 관리하는가, Pricing이 관리하는가?
- 주문 당시 가격은 Pricing을 다시 조회하는가, Order에 Snapshot으로 남기는가?
- 재고 차감은 Order가 하는가, Inventory가 하는가?
- 쿠폰 계산은 Promotion이 하는가, Order가 하는가?
- 결제 성공 이후 주문 저장 실패 시 누가 보상처리하는가?

---

# 6. Business Flow 설계

화면보다 먼저 업무 흐름을 만든다.

정상 주문 예:

```text
상품조회
   ↓
옵션선택
   ↓
장바구니
   ↓
주문서 생성
   ↓
가격 재검증
   ↓
쿠폰 검증
   ↓
재고 확보
   ↓
결제 요청
   ↓
결제 승인
   ↓
주문 확정
   ↓
재고 확정
   ↓
판매자 주문 전달
   ↓
배송 준비
   ↓
출고
   ↓
배송 완료
   ↓
구매 확정
   ↓
정산
```

실패 흐름도 함께 정의한다.

```text
결제 승인 성공
→ 주문 DB 저장 실패

주문 성공
→ 재고 차감 실패

카드 승인 성공
→ PG 응답 Timeout

동일 결제 Callback 2회 수신

동일 주문 버튼 2회 클릭
```

AI에게 반드시 **Happy Path + Exception Path**를 모두 설계하게 한다.

---

# 7. Use Case 정의

예시:

```text
UC-ORD-001 주문 생성
UC-ORD-002 주문 조회
UC-ORD-003 주문 취소
UC-ORD-004 부분 취소
UC-ORD-005 주문 실패 복구
```

각 Use Case에는 최소 다음 항목을 포함한다.

| 항목 | 내용 |
|---|---|
| Actor | 고객 |
| Trigger | 결제 버튼 클릭 |
| Preconditions | 로그인, 장바구니 존재 |
| Main Flow | 정상 주문 |
| Alternative Flow | 품절 등 |
| Exception | PG Timeout |
| Business Rule | 할인 계산 |
| Input | 주문상품 |
| Output | 주문번호 |
| Transaction | 주문 생성 |
| Audit | 주문 생성 기록 |
| Permission | 고객 본인 |
| Acceptance Criteria | 완료 판단 기준 |

---

# 8. Business Rule 별도 관리

예:

```text
BR-ORD-001
주문금액은 상품금액 + 배송비 - 상품할인 - 주문할인 - 포인트로 계산한다.

BR-ORD-002
포인트 사용액은 결제금액을 초과할 수 없다.

BR-ORD-003
품절 상품은 주문할 수 없다.

BR-ORD-004
결제 승인 후 주문 생성 실패 시 결제를 자동 취소한다.
```

추천 구조:

```text
/docs/01_requirements
    REQUIREMENTS.md
    BUSINESS_RULES.md
    USE_CASES.md
```

이후 AI에게 다음처럼 검증시킬 수 있다.

```text
BR-ORD-001~004가 실제 코드와 테스트에 모두 구현되어 있는지
Traceability Matrix를 작성하라.
```

---

# 9. 화면 IA 및 화면설계

먼저 IA를 작성한다.

```text
Home

상품
 ├─ 카테고리
 ├─ 검색
 ├─ 상품상세

회원
 ├─ 로그인
 ├─ 가입
 ├─ 마이페이지

주문
 ├─ 장바구니
 ├─ 주문서
 ├─ 결제완료
 ├─ 주문조회

고객센터
 ├─ FAQ
 ├─ 문의
```

화면별 Screen ID를 부여한다.

```text
SCR-MEM-001 로그인
SCR-CAT-001 상품목록
SCR-CAT-002 상품상세
SCR-ORD-001 장바구니
SCR-ORD-002 주문서
SCR-ORD-003 주문완료
```

화면은 이미지뿐 아니라 구조화된 Markdown Spec을 함께 관리한다.

```text
[SCR-ORD-002]

화면명: 주문서

입력
- 배송지
- 쿠폰
- 포인트
- 결제수단

표시
- 상품금액
- 할인금액
- 배송비
- 최종결제금액

Action
- 쿠폰 적용
- 배송지 변경
- 결제

Validation
- 배송지 필수
- 결제수단 필수

API
POST /orders/preview
POST /orders
```

---

# 10. UI는 Figma + Markdown 조합

권장 방식:

```text
Figma
→ 사람이 보는 UI

PNG
→ AI가 디자인 이해

Markdown
→ AI가 구조와 규칙 이해
```

Figma만 주거나 Markdown만 주는 것보다 둘을 함께 사용하는 것이 좋다.

---

# 11. 비기능 요구사항 정의

대형 쇼핑몰은 기능 요구사항만 정의하면 안 된다.

예:

| 영역 | 목표 |
|---|---|
| 가용성 | 99.95% |
| API 응답 | p95 < 300ms |
| 상품검색 | p95 < 500ms |
| 주문처리 | p95 < 1초 |
| 확장 | Auto Scaling |
| DB | Point-in-Time Recovery |
| RPO | 5분 |
| RTO | 30분 |
| 감사로그 | 관리자 변경 기록 |
| 개인정보 | 암호화 |
| 장애추적 | Trace ID |

Black Friday, 프로모션 오픈 등 급격한 트래픽 증가 시나리오도 포함한다.

---

# 12. 시스템 Architecture

처음부터 Microservices를 선택할 필요는 없다.

AI 코딩 프로젝트라면 초기에는 **Modular Monolith**가 현실적이다.

```text
commerce-backend

member
catalog
pricing
inventory
cart
order
payment
delivery
claim
promotion
```

코드는 하나의 Backend 프로젝트이지만 Domain Boundary는 명확하게 유지한다.

이후 필요 시 다음 도메인을 선택적으로 분리한다.

```text
Order
Payment
Search
Notification
```

권장 전략:

```text
Modular Monolith
→ Selective Microservices
```

---

# 13. 기술 Stack 예시

```text
Frontend
Next.js
TypeScript
React

Backend
Spring Boot
또는
FastAPI

Database
PostgreSQL

Cache
Redis

Search
OpenSearch / Elasticsearch

Message
Kafka

Object Storage
S3 Compatible Storage

CDN
CloudFront 계열

Observability
OpenTelemetry
Prometheus
Grafana

Container
Docker

Deployment
Kubernetes
또는 초기 단계 ECS류
```

중요한 것은 기술 이름 자체보다 **왜 선택했는지 ADR에 기록하는 것**이다.

---

# 14. ADR 운영

ADR = Architecture Decision Record

예:

```text
ADR-001 Backend Framework
ADR-002 Database
ADR-003 Authentication
ADR-004 Search Engine
ADR-005 Message Broker
ADR-006 Transaction Strategy
```

예시:

```text
ADR-006

결정:
주문/결제 간 Distributed Transaction에
2PC를 사용하지 않는다.

대안:
1. 2PC
2. Saga
3. Event + Compensation

결론:
Saga + Compensation 사용

이유:
확장성과 장애 격리
```

---

# 15. ERD 설계

Domain별로 설계한다.

```text
MEMBER
ADDRESS

PRODUCT
PRODUCT_OPTION
SKU
CATEGORY

CART
CART_ITEM

ORDER
ORDER_ITEM
ORDER_PAYMENT
ORDER_DELIVERY

PAYMENT
PAYMENT_TRANSACTION

DELIVERY
DELIVERY_HISTORY

CLAIM
CLAIM_ITEM

COUPON
COUPON_ISSUE

POINT_LEDGER
```

특히 대형 쇼핑몰은 **상태 변경 이력과 Snapshot**이 중요하다.

예:

```text
PRODUCT.name

ORDER_ITEM.product_name
ORDER_ITEM.sale_price
ORDER_ITEM.option_name
```

과거 주문은 당시 상품명, 가격, 옵션 정보가 보존되어야 한다.

---

# 16. 상태 머신 설계

주문 상태 예:

```text
CREATED
PAYMENT_PENDING
PAID
PREPARING
SHIPPED
DELIVERED
CONFIRMED

CANCELLED
```

반품 상태 예:

```text
REQUESTED
APPROVED
COLLECTING
COLLECTED
REFUND_PENDING
REFUNDED
```

추천 문서:

```text
ORDER_STATE_TRANSITION.md
CLAIM_STATE_TRANSITION.md
DELIVERY_STATE_TRANSITION.md
```

원칙:

```text
정의되지 않은 상태 전이는 코드에서 허용하지 않는다.
```

---

# 17. API 설계

구현보다 먼저 OpenAPI Specification을 작성하고 승인한다.

예:

```http
GET /api/v1/products/{productId}

POST /api/v1/cart/items

POST /api/v1/orders/preview

POST /api/v1/orders

POST /api/v1/payments

POST /api/v1/orders/{id}/cancel
```

API마다 다음을 정의한다.

```text
Request
Response
Validation
Error Code
Authentication
Authorization
Idempotency
Transaction
Rate Limit
```

특히 주문/결제에는 중복 요청 방지를 고려한다.

```http
Idempotency-Key
```

---

# 18. Error Code 설계

예:

```text
ORD-0001 ORDER_NOT_FOUND
ORD-0002 INVALID_ORDER_STATUS
ORD-0003 OUT_OF_STOCK

PAY-0001 PAYMENT_FAILED
PAY-0002 PAYMENT_TIMEOUT
PAY-0003 PAYMENT_ALREADY_COMPLETED
```

Frontend와 Backend 간 계약을 명확하게 한다.

---

# 19. Event 설계

대형 쇼핑몰은 동기 API만으로 구성하지 않는다.

예:

```text
OrderCompleted
PaymentCompleted
PaymentFailed
InventoryReserved
ShipmentStarted
DeliveryCompleted
OrderCancelled
```

Consumer 예:

```text
OrderCompleted
 ├─ Notification
 ├─ Analytics
 └─ Seller
```

AI에게 반드시 검증시킬 것:

```text
이벤트가 중복 수신되어도 안전한가?
```

즉 **Idempotent Consumer**가 필요하다.

---

# 20. 개인정보와 보안 설계

초기 설계부터 포함한다.

```text
회원 인증
OAuth/OIDC
JWT/Session

관리자 인증
MFA

권한
RBAC

개인정보
암호화

Password
Argon2/bcrypt

Network
TLS

Secrets
Secret Manager

로그
개인정보 Masking
```

관리자 기능은 Audit Log를 남긴다.

```text
누가
언제
어떤 메뉴에서
어떤 데이터를
이전 값에서
어떤 값으로
변경했는가
```

---

# 21. AI Coding Constitution 작성

프로젝트 최상위에 AI가 반드시 읽어야 할 규칙을 둔다.

예:

```text
모든 구현은 /docs 설계를 기준으로 한다.

설계와 코드가 충돌하면
임의로 구현하지 말고 설계 불일치로 보고한다.

새로운 라이브러리는 임의 도입하지 않는다.

DB Schema 변경은 Migration으로 수행한다.

Domain Boundary를 위반하지 않는다.

API 변경 시 OpenAPI도 수정한다.

Business Rule 변경 시 테스트도 수정한다.

모든 신규 기능에는 테스트가 필요하다.

임시 코드/TODO/mock을 완료 처리하지 않는다.

보안 검증을 우회하지 않는다.

사용자의 승인 없이 Architecture를 변경하지 않는다.
```

Claude Code라면 `CLAUDE.md`, Codex라면 해당 프로젝트 지침 체계를 사용한다.

---

# 22. 개발 표준 정의

추천 문서:

```text
CODING_STANDARD.md
DATABASE_STANDARD.md
API_STANDARD.md
SECURITY_STANDARD.md
TEST_STANDARD.md
LOGGING_STANDARD.md
```

DB 표준 예:

```text
PK 규칙
FK 규칙
INDEX 규칙
TIMESTAMP 규칙
Logical Delete 규칙
Naming Convention
Audit Column
```

---

# 23. Walking Skeleton 구축

개발을 바로 시작하지 말고 전체 기술 경로를 먼저 연결한다.

```text
Browser
 ↓
Frontend
 ↓
API Gateway
 ↓
Backend
 ↓
PostgreSQL
 ↓
Redis
 ↓
Observability
```

최소 시나리오:

```text
Login
→ 상품 1건 조회
→ 주문 Test
→ DB 저장
→ 로그 확인
```

목적은 기능 개발이 아니라 **기술 구조 검증**이다.

---

# 24. MVP 개발

MVP는 허술한 시스템이 아니다.

**기능 범위는 작지만 Architecture와 품질 기준은 실제 서비스 수준**이어야 한다.

예:

```text
회원
상품
장바구니
주문
결제
배송
```

테스트, 보안, 로그, 트랜잭션은 실제 운영 수준으로 만든다.

---

# 25. Vertical Slice 방식

비추천:

```text
전체 DB 구현
↓
전체 Backend
↓
전체 Frontend
```

추천:

```text
상품조회
DB → Backend → API → Frontend → Test

장바구니
DB → Backend → API → Frontend → Test

주문
DB → Backend → API → Frontend → Test
```

기능 하나를 끝에서 끝까지 완성한다.

---

# 26. AI 작업 단위를 작게 유지

나쁜 요청:

```text
주문 시스템 구현해.
```

좋은 요청:

```text
UC-ORD-001 주문 생성의 Step 1을 구현한다.

범위:
- Order Entity
- Order Repository
- Order Service
- POST /orders

참조:
BR-ORD-001
BR-ORD-002
API-ORD-001

이번 작업에서는
결제 구현 금지
배송 구현 금지

완료 후
테스트 결과와 변경파일을 보고한다.
```

---

# 27. 구현 Agent와 Review Agent 분리

권장 역할:

```text
Agent A
구현

Agent B
Code Review

Agent C
Security Review

Agent D
Test Review
```

실제 Multi-Agent 제품이 아니더라도 동일 AI에 역할을 나누어 순차 수행시킬 수 있다.

---

# 28. 사용자가 확인해야 할 것

코드 전체보다 다음을 확인한다.

| 확인 항목 | 사용자 확인 |
|---|---|
| 구현 기능 | 원하는 기능인가 |
| 화면 | 원하는 UI인가 |
| 업무 흐름 | 맞는가 |
| 오류 처리 | 적절한가 |
| 권한 | 올바른가 |
| 테스트 | 통과했는가 |
| 미구현 | 남았는가 |
| 설계 변경 | 있었는가 |
| 위험 | 무엇인가 |

AI에게 다음을 요구한다.

```text
기술적인 코드 설명보다
업무적으로 무엇이 구현되었는지를 설명하라.
```

---

# 29. Traceability Matrix 운영

예:

| Requirement | Screen | API | DB | Code | Test |
|---|---|---|---|---|---|
| REQ-ORD-01 | SCR-ORD-01 | API-ORD-01 | ORDER | OrderService | TC-ORD-01 |
| REQ-ORD-02 | SCR-ORD-02 | API-ORD-02 | ORDER | CancelService | TC-ORD-02 |

목적:

- 설계는 있는데 구현되지 않은 기능 발견
- 구현했지만 테스트가 없는 기능 발견
- 변경 영향도 추적
- 누락 방지

---

# 30. 테스트 전략

```text
Unit Test
↓
Domain Test
↓
Repository Test
↓
API Integration Test
↓
Contract Test
↓
E2E Test
↓
Performance Test
↓
Security Test
```

핵심 업무 테스트 케이스는 사용자가 확인하는 것이 좋다.

---

# 31. 주문 실패 테스트

정상보다 실패 케이스가 더 중요하다.

```text
정상 주문
품절 주문
가격 변경
쿠폰 만료
중복 주문
결제 실패
결제 Timeout
PG Callback 중복
DB 장애
Redis 장애
Kafka 장애
부분취소
전체취소
부분반품
전체반품
배송중 취소
```

---

# 32. Chaos / 장애 테스트

예:

```text
PostgreSQL 일시 장애

Redis 장애

Kafka 지연

PG API Timeout

택배 API Timeout

Notification 실패
```

핵심 원칙:

```text
결제됐는데 주문이 사라져서는 안 된다.
```

---

# 33. 성능 테스트

주요 API별 목표:

```text
GET /products
P95 < 300ms

GET /search
P95 < 500ms

POST /orders
P95 < 1s
```

도구 예:

```text
k6
JMeter
Gatling
```

---

# 34. Observability

초기부터 구축한다.

```text
Log
Metric
Trace
Alert
```

Trace 예:

```text
Trace ID

Client
 ↓
Frontend
 ↓
API
 ↓
Order
 ↓
Payment
 ↓
DB
```

---

# 35. 운영 대시보드

추천 지표:

```text
주문 성공률
결제 성공률
결제 실패율
PG Timeout
API Error Rate
CPU
Memory
DB Connection
Cache Hit Ratio
Kafka Lag
```

---

# 36. CI/CD

```text
Agent Code
 ↓
Lint
 ↓
Compile
 ↓
Unit Test
 ↓
Integration Test
 ↓
Security Scan
 ↓
Build
 ↓
Staging Deploy
 ↓
E2E Test
 ↓
Approval
 ↓
Production
```

AI가 테스트를 우회해 Production으로 갈 수 있는 경로를 만들지 않는다.

---

# 37. Git 운영

예:

```text
main
develop 또는 trunk 기반 전략

feature/ORD-001-create-order
feature/PAY-001-payment
```

AI Agent에게는 **한 작업당 하나의 Branch**를 권장한다.

PR에는 다음을 자동 작성하게 한다.

```text
변경사항
관련 요구사항
관련 Business Rule
DB 변경
API 변경
테스트 결과
위험사항
Rollback 방법
```

---

# 38. Backlog 중심 개발

구조:

```text
Epic
  ↓
Feature
  ↓
User Story
  ↓
Task
```

예:

```text
EPIC-ORD
주문

FEAT-ORD-01
주문 생성

US-ORD-001
고객은 장바구니 상품을 주문할 수 있다.

TASK
DB
API
Service
UI
Test
```

AI에게는 **Task 단위**로 일을 준다.

---

# 39. Roadmap 문서

예:

```text
[BACKLOG]Commerce_Roadmap.md
```

구성:

```text
Phase 1 Foundation
Phase 2 Member
Phase 3 Catalog
Phase 4 Cart
Phase 5 Order
Phase 6 Payment
...
```

매 Agent 세션 시작 시:

```text
먼저 Roadmap을 읽고
현재 진행 위치를 확인한다.
```

---

# 40. 설계 문서 무단 변경 방지

AI가 구현 편의를 위해 설계를 임의 변경하지 못하게 한다.

원칙:

```text
설계 변경이 필요하면 구현을 중지하고
CHANGE_REQUEST.md를 작성한다.
```

예:

```text
CR-023

현재 설계:
ORDER : PAYMENT = 1:N

문제:
부분결제 기능 때문에 확장 필요

제안:
PAYMENT_TRANSACTION 구조 추가

영향:
DB
API
Settlement

사용자 승인:
Pending
```

---

# 41. AI Hallucination 통제

대표적인 문제:

```text
존재하지 않는 API 사용

설계되지 않은 Column 추가

임의 라이브러리 추가

기존 코드를 이해하지 않고 새 코드 생성

테스트 없이 완료 선언
```

Definition of Done:

```text
코드 구현
+
Test 작성
+
모든 Test PASS
+
Lint PASS
+
Build PASS
+
API 문서 갱신
+
DB 문서 갱신
+
Roadmap 갱신
+
미해결 TODO 없음
```

---

# 42. 추천 프로젝트 문서 구조

```text
/docs

00_project
  PROJECT_CHARTER.md
  SCOPE.md
  GLOSSARY.md

01_requirements
  REQUIREMENTS.md
  BUSINESS_RULES.md
  USE_CASES.md

02_architecture
  SYSTEM_ARCHITECTURE.md
  DOMAIN_MODEL.md
  INTEGRATION_ARCHITECTURE.md
  adr/

03_data
  ERD.md
  DATA_DICTIONARY.md
  STATE_TRANSITION.md

04_api
  openapi.yaml
  EVENT_CATALOG.md
  ERROR_CODES.md

05_screen
  SCREEN_LIST.md
  IA.md
  SCREEN_SPEC.md

06_security
  SECURITY_ARCHITECTURE.md
  PRIVACY.md
  RBAC.md

07_development
  CODING_STANDARD.md
  DATABASE_STANDARD.md
  API_STANDARD.md
  TEST_STANDARD.md

08_operation
  DEPLOYMENT.md
  MONITORING.md
  INCIDENT_RESPONSE.md
  BACKUP_RECOVERY.md

09_test
  TEST_PLAN.md
  TEST_CASES.md

10_backlog
  ROADMAP.md
  TRACEABILITY_MATRIX.md
```

이 문서 저장소를 **AI의 장기 기억 역할**로 사용한다.

---

# 43. Human Approval Gate

| Gate | 사용자 승인 내용 |
|---|---|
| G1 | 프로젝트 목표 |
| G2 | Scope |
| G3 | Domain |
| G4 | Business Flow |
| G5 | 요구사항 |
| G6 | 화면 |
| G7 | Architecture |
| G8 | ERD |
| G9 | API |
| G10 | Security |
| G11 | MVP |
| G12 | 각 도메인 완료 |
| G13 | 통합테스트 |
| G14 | 성능 |
| G15 | Production |

특히 G2, G4, G6, G8, G11은 사용자가 직접 상세 검토하는 것이 좋다.

---

# 44. 사용자와 AI의 역할 구분

| 사용자 검토 | AI 검토 |
|---|---|
| 기능이 필요한가 | 코드 구조 |
| 업무 흐름이 맞는가 | Design Pattern |
| 화면이 좋은가 | 코드 품질 |
| 데이터가 필요한가 | Index |
| 권한이 맞는가 | SQL 최적화 |
| 에러 처리가 적절한가 | 메모리/성능 |
| 테스트 시나리오가 충분한가 | 자동화 테스트 |
| 결과가 요구사항과 같은가 | Security Scan |

권장 역할:

```text
사용자
= Product Owner + 업무 Architect

AI
= System Architect + Developer + Tester + Reviewer
```

---

# 45. Multi-Agent 구조

```text
Orchestrator
      │
      ├── Requirement Agent
      ├── Architecture Agent
      ├── DB Agent
      ├── Backend Agent
      ├── Frontend Agent
      ├── Test Agent
      ├── Security Agent
      └── Review Agent
```

초기에는 병렬 코딩보다 다음 순서가 안전하다.

```text
설계
↓
사용자 승인
↓
1개 Agent 구현
↓
다른 Agent 리뷰
↓
테스트 Agent 검증
↓
사용자 승인
```

---

# 46. AI가 작업 전에 반드시 수행할 절차

```text
1. 관련 설계 문서를 읽는다.

2. 관련 기존 코드를 읽는다.

3. 변경 범위를 파악한다.

4. 구현 계획을 작성한다.

5. 설계와 충돌 여부를 검사한다.

6. 충돌하면 구현하지 않는다.

7. 문제가 없을 때만 코딩한다.
```

즉 **Plan → Code**를 강제한다.

---

# 47. 구현 후 필수 절차

```text
Implementation
↓
Self Review
↓
Test
↓
Regression Test
↓
Security Review
↓
Documentation
↓
Completion Report
```

이 절차를 Harness에 포함시키는 것이 좋다.

핵심은 AI가 실수해도 **잘못된 결과가 Repository에 들어가지 못하게 하는 환경**을 만드는 것이다.

---

# 48. 실제 프로젝트 시작 순서

첫 개발 세션에서는 코딩을 하지 않는다.

먼저:

```text
PROJECT_CHARTER
SCOPE
DOMAIN_MAP
GLOSSARY
```

작성 후 사용자 검토.

다음:

```text
BUSINESS_FLOW
USE_CASE
BUSINESS_RULE
```

작성 후 사용자 검토.

다음:

```text
IA
SCREEN_LIST
SCREEN_SPEC
```

작성 후 사용자 검토.

다음:

```text
SYSTEM_ARCHITECTURE
ERD
API
EVENT
SECURITY
```

설계 후 사용자 검토.

그 다음:

```text
Walking Skeleton
```

그리고:

```text
MVP
```

이후 Vertical Slice 방식으로 확대한다.

```text
Catalog
→ Cart
→ Order
→ Payment
→ Delivery
→ Claim
→ Promotion
→ Point
→ Review
→ Seller
→ Settlement
```

---

# 49. 대형 쇼핑몰에서 빠뜨리기 쉬운 기능

```text
부분취소
부분반품
부분교환

복수 배송지

묶음배송
분리배송

판매자별 배송비

도서산간 배송비

쿠폰 중복정책

쿠폰 반환정책

포인트 적립/취소

결제 취소 실패 복구

PG 정산 대사

판매자 정산

세금계산

재고 예약

재고 복구

품절

옵션 변경

상품 가격 변경

관리자 강제 처리

CS 주문 변경

휴면/탈퇴 회원

개인정보 삭제

감사로그

재처리 Batch

외부 연동 재시도
```

AI에게 별도 Review를 시킨다.

```text
국내 대형 B2C Marketplace 운영 기준으로
누락되기 쉬운 예외 업무를 찾아라.
```

---

# 50. 최종 권장 방법론

권장 방식:

> **Human-Gated AI Engineering + Design-First + Vertical Slice + Living Documentation + Automated Verification + Harness Engineering**

즉,

```text
AI 설계
↓
사람 확인
↓
AI 보완
↓
사람 승인
↓
AI 구현
↓
AI 테스트
↓
다른 AI 리뷰
↓
자동 검증
↓
사람 결과 확인
↓
다음 기능
```

이 사이클을 반복한다.

---

# 51. 가장 중요한 운영 원칙

처음부터 전체 쇼핑몰을 AI에게 구현시키지 않는다.

초기에 충분히 만들어야 하는 것은 코드가 아니라 다음이다.

```text
요구사항
업무흐름
Business Rule
Domain
화면
ERD
API
Architecture
Security
Test Scenario
Development Rule
```

이것이 잘 만들어져 있으면 이후 AI의 코딩 속도와 품질이 크게 올라간다.

반대로 이 기반 없이 빠르게 코딩하면 시간이 지날수록 **전체 시스템의 동작을 누구도 확신하지 못하는 거대한 코드베이스**가 될 가능성이 높다.

---

# 52. 다음 단계 권장

실제 프로젝트를 시작한다면 다음 단계로 진행하는 것을 권장한다.

## Step 0 — AI Agent 개발 체계 구축

- Repository 구조
- 문서 구조
- Agent 지침
- Coding Constitution
- Roadmap
- Branch/PR 정책
- Definition of Done
- Review Gate
- 테스트 자동화
- CI/CD 기본 구조

## Step 1 — Project Charter / Scope

- 사업 목적
- 사용자 유형
- 핵심 KPI
- 예상 트래픽
- 기능 범위
- 제외 범위
- 향후 범위
- 서비스 수준
- 규제/보안 요구사항

이후 각 단계는 다음 네 가지를 세트로 관리하는 방식이 좋다.

1. **사용자가 해야 할 Action**
2. **AI에게 줄 Prompt**
3. **AI가 만들어야 할 산출물**
4. **사용자가 확인해야 할 Checklist**

이를 기반으로 전체 프로젝트를 **30~40개의 세부 Step으로 분할한 Master Action Plan**으로 발전시키면, Claude Code나 Codex와 실제 프로젝트를 차근차근 진행하기 좋은 형태가 된다.
