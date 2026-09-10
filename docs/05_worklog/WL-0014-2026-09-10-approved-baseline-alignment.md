# 작업 기록: 사용자 승인 완료 정책 정합화

- **Date:** 2026-09-10
- **Author:** Jules (AI Agent)
- **Status:** Completed

## 작업 목적
사용자가 승인한 정책(기술 스택, DB 네이밍 기준 등)을 프로젝트 설계 문서들에 현재 승인된 기준으로 정합화하여 기록합니다.

## 변경 사항
1. `docs/00_project/tech-stack-decision.md`
   - 기술 스택 결정 문서의 상태를 "초안 (Draft)"에서 "승인됨 (Approved)"으로 변경.
   - 설계 승인자 검토 완료, 최종 스택 확정 승인 항목 체크(`[x]`).

2. `docs/02_design/01_architecture/architecture-overview.md`
   - 공용 PostgreSQL 내 단일 Schema 테이블 예시를 접두어 없는 복수형 명칭(`users`, `orders`, `products` 등)으로 갱신.
   - 도메인 간 조인 방지 규칙 등에서 `order_*`와 같은 기존 표기를 규칙에 맞는 복수형 명칭으로 일괄 정정.
   - 아직 완전히 결정되지 않은 인프라(백업/장애 대응) 및 데이터베이스 상세 정책은 결정 대기 상태(`[ ]`)로 유지, 문서 전체 상태는 `Draft` 유지.

3. `docs/02_design/04_database/naming-conventions.md`
   - 확정된 규칙(테이블명 복수형, 도메인 접두어 미사용)과 미결정 대기 항목(UUID PK 사용, Enum 문자열 저장 방식 등)을 분리하여 명시.
   - 체크리스트에서 미결정 항목은 `[ ]`로 원복, 문서 전체 상태는 `Draft` 유지.

## 비고 / 특이사항
- 리뷰 도메인 관련 언급은 현재 PR에서 제외하며, 다음 별도 작업에서 처리할 예정.
- 본 PR은 인프라/코드 변경 없이 정책이 반영된 마크다운 문서 수정만 포함함.