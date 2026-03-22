# Alpha Wealth Desk 프론트엔드 전달서

작성일: 2026-03-21  
범위: **디자인 제외**, UI/UX 흐름 및 기능 연결 중심  
전제: 백엔드 snapshot 계약 확장 완료

---

## 1. 목적

이 문서는 프론트엔드가 다음 단계에서 무엇을 붙여야 하는지 정리한 전달서입니다.

이번 단계의 핵심은:

- 화면을 더 예쁘게 만드는 것이 아니라
- **사용자가 다음 행동을 더 빨리 이해하고**
- **manager 간 이동이 자연스럽고**
- **orchestrator가 실제 액션 인터페이스처럼 동작하도록**
- 백엔드에서 추가된 계약을 UI에 연결하는 것입니다.

---

## 2. 이번 백엔드에서 이미 준비된 데이터

프론트에서 바로 사용할 수 있는 신규 snapshot 블록:

- `home_discovery`
- `priority_actions`
- `cross_manager_alerts`
- `research_candidates`
- `orchestrator_prompt_starters`
- `report_highlights`
- `manager_events`
- `compare_data`

추가로 `event_timeline`는 이제 아래 정보를 포함합니다:

- `id`
- `title`
- `category`
- `severity`
- `source_manager_id`
- `entity_type`
- `entity_id`

Orchestrator 응답도 확장되었습니다:

- `short_answer`
- `source_details`
- `supporting_managers`
- `next_action`
- `go_to_screen`

---

## 3. 프론트 우선순위

### 1순위
- Home에서 신규 discovery/action 블록 연결
- OrchestratorPanel에서 새 응답 구조 연결

### 2순위
- Manager 화면에서 `manager_events` 및 `priority_actions` 활용

### 3순위
- Reports/Research에서 `report_highlights`, `research_candidates`, `compare_data` 활용

---

## 4. 화면별 해야 할 일

## 4.1 Home

대상 파일 예상:

- `app/web/src/pages/Home.tsx`
- `app/web/src/components/ManagerCard.tsx`
- `app/web/src/components/OrchestratorPanel.tsx`

### 기능적으로 해야 할 일

1. **우선 액션 영역 추가**
   - `priority_actions`를 상단 또는 hero 하단에 노출
   - 각 항목은 최소 아래를 보여주면 됨:
     - `title`
     - `detail`
     - `severity`
     - `recommended_action`
   - 클릭 시 `goto_screen`으로 이동

2. **cross-manager alert 영역 추가**
   - `cross_manager_alerts`를 별도 블록으로 분리
   - 이 블록의 목적은 “단일 manager 상태”가 아니라 “같이 봐야 하는 문제”를 알려주는 것
   - manager badge/label 정도만 붙여도 충분

3. **discovery entry 연결**
   - `home_discovery.priority_action_ids`
   - `home_discovery.cross_manager_alert_ids`
   - `home_discovery.prompt_ids`
   - `home_discovery.report_highlight_ids`
   - 프론트는 이 id를 기준으로 관련 블록의 우선 노출 순서를 맞추면 됨

4. **event_timeline 표시 개선**
   - 기존 단순 date/type/detail 표시에서
   - `title`, `severity`, `source_manager_id`를 활용해
   - “무슨 일이 누구에게서 발생했는가”가 더 잘 보이게 변경

5. **manager card와 액션 연결 강화**
   - `ManagerCard`에서 이미 summary가 있더라도
   - `priority_actions`와 연결된 manager는 더 쉽게 들어갈 수 있어야 함
   - 예: “다음 액션 있음” 상태 표시, 클릭 시 manager 페이지 이동

### UX 목표

- Home이 단순 상태판이 아니라
- “지금 어디부터 들어가야 하는지”를 알려주는 허브가 되어야 함

---

## 4.2 OrchestratorPanel

대상 파일 예상:

- `app/web/src/components/OrchestratorPanel.tsx`
- 관련 orchestrator UI 하위 컴포넌트들

### 기능적으로 해야 할 일

1. **답변 구조를 1단/2단으로 분리**
   - `short_answer`를 상단 요약으로 먼저 노출
   - `answer`는 상세 영역으로 분리

2. **다음 행동 표시**
   - `next_action`을 별도 action row로 표시
   - 클릭 가능하면 `go_to_screen`으로 이동

