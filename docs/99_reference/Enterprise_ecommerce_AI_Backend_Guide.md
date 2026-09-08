# 대형 이커머스 백엔드 시스템 구축 가이드

> **문서 성격**: 이 문서는 대형 이커머스 시스템 구축을 위한 참고 가이드다. 현재 프로젝트의 승인된 요구사항과 구현 범위는 `docs/00_project/project-scope.md` 및 개별 설계 문서를 우선한다. 이 문서의 내용은 별도 검토·승인 없이는 구현 범위로 간주하지 않는다.

> **목적**: 대규모 엔터프라이즈형 이커머스 백엔드 시스템을 AI Agent와 함께 안정적으로 구축하기 위한 아키텍처·기반 프레임워크·Reference Implementation·개발 표준·운영 원칙을 정의한다.
>
> **권장 대상**: 중대형 SI 프로젝트, 자체 플랫폼 개발 조직, 수십~수백 명 규모의 개발팀, 장기 운영을 전제로 하는 커머스/리테일 플랫폼

---

## 1. 문서의 핵심 결론

대형 이커머스 시스템은 업무 기능부터 바로 개발하는 방식보다 다음 순서를 권장한다.

```text
Architecture Vision
    ↓
Architecture & Engineering Rules
    ↓
Project Skeleton
    ↓
Foundation Framework
    ↓
Reference Implementation / Golden Path
    ↓
Architecture Validation
    ↓
AI Coding Instructions
    ↓
Domain별 병렬 개발
    ↓
Architecture Compliance / CI 검증
    ↓
통합·성능·보안·운영 안정화
```

핵심 원칙은 다음과 같다.

1. **업무 기능보다 아키텍처와 개발 규칙을 먼저 고정한다.**
2. **공통 프레임워크를 과도하게 만들지 않는다.**
3. **대표 업무 하나를 실제 운영 수준으로 끝까지 구현해 Reference Implementation으로 사용한다.**
4. **AI에게 매번 설계를 맡기지 않고, 이미 결정된 구조 안에서 구현하게 한다.**
5. **Domain 단위의 Vertical Slice로 개발한다.**
6. **아키텍처 규칙을 문서뿐 아니라 코드·테스트·CI로 강제한다.**

---

# 2. 대상 시스템 범위

대형 이커머스 시스템의 대표 업무 영역을 다음과 같이 가정한다.

```text
Customer
Member
Authentication
Authorization
Catalog
Product
Category
Inventory
Price
Promotion
Coupon
Cart
Order
Payment
Delivery
Return
Exchange
Refund
Settlement
Seller
Vendor
Marketplace
Review
Customer Service
Notification
Search
Recommendation
Admin
Batch
Reporting
Audit
```

모든 업무를 하나의 거대한 공통 계층으로 묶는 방식은 지양한다.

권장 방식은 **Domain 중심의 모듈화**다.

---

# 3. 권장 아키텍처 방향

## 3.1 초기 권장 구조

대부분의 신규 엔터프라이즈 이커머스 시스템은 다음 순서가 현실적이다.

```text
1단계: Modular Monolith
2단계: 명확한 Domain Boundary 확보
3단계: 필요 Domain만 독립 서비스로 분리
4단계: 선택적 Microservices 전환
```

초기부터 모든 기능을 Microservices로 분리하면 다음 비용이 급격히 증가한다.

- 분산 트랜잭션
- 서비스 간 API 관리
- 네트워크 장애 처리
- 메시지 정합성
- 모니터링
- 배포 파이프라인
- 장애 추적
- 운영 복잡성

따라서 **조직 규모·트래픽·업무 독립성·배포 독립성 요구가 충분하지 않다면 Modular Monolith부터 시작하는 것을 권장**한다.

---

## 3.2 기본 레이어 구조

예시:

```text
Presentation
    ↓
Application
    ↓
Domain
    ↓
Infrastructure
```

또는 Ports & Adapters 관점에서:

