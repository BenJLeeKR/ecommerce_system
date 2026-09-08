# PL-0004-2026-09-08-archive-문서-재배치

- 상태: Completed
- 작성일: 2026-09-08
- 연결 Backlog: `BL-0001`
- 관련 Analysis: `AN-0001`, `AN-0002`
- 관련 설계: `docs/01_governance/document-management-rules.md`

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|---|---|---|
| 2026-09-08 | v0.1 | archive 문서 재배치 계획 작성 |
| 2026-09-08 | v0.2 | 승인된 archive 문서 재배치 완료 |

## 1. 목적과 완료 기준

설계 결정 이력이 있는 archive 문서 3개를 활성 설계 경로와 분리된 `docs/08_archive/`로 이동하고, 보관 문서의 성격을 인덱스에서 명확히 한다.

완료 기준은 다음과 같다.

- archive 문서 3개가 `docs/08_archive/02_design/` 하위에 존재한다.
- 기존 설계 영역의 `.archive` 경로에는 대상 파일이 남아 있지 않다.
- archive 인덱스에서 각 문서의 보관 이유를 한 줄로 확인할 수 있다.
- 활성 문서, 설계 내용, archive 문서의 본문은 변경하지 않는다.
- `git diff --check`와 archive 참조 검증을 통과한다.

## 2. 범위

### 포함

- `docs/01_architecture/.archive/architecture-overview.md`를 `docs/08_archive/02_design/01_architecture/architecture-overview.md`로 이동한다.
- `docs/03_api/.archive/api-list.md`를 `docs/08_archive/02_design/03_api/api-list.md`로 이동한다.
- `docs/04_database/.archive/naming-conventions.md`를 `docs/08_archive/02_design/04_database/naming-conventions.md`로 이동한다.
- `docs/08_archive/README.md`와 설계 archive 영역 인덱스를 추가한다.
- Planning·Worklog·Backlog에 실행 결과를 기록한다.

### 제외

- 활성 설계 문서의 이동·수정
- archive 문서 3개의 내용·상태 변경
- `docs/README.md` 전체 문서 지도 생성
- 코드, DB, 배포 환경 변경

## 3. 단계별 계획

1. archive 대상 3개와 현재 유효 문서의 직접 참조 부재를 다시 확인한다.
2. Git 이동으로 archive 문서 3개를 `docs/08_archive/02_design/` 하위로 배치한다.
3. 최상위 archive 인덱스와 영역별 인덱스에 한 줄 설명을 추가한다.
4. 이전 `.archive` 경로의 대상 부재와 새 보관 경로의 대상 존재를 확인한다.
5. 활성 문서에서 새 archive 경로를 기준 문서로 참조하지 않는지 확인한다.
6. `git diff --check`를 실행하고 Planning·Worklog·Backlog를 갱신한다.

## 4. 변경 예상 파일

- archive 문서 3개 — `docs/08_archive/02_design/`으로 이동
- `docs/08_archive/README.md`와 `02_design` 하위 인덱스 4개 — 보관 문서 탐색용 추가
- `docs/03_planning/`, `docs/05_worklog/`, `docs/06_backlog/` — 실행 결과 기록

## 5. 위험 요소와 대응

| 위험 | 대응 |
|---|---|
| archive를 현재 기준 문서로 오인 | 인덱스에 보관 문서이며 현재 기준이 아님을 명시 |
| 숨은 직접 참조 누락 | 활성 문서와 Backlog에서 `.archive` 참조를 재검색 |
| 이동 후 복구 필요 | Git 이력에서 archive 파일 3개만 원래 위치로 복원 |

## 6. 검증 계획

- 새 archive 경로에 대상 문서 3개와 인덱스가 존재하는지 확인한다.
- 이전 `.archive` 경로에 대상 문서가 남아 있지 않은지 확인한다.
- 활성 문서와 Backlog에서 archive 경로 직접 참조가 없는지 확인한다.
- archive 문서 본문이 이동 외 변경되지 않았는지 확인한다.
- `git diff --check`를 실행한다.

## 7. 롤백 계획

- 문제가 생기면 Git 이력에서 archive 문서 3개만 원래 `.archive` 경로로 복원한다.
- 새 archive 인덱스는 함께 제거한다.
- 코드·DB·배포 변경이 없으므로 서비스 롤백은 필요하지 않다.

## 8. 승인 필요 사항

- 설계 archive 문서 3개의 `docs/08_archive/` 이동 승인
- archive 인덱스 추가 승인
