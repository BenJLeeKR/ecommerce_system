# WL-0014-2026-09-10-approved-baseline-alignment

- 상태: 완료
- 작업일: 2026-09-10
- 연결 Backlog/Planning/Analysis:
  - 기획자(사용자) 설계 및 정책 승인
- 관련 설계:
  - `docs/00_project/tech-stack-decision.md`
  - `docs/02_design/01_architecture/architecture-overview.md`
  - `docs/02_design/04_database/naming-conventions.md`

## 1. 목적
사용자가 승인한 정책(기술 스택, DB 네이밍 기준, DB 계정 권한 등)을 프로젝트 설계 문서들에 현재 승인된 기준으로 정합화하여 기록한다.

## 2. 수행 내용
- 기술 스택 결정 문서의 상태를 "초안 (Draft)"에서 "승인됨 (Approved)"으로 변경.
- 아키텍처 문서에서 공용 PostgreSQL 내 단일 Schema 테이블 예시를 접두어 없는 복수형 명칭(`users`, `orders`, `products` 등)으로 갱신하고, DB 접속 시 전용 최소 권한 계정 사용 원칙 추가.
- DB 네이밍 규약 문서에서 확정된 규칙(테이블명 복수형, 도메인 접두어 미사용)과 미결정 대기 항목을 분리.
- 문서들의 체크리스트를 업데이트하고 아직 확정되지 않은 항목은 `[ ]`로 유지.

## 3. 판단 및 결정
- 리뷰 도메인 관련 언급은 현재 PR에서 제외하며, 추후 별도 작업에서 처리하기로 결정함.
- 미결정 상태인 백업/장애 대응 및 일부 데이터베이스 정책(UUID, Enum 등)은 승인 완료되지 않았으므로 체크리스트와 문서 상태를 `Draft` 및 보류 상태로 남겨둠.

## 4. 변경 파일
- `docs/00_project/tech-stack-decision.md`
- `docs/02_design/01_architecture/architecture-overview.md`
- `docs/02_design/04_database/naming-conventions.md`
- `docs/05_worklog/WL-0014-2026-09-10-approved-baseline-alignment.md` (신규)
- `docs/05_worklog/README.md`

## 5. 검증 결과
- `git diff --check`를 통과함.
- 마크다운 문서들의 형식이 올바르며, 변경된 문서가 의도한 정책(복수형 테이블, 접두어 미사용, 최소 권한 계정 등)을 제대로 반영함.

## 6. 후속 작업
- 보류된 정책(UUID PK, Enum 문자열 처리 방식, 재고 TTL, 결제/PG 상세 규약 등)의 기획자 확인.
- MVP에서 제외된 리뷰 도메인 상세 정리 내용의 아키텍처 및 도메인 문서 반영.
