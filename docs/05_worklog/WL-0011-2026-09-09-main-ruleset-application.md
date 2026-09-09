# WL-0011-2026-09-09-main-ruleset-application

- 상태: Completed
- 작업일: 2026-09-09
- 연결 Backlog: BL-0003, BL-0004
- 연결 Planning: PL-0007
- 연결 Analysis: AN-0004
- 관련 설계: docs/01_governance/rules-git-workflow.md

## 1. 목적

승인된 최소 main 보호 규칙을 GitHub ruleset으로 적용하고, API 읽기 전용 조회로 활성 상태와 실제 규칙을 검증한다.

## 2. 수행 내용

- GitHub 저장소 BenJLeeKR/ecommerce_system에 Protect main ruleset을 생성했다.
- ruleset ID는 22599829이며, 대상은 refs/heads/main, 상태는 active다.
- PR 요구, 강제 푸시 금지, 브랜치 삭제 금지를 적용했다.
- bypass actor는 비워 두었고, 필수 상태 검사·배포·CI·Jules 권한·태그 보호는 변경하지 않았다.

## 3. 실제 적용값

| 항목 | 값 |
|---|---|
| 이름 | Protect main |
| 대상 | branch / refs/heads/main |
| 적용 상태 | active |
| PR 필요 | 사용 |
| 허용 병합 방식 | merge, squash, rebase |
| 필요한 GitHub 승인 수 | 0 |
| 마지막 푸시 승인 | 사용 안 함 |
| 강제 푸시 | 금지 |
| 브랜치 삭제 | 금지 |
| bypass actor | 없음 |
| GitHub 반환 추가값 | 작성자 정보가 확인되지 않는 변경에는 추가 승인 요구 |

사용자 명시적 병합 승인과 Codex 검토 절차는 GitHub 승인 수와 별도로 계속 적용한다.

## 4. 검증 결과

- ruleset 상세 API에서 ID 22599829, active, main 대상, bypass actor 없음과 세 규칙을 확인했다.
- main 적용 규칙 API에서 deletion, non_fast_forward, pull_request가 모두 이 ruleset에서 활성화됐음을 확인했다.
- 직접 푸시·강제 푸시·삭제 시도는 실제 보호를 우회하거나 실패 작업을 남길 수 있어 수행하지 않았다.
- 현재 작업 경로는 main이며 작업 트리가 깨끗하다.

## 5. 후속 작업

- 첫 릴리스 태그를 만들기 전에 v* tag ruleset 적용 여부를 다시 승인받는다.
- Jules를 실제로 연결할 때 설치 화면의 요청 권한을 PL-0007의 최소 권한과 대조하고, 초과 권한은 별도 승인받는다.
- CI 도입 PR에서만 필수 상태 검사를 추가한다.
