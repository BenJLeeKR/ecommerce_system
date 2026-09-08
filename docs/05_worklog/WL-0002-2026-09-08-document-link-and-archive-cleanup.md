# WL-0002-2026-09-08-문서-링크와-archive-정리

- 상태: Completed
- 작업일: 2026-09-08
- 연결 Backlog: `BL-0001`
- 연결 Planning: `PL-0001`
- 연결 Analysis: `AN-0001`
- 관련 설계: `docs/01_governance/document-management-rules.md`

## 1. 목적

활성 설계 문서의 잘못된 경로 참조를 바로잡고, 활성 문서와 완전히 중복된 archive 사본을 정리했다.

## 2. 수행 내용

- 아키텍처 문서의 기술 스택 참조를 `docs/00_project/tech-stack-decision.md`로 수정했다.
- API 규칙과 DB 설계 문서의 DB 명명 규칙 참조 3곳을 `docs/04_database/naming-conventions.md`로 수정했다.
- 활성 화면 명세와 완전히 동일한 `docs/05_screen/.archive/screen-spec.md` 사본을 삭제했다.
- 내용이 다른 architecture/API/database archive 3개는 변경하지 않았다.

## 3. 판단 및 결정

- 삭제 대상은 활성 화면 명세와 파일 비교 결과가 완전히 같고, 해당 archive를 직접 참조하는 활성 설계 문서가 없음을 재확인했다.
- 설계 변경 이력이 있는 archive 3개는 전체 문서 경로 재배치 단계까지 보관한다.

## 4. 변경 파일

- `docs/01_architecture/architecture-overview.md`
- `docs/03_api/api-convention.md`
- `docs/04_database/database-design.md`
- `docs/05_screen/.archive/screen-spec.md` 삭제
- `docs/03_planning/PL-0001-2026-09-08-document-link-and-archive-cleanup.md`
- `docs/05_worklog/README.md`, `docs/06_backlog/BL-0001-document-management-structure.md`

## 5. 검증 결과

- 수정 전 잘못된 두 경로 문자열이 세 활성 설계 문서에 남아 있지 않음을 확인했다.
- 수정된 참조 대상 3개와 활성 `docs/05_screen/screen-spec.md`의 존재를 확인했다.
- 삭제 대상 archive 사본이 존재하지 않으며, 내용이 다른 archive 3개는 그대로 유지됨을 확인했다.
- `git diff --check`를 통과했다.

## 6. 후속 작업

- 기존 설계·거버넌스·참고 문서를 목표 번호 경로로 재배치하기 위한 별도 분석과 계획을 작성한다.
- `docs/README.md` 전체 문서 지도 생성 시 현재 임시 참조를 함께 해소한다.
