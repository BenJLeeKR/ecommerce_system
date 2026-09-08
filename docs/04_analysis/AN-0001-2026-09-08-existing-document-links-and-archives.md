# AN-0001-2026-09-08-기존-문서-링크와-archive-분석

- 상태: Completed
- 작성일: 2026-09-08
- 연결 Backlog: `BL-0001`
- 관련 설계: `docs/01_governance/document-management-rules.md`

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|---|---|---|
| 2026-09-08 | v0.1 | 기존 문서 링크와 archive 상태 분석 |

## 1. 분석 목적과 질문

기존 활성 문서의 경로 참조가 실제 파일과 일치하는지, `.archive` 문서가 중복인지 또는 보관할 설계 이력인지 확인한다.

## 2. 범위와 전제

- `CLAUDE.md`와 `docs/`의 Markdown 문서에 명시된 `docs/...md` 경로를 확인했다.
- 활성 문서와 같은 영역의 `.archive` 문서를 파일 비교와 Git 이력으로 확인했다.
- 파일 이동·삭제·링크 수정은 이 분석 범위에서 수행하지 않았다.

## 3. 조사 결과와 근거

### 3-1. 경로 참조

| 문서 | 위치 | 현재 참조 | 판정 | 권장 대상 또는 처리 |
|---|---:|---|---|---|
| `architecture-overview.md` | 4 | `docs/01_architecture/tech-stack-decision.md` | 대상 없음 | `docs/00_project/tech-stack-decision.md`로 수정 |
| `database-design.md` | 4, 513 | `docs/03_database/naming-conventions.md` | 대상 없음 | `docs/04_database/naming-conventions.md`로 수정 |
| `api-convention.md` | 4 | `docs/03_database/naming-conventions.md` | 대상 없음 | `docs/04_database/naming-conventions.md`로 수정 |
| 문서 관리 규칙, `BL-0001` | 각 본문 | `docs/README.md` | 아직 없음 | 최상위 문서 지도 생성 단계에서 추가 |

나머지 확인된 활성 문서의 직접 경로 참조는 현재 파일 위치와 일치한다.

### 3-2. archive 비교

| 활성 문서 | archive 상태 | 차이 | 판단 |
|---|---|---|---|
| `01_architecture/architecture-overview.md` | 내용 상이 | 56행 추가, 16행 삭제 | 공용 PostgreSQL·전용 DB·단일 Schema로의 인프라 결정 이력. 보관 유지 |
| `03_api/api-list.md` | 내용 상이 | 39행 추가, 1행 삭제 | 관리자 상품·재고·회원·대시보드 API 4종 추가 이력. 보관 유지 |
| `04_database/naming-conventions.md` | 내용 상이 | 34행 추가, 38행 삭제 | 테이블 접두어 미사용과 UUID PK로의 명명 규칙 결정 이력. 보관 유지 |
| `05_screen/screen-spec.md` | 활성 문서와 동일 | 완전 일치 | 참조가 없음을 확인한 뒤 중복 archive 사본 정리 후보 |

`.archive` 경로를 직접 참조하는 문서는 발견하지 못했다. 다만 활성 문서와 내용이 다른 archive 3개는 설계 결정의 맥락을 보존하므로, 단순 중복 파일로 간주해 삭제하면 안 된다.

## 4. 대안 비교

| 대안 | 장점 | 단점 | 판단 |
|---|---|---|---|
| 모든 archive를 즉시 삭제 | 구조가 단순해짐 | 설계 변경 근거를 잃음 | 채택하지 않음 |
| 모든 archive를 현 위치 유지 | 변경 없음 | archive 위치와 상태가 불명확 | 임시 유지 |
| 중복만 정리하고 차이 문서는 중앙 archive로 이동 | 활성 문서와 이력을 함께 명확히 관리 | 링크·이동 검증 필요 | 권장 |

## 5. 결론과 권장안

다음 작업은 두 PR로 분리한다.

1. 경로 참조 3종을 실제 활성 문서 위치로 수정한다. `docs/README.md` 참조는 문서 지도 생성 작업에서 함께 해결한다.
2. 완전 중복인 `05_screen/.archive/screen-spec.md`만 별도 검증 후 정리한다. 내용이 다른 archive 3개는 우선 유지하고, 전체 경로 재배치 단계에서 `docs/08_archive/`로 이동할지 결정한다.

## 6. 후속 작업

- `PL-0001`에서 링크 수정과 중복 archive 정리의 정확한 대상·검증·롤백 방법을 계획한다.
- Planning 승인 후 링크 수정과 중복 archive 정리를 별도 PR로 수행한다.
