# Alpha Wealth Desk Home 레이아웃 개편 실행 지시서

작성일: 2026-03-21  
목적: 프론트엔드 레이아웃 개편 작업 시 계약 불일치, 라우팅 오류, inert UI, 중복 구현을 최대한 줄이기 위한 상세 작업 지시서  
범위: **Home 중심 레이아웃 개편 + Orchestrator rail + manager entry flow 정리**  
비범위: 색상 체계 재설계, 폰트 리브랜딩, 신규 디자인 시스템 구축

---

# 1. 이 문서의 목표

이 문서는 “데모 느낌으로 Home을 바꾸자”를 실제 작업 가능한 수준으로 쪼갠 지시서입니다.

이 문서의 목적은 두 가지입니다.

1. **레이아웃 개편 방향을 명확히 고정**
2. **이전 프론트 작업에서 발생한 문제를 다시 반복하지 않도록 방지**

특히 아래 실수를 다시 하지 않는 것이 중요합니다.

- 백엔드 계약과 다른 타입 선언
- `goto_screen`/manager route 불일치
- 클릭 가능해 보이지만 실제 동작하지 않는 버튼
- `orchestrator_prompt_starters` 같은 새 계약을 무시하고 기존 fixture/quick prompt를 계속 쓰는 것
- Home에 새 섹션을 추가만 하고, 정작 정보 우선순위는 바꾸지 않는 것

---

# 2. 최종 목표 상태

Home은 아래 구조가 되어야 합니다.

## 상단
- 기존 global nav 유지
- Hero는 compact welcome/status bar로 축소

## 본문
### 좌측 메인 허브
1. Priority Actions
2. Cross-Manager Alerts
3. Manager Workbench
4. Recent Activity
5. Secondary Discovery (Research / Reports)

### 우측 고정 패널
- Orchestrator Rail

즉, **현재의 세로형 섹션 나열 페이지를 운영 허브형 2-column 구조로 바꾸는 것**이 핵심입니다.

---

# 3. 반드시 지켜야 하는 계약 원칙

## 3.1 프론트는 백엔드 계약을 재정의하지 말 것

현재 사용해야 하는 백엔드 핵심 필드:

- `priority_actions`
- `cross_manager_alerts`
- `manager_events`
- `research_candidates`
- `report_highlights`
- `orchestrator_prompt_starters`
- `compare_data`
- `home_discovery`

### 중요
다음 필드는 **top-level**입니다.

- `research_candidates`
- `report_highlights`
- `orchestrator_prompt_starters`
- `compare_data`

`home_discovery`는 데이터 본문이 아니라 **우선순위/정렬용 id 집합**으로 사용해야 합니다.

즉:

좋은 방식:
- `home_discovery.priority_action_ids`로 `priority_actions` 정렬
- `home_discovery.report_highlight_ids`로 `report_highlights` 정렬

나쁜 방식:
- `home_discovery.research_candidates`
- `home_discovery.report_highlights`
를 새로 타입 정의해서 소비

---

## 3.2 라우트는 문자열 조합 금지

절대 이렇게 하지 마세요:

- `managerId.replace('_', '-')`
- `/${sourceManager}`
- `"/managers/" + managerId`

이 방식은 이미 한 번 깨졌습니다.

반드시 **중앙 route map**을 사용하세요.

예상 매핑:

```ts
const MANAGER_ROUTE_MAP = {
  core_strategy: '/managers/core-strategy',
  stock_research: '/managers/stocks',
  real_estate: '/managers/real-estate',
  cash_debt: '/managers/cash-debt',
}
```

그리고 `goto_screen`도 공통 해석 규칙을 가져야 합니다.

예:
- backend가 `/managers/core_strategy` 같은 내부 토큰을 주는지
- `/managers/core-strategy` 같은 실제 라우트를 주는지
- `home` 같은 semantic token을 주는지

이건 한 곳에서 normalize해야 합니다.

---

## 3.3 버튼/카드가 보이면 실제 동작해야 함

다음 UI는 inert 상태로 두면 안 됩니다.

- Priority Action CTA
- Action card 전체 클릭
- Cross-manager related link
- Orchestrator next action 버튼
- ManagerActionHeader 내 action 버튼
- prompt starter 버튼

원칙:

> 클릭 affordance가 있는 모든 요소는 실제 navigation 또는 submit을 수행해야 함

