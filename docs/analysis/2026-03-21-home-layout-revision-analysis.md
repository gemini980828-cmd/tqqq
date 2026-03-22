# Alpha Wealth Desk Home 레이아웃 개편 분석

작성일: 2026-03-21
기준 자료:
- `demo_dashboard.html`
- `app/web/src/pages/Home.tsx`
- `app/web/src/components/OrchestratorPanel.tsx`
- `app/web/src/components/ManagerCard.tsx`
- 기존 프론트 구현 보고서 및 백엔드 snapshot 계약

---

## 1. 결론 요약

데모의 핵심은 "새로운 위젯 추가"가 아니라 **정보 우선순위와 화면 골격을 바꾸는 것**입니다.

현재 Home은 다음 순서입니다.
1. hero
2. KPI metrics
3. manager hub + orchestrator
4. recent activity + alerts + action center
5. research/report discovery

반면 데모는 다음 순서입니다.
1. 간단한 인사/상태 헤더
2. Priority Actions
3. Cross-Manager Alerts
4. Manager Workbench
5. 우측 고정 Orchestrator

즉, 현재 구현은 "섹션 나열형 대시보드"이고,
데모는 "좌측 운영 허브 + 우측 실행 콘솔"입니다.

따라서 이번 개편의 핵심은:
- **컴포넌트를 새로 많이 만드는 것보다**
- **Home의 레이아웃 축을 바꾸는 것**
- **Action / Alert / Manager 진입 흐름을 앞으로 당기는 것**
- **Orchestrator를 보조 섹션이 아니라 항상 열려 있는 콘솔로 승격하는 것**
입니다.

---

## 2. 데모 상세 분석

## 2.1 상단 헤더

데모 헤더 특징:
- 높이가 낮고 밀도 높음
- 브랜드, 전역 네비, 알림 아이콘만 존재
- 콘텐츠의 시작점은 헤더 아래의 "Good Morning / attention" 문장

의미:
- Home hero가 "소개 문구"보다 "운영 시작 문장" 역할을 함
- 상단에서 설명을 길게 하지 않음

현재 대비 차이:
- 현재 Home hero는 문장이 길고 product intro 성격이 강함
- 데모는 intro를 줄이고 **오늘의 운영 시작점**으로 압축함

시사점:
- hero는 유지 가능하지만 더 얇고 짧아져야 함
- "오늘 무엇을 봐야 하는가"를 강조해야 함

---

## 2.2 Priority Actions

데모에서 가장 중요한 영역입니다.

특징:
- 화면 최상단 첫 섹션
- 카드 하나가 곧 하나의 운영 명령처럼 보임
- 각 카드 안에 다음 정보가 응축됨:
  - severity
  - source manager
  - title
  - reason/summary
  - CTA 버튼

이 영역의 역할:
- 사용자가 대시보드에 들어왔을 때 가장 먼저 "지금 처리할 것"을 보게 함
- 분석보다 실행을 먼저 열어 줌

현재 대비 차이:
- 현재 Home에서도 Action Center가 있지만 아래쪽에 있음
- 따라서 시선의 1차 도착지가 아님

시사점:
- `priority_actions`는 Home의 가장 첫 실무 블록으로 올려야 함
- CTA는 실제 이동 가능한 버튼이어야 함
- 카드 전체가 클릭 가능한 것이 더 자연스러움

---

## 2.3 Cross-Manager Alerts

특징:
- priority 아래에 바로 배치
- 단일 manager 상태가 아니라 manager 간 충돌/상관/공동검토 이슈를 강조
- 작지만 매우 의미 밀도 높은 섹션

의미:
- 데모는 대시보드를 단일 상태판이 아니라
  **manager coordination surface**로 사용함

현재 대비 차이:
- 현재 Home에도 `cross_manager_alerts` 섹션은 있으나
- action flow 속에서 핵심 위치를 차지하지 못함

시사점:
- 이 영역은 timeline 옆 보조 블록이 아니라
  priority 바로 다음에 와야 함
- "왜 같이 봐야 하는가"를 한 줄로 명확히 보여주는 것이 중요

---

## 2.4 Manager Workbench Grid

특징:
- manager 카드가 단순 overview card가 아니라 "진입 포털"처럼 보임
- 카드 내부에서 이미 상태가 요약됨
  - action required
  - warning
  - normal monitoring
- 카드 하단에 Enter affordance 존재

의미:
- 사용자는 Home에서 manager를 고르는 것이 아니라
  이미 정렬된 우선순위 속에서 적절한 workspace로 들어감

