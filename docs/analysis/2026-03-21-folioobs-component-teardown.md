# FolioObs 컴포넌트 단위 해부 분석

작성일: 2026-03-21  
대상: https://folioobs.com  
목적: FolioObs를 페이지 단위가 아니라 **레이아웃 / 컴포넌트 / 상태 / 상호작용 / 시각 언어** 단위로 분해해서 재조립 가능한 수준으로 분석

---

## 0. 이 문서의 관점

이 문서는 “사이트가 좋아 보인다” 수준이 아니라,
**무엇이 어떤 역할을 하며, 어떤 컴포넌트가 어떤 사용자 심리를 담당하는가**를 해부하는 문서입니다.

즉, 아래 질문에 답합니다.
- 어떤 레이아웃 셸 위에 제품이 올라가 있는가?
- 어떤 카드/테이블/배지가 핵심 경험을 만든다?
- 왜 이 컴포넌트들이 ‘투자자 추적 제품’처럼 느껴지게 하는가?
- 무엇을 벤치마킹해야 하고, 무엇은 그대로 따라 하면 안 되는가?

---

# 1. 전체 시스템을 이루는 5개 층

FolioObs는 사실상 아래 5개 층으로 구성됩니다.

## Layer 1. App Shell
- 상단 글로벌 네비게이션
- 언어 전환
- 테마 전환
- 전역 검색(Command Palette)
- 푸터 / 법적 안내

## Layer 2. Discovery Surface
- Hero
- KPI strip
- hot stocks
- most bought / sold
- recent changes
- screener table

## Layer 3. Relationship Surface
- compare table
- overlap heatmap
- common holdings
- conflicting trades
- sector/style charts

## Layer 4. Interpretation Surface
- AI insight cards
- summary blocks
- news cards
- guide articles

## Layer 5. Personalization Surface
- watchlist
- add-to-watchlist 버튼
- foliomatch CTA
- command palette 기반 빠른 개인 탐색

이 구조가 중요한 이유는, 사이트가 예쁜 것이 아니라
**“발견 → 비교 → 해석 → 개인화”로 이어지는 제품 루프**를 컴포넌트 수준에서 완성하고 있기 때문입니다.

---

# 2. App Shell 해부

## 2.1 상단 네비게이션 바

### 구성
- 좌측: 로고/Home
- 중앙: 7개 주 탭
- 우측: ⌘K, 언어, 테마

### 역할
이 컴포넌트는 단순 메뉴가 아니라, 제품의 IA를 요약하는 **제품 문장**입니다.

탭 구성만 보면 사용자 머릿속에 다음 맵이 생깁니다.
- 대시보드: 전체 상황 보기
- 스크리너: 종목 찾기
- 내부자거래: 더 빠른 신호 보기
- 워치리스트: 내 관심 모으기
- 비교: 투자자 대 투자자
- 인사이트: AI 해석 보기
- 뉴스: 콘텐츠 읽기

### 디자인 특징
- 탭 구조가 빽빽하지만 명료함
- selected state가 명확함
- dark theme에서 작은 icon/text controls가 금융 도구 감성을 강화함

### 컴포넌트 평가
**이 네비는 “웹사이트 메뉴”보다 “분석 도구 모듈 스위처”에 가깝습니다.**

---

## 2.2 언어 전환 토글

### 관찰 포인트
- EN/KO 토글이 실제 운영 기능으로 깊게 반영됨
- 라벨, 본문, footer, tab 명칭까지 상당 폭 전환됨
- 모바일에서는 탭 명칭도 더 짧게 바뀜
  - 예: 대시보드 → 홈, 스크리너 → 종목, 워치리스트 → 관심, 인사이트 → 분석

### 의미
이건 단순 localization이 아니라 **UI density optimization**입니다.
즉, 번역만 한 것이 아니라 공간 제약에 맞게 정보 구조를 다시 조정합니다.

