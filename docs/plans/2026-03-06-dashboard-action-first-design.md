# Action-First Dashboard MVP Design (2026-03-06)

## 1. 목표
텔레그램 알림과 동일한 의사결정 철학으로, 대시보드 첫 화면에서
1) 오늘 액션 판단(A)
2) 성과/리스크 건강도(B)
를 동시에 빠르게 확인할 수 있게 한다.

## 2. 범위
### 포함
- 단일 페이지 대시보드 MVP
- 상단 액션 Hero + KPI + 리스크 계기판 + 하단 이벤트 타임라인
- 운영 로그 접이식 패널

### 제외
- 전략 규칙 변경
- 사용자 인증/권한
- DB 신규 도입(Supabase 등)
- 실시간 websocket 스트리밍

## 3. UX 원칙 (확정)
- **Action First**: 오늘 액션이 화면 최상단 1순위
- **계기판형 표기**: 수치 + 임계값 병기 (`Vol20: 2.54% (<5.9%)`)
- **노이즈 최소화**: 매매 로직 비핵심 지표(예: 50/100 이격도) 기본 화면 제외
- **템플릿 분리**: 액션일/무액션일 정보 밀도 분리
- **운영 추적성 보존**: run_id/alert_key 원본 유지

## 4. 정보 구조 (IA)
### Row 1 — Action Hero (full-width)
- 오늘 액션(매수/매도/유지)
- 현재 목표비중
- 핵심 사유 1줄
- 체결 가이드(미국장 종가 기준)
- 마지막 업데이트 시각

### Row 2 — KPI 카드 4개
- 세후 CAGR
- MDD
- 최근 1개월 수익률
- 조건 충족률(예: 5/6)

### Row 3 — 리스크 신호등 + 임계값
- Vol20
- SPY200 Dist
- TQQQ Dist200
- 상태색: Green / Amber / Red

### Row 4 — 이벤트 타임라인 (확정)
- 최근 30거래일 이벤트 중심
- 이벤트 타입:
  - 비중 변경
  - 강제청산
  - 재진입
  - TP10 감량
- 무변화일은 생략

### Row 5 — 운영 로그 (접이식)
- run_id
- alert_key
- last_success_at
- next_run_at

## 5. 데이터/백엔드 구조
## 입력 소스
1. `reports/signals_s1_s2_s3_user_original.csv`
2. `data/user_input.csv`
3. `reports/backtest_metrics_primary.csv`
4. `reports/daily_telegram_alert_state*.json`

## API 응답 스키마(개략)
- `action_hero`
- `kpi_cards`
- `risk_gauges`
- `event_timeline[]`
- `ops_log`

## 이벤트 생성 규칙
- `S2_weight[t-1] != S2_weight[t]` → 비중 변경
- `>0 -> 0` + 락조건 → 강제청산
- `0 -> >0` → 재진입
- `1.0 -> 0.95` → TP10 감량

## 6. 상태/오류 처리
- 데이터 파일 누락 시: 카드 단위 `N/A` + 상단 경고 배너
- 일부 지표 결측 시: 해당 카드만 degrade
- 타임라인 계산 실패 시: 타임라인 영역 fallback 메시지 출력

## 7. 성공 기준 (MVP)
- 3초 이내(로컬 기준) 첫 렌더
- 상단에서 오늘 액션과 목표비중 즉시 판별 가능
- KPI 4개 + 리스크 3개 + 이벤트 타임라인이 모두 보임
- 텔레그램 알림과 동일한 임계값/라벨 규칙 일치

## 8. 벤치마크 반영
- Grafana: 상단 핵심 질문 우선 배치
- Uptime Kuma: 상태 즉시 인지(신호등)
- Netdata: 이상징후 빠른 탐색
- Metabase: Above-the-fold 핵심 카드 집중
- Prometheus Alerting: actionable 정보 우선
