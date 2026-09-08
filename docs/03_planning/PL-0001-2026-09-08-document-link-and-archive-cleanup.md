# PL-0001-2026-09-08-문서-링크와-archive-정리

- 상태: Completed
- 작성일: 2026-09-08
- 연결 Backlog: `BL-0001`
- 관련 Analysis: `AN-0001`
- 관련 설계: `docs/01_governance/document-management-rules.md`

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|---|---|---|
| 2026-09-08 | v0.1 | 링크 수정과 중복 archive 정리 계획 작성 |
| 2026-09-08 | v0.2 | 승인된 정리 작업 완료 |

## 1. 목적과 완료 기준

활성 설계 문서의 잘못된 경로 참조를 실제 문서 위치로 바로잡고, 활성 문서와 완전히 같은 archive 사본을 제거한다.

완료 기준은 다음과 같다.

- 확인된 경로 참조 3종이 실제 활성 문서를 가리킨다.
- `docs/05_screen/.archive/screen-spec.md`가 제거되고 활성 `screen-spec.md`는 유지된다.
- 다른 archive 문서 3개와 설계 내용은 변경하지 않는다.
- 문서 경로 검사와 `git diff --check`를 통과한다.

## 2. 범위

### 포함

- `architecture-overview.md`의 기술 스택 참조를 `docs/00_project/tech-stack-decision.md`로 수정한다.
- `database-design.md`의 DB 명명 규칙 참조 2곳을 `docs/04_database/naming-conventions.md`로 수정한다.
- `api-convention.md`의 DB 명명 규칙 참조를 `docs/04_database/naming-conventions.md`로 수정한다.
- 완전히 중복된 `docs/05_screen/.archive/screen-spec.md` 사본을 삭제한다.

### 제외

- `docs/README.md` 생성과 그 참조 해결
- 내용이 다른 architecture/API/database archive 3개의 이동·삭제
- 기존 설계 문서의 경로 재배치와 내용 변경
- 코드, DB, 배포 설정 변경

## 3. 단계별 계획

1. 변경 전 대상 파일과 archive 중복 상태를 다시 확인한다.
2. 활성 설계 문서 3개에서 경로 참조 4곳을 실제 경로로 수정한다.
3. 활성 화면 명세와 완전 동일한 archive 사본 1개만 삭제한다.
4. 이전의 잘못된 경로가 남지 않았는지 검색하고, 새 경로와 활성 화면 명세의 존재를 확인한다.
5. `git diff --check`와 변경 파일 목록을 검토한다.
6. 결과를 Worklog에 기록하고 `BL-0001` 상태·변경 이력을 갱신한다.

## 4. 변경 예상 파일

- `docs/01_architecture/architecture-overview.md` — 기술 스택 문서 참조 1곳 수정
- `docs/04_database/database-design.md` — DB 명명 규칙 참조 2곳 수정
- `docs/03_api/api-convention.md` — DB 명명 규칙 참조 1곳 수정
- `docs/05_screen/.archive/screen-spec.md` — 활성 문서와 완전 중복된 사본 삭제
- `docs/05_worklog/` 및 `docs/06_backlog/` — 작업 결과 기록과 상태 갱신

## 5. 위험 요소와 대응

| 위험 | 대응 |
|---|---|
| 수정 대상 외 참조를 잘못 바꿈 | `AN-0001`에서 확인한 4개 위치만 수정하고 diff를 검토 |
| 필요한 archive를 삭제 | 완전 동일한 `screen-spec.md` 사본만 대상으로 하고 나머지 3개는 제외 |
| 외부 링크 또는 미확인 참조가 archive를 사용 | 삭제 전 `.archive/` 직접 참조를 다시 검색 |
| 삭제 후 복구 필요 | Git 커밋 이력에서 해당 파일만 복원 |

## 6. 검증 계획

- 기존의 두 잘못된 경로 문자열이 활성 설계 문서에 남아 있지 않은지 검색한다.
- 수정된 세 경로가 실제 파일을 가리키는지 확인한다.
- 활성 `docs/05_screen/screen-spec.md`가 유지되고 archive 사본만 삭제됐는지 확인한다.
- 내용이 다른 archive 3개가 변경 대상에 포함되지 않았는지 확인한다.
- `git diff --check`를 실행한다.

## 7. 롤백 계획

- 링크 수정에 문제가 있으면 해당 세 문서의 참조 문자열만 이전 값으로 되돌린다.
- archive 사본 삭제가 부적절하다고 판단되면 Git 이력에서 `docs/05_screen/.archive/screen-spec.md`만 복원한다.
- 코드·DB·배포 변경이 없으므로 서비스 롤백은 필요하지 않다.

## 8. 승인 필요 사항

- 완전 중복으로 확인된 `docs/05_screen/.archive/screen-spec.md`의 삭제 승인
- 위 제한된 범위의 경로 참조 수정 승인