---

## 3.4 fixture/preview는 계약 adapter를 통과해야 함

현재 preview/mock는 남길 수 있습니다.  
하지만 반드시 **실제 backend 응답 shape와 동일한 adapter**를 거쳐야 합니다.

즉:
- 실API용 데이터 shape
- preview용 mock shape

가 달라지면 안 됩니다.

좋은 방식:
- `normalizeOrchestratorReply(rawReply)` 같은 함수 사용

나쁜 방식:
- preview용 타입과 실응답 타입이 따로 놀기

---

# 4. 작업 전 선행 체크리스트

작업 시작 전에 아래를 먼저 확인하세요.

- [ ] `app/web/src/App.tsx`의 실제 route 구조 확인
- [ ] `app/web/src/types/appSnapshot.ts`를 backend 기준으로 다시 정렬
- [ ] `app/api/main.py`, `src/tqqq_strategy/ops/dashboard_snapshot.py`, `src/tqqq_strategy/ai/orchestrator_service.py` 기준으로 snapshot/reply shape 확인
- [ ] Home에서 현재 사용 중인 fallback/mock가 실제 계약을 위반하지 않는지 확인
- [ ] route map / screen resolver를 공통 util로 뺄 위치 결정

이 선행 확인 없이 바로 JSX부터 바꾸면 다시 틀어질 가능성이 높습니다.

---

# 5. 파일별 작업 범위

## 5.1 수정 대상 핵심 파일

- `app/web/src/pages/Home.tsx`
- `app/web/src/components/OrchestratorPanel.tsx`
- `app/web/src/components/ManagerCard.tsx`
- `app/web/src/components/ManagerActionHeader.tsx`
- `app/web/src/types/appSnapshot.ts`

## 5.2 추가 가능성이 높은 파일

- `app/web/src/lib/navigation.ts` 또는 유사 util
- `app/web/src/lib/orchestratorReplyAdapter.ts`
- `app/web/src/components/home/*`

## 5.3 가급적 수정 최소화 대상

- `TopNav.tsx`
- manager detail 내부 business logic
- StockResearch workspace 내부 세부 상호작용

이번 작업은 Home shell 재배치가 중심이므로, 다른 manager 내부 기능까지 번지지 않게 하세요.

---

# 6. 타입 정리 지시

## 6.1 `AppSnapshot`에서 반드시 고쳐야 할 점

### `home_discovery`
이 블록은 아래처럼 유지하세요.

```ts
home_discovery?: {
  priority_action_ids?: string[]
  cross_manager_alert_ids?: string[]
  prompt_ids?: string[]
  report_highlight_ids?: string[]
}
```

### top-level로 둬야 하는 필드

```ts
priority_actions?: PriorityAction[]
cross_manager_alerts?: CrossManagerAlert[]
manager_events?: Record<string, EventTimelineItem[]>
research_candidates?: ResearchCandidate[]
report_highlights?: ReportHighlight[]
orchestrator_prompt_starters?: OrchestratorPromptStarter[]
compare_data?: CompareData
```

---

## 6.2 추가 타입 권장

```ts
type ResearchCandidate = {
  idea_id: string
  symbol: string
  status: string
  memo: string
  priority: string
  priority_reason: string
  manager_id: string
  next_action: string
}

type ReportHighlight = {
  id: string
  title: string
  summary: string
  severity: string
  manager_ids: string[]
  updated_at?: string
}

type OrchestratorPromptStarter = {
  id: string
  label: string
  prompt: string
  source_manager_ids: string[]
  intent: string
}
```

이 타입은 backend shape에 맞게 정의하세요.  
임의로 축소/단순화하지 마세요.

---

# 7. Home 레이아웃 개편 지시

## 7.1 현재 Home에서 해야 할 가장 큰 변화

현재 Home은 “섹션 추가형” 구조입니다.

이번 작업에서는 이렇게 바꿔야 합니다.

## 목표 구조

```tsx
<HomePage>
  <HomeHeroCompact />
  <div className="home-shell">
    <HomeActionHub>
      <HomePriorityActions />
      <HomeCrossManagerAlerts />
      <HomeManagerWorkbench />
      <HomeRecentActivity />
      <HomeDiscoverySecondary />
    </HomeActionHub>
    <HomeOrchestratorRail>
      <OrchestratorPanel />
    </HomeOrchestratorRail>
  </div>
</HomePage>
```

