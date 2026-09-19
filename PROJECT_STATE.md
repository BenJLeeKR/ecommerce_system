# PROJECT_STATE.md

> 이 문서는 단일 소비자 직접 판매(Direct-to-Consumer) E-commerce MVP 구축 프로젝트의 현재 상태, 환경, 확정/미결 정책을 Context 관리 목적으로 요약합니다. 세부 정책은 링크된 개별 기준 문서를 참조하십시오.

## 1. 갱신 정보
* **최종 갱신 시점:** 2026-09-19 16:16:52 KST
* **기준 main SHA:** `05c790053a1a588e74683e4cf1448b33f6059913`
* **문서 갱신 원칙:** Task Contract 완료, 중요 정책 변경 또는 인프라 환경 전환 시마다 본 문서를 갱신하여 최신 Context를 유지합니다.

## 2. 현재 단계 및 구현 착수 상태
* **현재 단계:** 초기 계획 및 거버넌스 정의, 기본 문서 구조화 단계.
* **구현 착수 상태:**
  * 프론트엔드/백엔드 기본 골격 및 핵심 로직 구현 전 상태.
  * Thin Orchestrator POC 검증 완료 후, 기본 Git 추적 대상(`.orchestrator/` 내 실행 코드, 테스트 코드, `AGENTS.md`, `.env.example`) 구조화 진행.

## 3. 환경 상태
* **개발 환경:** 로컬 개발 환경 구성 진행 중 (현재 DB 접속 및 마이그레이션을 위한 PostgreSQL 권한 설정 보류 상태).
* **테스트 환경:** 구성 전 확인 필요.
* **운영 환경:** 인프라 초기 기준(RPO 24h, RTO 4h, 매일 03:00 KST 자동 백업)만 정의된 상태이며 실제 리소스 배포는 이루어지지 않음.
* **Git 추적 정책:** `.orchestrator/` 내부에는 실행/테스트 코드, `AGENTS.md`, `.env.example`만 추적되며, 로컬 `.env`, SQLite DB, 기타 문서 파일은 추적하거나 생성하지 않습니다.

## 4. 확정된 결정 사항
주요 확정 사항은 다음 문서를 참조하십시오.
* **프로젝트 범위 및 기술 스택:**
  * Next.js + NestJS + PostgreSQL + Prisma 기반 모듈형 모놀리스 구조. ([tech-stack-decision.md](./docs/00_project/tech-stack-decision.md))
  * Review 도메인은 MVP 범위에서 완전 제외. ([project-scope.md](./docs/00_project/project-scope.md))
* **민감 도메인(주문, 결제, 재고) 정책:**
  * 재고 TTL 15분, 결제 재시도 최대 3회 제한, 보상 트랜잭션 등 복잡한 분산 로직 제외. ([rules-sensitive-domain.md](./docs/01_governance/rules-sensitive-domain.md))
* **문서 거버넌스:**
  * 모든 문서는 `docs/` 내 구조를 엄격히 준수. KST 기준 시각 명시 및 한국어 작성 원칙. ([document-management-rules.md](./docs/01_governance/document-management-rules.md))

## 5. 미결 사항 및 확인 필요 사항
* **승인 대기 (Codex 권장안):**
  * 데이터베이스 세부 스키마 및 데이터 타입(UUID, Enum, Prisma 매핑 등) 최종 정책.
* **확인 필요:**
  * 로컬 및 스테이징 환경에 대한 PostgreSQL 접근 권한 확보 방안.
  * 테스트 환경 및 CI/CD 파이프라인의 구체적 배포 절차.

## 6. 다음 우선 작업 및 선행 조건
* **우선 작업:** 데이터베이스 스키마 및 Prisma 모델 설계 확정.
* **선행 조건:** PostgreSQL 데이터베이스 접근 권한 승인 및 퍼블릭 DB 연결 확보. (마이그레이션 실행 전 필수)
