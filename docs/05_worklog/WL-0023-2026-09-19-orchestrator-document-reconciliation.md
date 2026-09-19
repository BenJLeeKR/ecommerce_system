# WL-0023-2026-09-19-orchestrator-document-reconciliation

- 상태: Completed
- 작업일: 2026-09-19 KST
- 연결 Backlog: 없음
- 연결 Planning: 없음
- 연결 Analysis: 없음
- 관련 설계: `.orchestrator/AGENTS.md`, `AGENTS.md`, `CLAUDE.md`

## 1. 목적

`.orchestrator/docs/`에 있던 미추적 Orchestrator 문서를 루트 문서 체계로 이관하고, 현재 승인·보안·경로 규칙과의 충돌을 정리한다.

## 2. 수행 내용

- Task Contract와 Project Profile 구조 문서를 `docs/07_templates/`로 이관했다.
- 이커머스 전용 Project Profile과 수동 Jules 폴백 절차를 `docs/01_governance/`로 이관했다.
- 단발 Session Monitor E2E POC 절차를 `docs/99_reference/` 참고 문서로 이관했다.
- 각 인덱스를 갱신하고 `.orchestrator/docs/` 경로를 제거했다.

## 3. 판단 및 결정

- 모든 Jules 세션은 LOW 위험 문서 작업을 포함해 Interactive Plan의 사용자 승인을 요구하도록 Task Contract 예시를 정정했다.
- 실제 API 키, source resource name, 원시 프롬프트·활동·로그, SQLite DB는 이관 문서와 Worklog에 기록하지 않았다.
- E2E POC 절차는 실제 실행 기준이 아닌 참고 문서로 표시했으며, 실행 전 별도 Task Contract와 사용자 승인이 필요하다.

## 4. 변경 파일

- `docs/07_templates/`: Task Contract·Project Profile 템플릿과 인덱스.
- `docs/01_governance/`: 이커머스 Orchestrator Profile·수동 Jules 절차와 인덱스.
- `docs/99_reference/`: 수동 Session Monitor E2E POC 참고 절차와 인덱스.
- `docs/05_worklog/`: 이 작업 기록과 인덱스.

## 5. 검증 결과

- `.orchestrator/docs/` 경로가 제거됐음을 확인했다.
- 이관 문서의 인덱스 링크와 기존 상대 링크 정합성을 확인했다.
- `git diff --check`를 실행한다.

## 6. 후속 작업

- Draft 상태의 Orchestrator Project Profile·수동 Jules 실행 절차를 검토·승인할지 결정한다.
- 실제 Session Monitor E2E POC 실행은 별도 Task Contract와 사용자 승인 후 진행한다.
