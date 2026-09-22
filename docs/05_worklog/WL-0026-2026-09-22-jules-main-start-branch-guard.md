# WL-0026: Jules 세션 main 시작 및 예상 브랜치 사후 결속 검증

- 작성일자: 2026-09-22
- 상태: Completed
- 유형: 기능 수정

## 1. 개요 및 배경

기존 Jules 세션 생성 시 사전에 명명한 브랜치명을 사용하여 세션을 결속(Binding)하는 방식은 Jules가 실제 생성한 브랜치와 일치하지 않을 수 있는 문제를 안고 있었습니다. 또한, 세션 생성 전 Base SHA 검증 로직이 불완전하여 최신 `main`에서 시작하지 않는 예외 상황 대응에 취약했습니다.
본 작업은 JULES-MAIN-START-GUARD-001 Contract에 의거하여 이러한 문제를 수정하고, 검증 실패 시 자동 진행을 차단하고 `NEEDS_HUMAN_REVIEW`로 전환하도록 규칙과 어댑터를 보완하는 것을 목적으로 합니다.

## 2. 작업 내용

### 2.1 문서 최신화
- `docs/01_governance/rules-orchestrated-jules-session.md`: 1:1:1 사후 결속(Binding) 원칙 명시 및 문서 롤백 시 단일 PR revert 정책 추가.
- `docs/07_templates/task-contract-template.md`: 예상 브랜치명을 사용하지 않고 결과 브랜치와 PR을 1:1:1로 결속하도록 Task Contract 템플릿 최신화.
- `AGENTS.md` 및 `.orchestrator/AGENTS.md`: 예측 브랜치명 결속 금지 및 결과 브랜치 사후 결속 원칙과 문서 변경의 PR revert 롤백 기준 추가.

### 2.2 어댑터 및 테스트 수정
- `.orchestrator/src/orchestrator/jules_adapter.py`:
  - 세션 생성 요청 객체(`JulesSessionRequest`)에서 `requested_branch` 제거 및 `base_sha` 필드 추가.
  - 세션 생성 시 원격 `origin/main`의 SHA와 전달된 `base_sha`를 대조하여 불일치 시 `NEEDS_HUMAN_REVIEW`를 반환하도록 `create_session` 로직 보완.
  - 기존 `update_session_pr` 메서드를 `bind_session_outputs`로 변경하여 Jules가 생성한 실제 브랜치명과 PR을 사후에 1:1:1로 결속하도록 개선.
- `.orchestrator/tests/test_jules_adapter.py`:
  - `requested_branch`를 `base_sha`로 대체한 테스트 데이터 최신화.
  - Base SHA 불일치 시 세션 생성이 차단되고 `NEEDS_HUMAN_REVIEW`가 반환되는지 검증하는 단위 테스트 추가.
  - 사후 결속(`bind_session_outputs`) 및 중복 바인딩 충돌 처리 기능 테스트 추가.

## 3. 검증 결과

- `pytest`를 활용하여 단위 테스트를 100% 통과했습니다.
- `git diff --check`로 포맷 오류가 없음을 확인했습니다.
- Base SHA 검증과 사후 결속 정책이 성공적으로 반영되었음을 어댑터 로직을 통해 확인했습니다.

## 4. 참고 및 영향

이후 Jules를 활용한 모든 Task Contract는 사전 브랜치명 없이 `base_sha`만을 명시하며, 세션 완료 후 생성된 브랜치와 PR을 바탕으로 1:1:1 결속을 기록해야 합니다.
문서 변경 사항을 롤백할 때는 병합된 PR을 revert 하는 방식으로 진행됩니다.