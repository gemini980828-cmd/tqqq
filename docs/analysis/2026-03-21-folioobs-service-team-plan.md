# Alpha Wealth Desk 개선안 — 프로젝트 팀 역할별 실행 문서

작성일: 2026-03-21  
기준 서비스: `app/web`의 현재 Alpha Wealth Desk  
참조 문서:
- `docs/analysis/2026-03-21-folioobs-site-analysis.md`
- `docs/analysis/2026-03-21-folioobs-component-teardown.md`

---

## 0. 이 문서의 목적

이 문서는 “FolioObs에서 영감을 받아 우리 서비스를 어떻게 개선할 것인가?”를,
**실제 하나의 제품 팀이 일한다고 가정했을 때 각 엔지니어가 무엇을 해야 하는지**까지 풀어쓴 실행 문서입니다.

즉, 아래에 답합니다.
- 지금 우리 서비스는 어디까지 와 있는가?
- FolioObs의 어떤 구조를 가져오면 좋은가?
- 그걸 현실적으로 구현하려면 어떤 팀 구성이 필요한가?
- 각 엔지니어는 어떤 파일, 어떤 화면, 어떤 데이터 계약, 어떤 검증을 맡아야 하는가?

이 문서는 설계와 실행 사이의 다리 역할을 합니다.

---

# 1. 현재 서비스 진단

현재 `Alpha Wealth Desk`는 다음 구조를 갖습니다.

## 현재 존재하는 주요 화면
- `Home`
- `Managers`
- `Research`
- `Inbox`
- `Reports`
- 개별 manager 화면
  - `CoreStrategyManager`
  - `StockResearchManager`
  - `RealEstateManager`
  - `CashDebtManager`

## 현재 강점
- 이미 “운영 데스크”라는 제품 프레임이 존재함
- Home / Manager / Inbox / Reports 구조가 있어 기본 운영 OS 형태가 있음
- `OrchestratorPanel`이 있어서 요약형 AI/질의형 인터페이스의 씨앗이 있음
- `StockResearchManager`는 watchlist/detail/workspace 패턴이 있어 FolioObs식 깊은 탐색 UI로 확장하기 좋음
- snapshot 중심 구조(`AppSnapshot`)가 있어 화면 조립과 정적/캐시 우선 렌더링 전략이 명확함

## 현재 한계
- Home은 아직 “운영 홈”이지 “탐색형 discovery surface”는 아님
- Manager hub는 존재하지만, 서로 간 관계/겹침/비교 UX가 약함
- 데이터는 있지만 “이벤트화 / 서사화 / 카드화”가 아직 부족함
- Orchestrator는 cache-first preview 성격은 있지만, 사용자가 계속 질문하고 탐색하는 루프는 아직 약함
- Research는 아직 shell 수준이고, Watchlist / 후보 관리 / 비교 / 판단 흐름이 충분히 productized되지는 않음
- Reports는 KPI 카드 중심이고 narrative/insight layer가 약함

---

# 2. 우리가 FolioObs에서 가져와야 할 핵심 원칙

FolioObs에서 배워야 할 것은 화면 스타일 그 자체보다,
**“데이터 → 탐색 → 비교 → 해석 → 재방문” 루프**를 제품화한 구조입니다.

우리 서비스 기준으로 번역하면 아래 6개 원칙이 핵심입니다.

## 원칙 1. Home을 요약판이 아니라 “운영 + 탐색 허브”로 바꾼다
현재 Home은 상태판에 가깝습니다.  
앞으로는:
- 오늘 액션
- 리스크/현금/보유 변화
- manager 간 주요 이벤트
- 주목 종목 / 주목 이슈 / 비교 진입점
이 한 화면에서 이어져야 합니다.

## 원칙 2. Manager를 단순 세부화면이 아니라 “전문 워크벤치”로 만든다
FolioObs의 Screener/Compare/Insights처럼,
각 manager는 단순 세부 정보가 아니라 **업무를 하는 공간**이 되어야 합니다.

