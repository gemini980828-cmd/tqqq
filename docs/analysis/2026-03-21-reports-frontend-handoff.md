# Alpha Wealth Desk Reports 프론트엔드 전달서

작성일: 2026-03-21  
범위: **디자인 제외**, UI/UX 흐름 / 기능 / 백엔드 계약 연결 중심  
목적: Reports 화면이 단순 KPI 카드 화면을 넘어, **운영 브리핑 + 비교 분석 진입점** 역할을 하도록 프론트 연결 방향을 정리

---

# 1. 이 문서의 목표

현재 Reports는 주로 KPI 카드 중심입니다.

즉, 지금은:
- CAGR
- MDD
- 1M 수익률

같은 숫자는 볼 수 있지만,

- 무슨 일이 있었는지
- 왜 중요한지
- 어떤 manager를 다시 봐야 하는지
- 어떤 manager끼리 비교해야 하는지

는 충분히 드러나지 않습니다.

이번 작업의 목표는 Reports를 아래처럼 바꾸는 것입니다.

> **숫자 대시보드**  
> → **운영 브리핑 + 비교 분석 화면**

즉, Reports는 “읽는 화면”이자 “다음 행동을 다시 정리하는 화면”이 되어야 합니다.

---

# 2. 이번 프론트 작업의 성격

이번 작업은 **새로운 리포트 엔진을 만드는 것**이 아닙니다.

이미 backend가 제공 중인 아래 필드를
Reports 화면이 **실제로 소비**하게 만드는 작업입니다.

주요 backend 필드:

- `kpi_cards`
- `report_highlights`
- `compare_data`
- `manager_events`
- `priority_actions`
- `cross_manager_alerts`
- `meta`

즉,
backend에서 이미 정리된 narrative/comparison 블록을
Reports UI에 연결하는 것이 핵심입니다.

---

# 3. 이번 작업에서 가장 중요한 UX 원칙

## 원칙 1. Reports는 “숫자 카드 모음”으로 끝나면 안 됨

사용자는 Reports에서 단순히
- CAGR이 얼마인지
- MDD가 얼마인지

만 보는 게 아니라,

**“이번에 무슨 판단 포인트가 있었는가”**
를 읽어야 합니다.

---

## 원칙 2. Reports는 Home의 재탕이 아니라 “정리된 시점”이어야 함

Home은 action-first입니다.  
Reports는 그 action을 다시 정리해서:

- 어떤 변화가 있었는지
- 어떤 manager가 중요했는지
- 어떤 충돌/비교 포인트가 있었는지

를 읽게 해주는 화면이어야 합니다.

즉:

- Home = 지금 행동
- Reports = 지금까지의 운영 맥락 정리

---

## 원칙 3. Reports도 결국 행동을 위한 화면이어야 함

읽고 끝나는 화면이 아니라,
읽은 뒤:

- manager 페이지로 가거나
- 비교 포인트를 다시 보거나
- orchestrator 질문으로 이어지게

연결되어야 합니다.

---

# 4. 반드시 사용해야 하는 backend 데이터

## 4.1 KPI 영역

사용 데이터:
- `snapshot.kpi_cards.cagr_pct`
- `snapshot.kpi_cards.mdd_pct`
- `snapshot.kpi_cards.month_1_return_pct`
- `snapshot.kpi_cards.condition_pass_rate`

이 영역은 기존처럼 유지 가능하지만, 화면에서 주연이 아니라 **상단 요약 띠**에 가까워져도 됩니다.

---

## 4.2 Narrative 영역

사용 데이터:
- `snapshot.report_highlights`

현재 backend가 주는 구조 예:
- `id`
- `title`
- `summary`
- `severity`
- `manager_ids`
- `updated_at`

이 영역이 Reports의 핵심입니다.

이걸 통해 사용자는
“이번 보고서에서 먼저 읽어야 할 포인트”를 바로 이해할 수 있어야 합니다.

---

## 4.3 Comparison 영역

사용 데이터:
- `snapshot.compare_data.manager_pairs`
- `snapshot.compare_data.holding_overlap`
- `snapshot.compare_data.conflicting_recommendations`

