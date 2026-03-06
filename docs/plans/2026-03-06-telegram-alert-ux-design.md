# Telegram Alert UX Improvement Design (2026-03-06)

## 1) Goal
일일 텔레그램 알림에서 **"오늘 액션 필요 여부"를 최상단에 명확히 표시**하고,
코드 중심 메시지를 사람이 즉시 이해 가능한 운영 메시지로 개선한다.

## 2) Scope
- 일일 텔레그램 메시지 포맷 개선
- 상태파일 확장(entry_price 등)으로 진입가 대비 손익 정확 계산
- 사유 문구를 체크리스트(조건 충족/미충족) 형태로 변경

Out of scope:
- 전략 규칙 변경
- 대시보드 구현 변경
- 백테스트 로직 변경

## 3) Approved UX Structure

### 3.1 Top Action Banner (highest priority)
- `📢 [액션 없음] 포지션 유지`
- `📢 [매매 필요] 현금 → TQQQ (비중 10%)`
- `📢 [매매 필요] TQQQ 100% → 95% (TP10 익절)`

### 3.2 Signal Label (replace raw code transition)
- 기존 `신호코드 전환: 2->2`를 라벨 중심으로 교체
- 예시:
  - `신호: 풀 투자 유지`
  - `신호: 부분 진입(10%)`
  - `신호: 과열 감량(95%)`
  - `신호: 강제 청산(0%)`

### 3.3 Profit/Loss section split
- `일간 수익: 🔴-0.92% (전일 종가 대비)`
- `진입가 대비: 🟢+1.23% (진입가 $49.20)`

### 3.4 Loss-cut absolute display
- `로스 컷: 활성 ($46.86 | 진입가×0.941)`

### 3.5 Reason block as condition checklist
표기 규칙:
- 충족: ✅
- 미충족/해당없음: ⬜
- 리스크 감시/근접: ⚠
- 강제청산 트리거: 🚨

예시:
- `✅ 20일 변동성 < 5.9%: 3.24%`
- `✅ SPY 200MA 필터(>97.75): 103.85`
- `✅ TQQQ 200일 이격도 ≥ 101%: 103.01`
- `⬜ 과열 감량 구간(≥139): 미해당`
- `⬜ TP10 조건(신규100% 진입 후 +10%): 미해당`
- `⚠ 손절 감시(고비중 & 진입가×0.941): 활성`

## 4) State/Data Design (approved A)
상태파일(`daily_telegram_alert_state`) 확장:
- `last_alert_key`
- `position_weight`
- `entry_price`
- `entry_date`
- `tp10_done`

동작 규칙:
1. 비중 증가(0→양수, 10→100 등) 시 `entry_price` 갱신
2. 비중 유지/감소 시 `entry_price` 유지
3. 완전 청산(0%) 시 `entry_price` 초기화
4. 계산식
   - 일간 수익: `today_close / yesterday_close - 1`
   - 진입가 대비: `today_close / entry_price - 1`
   - 로스컷 절대값: `entry_price * 0.941`

## 5) Error Handling
- entry_price 미존재 시 `진입가 대비`는 `N/A`로 표시
- 데이터 결측 시 항목별 `N/A` 처리(전체 발송 실패로 확장하지 않음)
- 상태파일 파손 시 기본 상태로 복구 후 발송

## 6) Test Criteria
- 메시지 최상단에 액션 배너 존재
- 코드 전환 raw 값 대신 시그널 라벨 표시
- 일간/진입가 기준 손익 2줄 동시 표시
- 로스컷 절대값 표시
- 체크리스트 아이콘 규칙(✅/⬜/⚠/🚨) 검증
- 상태 전이(증가/유지/감소/청산)별 entry_price 갱신 테스트

## 7) Recommendation
본 설계를 기준으로 구현 계획(writing-plans) 단계로 전환한다.