## 원칙 3. 데이터는 숫자만이 아니라 “이벤트 카드”로도 보여야 한다
예:
- “현금 여력 경고”
- “TQQQ 목표 비중 괴리 확대”
- “후보 종목 NVDA 우선순위 상승”
- “부동산 후보 단지 리스크 증가”
즉, snapshot을 event stream으로 재구성해야 합니다.

## 원칙 4. Orchestrator는 검색창이 아니라 ‘질문 기반 운영 인터페이스’가 되어야 한다
현재 preview는 존재하지만, 더 나아가:
- 무엇을 먼저 해야 하는지
- 어떤 manager가 근거를 갖고 있는지
- 어떤 action이 충돌하는지
를 연결해 주는 오케스트레이터가 필요합니다.

## 원칙 5. 비교 UX를 넣어야 한다
FolioObs가 강한 이유 중 하나는 관계를 보여주기 때문입니다.  
우리도 manager/asset/position/research candidate 사이의 관계를 보여줘야 합니다.

## 원칙 6. 리포트는 숫자 집합이 아니라 ‘운영 서사’가 되어야 한다
Reports는 단순 KPI 나열이 아니라,
- 무엇이 변했는지
- 왜 중요한지
- 다음 액션은 무엇인지
가 보여야 합니다.

---

# 3. 목표 제품상 (우리 서비스 기준)

이번 개선의 최종 목표는 아래와 같습니다.

## 목표 문장
**Alpha Wealth Desk를 “현재 상태를 보는 대시보드”에서 “오늘의 운영과 다음 의사결정을 직접 수행하는 자산관리 운영 시스템”으로 전환한다.**

## 목표 UX
사용자는 Home에 들어오면:
1. 오늘의 핵심 액션을 보고
2. 어떤 manager가 경고/기회를 만들었는지 확인하고
3. 특정 manager workspace로 깊게 들어가며
4. Orchestrator에게 질문하고
5. Reports에서 전체 흐름을 다시 정리하게 됩니다.

즉, 현재의 분절된 화면들을 하나의 작업 흐름으로 엮는 것이 핵심입니다.

---

# 4. 팀 구성 제안

이번 개선은 최소 아래 8개 역할로 나누는 것이 가장 효율적입니다.

1. **Product / Delivery Lead**
2. **Design Systems & UX Engineer**
3. **Home / Discovery Frontend Engineer**
4. **Manager Workspace Frontend Engineer**
5. **Data Contracts & Snapshot Backend Engineer**
6. **Orchestrator / AI Interaction Engineer**
7. **Research & Insights Engineer**
8. **QA / Verification Engineer**

필요하면 9번째로:
9. **Platform / Performance Engineer**

아래부터 각 역할별로 상세히 씁니다.

---

# 5. 역할별 상세 업무

## 5.1 Product / Delivery Lead

### 이 역할의 책임
- 전체 개선안의 scope를 관리
- FolioObs에서 가져올 것과 버릴 것을 결정
- 각 엔지니어의 산출물이 하나의 사용자 여정으로 이어지게 조정
- 단계별 release 기준을 정의

### 이 역할이 반드시 해야 하는 일
1. 현재 제품의 핵심 사용자 시나리오 정의
   - Home 진입
   - manager drill-down
   - orchestrator 질의
   - report 확인
2. 개선 범위를 3단계로 나누기
   - Phase 1: Home/Discovery 강화
   - Phase 2: Manager workspace 고도화
   - Phase 3: Orchestrator + Insights + Report narrative 연결
3. 성공 지표 정의
   - Home에서 manager 진입률
   - Orchestrator 질문 실행률
   - StockResearch manager 체류시간
   - inbox action 확인률
4. 각 화면의 owner 지정
5. QA 완료 기준 / 디자인 완료 기준 / 데이터 준비 기준을 문서화

### 이 역할의 산출물
- 제품 우선순위 문서
- release milestone 문서
- 화면별 owner table
- acceptance checklist

### 의존성
- 없음 (팀 출발점)

### 완료 기준
- 전체 팀이 “이번 개선에서 무엇을 만들고 무엇은 안 만드는지”를 명확히 이해한 상태

---

## 5.2 Design Systems & UX Engineer

### 이 역할의 책임
- FolioObs에서 참고할 컴포넌트 패턴을 우리 제품의 디자인 언어로 번역
- Home / Manager / Insights / Reports 전반에 공통적으로 쓰일 UI primitives 정의

