# 이커머스 프로젝트 — 공통 에이전트 작업 지도

이 문서는 Jules와 Claude Code를 포함한 모든 실행 에이전트의 짧은 진입점이다. 공통 핵심 규칙의 기준 문서는 기존 `CLAUDE.md`이며, 이 문서에 전체 규칙을 중복 작성하지 않는다.

## 시작 순서

1. `CLAUDE.md`를 읽고 공통 핵심 작업 원칙을 따른다.
2. `docs/README.md`에서 현재 문서 구조를 확인한다.
3. 작업 유형에 맞는 거버넌스·설계 문서를 읽는다.
4. 사용자 승인 범위와 이번 작업의 실행 에이전트(Jules 또는 Claude Code)를 확인한다.

## 작업 기준

- 구현 전 계획과 수정 대상 파일을 제시하고, 승인된 범위를 넘지 않는다.
- 민감 영역, DB 변경, 신규 외부 라이브러리, 범위 확대는 사전 보고·승인을 받는다.
- 하나의 작업·PR에는 실행 에이전트를 하나만 지정한다. Jules와 Claude Code가 같은 브랜치나 PR을 동시에 수정하지 않는다.
- 테스트 결과, 변경 범위, 검수 방법을 PR에 남긴다. 테스트 실패 상태에서는 병합하지 않는다.
- `main` 병합, 테스트계 배포, 운영계 승격은 사용자의 명시적 승인을 받아야 한다.

## 실행 에이전트 경계

- Jules는 GitHub 브랜치·PR과 작업 VM 안의 검증만 담당한다. SSH 서버, 테스트·운영 DB, 비밀값에는 접근하지 않는다.
- Claude Code는 지정된 개발 작업 경로에서만 작업한다. 테스트·운영 서버 경로를 직접 수정하지 않는다.
- 도구별 환경·권한·결과물은 `docs/01_governance/agent-execution-profiles.md`를 따른다.

## 작업별 상세 문서

- 역할·승인: `docs/01_governance/roles.md`
- Git·PR: `docs/01_governance/rules-git-workflow.md`
- 배포·롤백: `docs/01_governance/rules-deploy-rollback.md`
- 품질·테스트: `docs/01_governance/rules-code-quality.md`
- DB·민감 영역: `docs/01_governance/rules-db-migration.md`, `docs/01_governance/rules-sensitive-domain.md`
- 문서 작성·기록: `docs/01_governance/document-management-rules.md`

현재 설계·계획·분석·Backlog는 각각 `docs/02_design/`, `docs/03_planning/`, `docs/04_analysis/`, `docs/06_backlog/`에서 확인한다.
