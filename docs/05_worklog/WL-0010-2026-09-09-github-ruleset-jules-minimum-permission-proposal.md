# WL-0010-2026-09-09-GitHub-ruleset-Jules-최소-권한-설정안

- 상태: Completed
- 작업일: 2026-09-09
- 연결 Backlog: BL-0003, BL-0004
- 연결 Planning: PL-0006, PL-0007
- 연결 Analysis: AN-0004
- 관련 설계: docs/01_governance/agent-execution-profiles.md, docs/01_governance/rules-git-workflow.md

## 1. 목적

main 병합 뒤의 GitHub 상태를 읽기 전용으로 재확인하고, 실제 설정 변경 전 사용자 승인용 ruleset·Jules 최소 권한 제안값을 작성한다.

## 2. 수행 내용

- main의 최신 SHA와 자동 병합, branch protection, ruleset, Actions 설정을 읽기 전용으로 재조회했다.
- main 보호와 ruleset이 아직 없고 자동 병합은 비활성인 상태를 확인했다.
- PL-0007에 main·v* ruleset 및 Jules 최소 권한의 정확한 제안값을 기록했다.
- GitHub 설정, Jules 앱, 시크릿, 서버, CI는 변경하지 않았다.

## 3. 판단 및 결정

- CI가 아직 없으므로 필수 상태 검사는 제안하지 않는다.
- main에는 PR 요구·강제 푸시 금지·삭제 금지·bypass actor 없음을 우선 적용한다.
- v* 태그는 생성 뒤 갱신·삭제를 금지하되, 생성은 사용자 승인자가 수행할 수 있게 제한하지 않는다.
- Jules가 제안 범위를 초과하는 권한을 요구하면 설치·연결 전에 별도 승인받는다.

## 4. 변경 파일

- docs/03_planning/PL-0007-2026-09-09-github-ruleset-and-jules-minimum-permissions.md — 승인용 정확한 설정값 제안
- docs/03_planning/README.md — PL-0007 인덱스 연결
- docs/05_worklog/WL-0010-2026-09-09-github-ruleset-jules-minimum-permission-proposal.md — 점검·판단 기록
- docs/05_worklog/README.md — WL-0010 인덱스 연결

## 5. 검증 결과

- GitHub API로 main 보호 없음, ruleset 없음, 자동 병합 비활성, Actions 활성 상태를 확인했다.
- 문서 인덱스·교차 참조와 git diff --check는 PR 생성 전에 검증한다.

## 6. 후속 작업

- 사용자가 PL-0007의 각 설정값을 승인하면 GitHub ruleset과 Jules 권한을 적용한다.
- 적용 뒤 API/UI를 읽기 전용으로 재검증하고 실제 값을 Worklog와 거버넌스 문서에 기록한다.
