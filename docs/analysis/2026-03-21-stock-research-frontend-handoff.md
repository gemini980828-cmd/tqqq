# Alpha Wealth Desk — Stock Research 프론트엔드 구현 지시서

작성일: 2026-03-21  
대상: 프론트엔드 / 웹 디자이너 / UI 구현 담당  
목적: Stock Research 데모를 실제 React 구현으로 옮기기 전에, 현재 backend가 이미 제공 가능한 계약과 프론트에서 해야 할 연결 작업을 명확히 정리

---

# 1. 이 문서의 목적

이 문서는 Stock Research를 이제 실제 구현 단계로 옮기기 위한 전달서입니다.

이번 전달서의 핵심은:

1. backend가 이미 어떤 데이터를 줄 수 있는지 정리하고
2. 프론트가 지금 fixture 중심 구현에서 어디까지 snapshot 중심으로 전환할 수 있는지 정리하고
3. 데모(`demo_stock_research.html`)의 구조를 실제 React 컴포넌트로 옮길 때 무엇을 우선 구현해야 하는지 정리하는 것

입니다.

즉, 이 문서는 “어떻게 더 예쁘게 만들까”보다
**“어떤 데이터를 어떤 흐름으로 연결해서 실제 workbench를 만들까”**
에 초점을 둡니다.

---

# 2. 이번 backend에서 이미 준비된 것

Stock Research 쪽에서 프론트가 지금 바로 쓸 수 있는 backend 필드는 아래와 같습니다.

## 2.1 기존 공통 데이터

- `manager_cards.stock_research`
- `manager_summaries.stock_research`
- `manager_events.stock_research`
- `priority_actions`
- `cross_manager_alerts`
- `research_candidates`
- `compare_data`

---

## 2.2 새로 준비된 전용 seed

### `stock_research_workspace`

현재 backend가 제공하는 구조:

```json
{
  "generated_at": "...",
  "filters": {
    "total_count": 0,
    "held_count": 0,
    "candidate_count": 0,
    "observe_count": 0,
    "status_counts": {
      "전체": 0,
      "탐색": 0,
      "관찰": 0,
      "후보": 0,
      "보류": 0,
      "제외": 0
    }
  },
  "queue": [
    {
      "id": "...",
      "symbol": "...",
      "title": "...",
      "reason": "...",
      "severity": "...",
      "status": "...",
      "is_held": false,
      "next_action": "..."
    }
  ],
  "items": [
    {
      "idea_id": "...",
      "symbol": "...",
      "company_name": "...",
      "status": "...",
      "memo": "...",
      "is_held": false,
      "overlap_level": "low|high",
      "priority": "high|medium|low",
      "priority_reason": "...",
      "next_action": "...",
      "generated_at": "..."
    }
  ],
  "compare_seed": {
    "primary_symbol": "...",
    "candidate_symbols": ["...", "..."]
  }
}
```

이건 완전한 상세 데이터가 아니라,
**Stock Research workbench의 초기 상태를 프론트가 실제 snapshot 기반으로 조립할 수 있게 해주는 seed 계약**입니다.

---

# 3. 중요한 판단

## 지금 backend가 할 수 있는 것

현재 backend는 아래까지는 충분히 할 수 있습니다.

- 큐(오늘의 우선순위)
- 리스트 seed
- 상태 분류
- 보유 여부
- overlap level
- priority reason
- next action
- compare 시작점

즉, **watchlist / queue / top-level 탐색 흐름은 backend 기반으로 충분히 옮길 수 있습니다.**

---

## 아직 backend만으로는 부족한 것

현재 backend는 아직 아래까지는 못 줍니다.

- 실제 차트 series
- 실제 뉴스 목록
- 실제 기관투자 / 수급 레이어
- 상세 valuation / macro / options 모델

즉,
**상세 패널의 풍부한 내용은 당분간 fixture 또는 hybrid 방식이 필요합니다.**

이 점은 중요합니다.

이번 프론트 구현은

> **왼쪽 Screener / Queue / 상태 흐름은 backend 기반으로 옮기고,  
> 오른쪽 상세 패널은 기존 fixture/hybrid를 유지하면서 점진적으로 backend와 섞는 전략**

이 가장 현실적입니다.

---

# 4. 이번 프론트 구현의 최종 목표

Stock Research를 아래처럼 만들고자 합니다.

## 목표 문장