```text
Inbound Adapter
    ↓
Application Use Case
    ↓
Domain
    ↓
Outbound Port
    ↓
Infrastructure Adapter
```

권장 의존성 방향:

```text
Controller
   ↓
Application Service
   ↓
Domain Service / Aggregate
   ↓
Repository Interface
   ↓
Repository Implementation
```

금지 예시:

```text
Controller → Repository 직접 호출
Domain → 외부 API Client 직접 호출
Domain A → Domain B의 Repository 직접 호출
```

---

# 4. 프로젝트 착수 단계

## Phase 0. 기술 스택 선정

예시 Java 기반:

```text
Language        : Java 21+
Framework       : Spring Boot
Build           : Gradle
DB              : PostgreSQL / Oracle
Cache           : Redis
Message         : Kafka
Search          : OpenSearch / Elasticsearch
API             : REST + 선택적 gRPC
Batch           : Spring Batch
Container       : Docker
Orchestration   : Kubernetes
Observability   : OpenTelemetry + Prometheus + Grafana
CI/CD           : GitHub Actions / GitLab CI / Jenkins
```

Python 기반도 가능하지만, 수십 년 장기 운영·다수 개발자·대규모 SI 조직을 고려하면 Java/Spring 계열이 여전히 관리 측면에서 유리한 경우가 많다.

---

# 5. Architecture Vision 정의

프로젝트 초기에 최소 다음 내용을 명시한다.

## 5.1 시스템 구조

- Modular Monolith / Microservices 여부
- Domain Boundary
- 동기/비동기 통신 원칙
- 데이터 소유권
- 트랜잭션 경계
- 배치 처리 원칙
- 외부 시스템 연계 방식

## 5.2 데이터 정책

- 각 Domain 데이터 소유 원칙
- Cross Domain Join 제한
- 조회용 Read Model 허용 기준
- History / Audit 관리
- Soft Delete 기준
- 개인정보 분리
- 데이터 보존 정책

## 5.3 장애 정책

- Timeout
- Retry
- Circuit Breaker
- Idempotency
- Dead Letter Queue
- Compensation

---

# 6. Engineering Rules

AI 개발에서는 아키텍처보다 더 구체적인 Engineering Rules가 반드시 필요하다.

## 6.1 Controller 규칙

```text
- 비즈니스 로직 금지
- Repository 직접 접근 금지
- 요청 검증은 DTO Validation으로 처리
- Application Service만 호출
- Entity 직접 반환 금지
```

## 6.2 Application Service 규칙

```text
- Use Case 단위로 구성
- Transaction Boundary 관리
- 여러 Domain 객체 간 흐름 조정
- 외부 Port 호출 조정
- Domain 내부 규칙 직접 구현 최소화
```

## 6.3 Domain 규칙

```text
- 핵심 비즈니스 정책 위치
- 외부 기술 의존성 최소화
- Repository 구현체 의존 금지
- HTTP/Redis/Kafka/JPA 세부 구현 의존 금지
```

## 6.4 Repository 규칙

```text
- Domain Repository Interface와 Infrastructure 구현 분리
- 복잡한 Query는 전용 Query Repository 허용
- EntityManager / Mapper 직접 사용 범위 제한
```

## 6.5 DTO / Entity 규칙

```text
API DTO ≠ Domain Object ≠ Persistence Entity
```

대형 프로젝트에서는 세 계층을 명확하게 분리하는 편이 장기 유지보수에 유리하다.

---

# 7. 권장 프로젝트 구조

예시:

```text
com.company.commerce
│
├─ common
│  ├─ web
│  ├─ exception
│  ├─ security
│  ├─ logging
│  ├─ audit
│  ├─ validation
│  └─ util
│
├─ customer
│  ├─ presentation
│  ├─ application
│  ├─ domain
│  └─ infrastructure
│
├─ catalog
│  ├─ presentation
│  ├─ application
│  ├─ domain
│  └─ infrastructure
│
├─ inventory
├─ pricing
├─ promotion
├─ cart
├─ order
├─ payment
├─ delivery
├─ returnrefund
├─ settlement
├─ seller
│
├─ batch
├─ integration
└─ bootstrap
```

