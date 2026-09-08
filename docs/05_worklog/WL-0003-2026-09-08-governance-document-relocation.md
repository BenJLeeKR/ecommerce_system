# WL-0003-2026-09-08-거버넌스-문서-재배치

- 상태: Completed
- 작업일: 2026-09-08
- 연결 Backlog: `BL-0001`
- 연결 Planning: `PL-0002`
- 연결 Analysis: `AN-0002`
- 관련 설계: `docs/01_governance/document-management-rules.md`

## 1. 목적

루트에 있던 거버넌스 문서를 하나의 경로로 통합하고, 현재 유효한 참조를 새 경로로 갱신했다.

## 2. 수행 내용

- 규칙, 역할, 검수, 개정 이력 문서 8개를 `docs/01_governance/`으로 이동했다.
- `CLAUDE.md`의 거버넌스 참조 13곳을 새 경로로 갱신했다.
- 활성 설계 문서와 `BL-0003`의 민감 영역·DB·배포 규칙 참조를 새 경로로 갱신했다.
- 거버넌스 인덱스에 이동 문서 8개를 한 줄 설명으로 추가했다.

## 3. 판단 및 결정

- 정책·규칙의 본문과 승인 상태는 바꾸지 않고 경로와 현재 참조만 정리했다.
- 과거 분석·계획·Worklog에 남긴 이전 경로 인용은 당시 상태를 보존하기 위해 변경하지 않았다.

## 4. 변경 파일

- `CLAUDE.md`
- `docs/01_governance/`의 이동 문서 8개와 `README.md`
- `docs/01_architecture/architecture-overview.md`, `docs/02_domain/domain-model.md`
- `docs/03_api/api-list.md`, `docs/04_database/database-design.md`, `docs/04_database/naming-conventions.md`
- `docs/06_backlog/BL-0003-staging-deployment-pipeline.md`
- `docs/03_planning/PL-0002-2026-09-08-governance-document-relocation.md`, `docs/05_worklog/README.md`, `docs/06_backlog/BL-0001-document-management-structure.md`

## 5. 검증 결과

- 새 거버넌스 경로에 대상 문서 8개가 모두 존재함을 확인했다.
- 이전 루트 경로에 대상 문서가 남아 있지 않음을 확인했다.
- `CLAUDE.md`의 현재 거버넌스 참조가 모두 새 경로를 가리키는지 확인했다.
- 활성 설계 문서와 Backlog의 현재 규칙 참조를 확인했다.
- `git diff --check`를 통과했다.

## 6. 후속 작업

- 활성 설계 문서 8개를 `docs/02_design/`으로 재배치하기 위한 Planning을 작성한다.
- 내용이 다른 archive 문서 3개와 전체 문서 지도는 이후 단계에서 처리한다.