### 이 역할이 맡을 핵심 문제
현재 UI는 안정적이지만,
- section header 패턴
- event card 패턴
- ranked list 패턴
- compare / overlap 패턴
- insight card 패턴
같은 공통 문법이 약합니다.

이 엔지니어는 **제품 전체의 문장법을 만드는 역할**을 맡습니다.

### 작업 목록
1. 공통 섹션 헤더 컴포넌트 정의
   - 아이콘
   - title
   - sublabel
   - 상태 배지
2. 공통 카드 스타일 정의
   - summary metric card
   - event card
   - warning card
   - ranked item card
   - insight card
3. 상태 표현 체계 통일
   - stale
   - warning
   - active
   - success
   - info
4. mobile label density 규칙 정의
   - 긴 라벨을 축약하는 규칙
   - 탭명/버튼명/카드 라벨의 모바일 대응
5. 톤 앤 매너 가이드 작성
   - dark-first 유지 여부
   - accent color 기준
   - 배지 밀도 기준
   - 숫자 정보 hierarchy

### 주로 건드릴 파일
- `app/web/src/index.css`
- `app/web/src/App.css` (정리 필요 시)
- 신규 공통 컴포넌트 예시:
  - `app/web/src/components/ui/SectionHeader.tsx`
  - `app/web/src/components/ui/StatusBadge.tsx`
  - `app/web/src/components/ui/EventCard.tsx`
  - `app/web/src/components/ui/MetricCard.tsx`
  - `app/web/src/components/ui/InsightCard.tsx`

### 산출물
- 공통 UI 컴포넌트 세트
- 사용 규칙 문서
- 화면별 컴포넌트 매핑표

### 의존성
- Product Lead의 scope 정의 필요

### 완료 기준
- Home / Manager / Reports / Orchestrator가 같은 제품처럼 느껴지는 공통 문법 확보

---

## 5.3 Home / Discovery Frontend Engineer

### 이 역할의 책임
- Home을 FolioObs식 discovery hub로 업그레이드
- 현재 Home의 상태판 성격을 유지하면서도 “다음으로 무엇을 탐색해야 하는지”를 더 잘 제시

### 이 역할이 해결해야 할 핵심 문제
현재 `Home.tsx`는:
- action hero
- metric cards
- manager hub
- recent activity
- inbox preview
구조는 좋지만, 아직 **탐색을 유발하는 block**이 부족합니다.

### 목표 결과
Home이 다음 질문에 답해야 합니다.
- 오늘 가장 중요한 변화는?
- 어떤 manager에 지금 들어가야 하나?
- 어떤 종목/자산/리스크가 새롭게 떠올랐나?
- 어떤 질문을 Orchestrator에게 던져야 하나?

### 작업 목록
1. Hero 개선
   - 현재 action hero를 유지하되, 보조 CTA 추가
   - 예: “가장 위험한 이슈 보기”, “후보 종목 보기”, “Manager 비교 보기”
2. Event stream block 추가
   - 기존 `event_timeline`을 카드형 이벤트 피드로 재구성
   - 이벤트 타입별 시각 구분
3. Priority / Opportunity strip 추가
   - high priority manager
   - 최근 우선순위 상승 종목
   - 유동성/리스크 경고
4. manager hub 개선
   - 단순 card grid → “Open issues / last update / next action”이 더 잘 드러나도록 확장
5. inbox preview와 event stream 연결
   - 중복이 아니라 역할 분담이 되도록 재배치
6. Orchestrator prompt starter block 추가
   - quick prompts를 더 productized
   - 예: “오늘 무엇부터 해야 하나?”, “리스크가 가장 큰 자산군은?”, “새 후보 종목 요약”

### 주로 건드릴 파일
- `app/web/src/pages/Home.tsx`
- `app/web/src/components/ManagerCard.tsx`
- `app/web/src/components/OrchestratorPanel.tsx`
- 신규 제안:
  - `app/web/src/components/home/HomeHero.tsx`
  - `app/web/src/components/home/HomeEventFeed.tsx`
  - `app/web/src/components/home/HomePriorityStrip.tsx`
  - `app/web/src/components/home/HomePromptStarter.tsx`