### 벤치마킹 포인트
- 번역 이전에 “화면 폭에 맞는 단어 길이 전략”을 세워야 함
- 한국어 제품에서 보기 드문, 꽤 잘된 bilingual component 전략

---

## 2.3 테마 토글

### 관찰 포인트
- 다크/라이트 전환이 있음
- 다크 모드가 브랜드 중심
- 라이트는 보조 옵션처럼 작동

### 해석
많은 서비스가 라이트를 기본으로 하고 다크를 옵션으로 두는데,
FolioObs는 반대로 **정체성은 다크, 접근성은 라이트**에 가깝습니다.

### 컴포넌트 레벨 의미
- 브랜드 무드는 다크에서 완성됨
- 라이트 모드는 사용성 확장 장치

---

## 2.4 Footer

### 구성
- Privacy Policy / Terms
- “투자 권유 아님” 디스클레이머
- 회사명 / 대표 / 사업자번호 / 이메일

### 역할
투자/금융 카테고리의 제품에서 푸터는 단순 마감 요소가 아니라 **신뢰 장치**입니다.

### 좋은 점
- 과장하지 않고 명확함
- 로컬 사업자 정보가 들어가 있어 제품 실체감이 생김

---

# 3. Dashboard 컴포넌트 해부

대시보드는 FolioObs의 컴포넌트 박물관입니다.
핵심 컴포넌트 대부분이 여기서 처음 등장합니다.

## 3.1 Hero Banner

### 구성 요소
- social proof 텍스트: “워렌 버핏 · 레이 달리오 · 캐시 우드…”
- 강한 headline
- 신뢰 배지: 실시간 / 무료 / 매일 업데이트 / 분기 표시
- aggregate stats: 총 AUM / 추적 종목 / 추적 투자자
- 대표 이벤트 버튼 2개
- hot stock mini-cluster
- daily-trade 요약 카드
- foliomatch CTA
- 포트폴리오 보기 CTA

### 역할 분해
이 Hero는 단일 영웅 배너가 아니라 **복합 onboarding surface**입니다.

#### 역할 A: 제품 정의
“지금 무엇을 사고팔고 있을까?”
- 질문형 헤드라인으로 사용자 호기심을 즉시 자극

#### 역할 B: 신뢰 형성
- AUM, 종목 수, 투자자 수
- Q4 '25 같은 최신 분기 표기
- 무료 / 매일 업데이트 같은 약속

#### 역할 C: 구체 사례 제시
- Chase Coleman NFLX +1108%
- George Soros V -97%
이런 예시는 추상 서비스 설명보다 훨씬 강합니다.

#### 역할 D: 개인화 예고
- FolioMatch
- Analyze my stocks

### 구조적 포인트
이 Hero는 랜딩 페이지 문법을 갖고 있지만,
실제로는 **요약 대시보드 + CTA 허브 + 예시 콘텐츠 묶음**입니다.

### 왜 인상적인가
보통 Hero는 말만 하고 끝나는데,
FolioObs Hero는 **이미 “서비스 일부를 써 본 느낌”**을 줍니다.

---

## 3.2 KPI / Trust Strip

### 구성
- 총 운용자산
- 추적 종목 수
- 추적 투자자 수
- 데이터 배지

### 역할
- 크레딧 부여
- 제품의 데이터 스케일 전달
- “아마추어 개인 프로젝트” 느낌 제거

### 디자인 포인트
- 숫자는 크지 않지만 문맥상 강함
- 메인 헤드라인 아래에 배치되어 제품 가치의 증거처럼 작동

---

## 3.3 Event Buttons / Signal Chips

### 예시
- 특정 투자자의 급격한 매수/매도 버튼
- hot stocks mini-card
- new buy / sell / overlap 태그

### 컴포넌트 정체
이건 카드와 배지의 중간 형태입니다.

