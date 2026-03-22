# Alpha Wealth Desk — Stock Research 섹션 FolioObs 반영 분석 보고서

작성일: 2026-03-21  
대상 화면: `StockResearchManager`  
목적: FolioObs에서 어떤 구조와 UX 원칙을 가져오려는지, 현재 구현 상태가 어디까지 와 있는지, 최종적으로 어떤 기능과 UI/UX를 갖게 만들고 싶은지 명확히 정리

---

# 1. 이 문서의 목적

이 문서는 단순히 “Stock Research 화면을 더 멋있게 만들자”는 문서가 아닙니다.

우리가 지금 하려는 것은:

- FolioObs의 **Screener / Compare / Insights** 구조에서 무엇을 가져올지 정의하고
- 현재 Alpha Wealth Desk의 `StockResearchManager`가 어디까지 와 있는지 점검하고
- 최종적으로 이 화면을 **단순 종목 목록 화면이 아니라 실제 판단(workbench) 화면**으로 만들기 위한 목표 상태를 고정하는 것입니다.

즉, 이 문서는 다음 질문에 답합니다.

1. FolioObs에서 Stock Research 쪽으로 가져오고 싶은 핵심은 무엇인가?
2. 현재 우리 구현은 어디까지 와 있는가?
3. 아직 무엇이 부족한가?
4. 최종적으로 어떤 기능과 UX를 갖게 만들고 싶은가?

---

# 2. 먼저 결론부터

Stock Research에서 FolioObs로부터 가져오려는 핵심은 “예쁜 테이블”이 아닙니다.

핵심은 아래 4가지입니다.

1. **탐색 가능한 Screener-like list**
2. **선택 즉시 깊이 들어가는 Detail panel**
3. **비교/겹침/충돌을 고려한 판단 흐름**
4. **데이터 → 판단 → 다음 액션**으로 이어지는 작업 공간 구조

즉, 목표는:

> `StockResearchManager`를  
> “후보 종목 몇 개 보여주는 페이지”에서  
> “관심종목을 탐색하고, 우선순위를 정하고, 포트폴리오 적합성을 판단하고, 다음 행동을 정리하는 workbench”  
> 로 바꾸는 것입니다.

---

# 3. FolioObs에서 가져오고 싶은 점

## 3.1 단순 리스트가 아니라 Screener-like 탐색 도구라는 점

FolioObs의 Screener는 단순 종목 표가 아닙니다.

사용자는 Screener에서:
- 검색하고
- 상태를 필터링하고
- 최근 변화(New/Buy/Sell)를 보고
- 누가 들고 있는지 보고
- 어떤 종목을 더 깊게 볼지 결정합니다.

이 구조의 핵심은
**“목록 자체가 판단 도구”**라는 점입니다.

우리가 Stock Research에서 가져오려는 것도 यही입니다.

즉:
- watchlist는 단순 저장함이 아니라
- “무엇을 먼저 볼지 결정하는 작업 공간”이어야 합니다.

---

## 3.2 목록과 상세가 끊기지 않는 구조

FolioObs는 목록을 보고 끝나는 서비스가 아닙니다.

목록에서:
- 흥미를 느끼고
- 바로 상세로 들어가고
- 관련 정보를 읽고
- 비교하거나 해석으로 넘어갑니다.

이 흐름은 매우 중요합니다.

우리도 `StockResearchManager`에서
다음 흐름이 생겨야 합니다:

1. 후보를 훑어봄
2. 하나를 선택함
3. 상세 근거를 읽음
4. overlap / risk / fit을 판단함
5. memo와 next action을 남김

즉,
**List → Detail → Action**
흐름이 끊기지 않아야 합니다.

---

## 3.3 비교/겹침을 노출하는 관계형 UX

FolioObs가 강한 이유 중 하나는
단일 종목만이 아니라 **관계**를 보여주기 때문입니다.

예:
- 누가 같이 들고 있는지
- 어떤 포트폴리오와 겹치는지
- 어떤 시그널이 충돌하는지

Stock Research에서 우리가 가져오려는 것도 이 점입니다.

현재 우리 맥락으로 번역하면:
- 이 종목이 현재 포트폴리오와 얼마나 겹치는가?
- 섹터 중복이 있는가?
- 이미 보유한 종목과 성격이 겹치는가?
- 포트폴리오 적합도는 어떤가?

즉,
좋은 종목인지 여부만이 아니라
**우리 포트폴리오에 지금 넣는 것이 맞는지**
를 판단하게 해야 합니다.

---

## 3.4 AI / Insight 레이어의 역할

FolioObs는 raw data만 주지 않고
인사이트 카드, 요약, 해석 레이어를 제공합니다.

우리도 Stock Research에서
다음 정도는 필요합니다:

- 이 종목이 왜 후보인지
- 왜 보류인지
- 왜 축소 검토인지
- 어떤 리스크가 있는지
- 다음 액션이 무엇인지

