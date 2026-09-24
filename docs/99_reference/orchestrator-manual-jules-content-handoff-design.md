# Orchestrator 수동 리뷰(Content Handoff) 리더 설계 문서

**작성일**: 2026-09-24 (KST 기준)
**상태**: 사용자 승인 (PLAN APPROVED)

## 1. 목적
본 문서는 Orchestrator의 `jules_content_review_reader.py`를 통해 사용자가 Jules 세션의 활동 원문(Plan 내용 등)을 수동으로 안전하게 조회하기 위한 설계 및 정책을 정의합니다.

## 2. 보안 및 통제 정책 (HIGH 위험도 통제 항목)
1. **사전 검증 강제**:
   조회 요청 시, 다음 조건이 **모두** 만족해야 합니다. 어느 하나라도 실패하면 원격 API 호출은 0회로 제한되며, 즉시 `NEEDS_HUMAN_REVIEW`를 반환합니다.
   - `ApprovalEvidence.status == 'ACTIVE'`
   - `contract.plan_approval_required == True`
   - `contract.auto_merge == False`
   - `contract.task_id == JulesSessionResponse.task_id`
   - 요청된 세션 ID와 `JulesSessionResponse`의 리소스 이름(session_id)이 일치.

2. **데이터 추출 규칙 (대체 탐색 및 추정 금지)**:
   - `agentMessaged`: `agentMessage` 문자열 반환.
   - `planGenerated`: `plan.steps` 배열의 `title`(필수), `description`(선택) 텍스트 결합 반환.
   - `progressUpdated`: `title`(필수), `description`(선택) 반환.
   - `planApproved` / `sessionCompleted`: 본문(텍스트)이 없으므로 식별자·메타데이터 없이 활동 유형 표식만 반환.
   - `sessionFailed` 등 본문이 아직 규명되지 않은 이벤트는 즉시 조회 중단(NEEDS_HUMAN_REVIEW 반환). `userMessaged` (사용자 민감 정보)는 원문 반환 없이 건너뜀.

3. **자동화 금지**:
   - 자동 승인, 자동 검토, 자동 Plan 승인 기능은 제공하지 않습니다. (수동 조회 용도 한정)

4. **비영속 및 메모리 한정 사용**:
   - 추출된 원문 데이터를 담는 객체(`ReviewActivity`)는 `to_dict()`, `__str__()`, `__repr__()` 호출 시 원문 내용을 `<REDACTED>`로 치환합니다.
   - Git, SQLite, 문서, PR 본문, 콘솔 로그 등에 원시 텍스트가 유출되지 않도록 강력한 보호 조치를 취합니다.


## 5. 안전 진단 코드

수동 콘텐츠 조회 경계는 원문을 보존하거나 출력하지 않고, 다음의 고정된 비민감 사유 코드만 Reader로 전달합니다.

- 전송 계층: AUTHENTICATION_FAILED, HTTP_CONNECTION_FAILED, TIMEOUT_EXCEEDED, INVALID_RESPONSE_FORMAT
- activities 목록 형식: INVALID_ACTIVITIES_LIST_FORMAT
- 시간·union 이벤트 등 활동 구조: INVALID_EVENT_STRUCTURE
- 예상하지 못한 내부 실패: INTERNAL_CONTENT_REVIEW_FAILURE

ContentReviewFetchError는 사유 코드 외 자유 문자열이나 원시 데이터를 보유하지 않습니다. Reader는 허용된 안전 예외만 처리하며, 허용되지 않은 예외나 사유 코드는 고정 내부 실패 코드로 전환합니다. 기존 Fake Adapter가 None을 반환하는 경우에는 기존 RAW_ACTIVITIES_FETCH_FAILED fallback을 유지합니다.

이 분류는 수동 검토의 실패 원인을 비민감하게 구분하기 위한 것이며, 자동 승인·자동 검토·자동 병합·자동 배포·자동 재시도 기능을 추가하지 않습니다.
