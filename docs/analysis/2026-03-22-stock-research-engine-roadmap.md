# Stock Research Engine 설계 고려사항 / 숨은 제약 / 고도화 로드맵

작성일: 2026-03-22  
대상 범위: `stock_research_workspace`, `StockResearchManager`, 향후 별도 research/scoring engine

---

## 1. 지금 상태 한 줄 요약

현재 Stock Research는 **“리서치 작업대 UI + 수동 seed 기반 workspace”** 까지는 올라와 있지만,  
아직 **별도의 연구 엔진 / 점수 엔진 / 근거 수집 엔진** 이 분리된 상태는 아닙니다.

즉 지금 구조는:

- 프론트는 workbench 형태를 갖췄고
- 백엔드는 snapshot 안에 stock research seed를 밀어넣고
- 일부 evidence / compare / flow shape는 계약상 추가되었지만
- 실제 판단 품질을 좌우하는 엔진은 아직 시작 전 단계입니다.

---

## 2. 현재 코드 기준 실제 구현 상태

### 2.1 백엔드

현재 `src/tqqq_strategy/ops/dashboard_snapshot.py` 의 `_build_stock_research_workspace(...)` 는:

- `manual_inputs["stock_watchlist"]`
- `manual_inputs["positions"]`

만을 이용해 아래를 seed합니다.

- `items`
- `queue`
- `flow`
- `evidence`
- `compare_seed`

즉 현재는 **실제 market data / 뉴스 / 기관 수급 / 팩터 계산** 기반이 아니라,  
**수동 watchlist를 UI가 먹을 수 있는 workspace 계약으로 변환하는 어댑터**에 가깝습니다.

또 `src/tqqq_strategy/ai/manager_jobs.py` 의 stock research summary도:

- 상태 정규화
- 후보 수 / 관찰 수 카운트
- recommended action 1개 생성

정도의 매니저 summary 레벨까지만 담당합니다.

### 2.2 프론트

`app/web/src/pages/managers/StockResearchManager.tsx` 는 이미:

- Header
- Queue
- Watchlist
- Detail

흐름을 연결하고 있습니다.

하지만 실제 상세 블록을 보면 아직 다음이 많습니다.

- `StockResearchDetail.tsx` 내 signal / overlap 수치 / max drawdown / news 일부가 하드코딩
- `StockResearchComparePanel.tsx` 는 compare slot shell 수준
- `StockResearchEvidencePanel.tsx` 는 evidence seed를 받지만 표현은 아직 mock-friendly skeleton

즉 프론트는 **“진짜 엔진이 들어올 자리”** 를 미리 만들어 둔 상태입니다.

---

## 3. 가장 중요한 숨은 제약

이 작업에서 진짜 중요한 건 기능 추가보다 **계약 분리** 입니다.

### 제약 1. 지금은 “workspace 생성”과 “research 판단”이 섞여 있다

현재 snapshot builder가:

- 상태 정규화
- 점수 계산
- 리스크 레벨 추정
- 우선순위 이유 생성

까지 같이 해버립니다.

이 구조는 v1에는 빠르지만, 이후에는 문제가 됩니다.

왜냐하면:

- snapshot은 **표현용 read model**
- research engine은 **판단용 decision model**

이어야 하기 때문입니다.

이 둘이 섞이면 프론트 요구가 바뀔 때마다 판단 로직까지 흔들립니다.

### 제약 2. 점수 계산이 백엔드/프론트에 이원화될 위험이 있다

현재 백엔드에는 `_stock_score(...)` 가 있고,  
프론트에는 `calculateBuyPriorityScore(...)` 같은 별도 계산 계층이 존재합니다.

즉 지금 상태를 그대로 키우면:

- 홈/스냅샷 점수
- 상세 패널 점수
- 나중의 엔진 점수

가 서로 조금씩 다른 값을 낼 위험이 큽니다.

이건 나중에 사용자가 가장 먼저 불신하는 지점이 됩니다.

### 제약 3. 상태(state)와 점수(score)는 다른데 아직 경계가 약하다

현재 상태 모델은 `탐색 / 관찰 / 후보 / 보류 / 제외` 입니다.

이 상태는 원래:

- 운영 단계
- 워크플로우 위치
- 팀의 의사결정 상태

를 뜻해야 합니다.

반면 점수는:

- 매수 매력도
- 포트폴리오 적합도
- 집중/중복 패널티

같은 정량 판단이어야 합니다.

이 둘이 섞이면 아래 문제가 생깁니다.

- “후보라서 점수가 높다”
- “점수가 높아서 후보다”

가 순환 참조가 됩니다.

즉 앞으로는 **status는 workflow state**, **score는 ranking signal** 로 분리해야 합니다.

