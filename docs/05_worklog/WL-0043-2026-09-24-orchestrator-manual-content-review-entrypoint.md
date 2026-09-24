# Worklog: Orchestrator 수동 콘텐츠 검토 진입점 구현 및 보완

## 기본 정보
* **작성일:** 2026-09-24 (KST)
* **작성자:** Jules
* **태스크 ID:** ORCHESTRATOR-MANUAL-CONTENT-REVIEW-ENTRYPOINT-001
* **상태:** 완료

## 요약
Codex가 명시적으로 호출할 수 있는 단회성 수동 콘텐츠 검토 진입점(Manual Content Review Entrypoint)을 신규 구현하고, 사전 검증 실패 시 외부 호출을 0회로 차단하는 동시에 비민감 사유 코드를 포함한 `NEEDS_HUMAN_REVIEW`를 반환하도록 구축했습니다. 원문이 노출되지 않도록 메모리 안전성을 보장하고 기존 리더(Reader)에 위임하는 구조를 완성했습니다.

## 상세 작업 내역
1. **명시적 요청 객체 및 단일 진입점 신규 구현 (`.orchestrator/src/orchestrator/manual_content_review_entrypoint.py`)**
   * 비영속/비직렬화 전용 명시적 요청 객체 `ManualContentReviewRequest`를 신규 정의.
   * 의존성 주입(DI) 방식으로 Request, Contract, Evidence, SessionResponse, Binding, Adapter를 주입받아 객체 간의 식별자(Session, Task, Approval, Branch, PR, 각종 해시)를 상호 대조.
   * 검증 실패 시 비민감 사유 코드(reason_code)를 담은 구조화된 `NEEDS_HUMAN_REVIEW` 반환(API 0회 호출 보장).
2. **기존 리더 위임 수정 (`.orchestrator/src/orchestrator/jules_content_review_reader.py`)**
   * 진입점에서 사전 검증 완료 후 어댑터를 전달받아 처리하는 1회 위임 흐름으로 수정.
3. **인터페이스 노출 (`.orchestrator/src/orchestrator/__init__.py`)**
   * 신규 `execute_manual_content_review_reader` 및 `ManualContentReviewRequest`를 `__all__` 리스트에 포함.
4. **단위 테스트 작성 및 강화 (`.orchestrator/tests/test_manual_content_review_entrypoint.py`)**
   * 요청 객체의 식별자 불일치, evidence 버전 차이, binding의 branch/pr 불일치 등 모든 실패 케이스에 대해 Adapter raw-fetch 0회 호출과 reason_code 일치 여부 테스트.
   * 정상(1회 호출) 케이스에서 `logging`, `open`, `sqlite3`에 대한 Mock Assert(`assert_not_called`)를 통해 원문 데이터 비영속(노출 방지) 엄격 검증.
5. **문서화 정합화**
   * 설계 명세서(`docs/99_reference/orchestrator-manual-content-review-entrypoint-design.md`)에 입력 객체 및 검증 정책 갱신.
   * 불필요한 코드 내 영어 주석을 한국어로 모두 번역 및 정합화 완료.

## 이슈 및 해결
* 리뷰 피드백을 수용하여 단순 문자열 대신 `ManualContentReviewRequest` 객체를 정의하고, `ApprovalEvidence`의 `approval_id`, `contract_version` 대조를 비롯한 `PersistentSessionBinding`의 `branch_name`, `pr_number` 등의 누락되었던 상호 대조 로직을 완벽히 보완했습니다.
* 테스트에서 Contract의 속성 변경 시 기존 해시와 불일치하는 문제를 인지하여, 변경된 Contract로부터 해시를 재계산해 Request, Evidence, Binding 모두에 동기화해줌으로써 의도한 검증 분기를 정확히 테스트하도록 수정했습니다.
