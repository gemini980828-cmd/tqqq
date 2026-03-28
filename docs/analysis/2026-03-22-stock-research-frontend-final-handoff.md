# Alpha Wealth Desk — Stock Research 최종 프론트 구현 지시서

작성일: 2026-03-22  
대상: 프론트엔드 구현 담당  
목적: 현재까지 준비된 Stock Research backend 계약을 기준으로, 프론트에서 실제 `StockResearchManager` workbench를 구현/정리하기 위한 최종 handoff 문서

---

# 1. 이 문서의 목적

이 문서는 지금까지의 논의, 데모 검토, backend 고도화를 반영한
**최종 프론트 구현 지시서**입니다.

이 문서의 목표는:

1. Stock Research 화면이 원래 기획했던 위치(`Managers > Stocks`)에서
2. backend가 준비한 `stock_research_workspace`를 실제로 소비하고
3. screener + detail + compare + evidence 흐름을 가진
4. **실제 workbench**처럼 동작하도록 구현하는 것

입니다.

즉, 이 문서는 단순한 디자인 요청이 아니라
**어떤 데이터를 어떤 순서로 어떻게 연결해서 실제 작업 화면을 만들지**에 대한 구현 지침입니다.

---

# 2. 현재 전제

## 2.1 위치

Stock Research는 이제 다시 원래 의도대로:

- `#/managers/stocks`

에 위치해야 합니다.

즉:
- `Research` 탭 메인 화면이 아니라
- `Managers` 아래의 하나의 workbench입니다.

---

## 2.2 backend 선행 상태

현재 backend는 Stock Research용으로 아래 seed를 제공합니다.

### `snapshot.stock_research_workspace`

구성:
- `generated_at`
- `filters`
- `queue`
- `items`
- `flow`
- `evidence`
  - `chart`
  - `news`
  - `institutional_flow`
- `compare_seed`

즉, 프론트는 더 이상 전부를 fixture로만 만들 필요가 없습니다.

다만 여전히 상세 richness 일부는 hybrid가 필요합니다.

---

# 3. 이번 구현의 핵심 방향

## 핵심 원칙

> **backend는 workbench의 skeleton을 제공하고,  
> 프론트는 그 skeleton 위에 실제 탐색/선택/판단 흐름을 구현한다.**

즉:

- 리스트/큐/상태 흐름/비교 시작점은 backend 중심
- 차트/뉴스/기관 브리프의 상세 richness는 hybrid 가능
- 하지만 최소한 화면의 구조와 흐름은 backend contract를 기준으로 맞춰야 함

---

# 4. 프론트에서 반드시 소비해야 하는 backend 데이터

## 4.1 Queue

사용 위치:
- 상단 우선순위 큐

필드:
- `stock_research_workspace.queue[]`
  - `id`
  - `symbol`
  - `title`
  - `reason`
  - `severity`
  - `status`
  - `is_held`
  - `score`
  - `age_label`
  - `next_action`

필수 동작:
- queue item 클릭 시 해당 symbol이 선택되어야 함
- 선택 시 watchlist와 detail이 함께 반응해야 함

---

## 4.2 Filters

사용 위치:
- 왼쪽 Screener 상단

필드:
- `stock_research_workspace.filters`
  - `total_count`
  - `held_count`
  - `candidate_count`
  - `observe_count`
  - `status_counts`

필수 동작:
- 필터 칩 수치가 backend 기준으로 보임
- 필터는 실제 리스트 결과와 연결되어야 함

즉:
- UI만 있는 필터 금지

---

## 4.3 Items

사용 위치:
- 왼쪽 리스트 본문
- 오른쪽 detail 핵심 seed

필드:
- `idea_id`
- `symbol`
- `company_name`
- `status`
- `memo`
- `is_held`
- `overlap_level`
- `priority`
- `priority_reason`
- `next_action`
- `generated_at`
- `score`
- `risk_level`
- `recent_status_change`

이제 row는 최소한 이 데이터들을 직접 읽어야 합니다.

---

## 4.4 Flow

사용 위치:
- 상태 전이 흐름 시각화
- header / summary / badge 표현

필드:
- `stock_research_workspace.flow.pipeline`
- `stock_research_workspace.flow.active_stage`
- `stock_research_workspace.flow.stage_counts`