### 제약 4. 지금 evidence는 “실제 근거 저장소”가 아니라 UI seed다

현재 evidence는 snapshot에 실려 오는 작은 payload 입니다.

하지만 실제 엔진 단계에서는 evidence가 다음을 포함해야 합니다.

- 가격/기술적 구조 근거
- 이벤트/뉴스 근거
- 팩터/재무 근거
- 포트폴리오 적합도 근거
- 결정 로그(왜 후보/보류/제외인지)

이걸 계속 snapshot 안에 다 넣으면 금방 무거워집니다.

즉 snapshot은 **요약본**, engine/evidence store는 **원본** 이 되어야 합니다.

### 제약 5. “좋은 리서치 엔진”과 “알파 엔진”은 별개다

이건 설계상 매우 중요합니다.

1차 엔진은 충분히:

- 후보를 일관되게 정리하고
- 판단 근거를 구조화하고
- 점수/랭킹을 설명 가능하게 만들고
- 포트 적합성을 보조

할 수 있습니다.

하지만 그 자체가 곧바로 **초과수익 엔진** 을 의미하지는 않습니다.

따라서 검증도 분리해야 합니다.

- **엔진 검증:** 후보 선정/상태 전이/점수 일관성/설명 가능성
- **알파 검증:** 점수와 미래 수익의 상관, 포트 편입 성과, 리밸런싱 후 결과

---

## 4. 우리가 실제로 만들어야 하는 엔진의 층

추천 구조는 아래 4층입니다.

### Layer A. Research Registry

종목별 리서치 엔티티 저장소

예:

- symbol
- universe membership
- current status
- analyst memo
- latest thesis
- next action
- last reviewed at
- evidence refs

이 레이어가 있어야 `manual_truth.stock_watchlist` 를 넘어서:

- 지속적인 상태 관리
- 히스토리 추적
- decision log

가 가능해집니다.

### Layer B. Deterministic Scoring Engine

입력:

- 기술/가격 feature
- 이벤트 feature
- 기본 quality feature
- portfolio fit feature
- concentration / overlap penalty

출력:

- total score
- breakdown
- confidence
- warnings

중요한 점은 이 레이어가 **결정론적** 이어야 한다는 것입니다.

즉 같은 입력이면 같은 출력이 나와야 하고,  
LLM은 여기서 점수 본체가 아니라 **설명/요약 보조** 로 써야 합니다.

### Layer C. Evidence Builders

엔진이 바로 크롤러가 되면 안 됩니다.

근거는 adapter/builder 계층에서 모아야 합니다.

예:

- `price_technical_builder`
- `news_digest_builder`
- `ownership_flow_builder`
- `portfolio_fit_builder`

각 builder는 raw source를 받아 **엔진이 읽을 수 있는 표준 feature/evidence** 로 변환합니다.

### Layer D. Read Models

마지막에만 UI용 모델을 만듭니다.

- dashboard snapshot용 요약
- manager queue용 요약
- detail panel용 lightweight payload
- reports용 narrative block

즉 지금의 `stock_research_workspace` 는 장기적으로 이 레이어에 속해야 합니다.

---

## 5. 권장 고도화 순서

### Phase 1. 계약 분리

가장 먼저 해야 할 일은 새 알고리즘보다 **source of truth 정리** 입니다.

우선순위:

1. stock research domain model 정의
2. score / status / evidence 책임 분리
3. snapshot builder는 read model 생성기로 축소

이 단계의 완료 기준:

- 프론트/홈/리포트/인박스가 같은 stock research contract를 사용
- 점수 계산이 한 곳에서만 정의
- 상태 정규화 규칙이 공용화

### Phase 2. v1 Scoring Engine

이 단계에서는 복잡한 ML 말고 **설명 가능한 rule-based engine** 이 맞습니다.

추천 입력 축:

- trend / relative strength
- event freshness
- thesis quality
- cash availability
- existing holding overlap
- sector/theme concentration

추천 출력:

- `stock_quality_raw`
- `portfolio_fit_raw`
- `concentration_penalty`
- `total_score`
- `confidence_band`
- `primary_reason`
- `risk_flags`

### Phase 3. Evidence 실제화

현재 seed evidence를 실제화합니다.

최소 범위:

- chart evidence: 기간/주요 구간/신호 마커
- news evidence: 최근 핵심 이벤트 3~5개
- portfolio fit evidence: 기존 보유/섹터 중복/현금 여력

여기서 중요한 건 “많이 모으는 것”보다 **요약 가능한 구조** 입니다.

### Phase 4. 상태 전이와 액션 로그

상태 변경이 단순 UI 조작이 아니라 운영 기록이 되게 만들어야 합니다.

예:

- 관찰 → 후보 승격 이유
- 후보 → 보류 사유
- 제외 시 재검토 조건

