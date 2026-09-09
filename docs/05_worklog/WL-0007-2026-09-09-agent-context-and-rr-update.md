# WL-0007-2026-09-09-공통-에이전트-지침-R&R-갱신

- 상태: Completed
- 작업일: 2026-09-09
- 연결 Backlog: `BL-0003`, `BL-0004`
- 연결 Planning: `PL-0005`
- 연결 Analysis: `AN-0003`
- 관련 설계: `docs/01_governance/roles.md`, `docs/01_governance/agent-execution-profiles.md`

## 1. 목적

Jules를 기본 실행 에이전트로 도입하고 Claude Code를 선택적으로 병행할 수 있도록, 공통 작업 진입점과 실행 에이전트의 역할·권한 기준을 문서화한다.

## 2. 수행 내용

- 루트 `AGENTS.md`를 추가해 Jules와 Claude Code가 공통 핵심 규칙과 상세 문서를 찾는 시작 경로를 만들었다.
- 기존 `CLAUDE.md`를 공통 핵심 규칙의 기준 문서로 명확히 하고, 특정 도구 전용 표현을 최소화했다.
- R&R을 실행 에이전트 공통 책임으로 일반화하고, Jules·Claude Code 실행 프로필을 추가했다.
- Jules의 GitHub VM 전용 작업과 SSH·테스트/운영 DB·비밀값 접근 금지, 한 PR당 단일 실행 에이전트 원칙을 명시했다.

## 3. 판단 및 결정

- 공통 R&R을 도구별 문서로 분리하지 않고, `roles.md` 하나와 도구별 실행 프로필로 관리한다.
- Git·테스트 서버·릴리스 태그 규칙은 영향 범위를 줄이기 위해 다음 실행 단위로 분리한다.
- 병합·배포·운영 승격은 실행 에이전트나 Codex의 자동 권한이 아니라 사용자 승인 사항으로 유지한다.

## 4. 변경 파일

- `AGENTS.md` — 공통 에이전트 작업 지도 추가
- `CLAUDE.md` — 공통 핵심 규칙의 기준 문서임을 명확히 함
- `docs/01_governance/roles.md` — 실행 에이전트 공통 R&R으로 일반화
- `docs/01_governance/agent-execution-profiles.md` — Jules·Claude Code의 환경·권한·결과물 기준 추가
- `docs/01_governance/README.md`, `docs/01_governance/changelog.md` — 인덱스와 개정 이력 갱신
- `docs/05_worklog/README.md` — 이번 수행 기록 인덱스 추가

## 5. 검증 결과

- `AGENTS.md`의 모든 상세 문서 경로가 존재함을 확인했다.
- Jules의 SSH·테스트/운영 DB·비밀값 접근 금지와 단일 실행 에이전트 기준을 확인했다.
- 거버넌스 인덱스에서 실행 에이전트 프로필 링크를 확인했다.
- `git diff --check`를 통과했다.

## 6. 후속 작업

- Git 워크플로우와 배포·롤백 규칙, `BL-0003`, `BL-0004`를 승인된 `main`·테스트계·릴리스 태그 흐름에 맞게 갱신한다.
- 이후 프로젝트 골격 단계에서 환경 분리와 CI 품질 게이트를 실제 설정으로 구현한다.
