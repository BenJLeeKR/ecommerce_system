# WL-0024-2026-09-19-jules-source-validation-alignment

- 상태: Completed
- 작업일: 2026-09-19
- 연결 Backlog: 없음
- 연결 Planning: 없음
- 연결 Analysis: 없음
- 관련 설계: `docs/01_governance/orchestrator-project-profile.md`, `.orchestrator/AGENTS.md`

## 1. 목적

Jules 공식 Source Resource Name 형식과 Thin Orchestrator의 입력 검증을 정합화하여, 유효한 연결 소스가 과도한 문자 제한으로 차단되지 않도록 한다.

## 2. 수행 내용

- Source Resource Name을 불투명 식별자로 취급하고 `sources/` 접두어, 비어 있지 않은 식별자, 공백·제어문자 거부만 수행하도록 수정했다.
- 세션 생성 전 Sources API 목록의 모든 페이지를 조회하고 입력값과 메모리 내에서 정확히 대조하도록 추가했다.
- 목록 불일치와 조회 오류는 원문을 포함하지 않는 구조화 사유 코드로 `NEEDS_HUMAN_REVIEW` 처리하도록 했다.

## 3. 판단 및 결정

- Source Resource Name의 실제 연결 여부는 임의 정규식이 아닌 Jules Sources API 목록을 기준으로 검증한다.
- API 키, Source Resource Name, 원시 프롬프트·활동·로그, 페이지 토큰은 Git·PR·문서·결과에 기록하지 않는다.

## 4. 변경 파일

- `.orchestrator/src/orchestrator/jules_adapter.py` — 공식 형식 수용 및 연결 소스 목록 대조를 추가했다.
- `.orchestrator/tests/test_jules_adapter.py` — 형식·목록 대조·다중 페이지·오류 처리 테스트를 보강했다.
- `docs/05_worklog/README.md` — 작업 기록 인덱스를 갱신했다.

## 5. 검증 결과

- 관련 단위 테스트와 전체 Orchestrator 테스트를 실행한다.
- `git diff --check`를 실행한다.

## 6. 후속 작업

- 병합 후 `PROJECT-STATE-001`은 새 Task Contract·새 사용자 승인·새 Jules 세션으로 다시 시작한다.
