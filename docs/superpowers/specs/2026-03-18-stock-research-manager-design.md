# Stock Research Manager Design

**Date:** 2026-03-18  
**Scope:** `/app/web/src/pages/managers/StockResearchManager.tsx` 중심의 개별주 탐색 manager surface 설계  
**Session Goal:** scaffold-only 상태인 Stock Research Manager를 실제로 쓸 수 있는 스크리닝 + 분석 작업면으로 끌어올린다.

---

## 1. 배경과 세션 범위

현재 자산관리 시스템은 Home / Managers / Inbox / Reports 구조와 총괄 AI shell이 usable 수준까지 구현되어 있다. 다만 `Stock Research Manager`는 아직 scaffold-only 상태이며, 이번 세션은 이 매니저를 실제로 사용하는 작업면으로 만드는 데만 집중한다.

### 포함 범위

- watchlist 리스트 화면
- 상태 전이: `탐색 / 관찰 / 후보 / 보류 / 제외`
- 종목 상세 패널: 메모 / 캡처 / 다음 액션
- Home / Inbox와 연결될 최소 계약 정의
- 과도한 AI 고도화 없이 usable한 manager surface 구현

### 제외 범위

- 총괄 AI / 코어 대시보드 전체 리디자인
- 다른 manager(부동산 / 현금부채) 고도화
- 실제 파일 업로드형 캡처 저장 기능
- 정교한 실시간 AI scoring engine
- 백엔드의 대규모 데이터 파이프라인 증설

---

## 2. 사용자 의도 정리

사용자가 원하는 Stock Research Manager는 단순 메모장이 아니다. 이 매니저는 아래 역할을 수행해야 한다.

1. **종목 스크리닝**
   - watchlist를 점수순으로 빠르게 훑는다.
2. **깊은 분석**
   - 점수가 높은 종목을 클릭하면 차트 중심의 분석 workspace로 들어간다.
3. **매수/보유/축소 판단 보조**
   - 종합점수와 선정 이유를 통해 지금 어떤 액션이 맞는지 보조한다.
4. **리스크 관리 보조**
   - 종목 자체 리스크뿐 아니라 포트폴리오 중복/집중도도 같이 본다.

### 사용자 확정 요구

- 워치리스트는 **점수 높은 순 단일 리스트**
- 상세 패널 최상단은 **종합점수 + 선정 이유**
- 점수는 **매수 매력도 + 포트폴리오 적합도(중복/현금/집중도)** 기반
- 보유 종목은 발굴 흐름에 섞되 **보유중 배지 + 리스크 상태**만 함께 노출하고, 상세 패널에서만 현재 판단을 크게 보여준다
- 차트/종합판단은 크게, 매크로/옵션은 요약 카드 수준으로 시작
- 캡처는 이번 세션에서 **더미 이미지/썸네일 기반 데모 수준**
- Home / Inbox 계약은 **상위 후보 1~3개 + 다음 액션 1개 + 경고 1개** 수준

---

## 3. 벤치마크 관찰과 설계 반영

공식 제품/도움말 위주의 벤치마킹에서 공통적으로 드러난 패턴은 다음과 같다.

### 공통 패턴

- **TradingView:** 차트 중심 + watchlist 연동 + 매크로는 보조 위젯
- **thinkorswim:** scanner 결과를 watchlist처럼 운용, 섹터/시장 breadth는 별도 시각 레이어
- **TrendSpider:** Smart watchlist + chart 중심 deep analysis, 옵션은 sidebar widget
- **Finviz:** sector/theme/breadth 컨텍스트는 개별 종목보다 상단/별도 뷰에 강함

### 설계 반영 원칙

1. **차트가 메인 분석 영역의 중심**
2. **watchlist는 빠른 심볼 전환 허브**
3. **매크로 / 옵션은 보조 위젯 수준**
4. **섹터 겹침 / 테마 중복 / 포트 집중도는 별도 설명 레이어로 분리**
5. **스캐너 결과는 state workflow와 자연스럽게 연결**

