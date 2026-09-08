# PL-0003-2026-09-08-설계-문서-재배치

- 상태: Completed
- 작성일: 2026-09-08
- 연결 Backlog: `BL-0001`
- 관련 Analysis: `AN-0002`
- 관련 설계: `docs/01_governance/document-management-rules.md`

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|---|---|---|
| 2026-09-08 | v0.1 | 사용자 승인에 따라 설계 문서 재배치 계획 작성 |
| 2026-09-08 | v0.2 | 승인된 설계 문서 재배치 완료 |

## 1. 목적과 완료 기준

활성 설계 문서 8개를 `docs/02_design/` 하위의 도메인별 경로로 이동하고, 현재 유효한 참조를 새 경로로 갱신한다.

완료 기준은 다음과 같다.

- 설계 문서 8개가 `docs/02_design/` 하위 5개 영역에 존재한다.
- 기존 `docs/01_architecture/`~`docs/05_screen/`의 활성 문서 사본은 없다.
- 활성 설계 문서와 Backlog의 현재 설계 참조가 새 경로를 가리킨다.
- archive 문서 3개와 과거 분석·계획·Worklog의 경로 인용은 변경하지 않는다.
- `git diff --check`와 경로 검색을 통과한다.

## 2. 범위

### 포함

- `architecture-overview.md`를 `docs/02_design/01_architecture/`으로 이동한다.
- `domain-model.md`를 `docs/02_design/02_domain/`으로 이동한다.
- `api-convention.md`, `api-list.md`를 `docs/02_design/03_api/`으로 이동한다.
- `database-design.md`, `naming-conventions.md`를 `docs/02_design/04_database/`으로 이동한다.
- `screen-list.md`, `screen-spec.md`를 `docs/02_design/05_screen/`으로 이동한다.
- 이동한 문서 내부, `BL-0002`, `BL-0003`의 현재 설계 참조를 새 경로로 갱신한다.
- 각 설계 영역에 짧은 인덱스를 추가한다.

### 제외

- `.archive` 문서 3개의 이동·삭제
- 설계 문서의 정책·내용·승인 상태 변경
- 거버넌스·참고 문서의 재배치
- 최상위 `docs/README.md` 생성
- 코드, DB, 배포 환경 변경

## 3. 단계별 계획

1. 활성 설계 문서 8개와 archive 3개의 현재 위치를 확인한다.
2. Git 이동으로 활성 문서 8개만 `docs/02_design/` 하위 5개 영역에 배치한다.
3. 이동한 설계 문서 사이와 Backlog의 현재 참조를 새 경로로 갱신한다.
4. 각 설계 영역 인덱스에 문서를 한 줄 설명으로 등록한다.
5. 이전 활성 경로가 현재 설계·Backlog 문서에 남아 있지 않은지 확인한다. 과거 분석·계획·Worklog의 역사적 인용은 보존한다.
6. 새 대상 파일 존재, 이전 활성 파일 부재, archive 3개 유지, `git diff --check`를 검증한다.
7. Planning·Worklog·Backlog 상태를 갱신한다.

## 4. 변경 예상 파일

- 활성 설계 문서 8개 — `docs/02_design/` 하위로 이동
- `docs/02_design/01_architecture/README.md`~`05_screen/README.md` — 설계 영역 인덱스 추가
- 이동된 설계 문서 — 문서 간 현재 참조 갱신
- `docs/06_backlog/BL-0002-project-skeleton.md`, `BL-0003-staging-deployment-pipeline.md` — 아키텍처 참조 갱신
- `docs/03_planning/`, `docs/05_worklog/`, `docs/06_backlog/` — 실행 결과 기록

## 5. 위험 요소와 대응

| 위험 | 대응 |
|---|---|
| 설계 문서 간 참조 누락 | 이동 전후의 8개 활성 문서에서 이전 경로를 검색 |
| archive를 활성 문서와 함께 이동 | 활성 파일만 Git 이동하고 `.archive` 3개는 명시적으로 제외 |
| 과거 기록의 근거 훼손 | Analysis·Planning·Worklog의 과거 경로 인용은 변경하지 않음 |
| 이동 후 복구 필요 | Git 이력에서 8개 파일과 참조 변경만 원래 위치로 복원 |

## 6. 검증 계획

- 새 `docs/02_design/` 하위 5개 영역에 활성 문서 8개가 모두 존재하는지 확인한다.
- 이전 활성 경로의 8개 파일이 남아 있지 않은지 확인한다.
- 활성 설계 문서와 Backlog에서 이전 경로가 남아 있지 않은지 확인한다.
- archive 문서 3개가 기존 위치에 유지되는지 확인한다.
- 설계 영역 인덱스의 링크를 확인한다.
- `git diff --check`를 실행한다.

## 7. 롤백 계획

- 문제가 생기면 Git 이력에서 활성 설계 문서 8개만 원래 경로로 복원한다.
- 갱신한 현재 참조는 같은 커밋의 diff를 기준으로 이전 경로로 되돌린다.
- archive, 코드, DB, 배포 환경은 변경하지 않으므로 별도 롤백은 필요하지 않다.

## 8. 승인 필요 사항

- 사용자 승인 완료: 활성 설계 문서 8개의 `docs/02_design/` 이동과 현재 참조 갱신