### 역할
- 데이터 탐색을 “이벤트 기반”으로 바꿈
- 사용자가 어디를 먼저 볼지 결정해 줌
- 복잡한 데이터셋을 **행동 단위 스토리**로 압축

### 벤치마킹 포인트
정적인 “상위 10종목”보다,
**의미가 있는 사건 단위 인터페이스**가 훨씬 클릭을 유도합니다.

---

## 3.4 FolioMatch CTA Card

### 구성
- product name badge
- 설명 문장
- 예시 입력 placeholder
- 예시 결과 토큰
- 겹치는 투자자 아바타/약자 묶음
- CTA 문장

### 역할
이 카드는 단순 CTA가 아니라 **미리보기형 가치 시연 카드**입니다.

### 좋은 점
- CTA 전에 사용자가 “얻을 결과”를 미리 체험함
- 입력 기반 기능이지만 빈 입력칸만 보여주지 않음
- 개인화 기능을 두려워하지 않게 만듦

### 벤치마킹 포인트
사용자 입력이 필요한 기능은 빈 폼보다
**예시 결과를 먼저 보여주는 card demo**가 훨씬 강함

---

## 3.5 Section Header Pattern

FolioObs의 거의 모든 섹션은 공통된 헤더 패턴을 씁니다.

### 패턴
- 좌측 아이콘
- 섹션 제목
- 보조 라벨(분기, daily update, latest 등)

### 역할
- 긴 페이지에서 섹션 전환점을 명확히 함
- 데이터 블록들의 의미를 빠르게 분절
- 시각적 리듬 형성

### 왜 중요한가
데이터가 많은 화면은 제목만으로는 부족합니다.
아이콘 + 시점(label) 조합이 있어야 사용자가 정보 성격을 즉시 구분합니다.

---

# 4. Discovery 컴포넌트 해부

## 4.1 Investor Filter Chips

### 등장 위치
- Dashboard
- Screener
- Compare 등

### 형태
- 이름 + 약자
- 누르면 active filter가 되는 button chip

### 역할
- 복잡한 투자자 세계를 **직접 조작 가능한 태그 세트**로 바꿈
- 사용자가 제품 도메인을 빠르게 학습하게 함

### 장점
- 반복 노출로 학습 비용이 낮아짐
- initials가 mini brand처럼 작동
- dense data에서도 식별성이 높음

### 설계 핵심
이 제품은 사람 이름 전체보다 **약자 체계(WB, RD, CW…)**가 UI의 축입니다.
이게 매우 중요합니다.

---

## 4.2 Filter Bar

### 구성 예시
- 검색창
- sector combobox
- 상태 토글
- holders count filter
- sort button

### 역할
스크리너나 대시보드의 데이터를 “그냥 나열”하지 않고
**즉시 조작 가능한 작업대(workbench)**로 만듭니다.

### 좋은 점
- 필터 종류가 의미별로 잘 분리됨
  - 텍스트 검색
  - 카테고리 필터
  - 상태 필터
  - 정렬
- 대부분 한 줄에서 해결되어 조작성이 좋음

### 잠재 리스크
- 옵션이 더 늘어나면 압도감이 급증할 구조
- 저장된 필터/초기화/현재 상태 표시가 중요해질 수 있음

---

## 4.3 Ranking List / Top List Card

### 예시
- Holdings Performance ranking
- Most Bought TOP 5
- Most Sold TOP 5

### 공통 구조
- rank number
- ticker + name
- who holds/bought/sold
- 보조 수치(수익률, agree count 등)

### 역할
- 원시 데이터에서 “바로 볼 가치가 있는 목록”을 추출
- 페이지 탐색 시작점을 제공

### 설계 포인트
이 컴포넌트는 **스캔 최적화**가 강합니다.
사용자는 상위 몇 줄만 봐도 현재 분위기를 읽을 수 있습니다.

---

## 4.4 Table Row Anatomy (스크리너 핵심)

