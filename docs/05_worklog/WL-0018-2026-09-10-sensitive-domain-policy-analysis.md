# WL-0018-2026-09-10-sensitive-domain-policy-analysis

- 상태: Completed
- 작성일: 2026-09-10
- 연결 Planning: `docs/03_planning/PL-0008-2026-09-09-mvp-scalability-guardrails.md`
- 연결 Analysis: `docs/04_analysis/AN-0006-2026-09-10-sensitive-domain-policy-decision-options.md`
- 연결 Backlog: 없음

## 1. 작업 내용

민감 도메인(주문, 결제, 재고)의 정책 결정 옵션과 인프라 체크리스트를 분석하여, 사용자 의사결정을 돕는 `AN-0006` 분석 문서를 신규 작성했습니다.
이 문서는 전체 설계 작업 착수에 앞서 반드시 확정되어야 하는 선결 조건(재고 예약 TTL, 재고 동시성·트랜잭션, 결제 PG 멱등성 및 실패 정책, DB 백업/복구 절차 확인)에 대한 대안 및 권장안을 다루고 있습니다.

## 2. 주요 결정 및 근거

- **새로운 인프라 배제**: Redis, Kafka, 외부 분산 락 등의 추가 도입 없이, 이미 승인된 단일 PostgreSQL 환경 내에서 조건부 원자 갱신(`UPDATE ... WHERE`) 방식을 통해 동시성을 해결하도록 권장안을 작성했습니다.
- **트랜잭션 분리**: 안정성을 위해 외부 PG 통신은 DB 트랜잭션 밖에서 수행하도록 트랜잭션 경계 설정안을 제시했습니다.
- **KST / UTC 병행 운용 방침 적용**: 재고 만료 등 시각 데이터 저장에는 UTC를, 상태 전환 판단 시에는 KST를 기준으로 하도록 원칙을 적용했습니다.

## 3. 검증 결과

- `AN-0006` 및 해당 Worklog 문서의 작성과 인덱스 링크(README)가 모두 KST 날짜 기준인 `2026-09-10`로 맞게 작성되었습니다.
- 문서 포맷팅 검증(`git diff --check`)을 통과했습니다.

## 4. 후속 작업

- 사용자 결정 표(AN-0006)에 대해 사용자(기획/설계 의사결정권자)의 최종 승인을 요청합니다.
- 승인이 완료된 이후 해당 정책들이 `architecture-overview.md` 등의 설계 문서에 반영되며, 본 코드를 구현하는 단계로 이행됩니다.

## 5. 변경 파일 목록

- `docs/04_analysis/AN-0006-2026-09-10-sensitive-domain-policy-decision-options.md` (신규 파일)
- `docs/04_analysis/README.md`
- `docs/05_worklog/WL-0018-2026-09-10-sensitive-domain-policy-analysis.md` (신규 파일)
- `docs/05_worklog/README.md`
