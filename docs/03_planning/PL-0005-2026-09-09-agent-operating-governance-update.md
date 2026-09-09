# PL-0005-2026-09-09-에이전트-운영-거버넌스-갱신

- 상태: In Review
- 작성일: 2026-09-09
- 연결 Backlog: `BL-0003`, `BL-0004`
- 관련 Analysis: `AN-0003`
- 관련 설계: `docs/01_governance/roles.md`, `docs/01_governance/rules-git-workflow.md`, `docs/01_governance/rules-deploy-rollback.md`

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|---|---|---|
| 2026-09-09 | v0.1 | Jules 중심·Claude Code 병행 운영을 위한 거버넌스 갱신 계획 작성 |

## 1. 목적과 완료 기준

Jules를 GitHub 기반 기본 실행 에이전트로 도입하고 Claude Code를 선택적으로 병행할 수 있도록, 공통 작업 규칙·R&R·Git·배포 기준을 일관되게 갱신한다.

완료 기준은 다음과 같다.

- 공통 작업 기준은 `AGENTS.md`에서 찾을 수 있고, Claude Code 전용 보조 지침과 중복되지 않는다.
- R&R은 특정 실행 도구에 종속되지 않으며 Jules·Claude Code 실행 프로필의 권한 차이를 명확히 설명한다.
- `main`은 사용자 승인 없이는 병합되지 않으며, 테스트계 검증 후 승인된 릴리스 태그만 운영계로 승격한다.
- Jules에는 SSH·테스트/운영 비밀값·직접 DB 접근 권한을 부여하지 않는다.
- 기존 문서의 상충하는 `develop` 테스트 배포 기준이 승인된 흐름으로 정리되고, 링크·형식 검증을 통과한다.

## 2. 범위

### 포함

- 루트 `AGENTS.md`를 공통 작업 진입점으로 추가하고 `CLAUDE.md`의 공통 규칙 중복을 정리한다.
- `roles.md`를 실행 에이전트 공통 R&R로 일반화하고, Jules·Claude Code 실행 프로필 문서를 추가한다.
- Git 규칙에 사용자 수동 병합, 작업별 단일 실행 에이전트, 릴리스 태그 보호 원칙을 추가한다.
- 배포 규칙에 테스트계의 병합 커밋 SHA 검증과 태그·이미지 digest 기반 운영 승격 원칙을 추가한다.
- `BL-0003`, `BL-0004`, 거버넌스·Backlog 인덱스, 개정 이력을 갱신한다.

### 제외

- GitHub 브랜치 보호 규칙, Jules 앱 권한, SSH 서버 경로, DB·Docker·CI의 실제 설정 변경
- 테스트 서버·운영 서버 배포 실행
- 프로젝트 골격과 하네스의 코드·테스트·CI 구현
- 주문·결제·재고 기능 또는 DB 스키마 변경

## 3. 단계별 계획

1. 분석 PR `AN-0003`이 `main`에 병합되었는지 확인하고, 현재 문서의 Claude Code·`develop`·배포 관련 표현을 다시 검색한다.
2. `AGENTS.md`와 `CLAUDE.md`의 공통/전용 책임을 확정하고, 공통 원칙의 단일 진실 공급원을 정한다.
3. 공통 R&R과 Jules·Claude Code 실행 프로필을 작성한다. 실행 에이전트 선택, GitHub·SSH 권한, 결과물과 에스컬레이션 기준을 명시한다.
4. Git·배포 규칙과 `BL-0003`, `BL-0004`를 `feature → 사용자 승인 main 병합 → 테스트계 검증 → 사용자 승인 태그 → 운영계 배포` 흐름으로 정합화한다.
5. 갱신 문서의 인덱스·개정 이력·교차 참조를 반영한다.
6. 문서 링크, Claude/Jules 단일 전제 잔존 여부, `git diff --check`를 검증하고 Worklog에 실제 변경·검증 결과를 기록한다.

## 4. 변경 예상 파일