스크리너 테이블의 row는 사실 하나의 작은 분석 카드입니다.

### 한 row 안에 담긴 것
- watchlist action
- ticker / 회사명
- 가격 / filing 이후 변화
- sector
- holders avatars/buttons
- max weight
- total value
- recent change tags

### 이 row가 좋은 이유
일반 테이블은 column만 나열하지만,
FolioObs row는 **행 자체가 클릭 가능한 요약 인터페이스**입니다.

### row 설계 핵심
- 숫자만 있지 않고 의미 레이어가 있음
- “누가 들고 있는지”가 시각적으로 핵심 위치에 있음
- change tags가 행동 해석을 바로 붙여줌

### 벤치마킹 포인트
데이터 테이블을 설계할 때,
**컬럼 정확성**만 신경 쓰면 boring해지고,
**행의 이야기성**까지 넣으면 훨씬 강해집니다.

---

## 4.5 Empty State (Watchlist)

### 구성
- 아이콘
- 한 줄 설명
- 어디서 추가하는지 안내

### 역할
- 기능 부재가 아니라 “다음 행동 유도 상태”로 전환

### 좋은 점
- empty를 dead-end로 두지 않음
- 사용자가 어떤 다른 페이지로 돌아가야 하는지 자연스럽게 학습함

---

# 5. Relationship 컴포넌트 해부

## 5.1 Overlap Heatmap

### 정체
FolioObs 전체에서 가장 강력한 “관계형 컴포넌트”입니다.

### 구성
- 투자자 축
- 숫자 셀
- 겹치는 종목 수
- 색/강도 차이

### 역할
- 투자자 간 관계를 한눈에 보여줌
- 단일 데이터셋을 네트워크처럼 느끼게 함
- “누가 누구와 닮았는가”를 계산 이전에 체감하게 함

### UX 가치
이 컴포넌트는 사용자에게 **탐색 질문**을 만들어 줍니다.
- 왜 Buffett와 Dalio가 이렇게 많이 겹치지?
- 왜 Cathie와 특정 매니저는 거의 안 겹치지?

### 아주 중요한 점
Heatmap은 예쁜 시각화가 아니라,
**비교 기능으로 이동시키는 질문 생성 장치**입니다.

---

## 5.2 Compare Metrics Table

### 구성
- AUM
- holdings
- concentration
- top weight
- QoQ change
- style 등

### 역할
정성적 비교 전에 **기본 체급 차이**를 먼저 보여줍니다.

### 장점
- 사용자가 인물 캐릭터를 빠르게 이해함
- “Buffett vs Druckenmiller”가 숫자로 먼저 대비됨

---

## 5.3 Common Holdings / Conflicting Trades

### 정체
이건 Compare 페이지에서 가장 서사적인 부분입니다.

### 공통 보유 컴포넌트
- 어떤 종목을 둘 다 들고 있는가?
- 비중은 얼마나 다른가?
- 최근 변화 방향은 어떠한가?

### 충돌 시그널 컴포넌트
- 한 명은 줄이고, 다른 한 명은 늘린 종목
- 즉시 “관점 차이”를 드러냄

### UX 의미
사용자는 숫자를 보는 게 아니라,
**투자 철학의 충돌**을 보게 됩니다.

---

## 5.4 Radar / Allocation Charts

### 역할
- 숫자 테이블이 설명하지 못하는 “형태 차이”를 시각화
- style, focus, diversity, volatility 등 정체성을 보조 설명

### 장점
- 복잡한 비교를 빠르게 감각화
- 테이블과 차트가 역할 분담을 잘 함

### 주의점
이런 차트는 예쁘지만,
정의가 불명확하면 장식으로 보일 위험이 있음

---

# 6. Interpretation 컴포넌트 해부

## 6.1 AI Insight Card

이 사이트의 핵심 차별 컴포넌트입니다.