> `StockResearchManager`를  
> “fixture 기반 후보 종목 상세 화면”에서  
> “backend snapshot을 기반으로 리스트/큐/상태 흐름을 실제 운영하고, fixture는 상세 판단 영역에서만 보조적으로 쓰는 hybrid workbench”  
> 로 전환한다.

---

# 5. 프론트에서 반드시 구현해야 할 흐름

## 5.1 상단 우선순위 큐

사용 데이터:
- `stock_research_workspace.queue`

역할:
- 오늘 가장 먼저 볼 종목/판단 대상을 알려주는 큐

필수 표시:
- `title`
- `reason`
- `severity`
- `status`
- `next_action`

UX 목표:
- 사용자가 Stock Research에 들어오면 제일 먼저
  **“오늘 어떤 종목을 우선 검토해야 하는지”**
  를 알 수 있어야 함

중요:
- 이 영역은 단순 카드 예쁘게 보여주는 게 아니라
  **선택 시 watchlist/detail과 실제로 연결되는 시작점**
  이어야 함

예:
- 큐 카드 클릭 시 해당 symbol 선택

---

## 5.2 왼쪽 Screener-like 리스트

사용 데이터:
- `stock_research_workspace.items`
- `stock_research_workspace.filters`

역할:
- 실제 탐색 도구

필수 기능:
- 검색
- 상태 필터
- 보유 여부 필터
- 점수/priority/overlap 수준 표시
- next action preview

권장 규칙:
- `items`는 backend seed를 기본으로 쓰고
- 기존 fixture에서 richer 필드가 있으면 merge해서 보강 가능

즉:
- 리스트의 구조/순서/필터는 backend 중심
- 상세 richness는 fixture 보조

---

## 5.3 선택 → 상세 패널 흐름

현재처럼:
- 리스트에서 종목 선택
- 오른쪽 상세 열기

흐름은 유지하되,
이제 selected item의 기본 정보는
가능한 한 backend seed 기준으로 맞추는 것이 좋습니다.

즉:
- symbol
- status
- is_held
- next_action
- memo
- priority_reason

같은 핵심은 backend를 먼저 신뢰

그리고 아래는 fixture/hybrid 유지:
- chart
- macro
- options
- captures
- richer overlap detail

---

## 5.4 상태 전이 UX

현재 status 변경 기능은 있으므로 유지합니다.

다만 이 상태는 단순 드롭다운이 아니라
**탐색 파이프라인의 일부**처럼 보여야 합니다.

즉:
- 탐색
- 관찰
- 후보
- 보류
- 제외

가 단순 label이 아니라
작업 흐름처럼 느껴져야 합니다.

가능하면:
- header / queue / selected row에서 현재 상태를 더 강조
- 상태 전이 후 next action도 같이 보이게

---

## 5.5 compare seed 연결

사용 데이터:
- `stock_research_workspace.compare_seed.primary_symbol`
- `stock_research_workspace.compare_seed.candidate_symbols`

역할:
- compare slot의 초기값 제공

이번 단계에서 꼭 완전 구현할 필요는 없습니다.

하지만 최소한:
- compare slot이 진짜 “빈 박스”가 아니라
- backend가 주는 후보 symbol 기반으로 시작되게

연결하는 것이 좋습니다.

즉:
- 현재 선택 종목
- 비교 후보 추천 목록

까지는 붙여주세요.

---

# 6. 구현 전략 — fixture에서 snapshot으로 옮기는 방법

## 권장 방식: Hybrid Migration

### backend 기반으로 옮길 것
- queue
- list item seed
- filters/status counts
- compare seed
- generated_at / freshness

### fixture 유지할 것
- chart data
- chart markers
- macro_summary
- options_summary
- richer overlap_details
- captures

즉,

```text
backend = workbench skeleton
fixture = detail richness
```

구조로 가는 것이 가장 안정적입니다.

---

# 7. 현재 컴포넌트별 작업 지시

## 7.1 `StockResearchManager.tsx`

역할:
- 전체 state orchestration

해야 할 일:
- `stock_research_workspace`를 읽어오기
- queue / filters / items / compare_seed를 page 레벨에서 관리
- queue 클릭 → selected item 연결
- list 필터 상태와 backend filter counts 연결

현재 구현에서 보완할 점:
- 아직 fixture 중심 사고가 강함
- 이를 workspace seed 중심으로 점진 전환해야 함

---

## 7.2 `StockResearchHeader.tsx`

역할:
- top summary + top pick + next action