---

# 8. Foundation Framework 구축 범위

Foundation Framework는 '모든 것을 공통화'하는 것이 아니라 **정책적으로 동일해야 하는 기능을 공통화**해야 한다.

## 8.1 Web / API

구축 항목:

- 표준 API Response
- 표준 Error Response
- Request ID / Correlation ID
- Pagination
- Sorting
- API Versioning
- Validation
- Global Exception Handler

예시:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "traceId": "abc-123"
}
```

---

## 8.2 Exception Framework

예:

```text
BusinessException
ValidationException
AuthorizationException
ResourceNotFoundException
IntegrationException
SystemException
```

Error Code도 중앙 정책으로 관리한다.

예:

```text
ORD-001 : 주문을 찾을 수 없음
ORD-002 : 주문 취소 불가 상태
PAY-001 : 결제 승인 실패
INV-001 : 재고 부족
```

---

## 8.3 Security

구축 항목:

- Authentication
- Authorization
- JWT / Session 정책
- RBAC / ABAC
- Admin 권한
- 개인정보 접근 통제
- API 인증
- Service-to-Service 인증

---

## 8.4 Database Framework

구축 항목:

- DB Connection
- Transaction
- Lock 정책
- Query Timeout
- Read/Write 분리
- Pagination
- Optimistic Lock
- Pessimistic Lock 사용 기준

---

## 8.5 Logging

모든 로그는 구조화하는 것을 권장한다.

예:

```json
{
  "timestamp": "2026-09-08T13:00:00+09:00",
  "traceId": "...",
  "userId": "...",
  "domain": "ORDER",
  "action": "CREATE_ORDER",
  "elapsedMs": 132
}
```

---

## 8.6 Audit

특히 다음은 별도 Audit Trail을 권장한다.

- 주문 변경
- 결제
- 환불
- 관리자 변경
- 회원정보 변경
- 가격 변경
- 프로모션 변경
- 정산

---

## 8.7 Messaging

Kafka 등 이벤트 기반 처리 시 표준을 정한다.

```text
Topic Naming
Event Naming
Schema Version
Retry
Dead Letter Queue
Ordering
Idempotency
```

예:

```text
order.created.v1
payment.approved.v1
inventory.reserved.v1
shipment.started.v1
```

---

## 8.8 External API Integration

공통 기능:

- Timeout
- Retry
- Circuit Breaker
- HTTP Client Logging
- 인증
- Error Mapping

---

## 8.9 Batch Framework

- Job Naming
- Step Naming
- Restart 정책
- Retry 정책
- Skip 정책
- Job Parameter
- History
- 운영자 재처리

---

## 8.10 Test Framework

최소 제공:

- Unit Test Template
- Repository Test
- API Integration Test
- Test Fixture
- Test Container
- Mock External API

---

# 9. 공통화해서는 안 되는 것

대형 SI에서 흔히 발생하는 실패는 과도한 공통화다.

예를 들어 다음 구조는 지양한다.

```text
CommonController
CommonService
CommonDAO
CommonBusinessService
CommonProcessManager
```

모든 Domain의 업무 로직이 공통 Framework에 들어가기 시작하면 Framework가 사실상 거대한 업무 시스템이 된다.

공통화 판단 기준:

> **중복인가?**가 아니라 **정책적으로 동일해야 하는가?**

예:

| 항목 | 공통화 |
|---|---|
| Logging | 권장 |
| Authentication | 권장 |
| Error Response | 권장 |
| Audit | 권장 |
| Transaction 기본 정책 | 권장 |
| 주문 상태 변경 로직 | 비권장 |
| 배송 상태 로직 | 비권장 |
| 상품 가격 계산 정책 | 비권장 |

---

# 10. Reference Implementation / Golden Path

Foundation Framework가 만들어졌다면 대표 Domain 하나를 실제 운영 수준으로 구현한다.

대형 이커머스에서는 **Order Domain**을 Reference Implementation 후보로 추천한다.

이유:

```text
Order는
Customer
Product
Price
Promotion
Inventory
Payment
Delivery
등 여러 Domain과 연결되므로
전체 아키텍처를 검증하기 좋다.
```

단, 첫 구현 난이도를 낮추고 싶다면 Customer 또는 Product부터 시작할 수 있다.

---

# 11. Order Reference Implementation 범위

예시 Use Case:

```text
주문 생성
주문 조회
주문 취소
```

주문 생성 흐름 예:

```text
Order API Request
      ↓