### 카드 구조
- tag (Strategy / Increase / Trend / Risk / Macro ...)
- AI badge
- confidence
- 짧고 강한 제목
- 2~4문장 설명
- 확장/상세 보기 affordance

### 역할
원시 데이터의 의미를 사용자가 읽을 수 있는 문장으로 변환

### 왜 강한가
- 표보다 읽기 쉽다
- 기사보다 짧다
- 트윗보다 밀도 높다

### 심리적 효과
사용자는 “내가 분석했다”기보다
**“전문가 메모를 빠르게 훑는다”**는 느낌을 받습니다.

### 설계 핵심
좋은 insight card는 요약이 아니라 **논지(argument)**를 가져야 합니다.
FolioObs는 대체로 그 점을 잘 지킵니다.

---

## 6.2 Confidence Badge

### 역할
- AI 해석의 강도를 정량으로 표현
- 사용자가 카드를 가볍게 소비하면서도 신뢰도를 체감하게 함

### 위험
confidence가 너무 남발되면 오히려 “모든 게 비슷해 보이는 숫자”가 됩니다.
그래서 근거나 원문 연결이 더 중요해집니다.

---

## 6.3 News Card

### 구조
- 카테고리
- 날짜
- 읽기 시간
- 제목
- 요약
- 관련 티커
- 썸네일

### 역할
Insights가 분석 메모라면,
News는 **에디토리얼 패키징**입니다.

### 좋은 점
- 같은 데이터를 다른 소비 방식으로 재활용
- 재방문성을 높임
- 검색 유입/콘텐츠 유입 가능성을 만듦

### 디자인 포인트
- FOLIOBS TERMINAL 헤더와 ticker tape가 이 레이어의 톤을 크게 강화함

---

## 6.4 Guide Card

### 역할
- 초보자 흡수
- SEO / 교육 콘텐츠 역할
- 제품에 대한 진입 장벽 완화

### 의미
이 제품은 전문가만 위한 도구가 아니라,
**새로운 사용자를 스스로 교육하는 구조**도 함께 가져갑니다.

---

# 7. Personalization 컴포넌트 해부

## 7.1 Watchlist Heart Action

### 등장 위치
- investor card
- screener row
- 기타 리스트 아이템

### 역할
개인화로 가는 가장 작은 진입점

### 좋은 점
- 거대한 가입 플로우 없이 “내 것 만들기”를 시작시킴
- passive browsing을 active collection으로 바꿈

---

## 7.2 Command Palette

### 구조
- 검색창
- hot stocks preset
- popular investors preset
- 키보드 힌트

### 역할
- 빠른 이동
- 검색
- 추천 entry point 제공

### 왜 중요한가
정보량이 많은 사이트는 종종 “검색창 하나”로 끝내는데,
FolioObs는 command palette를 **mini dashboard**처럼 씁니다.

### 벤치마킹 포인트
전역 검색은 단순 검색보다,
**추천/최근/핫 항목이 붙을 때** 훨씬 제품답습니다.

---

# 8. 시각 언어를 만드는 원자들

## 8.1 Investor Initials System
- WB, CW, SD, RD, BA, GS...
- 이 약자들이 사실상 브랜드 자산처럼 반복 사용됨

### 효과
- 화면이 복잡해도 빠르게 인식 가능
- 사람 이름을 시각 토큰으로 압축
- 관계형 분석 화면에서 공간 효율 극대화

## 8.2 Badge / Chip Language
- New
- Buy
- Sell
- Latest
- Daily
- AI
- Risk
- Trend
- 속보 / 분석 / 가이드

### 효과
- 콘텐츠/데이터 성격을 초단위로 구분
- 작은 텍스트가 정보구조를 대신함

## 8.3 Icon-assisted Headers
- 거의 모든 섹션이 아이콘+제목 구조
- dense layout에서 섹션 인지를 크게 돕는다

## 8.4 숫자의 계층 구조
- headline number
- support number
- delta number
- rank number
이 4개가 섞여 쓰이는데, 역할이 대체로 잘 분리됨