### 필요한 데이터 계약
- event_timeline 세분화
- manager card metadata 확장
- opportunity / alert / stale reason 필드 추가 가능성

### 의존성
- Design Systems & UX Engineer
- Data Contracts Engineer

### 완료 기준
- Home에서 “상태 확인”을 넘어서 “다음 탐색 행동”이 자연스럽게 이어짐

---

## 5.4 Manager Workspace Frontend Engineer

### 이 역할의 책임
- 각 manager 화면을 단순 summary page가 아니라 실제 작업 공간(workbench)으로 전환
- 특히 `StockResearchManager`를 우선 개선해 FolioObs의 Screener + Detail + Insight 패턴에 대응

### 우선순위
1순위: `StockResearchManager`  
2순위: `CoreStrategyManager`  
3순위: `CashDebtManager`, `RealEstateManager`

### 작업 목록 — StockResearchManager
1. Watchlist 좌측 패널을 Screener-like list로 강화
   - 검색
   - 상태 필터
   - held / 후보 / 보류 필터
   - overlap/risk quick filter
2. item row density 개선
   - 현재 status / symbol / score 외에
   - 최근 판단, risk badge, overlap badge, next action preview 추가
3. detail panel 강화
   - macro / options / risk / overlap / memo / next action을 섹션형으로 재배치
4. top candidates block을 더욱 탐색형으로 변경
5. 상태 전이 UX 개선
   - 탐색 → 관찰 → 후보 → 보류 → 제외 흐름이 더 명확하게 보이게
6. future compare slot 확보
   - 종목 간 비교 또는 portfolio fit 비교를 넣을 수 있는 구조 미리 설계

### 작업 목록 — CoreStrategyManager
1. 목표 비중 vs 실제 비중 차이를 event화
2. 리밸런싱 필요 항목을 ranked task list로 노출
3. “왜 이 액션이 필요한가?” explanation card 추가
4. 리스크, 유동성, action hero와의 관계를 한 화면에서 보여주기

### 작업 목록 — CashDebtManager
1. 단순 현금 수치가 아니라 “현금 여력 상태 카드” 추가
2. 상환 일정, buffer, 투자 가능 여력을 구분
3. high/medium/low severity action list 구성

### 작업 목록 — RealEstateManager
1. 관심 단지 비교 카드 도입
2. 리스크/장점/다음 확인 액션을 checklist형으로 표현
3. 후보 단지 간 비교 가능 구조 확보

### 주로 건드릴 파일
- `app/web/src/pages/managers/StockResearchManager.tsx`
- `app/web/src/components/stock-research/*`
- `app/web/src/pages/managers/CoreStrategyManager.tsx`
- `app/web/src/pages/managers/CashDebtManager.tsx`
- `app/web/src/pages/managers/RealEstateManager.tsx`
- `app/web/src/pages/managers/ManagersLayout.tsx`

### 신규 제안 파일
- `app/web/src/components/stock-research/StockResearchFilters.tsx`
- `app/web/src/components/stock-research/StockResearchListItem.tsx`
- `app/web/src/components/managers/ManagerEventList.tsx`
- `app/web/src/components/managers/ActionQueueCard.tsx`
- `app/web/src/components/managers/ComparisonMiniPanel.tsx`

### 의존성
- Design Systems & UX Engineer
- Data Contracts Engineer
- Research & Insights Engineer

### 완료 기준
- manager 화면이 “보여주는 화면”이 아니라 “판단을 진행하는 화면”처럼 느껴짐

---

## 5.5 Data Contracts & Snapshot Backend Engineer

### 이 역할의 책임
- 프런트에서 쓸 discovery / event / insight / compare 데이터를 snapshot 계약으로 안정화
- 현재 `AppSnapshot`의 구조를 확장해 새로운 UI가 억지 계산 없이 그려질 수 있게 함

### 이 역할이 해결해야 할 핵심 문제
현재는 프런트가 일부 summary와 fixture를 바탕으로 화면을 조합합니다.  
FolioObs식 개선을 하려면, 프런트가 너무 많은 의미 계산을 하지 않도록 **백엔드/스냅샷 계약**이 더 좋아져야 합니다.

