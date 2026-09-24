# Orchestrator Manual Content Review Entrypoint Design

## 1. 개요
이 문서는 사용자의 수동 검토(Human Review) 요청에 대해 단회성으로 작동하는 `manual_content_review_entrypoint`의 설계 명세 및 책임 분리 원칙을 정의합니다. 본 진입점은 `Codex`가 명시적으로 호출할 수 있는 단일 인터페이스로서, 어댑터 및 시스템 의존성을 직접 주입받아 동작합니다.

## 2. 책임 분리 원칙
* **단일 진입점(Entrypoint):** 사전 검증, 외부 의존성(Adapter) 조율 및 기존 리더(Reader) 호출 위임에만 책임을 가지며, 데이터 구문 분석 등은 기존 `jules_content_review_reader.py`에 위임합니다.
* **사전 검증(Pre-validation) 및 방어:** 제공받은 요청(`session_id`), `TaskContract`, `ApprovalEvidence`, `JulesSessionResponse`, `PersistentSessionBinding`의 일치 여부(Task, Session, Branch, PR, 해시 값 일치 등)를 검증하고, 실패 시 0회의 API/Adapter 호출과 함께 `NEEDS_HUMAN_REVIEW`를 즉시 반환합니다.

## 3. 입력(DI) 및 검증
진입점은 다음 객체들을 의존성 주입(DI)으로 입력받습니다:
1. **요청 식별자:** `session_id`
2. **TaskContract:** 태스크의 요구사항, 정책 정보.
3. **ApprovalEvidence:** 태스크 정책 승인 증적(해시값 및 상태 등).
4. **JulesSessionResponse:** Jules의 작업 세션 결과(태스크/세션 매핑).
5. **PersistentSessionBinding:** 생성된 브랜치와 PR, 세션을 1:1:1로 묶는 영속 결속 객체.
6. **Adapter (Mock/Fake):** 외부 통신을 담당하는 어댑터.

모든 검증(`evidence.status == 'ACTIVE'`, `plan_approval_required=True`, `auto_merge=False` 등)이 성공할 때만, 주입된 어댑터를 기존 Reader에 단 1회 위임 전달합니다.

## 4. 원문 노출 방지(비영속 경계)
본 진입점 및 위임받는 Reader는 **메모리 안전성**을 최우선으로 합니다.
* 반환 객체(`ReviewActivity`)는 `__repr__`, `__str__`, `to_dict` 메서드를 오버라이드하여 민감 원문을 모두 마스킹합니다.
* 로깅(`logging`), 파일 입출력(`builtins.open`), SQLite 통신(`sqlite3.connect`) 등의 작업 시 원문이 기록되지 않음을 보장하는 엄격한 비로그 및 비영속 원칙을 적용합니다.

## 5. 롤백 정책
* 본 로직 자체는 상태를 영구 저장하거나 원문을 외부에 노출하지 않는 Read-Only에 해당합니다.
* 변경사항을 포함하는 Pull Request 롤백 정책은 병합 전 PR 수동 Close, 병합 후 Merge Commit의 수동 Revert로 제한되며, 자동 롤백은 사용하지 않습니다.
