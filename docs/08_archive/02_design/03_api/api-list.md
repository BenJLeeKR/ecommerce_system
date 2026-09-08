# API 목록 (API List)

> 상태: 초안 (Draft) — 설계 승인자(기획자) 검토 필요
> 관련 문서: `docs/03_api/api-convention.md` (모든 API가 이 규칙을 따름), `docs/02_domain/domain-model.md`, `docs/04_database/database-design.md`
> 표시 규칙: 🔴 = 주문/결제/재고 관련 **위험 API** (별도 신중한 검토·테스트 필요), 🔒 = **관리자 권한 필수** API

각 API는 **Method / URL / 설명 / 인증 필요 여부 / 권한 / 요청 파라미터 / 응답 요약 / 주요 실패 케이스** 순으로 정리했다.

---

## 1. Auth API (인증)

### 1-1. 회원가입
- **Method/URL**: `POST /api/v1/auth/signup`
- **설명**: 일반 고객 회원가입
- **인증**: 불필요
- **권한**: 없음
- **요청**: `email`, `password`, `name`, `phoneNumber`
- **응답 요약**: 생성된 회원 기본정보 (비밀번호 제외)
- **주요 실패 케이스**: 이메일 중복(`409 AUTH_EMAIL_ALREADY_EXISTS`), 입력값 오류(`400`)

### 1-2. 로그인
- **Method/URL**: `POST /api/v1/auth/login`
- **설명**: 이메일/비밀번호 로그인
- **인증**: 불필요
- **권한**: 없음
- **요청**: `email`, `password`
- **응답 요약**: `accessToken`, `refreshToken`, 회원 기본정보
- **주요 실패 케이스**: 자격증명 불일치(`401 AUTH_INVALID_CREDENTIALS`), 잠긴 계정(`403 AUTH_ACCOUNT_LOCKED`), 탈퇴한 계정(`403 AUTH_ACCOUNT_WITHDRAWN`)

### 1-3. 토큰 재발급
- **Method/URL**: `POST /api/v1/auth/refresh`
- **설명**: 만료된 Access Token을 Refresh Token으로 재발급
- **인증**: Refresh Token 자체가 인증 수단
- **권한**: 없음
- **요청**: `refreshToken`
- **응답 요약**: 새 `accessToken`
- **주요 실패 케이스**: 토큰 만료/위조(`401 AUTH_INVALID_REFRESH_TOKEN`)

### 1-4. 로그아웃
- **Method/URL**: `POST /api/v1/auth/logout`
- **설명**: 현재 Refresh Token 무효화
- **인증**: 필요
- **권한**: 본인
- **요청**: 없음 (토큰은 헤더로 전달)
- **응답 요약**: 처리 완료 메시지
- **주요 실패 케이스**: 인증되지 않음(`401`)

### 1-5. 비밀번호 재설정 요청
- **Method/URL**: `POST /api/v1/auth/password/reset-request`
- **설명**: 비밀번호 재설정 메일 발송
- **인증**: 불필요
- **권한**: 없음
- **요청**: `email`
- **응답 요약**: 처리 접수 메시지 (이메일 존재 여부와 무관하게 동일 응답 — 계정 존재 여부 노출 방지)
- **주요 실패 케이스**: 과도한 요청 반복(`429`, ➕ 확인 필요: 구체적 제한 정책)

### 1-6. 비밀번호 재설정
- **Method/URL**: `POST /api/v1/auth/password/reset`
- **설명**: 재설정 토큰으로 새 비밀번호 설정
- **인증**: 재설정 토큰(이메일 링크)이 인증 수단
- **권한**: 없음
- **요청**: `resetToken`, `newPassword`
- **응답 요약**: 처리 완료 메시지
- **주요 실패 케이스**: 토큰 만료/무효(`401 AUTH_INVALID_RESET_TOKEN`)

### 1-7. 관리자 로그인 🔒
- **Method/URL**: `POST /api/v1/admin/auth/login`
- **설명**: 관리자 전용 로그인 (고객 로그인과 완전히 분리된 별도 엔드포인트)
- **인증**: 불필요
- **권한**: 관리자 계정만 시도 가능 (일반 회원 계정으로는 로그인 자체가 불가)
- **요청**: `loginId`, `password`
- **응답 요약**: 관리자용 `accessToken`, `refreshToken`
- **주요 실패 케이스**: 자격증명 불일치(`401`), 비활성화 계정(`403 ADMIN_ACCOUNT_DISABLED`)

