# Task Contract v0.1

이 문서는 Codex-Jules Thin Orchestrator 운영 환경에서 Codex가 작업 프롬프트를 작성하고 Jules에 실행을 지시하기 위한 Task Contract의 v0.1 템플릿과 예시를 정의합니다.

> 상태: Draft — 개별 작업에 적용하기 전 사용자 승인을 받아야 하는 템플릿입니다.

> **주의:** 이 템플릿은 문서 작업만 수행하는 초기 수동 복사-붙여넣기 운영 방식을 위한 것으로, 민감한 실제 데이터나 비밀값을 직접 기입해서는 안 됩니다.

## Markdown 템플릿

```markdown
# Task Contract [Contract 버전]

## 1. 기본 정보

- **Task ID**: [Task ID]
- **적용 Project Profile ID**: [예: PROFILE-EXAMPLE-001]
- **적용 Project Profile 버전**: [예: v0.1]
- **적용 Profile 참조 경로**: [예: docs/01_governance/orchestrator-project-profile.md]
- **작업 목표**: [작업 목표를 명확하게 1-2줄로 기재]
- **실행 에이전트**: [에이전트 이름, 예: Jules]
- **위험도**: [위험도, 예: LOW/MEDIUM/HIGH/CRITICAL]

> **주의:** Task Contract는 개별 작업의 기준 SHA, 허용·금지 경로, 위험도, 완료 조건, 승인 증적을 명시적으로 포함해야 합니다. Project Profile이 선언되어 있더라도 위 항목들을 자동으로 대체하거나 작업 범위를 임의로 확장하지 않습니다.

## 2. 작업 대상 및 환경

- **대상 저장소**: [작업 대상 저장소 URL 또는 경로]
- **기준 브랜치**: [기준 브랜치명, 예: main]
- **기준 커밋 SHA**: [기준이 되는 Commit SHA (필요 시)]
- **기준 문서**:
  - [참조할 요구사항, 설계, 거버넌스 문서 목록]

## 3. 작업 범위 및 규칙

- **허용 경로**:
  - [수정이 허용된 경로 목록]
- **금지 경로**:
  - [수정이 금지된 경로 목록]
- **허용 경로 검증 실패 시 처리 기준**: 실패 시 진행 중단 및 `NEEDS_HUMAN_REVIEW` 전환

## 4. 제어 및 상태

- **병합 설정**: `auto_merge: false` (항상 false로 유지)
- **계획 승인 필요 여부**: true — 모든 Jules 세션에서 Interactive Plan 사용자 승인을 요구
- **세션 생성 적격성/예상 산출물**: [예상 변경 파일/경로 및 PR 생성 조건 명시. 실제 파일 변경 및 PR 산출물이 없는 작업(예: Contract 초안 작성, 계획 검토 등)은 Jules 세션 생성 대상이 아님]
- **절대 규칙 (시작 브랜치 검증 및 세션·실제 브랜치·PR 1:1:1 사후 결속)**:
  - 시작 브랜치는 반드시 실제 `main`을 사용해야 하며, 세션 생성 전 원격 `origin/main`과 승인된 기준 SHA 대조 시 불일치하면 세션 생성 및 API 호출을 차단하고 `NEEDS_HUMAN_REVIEW`로 즉시 중단한다.
  - 생성 전 예상 브랜치명을 결속이나 API 입력에 선제적으로 사용하지 않고, Jules가 생성 및 반환한 실제 작업 브랜치와 PR만 사후에 확인하여 1:1:1로 결속한다.
  - 이전 작업의 병합 또는 종료 후 시작하는 후속 작업은 반드시 새 Task Contract, 새 사용자 승인, 새 Jules 세션 ID를 사용하여 진행한다.
- **중복 실행 방지 기준**: [중복 방지 키 또는 idempotency 기준 명시]
- **취소 조건**: [Contract 실행을 취소해야 하는 명확한 조건]

## 5. 완료 및 검증

- **완료 조건**:
  - [작업이 성공적으로 간주되기 위한 테스트, 문서 링크, 검수 기준 등]

## 6. 승인 상태 및 증적

- **승인 상태**: [예: DRAFT / APPROVED 등]
- **승인 증적 식별자**: [승인 내역 추적용 고유 식별자]
- **승인 내역**:
  - **승인자**: [승인자 이름 또는 식별자]
  - **승인 범위**: [승인된 작업 내용과 범위]
  - **승인 시각**: [UTC 시각 기록] / [KST 시각 표시]
  - **철회/만료 규칙**: [승인 철회, 변경, 만료 시 Dispatch 금지 및 재승인 필요 조건]
```