활용 목적:
- 현재 상태가 단순 label이 아니라
  **탐색 파이프라인의 일부**처럼 느껴지게 만들기

---

## 4.5 Evidence

사용 위치:
- detail 패널 하단 또는 우측 보조 영역

필드:
- `stock_research_workspace.evidence.chart`
- `stock_research_workspace.evidence.news`
- `stock_research_workspace.evidence.institutional_flow`

설명:
- 이건 full raw data가 아니라 seed입니다.
- 프론트는 이걸 바탕으로
  - evidence panel
  - news list
  - institutional brief
  를 구성하면 됩니다.

---

## 4.6 Compare Seed

사용 위치:
- compare slot
- compare viewer 시작점

필드:
- `stock_research_workspace.compare_seed.primary_symbol`
- `stock_research_workspace.compare_seed.candidate_symbols`
- `stock_research_workspace.compare_seed.default_mode`

현재 단계 목표:
- compare UI를 실제로 시작할 수 있는 seed 연결

즉:
- 그냥 “비교 대상 추가하기 +” 빈 박스가 아니라
- 어떤 비교를 시작하면 되는지 seed가 보여야 함

---

# 5. 현재 프론트 구현 시 반드시 지켜야 하는 구조

## 최종 화면 구조

```tsx
<StockResearchManager>
  <ManagerActionHeader />
  <StockResearchHeader />
  <StockResearchQueue />
  <div className="workspace">
    <StockResearchWatchlist />
    <StockResearchDetail />
  </div>
</StockResearchManager>
```

그리고 `StockResearchDetail` 안에서:

```tsx
<StockResearchDetail>
  <JudgmentBlock />
  <SignalsMetrics />
  <FitAnalysis />
  <StockResearchEvidencePanel />
  <StockResearchComparePanel />
  <NextActionConsole />
  <MemoPanel />
</StockResearchDetail>
```

즉, 현재 데모 구조를 React에 옮기되,
이제 실제 데이터 source는 backend seed 중심으로 전환합니다.

---

# 6. 컴포넌트별 구현 지시

## 6.1 `StockResearchManager.tsx`

역할:
- 전체 orchestration

해야 할 일:
- `snapshot.stock_research_workspace`를 기본 source로 읽기
- queue 선택, list 필터, selected item, compare seed를 page state에서 관리
- detail에 들어갈 hybrid data merge 전략 유지

핵심 규칙:
- selected symbol은 queue / list / detail 모두에서 동일 source를 사용
- 선택 종목이 필터에서 사라지면 fallback selection 필요

---

## 6.2 `StockResearchQueue.tsx`

역할:
- 오늘의 우선순위 큐

해야 할 일:
- `queue`를 그대로 읽기
- severity별 강조
- score, age_label, next_action 표시
- 클릭 시 symbol 선택

절대 하지 말 것:
- queue 텍스트를 프론트에서 재구성하지 말 것

---

## 6.3 `StockResearchWatchlist.tsx`

역할:
- Screener

해야 할 일:
- `items` + `filters` 기반으로 리스트 렌더링
- query / status / holding / advanced filter chips를 실제로 적용
- sorting도 실제로 동작시킬 것

반드시 반영할 항목:
- 상태 badge
- 보유 여부
- score
- risk_level
- overlap_level
- recent_status_change
- next_action preview

즉, row는 단순 종목명 카드가 아니라
**1차 판단이 가능한 정보 밀도**를 가져야 함

---

## 6.4 `StockResearchHeader.tsx`

역할:
- 상단 summary / top pick / next action 요약

해야 할 일:
- `managerCard`, `managerSummary`, `flow`, `queue[0]`
를 조합해 더 일관된 상단 요약 제공

중요:
- top pick이 queue와 너무 따로 놀지 않게 조정

즉:
- “상단에서 말하는 우선 후보”
- “실제 queue 1번”
- “리스트 1순위”

가 최대한 비슷한 맥락이 되도록

---

## 6.5 `StockResearchEvidencePanel.tsx`

역할:
- 차트 / 기관 브리프 / 뉴스

해야 할 일:
- `evidence.chart`
- `evidence.institutional_flow`
- `evidence.news`
를 표시