이 영역은 비교 분석용입니다.

지금 단계에서는 완전한 분석 툴로 만들 필요 없습니다.
우선은:

- 어떤 manager pair가 중요한지
- 어떤 공통 항목(shared symbol)이 있는지
- 어떤 recommendation conflict가 있는지

를 읽기 좋게 보여주면 충분합니다.

---

## 4.4 Supporting context 영역

사용 가능 데이터:
- `snapshot.priority_actions`
- `snapshot.cross_manager_alerts`
- `snapshot.manager_events`

이 데이터는 Reports의 주연은 아니지만,
필요하면
“이번 브리핑과 연결된 최근 변화”
정도로 보조적으로 붙일 수 있습니다.

단, Home처럼 action hub 구조로 만들 필요는 없습니다.

---

## 4.5 Freshness / provenance

사용 가능 데이터:
- `snapshot.meta.signal_updated_at`
- `snapshot.meta.market_updated_at`
- `snapshot.meta.summary_source_version`
- `snapshot.meta.audit_available`

이건 화면 하단 또는 header subtext 정도에서
“이 리포트가 어떤 시점 기준인지”
를 보여주는 용도로만 쓰면 충분합니다.

---

# 5. Reports 화면 목표 구조

아래 구조를 권장합니다.

```tsx
<ReportsPage>
  <ReportsSummaryBar />
  <ReportsNarrativeSection />
  <ReportsComparisonSection />
  <ReportsContextSection />
</ReportsPage>
```

---

## 5.1 `ReportsSummaryBar`

역할:
- 숫자 KPI를 짧게 요약

포함 추천:
- CAGR
- MDD
- 1M 수익률
- condition pass rate

주의:
- 이 영역은 중요하지만, narrative보다 위계가 높아지면 안 됩니다.
- 즉, KPI는 **요약 도구**이지 화면의 주인공이 아닙니다.

---

## 5.2 `ReportsNarrativeSection`

역할:
- Reports의 주연 블록

사용 데이터:
- `report_highlights`

표시 최소 단위:
- `title`
- `summary`
- `severity`
- `manager_ids`

UX 목표:
- 사용자가 Reports에 오면 제일 먼저
  **“이번에 다시 볼 포인트가 무엇인지”**
  를 여기서 파악해야 함

동작:
- 각 highlight는 관련 manager로 이동 가능하면 좋음
- 최소한 manager badge는 표시

주의:
- 디자인보다 정보 위계가 더 중요
- 카드 수가 많으면 3~5개 정도로 압축

---

## 5.3 `ReportsComparisonSection`

역할:
- 비교/충돌 포인트 정리

### A. manager_pairs
표시 목적:
- 어떤 manager들을 함께 봐야 하는지

표시 최소 항목:
- pair 이름
- 두 manager 이름
- 각 manager headline

### B. holding_overlap
표시 목적:
- 공통 추적 항목이 무엇인지

표시 최소 항목:
- left manager
- right manager
- shared symbols

### C. conflicting_recommendations
표시 목적:
- 왜 같이 봐야 하는지
- 어떤 우선순위 충돌이 있는지

표시 최소 항목:
- 관련 manager들
- conflict detail

주의:
- 이 영역은 “비교 도구”라기보다
  **“비교 이슈 브리핑”**
  으로 생각하면 됩니다.

---

## 5.4 `ReportsContextSection`

역할:
- 보조 컨텍스트 제공

가능한 내용:
- 최근 manager event 2~3개
- 최근 priority action 요약
- meta freshness 정보

이 영역은 너무 크지 않게 하세요.

목적은:
- narrative와 comparison을 읽고 난 뒤
- “이 리포트가 어느 시점 기준인가”
- “어떤 최근 변화가 연결돼 있나”
를 확인하게 하는 것입니다.

---

# 6. 프론트에서 해야 할 기능 작업

## Task A. `Reports.tsx`를 narrative/comparison 중심으로 재구성

현재 KPI-only 구조를 아래 단계로 확장하세요:

1. KPI bar 유지
2. `report_highlights` 섹션 추가
3. `compare_data` 섹션 추가
4. 필요 시 context/meta block 추가