---

## 가상 예시 (LOW 위험 문서 작업)

다음은 실제 데이터를 사용하지 않은 LOW 위험 문서 작업의 예시입니다. API 키, 토큰, 비밀값, SQLite 경로, 로그 원문은 기입하지 않습니다.

```markdown
# Task Contract v0.1

## 1. 기본 정보

- **Task ID**: DOC-EXAMPLE-001
- **적용 Project Profile ID**: PROFILE-EXAMPLE-001
- **적용 Project Profile 버전**: v0.1
- **적용 Profile 참조 경로**: `docs/01_governance/orchestrator-project-profile.md`
- **작업 목표**: 프로젝트 거버넌스의 코딩 컨벤션 규칙 문서 추가 및 요약 업데이트
- **실행 에이전트**: Jules
- **위험도**: LOW

> **주의:** Task Contract는 개별 작업의 기준 SHA, 허용·금지 경로, 위험도, 완료 조건, 승인 증적을 명시적으로 포함해야 합니다. Project Profile이 선언되어 있더라도 위 항목들을 자동으로 대체하거나 작업 범위를 임의로 확장하지 않습니다.

## 2. 작업 대상 및 환경

- **대상 저장소**: `example/repository`
- **기준 브랜치**: `main`
- **기준 커밋 SHA**: `0123456789abcdef0123456789abcdef01234567`
- **기준 문서**:
  - `docs/01_governance/roles.md`

## 3. 작업 범위 및 규칙

- **허용 경로**:
  - `docs/01_governance/coding-conventions.md`
  - `docs/01_governance/README.md`
- **금지 경로**:
  - `src/` (특히 `src/auth/`, `src/payments/` 등 핵심 비즈니스 로직)
  - `infrastructure/`
- **허용 경로 검증 실패 시 처리 기준**: 실패 시 진행 중단 및 `NEEDS_HUMAN_REVIEW` 전환

## 4. 제어 및 상태

- **병합 설정**: `auto_merge: false`
- **계획 승인 필요 여부**: true — LOW 위험 문서 작업도 Jules Interactive Plan을 사용자 승인한 후에만 실행함
- **세션 생성 적격성/예상 산출물**: 실제 파일 변경(`docs/01_governance/` 내 마크다운 파일) 및 PR 생성이 완료 조건이므로 Jules 세션 생성(또는 수동 실행) 적격함.
- **절대 규칙 (시작 브랜치 검증 및 세션·실제 브랜치·PR 1:1:1 사후 결속)**:
  - 시작 브랜치는 반드시 실제 `main`을 사용해야 하며, 세션 생성 전 원격 `origin/main`과 승인된 기준 SHA 대조 시 불일치하면 세션 생성 및 API 호출을 차단하고 `NEEDS_HUMAN_REVIEW`로 즉시 중단한다.
  - 생성 전 예상 브랜치명을 결속이나 API 입력에 선제적으로 사용하지 않고, Jules가 생성 및 반환한 실제 작업 브랜치와 PR만 사후에 확인하여 1:1:1로 결속한다.
  - 이전 작업의 병합 또는 종료 후 시작하는 후속 작업은 반드시 새 Task Contract, 새 사용자 승인, 새 Jules 세션 ID를 사용하여 진행한다.
- **중복 실행 방지 기준**: Task ID `DOC-EXAMPLE-001`로 이미 실행된 이력이 있는 경우 중복 실행 방지
- **취소 조건**: 대상 저장소의 `main` 브랜치에 대규모 변경이 발생하여 기준 커밋과의 충돌이 예상되는 경우

## 5. 완료 및 검증

- **완료 조건**:
  - `docs/01_governance/coding-conventions.md` 파일이 정상적으로 생성됨
  - `docs/01_governance/README.md`에 새 문서 링크가 포함됨
  - Markdown 문법 검사에 통과함

## 6. 승인 상태 및 증적

- **승인 상태**: APPROVED
- **승인 증적 식별자**: APV-DOC-001
- **승인 내역**:
  - **승인자**: 사용자 (User-A)
  - **승인 범위**: `docs/01_governance/` 내 코딩 컨벤션 문서 추가
  - **승인 시각**: `2026-09-10T01:00:00Z` (UTC) / `2026-09-10 10:00:00 KST`
  - **철회/만료 규칙**: 프로젝트별 명시 승인 정책에 따르며, 정책이 없거나 승인 조건이 불명확하면 Dispatch하지 않고 사람 검토로 전환한다. (허용 경로 외 파일 수정 시 승인 즉시 철회)
```