---

## 2. User API (회원)

### 2-1. 내 정보 조회
- **Method/URL**: `GET /api/v1/me`
- **설명**: 로그인한 회원 본인 정보 조회
- **인증**: 필요
- **권한**: 본인
- **요청**: 없음
- **응답 요약**: 이름, 이메일, 연락처, 가입일 등
- **주요 실패 케이스**: 인증되지 않음(`401`)

### 2-2. 내 정보 수정
- **Method/URL**: `PATCH /api/v1/me`
- **설명**: 이름/연락처 등 일부 정보 수정
- **인증**: 필요
- **권한**: 본인
- **요청**: `name`, `phoneNumber` (일부만 전달 가능)
- **응답 요약**: 수정된 회원 정보
- **주요 실패 케이스**: 입력값 오류(`400`)

### 2-3. 회원 탈퇴
- **Method/URL**: `POST /api/v1/me/withdraw`
- **설명**: 회원 탈퇴 처리 (즉시 삭제가 아니라 `WITHDRAWN` 상태 전환)
- **인증**: 필요
- **권한**: 본인
- **요청**: 없음 (필요 시 탈퇴 사유)
- **응답 요약**: 처리 완료 메시지
- **주요 실패 케이스**: 진행 중인 주문이 있는 경우 처리 방식(`409`, ➕ 확인 필요 — 탈퇴 제한 여부 정책 미정)

### 2-4. 배송지 목록 조회
- **Method/URL**: `GET /api/v1/me/addresses`
- **설명**: 등록된 배송지 목록
- **인증**: 필요
- **권한**: 본인
- **요청**: 없음
- **응답 요약**: 배송지 배열
- **주요 실패 케이스**: 없음 (없으면 빈 배열)

### 2-5. 배송지 등록
- **Method/URL**: `POST /api/v1/me/addresses`
- **설명**: 새 배송지 등록
- **인증**: 필요
- **권한**: 본인
- **요청**: `recipientName`, `phoneNumber`, `postalCode`, `addressLine1`, `addressLine2`, `isDefault`
- **응답 요약**: 생성된 배송지
- **주요 실패 케이스**: 입력값 오류(`400`)

### 2-6. 배송지 수정
- **Method/URL**: `PATCH /api/v1/me/addresses/{addressId}`
- **설명**: 배송지 정보 수정
- **인증**: 필요
- **권한**: 본인 소유 배송지만
- **요청**: 수정할 필드 일부
- **응답 요약**: 수정된 배송지
- **주요 실패 케이스**: 타인 배송지 접근(`403`), 존재하지 않음(`404`)

### 2-7. 배송지 삭제
- **Method/URL**: `DELETE /api/v1/me/addresses/{addressId}`
- **설명**: 배송지 삭제 (Soft Delete)
- **인증**: 필요
- **권한**: 본인 소유 배송지만
- **요청**: 없음
- **응답 요약**: `204 No Content`
- **주요 실패 케이스**: 타인 배송지 접근(`403`), 존재하지 않음(`404`)

---

## 3. Product API (상품 — 고객 조회용, 등록/수정은 10장 Admin API 참고)

### 3-1. 상품 목록 조회
- **Method/URL**: `GET /api/v1/products`
- **설명**: 판매중 상품 목록 조회 (페이징/정렬/필터/키워드검색)
- **인증**: 불필요
- **권한**: 없음
- **요청**: `page`, `size`, `categoryId`, `keyword`, `minPrice`, `maxPrice`, `sort` (허용: `createdAt`, `basePrice`)
- **응답 요약**: 상품 요약 목록(이름, 대표이미지, 가격, 상태) + 페이징 메타
- **주요 실패 케이스**: 잘못된 정렬 필드(`400`)

### 3-2. 상품 상세 조회
- **Method/URL**: `GET /api/v1/products/{productId}`
- **설명**: 상품 상세 정보, 옵션 목록, 이미지 목록 포함
- **인증**: 불필요
- **권한**: 없음
- **요청**: 없음
- **응답 요약**: 상품 상세 + 옵션별 재고 상태(`ACTIVE`/`SOLD_OUT`/`HIDDEN`) + 이미지 목록
- **주요 실패 케이스**: 존재하지 않거나 숨김/단종 처리됨(`404 PRODUCT_NOT_FOUND`)