이 벤치마킹 덕분에 초기 C안(analysis workspace형)을 유지하되, 차트 중심성을 강화하고 섹터 겹침을 점수 밖으로도 설명하는 방향으로 확정했다.

---

## 4. 화면 구조

Stock Research Manager는 **차트 중심 C안 workspace**를 채택한다. 다만 과설계를 피하기 위해 각 영역의 깊이는 구분한다.

### 4.1 상단: Screening Header

상단에는 manager 전체 상황을 짧게 요약하는 strip를 둔다.

- 상위 후보 1개 강조 카드
- 상태 분포: `탐색 / 관찰 / 후보 / 보류 / 제외`
- 오늘의 다음 액션 1개
- Home / Inbox contract preview 수준의 요약

### 4.2 좌측: Watchlist Rail

좌측은 빠른 스캔용 리스트다. 기본 정렬은 **Buy Priority Score 내림차순**이다.

각 row는 다음 정보를 포함한다.

- 종목명 / 티커
- 종합점수
- 상태
- 보유중 배지
- 선정 이유 1줄
- 리스크 또는 집중도 플래그
- 점수 드라이버 태그
  - 예: `현금 적합`, `반도체 중복`, `성장 모멘텀`

### 4.3 우측: Analysis Workspace

우측은 선택 종목을 깊게 파는 분석 작업면이다.

#### 상단

- 종합점수
- 현재 판단: `매수 후보 / 추가매수 후보 / 보유 유지 / 축소 검토 / 제외`
- 선정 이유 한 줄
- 점수 분해
  - 종목 매력도
  - 포트 적합도
  - 집중도 페널티

#### 중앙 메인

- **가장 큰 블록은 차트**
- 가격 차트
- 이동평균 / 주요 가격대
- 이벤트 마킹
- 기술적 포인트 2~3개

#### 우측 보조 카드

- 매크로 상황 요약
- 옵션시장 요약
- 메모/액션 요약

#### 하단 작업 카드

- 섹터/테마 겹침 상세
- 캡처 썸네일 strip
- 다음 액션

---

## 5. 점수 모델

메인 정렬 기준은 단일 점수인 **Buy Priority Score**다. 다만 점수 자체를 과하게 복잡하게 드러내지 않고, 설명 태그와 분해 점수로 이해 가능하게 만든다.

### 5.1 점수의 내부 구조

#### A. 종목 매력도

- 추세 / 차트 구조
- 성장성 / 사업 내러티브
- 이벤트 모멘텀
- 기술적 위치

#### B. 포트폴리오 적합도

- 현금 여력
- 현재 보유 비중과 충돌 여부
- 리스크 한도 초과 가능성

#### C. 중복 / 집중도 조정

- 섹터 겹침
- 테마 겹침
- 기존 보유 종목과의 유사 노출

### 5.2 UI 표현 원칙

리스트에는 아래만 보여준다.

- 종합점수 `0~100`
- 짧은 드라이버 태그
  - 예: `추세 우호`
  - 예: `현금 여력 보통`
  - 예: `AI 테마 중복`

상세 패널에서만 분해 점수를 보여준다.

### 5.3 섹터 겹침 처리

섹터/테마 겹침은 점수 안에 묻어두지 않는다. 아래처럼 **독립 배지/경고**로 노출한다.

- `섹터 중복 높음`
- `AI 테마 노출 과다`
- `대형 기술주 편중`
- `기보유 종목과 유사 노출`

이 정보는 watchlist row와 상세 패널 모두에 반영한다.

---

## 6. 상태 모델

상태는 점수와 별개로 운영 단계용이다.

- **탐색:** 스크리닝에 막 들어온 종목
- **관찰:** 계속 볼 가치가 있으나 아직 확신 전
- **후보:** 실제 매수 검토 우선군
- **보류:** 아이디어는 좋지만 타이밍/포트 상황상 대기
- **제외:** 현재 논리상 당분간 제외

### 상태 모델 원칙

- 정렬은 **점수 기준**
- 상태는 **운영 단계 표시**
- 상세 패널에서 상태 전이 액션 제공
  - 예: `관찰 → 후보`
  - 예: `후보 → 보류`
  - 예: `보류 → 제외`

