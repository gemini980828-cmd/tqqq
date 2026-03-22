# Alpha Wealth Desk UI Flow QA Plan

작성일: 2026-03-22  
목적: 현재까지 구현된 Home / Reports / Orchestrator / Stock Research workbench의 핵심 사용자 플로우를 실제 브라우저에서 검증하기 위한 QA 체크리스트

---

## 검증 범위

### 1. Home
- Home 진입 가능
- Manager hub 노출 확인
- Priority / Cross-manager / Orchestrator 섹션 확인

### 2. Managers
- `#/managers` 진입 가능
- `#/managers/stocks` 진입 가능
- Managers sub-nav에서 Stocks 탭 정상 활성화

### 3. Stock Research Workbench
- 상단 Queue 노출
- Queue 클릭 시 detail 종목 변경
- 좌측 Screener row 클릭 시 detail 종목 변경
- Layout이 좌우 독립 스크롤형 workbench 구조인지 확인

### 4. Reports
- `#/reports` 진입 가능
- KPI / Narrative / Comparison / Context 섹션 노출
- Context 액션 버튼 클릭 시 관련 manager 이동

### 5. Orchestrator
- Home에서 prompt starter 또는 직접 질문 입력 가능
- 질문 후 응답 카드 노출
- Next action 버튼 존재 시 동작 확인

---

## 완료 기준

- 위 5개 영역의 핵심 플로우가 실제 브라우저에서 재현됨
- 치명적 라우팅 오류 없음
- build/lint 통과 상태 유지