즉, 숫자와 차트만으로 끝나는 것이 아니라
**판단 문장**이 필요합니다.

---

# 4. 현재 Stock Research의 상태

현재 `StockResearchManager`는 이미 꽤 중요한 기반을 갖고 있습니다.

## 4.1 현재 이미 있는 것

### A. Header
- top pick
- summary line
- warning line
- backend seed / next action

즉, 상단 요약 영역은 이미 존재합니다.

### B. Watchlist
- 점수순 정렬
- 상태 badge
- 보유 여부 표시
- 일부 risk/score driver 표시
- 상태 변경 가능

### C. Detail panel
- judgment
- priority score
- macro / options / risk
- chart
- memo
- next action
- overlap

### D. 필터
- 검색
- 상태 필터
- 보유 여부 필터

즉, 현재는 **“초기형 workbench”** 수준까지는 와 있습니다.

---

## 4.2 현재 상태를 한 문장으로 요약하면

현재 Stock Research는:

> “watchlist + detail panel이 있는 후보 검토 화면”

정도입니다.

이건 나쁜 상태가 아닙니다.
오히려 출발점으로는 꽤 좋습니다.

하지만 아직 FolioObs 수준의
**실무형 탐색 / 비교 / 판단 흐름**
까지는 가지 못했습니다.

---

# 5. 현재 부족한 점

## 5.1 Watchlist가 아직 완전한 Screener는 아님

지금도 검색/필터는 있지만,
아직 아래가 부족합니다.

- more screener-like sorting
- preset filter modes
- overlap/risk quick filters
- row 안에서 더 많은 판단 힌트

즉, 현재는 “좋은 리스트”이긴 하지만
아직 “강한 스크리너”는 아닙니다.

---

## 5.2 상태 전이 흐름이 충분히 드러나지 않음

현재 상태 값은 있습니다:

- 탐색
- 관찰
- 후보
- 보류
- 제외

하지만 이 상태들이
사용자에게 **하나의 파이프라인**처럼 느껴지진 않습니다.

즉:
- 어디서 어디로 이동하는지
- 왜 후보가 됐는지
- 왜 보류가 됐는지
- 다음에 무엇을 해야 하는지

가 더 선명해질 필요가 있습니다.

---

## 5.3 포트폴리오 fit / overlap 판단이 아직 보조적임

현재 overlap은 detail 하단에 일부 보입니다.
하지만 FolioObs식 관계형 UX를 생각하면,
이건 아직 너무 약합니다.

이상적인 상태는:
- 후보를 볼 때 바로
  - “좋은 종목”인지
  - “우리 포트폴리오에 지금 넣어도 되는 종목”인지
를 함께 느낄 수 있어야 합니다.

즉,
**quality와 fit이 동시에 보여야** 합니다.

---

## 5.4 compare slot이 아직 사실상 없음

계획서에서 이미 언급했듯,
future compare slot이 필요합니다.

왜냐하면 실제 판단은 자주 이렇게 일어나기 때문입니다.

- NVDA vs AMZN 중 무엇이 더 우선인가?
- AAPL을 유지할지 줄일지, META를 넣을지 비교해야 하지 않나?
- 이 종목이 기존 보유 종목보다 낫나?

현재는 compare가 아직 구조적으로 본격 지원되지 않습니다.

---

## 5.5 “다음 행동”은 있지만 “작업 큐” 느낌은 약함

현재 각 item에 next action은 있습니다.
하지만 화면 전체가
그 next action들을 관리하는 workbench처럼 느껴지진 않습니다.

즉,
종목 하나를 보는 것은 되지만
종목 여러 개를 놓고 **작업 우선순위를 운영하는 감각**은 아직 부족합니다.

---

# 6. 최종적으로 만들고 싶은 Stock Research

이제 목표 상태를 더 명확히 정의하겠습니다.

## 목표 문장

> `StockResearchManager`를  
> “관심종목을 보는 화면”에서  
> “후보 종목을 탐색하고, 포트폴리오 적합도를 비교하고, 상태를 전이시키며, 다음 행동을 관리하는 주식 리서치 workbench”  
> 로 완성한다.

---

# 7. 최종적으로 갖고 싶은 기능

## 7.1 왼쪽 Screener-like Watchlist

목표:
- 왼쪽 패널만 봐도 “무엇을 먼저 볼지” 정해져야 함

필수 기능:
- 검색
- 상태 필터
- 보유/미보유 필터
- overlap quick filter
- risk quick filter
- score 정렬
- 최근 판단 / next action 미리보기

즉, list 자체가 탐색 도구여야 합니다.

---

## 7.2 가운데/오른쪽 Detail Workbench

상세 패널은 단순 설명판이 아니라,
아래를 모두 포함한 판단 화면이 되어야 합니다.