3. **source transparency 표시**
   - `source_details`를 사용해
     - 어떤 manager가 답변 근거인지
     - stale 여부가 있는지
     - recommended action이 무엇인지
   - 최소한 manager 이름 + stale 여부 정도는 노출 필요

4. **supporting managers 표시**
   - `supporting_managers`가 2개 이상이면
   - “이 답변은 여러 manager 기준으로 조합됨”을 보여줘야 함

5. **prompt starters를 backend 기준으로 통일**
   - 기존 quick prompt 하드코딩이 있다면
   - `orchestrator_prompt_starters` 기반으로 렌더링 전환

### UX 목표

- Orchestrator가 단순 채팅창이 아니라
- “요약 → 근거 → 다음 이동” 구조를 가진 운영 인터페이스처럼 보여야 함

---

## 4.3 Manager 페이지

대상 파일 예상:

- `app/web/src/pages/managers/*`

### 기능적으로 해야 할 일

1. **manager별 event 연결**
   - `manager_events[manager_id]`를 각 manager 페이지에 붙이기
   - 이 영역은 “최근 변화 / 최근 경고 / 최근 판단 변화” 용도

2. **priority action 소비**
   - 현재 manager에 해당하는 `priority_actions`가 있으면
   - 페이지 상단에서 보여주기

3. **cross-manager 관련성 힌트**
   - 현재 manager가 `cross_manager_alerts.manager_ids`에 포함되면
   - 관련 manager로 넘어갈 수 있는 보조 링크 제공

### UX 목표

- manager 화면이 설명 페이지가 아니라
- “이 manager에서 지금 처리할 것”이 드러나는 workbench가 되어야 함

---

## 4.4 Research / Reports

### Research 쪽

1. `research_candidates`를 기존 watchlist/후보 흐름에 연결
2. 최소 표시 항목:
   - `symbol`
   - `status`
   - `priority`
   - `priority_reason`
   - `next_action`

### Reports 쪽

1. `report_highlights`를 narrative entry로 사용
2. 숫자 카드 위주의 화면이라면
   - highlights를 “이번에 다시 볼 포인트” 블록으로 먼저 추가

### compare 기능 준비

1. `compare_data.manager_pairs`
2. `compare_data.holding_overlap`
3. `compare_data.conflicting_recommendations`

지금 당장 완전한 compare UI를 만들 필요는 없고,
우선은:

- pair list
- shared symbol list
- conflict summary

정도만 노출해도 충분합니다.

---

## 5. 프론트 구현 시 주의사항

1. **프론트에서 의미 계산을 다시 하지 말 것**
   - severity, next_action, goto_screen, source_manager_id 등은 backend가 이미 줌

2. **기존 fixture 하드코딩을 줄일 것**
   - quick prompts, discovery card, event summary 등을 점차 snapshot 기반으로 이동

3. **UI 우선순위는 “정보량”보다 “다음 행동 연결”**
   - 새 필드를 한 번에 다 보여주기보다
   - 사용자가 어디로 이동해야 하는지 명확하게 만드는 쪽이 중요

4. **stale 표시를 숨기지 말 것**
   - source_details.stale, manager summary stale 등은 운영 UX에서 중요

---

## 6. 추천 작업 순서

### Step 1
- Home에서 `priority_actions`, `cross_manager_alerts`, `event_timeline` 확장 필드 연결

### Step 2
- OrchestratorPanel에서
  - `short_answer`
  - `next_action`
  - `go_to_screen`
  - `source_details`
  - `orchestrator_prompt_starters`
  연결

### Step 3
- 각 manager 페이지에 `manager_events`와 manager별 priority action 연결

### Step 4
- Research/Reports에 `research_candidates`, `report_highlights`, `compare_data` 점진 연결

---

## 7. 프론트 완료 기준

프론트 1차 완료는 아래를 만족하면 됩니다.

- Home에서 “지금 할 일”이 보인다
- Home에서 manager 이동이 더 직접적이다
- Orchestrator 답변에서 다음 행동과 이동 화면이 보인다
- manager 페이지에서 최근 이벤트/경고를 읽을 수 있다
- Research/Reports가 신규 backend 블록을 최소 1개 이상 소비한다

---

## 8. 한 줄 요약

프론트의 다음 작업은 “디자인 리뉴얼”이 아니라,  
**이번에 추가된 backend discovery/action/context 계약을 Home, Orchestrator, Manager 화면에 연결해서 사용자의 다음 행동을 더 직접적으로 안내하는 것**입니다.