### 3-3. 상품 옵션 목록 조회
- **Method/URL**: `GET /api/v1/products/{productId}/options`
- **설명**: 특정 상품의 옵션 조합 목록 (재고 상태 포함)
- **인증**: 불필요
- **권한**: 없음
- **요청**: 없음
- **응답 요약**: 옵션명, 추가금액, 상태
- **주요 실패 케이스**: 상품 없음(`404`)

---

## 4. Category API (카테고리 — 고객 조회용, 관리는 10장 Admin API 참고)

### 4-1. 카테고리 트리 조회
- **Method/URL**: `GET /api/v1/categories`
- **설명**: 전체 카테고리를 상위-하위 구조로 조회
- **인증**: 불필요
- **권한**: 없음
- **요청**: 없음
- **응답 요약**: 계층형 카테고리 목록
- **주요 실패 케이스**: 없음

### 4-2. 카테고리별 상품 조회
- **Method/URL**: `GET /api/v1/categories/{categoryId}/products`
- **설명**: 특정 카테고리에 속한 상품 목록
- **인증**: 불필요
- **권한**: 없음
- **요청**: `page`, `size`, `sort`
- **응답 요약**: 상품 요약 목록 + 페이징 메타
- **주요 실패 케이스**: 카테고리 없음(`404`)

---

## 5. Cart API (장바구니 — 고객 전용, 본인 것만)

### 5-1. 장바구니 조회
- **Method/URL**: `GET /api/v1/cart`
- **설명**: 내 장바구니 항목 조회
- **인증**: 필요
- **권한**: 본인
- **요청**: 없음
- **응답 요약**: 담긴 항목 목록(상품/옵션/수량/현재가격), 항목별 현재 재고상태 참고 표시
- **주요 실패 케이스**: 없음 (비어있으면 빈 배열)

### 5-2. 장바구니에 담기
- **Method/URL**: `POST /api/v1/cart/items`
- **설명**: 상품 옵션을 장바구니에 담기
- **인증**: 필요
- **권한**: 본인
- **요청**: `productOptionId`, `quantity`
- **응답 요약**: 추가된 장바구니 항목
- **주요 실패 케이스**: 존재하지 않는 옵션(`404`), 이미 담긴 옵션이면 수량 합산 처리(에러 아님). **참고**: 품절 옵션이어도 담기 자체는 허용되며, 실제 구매 가능 여부는 주문 생성 시점에 확인한다 (`domain-model.md` Cart 도메인 규칙)

### 5-3. 장바구니 항목 수량 변경
- **Method/URL**: `PATCH /api/v1/cart/items/{cartItemId}`
- **설명**: 담긴 항목의 수량 변경
- **인증**: 필요
- **권한**: 본인 소유 항목만
- **요청**: `quantity`
- **응답 요약**: 수정된 항목
- **주요 실패 케이스**: 타인 항목 접근(`403`), 존재하지 않음(`404`)

### 5-4. 장바구니 항목 삭제
- **Method/URL**: `DELETE /api/v1/cart/items/{cartItemId}`
- **설명**: 담긴 항목 제거
- **인증**: 필요
- **권한**: 본인 소유 항목만
- **요청**: 없음
- **응답 요약**: `204 No Content`
- **주요 실패 케이스**: 타인 항목 접근(`403`), 존재하지 않음(`404`)

### 5-5. 장바구니 비우기
- **Method/URL**: `DELETE /api/v1/cart`
- **설명**: 장바구니 전체 비우기
- **인증**: 필요
- **권한**: 본인
- **요청**: 없음
- **응답 요약**: `204 No Content`
- **주요 실패 케이스**: 없음

---

## 6. Order API (주문) 🔴 위험 API

> 이 그룹의 모든 API는 재고/결제와 직결되는 위험 영역이다. 구현 시 `docs/rules-sensitive-domain.md`와 `docs/02_domain/domain-model.md` 3~9장의 상태 흐름을 반드시 그대로 따른다.

### 6-1. 주문 생성 🔴
- **Method/URL**: `POST /api/v1/orders`
- **설명**: 장바구니 또는 즉시구매 항목으로 주문 생성. **이 시점에 재고가 임시 예약(HOLD)된다**
- **인증**: 필요
- **권한**: 본인
- **요청**: `items[]` (`productOptionId`, `quantity`) 또는 `cartItemIds[]`, `addressId` 또는 직접입력 배송지(`recipientName`,`phoneNumber`,`postalCode`,`addressLine1`,`addressLine2`)
- **응답 요약**: 생성된 주문(`status: PENDING`), 예약된 재고 정보
- **주요 실패 케이스**: 재고 부족(`409 ORDER_STOCK_INSUFFICIENT`), 존재하지 않거나 판매중지된 옵션(`404`/`409 ORDER_OPTION_UNAVAILABLE`), 배송지 누락(`400`)

