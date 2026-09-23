# BL-0005: Orchestrator Runtime DB 실제 운영 기준 확립 및 이관

- **상태**: 제안됨 (Proposed)
- **우선순위**: P1
- **등록일**: 2026-09-22 (KST)
- **관련 문서**: [Orchestrator Runtime DB 운영 기준](../01_governance/orchestrator-runtime-db-operations.md)

## 설명
Orchestrator의 상태와 기록을 관리하는 Runtime SQLite DB를 안정적으로 운영하기 위한 실제 설정 및 이관 작업을 수행한다. 현재는 `ORCHESTRATOR_JULES_STATE_DIR`를 이용해 **Jules 전용 상태 저장소 팩토리(`get_jules_state_repository`)가 준비**되었고, 이를 `execute_review_handoff`에 `jules_state_repository_factory` 인자로 주입할 수 있도록 통합 지점까지 구현 완료된 상태이다. 그러나 운영 환경용 Runtime DB를 실제로 초기화하거나 전체 시스템 진입점에서 팩토리를 실제로 주입하는 작업은 여전히 제외되어 있다.

따라서 실제 환경을 구성하고, `ORCHESTRATOR_JULES_STATE_DIR` 환경 변수 적용, 최상위 진입점 호출부 연결, 실제 DB 생성, 권한 적용(`ubuntu:ubuntu`), 백업 및 복구 체계(현재 미구성)를 구축하는 것은 후속 Codex 운영 작업으로 수행되어야 한다.

본 백로그는 향후 승인된 기반에서 실제 환경 설정 및 시스템 변경(디렉터리/DB 생성 및 연결 등)을 완수하는 것을 목표로 한다.

## 사용자 결정 필요 사항
실행 계정은 `ubuntu:ubuntu`로 승인 완료되었으며, 실제 운영 환경 적용(DB 생성 및 쓰기)은 후속 Codex 운영 작업으로 진행할 예정이다.
백업 및 복구는 현재 미구성 상태이며, 이 작업을 진행하기 전에 아래 백업 및 복구 관련 사항들에 대한 추가 승인과 결정이 필요하다:

1. **백업 정책 (Backup Policy)**
   - 백업 실행 주기 (예: 매일 오전 3시, 매시간 등)
   - 백업 데이터의 보존 기간 (예: 30일 보관, 1년 보관 등)
2. **복구 목표 (Recovery Objectives)**
   - **RPO (Recovery Point Objective)**: 허용 가능한 최대 데이터 손실 시간.
   - **RTO (Recovery Time Objective)**: 장애 발생 시 복구까지 허용되는 최대 시간.

## 제약 및 통제 사항
- 이 작업에서는 **실제** 디렉터리 생성, 권한 변경, 백업/복구 테스트 및 설정 작업이 이루어지게 되므로, 사전에 위의 결정 사항이 확정되어야 한다.
- 모든 시스템 변경(크론탭 등록, 디렉터리 권한 부여, 환경 변수 변경 등)은 기록되어 검토되어야 한다.
- 보안 원칙에 따라, 어떠한 설정이나 로그에도 API 키, 토큰, 원시 프롬프트, 실제 DB 내용이 포함되어서는 안 된다.

## 목표
사용자 결정이 완료되면, 해당 내용을 바탕으로 인프라 프로비저닝 또는 구성 스크립트를 작성하고 실제 경로로의 데이터베이스 이관 및 백업/복구 스케줄러 등록을 완수한다.

## 변경 이력

| 날짜 (KST) | 변경자 | 변경 내용 |
|------------|--------|-----------|
| 2026-09-22 | Jules | 최초 등록 |
| 2026-09-23 | Jules | 환경 변수(`ORCHESTRATOR_JULES_STATE_DIR`) 도입으로 인한 이관 계획 내용 갱신 |
| 2026-09-23 | Jules | 상태 저장소 팩토리 생성 및 테스트 연결 준비 완료 상태로 변경 |
| 2026-09-23 | Jules | review_handoff 내 jules_state_repository_factory 통합 지점 구현 상태로 갱신 |

## 진행 상황 및 업데이트

- **업데이트 일자 (미정)**: 최상위 진입점(execute_review_handoff_with_repository)을 통해 저장소 팩토리를 주입받아 1:1:1 결속 영속화를 지연 실행하는 통합 준비가 완료됨. 실제 운영 DB 생성·쓰기, ubuntu:ubuntu 권한 적용, 백업·복구는 후속 Codex 운영 작업으로 남아 있으므로 '제안됨' 상태를 유지함.