주의:
- 지금 단계에서는 seed 기반이므로
  “완전한 분석 툴”처럼 보이게 하기보다
  **판단 보조 레이어**
  로 유지할 것

원칙:
- 차트 = 큰 보조 패널
- 기관 브리프 = 작고 강한 요약 카드
- 뉴스 = 2~3개 핵심 이벤트 요약

---

## 6.6 `StockResearchComparePanel.tsx`

역할:
- compare workflow 시작점

해야 할 일:
- `compare_seed.primary_symbol`
- `compare_seed.candidate_symbols`
- `compare_seed.default_mode`
표시

이번 단계 목표:
- 실제 compare engine 완성 아님
- 최소한 “비교 시작 가능”한 상태

즉:
- 현재 선택 종목
- 추천 비교 종목
- fit / overlap / action 비교 모드 seed
를 보여줘야 함

---

## 6.7 `StockResearchDetail.tsx`

역할:
- 판단 콘솔

해야 할 일:
- selected item의 핵심 상태는 backend seed 우선 사용
- richer explanation은 fixture/hybrid 보조

최소한 backend 우선이어야 하는 것:
- symbol
- status
- is_held
- next_action
- memo
- score
- risk_level

fixture/hybrid 가능:
- chart details
- macro summary
- options summary
- richer overlap explanation
- captures

---

# 7. 지금 단계에서 프론트가 하지 말아야 할 것

1. **backend seed를 무시하고 전부 fixture만 쓰지 말 것**
2. **queue/list/detail 선택 흐름이 서로 따로 놀게 두지 말 것**
3. **compare slot을 다시 빈 placeholder로 두지 말 것**
4. **evidence/news/기관 브리프를 너무 큰 주연 블록으로 만들지 말 것**
5. **새로운 판단 로직을 프론트에서 임의 계산하지 말 것**
   - 점수/우선순위 로직은 나중에 engine에서 할 일

---

# 8. 권장 구현 순서

## Step 1
- `app/web/src/types/appSnapshot.ts`에 `stock_research_workspace` 타입을 완전히 반영

## Step 2
- `StockResearchManager.tsx`에서 queue/list/detail selection state 정리

## Step 3
- `StockResearchQueue.tsx` backend queue 기반 연결

## Step 4
- `StockResearchWatchlist.tsx` backend items 기반 row density 연결

## Step 5
- `StockResearchEvidencePanel.tsx` backend evidence seed 연결

## Step 6
- `StockResearchComparePanel.tsx` compare seed 연결

## Step 7
- header / detail과 queue/list 흐름 정리

---

# 9. 검증 체크리스트

## 기능
- [ ] queue 클릭 시 detail 종목이 바뀐다
- [ ] 리스트 클릭 시 detail 종목이 바뀐다
- [ ] 검색이 실제 items를 필터링한다
- [ ] status filter가 실제 items를 필터링한다
- [ ] holding filter가 실제 items를 필터링한다
- [ ] compare seed가 화면에 표시된다
- [ ] evidence panel이 chart/news/institutional seed를 표시한다

## 구조
- [ ] Stock Research는 `#/managers/stocks` 아래에 있다
- [ ] Research 탭과 혼동되지 않는다
- [ ] queue / list / detail / compare 흐름이 workbench처럼 이어진다

## 기술
- [ ] `npm run build`
- [ ] `npm run lint`
- [ ] `node --test app/web/src/lib/stockResearchWorkspace.test.js`

---

# 10. 완료 정의

이번 프론트 구현은 아래를 만족하면 완료입니다.

1. Stock Research가 fixture-only 화면이 아니다
2. backend seed가 실제 queue/list/evidence/compare에 연결된다
3. 리스트는 실제 screener처럼 동작한다
4. detail은 판단 콘솔처럼 동작한다
5. compare는 실제 시작 가능한 구조를 가진다
6. 화면 전체가 “종목 설명 페이지”보다 “리서치 작업대”처럼 느껴진다

---

# 11. 한 줄 지시

이번 작업의 본질은  
**Stock Research를 더 예쁘게 꾸미는 것이 아니라, backend가 준비한 `stock_research_workspace`를 실제로 소비해서 Screener + Detail + Compare + Evidence가 이어지는 workbench로 완성하는 것**입니다.