Authentication
      ↓
Validation
      ↓
OrderApplicationService
      ↓
Customer 확인
      ↓
Product / Price 확인
      ↓
Promotion 계산
      ↓
Inventory 예약
      ↓
Order 생성
      ↓
Payment 요청
      ↓
Order 저장
      ↓
OrderCreated Event
      ↓
Audit Log
      ↓
API Response
```

이 하나를 통해 다음을 검증할 수 있다.

- API 구조
- Transaction Boundary
- Lock
- DB 접근
- 외부 연계
- Event
- Exception
- Logging
- Audit
- Test

---

# 12. 주문 Transaction 설계 예

대형 커머스에서 중요한 문제 중 하나는 '하나의 거대한 DB Transaction'을 피하는 것이다.

잘못된 예:

```text
Order Transaction BEGIN

Inventory API
Payment API
Coupon API
Delivery API

Order DB INSERT

COMMIT
```

외부 API 호출을 DB Transaction 안에서 오래 유지하면 Lock과 장애 전파 문제가 커진다.

권장:

```text
Local Transaction
+
Event / Saga / Compensation
```

예:

```text
Order 생성
   ↓
Inventory Reserved
   ↓
Payment Approved
   ↓
Order Confirmed
```

실패 시:

```text
Payment Failure
   ↓
Inventory Reservation Cancel
   ↓
Order Cancel
```

---

# 13. Idempotency

커머스 시스템에서 필수다.

특히:

- 주문
- 결제
- 환불
- 쿠폰
- 포인트
- 정산

등에는 중복 요청 방지가 필요하다.

예:

```text
Idempotency-Key
```

또는 Business Key 기반 중복 방지를 적용한다.

---

# 14. Event Driven Architecture

다음 업무는 비동기 이벤트가 적합하다.

```text
Order Created
Payment Approved
Payment Failed
Inventory Reserved
Shipment Started
Shipment Completed
Refund Completed
```

단, 모든 것을 이벤트로 만드는 것은 피한다.

판단 기준:

```text
즉시 응답이 필요한가?
강한 정합성이 필요한가?
업무가 독립적으로 재처리 가능한가?
장애 격리가 필요한가?
```

---

# 15. AI 개발 규칙

프로젝트 Root에 다음 문서를 두는 것을 권장한다.

```text
AGENTS.md
ARCHITECTURE.md
CODING_RULES.md
DOMAIN_RULES.md
TEST_RULES.md
DATABASE_RULES.md
API_RULES.md
```

---

# 16. AGENTS.md 예시

```markdown
# AI Development Rules

## Architecture

- Modular Monolith 구조를 유지한다.
- 모든 신규 업무는 기존 Domain Boundary를 우선 사용한다.
- 신규 Domain 생성 전 기존 Domain으로 수용 가능한지 검토한다.

## Dependency

- Controller는 Application Service만 호출한다.
- Controller에서 Repository 호출 금지.
- Domain에서 Infrastructure 구현체 참조 금지.
- Domain 간 Repository 직접 접근 금지.

## Data

- API DTO를 Persistence Entity로 사용하지 않는다.
- Entity를 API Response로 직접 반환하지 않는다.

