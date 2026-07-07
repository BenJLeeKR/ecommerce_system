# API 공통 규칙 (API Convention)

> 상태: 초안 (Draft) — 설계 승인자(기획자) 검토 필요
> 관련 문서: `docs/01_architecture/architecture-overview.md`, `docs/02_domain/domain-model.md`, `docs/03_database/naming-conventions.md`, `docs/04_database/database-design.md`
> 목적: 모든 API가 예외 없이 따를 공통 규칙을 먼저 정한다. `api-list.md`의 모든 API는 이 문서를 기준으로 설계되었다.

---

## 1. API URL 규칙

- 모든 API는 `/api/v1/` 로 시작한다. (버전을 명시해 향후 v2 전환 시 기존 클라이언트에 영향 없이 확장 가능)
- URL은 **명사(자원)** 로 구성하고, 동사를 쓰지 않는다. (예: `GET /api/v1/products` — O, `GET /api/v1/getProducts` — X)
- 여러 단어로 된 자원명은 **kebab-case**를 사용한다. (예: `/api/v1/product-options`)
- 목록은 복수형을 사용한다. (예: `/api/v1/orders`, 단건은 `/api/v1/orders/{orderId}`)
- 로그인한 본인의 정보를 다루는 API는 URL에 사용자 ID를 넣지 않고 `/api/v1/me/...` 형태를 사용한다. 어떤 회원인지는 인증 토큰에서 판별한다. (예: `GET /api/v1/me`, `GET /api/v1/me/addresses`)
- 관리자 전용 API는 반드시 `/api/v1/admin/...` 로 시작한다. 고객용 API와 URL 자체로 명확히 구분되게 한다.
- 상태 전이처럼 단순 CRUD로 표현하기 애매한 동작은 하위 행동 경로를 허용한다. (예: `POST /api/v1/orders/{orderId}/cancel`) 단, 이런 "행동형 URL"은 **위험도가 높거나 감사가 필요한 상태 변경**에 한해서만 사용하고 남용하지 않는다.

---

## 2. HTTP Method 사용 규칙

| Method | 용도 |
|---|---|
| `GET` | 조회 (목록/상세). 부작용 없음 |
| `POST` | 생성, 또는 단순 CRUD로 표현하기 어려운 행동(주문 취소, 결제 요청 등) 수행 |
| `PATCH` | 일부 필드 수정 |
| `PUT` | 사용하지 않음 (전체 교체 방식은 이번 프로젝트에서 필요성이 낮아 배제) |
| `DELETE` | 삭제 (실제 삭제/Soft Delete 여부는 `database-design.md`의 테이블별 삭제 정책을 따름) |

**중요한 원칙**: 주문(Order)·결제(Payment)·배송(Shipment)의 **상태값 변경은 `PATCH`로 상태 필드를 직접 수정하게 하지 않는다.** 대신 `POST /orders/{id}/cancel`, `PATCH /admin/orders/{id}/status`처럼 **의도가 분명한 개별 행동 API**로만 상태를 바꾼다. 임의의 상태로 마음대로 바꿀 수 있는 범용 API는 만들지 않는다. (`domain-model.md`의 상태 전이 규칙과 직결)

---

## 3. 공통 응답 포맷

모든 성공 응답은 아래 형태를 따른다.

```json
{
  "success": true,
  "data": { },
  "meta": { }
}
```

- `data`: 실제 응답 데이터 (목록이면 배열, 단건이면 객체)
- `meta`: 페이징 등 부가 정보가 있을 때만 포함 (7장 참고). 없으면 생략

---

## 4. 공통 에러 응답 포맷

모든 실패 응답은 아래 형태를 따른다.

```json
{
  "success": false,
  "error": {
    "code": "ORDER_STOCK_INSUFFICIENT",
    "message": "선택하신 옵션의 재고가 부족합니다.",
    "details": []
  }
}
```

- `code`: **대문자 스네이크케이스**, 도메인 접두어를 붙인다. (예: `AUTH_INVALID_CREDENTIALS`, `ORDER_ALREADY_CANCELED`, `PAYMENT_DUPLICATE_REQUEST`)
- `message`: 사용자에게 그대로 보여줘도 되는 한국어 메시지
- `details`: 필드별 상세 정보가 필요한 경우 배열로 채움 (11장 validation error 참고). 없으면 빈 배열 또는 생략

---

## 5. 상태 코드 규칙

| 상태 코드 | 의미 | 사용 상황 |
|---|---|---|
| `200 OK` | 성공 | 조회/수정/행동(cancel 등) 성공 |
| `201 Created` | 생성 성공 | `POST`로 새 자원 생성 성공 |
| `204 No Content` | 성공, 응답 본문 없음 | 삭제 성공 등 |
| `400 Bad Request` | 요청 형식 오류 | 필수값 누락, 형식 오류(validation) |
| `401 Unauthorized` | 인증 실패 | 토큰 없음/만료/유효하지 않음 |
| `403 Forbidden` | 권한 없음 | 인증은 됐지만 본인 소유가 아니거나 관리자 권한 필요 |
| `404 Not Found` | 대상 없음 | 존재하지 않거나 조회 불가능(숨김 등) 처리된 자원 |
| `409 Conflict` | 현재 상태에서 수행 불가 | 재고 부족, 이미 취소된 주문, 배송 시작 이후 취소 시도, 중복 결제 요청 등 **비즈니스 규칙 위반** 전반 |
| `500 Internal Server Error` | 서버 오류 | 예상치 못한 서버 내부 오류 |