### legacy 상태 정규화 규칙

기존 수동 데이터 및 테스트와 divergence를 막기 위해 legacy 상태값은 아래처럼 정규화한다.

- `매수후보` → `후보`
- `검토` → `후보`
- `관찰` → `관찰`
- `후보` → `후보`
- `보류` → `보류`
- `제외` → `제외`
- 그 외 / 빈값 → `탐색`

이 정규화는 **stock_research 관련 backend summary/inbox builder와 frontend adapter가 공유해야 하는 계약 규칙**이다. 즉, Home / Managers / Inbox용 stock_research 요약을 만들 때도 같은 정규화를 적용해야 한다.

구체적인 backend touchpoint:

- `src/tqqq_strategy/ai/manager_jobs.py`
- `src/tqqq_strategy/ai/inbox_builder.py`
- 관련 contract tests (`tests/ai/*`, `tests/wealth/*`)

---

## 7. 보유 종목 처리

Stock Research Manager는 후보 발굴 중심이지만, 보유 종목도 같은 화면 안에서 처리할 수 있어야 한다. 다만 **이번 v1에서는 held stock visibility를 계좌 자동 연동이 아니라 frontend fixture가 명시한 종목에 한해 지원**한다.

즉, v1에서 보유 종목이 화면에 보이려면 해당 종목이 `StockResearchViewModel.items`에 포함되어 있어야 한다. 현재 세션 범위에서는 "보유 계좌 전체를 자동으로 끌어와 watchlist에 합치는 기능"은 만들지 않는다.

### 리스트에서 추가로 노출할 것

- `보유중` 배지
- 리스크 상태 한 줄

### 해석 원칙

- 미보유 종목: **매수 우선순위**
- 보유 종목: **추가매수/보유유지/축소검토 우선순위**
- 보유 종목 + `축소 검토`는 리스트 혼란을 막기 위해 **하위 score band**로 강등
- 보유 종목 + `보유 유지`는 **중립 score band**
- 보유 종목 + `추가매수 후보`만 상위 score band 허용

즉, 동일한 watchlist rail 안에서 발굴과 관리가 공존하지만, 해석 문구가 다르다.

`현재 판단(보유 유지 / 추가매수 후보 / 축소 검토)`은 watchlist row가 아니라 **상세 패널 판단 헤더**에서만 강조한다.

---

## 8. 상세 패널 블록 구성

### 8.1 판단 헤더

- 종합점수
- 현재 판단
- 선정 이유
- 점수 분해

### 8.2 메인 차트 블록

- 가격 차트
- 주요 가격대 / 추세 구간
- 이벤트 마킹
- 짧은 기술적 해석

### 8.3 보조 분석 카드

- 매크로 상황
- 옵션시장
- 리스크 상태

이번 세션 v1에서는 모두 **요약 카드 수준**으로 구현한다.

### 8.4 메모 / 캡처 / 다음 액션

- 메모
- 더미 썸네일 기반 캡처 strip
- 다음 액션
  - 예: `실적 발표 후 재평가`
  - 예: `후보 유지`
  - 예: `보류 전환`

### 8.5 섹터/테마 겹침 상세

사용자가 지적한 중요 포인트이므로 하단 별도 블록으로 둔다.

- 어떤 보유 종목과 겹치는지
- 어떤 테마가 중복되는지
- 그래서 왜 점수가 깎였는지

---

## 9. Home / Inbox 최소 계약

이번 세션은 Stock Research Manager 내부 작업면이 중심이다. 따라서 **Home / Inbox는 기존 backend snapshot contract를 유지**하고, 이 세션에서 새 신호 체계를 강제로 주입하지 않는다.

즉, 목표 4의 의미는 **기존 Home / Inbox가 stock_research manager와 느슨하게 계속 연결되도록 최소 contract를 명시**하는 것이다. 이번 세션은 Home / Inbox의 source of truth를 바꾸지 않는다.

### 9.1 Home

- 상위 후보 1~3개
- 한 줄 요약
  - 예: `상위 후보 3개 추적 중, 반도체 섹터 중복 주의`
