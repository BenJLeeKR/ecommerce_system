# 수동 E2E POC 실행 프로토콜 v0.1 (Manual Session Monitor Execution Protocol)

> 상태: Reference — 실제 E2E 실행에는 별도 Task Contract와 사용자 승인이 필요합니다.

## 1. 목적
본 문서는 `BL-PH2-001G-MANUAL-ENTRYPOINT-E2E-POC-PREPARATION` 준비 작업 이후, 사용자 승인을 득한 향후 실제 E2E POC 실행 시 적용할 **수동 Session Monitor Entrypoint 호출 및 기록 절차**를 정의합니다.
*이 문서는 기존 `docs/01_governance/rules-orchestrated-jules-session.md` 정책을 대체하지 않으며, 이번 수동 one-shot E2E POC 실행 건에만 한정하여 적용됩니다.*

## 2. 권한 및 책임 경계
- `execute_manual_session_monitor` Entrypoint는 입력된 바인딩 상태(`is_binding_valid`)를 스스로 검증하거나 판단하지 않습니다.
- **사전 확인**: 사용자와 Codex는 대상 세션의 사전 승인 상태, 그리고 1:1:1 결속(1 Jules 세션 ↔ 1 전용 브랜치 ↔ 1 PR)을 사전에 확인한 후 Entrypoint를 호출해야 합니다.
- **사전 게이트 (Pre-gate)**: 현재 이 문서는 준비 작업용입니다. 향후 실제 Entrypoint를 호출하기 전에는 **반드시 별도의 새 Task ID, 새 Task Contract, 새 사용자 승인, 새 Jules 세션**이 생성되어야 합니다. 이 사전 조건이 충족되지 않으면 호출을 진행해서는 안 됩니다.
- **결과 처리**: Entrypoint는 최종 검수, 수용 및 병합 판단을 수행하지 않으며, 오직 비민감 `BridgeSignal` 상태만을 반환합니다.

## 3. 실행 절차
사용자(또는 Codex)는 로컬 환경에서 다음과 같이 수동으로 스크립트를 1회 실행합니다.

```python
from orchestrator.manual_entrypoint import execute_manual_session_monitor

# 주의: 실제 값은 소스코드나 문서에 기록하지 않고 환경 변수나 보안 저장소를 통해 주입해야 합니다.
api_key = None  # `.orchestrator/.env`의 API 키를 사용
session_resource_name = "sessions/[실제세션ID는기록금지]"
is_binding_valid = True  # 사용자/Codex가 사전에 확인한 결속 상태

# Entrypoint 정확히 1회 호출
signal = execute_manual_session_monitor(
    api_key=api_key,
    session_resource_name=session_resource_name,
    is_binding_valid=is_binding_valid
)

# 비민감 상태 출력
print(f"Status: {signal.status_signal}")
print(f"Reason: {signal.reason_code}")
```

## 4. 기록 규칙 및 제약 사항
본 POC 실행 후 생성되는 Worklog 또는 PR에는 아래 규칙을 엄격히 준수하여 기록해야 합니다.

### 허용되는 기록 (예시)
- 반환된 `BridgeSignal`의 비민감 상태 신호 (예: `READY_FOR_REVIEW`, `NEEDS_HUMAN_REVIEW`)
- 반환된 `BridgeSignal`의 사유 코드 (예: `SESSION_COMPLETED`, `BINDING_INVALID`)

### 금지되는 기록 (예시 포함 문서/PR 기록 불가)
- 실제 세션 식별자 (`sessions/12345...`)
- API 키 및 토큰
- 원시 로그, 오류 추적(Traceback), 프롬프트 원문
- 실제 POC의 구체적 실행 결과 데이터

*참고: 현재 준비 세션(PREPARATION)에서는 위 절차를 포함한 실제 API 호출을 절대 수행하지 않으며, 향후 실제 POC Worklog가 작성될 때까지 본 문서만 참조 용도로 유지됩니다.*