### 6-2. 내 주문 목록 조회
- **Method/URL**: `GET /api/v1/orders`
- **설명**: 본인 주문 목록 (상태별 필터, 페이징)
- **인증**: 필요
- **권한**: 본인
- **요청**: `page`, `size`, `status`, `sort`(`createdAt`만 허용)
- **응답 요약**: 주문 요약 목록 + 페이징 메타
- **주요 실패 케이스**: 없음

### 6-3. 주문 상세 조회
- **Method/URL**: `GET /api/v1/orders/{orderId}`
- **설명**: 주문 상세(주문상품, 배송지, 결제 이력 요약, 배송상태)
- **인증**: 필요
- **권한**: 본인 소유 주문만
- **요청**: 없음
- **응답 요약**: 주문 상세 전체
- **주요 실패 케이스**: 타인 주문 접근(`403`), 존재하지 않음(`404`)

### 6-4. 주문 취소 🔴
- **Method/URL**: `POST /api/v1/orders/{orderId}/cancel`
- **설명**: 배송 시작 전 주문 취소. 결제가 있었다면 결제취소(환불)도 함께 트리거됨
- **인증**: 필요
- **권한**: 본인 소유 주문만
- **요청**: 없음 (취소 사유 선택 입력 가능)
- **주요 실패 케이스**: 이미 배송 시작됨(`409 ORDER_CANCEL_NOT_ALLOWED_AFTER_SHIPPING`, `domain-model.md` 9장), 이미 취소됨(`409 ORDER_ALREADY_CANCELED`)

### 6-5. 결제 실패 주문 재결제 시도 🔴
- **Method/URL**: `POST /api/v1/orders/{orderId}/retry-payment`
- **설명**: `PAYMENT_FAILED` 상태 주문에 대해 재고를 재예약하고 새 결제 시도를 생성
- **인증**: 필요
- **권한**: 본인 소유 주문만
- **요청**: `paymentMethod`
- **응답 요약**: 새 결제 시도 정보 (성공 시 `PENDING`으로 전환)
- **주요 실패 케이스**: 재고 소진으로 재예약 실패(`409 ORDER_STOCK_INSUFFICIENT` → 이 경우 주문은 `CANCELED`로 전환됨), 이미 결제완료된 주문(`409 ORDER_ALREADY_PAID`), 취소된 주문(`409`)

---

## 7. Payment API (결제) 🔴 위험 API

### 7-1. 결제 요청 생성 🔴
- **Method/URL**: `POST /api/v1/orders/{orderId}/payments`
- **설명**: 결제 승인 요청 (PG로 전달). 고유 멱등키가 함께 발급된다
- **인증**: 필요
- **권한**: 본인 소유 주문만
- **요청**: `paymentMethod`
- **응답 요약**: 결제 시도 정보, PG 결제창 연동에 필요한 값(리다이렉트 URL 등)
- **주요 실패 케이스**: 이미 결제완료된 주문(`409 PAYMENT_ALREADY_APPROVED`), 재고 예약 만료(`409 ORDER_RESERVATION_EXPIRED`)

### 7-2. PG 콜백 수신 🔴
- **Method/URL**: `POST /api/v1/payments/webhook`
- **설명**: PG사가 결제 결과를 서버-서버로 통보하는 콜백. **결제 결과의 최종 확정 기준**(`domain-model.md` 8장)
- **인증**: 사용자 인증 아님 — PG 고유 서명 검증으로 대체
- **권한**: 없음 (PG만 호출)
- **요청**: PG사 콜백 규격에 따름 (거래번호, 승인/실패 결과 등)
- **응답 요약**: 수신 확인 응답
- **주요 실패 케이스**: 서명 불일치/위조 의심(`401`/`403`), **중복 콜백**은 오류가 아니라 정상 응답하되 실제 처리는 생략(멱등 처리, `domain-model.md` 8장)

