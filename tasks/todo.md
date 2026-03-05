# TODO - Serena / Context7 / Playwright setup

- [x] Confirm install target type (MCP vs skill) and map each tool
- [x] Install missing runtime prerequisites (uv for Serena)
- [x] Register MCP servers in Codex config for Serena, Context7, Playwright
- [x] (Optional) Install Playwright skill from GitHub curated skills
- [x] Verify installation with `codex mcp list` and per-server `codex mcp get`

## Review
- Added MCP servers:
  - `serena` → `uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context codex`
  - `context7` → `npx -y @upstash/context7-mcp@latest`
  - `playwright` → `npx -y @playwright/mcp@latest`
- Installed Playwright skill from GitHub curated skills into `~/.codex/skills/playwright`
- Verified all 3 servers appear as `enabled` in `codex mcp list`

---

# TODO - TQQQ 전략 고도화 (Brainstorming)

- [x] (1) 프로젝트 컨텍스트 탐색 (파일/문서/변경이력)
- [x] (2) 명확화 질문 1개씩 진행 (목표/제약/성공기준)
- [x] (3) 2~3개 접근안 + 트레이드오프 제시
- [x] (4) 섹션별 설계안 제시 및 사용자 승인 획득
- [x] (5) 설계 문서 작성 (`docs/plans/YYYY-MM-DD-<topic>-design.md`)
- [x] (6) writing-plans 단계로 전환

## Review (진행중)
- TradingView 코드 로드 완료(1297 lines)
- 핵심 엔진 블록 위치 확인:
  - RTH 종가 이벤트: `tradingview.txt:302-315`
  - 상태 업데이트/의사결정: `tradingview.txt:402-688`
  - 텔레그램 알림 출력: `tradingview.txt:1137-1297`

- 아키텍처 재검토 요청 반영: 누락 가능 항목(시간대/세금 환산/데이터 정합/알림 멱등성/실험 거버넌스) 점검 예정


## 설계 섹션 승인 현황
- [x] 섹션1: 전체 아키텍처(2안+3전환 트리거)
- [x] 섹션2: 데이터 계약 & 정합성
- [x] 섹션3: 신호엔진/백테스트/검증 게이트
- [x] 섹션4: 2차 실험 프레임
- [x] 섹션5: 3차 운영자동화/웹앱 (텔레그램 UI 매핑 포함)

- 텔레그램 샘플 UI 반영 요구 확인: `9551781008_192159903_f42a776fa8b229fbdd2105c6cd411d85.webp`

## 작성된 산출물
- `docs/plans/2026-03-05-tqqq-strategy-design.md`
- `docs/plans/2026-03-05-tqqq-strategy-implementation-plan.md`