## Transaction

- Transaction Boundary는 Application Layer에서 정의한다.
- 외부 API 호출을 장시간 DB Transaction 내부에서 실행하지 않는다.

## Reference Implementation

- 신규 Domain 개발 시 order 모듈의 구조와 구현 패턴을 우선 참고한다.

## Testing

- 모든 신규 Use Case는 Unit Test를 작성한다.
- Repository 변경 시 Repository Test를 작성한다.
- API 변경 시 Integration Test를 추가한다.
```

---

# 17. AI에게 업무를 지시하는 방식

피해야 할 예:

```text
상품 관리 기능 만들어줘.
```

권장:

```text
catalog domain에 상품 등록 기능을 구현한다.

다음 규칙을 반드시 따른다.

1. ARCHITECTURE.md 준수
2. CODING_RULES.md 준수
3. order domain을 Reference Implementation으로 사용
4. Controller → Application → Domain → Infrastructure 구조 유지
5. 기존 공통 Exception Framework 사용
6. 신규 공통 Utility 생성 금지
7. Unit Test와 Integration Test 작성
8. Architecture Rule 위반 여부 확인
```

---

# 18. AI에게 설계 결정권을 과도하게 주지 않는다

AI에게 다음과 같은 질문을 매번 맡기지 않는 것이 좋다.

```text
어떤 Layer에 넣을까?
Exception 구조는 어떻게 할까?
Repository 구조는 어떻게 할까?
Transaction은 어디서 잡을까?
```

이런 결정은 프로젝트 초기에 사람이 고정한다.

AI는 그 결정 안에서 구현하도록 한다.

---

# 19. Domain 개발 순서

권장 예:

```text
Foundation
   ↓
Customer
   ↓
Catalog
   ↓
Pricing
   ↓
Inventory
   ↓
Promotion
   ↓
Cart
   ↓
Order
   ↓
Payment
   ↓
Delivery
   ↓
Return / Refund
   ↓
Settlement
```

실제 프로젝트에서는 병렬화할 수 있다.

---

# 20. Vertical Slice 개발

Domain마다 다음 사이클을 완료하고 넘어가는 방식이 좋다.

```text
Domain Design
   ↓
API Design
   ↓
Data Model
   ↓
Implementation
   ↓
Unit Test
   ↓
Integration Test
   ↓
Architecture Review
   ↓
Merge
```

CRUD를 전체 시스템에 먼저 뿌린 뒤 뒤늦게 비즈니스 로직을 채우는 방식은 권장하지 않는다.

---

# 21. Architecture Compliance

대형 프로젝트에서 문서만으로 아키텍처를 유지하기 어렵다.

가능하면 CI에서 자동 검증한다.

예:

```text
Controller → Repository 참조 금지
Domain → Infrastructure 참조 금지
Domain 간 직접 Repository 접근 금지
```

Java에서는 ArchUnit 같은 도구를 활용할 수 있다.

---

# 22. Code Review에서 확인할 항목

AI 생성 코드는 최소 다음 기준으로 검토한다.

```text
[ ] Architecture Boundary 위반 여부
[ ] Transaction Boundary 적절성
[ ] DB Lock 문제
[ ] N+1 Query
[ ] Exception 정책
[ ] Logging
[ ] Audit
[ ] Security
[ ] 개인정보 노출
[ ] Idempotency
[ ] Retry 안전성
[ ] Test Coverage
[ ] 성능 영향
```

---

# 23. Database 설계 원칙

## 권장

```text
PK 명확화
Business Key 분리
CreatedAt / UpdatedAt
Version Column
Audit Column
Index 정책
FK 정책
```

## 주의

대형 커머스에서 성능을 이유로 모든 FK를 제거하는 접근은 위험하다.

정합성과 운영 편의성을 함께 고려해야 한다.

---

# 24. 동시성 설계

특히 다음은 동시성 제어가 중요하다.

```text
재고
쿠폰
포인트
한정 판매
주문
결제
```

대표 전략:

- Optimistic Lock
- Pessimistic Lock
- Redis Distributed Lock
- Queue Serialization
- Atomic DB Update

Domain 성격에 따라 선택한다.

---

# 25. 재고 예시

잘못된 형태:

```sql
SELECT stock
FROM inventory;

