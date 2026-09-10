# WL-0016-2026-09-10-review-domain-mvp-deferral

- 상태: Completed
- 작업일: 2026-09-10
- 연결 Backlog: 없음
- 연결 Planning: `PL-0008`
- 연결 Analysis: `AN-0005`
- 관련 설계: `docs/02_design/02_domain/domain-model.md`, `docs/02_design/03_api/api-list.md`, `docs/02_design/04_database/database-design.md`

## 1. 목적
사용자 승인 기준에 따라 리뷰 도메인을 1차 MVP 범위 밖으로 명확히 정리하고, 리뷰 기능과 관련된 API 및 데이터베이스 스키마가 미리 반영되어 있던 부분들을 설계 문서에서 제거하여 불필요한 혼선 및 작업 범위 확장을 방지한다.

## 2. 수행 내용
- **`domain-model.md` 수정**: 전체 ERD에서 `REVIEW` 엔티티와 관계선 제거, 도메인별 상세 정의에서 관계 참조 제거. '2-12 Review' 섹션의 상세 모델을 MVP 범위 밖으로 지연한다는 문구로 대체.
- **`api-list.md` 수정**: 9-1부터 9-4까지 기재되어 있던 리뷰 관련 상세 API 엔드포인트 내역과 승인 체크 항목 삭제 후 MVP 제외 문구로 대체.
- **`database-design.md` 수정**: 전체 테이블 목록 및 전체 ERD에서 리뷰 엔티티 제거. '3-16 reviews' 테이블 상세 구조, Soft delete 기준표의 `reviews` 삭제, 규칙 및 승인 체크리스트에서의 연관 내용 삭제 및 안내 문구로 대체.

## 3. 판단 및 결정
- 리뷰 도메인은 MVP 핵심 흐름인 주문, 결제, 재고와 달리 부가적인 기능이므로 서비스 런칭 시점에는 포함하지 않는 것이 타당하다.
- 이후 2차 고도화 등 확장이 필요할 경우 새로운 설계와 승인 후 반영하는 것으로 결정했다.
- 리뷰 기능 제외를 위한 선반영 부분 삭제는 기존 주문·결제·재고 등 다른 민감 영역의 설계와 내용에 영향을 미치지 않도록 주의하여 수행했다.

## 4. 변경 파일
- `docs/02_design/02_domain/domain-model.md`: 모델 및 관계 선반영 내역 삭제
- `docs/02_design/03_api/api-list.md`: 상세 API 선반영 내역 삭제
- `docs/02_design/04_database/database-design.md`: 스키마 선반영 및 규칙 항목 삭제
- `docs/05_worklog/README.md`: 신규 Worklog(WL-0016) 링크 추가
- `docs/05_worklog/WL-0016-2026-09-10-review-domain-mvp-deferral.md`: 신규 생성 (본 파일)

## 5. 검증 결과
- `grep` 등을 통해 `docs/02_design/` 내 파일들에 리뷰의 상세 설계 내용, API 및 스키마가 더 이상 존재하지 않는 것을 확인.
- Markdown 체크(`git diff --check`)를 통과하여 문서 포맷 문제가 없음을 확인.
- 변경된 파일은 지정된 5개 파일(기존 파일 수정 4개 + 워크로그 1개)로 제한됨.

## 6. 후속 작업
- 향후 `screen-spec.md` 등 화면 명세서 내에 포함된 리뷰 탭 및 화면에 대한 정합성 검토 및 수정 작업을 다른 PR로 진행.