### 작업 목록
1. `AppSnapshot` 확장 제안
   - `home_discovery`
   - `manager_events`
   - `priority_actions`
   - `cross_manager_alerts`
   - `research_candidates`
   - `orchestrator_prompt_starters`
   - `report_highlights`
2. manager summary record 세분화
   - summary_text 외에
   - headline
   - reasoning bullets
   - stale reason
   - recommended actions typed array
3. event_timeline 표준화
   - category
   - severity
   - source_manager_id
   - entity_type (position / stock / cash / debt / property)
   - entity_id
4. compare data 계약 추가
   - manager vs manager 비교
   - holding overlap
   - conflicting recommendation
5. stock research fixture를 실제 snapshot 구조로 옮길 수 있게 schema 정의
6. contract tests 추가
   - snapshot JSON shape 보장
   - 필수 필드 누락 방지

### 주로 건드릴 파일
- `app/web/src/types/appSnapshot.ts`
- `app/contracts/*.json`
- `app/api/main.py`
- snapshot 생성 파이프라인 관련 Python 모듈
- 필요시 테스트:
  - `tests/contracts/*`
  - `tests/ai/*`

### 산출물
- 확장된 snapshot schema
- contract tests
- sample snapshot fixture

### 의존성
- Product Lead의 우선순위
- Home / Manager FE에서 필요한 필드 목록

### 완료 기준
- 프런트가 임시 계산/fixture에 덜 의존하고, 명확한 snapshot 계약 기반으로 렌더링 가능

---

## 5.6 Orchestrator / AI Interaction Engineer

### 이 역할의 책임
- 현재 `OrchestratorPanel`을 preview 위젯에서 실제 운영 질의 인터페이스로 업그레이드
- 사용자의 질문과 manager brief 간 연결을 더 정교하게 만들기

### 현재 상태 요약
- `buildPreviewReply()`는 rule/token 기반 intent classification + brief 조합을 수행함
- quick prompt와 session history는 이미 있음
- 하지만 답변은 아직 비교적 평면적이며, multi-manager orchestration이 약함

### 목표 결과
사용자가 Orchestrator에 물으면:
- 어떤 manager 관점인지
- 왜 그런 답이 나왔는지
- 다음 액션이 무엇인지
- 어느 화면으로 가야 하는지
가 더 명확히 보여야 합니다.

### 작업 목록
1. prompt starter 개선
   - Home과 OrchestratorPanel에서 일관된 prompt 추천
2. intent rule 체계 확장
   - 복합 질문(예: 리스크 + 현금 + 개별주)을 더 잘 분해
3. answer structure 개선
   - short answer
   - supporting managers
   - next action
   - go-to screen 링크
4. source transparency 강화
   - 어떤 manager brief가 사용됐는지 표시
   - stale data 여부 표시
5. question history UX 개선
   - replay
   - compare previous answers
   - frequent intents summary
6. orchestrator insights panel 추가
   - 가장 많이 물은 질문
   - 반복 intent
   - unresolved topic

### 주로 건드릴 파일
- `app/web/src/components/OrchestratorPanel.tsx`
- `app/web/src/lib/orchestratorPreview.js`
- `app/web/src/lib/orchestratorSession.js`
- `app/web/src/lib/orchestratorPreview.test.js`
- `app/web/src/lib/orchestratorSession.test.js`

### 신규 제안 파일
- `app/web/src/components/orchestrator/OrchestratorAnswerCard.tsx`
- `app/web/src/components/orchestrator/OrchestratorSourcePanel.tsx`
- `app/web/src/components/orchestrator/OrchestratorHistoryList.tsx`
- `app/web/src/components/orchestrator/OrchestratorPromptStarters.tsx`

### 의존성
- Data Contracts Engineer
- Home FE Engineer

### 완료 기준
- Orchestrator가 “그럴듯한 텍스트 출력”이 아니라 “실제 다음 행동을 연결하는 인터페이스”가 됨

---

## 5.7 Research & Insights Engineer