주의:
- KPI 위주에서 narrative 위주로 위계를 옮겨야 합니다.

---

## Task B. `report_highlights` 소비

반드시 top-level에서 읽으세요.

좋은 방식:

```ts
const highlights = snapshot?.report_highlights ?? []
```

나쁜 방식:

```ts
snapshot?.home_discovery?.report_highlights
```

이건 잘못입니다.

---

## Task C. `compare_data` 소비

반드시 아래를 분리해서 읽으세요.

```ts
const pairs = snapshot?.compare_data?.manager_pairs ?? []
const overlap = snapshot?.compare_data?.holding_overlap ?? []
const conflicts = snapshot?.compare_data?.conflicting_recommendations ?? []
```

이후 Reports 안에서
- pair list
- overlap list
- conflict list

를 각각 보여주세요.

---

## Task D. 관련 manager 이동 affordance 연결

Narrative나 comparison을 읽은 뒤
사용자가 다시 manager로 들어갈 수 있어야 합니다.

따라서 아래 affordance를 권장합니다.

- manager badge 클릭
- “Go to manager”
- “Review workspace”

중요:
- route는 문자열 조합 금지
- 반드시 기존 공통 navigation resolver 사용

예:
- `getManagerRoute(managerId)`
- `resolveScreenRoute(...)`

---

## Task E. freshness 표시

`meta.signal_updated_at`, `meta.market_updated_at`는
크게 강조할 필요는 없지만,
리포트 하단이나 소제목 근처에
“기준 시점”으로 붙여주면 좋습니다.

이건 신뢰감과 운영 UX에 중요합니다.

---

# 7. 하지 말아야 할 것

1. **Reports를 다시 KPI-only 화면으로 유지하지 말 것**
2. **backend narrative 데이터를 프론트에서 다시 해석/재계산하지 말 것**
3. **`report_highlights`를 잘못된 위치에서 읽지 말 것**
4. **`compare_data`를 한 묶음 raw blob처럼 처리하지 말 것**
5. **comparison block을 거대한 분석 도구처럼 만들지 말 것**
6. **Home과 똑같은 action hub 구조를 Reports에 복제하지 말 것**

---

# 8. 권장 구현 순서

## Step 1
- `Reports.tsx`에서 top-level `report_highlights`, `compare_data` 읽기

## Step 2
- KPI summary bar 유지
- 그 아래에 narrative section 추가

## Step 3
- comparison section 추가
  - manager pairs
  - overlap
  - conflicts

## Step 4
- manager 이동 affordance 추가

## Step 5
- freshness/meta 보조 정보 추가

---

# 9. 검증 체크리스트

## 필수
- [ ] `report_highlights`가 실제로 렌더링됨
- [ ] `compare_data.manager_pairs`가 렌더링됨
- [ ] `compare_data.holding_overlap`가 렌더링됨
- [ ] `compare_data.conflicting_recommendations`가 렌더링됨
- [ ] manager 관련 이동 affordance가 실제 동작함
- [ ] build 통과
- [ ] lint 통과

## UX 확인
- [ ] Reports 첫 화면에서 숫자보다 narrative가 먼저 읽힘
- [ ] comparison block이 “무슨 관계를 봐야 하는지”를 설명함
- [ ] Reports가 Home의 복제품이 아니라 브리핑 화면처럼 느껴짐

---

# 10. 완료 정의

이번 Reports 프론트 작업은 아래를 만족하면 완료입니다.

1. Reports가 더 이상 KPI-only 화면이 아니다
2. `report_highlights`를 통해 이번에 읽어야 할 핵심 포인트가 드러난다
3. `compare_data`를 통해 manager 관계/겹침/충돌이 드러난다
4. 사용자가 Reports에서 manager 화면으로 다시 이동할 수 있다
5. backend narrative/comparison 계약을 올바르게 소비한다

---

# 11. 한 줄 지시

이번 작업은 Reports를 예쁘게 꾸미는 것이 아니라,  
**이미 backend가 제공하는 narrative / comparison 데이터를 실제로 읽고 연결해서, Reports를 “운영 브리핑 화면”으로 만드는 작업**입니다.