이게 있어야 나중에:

- 어떤 판단이 맞았는지
- 어떤 기준이 과도했는지
- 어떤 analyst behavior가 drift를 만들었는지

를 돌아볼 수 있습니다.

### Phase 5. 알파 검증

엔진이 돌아간 뒤에야 비로소:

- 상위 점수군 forward return
- score decile별 성과
- 편입 후 n일 / n주 성과
- 후보→편입 전환 룰의 성과

같은 백테스트 검증을 붙입니다.

순서를 거꾸로 하면 “데이터 없는 백테스트 흉내”가 됩니다.

---

## 6. 지금 당장 하면 좋은 백엔드 우선 작업

프론트를 더 만지기 전에 백엔드에서 먼저 끝내면 좋은 건 아래입니다.

### 6.1 stock research domain contract 고정

최소 신규 필드:

- `thesis`
- `primary_reason`
- `risk_flags`
- `scoring_breakdown`
- `fit_summary`
- `evidence_refs`
- `decision_log`

### 6.2 score 계산 위치 단일화

현재/향후 점수 계산은 한 모듈로 모아야 합니다.

추천:

- `src/tqqq_strategy/ai/stock_research_engine.py`

또는

- `src/tqqq_strategy/research/scoring.py`

여기에서만:

- 점수 계산
- breakdown 계산
- warning 계산

을 수행하고, snapshot builder는 그 결과만 읽어야 합니다.

### 6.3 workspace builder를 read model로 축소

`_build_stock_research_workspace(...)` 는 장기적으로:

- 엔진 결과
- evidence 요약
- queue projection

을 합쳐 UI용 payload를 만드는 역할만 해야 합니다.

### 6.4 decision history 저장 시작

수동 watchlist 한 줄로는 곧 한계가 옵니다.

최소한 다음은 남겨야 합니다.

- 상태 변경 시각
- 변경 사유
- 이전 점수 / 새 점수
- 누가 바꿨는지(수동/엔진/운영 rule)

---

## 7. 프론트가 나중에 쉽게 붙도록 하기 위한 조건

프론트는 이미 껍데기를 만들어 두었기 때문에, 백엔드가 아래만 지켜주면 이후 작업이 훨씬 쉬워집니다.

1. `detail` 에 필요한 필드명을 자주 바꾸지 말 것
2. `score`, `breakdown`, `warnings`, `evidence` 를 분리할 것
3. compare panel용 데이터는 단순 symbol list가 아니라  
   **비교 가능한 normalized fields** 로 줄 것
4. 하드코딩 영역을 치환할 때도 빈 상태(empty state) 계약을 먼저 고정할 것

특히 compare는 나중에 아래 축이 필요합니다.

- quality
- fit
- overlap
- action difference

즉 compare는 단순 “AAPL vs NVDA” 가 아니라  
**우리 포트 기준으로 왜 더 맞는지** 를 보여주는 구조여야 합니다.

---

## 8. 추천 최종 목표상

최종적으로 Stock Research는 아래처럼 되어야 합니다.

### Home / Manager / Reports / Inbox 가 같은 엔진 결과를 바라본다

- Home: 상위 후보와 경고
- Manager: 탐색/상세/비교/액션
- Inbox: 우선순위 태스크
- Reports: 이번 주 후보 변화와 이유

즉 UI가 4개가 아니라 **하나의 research engine을 4개 surface가 다르게 투영** 하는 구조여야 합니다.

### 엔진은 “설명 가능한 결정기” 여야 한다

최종 엔진은 black-box 예측기가 아니라:

- 왜 후보인지
- 왜 보류인지
- 왜 포트에 안 맞는지
- 다음 액션이 뭔지

를 일관되게 설명할 수 있어야 합니다.

### AI는 점수 본체보다 설명/요약/질문 보조가 적합하다

이 프로젝트 맥락에서는 LLM을:

- 근거 요약
- narrative 생성
- 보고서 문장화
- follow-up question 생성

에 쓰는 것이 맞고,

핵심 ranking/score 본체는 deterministic layer가 더 적합합니다.

---

## 9. 결론

현재 해야 할 다음 단계는 **프론트 디테일 polish** 가 아니라,  
**별도 stock research engine의 경계를 세우는 것** 입니다.

가장 추천하는 실제 순서는 아래입니다.

1. **contract 정리**
2. **scoring engine 분리**
3. **evidence builder 추가**
4. **decision/state history 도입**
5. **그 다음 compare/report/inbox 고도화**
6. **마지막에 알파 검증**

핵심은 이것입니다.

> 지금 필요한 것은 “더 화려한 연구 화면”이 아니라  
> “모든 화면이 공통으로 신뢰할 수 있는 stock research 판단 엔진” 입니다.

