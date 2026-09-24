# Orchestrator 수동 콘텐츠 검토 진입점 설계 명세

## 1. 개요
이 문서는 사용자의 수동 검토(Human Review) 요청에 대해 단회성으로 작동하는 `manual_content_review_entrypoint`의 설계 명세 및 책임 분리 원칙을 정의합니다. 본 진입점은 `Codex`가 명시적으로 호출할 수 있는 단일 인터페이스로서, 어댑터 및 시스템 의존성을 직접 주입받아 동작합니다.

## 2. 책임 분리 원칙
* **단일 진입점(Entrypoint):** 사전 검증, 외부 의존성(Adapter) 조율 및 기존 리더(Reader) 호출 위임에만 책임을 가지며, 데이터 구문 분석 등은 기존 `jules_content_review_reader.py`에 위임합니다.
* **사전 검증(Pre-validation) 및 방어:** 제공받은 명시적 요청 객체(`ManualContentReviewRequest`)와 `TaskContract`, `ApprovalEvidence`, `JulesSessionResponse`, `PersistentSessionBinding` 간의 모든 식별자(Session, Task, Approval, Branch, PR, Hash) 일치 여부를 검증합니다. 실패 시 0회의 API/Adapter 호출을 강제하며 비민감한 `reason_code`를 포함한 `NEEDS_HUMAN_REVIEW`를 즉시 반환합니다.

## 3. 입력(DI) 및 검증
진입점은 다음 객체들을 의존성 주입(DI)으로 입력받습니다:
1. **ManualContentReviewRequest:** 수동 검토를 위한 비영속/비직렬화 명시적 요청 객체(`session_id`, `task_id`, `approval_id`, `contract_hash`, `approved_scope_hash` 포함).
2. **TaskContract:** 태스크의 요구사항 및 정책.
3. **ApprovalEvidence:** 태스크 승인 증적.
4. **JulesSessionResponse:** Jules 작업 세션 응답 객체.
5. **PersistentSessionBinding:** 생성된 브랜치와 PR, 세션을 1:1:1로 묶는 영속 결속 객체.
6. **Adapter (Mock/Fake/Protocol):** 외부 원문 조회를 담당하는 어댑터.

위 객체들 간의 모든 상호 대조(예: `evidence.contract_version` vs `contract.contract_version`, `binding.branch_name` vs `session_response.branch_name` 등) 및 정책(`evidence.status == 'ACTIVE'`, `auto_merge == False` 등) 검증을 통과한 경우에만 기존 Reader에 단 1회 위임 전달합니다.

## 4. 원문 노출 방지(비영속 경계)
본 진입점 및 위임받는 Reader는 **메모리 안전성**을 최우선으로 합니다.
* 반환 객체(`ReviewActivity`)는 `__repr__`, `__str__`, `to_dict` 메서드를 오버라이드하여 민감 원문을 모두 마스킹(`<REDACTED>`)합니다.
* 로깅(`logging`), 파일 입출력(`builtins.open`), SQLite 통신(`sqlite3.connect`) 등의 작업 시 원문이 기록되지 않음을 보장하는 엄격한 비로그 및 비영속 원칙을 적용합니다.

## 5. 롤백 정책
* 본 로직 자체는 상태를 영구 저장하거나 원문을 외부에 노출하지 않는 Read-Only에 해당합니다.
* 변경사항을 포함하는 Pull Request 롤백 정책은 병합 전 PR 수동 Close, 병합 후 Merge Commit의 수동 Revert로 제한되며, 자동 롤백은 절대 사용하지 않습니다.
