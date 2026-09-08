# WL-0005-2026-09-08-archive-문서-재배치

- 상태: Completed
- 작업일: 2026-09-08
- 연결 Backlog: `BL-0001`
- 연결 Planning: `PL-0004`
- 연결 Analysis: `AN-0001`, `AN-0002`
- 관련 설계: `docs/01_governance/document-management-rules.md`

## 1. 목적

현재 기준이 아닌 설계 결정 이력을 활성 설계 경로와 분리된 중앙 archive 경로로 통합했다.

## 2. 수행 내용

- Architecture, API, Database 영역의 archive 문서 3개를 `docs/08_archive/02_design/` 하위로 이동했다.
- 최상위 archive 인덱스와 각 archive 영역 인덱스를 추가했다.
- 인덱스에서 archive 문서가 현재 구현·검토의 기준이 아님을 명시했다.

## 3. 판단 및 결정

- archive 문서의 본문과 활성 설계 문서는 변경하지 않았다.
- 현재 유효한 문서에서 archive 대상 3개를 직접 참조하지 않음을 확인한 뒤 이동했다.

## 4. 변경 파일

- `docs/08_archive/02_design/` 하위 archive 문서 3개와 인덱스 4개
- `docs/03_planning/PL-0004-2026-09-08-archive-document-relocation.md`
- `docs/05_worklog/README.md`, `docs/06_backlog/BL-0001-document-management-structure.md`

## 5. 검증 결과

- 새 archive 경로에 보관 문서 3개와 인덱스 4개가 존재함을 확인했다.
- 이전 `.archive` 경로에 대상 문서가 남아 있지 않음을 확인했다.
- 활성 문서와 Backlog에서 archive 대상 3개를 직접 참조하지 않음을 확인했다.
- `git diff --check`를 통과했다.

## 6. 후속 작업

- 최상위 `docs/README.md` 문서 지도를 작성한다.
- 모든 현재 유효 문서 경로와 인덱스 링크를 최종 검증한다.