### 이 역할의 책임
- Reports / Insights / Narrative layer를 담당
- 현재 서비스에 부족한 “왜 중요한가” 레이어를 만들어 줌

### 왜 이 역할이 필요하나
현재 서비스는 운영 도구 성격은 있지만,
FolioObs처럼 **데이터를 해석 카드 / 보고서 문장 / 요약 이슈**로 재가공하는 층이 약합니다.

### 작업 목록
1. Reports 재설계
   - KPI 카드만이 아니라
   - 이번 주 핵심 변화
   - manager별 highlight
   - 리스크/기회 요약
   - 다음 액션 제안
2. insight card data model 정의
   - tag
   - title
   - explanation
   - confidence
   - source_manager_id
   - stale flag
3. Home/Manager/Reports에 재사용되는 narrative block 설계
4. stock research insight layer 강화
   - 현재 detail 내부의 macro/options/risk를 더 카드화
5. “cross-manager summary” 작성 로직 설계
   - 예: “현금 여력은 충분하지만 stock 후보가 과밀함”
6. report snapshot 데이터와 UI 연결

### 주로 건드릴 파일
- `app/web/src/pages/Reports.tsx`
- `app/web/src/pages/Research.tsx`
- `app/web/src/types/appSnapshot.ts`
- 필요시 신규 컴포넌트:
  - `app/web/src/components/reports/ReportHighlightCard.tsx`
  - `app/web/src/components/reports/ManagerNarrativeCard.tsx`
  - `app/web/src/components/reports/CrossManagerSummary.tsx`

### 의존성
- Data Contracts Engineer
- Design Systems & UX Engineer
- Orchestrator Engineer

### 완료 기준
- Reports가 숫자판이 아니라 “운영 리뷰 문서 화면”처럼 바뀜

---

## 5.8 QA / Verification Engineer

### 이 역할의 책임
- 이번 개선이 산발적 UI 변경으로 끝나지 않도록, 화면/상태/데이터 계약을 검증
- 사용자가 실제로 핵심 흐름을 수행할 수 있는지 보장

### 작업 목록
1. 핵심 사용자 시나리오 정의
   - Home 진입 → manager 클릭 → detail 편집 → inbox 확인 → report 확인
   - Orchestrator 질문 실행 → 답변 확인 → source 확인
   - StockResearch status 전이 → memo 수정 → next action 반영
2. UI regression checklist 작성
3. snapshot contract regression 추가
4. orchestrator intent regression 테스트 추가
5. visual smoke test 혹은 snapshot test 설계
6. mobile/desktop 반응형 체크리스트 작성

### 주로 건드릴 파일
- `app/web/src/lib/*.test.js`
- 프런트 테스트 추가 시:
  - `app/web/src/components/**/*.test.*`
  - `app/web/src/pages/**/*.test.*`
- Python contract tests:
  - `tests/contracts/*`

### 완료 기준
- 단순히 화면이 보이는 수준이 아니라, 핵심 운영 플로우가 유지된다는 증거 확보

---

## 5.9 Platform / Performance Engineer (선택)

### 이 역할이 필요한 경우
- snapshot이 커지고
- event/insight/compare 데이터가 늘고
- manager별 화면이 무거워질 때

### 작업 목록
1. 번들 분리 / 라우트 단위 lazy loading 검토
2. 큰 manager 화면의 렌더링 비용 측정
3. 차트/리스트 virtualization 필요성 평가
4. snapshot fetch 전략 개선
5. static export / cache invalidation 전략 정리

### 완료 기준
- 기능 추가 이후에도 Home/Managers/Research 성능 저하가 체감되지 않음

---

# 6. 추천 실행 순서

## Phase 1 — Home/Discovery 기반 만들기
담당:
- Product Lead
- Design Systems & UX Engineer
- Home FE Engineer
- Data Contracts Engineer
- QA Engineer

### 목표
Home을 “상태판”에서 “탐색 허브”로 전환

### 주요 결과
- Home hero 개선
- event feed 추가
- manager card 강화
- prompt starter 강화
- snapshot 계약 확장 1차

---

## Phase 2 — Manager Workspace 강화
담당:
- Manager Workspace FE Engineer
- Design Systems & UX Engineer
- Data Contracts Engineer
- QA Engineer

