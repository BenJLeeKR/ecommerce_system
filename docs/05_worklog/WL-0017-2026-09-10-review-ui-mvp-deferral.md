# WL-0017-2026-09-10-review-ui-mvp-deferral

- 상태: Completed
- 작업일: 2026-09-10
- 연결 Backlog: 없음
- 연결 Planning: `PL-0008`
- 연결 Analysis: `AN-0005`
- 관련 설계: `docs/02_design/05_screen/screen-spec.md`

## 1. 목적
리뷰 도메인의 MVP 제외 정책에 따라 화면 명세서(`screen-spec.md`)에 남아 있는 리뷰 UI 선반영 부분을 제거하여, 설계 문서 간의 정합성을 확보하고 MVP 구현 범위를 명확히 한다.

## 2. 수행 내용
- `docs/02_design/05_screen/screen-spec.md` 파일에서 `USR_PRODUCT_DETAIL` 상품 상세 화면의 와이어프레임 내 `[상세설명 / 리뷰 탭]`을 `[상세설명]`으로 수정.

## 3. 판단 및 결정
- 리뷰 도메인이 MVP 범위에서 제외되었으므로, 화면 UI에서도 리뷰 관련 탭이나 문구가 노출되지 않도록 변경하였다.
- 이미 도메인, API, 데이터베이스 설계 문서에 리뷰의 MVP 제외 안내가 명시되어 있으므로, 화면 명세서에는 중복된 안내 문구를 추가하지 않고 UI 텍스트만 수정하는 것으로 결정하였다.

## 4. 변경 파일
- `docs/02_design/05_screen/screen-spec.md`: 리뷰 관련 UI 요소를 삭제하여 MVP 범위와 일치시킴.
- `docs/05_worklog/WL-0017-2026-09-10-review-ui-mvp-deferral.md`: 변경 내역을 기록하기 위해 신규 작성.
- `docs/05_worklog/README.md`: 신규 Worklog 인덱스 추가.

## 5. 검증 결과
- `screen-spec.md` 파일 내 '리뷰' 검색 결과 없음.
- 변경 파일 수가 정확히 3개임을 확인.
- Worklog가 KST 기준으로 정확히 작성되었음을 확인.
- `git diff --check` 오류 없음.

## 6. 후속 작업
- 기획 및 프론트엔드 파트에서 수정된 화면 명세를 바탕으로 구현 진행 확인.