> 단순화를 위해 `422 Unprocessable Entity`는 사용하지 않고, 입력 형식 문제는 `400`, 비즈니스 규칙(상태) 문제는 `409`로 통일한다.

---

## 6. 인증 헤더 규칙

- 인증이 필요한 모든 API는 `Authorization: Bearer {accessToken}` 헤더를 요구한다.
- **고객용 토큰과 관리자용 토큰은 완전히 분리**되어 있으며 서로 호환되지 않는다. 고객 토큰으로 `/api/v1/admin/...`에 접근하면 `403`을 반환한다.
- Access Token 만료 시 `POST /api/v1/auth/refresh`로 재발급받는다. (구체적 만료 시간은 `domain-model.md` "확인 필요" 보안 정책 항목과 함께 결정)
- 관리자 토큰에는 역할(권한) 정보가 포함되며, 관리자 전용 API는 서버에서 이 정보를 반드시 검증한다.

---

## 7. 페이징 규칙

- 목록 조회 API는 아래 쿼리 파라미터를 공통으로 사용한다.

| 파라미터 | 설명 | 기본값 |
|---|---|---|
| `page` | 페이지 번호 (1부터 시작) | `1` |
| `size` | 페이지당 항목 수 | `20` (최대값은 API별로 다를 수 있음, `api-list.md`에 명시) |

- 응답의 `meta`에는 아래 정보를 포함한다.

```json
"meta": {
  "page": 1,
  "size": 20,
  "totalCount": 134,
  "totalPages": 7
}
```

---

## 8. 정렬 규칙

- `sort` 쿼리 파라미터에 `{필드명}:{방향}` 형식을 사용한다. (방향은 `asc` 또는 `desc`)
- 여러 조건은 쉼표로 구분한다. (예: `sort=createdAt:desc,price:asc`)
- 정렬 가능한 필드는 API마다 미리 정해둔 목록으로 제한한다 (인덱스가 걸린 컬럼만 허용 — `database-design.md`의 Index 후보 참고). 목록에 없는 필드로 정렬을 요청하면 `400`을 반환한다.
- 기본 정렬은 별도 지정이 없으면 `createdAt:desc`(최신순)로 한다.

---

## 9. 검색 조건 규칙

- 단순 필터는 쿼리 파라미터로 전달한다. (예: `GET /api/v1/products?categoryId=...&status=ON_SALE`)
- 여러 값을 허용하는 필터는 쉼표로 구분한다. (예: `status=ON_SALE,HIDDEN`)
- 텍스트 검색은 `keyword` 파라미터를 사용하며, MVP에서는 상품명 대상 단순 포함 검색(대소문자 무관)으로 구현한다. (`project-scope.md`에서 "검토 필요"로 남긴 항목 — 검색 고도화는 2차 범위)
- 범위 검색(가격 등)은 `min{Field}` / `max{Field}` 형태를 사용한다. (예: `minPrice=10000&maxPrice=50000`)

---

## 10. 날짜/시간 포맷

- 모든 날짜/시간은 **ISO 8601, UTC 기준**으로 주고받는다. (예: `2026-07-07T10:00:00.000Z`)
- 프론트엔드에서 사용자의 로컬 시간대로 변환해 화면에 표시한다. 서버는 시간대 변환을 하지 않는다.
- 날짜만 필요한 값(예: 통계 조회 기간)은 `YYYY-MM-DD` 형식을 사용한다.

---

## 11. Validation Error 포맷

입력값 검증 실패(`400`)는 4장의 공통 에러 포맷을 그대로 사용하되, `details`에 필드별 오류를 채운다.

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력값을 확인해주세요.",
    "details": [
      { "field": "email", "message": "올바른 이메일 형식이 아닙니다." },
      { "field": "quantity", "message": "수량은 1 이상이어야 합니다." }
    ]
  }
}
```

- 여러 필드에 오류가 있으면 한 번에 모두 반환한다. (하나씩 고쳐서 재요청하게 하지 않는다)
- 필드명은 요청 바디의 필드명(camelCase)을 그대로 사용한다.

---

## 12. 승인 체크리스트

- [ ] URL/Method 규칙 승인
- [ ] 공통 응답/에러 포맷 승인
- [ ] 상태 코드 규칙 승인 (422 미사용 방침 포함)
- [ ] 인증 헤더 및 고객/관리자 토큰 분리 방식 승인
- [ ] 페이징/정렬/검색 규칙 승인
- [ ] 다음 단계(`api-list.md`에 따른 상세 API 구현) 진행 승인

> 승인 전까지는 초안(Draft) 상태이며, 코드는 작성하지 않는다.
