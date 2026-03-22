# Lessons Learned

- When presenting after-tax backtest metrics, do not apply tax directly to equity curve deltas.
  Always compute tax from realized gains at transaction level (sell events), aggregate by tax year,
  then apply deduction/rate. Add a tax ledger output to make assumptions auditable.
- 사용자가 기준 엔진(원본 코드)을 제공했을 때는, 명시적 승인 없이 대체 구현으로 실행하지 않는다.
  먼저 원본 코드 그대로 재현 실행을 하고, 대체/개선 엔진은 분리 실험으로 제안한다.
- 사용자가 스트레스 테스트 구간을 특정(예: 2011년 이전)하면, 임의 구간 대체 없이 해당 구간을 반드시 포함해 보고한다.
  보고 전에 요청 구간 포함 여부를 체크리스트로 검증한다.
- 사용자가 알림 UI 샘플(이미지/스크린샷)을 제공하면, 섹션/문구/핵심 필드명을 샘플에 맞춰 우선 정렬하고 구현한다.
  "정보는 맞지만 형태가 다른" 상태로 완료 처리하지 않는다.
- 사용자가 "제가 해야 할 일 최소화"를 요청하면, 자동화 경로를 우선 제안하고
  사용자가 직접 해야 하는 항목을 1~2개 수준으로 축소해 명확히 분리 전달한다.
- 알림 UX 피드백이 오면 "읽기 좋은 문장"보다 "계기판형(수치+임계값)"을 우선한다.
  특히 액션 유무에 따라 템플릿 길이를 분리(무액션=짧게, 액션=상세)해야 실전 가독성이 높다.

- Step 진행 중 사용자가 숨은 선행조건(예: `transactions`, `build_liquidity_summary`)을 지적하면, 즉시 worktree의 미완성 테스트/수정 파일을 점검해 선행조건을 먼저 정리한 뒤 본 작업 범위만 마무리한다.
  특히 Task 3 범위 파일(inbox/export integration)은 섣불리 커밋하지 말고 scope 밖 변경은 되돌리거나 제외한다.
- 사용자가 특정 skill(예: `$using-superpowers`, `$review`)을 명시하면, 작업/질문 전에 해당 skill 사용을 먼저 명시하고 그 흐름에 맞춰 진행한다.
  skill 이름을 나중에 반영하거나 생략한 채 바로 본론으로 들어가지 않는다.
- IDE/Python interpreter 문제에서 `.vscode/settings.json`이나 `.venv`만 고쳤다고 해결로 간주하지 않는다.
  사용자가 "아직도 안 된다"고 하면 곧바로 VS Code/Cursor의 workspace interpreter internal storage/cache가 설정을 덮어쓰는 가능성을 점검하고,
  `Python: Clear Workspace Interpreter Setting` + Python Output 로그 확인을 다음 단계의 기본 루틴으로 삼는다.
- 사용자가 멀티-매니저 구조에서 "각 섹터 매니저는 틀만, 총괄 AI는 제대로"라고 범위를 조정하면,
  개별 매니저 고도화를 현재 프로젝트 안에서 과하게 진행하지 않는다.
  우선은 schema/shell/summary contract만 유지하고, 구현 깊이는 총괄 orchestrator에 집중한다.

## 2026-03-09
- 사용자 환경 제약은 세션 중 계속 유지되는 기본 가정으로 취급한다. 특히 삼성증권은 API 연동이 없고 주문은 수동 입력이라는 점을 운영/대시보드 설계의 기본 전제로 삼는다.
- 실행 보드를 설계할 때는 자동집행보다 수동 주문 체크리스트/주문안 생성 UX를 우선한다.
- 사용자가 AI 매니저 톤에 대해 피드백하면 전략 용어를 전면에 내세우지 말고, 쉬운 한국어로 먼저 설명한 뒤 필요할 때만 내부 상태명/전문용어를 보조로 붙인다. 특히 운영판 AI는 'buffer 구간' 같은 엔진 용어보다 사용자가 바로 이해할 행동언어를 우선한다.

## 2026-03-11
- 빌드 명령에 `| tail -N`, `| head -N` 등 파이프 요약을 절대 쓰지 않는다. 원본 stdout/stderr를 유지한 채 실행하고, 로그가 길면 `tee /tmp/build.log`로 저장한다. 빌드 완료 후에만 마지막 30줄을 별도로 확인한다. `set -o pipefail`로 실패 코드가 가려지지 않게 한다. 패턴: `set -o pipefail && npm run build 2>&1 | tee /tmp/build.log`
- 브라우저 검증 시 내장 브라우징 매니저(IDE 내장 브라우저)를 절대 사용하지 않는다. 반드시 `browser_subagent` 도구만 사용한다. subagent가 내부적으로 view_file이나 replace_file_content로 브라우저 설정을 건드리지 않도록 Task 설명에 "브라우저 설정 파일을 건드리지 말고 바로 URL을 열어라"고 명시한다.
- `npx vite preview`로 프리뷰 서버를 띄울 때 npx 다운로드 지연으로 UI에서 "멈춤"처럼 보이는 문제 발생. 대안:- `python3 -m http.server`는 `npx vite preview`보다 안정적이지만 캐시 헤더를 설정하지 않아 Playwright 브라우저가 이전 빌드 JS를 캐시할 수 있음. 빌드 후 검증 시 `about:blank`으로 먼저 이동하거나, CDPSession의 `Network.clearBrowserCache`를 호출해서 캐시를 비워야 함.
- Playwright MCP(`@playwright/mcp@latest`)를 `mcp_config.json`에 추가하면 `mcp_playwright_browser_*` 도구로 브라우저 제어 가능. `browser_subagent`보다 직접 제어가 안정적.

## 2026-03-18
- 사용자가 "프론트는 나중에 더 손볼 것"이라고 범위를 조정하면, 현재 세션은 UI 야심보다 기능 동작과 계약 정합성에 집중한다. 다만 초안이어도 기존 디자인 톤/레이아웃 언어는 유지해야 하므로, 새 시각 실험보다 기존 스타일의 얇은 확장을 우선한다.
- 사용자가 기존 프론트 기준 UI를 지적하면, 현재 worktree/브랜치만 보지 말고 사용자가 지정한 실제 작업 경로(예: 별도 git worktree)의 기준 파일까지 직접 확인한 뒤 톤/레이아웃 기준을 정한다. 기억에 의존해 현재 스타일을 "기존 톤"으로 가정하지 않는다.