- 다음 액션 1개

고정 contract ownership:

- 소유권: 기존 backend snapshot export
- 프론트는 기존 `ManagerCardSummary`만 소비
- precedence: `wealth_home.manager_cards[]` 우선, 없으면 top-level `manager_cards[]` fallback

정확한 field:

- `ManagerCardSummary.manager_id = 'stock_research'`
- `ManagerCardSummary.status`
- `ManagerCardSummary.headline`
- `ManagerCardSummary.summary`
- `ManagerCardSummary.recommended_action`
- `ManagerCardSummary.key_points`
- `ManagerCardSummary.warning_count`
- `ManagerCardSummary.stale`
- `ManagerCardSummary.warnings`
- `ManagerCardSummary.generated_at`

field 의미 고정:

- `headline`
  - stock research headline 한 줄
- `summary`
  - manager 전반의 짧은 요약
- `recommended_action`
  - manager 차원의 다음 액션 1개
- `key_points`
  - 기존 summary builder가 주는 포인트 목록

### 9.2 Inbox

- action item 1개
- warning 1개
- 필요하면 후보 관련 메시지 1개 추가

고정 contract ownership:

- 소유권: 기존 backend snapshot export
- 프론트는 기존 `HomeInboxItem`만 소비
- precedence: `wealth_home.inbox_preview[]` 우선, 없으면 top-level `home_inbox[]` fallback

정확한 field:

- `HomeInboxItem.id`
- `HomeInboxItem.manager_id = 'stock_research'`
- `HomeInboxItem.severity`
- `HomeInboxItem.title`
- `HomeInboxItem.detail`
- `HomeInboxItem.recommended_action`
- `HomeInboxItem.stale`

업데이트 타이밍:

- snapshot refresh 시점에 함께 갱신
- Stock Research Manager 내부 local edit는 v1에서 Home / Inbox로 write-through 하지 않음

field 의미 고정:

- `title`
  - stock research 관련 액션 또는 경고 제목
- `detail`
  - 왜 이 항목이 필요한지 한 줄 설명
- `recommended_action`
  - 실제 사용자가 취할 다음 액션
- `stale`
  - 기존 계약상 string 형태를 그대로 소비

### 9.3 일부러 제외하는 것

이번 세션에서는 Home / Inbox에 아래는 싣지 않는다.

- manager 내부 score 상세
- top candidates local recompute 결과
- local edit 상태
- 차트
- 매크로 상세
- 옵션시장 상세
- 캡처
- 상세 점수 분해

이들은 모두 Stock Research Manager 내부 workspace에서만 본다.

---

## 10. 데이터와 구현 깊이

이번 세션은 usable surface가 우선이므로 **설명 가능한 더미/수동 데이터 기반 v1**을 허용한다.

### 10.0 v1 데이터 소유권 원칙

v1은 완전한 research system이 아니라 **읽기 중심 + 세션 내 편집 가능한 작업면**이다. 따라서 데이터 소유권을 아래처럼 고정한다.

- **Home / Inbox / manager card 요약**
  - 소유권: 기존 backend snapshot export
  - 프론트는 기존 `AppSnapshot` contract를 그대로 소비
- **Stock Research Manager 내부 상세 workspace**
  - 소유권: frontend-derived `StockResearchViewModel`
  - 기존 snapshot summary + frontend fixture/adapter 조합으로 생성
- **상태 전이 / 메모 수정 / 다음 액션 수정**
  - v1에서는 **브라우저 세션 메모리(local component state)** 에만 반영
  - backend write path는 이번 세션 범위에서 제외

### 10.1 v1 StockResearchViewModel

구현 계획이 추측하지 않도록, v1 UI model을 아래처럼 고정한다.