### 목표
StockResearchManager를 기준 모델로 삼아 manager 경험을 workbench화

### 주요 결과
- StockResearch filters/list/detail 고도화
- CoreStrategy action queue
- CashDebt severity blocks
- RealEstate compare shell

---

## Phase 3 — Orchestrator / Insights / Reports 연결
담당:
- Orchestrator Engineer
- Research & Insights Engineer
- Data Contracts Engineer
- QA Engineer

### 목표
질문-해석-리포트 루프를 닫기

### 주요 결과
- richer orchestrator answers
- insight cards
- reports narrative blocks
- cross-manager summary

---

# 7. 팀 간 의존성 맵

## 가장 먼저 필요한 것
- Product Lead의 범위 고정
- Design Systems의 공통 문법 초안
- Data Contracts의 snapshot 확장 초안

## Home FE가 막히는 조건
- event/priority 관련 데이터 계약 미정
- 공통 카드/헤더 스타일 미정

## Manager FE가 막히는 조건
- research item schema 미정
- 공통 UI primitives 미정

## Orchestrator가 막히는 조건
- source transparency와 next action contract 미정
- manager brief 확장 미정

## Reports/Insights가 막히는 조건
- insight data contract 미정
- cross-manager aggregation 정의 미정

---

# 8. 현실적인 팀 운영 방식 제안

## 스쿼드 분리 방식
### Squad A — Experience Surface
- Design Systems & UX Engineer
- Home FE Engineer
- Manager Workspace FE Engineer

### Squad B — Data & Intelligence
- Data Contracts Engineer
- Orchestrator Engineer
- Research & Insights Engineer

### Shared
- Product Lead
- QA Engineer

이렇게 나누면 A는 화면/상호작용, B는 데이터/해석 레이어를 맡아 병렬 진행할 수 있습니다.

---

# 9. 각 역할의 최종 산출물 요약

| 역할 | 최종 산출물 |
|---|---|
| Product / Delivery Lead | 우선순위/범위/릴리즈 계획 |
| Design Systems & UX Engineer | 공통 UI 문법, 카드/배지/헤더 컴포넌트 |
| Home / Discovery FE Engineer | Home 개선본, 탐색 허브 UX |
| Manager Workspace FE Engineer | StockResearch/CoreStrategy/CashDebt/RealEstate workbench 개선 |
| Data Contracts Engineer | 확장된 AppSnapshot 및 contract tests |
| Orchestrator Engineer | 개선된 질의 인터페이스와 source-aware reply 시스템 |
| Research & Insights Engineer | insight cards / report narrative / cross-manager summary |
| QA Engineer | 핵심 사용자 플로우 검증 체계 |
| Platform Engineer(선택) | 성능/캐시/번들 최적화 |

---

# 10. 결론

이 개선 프로젝트의 핵심은 “FolioObs처럼 보이게 만들기”가 아닙니다.

핵심은,
**우리 서비스 Alpha Wealth Desk를 더 강한 운영 시스템으로 만드는 것**입니다.

즉:
- Home은 더 강한 탐색 허브가 되어야 하고,
- Manager는 실제 작업 공간이 되어야 하며,
- Orchestrator는 질문 기반 운영 인터페이스가 되어야 하고,
- Reports는 숫자판이 아니라 운영 해석 레이어가 되어야 합니다.

그리고 이 변화는 한 명이 다 하는 것이 아니라,
각 역할이 자기 책임을 선명하게 가져갈 때 가장 잘 됩니다.

이 문서의 역할은 바로 그 책임 분리를 선명하게 만드는 것입니다.

---

# 11. 바로 실행 가능한 팀 킥오프 문장

팀 킥오프에서 이렇게 선언하면 됩니다.

> 이번 프로젝트의 목표는 Alpha Wealth Desk를 단순 상태 대시보드에서 자산관리 운영 시스템으로 끌어올리는 것이다. Home은 discovery hub가 되고, Manager는 workbench가 되며, Orchestrator는 action interface가 되고, Reports는 narrative layer가 된다. 각 엔지니어는 자기 화면이 아니라 자기 역할이 담당하는 사용자 여정을 책임진다.