현재 대비 차이:
- 현재 `ManagerCard`는 방향은 맞지만, 배치가 조금 늦음
- 그리고 priority/actions와 묶인 연속 흐름으로 보이지 않음

시사점:
- manager hub는 Home 중간이 아니라
  Priority -> Cross Alert -> Manager Workbench 순서여야 함
- `ManagerCard`는 유지 가능하되 more portal-like wording 필요

---

## 2.5 Right-side Orchestrator

이 데모의 가장 큰 구조적 특징입니다.

특징:
- 우측 고정 aside
- 단순 채팅박스가 아니라 "운영 분석 콘솔"
- 응답이 구조화됨:
  - short answer
  - detail
  - sources
  - next action
  - go to workspace
- 입력창은 항상 하단에 고정

의미:
- Orchestrator는 페이지의 한 섹션이 아니라 **항상 병행되는 사고/분석 레이어**
- 왼쪽의 action hub와 오른쪽의 analysis console이 서로 보완함

현재 대비 차이:
- 현재는 manager hub 옆 패널이긴 하지만, section처럼 보임
- 데모만큼 고정된 sidebar console 느낌은 아님

시사점:
- OrchestratorPanel은 Home 전용으로 폭이 고정된 aside에 가까워져야 함
- 높이/스크롤 구조도 별도로 잡는 것이 좋음

---

## 2.6 Research / Reports 노출 방식

데모에서는 메인 시야의 최상단에 직접 드러나지 않음
- 즉, discovery는 중요하지만 1차 시선 요소는 아님
- 운영 액션이 먼저이고, research/report는 하위 또는 후속 맥락임

현재 대비 차이:
- 현재 Home 하단에 discovery section이 들어간 것은 방향상 문제 없음
- 다만 데모 감성으로 가려면 정보 위계상 더 아래로 밀어도 됨

시사점:
- `research_candidates`, `report_highlights`는 유지하되
- 메인 허브 핵심축으로 보지 말고 secondary discovery로 위치시켜야 함

---

## 3. 현재 구현에서 유지할 것 / 바꿀 것

## 3.1 유지할 것

1. `priority_actions`, `cross_manager_alerts`, `manager_cards`, `event_timeline`, `orchestrator`라는 정보 구조 자체
2. `ManagerCard` 기반 manager entry 방식
3. `OrchestratorPanel`의 구조화된 응답 방향
4. Home이 action-first hub여야 한다는 기본 철학

즉, **무엇을 보여줄지**는 크게 틀리지 않았음

---

## 3.2 바꿔야 할 것

### A. Home 전체 레이아웃 축
현재:
- 다층 vertical stack

변경:
- `main content (left)` + `orchestrator aside (right)`

### B. 정보 순서
현재:
- hero → metrics → manager/orchestrator → timeline/action

변경:
- compact hero → priority actions → cross-manager alerts → manager workbench → secondary discovery

### C. Orchestrator의 역할
현재:
- 동등 섹션 중 하나

변경:
- 항상 열려 있는 우측 작업 콘솔

### D. timeline 위치
현재:
- 꽤 큰 독립 섹션

변경:
- 메인 허브의 하위 supporting section으로 축소 또는 manager workbench 아래로 이동

### E. metrics의 비중
현재:
- 상단에서 큰 비중

변경:
- 더 compact하게 축소
- action hub보다 앞에 오더라도 시각적 dominance는 줄여야 함

---

## 4. 구체적인 레이아웃 개편안

## 제안안: 2-column Action Hub Layout

### 상단
- global nav 유지
- Home hero는 compact welcome/status bar로 축소
  - headline: 짧게
  - subcopy: 한 줄
  - today action / stance 정도만 유지

### 본문
#### 좌측 `HomeActionHub`
순서:
1. `PriorityActionsSection`
2. `CrossManagerAlertsSection`
3. `ManagerWorkbenchSection`
4. `RecentActivitySection` (축소형)
5. `SecondaryDiscoverySection` (research/report)

#### 우측 `HomeOrchestratorRail`
- `OrchestratorPanel` 고정 폭 aside
- sticky 또는 독립 scroll
- Home에서만 콘솔처럼 보이게 강화

---

## 5. 현재 작업에서 달라져야 하는 점

## 5.1 Home.tsx
현재 작업 방향:
- 새 블록을 기존 섹션 구조 안에 추가하는 방식

변경 필요:
- 새 블록 추가가 아니라 **섹션 재조합**으로 바뀌어야 함
- 특히 아래를 해야 함:
  - manager/orchestrator 2단 section 해체
  - timeline + action center 하단 section 해체
  - 좌측 main hub를 새 순서로 재구성
  - 우측 aside로 orchestrator 분리