---

## 7.2 Home에서 각 섹션의 역할

### `HomeHeroCompact`
역할:
- 소개 문구가 아니라 “운영 시작점” 제공

포함 정보:
- 짧은 headline
- 한 줄 설명
- today action / strategy stance 정도

하지 말 것:
- 긴 product 설명
- metric보다 더 큰 시각적 비중

---

### `HomePriorityActions`
역할:
- 첫 번째 주연 블록

표시 필드:
- `severity`
- `manager_id`
- `title`
- `detail`
- `recommended_action`

동작:
- 카드 클릭 또는 CTA 클릭 시 `goto_screen` 이동

추가 규칙:
- `home_discovery.priority_action_ids` 순서 우선
- 순서 id가 없으면 원본 배열 순서 사용

---

### `HomeCrossManagerAlerts`
역할:
- manager coordination block

표시 필드:
- `title`
- `detail`
- `manager_ids`

동작:
- 관련 manager link 제공
- 가능하면 conflict 대상 manager로 빠르게 이동 가능해야 함

추가 규칙:
- `home_discovery.cross_manager_alert_ids` 순서 우선

---

### `HomeManagerWorkbench`
역할:
- manager entry portal

표시 요구:
- manager 상태
- action required / alerted 상태
- headline
- next action 1줄
- workspace 진입 affordance

주의:
- summary density를 과도하게 올리지 말 것
- card는 “읽는 카드”가 아니라 “들어가는 카드”처럼 보여야 함

---

### `HomeRecentActivity`
역할:
- supporting context

주의:
- Action Center보다 앞에 오면 안 됨
- 크기를 줄여서 supporting section으로 배치
- 최대 4~5개 정도로 압축

---

### `HomeDiscoverySecondary`
역할:
- research/report 후속 탐색

구성:
- `research_candidates`
- `report_highlights`

주의:
- 주연 영역이 아님
- action 이후의 탐색 진입점

---

### `HomeOrchestratorRail`
역할:
- 항상 열려 있는 분석 콘솔

필수 요구:
- 고정 폭
- Home 메인 흐름과 분리된 독립 패널
- 내부 스크롤/입력 영역 구분

데스크탑:
- 오른쪽 rail

태블릿/모바일:
- 아래로 내려오더라도 “독립 패널” 느낌 유지

---

# 8. OrchestratorPanel 작업 지시

## 8.1 prompt source

반드시 이 순서로 사용:

1. `orchestrator_prompt_starters`
2. 없으면 `orchestrator_policy.quick_prompts`
3. 그것도 없으면 local fallback

즉, 새 starter 계약을 우선 소비해야 합니다.

---

## 8.2 응답 표시 구조

필수 순서:

1. `short_answer`
2. `answer`
3. `source_details`
4. `next_action`
5. `go_to_screen`

### source_details
최소 표시:
- manager name
- stale 여부

### next_action
- 텍스트만 두지 말고 실제 action row처럼 보여야 함

### go_to_screen
- 실제 navigation 연결
- 버튼이 보이면 반드시 동작해야 함

---

## 8.3 adapter 레이어 권장

`OrchestratorPanel` 내부에서 raw response shape를 직접 가공하지 말고,

예:

```ts
normalizeOrchestratorReply(rawReply)
```

형태로 한 번 정규화하세요.

이렇게 하면
- preview mock
- 실제 backend reply

를 같은 UI에 안정적으로 연결할 수 있습니다.

---

# 9. ManagerCard / ManagerActionHeader 지시

## 9.1 공통 route resolver 사용

`ManagerCard`와 `ManagerActionHeader`가 서로 다른 방식으로 route를 만들면 안 됩니다.

반드시 공통 함수 사용:

```ts
getManagerRoute(managerId)
resolveScreenRoute(gotoScreen, fallbackManagerId)
```

---

## 9.2 ManagerCard 역할

바뀌어야 하는 점:
- summary card → workspace entry tile

필수:
- action required 상태
- alert 상태
- stale 상태
- entry affordance

권장:
- 하단에 “Open workspace” 또는 유사 wording

---

## 9.3 ManagerActionHeader 역할

상단에서 아래 3개만 명확히 보여주세요.

