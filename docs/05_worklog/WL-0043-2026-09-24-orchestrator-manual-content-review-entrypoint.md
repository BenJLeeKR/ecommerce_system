# Worklog: Orchestrator 수동 콘텐츠 검토 진입점 구현

## 기본 정보
* **작성일:** 2026-09-24 (KST)
* **작성자:** Jules
* **태스크 ID:** ORCHESTRATOR-MANUAL-CONTENT-REVIEW-ENTRYPOINT-001
* **상태:** 완료

## 요약
Codex가 명시적으로 호출할 수 있는 단회성 수동 콘텐츠 검토 진입점(Manual Content Review Entrypoint)을 신규 구현하고, 사전 검증 실패 시 외부 호출을 0회로 보장하며 원문이 노출되지 않도록 하는 메모리 안전성 및 위임 구조를 구축했습니다.

## 상세 작업 내역
1. **단일 진입점 신규 구현 (`.orchestrator/src/orchestrator/manual_content_review_entrypoint.py`)**
   * 의존성 주입(DI) 방식으로 요청 ID, Contract, Evidence, SessionResponse, Binding 및 Adapter를 주입받도록 설계.
   * 주입된 객체들의 일치(session, task, contract hash, scope hash 등)와 정책(auto_merge=False 등)을 사전 검증하는 로직 추가.
   * 검증 실패 시 호출 0회 및 구조화된 `NEEDS_HUMAN_REVIEW` 응답 반환 로직 구현.
2. **기존 리더 위임 수정 (`.orchestrator/src/orchestrator/jules_content_review_reader.py`)**
   * 기존 객체 구조 유지하되 진입점에서 검증 후 어댑터를 전달받아 처리하는 위임 흐름 보완.
3. **인터페이스 노출 (`.orchestrator/src/orchestrator/__init__.py`)**
   * 신규 `execute_manual_content_review_reader`를 `__all__` 리스트에 포함.
4. **단위 테스트 작성 (`.orchestrator/tests/test_manual_content_review_entrypoint.py`)**
   * 정상(1회 호출) 및 각종 정책/결속 불일치 실패(0회 호출) 테스트 케이스 작성.
   * `logging`, `open`, `sqlite3`에 대한 Mock Assert로 원문 데이터 비영속(노출 방지)을 엄격히 검증.
5. **문서화**
   * 진입점 설계 명세서(`docs/99_reference/orchestrator-manual-content-review-entrypoint-design.md`) 신규 작성.
   * Worklog 작성 및 인덱스 갱신.

## 이슈 및 해결
* 테스트 작성 중 `TaskContract`, `ApprovalEvidence` 등의 모델 초기화 인자 누락(Missing arguments) 이슈가 있었으나, 각 데이터 클래스의 설계에 맞추어 `kind="file"`, `contract_version`, `approval_id` 등을 올바르게 보강하여 해결했습니다.
* 진입점에서 기존 Reader로 위임할 때 이중 호출 문제가 발생할 수 있어 진입점 내에서는 사전 검증만 수행하고 Reader 호출 시 바로 위임하도록 리팩토링했습니다.