즉, Home은 "점진 확장"보다 "배치 재편"이 더 중요함

---

## 5.2 OrchestratorPanel
현재 작업 방향:
- 카드형 응답 구조는 잘 가고 있음

변경 필요:
- Home embedded card가 아니라 **rail component**처럼 동작해야 함
- 필요 시 아래를 추가:
  - fixed/sticky container
  - scrollable history area
  - 하단 input fixed zone
  - source / next action / workspace jump를 더 선명하게 분리

즉, 컴포넌트 내부 로직보다 **container role**이 달라져야 함

---

## 5.3 ManagerCard
현재 작업 방향:
- action req / alerted 상태 강조는 적절함

변경 필요:
- 더 명확한 entry affordance 필요
- 예:
  - "Enter" / "Open workspace"
  - headline 하단에 next action 1줄
  - manager 카드의 정보 밀도를 살짝 줄이고 포털 성격 강화

즉, summary card보다 **workspace entry tile**에 가까워져야 함

---

## 5.4 Action Center
현재 작업 방향:
- 별도 섹션으로 구현되어 있음

변경 필요:
- Home의 핵심 첫 블록으로 승격
- 시각적으로도 가장 강한 블록이어야 함
- CTA는 반드시 이동 가능해야 함

즉, 위치와 인터랙션 우선순위가 달라져야 함

---

## 5.5 Cross-Manager Alerts
현재 작업 방향:
- 좋은 시작

변경 필요:
- timeline 옆 보조 섹션이 아니라 priority 다음의 coordination block으로 승격
- 관련 manager jump를 더 직접적으로 연결

---

## 5.6 Research / Reports discovery
현재 작업 방향:
- Home 하단에 discovery section 추가

변경 필요:
- 유지 가능
- 다만 메인 구조의 주연이 아니라 하위 supporting zone으로 위치 고정

---

## 6. 구현 난이도 평가

### 낮음
- ManagerCard wording/entry affordance 조정
- Action / Alert / Discovery 순서 일부 변경

### 중간
- Home을 좌측 hub / 우측 orchestrator rail로 재배치
- metrics/hero compact화
- timeline 위치 축소

### 높음
- Orchestrator rail을 sticky/fixed console처럼 완성도 높게 만드는 것
- 반응형에서 mobile/tablet/desktop 모두 자연스럽게 정리하는 것

즉, 이번 작업은
**새 기능 추가 난이도보다 레이아웃 재조합 난이도가 더 큰 작업**입니다.

---

## 7. 추천 접근 방식

### Approach A — 최소 침습형
- 기존 컴포넌트 유지
- Home에서 배치만 재구성
- 우측 orchestrator rail 추가
- action/alert를 상단으로 이동

장점:
- 빠름
- 현재 작업과 연결 쉬움

단점:
- 데모의 밀도감/완성도는 다소 약할 수 있음

### Approach B — Home 전용 shell 재구성 (추천)
- `Home.tsx`를 Home shell + section components로 나눔
- 예:
  - `HomeHeroCompact`
  - `HomePriorityActions`
  - `HomeCrossAlerts`
  - `HomeManagerWorkbench`
  - `HomeRecentActivity`
  - `HomeDiscoverySecondary`
  - `HomeOrchestratorRail`

장점:
- 데모 방향과 가장 잘 맞음
- 이후 수정/확장 쉬움

단점:
- 지금보다 파일 구조 손이 조금 더 감

---

## 8. 최종 권고

이번 개편은 “지금 페이지를 완전히 갈아엎자”가 아니라,

> **현재 Home에 이미 있는 action/alert/manager/orchestrator 요소를,
> 데모처럼 운영 우선순위가 보이도록 다시 배치하는 작업**

으로 보는 것이 맞습니다.

따라서 권고는 아래와 같습니다.

1. 전체 철학은 유지한다
2. Home 레이아웃만 중간 규모로 재편한다
3. Orchestrator를 우측 rail로 승격한다
4. Action / Alert / Manager를 좌측 메인 허브의 핵심 흐름으로 재정렬한다
5. Research / Reports discovery는 secondary zone으로 유지한다

---

## 9. 한 줄 요약

데모 느낌으로 가려면 현재 작업의 방향을 버릴 필요는 없지만,
**“새 섹션을 더하는 방식”에서 “운영 허브 구조로 재배치하는 방식”으로 사고방식을 바꿔야 합니다.**
