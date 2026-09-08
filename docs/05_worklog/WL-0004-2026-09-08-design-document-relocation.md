# WL-0004-2026-09-08-설계-문서-재배치

- 상태: Completed
- 작업일: 2026-09-08
- 연결 Backlog: `BL-0001`
- 연결 Planning: `PL-0003`
- 연결 Analysis: `AN-0002`
- 관련 설계: `docs/01_governance/document-management-rules.md`

## 1. 목적

활성 설계 문서를 하나의 설계 경로로 통합하고, 현재 설계 참조가 새 경로를 가리키도록 정리했다.

## 2. 수행 내용

- Architecture, Domain, API, Database, Screen 영역의 활성 설계 문서 8개를 `docs/02_design/` 하위로 이동했다.
- 각 설계 영역에 문서별 한 줄 인덱스를 추가했다.
- 이동한 설계 문서와 `BL-0002`, `BL-0003`의 현재 설계 참조를 새 경로로 갱신했다.
- 내용이 다른 archive 문서 3개는 기존 위치에 유지했다.

## 3. 판단 및 결정

- 설계 문서의 정책·내용·승인 상태는 변경하지 않고 경로와 현재 참조만 정리했다.
- 과거 분석·계획·Worklog에 남긴 이전 경로 인용은 당시 상태를 보존하기 위해 변경하지 않았다.

## 4. 변경 파일

- `docs/02_design/` 하위 활성 설계 문서 8개와 영역별 인덱스 5개
- `docs/06_backlog/BL-0002-project-skeleton.md`, `docs/06_backlog/BL-0003-staging-deployment-pipeline.md`
- `docs/03_planning/PL-0003-2026-09-08-design-document-relocation.md`, `docs/05_worklog/README.md`, `docs/06_backlog/BL-0001-document-management-structure.md`

## 5. 검증 결과

- 새 설계 경로에 활성 문서 8개와 영역 인덱스 5개가 모두 존재함을 확인했다.
- 이전 활성 경로의 문서 8개가 남아 있지 않음을 확인했다.
- 이동된 설계 문서와 Backlog에서 이전 활성 설계 경로 참조가 남아 있지 않음을 확인했다.
- archive 문서 3개가 기존 위치에 유지됨을 확인했다.
- `git diff --check`를 통과했다.

## 6. 후속 작업

- 설계 이력이 있는 archive 문서 3개를 `docs/08_archive/`로 이동하기 위한 Planning을 작성한다.
- 최상위 `docs/README.md` 문서 지도 생성과 최종 링크 검증을 진행한다.