```ts
type StockResearchStatus = '탐색' | '관찰' | '후보' | '보류' | '제외'

type StockResearchHoldAction = '추가매수 후보' | '보유 유지' | '축소 검토' | null

type StockResearchJudgment = '매수 후보' | '추가매수 후보' | '보유 유지' | '축소 검토' | '제외'

type StockChartPoint = {
  date: string
  close: number
  ma20?: number
  ma50?: number
}

type StockChartMarker = {
  kind: 'earnings' | 'risk' | 'memo'
  date: string
  label: string
}

type StockPriceZone = {
  label: string
  value: number
}

type StockCaptureThumb = {
  id: string
  label: string
  image_url: string
}

type StockOverlapDetail = {
  type: 'sector' | 'theme' | 'holding'
  label: string
  matched_symbol?: string
  impact: 'low' | 'medium' | 'high'
  reason: string
}

type StockResearchItemViewModel = {
  id: string
  symbol: string
  company_name: string
  status: StockResearchStatus
  buy_priority_score: number
  primary_reason: string
  score_drivers: string[]
  is_held: boolean
  hold_action: StockResearchHoldAction
  display_judgment: StockResearchJudgment
  risk_flags: string[]
  sector_overlap_flags: string[]
  overlap_details: StockOverlapDetail[]
  scoring_breakdown: {
    stock_quality_raw: number
    portfolio_fit_raw: number
    concentration_penalty: number
  }
  chart_series: StockChartPoint[]
  chart_markers: StockChartMarker[]
  price_zones: StockPriceZone[]
  chart_notes: string[]
  macro_summary: string
  options_summary: string
  memo: string
  next_action: string
  captures: StockCaptureThumb[]
}

type StockResearchViewModel = {
  generated_at: string
  items: StockResearchItemViewModel[]
  selected_item_id: string | null
  status_counts: Record<StockResearchStatus, number>
  top_candidates: string[] // symbol list
  summary_line: string
  warning_line: string | null
}
```

#### 블록별 필드 매핑

- watchlist rail
  - `symbol`, `company_name`, `status`, `buy_priority_score`, `primary_reason`, `score_drivers`, `is_held`, `risk_flags`
- 판단 헤더
  - `buy_priority_score`, `primary_reason`, `display_judgment`, `scoring_breakdown`
- 차트 블록
  - `chart_series`, `chart_markers`, `price_zones`, `chart_notes`
- 보조 분석 카드
  - `macro_summary`, `options_summary`, `risk_flags`
- 메모/캡처/다음 액션
  - `memo`, `captures`, `next_action`
- 섹터/테마 겹침 상세
  - `sector_overlap_flags`, `overlap_details`

### 10.2 v1 데이터 생성 규칙

v1은 기존 backend snapshot만으로 상세 workspace를 채우기 어렵기 때문에, 아래 2단 구조를 사용한다.

1. **기존 snapshot에서 읽는 것**
   - `manager_cards[]` / `wealth_home.manager_cards[]` 중 `manager_id === 'stock_research'`
   - `manager_summaries.stock_research`
   - `home_inbox[]` / `wealth_home.inbox_preview[]` 중 `manager_id === 'stock_research'`
2. **frontend fixture/adapter에서 채우는 것**
   - `StockResearchViewModel.items`
   - 차트/매크로/옵션/캡처/메모 더미 데이터

즉, v1은 **Home / Inbox는 기존 snapshot 유지**, **manager workspace는 frontend adapter + fixture로 채움**이 원칙이다.

#### adapter 입력과 join 규칙