### 7-3. 결제 이력 조회
- **Method/URL**: `GET /api/v1/orders/{orderId}/payments`
- **설명**: 해당 주문의 모든 결제 시도 이력(재시도 포함) 조회
- **인증**: 필요
- **권한**: 본인 소유 주문 또는 관리자
- **요청**: 없음
- **응답 요약**: 결제 시도 목록(상태, 시도시각, 실패사유 등)
- **주요 실패 케이스**: 타인 주문 접근(`403`)

---

## 8. Shipment API (배송)

### 8-1. 배송 상태 조회
- **Method/URL**: `GET /api/v1/orders/{orderId}/shipment`
- **설명**: 주문의 배송 준비/배송중/배송완료 상태 조회
- **인증**: 필요
- **권한**: 본인 소유 주문만
- **요청**: 없음
- **응답 요약**: 배송상태, 택배사명, 운송장번호(있으면), 배송 시작/완료 시각
- **주요 실패 케이스**: 아직 결제 전이라 배송 정보 없음(`404 SHIPMENT_NOT_FOUND`), 타인 주문 접근(`403`)

> 배송 시작/완료 처리(상태 변경)는 고객이 아니라 관리자만 수행하므로 10장 Admin API를 참고한다.

---

## 9. Review API (리뷰) — 2차 고도화 대상

> `project-scope.md`에 따라 **MVP 범위가 아니다.** API 구조만 미리 정의하며, 실제 구현은 별도 승인 후 진행한다.

### 9-1. 리뷰 목록 조회
- **Method/URL**: `GET /api/v1/products/{productId}/reviews`
- **설명**: 특정 상품의 리뷰 목록
- **인증**: 불필요
- **권한**: 없음
- **요청**: `page`, `size`, `sort`(`createdAt`,`rating`)
- **응답 요약**: 리뷰 목록 + 페이징 메타
- **주요 실패 케이스**: 상품 없음(`404`)

### 9-2. 리뷰 작성
- **Method/URL**: `POST /api/v1/products/{productId}/reviews`
- **설명**: 구매 확정(배송완료) 상품에 대한 리뷰 작성
- **인증**: 필요
- **권한**: 본인, 해당 상품의 실제 구매(배송완료) 이력 필요
- **요청**: `orderItemId`, `rating`, `content`
- **응답 요약**: 생성된 리뷰
- **주요 실패 케이스**: 구매 이력 없음(`403 REVIEW_PURCHASE_NOT_VERIFIED`), 중복 작성(`409 REVIEW_ALREADY_EXISTS`)

### 9-3. 리뷰 수정
- **Method/URL**: `PATCH /api/v1/reviews/{reviewId}`
- **설명**: 본인이 작성한 리뷰 수정
- **인증**: 필요
- **권한**: 본인 작성 리뷰만
- **요청**: `rating`, `content`
- **응답 요약**: 수정된 리뷰
- **주요 실패 케이스**: 타인 리뷰 접근(`403`)

### 9-4. 리뷰 삭제
- **Method/URL**: `DELETE /api/v1/reviews/{reviewId}`
- **설명**: 리뷰 삭제 (Soft Delete)
- **인증**: 필요
- **권한**: 본인 작성자 또는 관리자
- **요청**: 없음
- **응답 요약**: `204 No Content`
- **주요 실패 케이스**: 타인 리뷰 접근(`403`, 관리자 제외)

---

## 10. Admin API (관리자) 🔒 전체 관리자 권한 필수

> 이 그룹의 **모든 API는 예외 없이 관리자 인증 + 관리자 권한이 필요**하다. 고객 토큰으로는 어떤 Admin API도 호출할 수 없다 (`api-convention.md` 6장). 주문/결제/재고와 관련된 항목은 🔴 표시를 추가로 병기한다.

### 10-1. 상품 관리

#### 상품 목록 조회 (관리자용) 🔒
- **Method/URL**: `GET /api/v1/admin/products`
- **설명**: 숨김/단종 포함 전체 상품 목록 조회
- **인증**: 필요 / **권한**: 관리자
- **요청**: `page`, `size`, `status`, `categoryId`, `keyword`
- **응답 요약**: 상품 목록(모든 상태 포함) + 페이징 메타
- **주요 실패 케이스**: 관리자 권한 없음(`403`)