필수 구성:
- 왜 이 종목을 보고 있는가
- 현재 judgment가 무엇인가
- 점수/quality/fit은 어떤가
- 차트 상 어떤 마커가 있는가
- 리스크는 무엇인가
- overlap은 무엇인가
- memo는 무엇인가
- next action은 무엇인가

즉,
**“읽고 끝나는 정보”**가 아니라
**“결론을 내릴 수 있는 정보 묶음”**이 되어야 합니다.

---

## 7.3 상태 전이 UX

최종적으로는 사용자가
다음 흐름을 명확히 체감해야 합니다.

- 탐색 → 관찰
- 관찰 → 후보
- 후보 → 보류
- 후보 → 제외
- 보유중 → 유지 / 축소 검토 / 추가매수 후보

중요한 것은 상태값 그 자체보다,
**왜 그 상태인지와 다음에 어디로 갈지**
가 보여야 한다는 점입니다.

---

## 7.4 Compare slot

최종적으로는 이 화면 안에
“두 종목을 비교할 수 있는 자리”가 있어야 합니다.

지금 당장 완전 구현이 아니라도,
구조적으로는 준비되어야 합니다.

예:
- `selected item` + `compare candidate`
- quality vs fit
- overlap risk 비교
- next action 비교

즉,
FolioObs의 Compare처럼
**관계를 기반으로 판단하는 흐름**을 준비해야 합니다.

---

## 7.5 Top candidates / action queue

최종적으로는 상단 summary가 단순 top pick 노출을 넘어서,
**오늘의 리서치 우선순위 큐**처럼 보여야 합니다.

예:
- top candidates 3개
- 보유중이지만 축소 검토 중인 종목
- overlap이 높은 후보
- next action overdue 항목

즉, top block이
“예쁜 헤더”가 아니라 **리서치 작업 큐 요약판**이 되어야 합니다.

---

# 8. 최종적으로 갖고 싶은 UI/UX

## 8.1 화면을 보는 순간 “탐색형 workbench”처럼 느껴져야 함

현재는 list + detail 구조입니다.
최종적으로는 여기에 더해

- screener
- detail
- action queue
- compare 준비

가 동시에 느껴져야 합니다.

즉, 사용자는
“종목 상세 페이지에 들어온 것”이 아니라
**“주식 리서치 작업대에 앉은 것”**
처럼 느껴야 합니다.

---

## 8.2 리스트에서 이미 판단 힌트가 보여야 함

좋은 UX는 상세로 들어가기 전에도
“왜 이걸 봐야 하는지”가 보입니다.

그래서 row 단계에서 최소한 다음이 드러나야 합니다.

- 상태
- score
- 핵심 risk
- overlap 힌트
- next action

즉, 상세는 “확인”이고,
list는 이미 “1차 판단”이 가능해야 합니다.

---

## 8.3 상세 패널은 ‘정보 박스’가 아니라 ‘판단 콘솔’이어야 함

상세 패널의 목표는 많은 정보를 보여주는 것이 아닙니다.

목표는:
- 사용자가 이 종목을
  - 올릴지
  - 유지할지
  - 미룰지
  - 제외할지
결정하게 돕는 것입니다.

즉,
**데이터 → 해석 → 기록 → 다음 행동**
의 흐름이 한 화면에서 이어져야 합니다.

---

## 8.4 리서치와 포트폴리오가 연결되어야 함

Stock Research는 단순한 종목 연구가 아니라,
**우리 포트폴리오 안에서 이 종목을 어떻게 다룰지**
를 판단하는 화면이어야 합니다.

따라서 최종 UX는:
- 좋은 종목 발견
가 아니라
- 지금 우리 포트폴리오에 적합한 종목 판단
이어야 합니다.

이게 FolioObs의 관계형 접근에서 우리가 가져오려는 가장 중요한 점 중 하나입니다.

---

# 9. 단계별 로드맵 제안

## Stage 1 — 이미 일부 진행됨
- list + detail 구조
- 기본 필터
- memo / next action
- overlap / risk / chart

## Stage 2 — 다음 목표
- screener-like list 강화
- row density 강화
- 상태 전이 UX 선명화
- top candidate/action queue 강화

## Stage 3 — 이후 목표
- compare slot 도입
- portfolio fit 비교 강화
- 더 강한 action queue / insight 연결

---

# 10. 한 줄 정리

Stock Research에서 FolioObs로부터 가져오려는 핵심은  
**“종목을 예쁘게 나열하는 방식”이 아니라, 후보를 탐색하고 비교하고 포트폴리오 적합도를 판단하고 다음 액션을 정리하는 workbench 구조”**입니다.

현재는 그 workbench의 초기형까지는 와 있고,  
최종 목표는 `Screener + Detail + Insight + Compare 준비`가 한 화면 안에서 이어지는 **진짜 리서치 작업 공간**을 만드는 것입니다.
