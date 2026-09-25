# WL-0049: Orchestrator 실제 Activity Schema 정합화

- **작성일**: 2026-09-25 (KST)
- **작성자**: Jules
- **태스크 ID**: TASK-123 (비민감 문서 갱신 및 Adapter 갱신)
- **상태**: 완료

## 1. 목적
본 작업은 비민감 진단을 통해 확정된 실제 Jules API의 Activity envelope 구조(`createTime`, `id`, `name`, `originator`, `artifacts`)에 맞춰 `jules_adapter.py` 내의 수동 콘텐츠 검토(Content Review) Reader 로직을 정합화하기 위함이다. 알 수 없는 이벤트나 규격 외 구조의 처리를 명확히 하고, 안전한 비민감 실패 처리를 보장하는 것이 목적이다.

## 2. 변경 내용 및 검증 기준
- **허용 경로 제한 준수**: 승인된 6개의 파일(`.orchestrator/src/orchestrator/jules_adapter.py`, `.orchestrator/tests/test_jules_adapter.py`, `.orchestrator/tests/test_jules_content_review_reader.py`, `docs/99_reference/orchestrator-manual-jules-content-handoff-design.md`, `docs/05_worklog/WL-0049-2026-09-25-orchestrator-actual-activity-schema-alignment.md`, `docs/05_worklog/README.md`)만을 수정했다.
- **실행 경계 준수**: 본 구현 및 테스트 작업은 Mock/Fake만을 사용하였으며, 실제 API·외부 DB·배포에 접근하지 않았다.
- **Envelope 메타 필드 처리**:
  - `createTime`, `id`, `name`, `originator`, `artifacts` 메타 필드를 처리할 수 있도록 갱신했다.
- **단일 `userMessaged` 즉시 제외 및 다중 Union 처리**:
  - 단일 Union이 `userMessaged`일 경우, 본문·시간·메타데이터 값을 읽거나 반환하지 않고 즉시 제외했다.
  - 다중 Union에 섞여 있거나 알 수 없는 이벤트인 경우 `INVALID_EVENT_STRUCTURE`로 안전 중단하도록 보강했다.
- **사후 1:1:1 결속 운영 절차 명시**:
  - 실제 Jules 브랜치 및 단일 PR 생성 후 Codex가 등록 정보와 사후 1:1:1 결속을 검증하며 불일치 시 `NEEDS_HUMAN_REVIEW`로 중단하는 운영 절차를 설계 문서에 반영했다.
- **비영속 및 보안 정책**:
  - 원문, 프롬프트, 활동(Activity), API 설정값, SQLite 내용이나 경로는 문서 및 Git에 절대 기록하지 않는다.

## 3. 롤백 기준
- 본 변경 사항의 롤백은 자동화 방식을 배제하고, 수동으로만 처리한다.
- PR 병합 전: 해당 PR을 단순히 닫는다(Close).
- PR 병합 후: Git `revert` 명령어를 사용하여 해당 merge commit만을 되돌린다.

## 4. 검증 결과
- 전체 테스트(`PYTHONPATH=.orchestrator/src python3 -m unittest discover -s .orchestrator/tests`) 정상 통과 확인.
- `git diff --check`를 통한 포맷팅 및 공백 에러 없음 확인.
- `git diff --name-only`를 통해 정확히 6개의 허용 경로만 변경되었음 확인.
- 비민감 진단 실패 및 롤백 요건 충족, 문서 내 원시/비밀값 미포함 재확인.