---

# 9. 상태(State) 설계 분석

FolioObs는 상태 표현이 꽤 좋은 편입니다.

## 주요 상태
- loading
- selected tab
- active filter
- empty watchlist
- latest/current badge
- rank/order state
- buy/sell/new semantic state
- language state
- theme state

### 좋은 점
- 사용자가 “지금 어떤 모드인지” 비교적 잘 알 수 있음
- 상태가 텍스트, 색, 배지, 정렬 라벨로 중복 표현됨

### 특히 좋은 상태
- empty state의 안내성
- latest / daily / quarter 시점 표시
- table/filter의 active affordance

---

# 10. 반응형(Responsive) 해부

Playwright로 확인한 모바일 특성:
- 상단 탭명이 짧아짐
- 로고 텍스트는 축약되고 icon 중심이 됨
- 동일 기능을 유지하면서 label density를 줄임
- 전체 구조는 꽤 잘 보존됨

### 해석
이 사이트는 모바일에서 완전히 다른 앱이 되기보다,
**동일한 정보 구조를 압축해서 유지**하는 전략입니다.

### 장점
- 멘탈 모델이 유지됨
- 데스크탑에서 본 정보를 모바일에서도 이어서 인지 가능

### 리스크
- 데이터 밀도 자체는 여전히 높아서,
  모바일에서 일부 섹션은 상당히 길고 무겁게 느껴질 수 있음

---

# 11. 기술적 구현을 시사하는 컴포넌트 단서

네트워크와 렌더링 관찰 기준:
- SPA 탭 이동 구조
- Vite 기반 번들 정황
- Supabase REST 호출 다수
- live-prices 서버 함수 호출
- Polygon 기반 참조/브랜딩 호출
- GA page_view / scroll 이벤트

### 컴포넌트 관점에서의 함의
1. 차트/테이블/카드가 모두 **클라이언트 조합형 UI**일 가능성이 큼
2. 데이터 양이 많아질수록:
   - pagination
   - 캐싱
   - prefetch
   - skeleton/loading state
   - bundle splitting
   이 중요해질 구조

### 특히 눈에 띄는 점
- Ray Dalio 같은 대규모 포트폴리오는 holding_changes offset 호출이 매우 많음
- 즉, 일부 컴포넌트는 데이터 스케일 차이의 영향을 크게 받을 수 있음

---

# 12. 재조립 가능한 컴포넌트 목록

FolioObs를 참고해 다른 제품을 만든다면, 아래처럼 재사용 가능한 블록으로 생각할 수 있습니다.

## Core Shell
- GlobalNav
- CommandPalette
- LocaleToggle
- ThemeToggle
- TrustFooter

## Dashboard Blocks
- HeroStoryBanner
- KPITrustStrip
- InvestorEventButtons
- HotStocksCluster
- PersonalizedInputCTA
- SectionHeader

## Data Discovery Blocks
- InvestorChipGroup
- FilterWorkbench
- DenseDataTable
- RankedStockList
- ChangeTagGroup
- EmptyState

## Relationship Blocks
- OverlapHeatmap
- CompareMetricsTable
- CommonHoldingsTable
- ConflictSignalCard
- StyleRadarChart
- SectorAllocationChart

## Interpretation Blocks
- InsightCard
- ConfidenceBadge
- EditorialNewsCard
- GuideCard
- CategoryFilterTabs

## Personalization Blocks
- WatchlistAction
- Stock/Investor Quick Add
- MyPortfolio Match CTA

이 식으로 보면, FolioObs의 강점은 특정 한 카드가 아니라
**이 블록들이 하나의 논리로 연결된다는 점**입니다.

---

# 13. 정말 배워야 할 것 / 표면만 따라 하면 안 되는 것

## 진짜 배워야 할 것
1. **도메인 개념을 UI 토큰으로 압축하는 법**
   - initials, badges, tags