stock = stock - 1;

UPDATE inventory;
```

동시 주문 시 문제가 발생한다.

예:

```sql
UPDATE inventory
SET available_qty = available_qty - :qty
WHERE product_id = :id
AND available_qty >= :qty;
```

영향 행 수를 기준으로 성공 여부를 판단하는 방식이 더 안전할 수 있다.

---

# 26. Observability

운영 단계에서 다음 세 가지를 반드시 연계한다.

```text
Logs
Metrics
Traces
```

대표 추적 흐름:

```text
API Request
  ↓ traceId
Order
  ↓
Inventory
  ↓
Payment
  ↓
Kafka
  ↓
Delivery
```

모든 서비스와 로그에서 동일 Trace ID를 추적할 수 있어야 한다.

---

# 27. 성능 테스트

대형 이커머스는 평균 TPS보다 이벤트 트래픽이 중요하다.

예:

```text
타임세일
쿠폰 오픈
라이브커머스
대형 프로모션
신상품 출시
```

테스트 항목:

```text
Normal Load
Peak Load
Spike Load
Soak Test
Failure Test
```

---

# 28. 장애 테스트

반드시 테스트할 시나리오:

```text
Payment API Timeout
Inventory Delay
Kafka 장애
Redis 장애
DB Failover
Search Cluster 장애
외부 배송 API 장애
```

시스템은 '정상 동작'보다 '부분 장애 상태'에서 어떻게 동작하는지가 중요하다.

---

# 29. CI/CD Quality Gate

권장 파이프라인:

```text
Compile
   ↓
Unit Test
   ↓
Static Analysis
   ↓
Architecture Test
   ↓
Security Scan
   ↓
Integration Test
   ↓
Container Build
   ↓
Deploy Test Environment
   ↓
Smoke Test
```

---

# 30. AI Agent 역할 분리

대형 프로젝트에서는 AI Agent 하나가 모든 역할을 수행하게 하기보다 역할을 분리하는 것이 좋다.

예:

```text
Architecture Agent
Backend Implementation Agent
Database Review Agent
Test Agent
Security Review Agent
Code Review Agent
Documentation Agent
```

단, 각 Agent가 서로 다른 아키텍처를 제안하지 않도록 동일한 규칙 문서를 기준으로 사용해야 한다.

---

# 31. AI Multi-Agent 운영 구조

```text
                   Architecture Rules
                          │
                          ▼
                     Orchestrator
                          │
        ┌─────────────────┼──────────────────┐
        │                 │                  │
        ▼                 ▼                  ▼
 Backend Agent       Test Agent        Review Agent
        │                 │                  │
        └─────────────────┼──────────────────┘
                          │
                          ▼
                    CI / Quality Gate
```

---

# 32. AI Context 관리

프로젝트가 커지면 AI가 전체 코드를 한 번에 이해하도록 기대하면 안 된다.

Context 구조를 계층화한다.

```text
Global
 ├─ Architecture
 ├─ Coding Rules
 └─ Common Policies

Domain
 ├─ Domain Model
 ├─ API
 ├─ Data Model
 └─ Business Rules

Task
 ├─ Requirement
 ├─ Target Files
 └─ Acceptance Criteria
```

AI에게 매 작업 시 필요한 범위만 제공하는 것이 좋다.

---

# 33. 문서 구조 권장

```text
/docs
│
├─ architecture
│  ├─ ARCHITECTURE.md
│  ├─ DOMAIN_MAP.md
│  └─ ADR/
│
├─ standards
│  ├─ CODING_RULES.md
│  ├─ API_RULES.md
│  ├─ DB_RULES.md
│  └─ TEST_RULES.md
│
├─ domains
│  ├─ customer.md
│  ├─ catalog.md
│  ├─ inventory.md
│  └─ order.md
│
└─ operations
   ├─ deployment.md
   ├─ monitoring.md
   └─ incident.md
