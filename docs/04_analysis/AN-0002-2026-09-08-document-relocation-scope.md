# AN-0002-2026-09-08-문서-재배치-범위

- 상태: Completed
- 작성일: 2026-09-08
- 연결 Backlog: `BL-0001`
- 관련 설계: `docs/01_governance/document-management-rules.md`

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|---|---|---|
| 2026-09-08 | v0.1 | 기존 문서 재배치 범위와 링크 영향 분석 |

## 1. 분석 목적과 질문

기존 프로젝트 문서를 목표 번호 경로로 옮길 때의 정확한 대상, 링크 영향, 안전한 분할 단위를 확인한다.

## 2. 범위와 전제

- 현재 활성 문서와 `.archive`의 파일 위치, `CLAUDE.md` 및 Markdown 문서의 직접 경로 참조를 확인했다.
- 문서 내용·승인 상태는 바꾸지 않고, 경로와 링크 정합성만 다룬다.
- 이번 분석에서는 파일 이동·삭제·링크 수정은 수행하지 않았다.

## 3. 조사 결과와 근거

### 3-1. 재배치 대상

| 현재 경로 | 대상 수 | 권장 목표 경로 | 판단 |
|---|---:|---|---|
| `docs/00_project/` | 2 | 유지 | 이미 목표 구조와 일치 |
| `docs/01_architecture/` | 1 활성 + 1 archive | `docs/02_design/01_architecture/` | 설계 영역으로 이동 |
| `docs/02_domain/` | 1 | `docs/02_design/02_domain/` | 설계 영역으로 이동 |
| `docs/03_api/` | 2 활성 + 1 archive | `docs/02_design/03_api/` | 설계 영역으로 이동 |
| `docs/04_database/` | 2 활성 + 1 archive | `docs/02_design/04_database/` | 설계 영역으로 이동 |
| `docs/05_screen/` | 2 | `docs/02_design/05_screen/` | 설계 영역으로 이동 |
| 루트 거버넌스 문서 | 8 | `docs/01_governance/` | 규칙·역할·검수 문서로 통합 |
| `docs/99_reference/` | 2 | 유지 | 이미 목표 구조와 일치 |

루트 거버넌스 문서는 `rules-*.md` 5개, `roles.md`, `review-guide-template.md`, `changelog.md`다.

### 3-2. 링크 영향

| 연결 범위 | 확인 결과 | 재배치 시 처리 |
|---|---|---|
| `CLAUDE.md` → 루트 거버넌스 | 13곳 | 거버넌스 이동과 같은 PR에서 경로 일괄 수정 |
| 활성 설계 문서 간 참조 | Architecture·Domain·API·DB·Screen 사이 다수 | 설계 이동 PR에서 대상 경로로 일괄 수정 |
| 활성 설계 문서 → 루트 거버넌스 | 민감 영역·DB·배포 규칙 참조 다수 | 거버넌스 이동 뒤 대상 경로로 수정 |
| Backlog·Worklog·Analysis·Planning | 기존 설계·거버넌스 경로를 기록 | 현재 유효 문서를 가리키는 링크는 갱신, 과거 오류를 인용한 분석 내용은 보존 |
| `.archive` 직접 참조 | 현재 활성 문서에서 없음 | archive 이동은 별도 PR로 분리 가능 |

### 3-3. archive 처리

내용이 다른 archive 3개는 활성 설계 문서와 함께 옮기지 않고, 다음 목표 위치로 별도 이동하는 것이 명확하다.

- `docs/08_archive/02_design/01_architecture/architecture-overview.md`
- `docs/08_archive/02_design/03_api/api-list.md`
- `docs/08_archive/02_design/04_database/naming-conventions.md`

Git 이력은 이동 후에도 유지된다. archive 문서가 현재 기준이 아니라는 상태 안내는 archive 인덱스에서 관리한다.

## 4. 대안 비교

| 대안 | 장점 | 단점 | 판단 |
|---|---|---|---|
| 전체 문서를 한 PR에서 이동 | 최종 구조를 빠르게 완성 | 링크 누락 시 원인 파악·롤백이 어려움 | 채택하지 않음 |
| 경로별로 개별 이동 | 변경 범위가 매우 작음 | PR 수가 과도하고 설계 간 링크가 중간에 자주 깨짐 | 채택하지 않음 |
| 거버넌스·설계·archive·문서 지도로 4단계 분리 | 의존 관계에 맞춰 검증 가능 | 여러 순차 PR이 필요 | 권장 |

## 5. 결론과 권장안

다음 순서로 실행한다.

1. 루트 거버넌스 문서 8개를 `docs/01_governance/`으로 이동하고 `CLAUDE.md`와 규칙 참조를 갱신한다.
2. 활성 설계 문서 8개를 `docs/02_design/` 하위 5개 영역으로 이동하고 설계 간 참조를 갱신한다.
3. 내용이 다른 archive 문서 3개를 `docs/08_archive/02_design/`으로 이동하고 archive 인덱스를 추가한다.
4. `docs/README.md` 전체 문서 지도를 만들고 모든 현재 유효 경로를 최종 검증한다.

각 단계는 별도 Planning 승인과 PR로 진행한다.

## 6. 후속 작업

- `PL-0002`에서 1단계 거버넌스 문서 이동의 정확한 파일·참조·검증·롤백 범위를 작성한다.
- 거버넌스 이동 승인 후, 설계·archive·문서 지도 작업을 차례로 계획한다.