v1 adapter는 **`/dashboard_snapshot.json` + frontend static fixture + local state`만 사용**한다.

- snapshot input
  - `manager_cards[]` / `wealth_home.manager_cards[]`
  - `manager_summaries.stock_research`
  - `home_inbox[]` / `wealth_home.inbox_preview[]`
- frontend static fixture
  - key: `symbol`
  - `StockResearchItemViewModel`의 상세 필드 source of truth
  - 필요 시 held stock도 이 fixture에 직접 포함

즉, v1은 `data/manual/wealth_manual.json`을 직접 fetch/import하지 않는다. planner가 새 fetch path나 snapshot export 변경을 추측하지 않도록, **manager workspace 데이터는 frontend static fixture가 책임진다.**

#### 점수 출처와 산식

v1에서 `scoring_breakdown`은 **frontend detail fixture가 source of truth**이고, `buy_priority_score`는 **adapter가 계산하는 값**이다.

- `stock_quality_raw`: 0~100
- `portfolio_fit_raw`: 0~100
- `concentration_penalty`: 0~30
- `base_score = round(clamp(stock_quality_raw * 0.6 + portfolio_fit_raw * 0.4 - concentration_penalty, 0, 100))`
- `buy_priority_score`는 **held/unheld band rule까지 적용된 최종 displayed/sorted score**

즉, backend snapshot에서 score를 파생하지 않는다. v1은 **설명 가능한 fixture 기반 점수**를 쓰고, 후속 단계에서만 backend/AI 점수화로 확장한다.

#### held / unheld score 해석 band

- 미보유 종목: 계산된 `buy_priority_score` 그대로 사용
- 보유 종목 + `추가매수 후보`: score 유지
- 보유 종목 + `보유 유지`: `50~69` band로 clamp
- 보유 종목 + `축소 검토`: `0~29` band로 clamp

이 규칙은 “축소 검토인데도 상단에 남는” 문제를 막기 위한 UI 해석 규칙이다.

#### 현재 판단(display_judgment) 생성 규칙

`display_judgment` 역시 fixture/adapter가 명시적으로 만든다.

- `status === '제외'` 이면 무조건 `제외`
- `is_held === true` 이고 `hold_action`이 있으면 `hold_action`을 그대로 사용
- `is_held === false` 이고 `status === '후보'` 이면 `매수 후보`
- `is_held === false` 이고 `status !== '후보'` 이면 fixture가 준 `display_judgment` 사용하되 v1 권장값은 `매수 후보` 또는 `제외`

즉, 판단 헤더는 `status + is_held + hold_action + fixture`의 조합으로 결정되며, planner가 추측하지 않도록 `display_judgment`를 최종 field로 저장한다.

#### adapter fallback 규칙

- 같은 `symbol`이 여러 번 나오면
  - 첫 번째 row를 유지하고 나머지는 무시
- fixture entry가 없으면
  - `company_name = symbol`
  - `stock_quality_raw = 55`
  - `portfolio_fit_raw = 50`
  - `concentration_penalty = 0`
  - `primary_reason = '세부 리서치 데이터가 아직 없습니다.'`
  - `chart_series = []`, `chart_markers = []`, `price_zones = []`
  - `macro_summary = '시장 요약 데이터 없음'`
  - `options_summary = '옵션시장 데이터 없음'`
  - `captures = []`
- malformed score input는 clamp 후 기본값으로 대체
- held 여부가 명시되지 않으면 `is_held = false`, `hold_action = null`

### 10.3 비어 있음 / 누락 / stale 기본 동작

- watchlist가 비어 있으면
  - 빈 상태 화면: `관심종목이 없습니다. 새 후보를 추가하세요.`
- 선택 종목이 없으면
  - 첫 번째 score item 자동 선택
  - item도 없으면 empty workspace
- 차트/매크로/옵션 상세가 없으면
  - placeholder copy 표시
- snapshot이 stale이면
  - stock_research header에 stale badge 추가
  - Home / Inbox contract는 건드리지 않고 manager 내부에서만 stale 안내

### 10.4 local edit lifecycle

v1 local edit는 아래처럼 동작한다.

- route 진입 시: adapter 결과를 초기 local state로 복사
- 같은 브라우저 세션 내 편집:
  - `onSelect(itemId)`
  - `onStatusChange(itemId, nextStatus)`
  - `onMemoChange(itemId, nextMemo)`
  - `onNextActionChange(itemId, nextAction)`
- route 재진입 / full refresh / 새 snapshot load 시:
  - local edit는 **reset**
  - merge/write-through 없음

즉, v1 편집은 어디까지나 workspace usability용 세션 상태다.

#### local edit가 반영되는 영역

- **반영됨**
  - Stock Research Manager 내부의 `status_counts`
  - `top_candidates`
  - `summary_line`
  - 현재 선택 종목 상세 패널
- **반영되지 않음**
  - Home 페이지
  - Inbox 페이지
  - backend-owned `manager_cards[]`
  - backend-owned `home_inbox[]`

즉, manager 내부 header summary는 local state를 따라가지만, Home / Inbox는 snapshot refresh 전까지 frozen 상태를 유지한다.

### 10.5 source-of-truth 표

| 데이터 | 로드 위치 | 소유 레이어 | v1 반영 위치 |
|---|---|---|---|
| `manager_cards[]` / `wealth_home.manager_cards[]`의 `stock_research` entry | `/dashboard_snapshot.json` | backend snapshot export | Home / Managers 카드, manager 상단 summary seed |
| `home_inbox[]` / `wealth_home.inbox_preview[]`의 `stock_research` item | `/dashboard_snapshot.json` | backend snapshot export | Inbox / Home preview |
| `StockResearchViewModel.items` | frontend static fixture | frontend | manager watchlist + detail workspace |
| local 상태 전이 / 메모 / next action | component local state | frontend session state | manager 내부만 |
| `top_candidates`, `summary_line`, `warning_line` | fixture + local state 파생 | frontend | manager 내부 header만 |
| stale badge | snapshot + local manager rule | mixed | manager 내부 header, 기존 Home/Inbox stale 필드 유지 |

### 10.6 snapshot/header fallback 규칙

- `/dashboard_snapshot.json` 로드 실패 시
  - manager header는 fixture 기반 fallback headline 사용
  - Home / Inbox 연동은 비활성
- `manager_summaries.stock_research`가 비어 있으면
  - header summary는 `StockResearchViewModel.summary_line` 사용
  - warning line이 있으면 header에 함께 표시
- `manager_cards[]`에 `stock_research` entry가 없으면
  - manager 내부 화면은 계속 렌더링하되 카드 연동은 fallback copy 사용

### 10.7 manager-internal 파생 규칙

아래 값들은 Home / Inbox가 아니라 **Stock Research Manager 내부 header** 전용 파생값이다.

- `top_candidates`
  - 포함 대상:
    - `status === '후보'`
    - 또는 `is_held === true && display_judgment === '추가매수 후보'`
  - 정렬: `buy_priority_score` 내림차순
  - 출력: 상위 3개 `symbol`
- `warning_line`
  - 우선순위:
    1. `overlap_details` 중 `impact === 'high'` 첫 항목
    2. 없으면 첫 `risk_flags`
    3. 없으면 `null`
- `summary_line`
  - `top_candidates.length > 0` 이면
    - `상위 후보 {n}개 추적 중`
    - `warning_line`이 있으면 뒤에 연결
  - 그렇지 않으면
    - `후보 없음, 관찰 종목 중심으로 관리 중`
- stale badge
  - `manager_cards[].stale === true` 이거나
  - `manager_summaries.stock_research.stale === true`
  - 둘 중 하나면 manager 내부 stale badge 표시
  - 참고: `ManagerCardSummary.stale`는 boolean, `HomeInboxItem.stale`는 기존 계약상 string이므로 v1에서는 형 변환 없이 소비한다

### 10.8 worked example

#### 예시 1: 미보유 후보 `NVDA`

- fixture row
  - `symbol = 'NVDA'`
  - `status = '후보'`
  - `is_held = false`
  - `stock_quality_raw = 88`
  - `portfolio_fit_raw = 82`
  - `concentration_penalty = 9`
- 계산
  - `base_score = round(88 * 0.6 + 82 * 0.4 - 9) = 76`
  - 미보유이므로 `buy_priority_score = 76`
  - `display_judgment = '매수 후보'`
- UI 결과
  - watchlist 상단권 노출 가능
  - row에는 `후보`, `성장 모멘텀`, `반도체 중복`
  - detail header에는 `매수 후보`

#### 예시 2: 보유중이지만 축소 검토인 `AAPL`

- fixture row
  - `symbol = 'AAPL'`
  - `status = '관찰'`
  - `is_held = true`
  - `hold_action = '축소 검토'`
  - `stock_quality_raw = 72`
  - `portfolio_fit_raw = 41`
  - `concentration_penalty = 12`
- 계산
  - `base_score = round(72 * 0.6 + 41 * 0.4 - 12) = 48`
  - held + `축소 검토`이므로 `buy_priority_score = clamp(48, 0, 29) = 29`
  - `display_judgment = '축소 검토'`
- UI 결과
  - watchlist 하단권 이동
  - row에는 `보유중` 배지 + 리스크 상태
  - detail header에는 `축소 검토`
  - Home / Inbox는 즉시 바뀌지 않고 snapshot refresh 전까지 기존 값 유지

### 10.9 의존성 원칙

v1 차트/캡처 표현은 **신규 외부 의존성 없이 구현**한다.

- 차트: SVG / div 기반 lightweight visualization 우선
- 캡처: 정적 더미 이미지 URL 또는 public asset 사용
- 실제 업로드 / 저장 / charting library 도입은 후속 단계

### v1에서 실제 구현할 것

- watchlist 리스트 화면
- 상태 전이 UI
- 점수 + 점수 드라이버 + 집중도/중복 배지
- 종목 상세 패널
- 차트 중심 레이아웃
- 매크로/옵션 요약 카드
- 메모/캡처/다음 액션
- Home / Inbox 최소 contract 연결

### v1에서 placeholder 또는 요약으로 둘 것

- 실제 업로드형 캡처 저장
- 정교한 실시간 매크로 엔진
- 정교한 옵션시장 분석 엔진
- 실시간 AI 리서치 생성
- 자동화된 정량 스코어링 모델

---

## 11. 경계와 인터페이스

설계 단위는 아래처럼 나눈다.

### A. Stock watchlist surface

- 책임: 종목 목록 정렬 / 선택 / 상태 표시
- 입력: `StockResearchViewModel.items`
- 출력: 선택 종목 id, 상태 전이 이벤트

### B. Stock detail workspace

- 책임: 선택 종목의 종합 분석 UI 렌더링
- 입력: `StockResearchItemViewModel`
- 출력: 메모/상태/다음 액션 변경 이벤트

### C. Stock manager summary contract

- 책임: Home / Inbox / manager card에 필요한 최소 요약 파생
- 입력:
  - 기존 backend stock_research summary builder output
  - 기존 backend stock_research inbox builder output
- 출력:
  - `manager_cards` 배열 중 `manager_id === 'stock_research'` entry
  - `home_inbox` / `inbox_preview` 배열 중 `manager_id === 'stock_research'` entry
- 비고:
  - 기존 UI 컴포넌트는 변경하지 않는다
  - 이번 세션은 contract shape를 유지하고 frontend는 소비만 한다

### D. Fixture/manual data adapter

- 책임: v1에서 frontend static fixture를 화면 친화적인 구조로 매핑
- 입력:
  - 기존 snapshot summary fields
  - frontend detail fixture
- 출력: `StockResearchViewModel`

이 분리는 구현 계획 단계에서 파일 단위 책임으로 바로 옮길 수 있어야 한다.

---

## 12. 성공 기준

이 세션이 끝났다고 말할 수 있으려면 다음이 충족되어야 한다.

1. Stock Research Manager가 더 이상 scaffold-only가 아니다.
2. watchlist를 점수순으로 훑을 수 있다.
3. 상태 전이가 눈에 보이고 조작 가능하다.
4. 종목 클릭 시 차트 중심의 분석 workspace가 열린다.
5. 종합점수 / 선정 이유 / 포트 적합도 / 섹터 겹침이 화면에서 이해된다.
6. Home / Inbox에 stock_research 관련 최소 계약이 연결된다.
7. 다른 manager와 코어 대시보드의 범위를 침범하지 않는다.

---

## 13. 구현 시 주의점

- 과도한 AI 고도화 없이 **usable surface**를 먼저 만든다.
- 섹터 겹침은 단순 경고 문구가 아니라 **설명 가능한 UI 신호**여야 한다.
- 다른 manager 파일은 건드리지 않거나, contract 유지 수준의 최소 수정만 허용한다.
- 차트가 workspace의 중심이라는 원칙을 유지한다.
- Home / Inbox에는 요약/행동 유도만 싣고, 상세 분석은 절대 넘치게 보내지 않는다.
