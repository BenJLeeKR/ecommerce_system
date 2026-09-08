# PL-0002-2026-09-08-거버넌스-문서-재배치

- 상태: In Review
- 작성일: 2026-09-08
- 연결 Backlog: `BL-0001`
- 관련 Analysis: `AN-0002`
- 관련 설계: `docs/01_governance/document-management-rules.md`

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|---|---|---|
| 2026-09-08 | v0.1 | 거버넌스 문서 재배치 계획 작성 |

## 1. 목적과 완료 기준

루트에 흩어진 거버넌스 문서 8개를 `docs/01_governance/`으로 통합하고, 현재 유효한 참조를 새 경로로 갱신한다.

완료 기준은 다음과 같다.

- 거버넌스 문서 8개가 `docs/01_governance/`에 존재하고 기존 루트 사본은 없다.
- `CLAUDE.md`의 거버넌스 참조 13곳이 새 경로를 가리킨다.
- 활성 설계 문서와 Backlog의 현재 규칙 참조가 새 경로를 가리킨다.
- 거버넌스 인덱스에서 각 문서를 한 줄 설명으로 찾을 수 있다.
- `git diff --check`와 경로 검색을 통과한다.

## 2. 범위

### 포함

- 다음 8개 문서를 `docs/01_governance/`으로 이동한다.
  - `rules-code-quality.md`
  - `rules-db-migration.md`
  - `rules-deploy-rollback.md`
  - `rules-git-workflow.md`
  - `rules-sensitive-domain.md`
  - `roles.md`
  - `review-guide-template.md`
  - `changelog.md`
- `CLAUDE.md`의 13개 거버넌스 참조를 새 경로로 수정한다.
- 활성 설계 문서와 `BL-0003`의 현재 거버넌스 참조를 새 경로로 수정한다.
- `docs/01_governance/README.md`에 이동 문서 8개를 한 줄 설명으로 등록한다.

### 제외

- 거버넌스 문서의 정책·내용·승인 상태 변경
- 활성 설계 문서의 `docs/02_design/` 재배치
- archive 이동과 `docs/08_archive/` 생성
- `docs/README.md` 전체 문서 지도 생성
- 코드, DB, 배포 환경 변경

## 3. 단계별 계획

1. 이동 대상 8개와 현재 참조 위치를 다시 확인한다.
2. Git 이동으로 대상 문서를 `docs/01_governance/`에 배치한다.
3. `CLAUDE.md`, 활성 설계 문서, `BL-0003`의 현재 참조를 새 경로로 갱신한다.
4. 거버넌스 인덱스에 각 문서를 한 줄로 추가한다.
5. 이전 루트 경로가 현재 기준 문서에서 남아 있지 않은지 확인한다. 과거 분석·계획·Worklog의 경로 인용은 보존한다.
6. 새 대상 파일 존재, 이전 원본 부재, `git diff --check`를 검증한다.
7. Worklog·Backlog·Planning 상태를 갱신한다.

## 4. 변경 예상 파일

- 루트 거버넌스 문서 8개 — `docs/01_governance/`으로 이동
- `CLAUDE.md` — 거버넌스 참조 13곳 갱신
- `docs/01_architecture/architecture-overview.md`, `docs/02_domain/domain-model.md` — 민감 영역 규칙 참조 갱신
- `docs/03_api/api-list.md` — 민감 영역 규칙 참조 갱신
- `docs/04_database/database-design.md`, `docs/04_database/naming-conventions.md` — DB 변경 규칙 참조 갱신
- `docs/06_backlog/BL-0003-staging-deployment-pipeline.md` — 배포 규칙 참조 갱신
- `docs/01_governance/README.md`, `docs/05_worklog/`, `docs/06_backlog/` — 인덱스와 결과 기록 갱신

## 5. 위험 요소와 대응

| 위험 | 대응 |
|---|---|
| `CLAUDE.md` 참조 누락 | 이동 전후 13개 참조를 검색하고 diff로 확인 |
| 활성 문서의 규칙 링크 누락 | 민감·DB·배포 규칙별로 대상 문서를 검색 |
| 과거 기록의 경로 인용을 부정확하게 바꿈 | Analysis·Planning·Worklog의 역사적 인용은 변경하지 않음 |
| 이동 후 복구 필요 | Git 이동 이력에서 대상 파일만 원래 위치로 복원 |

## 6. 검증 계획

- 새 `docs/01_governance/` 경로에 대상 8개가 모두 존재하는지 확인한다.
- 루트의 대상 파일 8개가 남아 있지 않은지 확인한다.
- `CLAUDE.md`에서 이전 루트 거버넌스 경로가 남지 않았는지 확인한다.
- 활성 설계 문서와 Backlog에서 새 거버넌스 경로가 실제 파일을 가리키는지 확인한다.
- 거버넌스 인덱스의 9개 문서 링크를 확인한다.
- `git diff --check`를 실행한다.

## 7. 롤백 계획

- 문제가 생기면 Git 이력에서 이동한 8개 파일만 원래 루트 위치로 복원한다.
- 변경된 참조는 같은 커밋의 diff를 기준으로 이전 경로로 되돌린다.
- 코드·DB·배포 변경이 없으므로 서비스 롤백은 필요하지 않다.

## 8. 승인 필요 사항

- 루트 거버넌스 문서 8개의 `docs/01_governance/` 이동 승인
- `CLAUDE.md`와 현재 문서 참조의 새 경로 일괄 갱신 승인
