# TQQQ 전략 성과개선 실험 설계서 (Phase 2)

## 1) 목표/가드레일 (확정)
- 1순위 목표: **세후 CAGR 최대화**
- 리스크 가드레일: **MDD -50% 이내**
- 변경 범위: **기존 파라미터 튜닝 + 비중 규칙 일부 조정(B)**
- 금지: 신규 필터 추가(과최적화 우려로 제외)

## 2) 기준선 (고정)
- 신호엔진: `user_original_signal` (사용자 제공 원본 신호)
- 백테스트 엔진: 거래단위(현금/주식수) + 비용 + 세후(실현손익 연도과세)
- 구간: 2011-06-23 ~ 2026-01-30
- 비용: one-way 5bps
- 초기자본: 1억원

### Baseline Snapshot
- Pretax CAGR: 41.57%
- After-tax CAGR: 38.60%
- Tax drag: 2.97%p
- Pretax MDD: -40.47%

## 3) 접근안 (확정)
채택 접근: **파라미터 그리드 + 안정성 게이트**

### 3.1 탐색 대상
- `vol_threshold`
- `dist200_enter`, `dist200_exit`
- `slope_thr`, `dist_cap`, `vol_cap`
- overheat 4단계 진입/해제 레벨
- `tp10_trigger`, `tp10_cap`
- 단계별 비중값(90/80/10/5 계열 소폭 조정)

### 3.2 탐색 방식
- 1차 Coarse Grid(넓게)
- 상위 후보 10~20개 선별
- 2차 Fine Grid(좁게 재탐색)

### 3.3 유효성 제약
- 히스테리시스: `enter > exit`
- overheat 단계 단조성: 1 < 2 < 3 < 4
- 비중 단계 체계 유지(비중 단조성)

## 4) 채택 게이트
- 하드 게이트:
  - MDD < -50% → 탈락
  - OOS 유지율 < 70% → 탈락
- 최종 선택:
  - 게이트 통과군 중 After-tax CAGR 최대
  - 동률 시 MDD 우위 후보 선택

## 5) 검증/리포팅
- `experiments/trials.csv`: 전체 후보
- `experiments/passed_leaderboard.csv`: 게이트 통과군
- `experiments/best_config.json`: 최종 채택 1개 + 근거
- 기준선 대비 diff 자동 기록(무개선 시 baseline 유지 허용)

## 6) 비범위
- 신규 거시/레짐 필터 추가
- 브로커 자동주문
- TradingView 강제 의존 검증