2. **raw data를 event / comparison / narrative로 재포장하는 법**
3. **첫 화면부터 가치 시연을 하는 hero 설계**
4. **도구형 페이지와 콘텐츠형 페이지를 한 제품으로 묶는 법**
5. **다국어와 반응형에서 label density를 조절하는 법**

## 겉모습만 따라 하면 위험한 것
1. 다크 테마만 베끼기
2. 숫자/카드만 많이 쌓기
3. AI 카드만 추가하기
4. heatmap/chart를 장식처럼 넣기

FolioObs는 ‘멋진 금융 UI’라서 좋은 게 아니라,
**각 컴포넌트의 역할이 아주 분명해서** 좋습니다.

---

# 14. 가장 중요한 통찰

FolioObs를 컴포넌트 단위로 해부해 보면, 결국 이 사이트는 아래 구조를 가집니다.

- 상단 셸이 제품의 사고방식을 설명하고
- 대시보드 컴포넌트가 사용자의 호기심을 자극하고
- 스크리너/비교 컴포넌트가 사용자의 탐색 욕구를 충족시키고
- 인사이트/뉴스 컴포넌트가 해석과 체류를 만들어내고
- 워치리스트/커맨드 팔레트가 개인화를 준비시킵니다.

즉, 좋은 컴포넌트가 많은 것이 아니라,
**컴포넌트들이 모두 같은 사용자 여정을 향해 작동**합니다.

이게 이 사이트의 진짜 완성도입니다.

---

# 15. 한눈에 보는 컴포넌트 평가표

| 컴포넌트 | 역할 | 강점 | 주의점 |
|---|---|---|---|
| Global Nav | 제품 구조 설명 | IA가 명확함 | 탭 수가 많아지면 과밀 위험 |
| Hero Banner | 가치 시연 + CTA | 제품 일부를 즉시 체험시킴 | 정보량 과다 가능 |
| KPI Strip | 신뢰 형성 | 스케일 전달 | 너무 많아지면 장식화 |
| Event Buttons | 사건 단위 탐색 유도 | 클릭 유도 강함 | 이벤트 품질 관리 필요 |
| Screener Table | 실무 탐색 | row 자체가 스토리 | 모바일 피로도 |
| Investor Chips | 필터/학습 | 학습 비용 낮춤 | 수가 늘면 복잡해짐 |
| Overlap Heatmap | 관계 탐색 | 질문을 만들어냄 | 정의 불명확 시 장식화 |
| Compare Tables/Charts | 상대 비교 | 숫자+시각화 균형 | 과도하면 인지 부하 |
| Insight Card | 데이터 의미화 | 읽기 쉽고 밀도 높음 | AI 신뢰성 관리 중요 |
| News Card | 콘텐츠 소비 | 재방문/브랜드 강화 | 운영 리소스 필요 |
| Watchlist Empty State | 개인화 유도 | dead-end 방지 | 추천 seed 없으면 약함 |
| Command Palette | 전역 탐색 | 파워유저 만족도 높음 | 추천 품질 중요 |

---

# 16. 결론

FolioObs를 잘게 쪼개 보면, 이 사이트는 “카드가 예쁜 제품”이 아니라
**도메인 개념을 컴포넌트로 번역하는 능력이 매우 좋은 제품**입니다.

- 투자자는 initials가 되고
- 공시는 event chip이 되고
- 포트폴리오는 비교 테이블과 heatmap이 되고
- 해석은 AI card가 되고
- 이야기는 news card가 됩니다.

이 변환이 자연스럽기 때문에,
사용자는 데이터베이스를 보는 느낌이 아니라
**살아 있는 투자 관찰 도구**를 쓰는 느낌을 받습니다.

그래서 진짜 배울 포인트는 디자인 취향이 아니라,
**도메인 구조를 UI 구조로 압축하는 방식**입니다.
