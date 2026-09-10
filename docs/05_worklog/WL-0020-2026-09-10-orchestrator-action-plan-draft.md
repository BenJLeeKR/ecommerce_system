# WL-0020-2026-09-10-orchestrator-action-plan-draft

- 상태: Completed
- 작업일: 2026-09-10
- 연결 Backlog: `BL-0004`
- 연결 Planning: 없음
- 연결 Analysis: `AN-0003`, `AN-0004`
- 관련 설계: `docs/01_governance/roles.md`, `docs/01_governance/agent-execution-profiles.md`

## 1. 목적

Codex–Jules Thin Orchestrator의 별도 프로젝트 도입을 준비하기 위해, 이커머스 저장소의 임시 참고 경로에 Task Contract 기반 Action Plan 초안을 기록했다.

## 2. 수행 내용

- `/workspace/orchestrator/`를 별도 제어 프로젝트의 목표 경로로 정하고, 이커머스 애플리케이션·테스트계·운영계와 실행 상태 및 비밀값을 분리하는 원칙을 기록했다.
- 1단계는 Codex 프롬프트 전달과 Jules 완료 결과 수집 자동화에 한정하고, LOW 위험 문서 작업 POC를 완료 기준으로 설정했다.
- 2단계는 프로젝트 골격과 기본 CI가 마련된 뒤 일반 구현 작업의 계획 승인·PR·CI 추적까지 확장하도록 정의했다.
- 자동 main 병합·자동 배포·민감 영역 자동 실행은 두 단계 모두 제외했다.

## 3. 판단 및 결정

- 현재 `docs/99_reference/`는 이커머스 구현 기준을 대체하지 않는 임시 보관 위치로만 사용한다.
- 별도 저장소 생성 후 Action Plan은 `/workspace/orchestrator/` 저장소의 `docs/03_planning/`으로 이동한다.
- 실제 별도 경로 생성, API 키 관리, LOW 위험 POC 실행은 사용자 승인 후 별도 작업으로 진행한다.

## 4. 변경 파일

- `docs/99_reference/codex-jules-thin-orchestrator-action-plan.md` — 별도 Orchestrator 프로젝트의 단계별 Action Plan 초안 추가
- `docs/99_reference/README.md` — 참고 문서와 임시 Action Plan 인덱스 추가
- `docs/05_worklog/WL-0020-2026-09-10-orchestrator-action-plan-draft.md` — 작업 기록 추가
- `docs/05_worklog/README.md` — WL-0020 인덱스 추가

## 5. 검증 결과

- 문서 경로, 링크, 파일명 규칙을 확인했다.
- Action Plan은 현재 이커머스 구현·배포 기준을 직접 변경하지 않으며, 자동 병합·배포를 승인하지 않음을 명시했다.
- `git diff --check` 검증은 PR 생성 전 수행한다.

## 6. 후속 작업

- 사용자 승인 후 `/workspace/orchestrator/` 별도 저장소를 만들고 이 문서를 `docs/03_planning/`으로 이전한다.
- Task Contract v0.1과 LOW 위험 문서 작업 POC의 상세 설계를 별도 Orchestrator 프로젝트에서 진행한다.
