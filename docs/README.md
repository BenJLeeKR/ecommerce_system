# 이커머스 프로젝트 문서 지도

이 문서는 현재 유효한 프로젝트 문서를 빠르게 찾기 위한 시작점이다. 세부 작업 내용은 각 경로의 인덱스와 개별 문서에서 확인한다.

## 프로젝트와 거버넌스

- [프로젝트 범위](00_project/project-scope.md) — MVP 범위, 사용자 흐름, 성공 기준을 정의한다.
- [기술 스택 결정](00_project/tech-stack-decision.md) — 채택 기술과 선택 근거를 정의한다.
- [거버넌스](01_governance/README.md) — 작업, 품질, 배포, 민감 영역, 문서 관리 규칙을 제공한다.

## 현재 설계 기준

- [아키텍처](02_design/01_architecture/README.md) — 시스템 구조와 인프라·배포 방향을 정의한다.
- [도메인](02_design/02_domain/README.md) — 엔터티와 주문·결제·재고 상태 흐름을 정의한다.
- [API](02_design/03_api/README.md) — API 공통 규칙과 기능별 계약을 정의한다.
- [데이터베이스](02_design/04_database/README.md) — 테이블, 명명 규칙, 트랜잭션 정책을 정의한다.
- [화면](02_design/05_screen/README.md) — 고객·관리자 화면과 검수 포인트를 정의한다.

## 작업 관리

- [Planning](03_planning/README.md) — 큰 작업의 범위, 검증, 롤백 계획을 기록한다.
- [Analysis](04_analysis/README.md) — 조사 결과와 대안 비교 근거를 기록한다.
- [Worklog](05_worklog/README.md) — 실제 수행 작업과 검증 결과를 기록한다.
- [Backlog](06_backlog/README.md) — 앞으로 할 작업 후보와 우선순위를 관리한다.
- [Templates](07_templates/README.md) — Planning, Analysis, Worklog, Backlog의 표준 양식을 제공한다.

## 보관 및 참고

- [Archive](08_archive/README.md) — 현재 기준이 아닌 과거 설계 결정 이력을 보관한다.
- [Reference](99_reference/AI_Agent_Coding_Large_Commerce_Guide.md) — 대형 이커머스 AI 개발 참고 가이드를 제공한다.
- [Enterprise Reference](99_reference/Enterprise_ecommerce_AI_Backend_Guide.md) — 엔터프라이즈 이커머스 백엔드 참고 가이드를 제공한다.

## 문서 작성 흐름

새 작업은 Backlog에 등록하고, 조사와 큰 작업 계획이 필요하면 Analysis와 Planning을 작성한다. 수행 결과는 Worklog에 남기고, 현재 기준이 바뀌면 Design 또는 Governance 문서를 함께 갱신한다. 자세한 규칙은 [문서 관리 규칙](01_governance/document-management-rules.md)을 따른다.