- `AGENTS.md` — Jules와 Claude Code가 함께 읽는 짧은 작업 지도 추가
- `CLAUDE.md` — Claude Code 전용 보조 지침과 공통 규칙 참조로 조정
- `docs/01_governance/roles.md` — 공통 R&R 및 사용자 승인 경계 갱신
- `docs/01_governance/agent-execution-profiles.md` — Jules·Claude Code의 실행 환경·권한·결과 전달 방식 추가
- `docs/01_governance/rules-git-workflow.md` — 수동 병합·단일 실행 에이전트·릴리스 태그 규칙 갱신
- `docs/01_governance/rules-deploy-rollback.md` — 테스트계 SHA 검증·태그·이미지 digest 운영 승격 규칙 갱신
- `docs/01_governance/README.md`, `docs/01_governance/changelog.md` — 인덱스·개정 이력 갱신
- `docs/06_backlog/BL-0003-staging-deployment-pipeline.md`, `docs/06_backlog/BL-0004-ai-development-harness.md`, `docs/06_backlog/README.md` — 승인된 흐름과 연결 문서 반영
- `docs/05_worklog/` 및 `docs/05_worklog/README.md` — 실제 변경과 검증 결과 기록

## 5. 위험 요소와 대응

| 위험 | 대응 |
|---|---|
| `AGENTS.md`와 `CLAUDE.md`에 규칙이 중복되어 서로 달라짐 | 공통 규칙의 단일 진실 공급원을 정하고, 다른 문서는 링크·도구별 예외만 기록 |
| Jules가 권한이 필요한 서버·비밀값 작업을 수행하도록 오해 | 실행 프로필에 GitHub VM 전용·SSH/비밀값 금지를 명시 |
| `develop`과 `main`의 테스트 배포 기준이 동시에 남음 | 사용자 승인 후 하나의 흐름만 현재 기준으로 남기고, 대체된 기준을 명시 |
| 자동 병합 또는 자동 운영 배포로 오해 | 사용자 승인 단계와 태그 생성 조건을 Git·배포 규칙에 분리해 명시 |
| 문서 변경이 과도하게 커짐 | 공통 지침/R&R과 Git·배포 정합화를 두 개의 실행 PR로 분리 |

## 6. 검증 계획

- `AGENTS.md`에서 공통 규칙과 기준 문서 링크를 찾을 수 있는지 확인한다.
- `CLAUDE.md`, R&R, 아키텍처·Backlog 문서에서 Claude Code 단독 실행을 현재 기준으로 강제하는 표현이 의도대로 정리됐는지 검색한다.
- Jules 실행 프로필에 SSH·테스트/운영 비밀값·직접 DB 접근 금지가 명시됐는지 확인한다.
- Git·배포·Backlog 문서가 동일한 병합·테스트·태그·운영 승격 흐름을 가리키는지 대조한다.
- 모든 신규 문서가 인덱스에 연결됐는지 확인하고 `git diff --check`를 실행한다.

## 7. 롤백 계획

- 문서 기준이 부적절하면 해당 실행 PR의 변경 문서만 이전 커밋으로 되돌린다.
- 이번 계획에는 GitHub 설정, 서버 경로, 배포, DB 변경이 없으므로 서비스 롤백은 필요하지 않다.
- 실제 배포 자동화는 별도 계획·승인 없이는 시작하지 않는다.

## 8. 승인 필요 사항

- Jules를 GitHub 기반 기본 실행 에이전트로 사용하고 Claude Code를 선택적으로 병행하는 운영 모델 승인
- 공통 R&R + 도구별 실행 프로필 문서 구조 승인
- `feature → 사용자 승인 main 병합 → 테스트계 검증 → 사용자 승인 릴리스 태그 → 운영계 배포` 흐름 승인
- Jules에 SSH·테스트/운영 비밀값·직접 DB 접근 권한을 부여하지 않는 원칙 승인
- 실제 규칙 변경을 공통 지침/R&R PR과 Git·배포 정합화 PR로 나누어 진행하는 방식 승인
