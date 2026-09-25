# WL-0048: Codex-Jules 안전 API 실행 절차 및 결속 기준 정합화

- **작성일**: 2026-09-25 (KST)
- **작성자**: Jules
- **태스크 ID**: 비민감 문서 갱신
- **상태**: 완료

## 1. 목적
본 작업은 Codex-Jules 안전 API 실행 절차 및 상태 결속 기준을 관련 거버넌스 및 규칙 문서에 명확히 명시하기 위함이다.
주요 목표는 외부 런타임 환경, 실제 데이터베이스, 원시 API의 노출 없이 API 호출 경계, 사전/사후 검증 절차, 그리고 비영속 처리 기준을 안전하게 문서화하는 것이다.

## 2. 변경 내용 및 검증 기준
- **허용 경로 제한 준수**: 승인된 4개의 문서(`.orchestrator/AGENTS.md`, `docs/01_governance/orchestrator-runtime-db-operations.md`, `WL-0048`, `docs/05_worklog/README.md`) 외에는 일체 수정하지 않았다.
- **안전 API 실행 절차 정합화 (`AGENTS.md`)**:
  - API 호출 전 Contract, ACTIVE 상태의 ApprovalEvidence, 기준 SHA, Contract/Scope 해시 사전 검증 의무 명시.
  - Interactive Plan 모드 (`requirePlanApproval=true`) 및 실제 `main` 시작 조건 명시.
  - 브랜치명/PR 번호 사전 할당 불가, 사후 1:1:1 결속 검증 기준 추가.
  - 자동 승인, 자동 검토, 자동 병합, 자동 배포, 자동 재시도, 자동 재작업 금지 원칙 명시.
- **비영속 경계 및 결속 기록 기준 최신화 (`orchestrator-runtime-db-operations.md`)**:
  - 원문 Plan, 프롬프트, 활동(Activity) 등의 영구 저장(Git, PR, DB 등) 금지 및 수동 검토 요청 시 일시적 객체 전달 원칙 추가.
  - 동일 Contract 내 비민감 보완 메시지 허용 및 변경 시 새 Contract 분리 원칙 명시.
  - 1:1:1 실제 산출물과 식별자 해시 완벽 일치 시에만 외부 DB 기록 (불일치 시 기록 생략) 기준 반영.
- **문서화 원칙**: 본 Worklog 및 관련된 모든 문서에 원시 API 응답, 실제 DB 경로, 원시 활동 내용, 구체적인 API 설정값(예: Key 등)은 포함하지 않는다.

## 3. 롤백 기준
- 본 변경 사항의 롤백은 자동화 방식을 일절 배제하며, 오로지 수동으로 처리한다.
- PR 병합 전: 해당 PR을 단순히 닫는다(Close).
- PR 병합 후: Git `revert` 명령어를 사용하여 해당 merge commit만을 되돌리고, 이를 반영하는 새로운 수동 PR을 생성하여 승인 및 병합한다.

## 4. 검증 결과
- `git diff --check`를 통한 공백 및 서식 오류 미발견.
- `git diff --name-only`로 수정된 파일 4개 확인.
- 마크다운 링크 유효성 점검 완료.
- 본 작업은 오직 문서 수정에 국한되었으며, 실제 API 통신, 외부 DB 쓰기, 배포, 또는 여타의 신규 자동화 프로세스가 수행되지 않았음을 검증함.