```

---

# 34. ADR 사용

Architecture Decision Record를 적극 권장한다.

예:

```text
ADR-001 Modular Monolith 선택
ADR-002 Kafka 사용
ADR-003 Redis Cache 정책
ADR-004 Inventory Lock 전략
ADR-005 Saga 적용 기준
```

AI가 과거 설계 결정을 임의로 변경하지 않도록 하는 데 효과적이다.

---

# 35. Foundation Framework 완료 조건

다음 항목이 완료되면 업무 개발을 본격화할 수 있다.

## Architecture

```text
[ ] Domain Boundary
[ ] Layer Architecture
[ ] Dependency Rule
[ ] Transaction Rule
[ ] Integration Rule
```

## Common Framework

```text
[ ] API Response
[ ] Exception
[ ] Validation
[ ] Security
[ ] Database
[ ] Transaction
[ ] Logging
[ ] Audit
[ ] Messaging
[ ] External API
[ ] Batch
[ ] Test Framework
```

## Operations

```text
[ ] Build
[ ] CI
[ ] Container
[ ] Configuration
[ ] Logging
[ ] Metrics
[ ] Trace
```

---

# 36. Reference Implementation 완료 조건

```text
[ ] 실제 Domain Use Case 구현
[ ] API
[ ] Validation
[ ] Authorization
[ ] Transaction
[ ] Repository
[ ] External Integration
[ ] Event
[ ] Exception
[ ] Logging
[ ] Audit
[ ] Unit Test
[ ] Integration Test
[ ] Architecture Test
[ ] API Documentation
```

이 정도가 완료된 이후 Reference Implementation을 프로젝트 표준 예제로 지정하는 것이 좋다.

---

# 37. 업무 개발 시작 후 지켜야 할 원칙

매 Domain 개발 완료 시 다음을 확인한다.

```text
Architecture
  ↓
Implementation
  ↓
Test
  ↓
Review
  ↓
Architecture Compliance
  ↓
Merge
```

'일단 개발하고 마지막에 구조를 맞춘다'는 접근은 대규모 AI 개발에서 특히 위험하다.

---

# 38. 대형 프로젝트에서 피해야 할 패턴

## 38.1 God Common Module

모든 코드를 common에 넣는 구조.

## 38.2 Shared Database Everywhere

모든 Domain이 다른 Domain 테이블을 자유롭게 접근.

## 38.3 Generic Service Framework

```text
BaseService
GenericService
CommonService
```

등으로 모든 업무를 추상화.

## 38.4 AI 자유 설계

각 기능을 개발할 때마다 AI가 다른 구조를 선택.

## 38.5 Massive Prompt Development

전체 요구사항 수백 페이지를 AI에게 주고 전체 시스템을 한 번에 생성.

---

# 39. 권장 프로젝트 개발 로드맵

## Stage 1 — Foundation

```text
Architecture
Project Skeleton
Foundation Framework
CI/CD
Observability
```

## Stage 2 — Golden Path

```text
Customer
Catalog
Order Reference Implementation
```

## Stage 3 — Core Commerce

```text
Pricing
Promotion
Inventory
Cart
Order
Payment
```

## Stage 4 — Fulfillment

```text
Delivery
Return
Exchange
Refund
```

## Stage 5 — Business Operations

```text
Seller
Settlement
Admin
Customer Service
Reporting
```

## Stage 6 — Optimization

```text
Search
Recommendation
Caching
Performance
Cost Optimization
```

---

# 40. 프로젝트 초기 권장 산출물

최소 다음 문서를 프로젝트 초기에 만든다.

```text
01_ARCHITECTURE.md
02_DOMAIN_MAP.md
03_CODING_RULES.md
04_API_RULES.md
05_DATABASE_RULES.md
06_TRANSACTION_RULES.md
07_EVENT_RULES.md
08_SECURITY_RULES.md
09_TEST_RULES.md
10_AGENTS.md
```

그리고 실제 코드로:

```text
Foundation Framework
+
Reference Domain
```

을 만든다.

---

# 41. 핵심 원칙 요약

대형 이커머스 프로젝트의 성공적인 AI 개발 전략은 다음 한 문장으로 정리할 수 있다.

> **AI에게 시스템을 설계하게 하지 말고, 사람이 정의한 아키텍처와 Golden Path 안에서 AI가 빠르게 구현하게 한다.**

개발 순서는 다음이 가장 안정적이다.

```text
Architecture
    ↓
