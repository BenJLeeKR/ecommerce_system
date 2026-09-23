# Plan Review Reader 설계 명세서

## 1. 목적
활성화된 세션에서 최신 `planGenerated` 이벤트의 Plan 텍스트 원문을 조회하여 반환합니다.
이 과정에서 시스템은 어떠한 원문 데이터도 디스크, 로거, 데이터베이스, Git 등 외부 영구 저장소나 로그 파일에 기록하지 않고 1회성(Ephemeral)으로 반환하는 엄격한 비영속(Non-persistence) 경계를 준수합니다.

## 2. 역할 분리
1. **jules_adapter.py**:
   - `get_latest_plan_text(session_resource_name: str) -> Optional[str]` 인터페이스를 노출하여 가장 최근의 Plan 본문만 반환하는 좁은 일회성 통로를 제공합니다.
   - 원시 API 응답 패이로드는 일반 `ActivitySummary` 등에 노출하지 않습니다.
2. **plan_review_reader.py**:
   - `read_latest_plan_review(...) -> PlanReviewResult` 함수로 진입점을 제공합니다.
   - Session ID 형식, 권한, Binding 일치 여부를 철저히 검증하고, 검증 실패 시 API 호출 전에 즉시 중단합니다.

## 3. 비영속·비로그 경계 (보안 정책)
- **PlanReviewResult 클래스**:
  - 내부에 `_plan_text` 프라이빗 필드로 원문을 보유합니다.
  - `__repr__`, `__str__`, `to_dict` 메서드를 오버라이드하여 원문이 아닌 `"<REDACTED>"`로 숨겨 직렬화를 차단합니다.
  - 이를 통해 예외 메시지, 시스템 로거, PR 본문, SQLite 기록 등에 원문이 의도치 않게 노출되는 취약점을 원천 차단합니다.