#### 상품 등록 🔒
- **Method/URL**: `POST /api/v1/admin/products`
- **설명**: 신규 상품 등록 (옵션/이미지 포함 가능)
- **인증**: 필요 / **권한**: 관리자
- **요청**: `name`, `description`, `categoryId`, `basePrice`, `options[]`(옵션명,추가금액,초기재고), `images[]`
- **응답 요약**: 생성된 상품 상세
- **주요 실패 케이스**: 입력값 오류(`400`), 존재하지 않는 카테고리(`404`)

#### 상품 수정 🔒
- **Method/URL**: `PATCH /api/v1/admin/products/{productId}`
- **설명**: 상품 기본정보 수정 (가격, 설명, 카테고리 등)
- **인증**: 필요 / **권한**: 관리자
- **요청**: 수정할 필드 일부
- **응답 요약**: 수정된 상품
- **주요 실패 케이스**: 존재하지 않음(`404`)

#### 상품 상태 변경 🔒
- **Method/URL**: `PATCH /api/v1/admin/products/{productId}/status`
- **설명**: 판매중/숨김/단종 상태 전환 (하드 삭제 대신 사용, `database-design.md` 참고)
- **인증**: 필요 / **권한**: 관리자
- **요청**: `status`(`ON_SALE`/`HIDDEN`/`DISCONTINUED`)
- **응답 요약**: 변경된 상품 상태
- **주요 실패 케이스**: 허용되지 않는 상태값(`400`)

#### 상품 옵션 추가 🔒
- **Method/URL**: `POST /api/v1/admin/products/{productId}/options`
- **설명**: 상품에 옵션 조합 추가
- **인증**: 필요 / **권한**: 관리자
- **요청**: `optionName`, `additionalPrice`, `initialQuantity`
- **응답 요약**: 생성된 옵션 + 초기 재고 레코드
- **주요 실패 케이스**: 동일 옵션 중복(`409 PRODUCT_OPTION_DUPLICATE`, `database-design.md` unique 제약)

#### 상품 옵션 수정 🔒
- **Method/URL**: `PATCH /api/v1/admin/product-options/{optionId}`
- **설명**: 옵션 가격/상태 수정 (재고 수량은 아래 재고 API로 별도 처리)
- **인증**: 필요 / **권한**: 관리자
- **요청**: `additionalPrice`, `status`
- **응답 요약**: 수정된 옵션
- **주요 실패 케이스**: 존재하지 않음(`404`)

### 10-2. 재고 관리 🔴

#### 재고 수량 조정 🔒 🔴
- **Method/URL**: `PATCH /api/v1/admin/inventory/{optionId}`
- **설명**: 입고/조정 등으로 총 재고 수량을 변경. **위험 API — 반드시 예약중인 수량을 고려한 검증 필요**
- **인증**: 필요 / **권한**: 관리자
- **요청**: `quantityChange` (증감값) 또는 `totalQuantity`(절대값, 설계 시 하나로 확정)
- **응답 요약**: 변경된 재고 현황(총재고/예약중/가용재고)
- **주요 실패 케이스**: 변경 결과 재고가 음수가 되는 경우(`400`), 예약중인 수량보다 적은 총재고로 낮추려는 시도(`409 INVENTORY_ADJUSTMENT_CONFLICT`)

### 10-3. 카테고리 관리

#### 카테고리 등록/수정/삭제 🔒
- **Method/URL**: `POST /api/v1/admin/categories`, `PATCH /api/v1/admin/categories/{categoryId}`, `DELETE /api/v1/admin/categories/{categoryId}`
- **설명**: 카테고리 CRUD
- **인증**: 필요 / **권한**: 관리자
- **요청**: `name`, `parentId`, `displayOrder`
- **응답 요약**: 생성/수정된 카테고리, 삭제는 `204`
- **주요 실패 케이스**: 소속 상품이 있는 카테고리 삭제 시도(`409`, ➕ 확인 필요 — `domain-model.md`에서 정책 미확정)

### 10-4. 주문 관리 🔴

#### 전체 주문 목록 조회 🔒 🔴
- **Method/URL**: `GET /api/v1/admin/orders`
- **설명**: 전체 회원의 주문을 상태/기간별로 조회
- **인증**: 필요 / **권한**: 관리자
- **요청**: `page`, `size`, `status`, `fromDate`, `toDate`, `sort`
- **응답 요약**: 주문 목록 + 페이징 메타
- **주요 실패 케이스**: 없음