Engineering Rules
    ↓
Foundation Framework
    ↓
Reference Implementation
    ↓
AI Rules
    ↓
Domain Development
    ↓
Architecture Compliance
    ↓
Operations
```

AI는 개발 속도를 크게 높일 수 있지만, 엔터프라이즈 시스템에서 가장 중요한 것은 '코드 생성 속도'가 아니라 다음이다.

```text
Consistency
Maintainability
Observability
Testability
Security
Operability
```

따라서 대형 프로젝트에서는 AI를 자유롭게 코딩하는 도구가 아니라 **Architecture Guardrail 안에서 동작하는 고속 개발 Agent**로 운영하는 것이 바람직하다.

---

# 42. 프로젝트 착수용 최종 체크리스트

## Architecture

- [ ] Modular Monolith / Microservices 결정
- [ ] Domain Map 작성
- [ ] Layer Architecture 정의
- [ ] Dependency Rule 정의
- [ ] Transaction Boundary 정의
- [ ] Event 적용 기준 정의

## Foundation

- [ ] API Framework
- [ ] Exception Framework
- [ ] Security
- [ ] Database
- [ ] Transaction
- [ ] Logging
- [ ] Audit
- [ ] Cache
- [ ] Messaging
- [ ] External Integration
- [ ] Batch
- [ ] Test Framework

## Golden Path

- [ ] Reference Domain 선정
- [ ] End-to-End Use Case 구현
- [ ] Unit Test
- [ ] Integration Test
- [ ] Architecture Test

## AI Development

- [ ] AGENTS.md
- [ ] Architecture Rules
- [ ] Coding Rules
- [ ] Domain Rules
- [ ] AI Prompt Template
- [ ] Reference Implementation 명시

## CI/CD

- [ ] Build
- [ ] Unit Test
- [ ] Static Analysis
- [ ] Architecture Test
- [ ] Security Scan
- [ ] Integration Test
- [ ] Container Build
- [ ] Deployment

## Operations

- [ ] Structured Logging
- [ ] Metrics
- [ ] Distributed Trace
- [ ] Alert
- [ ] Audit
- [ ] Incident Runbook

---

## 마무리

대형 이커머스 시스템은 업무 기능 수가 많다는 것보다 **업무 간 상호작용과 상태 변화가 복잡하다는 점**이 더 어렵다.

특히 주문·재고·결제·배송·환불·정산은 서로 강하게 연결되어 있으면서도 장애 시 독립적으로 복구할 수 있어야 한다.

따라서 기반 프레임워크와 Reference Implementation은 단순 개발 편의 기능이 아니라 **프로젝트 전체의 기술적 일관성과 장기 유지보수를 보장하는 설계 자산**으로 취급해야 한다.

AI 개발에서는 이 역할이 더욱 중요하다.

AI가 빠르게 코드를 생성할수록 아키텍처 규칙과 자동 검증 체계가 강해야 하며, 이를 통해 수십 명 또는 수백 명의 개발자와 여러 AI Agent가 동시에 작업하더라도 하나의 시스템처럼 일관된 결과물을 유지할 수 있다.
