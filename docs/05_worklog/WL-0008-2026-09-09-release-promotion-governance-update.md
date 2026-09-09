# WL-0008-2026-09-09-릴리스-승격-거버넌스-갱신

- 상태: Completed
- 작업일: 2026-09-09
- 연결 Backlog: `BL-0003`, `BL-0004`
- 연결 Planning: `PL-0005`
- 연결 Analysis: `AN-0003`
- 관련 설계: `docs/01_governance/rules-git-workflow.md`, `docs/01_governance/rules-deploy-rollback.md`

## 1. 목적

Jules·Claude Code 병행 작업의 Git 기준과 테스트계·운영계 승격 기준을 사용자 승인, 커밋 SHA, 릴리스 태그, 동일 이미지 digest 중심으로 정리한다.

## 2. 수행 내용

- `develop` 기반 테스트 배포 표현을 제거하고, 수동 `main` 병합 후 특정 커밋을 테스트계에서 검증하는 흐름으로 정리했다.
- 테스트계 검증과 사용자 승인 후 `vMAJOR.MINOR.PATCH` 릴리스 태그를 생성하고, 동일 이미지 digest를 운영계에 배포하는 기준을 추가했다.
- 자동 병합·자동 운영 배포 금지, Jules의 GitHub PR 범위, 테스트/운영 환경 분리 기준을 명시했다.
- 테스트 서버 배포와 AI 하네스 Backlog를 새 운영 흐름에 연결했다.

## 3. 판단 및 결정

- 현재는 별도 `develop` 브랜치를 사용하지 않는다. 향후 재도입은 별도 분석·승인이 필요하다.
- `main` 병합만으로 테스트계 배포나 운영계 승격을 자동 수행하지 않는다.
- 운영계는 `main`을 직접 추적하지 않고, 승인된 릴리스 태그가 가리키는 동일 산출물만 배포한다.

## 4. 변경 파일

- `docs/01_governance/rules-git-workflow.md` — 브랜치·PR·릴리스 태그 규칙 갱신
- `docs/01_governance/rules-deploy-rollback.md` — 테스트계·운영계·롤백 기준 갱신
- `docs/06_backlog/BL-0003-staging-deployment-pipeline.md` — 테스트 서버 배포 목표 갱신
- `docs/06_backlog/BL-0004-ai-development-harness.md` — 공통 실행 에이전트·릴리스 기준 반영
- `docs/01_governance/changelog.md`, `docs/05_worklog/README.md` — 개정·수행 이력 갱신

## 5. 검증 결과

- Git·배포·Backlog 문서가 수동 main 병합, 테스트계 검증, 사용자 승인 태그, 운영계 동일 산출물 배포 흐름을 가리키는지 확인했다.
- `develop` 기반 테스트 배포 기준이 현재 활성 Git·Backlog 문서에 남지 않았는지 확인했다.
- `git diff --check`를 통과했다.

## 6. 후속 작업

- GitHub의 실제 브랜치 보호·Jules 저장소 권한·릴리스 태그 보호 설정을 별도 계획으로 수립한다.
- 프로젝트 골격 구현 시 개발·테스트 환경 분리, 이미지 digest 기록, CI 품질 게이트를 실제 설정으로 구현한다.