해야 할 일:
- `managerCard`, `managerSummary`는 유지
- 가능하면 `queue[0]`와 `compare_seed.primary_symbol`도 활용
- top pick이 단순 fixture 결과가 아니라
  backend queue와 더 자연스럽게 연결되도록 조정

즉:
- “지금 가장 우선인 종목”과
- “상위 후보”가 서로 따로 놀지 않게

---

## 7.3 `StockResearchWatchlist.tsx`

역할:
- Screener 역할

해야 할 일:
- 현재 필터 UI 유지/강화
- backend `filters.status_counts`를 활용해 필터 칩/수치 강화
- `items`에 대해
  - status
  - is_held
  - overlap_level
  - priority_reason
  - next_action
를 더 직접적으로 보여주기

즉:
- 단순 row 나열이 아니라
  **판단 힌트가 응축된 row**
로 만들어야 함

---

## 7.4 `StockResearchDetail.tsx`

역할:
- 선택 종목 판단 콘솔

해야 할 일:
- 현재 상세 구조는 유지 가능
- 다만 selected item의 핵심 상태는 backend seed 기준으로 동기화

예:
- status
- memo
- next_action
- is_held

는 snapshot seed 우선

그리고 chart/macro/options 등은 fixture 보조

---

## 7.5 신규 권장 컴포넌트

현재 데모 구조를 실제로 옮기려면 아래 분리가 유리합니다.

- `StockResearchQueue.tsx`
- `StockResearchFilters.tsx`
- `StockResearchListItem.tsx`
- `StockResearchCompareSeed.tsx`

지금 한 파일에 다 몰아넣기보다,
기능별로 끊는 것이 좋습니다.

---

# 8. 하지 말아야 할 것

1. **상세 패널까지 모두 backend-only로 억지 전환하지 말 것**
   - 아직 차트/뉴스/기관 정보는 backend가 못 줌

2. **fixture를 완전히 버리지 말 것**
   - 지금은 hybrid가 맞음

3. **queue / list / detail이 서로 따로 놀게 두지 말 것**
   - 우선순위 큐와 선택 흐름은 연결되어야 함

4. **filter를 UI만 만들고 실제 데이터와 안 연결하지 말 것**
   - counts / items / status가 실제로 반응해야 함

5. **compare slot을 빈 디자인 요소로만 두지 말 것**
   - 최소한 compare seed는 연결해야 함

---

# 9. 권장 구현 순서

## Step 1
- `AppSnapshot`에서 `stock_research_workspace` 타입 추가

## Step 2
- `StockResearchManager.tsx`에서 workspace seed 읽기

## Step 3
- queue UI를 backend data 기반으로 연결

## Step 4
- watchlist row를 backend seed 중심으로 재구성

## Step 5
- compare seed 연결

## Step 6
- detail panel과 backend seed 핵심 필드 동기화

---

# 10. 검증 체크리스트

## 기능 검증
- [ ] queue 카드 클릭 시 해당 종목이 선택됨
- [ ] 검색 필터가 실제 item 목록에 반영됨
- [ ] 상태 필터가 실제 item 목록에 반영됨
- [ ] 보유 필터가 실제 item 목록에 반영됨
- [ ] compare seed가 화면에 반영됨
- [ ] selected item 상태/메모/next action이 일관되게 유지됨

## 계약 검증
- [ ] `stock_research_workspace.items`를 실제 소비함
- [ ] `stock_research_workspace.filters`를 실제 소비함
- [ ] `stock_research_workspace.queue`를 실제 소비함
- [ ] `stock_research_workspace.compare_seed`를 실제 소비함

## 기술 검증
- [ ] `npm run build`
- [ ] `npm run lint`
- [ ] 기존 `stockResearchWorkspace.test.js`와 충돌 없음

---

# 11. 완료 정의

이번 프론트 작업은 아래를 만족하면 완료입니다.

1. Stock Research가 fixture-only 화면이 아니라 backend seed를 실제로 소비한다
2. queue / list / detail이 하나의 workbench 흐름으로 연결된다
3. 리스트가 실제 screener-like 탐색 도구로 동작한다
4. compare slot이 빈 구조가 아니라 backend seed와 연결된다
5. detail panel은 여전히 풍부하지만, 핵심 상태 정보는 backend와 정합성을 가진다

---

# 12. 한 줄 지시

이번 작업의 본질은  
**Stock Research를 “fixture 기반 화면”에서 “backend snapshot seed를 실제로 소비하는 hybrid workbench”로 전환하는 것**입니다.
