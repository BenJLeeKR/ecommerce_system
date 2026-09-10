# WL-0015-2026-09-10-kst-and-korean-writing-rules

- 상태: Completed
- 작업일: 2026-09-10
- 연결 Backlog: 없음
- 연결 Planning: 없음
- 연결 Analysis: 없음
- 관련 설계: `CLAUDE.md`, `AGENTS.md`

## 1. 목적

- 모든 실행 에이전트가 공통으로 지켜야 할 한국어 기본 작성 원칙 및 KST(한국 표준시) 시간 기준 규칙을 거버넌스 문서에 명문화하여 일관성을 확보한다.

## 2. 수행 내용

- `CLAUDE.md`의 절대 규칙에 한국어 작성 및 KST 시간 기준에 대한 구체적인 원칙을 추가했다.
- `AGENTS.md`에서 중복된 한국어 관련 규칙을 제거하고 `CLAUDE.md`의 언어 및 시간 기준을 따르도록 안내 문구를 수정했다.
- 새롭게 정의된 규칙 및 문서 변경 이력을 `Worklog`에 기록했다.

## 3. 판단 및 결정

- 한국어 작성 및 KST 시간 기준은 모든 에이전트가 예외 없이 적용해야 하는 핵심 규칙이므로 `CLAUDE.md`의 절대 규칙 항목에 추가하였다.
- 규칙의 중복을 방지하고 단일 진실 공급원(SSOT)을 유지하기 위해, `AGENTS.md`에는 상세 내용 대신 `CLAUDE.md`를 참조하라는 짧은 안내만 추가하였다.

## 4. 변경 파일

- `CLAUDE.md`: 절대 규칙 10, 11, 12 항목 추가 (한국어 작성, KST 기준, 시간 데이터 처리 기준 명시)
- `AGENTS.md`: 작업 기준 항목에서 기존 한국어 관련 문구 대신 `CLAUDE.md` 참조 안내로 대체
- `docs/05_worklog/WL-0015-2026-09-10-kst-and-korean-writing-rules.md`: 신규 Worklog 작성
- `docs/05_worklog/README.md`: Worklog 인덱스 갱신 (WL-0015 추가)

## 5. 검증 결과

- `git diff --check` 명령을 통해 변경된 마크다운 문서의 문법 및 형식을 검증하였다.
- 변경된 파일은 총 4개(`CLAUDE.md`, `AGENTS.md`, `docs/05_worklog/WL-0015...`, `docs/05_worklog/README.md`)임을 확인하였다.
- README.md의 인덱스 링크가 생성된 신규 문서를 올바르게 가리키는지 확인하였다.

## 6. 후속 작업

- 없음
