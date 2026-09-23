# Worklog 인덱스

실제로 수행한 작업, 결정과 검증 결과를 시간순으로 기록한다.

- [WL-0001](WL-0001-2026-09-08-document-management-foundation.md) — 문서 관리 규칙, 기록 경로와 템플릿을 도입했다.
- [WL-0002](WL-0002-2026-09-08-document-link-and-archive-cleanup.md) — 설계 문서 링크와 중복 archive 사본을 정리했다.
- [WL-0003](WL-0003-2026-09-08-governance-document-relocation.md) — 거버넌스 문서를 통합하고 현재 참조를 갱신했다.
- [WL-0004](WL-0004-2026-09-08-design-document-relocation.md) — 활성 설계 문서를 설계 경로로 통합하고 현재 참조를 갱신했다.
- [WL-0005](WL-0005-2026-09-08-archive-document-relocation.md) — 설계 archive 문서를 중앙 보관 경로로 통합했다.
- [WL-0006](WL-0006-2026-09-08-document-structure-completion.md) — 전체 문서 지도와 최종 링크 검증을 완료했다.
- [WL-0007](WL-0007-2026-09-09-agent-context-and-rr-update.md) — 공통 에이전트 작업 지도와 Jules·Claude Code R&R을 정리했다.
- [WL-0008](WL-0008-2026-09-09-release-promotion-governance-update.md) — 테스트계 검증과 릴리스 태그 기반 운영 승격 기준을 정리했다.
- [WL-0009](WL-0009-2026-09-09-github-jules-guardrails-readiness-check.md) — GitHub 보호·자동 병합·Jules 접근 상태를 읽기 전용으로 점검했다.
- [WL-0010](WL-0010-2026-09-09-github-ruleset-jules-minimum-permission-proposal.md) — GitHub 보호 설정과 Jules 최소 권한의 승인안을 작성했다.
- [WL-0011](WL-0011-2026-09-09-main-ruleset-application.md) — GitHub main 보호 ruleset을 적용하고 API로 활성 상태를 검증했다.
- [WL-0012](WL-0012-2026-09-09-design-baseline-consistency-review.md) — 설계 정합성 검토 및 분석 문서 작성 작업을 기록했다.
- [WL-0013](WL-0013-2026-09-09-mvp-scalability-guardrails.md) — AN-0005에 따른 MVP 확장성 가드레일 계획 문서를 작성했다.
- [WL-0014](WL-0014-2026-09-10-approved-baseline-alignment.md) — 사용자 승인 완료 정책(스택, DB 네이밍 규칙 등)을 아키텍처 및 DB 문서에 정합화했다.
- [WL-0015](WL-0015-2026-09-10-kst-and-korean-writing-rules.md) — 공통 에이전트 한국어 작성 및 KST 시간 기준 규칙을 거버넌스 문서에 반영했다.
- [WL-0016](WL-0016-2026-09-10-review-domain-mvp-deferral.md) — 리뷰 도메인을 MVP 범위 밖으로 정리하고, 모델·API·DB 설계 선반영을 제거했다.
- [WL-0017](WL-0017-2026-09-10-review-ui-mvp-deferral.md) — 리뷰 도메인 MVP 제외 정책에 따라 화면 명세서의 리뷰 UI 선반영을 제거했다.
- [WL-0018](WL-0018-2026-09-10-sensitive-domain-policy-analysis.md) — 민감 도메인 정책 옵션 및 인프라 체크리스트 분석 작업을 기록했다.
- [WL-0019](WL-0019-2026-09-10-sensitive-policy-design-alignment.md) — 승인 완료된 민감 도메인 정책 8건 및 초기 인프라 기준을 설계 문서에 정합화했다.
- [WL-0020](WL-0020-2026-09-10-orchestrator-action-plan-draft.md) — 별도 Orchestrator 프로젝트 이전 전 Task Contract 기반 Action Plan 초안을 기록했다.
- [WL-0021](WL-0021-2026-09-10-orchestrator-poc-checklist.md) — Thin Orchestrator Action Plan을 Superseded 문서로 전환하고 POC 수행 기록을 남겼다.
- [WL-0022](WL-0022-2026-09-19-thin-orchestrator-initial-import.md) — Thin Orchestrator 초기 이식과 런타임 설정 로더 추가 작업을 기록했다.
- [WL-0023](WL-0023-2026-09-19-orchestrator-document-reconciliation.md) — 하위 Orchestrator 문서를 루트 체계로 이관하고 규칙 충돌을 정합화했다.
- [WL-0024](WL-0024-2026-09-19-user-decision-inventory.md) — 사용자 승인 완료 정책 및 미결 사항 인벤토리 작성과 후속 PR 분할안 기록 작업을 정리했다.
- [WL-0025](WL-0025-2026-09-19-decision-register-foundation.md) — 결정 레지스터 초안 작성 및 문서 지도 반영 작업을 정리했다.
- [WL-0026](WL-0026-2026-09-22-jules-main-start-branch-guard.md) — Jules 세션 main 시작 및 예상 브랜치 사후 결속 정책을 어댑터와 거버넌스에 반영했다.
- [WL-0027](WL-0027-2026-09-22-persistent-session-binding.md) — Jules 세션 ID, 브랜치명, PR 번호를 SQLite DB에 영속 결속하여 1:1:1 중복 및 불일치를 차단하는 모델을 추가했다.
- [WL-0028-2026-09-22-orchestrator-runtime-db-operating-baseline](WL-0028-2026-09-22-orchestrator-runtime-db-operating-baseline.md) — Orchestrator Runtime DB 저장 원칙 및 미결 백업·복구 기준 문서화 완료 기록.
- [WL-0029-2026-09-23-orchestrator-jules-state-dir](WL-0029-2026-09-23-orchestrator-jules-state-dir.md) — Orchestrator 상태 디렉터리 경로 환경 변수 로더 추가 및 외부 경로 검증 로직 구현.
- [WL-0030-2026-09-23-orchestrator-repository-integration](WL-0030-2026-09-23-orchestrator-repository-integration.md) — Orchestrator 상태 저장소 연동 팩토리 구현 및 테스트 환경 구성 완료 기록.
- [WL-0031-2026-09-23-orchestrator-runtime-binding-injection](WL-0031-2026-09-23-orchestrator-runtime-binding-injection.md) — Orchestrator 완료 검토 인계 과정에 상태 저장소 팩토리 주입 지점 구현.
- [WL-0032](WL-0032-2026-09-23-runtime-entrypoint-integration.md) — 최상위 검토 인계 진입점 통합 준비와 테스트 및 Worklog 갱신을 완료했다.
- [WL-0033-2026-09-23-runtime-db-initialization-documentation](WL-0033-2026-09-23-runtime-db-initialization.md) — 외부 상태 디렉터리 확인, 빈 DB 초기화 및 최소 권한 적용을 비민감 범위 내에서 문서에 정합화한 내역 기록.