1. current manager priority action
2. current manager related cross alerts
3. current manager recent events

주의:
- 버튼은 inert 금지
- 관련 manager link는 반드시 실제 route로 이동해야 함

---

# 10. 절대 하지 말아야 할 것

1. **backend 계약을 프론트 편의대로 재배열하지 말 것**
2. **route를 문자열 replace로 만들지 말 것**
3. **버튼/카드에 hover/cursor만 넣고 실제 동작 연결 안 하지 말 것**
4. **Home에 새 블록만 더하고 전체 레이아웃은 그대로 두지 말 것**
5. **preview/mock 타입을 실제 응답 타입과 분리해두지 말 것**
6. **research/report를 action보다 더 앞세우지 말 것**
7. **timeline을 다시 주연 섹션으로 키우지 말 것**

---

# 11. 권장 구현 순서

## Phase 1 — 계약/라우팅 정리

- [ ] `AppSnapshot` 타입 수정
- [ ] route map / screen resolver 추가
- [ ] orchestrator reply adapter 추가

### 완료 기준
- 타입이 실제 backend shape와 맞음
- route 생성이 중앙화됨

---

## Phase 2 — Home shell 재배치

- [ ] Home을 2-column shell로 분리
- [ ] hero compact화
- [ ] priority actions를 최상단으로 이동
- [ ] cross-manager alerts를 priority 바로 아래 배치
- [ ] manager workbench를 그 아래로 이동
- [ ] timeline은 supporting zone으로 축소
- [ ] discovery는 하단 secondary zone으로 유지

### 완료 기준
- 페이지 첫 시선이 action → alert → manager 순으로 흐름

---

## Phase 3 — Orchestrator rail 승격

- [ ] OrchestratorPanel을 rail 문맥에 맞게 배치
- [ ] prompt starters 실제 계약 기반으로 렌더링
- [ ] next action / go_to_screen 연결
- [ ] source transparency 유지

### 완료 기준
- Home 오른쪽에 항상 켜진 분석 콘솔처럼 보임

---

## Phase 4 — Manager entry polish

- [ ] ManagerCard를 workspace entry tile로 다듬기
- [ ] ManagerActionHeader 버튼/링크 연결
- [ ] cross-manager 이동 정확성 검증

### 완료 기준
- Home과 manager pages 간 이동 흐름이 막히지 않음

---

# 12. 검증 체크리스트

## 타입/정적 검증
- [ ] `cd app/web && npm run lint`
- [ ] `cd app/web && npm run build`

## 기능 검증
- [ ] Priority Action 클릭 시 올바른 manager/workspace로 이동
- [ ] Cross-Manager Alert 관련 manager link 이동 확인
- [ ] ManagerCard 클릭 시 올바른 route 이동
- [ ] Orchestrator next action 버튼 이동 확인
- [ ] Orchestrator prompt starter 클릭 시 질문 제출 확인

## 계약 검증
- [ ] `research_candidates`가 top-level에서 읽힘
- [ ] `report_highlights`가 top-level에서 읽힘
- [ ] `orchestrator_prompt_starters`를 실제 소비함
- [ ] `home_discovery`는 id 정렬용으로만 사용함

## 레이아웃 검증
- [ ] 데스크탑에서 좌/우 구조가 명확함
- [ ] Orchestrator가 독립 rail처럼 보임
- [ ] action → alert → manager 순서가 눈에 들어옴
- [ ] discovery는 하위 보조 영역처럼 보임

---

# 13. 완료 정의

이 작업은 아래를 만족해야 완료입니다.

1. Home이 더 이상 “세로형 섹션 목록”처럼 보이지 않는다
2. 사용자가 첫 화면에서 곧바로 action을 이해할 수 있다
3. 관련 manager로 바로 이동할 수 있다
4. Orchestrator가 항상 열려 있는 실행 콘솔처럼 보인다
5. 타입/라우팅/계약 mismatch가 없다
6. 클릭 affordance가 있는 UI는 모두 실제 동작한다

---

# 14. 최종 한 줄 지시

이번 작업의 본질은 **새 카드 몇 개를 더 붙이는 것**이 아니라,  
**Home을 action-first 운영 허브로 재배치하고, 오른쪽에 Orchestrator rail을 붙여 사용자의 판단과 이동 흐름을 다시 설계하는 것**입니다.
