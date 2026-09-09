# PL-0007-2026-09-09-GitHub-ruleset-및-Jules-최소-권한-설정안

- 상태: In Review
- 작성일: 2026-09-09
- 연결 Backlog: BL-0003, BL-0004
- 관련 Analysis: AN-0004
- 관련 설계: docs/01_governance/agent-execution-profiles.md, docs/01_governance/rules-git-workflow.md, docs/01_governance/rules-deploy-rollback.md

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|---|---|---|
| 2026-09-09 | v0.1 | main·v* ruleset 및 Jules 최소 권한의 적용값 제안 |

## 1. 목적과 완료 기준

이미 병합된 사용자 승인·수동 배포 정책을 GitHub 설정으로 보강하기 위한 정확한 적용값을 제안한다. 이 문서는 설정 변경 승인을 위한 기준이며, 승인 전에는 GitHub·Jules 설정을 바꾸지 않는다.

완료 기준은 다음과 같다.

- main과 v*에 적용할 ruleset 이름, 대상, 활성 상태, 규칙과 예외 기준이 명확하다.
- 현재 CI가 없어서 병합을 막는 필수 상태 검사는 제안에서 제외한다.
- Jules는 이 저장소에서 브랜치·커밋·PR 작업에 필요한 GitHub 권한만 받고, 서버·시크릿·관리 권한을 받지 않는다.
- 사용자 승인 후의 적용·재검증·롤백 절차가 정의되어 있다.

## 2. 적용 전 확인 결과

| 항목 | 현재 상태 | 적용 판단 |
|---|---|---|
| 기본 브랜치 | main | 보호 대상 |
| 자동 병합 | 비활성 | 현 상태 유지 |
| main 브랜치 보호 | 없음 | ruleset 신규 적용 |
| 저장소 ruleset | 없음 | branch·tag ruleset 신규 적용 |
| GitHub Actions | 활성 | CI 도입 전 필수 검사 미지정 |
| Jules 설치·권한 | 현재 토큰으로 확인 불가 | 설치 화면에서 아래 최소 권한과 실제 요청 권한을 대조 |

## 3. 제안 설정값

### main branch ruleset

| 항목 | 제안값 | 이유 |
|---|---|---|
| 이름 | Protect main | 목적이 명확한 고정 이름 |
| 적용 상태 | Active | 승인 뒤 즉시 보호 적용 |
| 대상 | refs/heads/main | 기본 통합 브랜치만 대상 |
| PR 필요 | 사용 | main 직접 커밋 금지 |
| 필요한 승인 수 | 0 | GitHub 승인 수와 사용자의 명시적 병합 승인을 혼동하지 않음 |
| 마지막 푸시 승인 | 사용 안 함 | 단일 사용자·현재 협업 구조에서 불필요 |
| 필수 상태 검사 | 없음 | CI가 아직 없어 병합을 막지 않음 |
| 강제 푸시 | 금지 | 이력 변경 방지 |
| 브랜치 삭제 | 금지 | 기본 브랜치 보호 |
| bypass actor | 없음 | 관리자·앱을 포함한 예외를 기본적으로 두지 않음 |
| 선형 이력 | 강제하지 않음 | 현재 승인된 merge commit 병합 방식을 유지 |

사용자 수동 병합 원칙은 GitHub의 승인 수가 아니라 Codex 검토와 사용자의 이 대화에서의 명시적 병합 지시로 유지한다.

### v* tag ruleset

| 항목 | 제안값 | 이유 |
|---|---|---|
| 이름 | Protect release tags | 릴리스 태그 목적을 명확히 표시 |
| 적용 상태 | Active | 승인 뒤 즉시 보호 적용 |
| 대상 | refs/tags/v* | v로 시작하는 릴리스 태그만 대상 |
| 태그 갱신 | 금지 | 생성 뒤 SHA 변경 방지 |
| 태그 삭제 | 금지 | 검증·운영 승격 이력 보존 |
| 태그 생성 | 제한하지 않음 | 사용자 승인자가 릴리스 태그를 생성할 수 있도록 유지 |
| bypass actor | 없음 | 예외 생성은 별도 승인과 일시적 변경으로만 처리 |

태그 생성 전에는 테스트계 검증 결과, 대상 main SHA, image digest, 이전 롤백 태그를 릴리스 기록에 남긴다.

### Jules GitHub App 최소 권한

| 구분 | 제안 | 이유 |
|---|---|---|
| 설치 범위 | 이 저장소만 | 다른 저장소 접근 차단 |
| Metadata | 읽기 | GitHub App 필수 기본 권한 |
| Contents | 읽기·쓰기 | 작업 브랜치 생성과 커밋 푸시 |
| Pull requests | 읽기·쓰기 | PR 생성·갱신 |
| Issues | 부여하지 않음 | 현재 작업 흐름에서 필요하지 않음 |
| Actions·Workflows | 부여하지 않음 | CI·워크플로 변경은 별도 승인 대상 |
| Administration | 부여하지 않음 | ruleset·권한·저장소 설정 변경 차단 |
| Secrets·Environments | 부여하지 않음 | 테스트·운영 비밀값 접근 차단 |
| SSH·서버 접근 | 부여하지 않음 | GitHub VM 작업 경계 유지 |

Jules 설치 화면이 이보다 넓은 권한을 필수로 요구하면 설치를 중단하고, 권한별 필요 근거와 대안을 사용자에게 먼저 제시한다.

## 4. 적용 및 검증 순서

1. 사용자가 main ruleset, v* tag ruleset, Jules 최소 권한을 각각 승인한다.
2. GitHub UI에서 기존 ruleset·branch protection·tag protection·bypass actor가 없는지 다시 확인한다.
3. main branch ruleset과 v* tag ruleset을 제안값 그대로 적용한다.
4. Jules가 아직 설치되지 않았다면 단일 저장소 범위와 최소 권한으로만 설치한다. 이미 설치됐다면 실제 권한을 대조하고 초과 권한은 제거한다.
5. API/UI를 읽기 전용으로 다시 조회해 자동 병합 비활성, ruleset 활성, 대상 ref, 규칙, bypass actor, Jules 범위를 확인한다.
6. CI를 도입하는 별도 PR에서만 필수 상태 검사를 추가한다.

## 5. 위험 요소와 롤백

| 위험 | 대응·롤백 |
|---|---|
| ruleset이 예상보다 병합을 막음 | 사용자 승인 하에 방금 만든 ruleset만 비활성화하거나 수정 |
| Jules가 추가 권한을 요구 | 설치·연결을 중단하고 별도 승인 요청 |
| 태그 생성자가 보호 규칙에 막힘 | bypass를 상시 추가하지 않고 사용자 승인 하에 규칙을 일시 조정한 뒤 재보호 |
| CI 도입 전 상태 검사 요구 | 필수 검사 없이 시작하고 CI PR에서 별도 적용 |

## 6. 승인 필요 사항

- Protect main ruleset의 모든 제안값, 특히 승인 수 0·bypass actor 없음
- Protect release tags ruleset의 v* 대상과 태그 갱신·삭제 금지
- Jules를 이 저장소로 한정하고 Contents·Pull requests 읽기·쓰기만 부여하는 것
- 제안값 적용 후 GitHub UI/API 재검증 수행