#### 주문 상세 조회 🔒 🔴
- **Method/URL**: `GET /api/v1/admin/orders/{orderId}`
- **설명**: 특정 주문의 전체 상세(결제 이력, 배송 상태 포함) 조회
- **인증**: 필요 / **권한**: 관리자
- **요청**: 없음
- **응답 요약**: 주문 상세 전체
- **주요 실패 케이스**: 존재하지 않음(`404`)

#### 주문 상태 변경 🔒 🔴
- **Method/URL**: `PATCH /api/v1/admin/orders/{orderId}/status`
- **설명**: 결제완료 → 배송준비중 전환 등, `domain-model.md` 3장에 정의된 허용 전이만 수행
- **인증**: 필요 / **권한**: 관리자
- **요청**: `status`(다음 상태)
- **응답 요약**: 변경된 주문 상태
- **주요 실패 케이스**: 허용되지 않는 상태 전환 시도(`409 ORDER_INVALID_STATUS_TRANSITION`)

#### 관리자에 의한 주문 취소 🔒 🔴
- **Method/URL**: `POST /api/v1/admin/orders/{orderId}/cancel`
- **설명**: 관리자가 주문을 취소 처리 (결제취소/환불 포함, 배송 오류 회수 등 예외 상황용)
- **인증**: 필요 / **권한**: 관리자
- **요청**: `reason`
- **응답 요약**: 취소 처리된 주문
- **주요 실패 케이스**: 배송완료 후 취소 시도(`409`), 이미 취소됨(`409`)

### 10-5. 배송 관리

#### 배송 시작 처리 🔒
- **Method/URL**: `PATCH /api/v1/admin/shipments/{shipmentId}/start`
- **설명**: 배송 준비중 → 배송중 전환, 운송장번호 입력 (MVP는 수동 입력)
- **인증**: 필요 / **권한**: 관리자
- **요청**: `carrierName`, `trackingNumber`
- **응답 요약**: 변경된 배송 상태
- **주요 실패 케이스**: 결제 미완료 주문에 대한 시도(`409`), 이미 배송중/완료(`409`)

#### 배송 완료 처리 🔒
- **Method/URL**: `PATCH /api/v1/admin/shipments/{shipmentId}/complete`
- **설명**: 배송중 → 배송완료 전환
- **인증**: 필요 / **권한**: 관리자
- **요청**: 없음
- **응답 요약**: 변경된 배송 상태
- **주요 실패 케이스**: 배송중 상태가 아닌 경우(`409`)

### 10-6. 결제 관리 🔴

#### 전체 결제 내역 조회 🔒 🔴
- **Method/URL**: `GET /api/v1/admin/payments`
- **설명**: 전체 결제 시도/승인/실패 이력 조회
- **인증**: 필요 / **권한**: 관리자
- **요청**: `page`, `size`, `status`, `fromDate`, `toDate`
- **응답 요약**: 결제 목록 + 페이징 메타
- **주요 실패 케이스**: 없음

#### 결제 취소(환불) 처리 🔒 🔴
- **Method/URL**: `POST /api/v1/admin/payments/{paymentId}/cancel`
- **설명**: 승인된 결제를 취소(환불)한다. **가장 민감한 API 중 하나 — 반드시 PG 환불 연동과 함께 트랜잭션으로 처리**
- **인증**: 필요 / **권한**: 관리자
- **요청**: `reason`
- **응답 요약**: 취소 처리된 결제 정보
- **주요 실패 케이스**: 이미 취소됨(`409 PAYMENT_ALREADY_CANCELED`), PG 환불 자체가 실패(`502`/`500`, 이 경우 결제 상태를 임의로 취소 처리하지 않고 재시도/수동 확인 절차로 안내)

---

## 11. 승인 체크리스트

- [ ] Auth/User API 승인
- [ ] Product/Category/Cart API 승인
- [ ] Order/Payment/Shipment API 🔴 승인 (특히 상태 전이, 실패 케이스)
- [ ] Review API 구조 승인 (MVP 미구현 확인)
- [ ] Admin API 🔒 전체 권한 검증 방식 승인
- [ ] ➕ 확인 필요 항목 일괄 검토 (탈퇴 제한, 비밀번호 재설정 요청 제한, 카테고리 삭제 시 소속상품 처리, 재고 조정 API 파라미터 방식)
- [ ] 다음 단계(Prisma schema / NestJS 모듈 구현) 진행 승인

> 승인 전까지는 초안(Draft) 상태이며, 코드는 작성하지 않는다.
