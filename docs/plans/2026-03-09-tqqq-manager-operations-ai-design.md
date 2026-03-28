# TQQQ Manager Operations + AI Design

**Date:** 2026-03-09  
**Scope:** Alpha Wealth Desk / Core Strategy Manager (`soft_overheat_buffer` 메인 엔진 반영)  
**Decision status:** Approved in-session

---

## 1. Goal

TQQQ 매니저를 기존의 "legacy 대시보드 임베드" 상태에서 벗어나,

- 현재 엔진 상태를 먼저 보여주고
- 그 상태에서 나온 주문안을 설명하며
- 삼성증권 수동 주문 환경에 맞는 실행 판단을 돕는
- 쉬운 설명형 AI 운영 매니저를 붙인

**실전 운영판**으로 승격한다.

메인 실전 엔진은 이번 세션에서 확정한 `soft_overheat_buffer`를 사용한다.

---

## 2. Product constraints

### 운영 제약
- 삼성증권은 API 자동 주문 연동이 불가하다.
- 사용자가 수동으로 주문을 입력한다.
- 따라서 시스템의 1차 역할은 **자동 주문**이 아니라 **정확한 수동 주문 보조**다.

### 전략 제약
- 메인 엔진의 성격은 유지한다.
- `soft_overheat_buffer`는 기존 변형티큐 엔진을 유지하면서 과열 구간에서만 보수적으로 완충하는 overlay다.
- AI는 비중을 새로 결정하면 안 된다.

### UX 제약
- AI는 쉬운 한국어로 설명해야 한다.
- `buffer`, `overheat active`, `cap weight` 같은 내부 용어를 전면에 내세우지 않는다.
- 기본은 행동 언어, 상세는 보조 설명으로 제공한다.

---

## 3. Current state diagnosis

현재 `CoreStrategyManager`는 다음 구조다.

- 상단: 실제 비중 / 목표 비중 / 리밸런싱 차이 / 평가금액
- 하단: 기존 `Dashboard` 컴포넌트 embedded

문제는 다음과 같다.

1. **상태기계가 직접 보이지 않는다**  
   현재 비중이 왜 90/95/100/0인지 해석하기 어렵다.

2. **최신 메인 엔진이 화면에 반영되지 않았다**  
   `soft_overheat_buffer`의 발동/해제와 같은 핵심 운영 정보가 UI에 없다.

3. **수동 주문용 제안이 약하다**  
   지금 화면은 보는 데는 도움이 되지만, 삼성증권에 무엇을 입력해야 할지 바로 이어지지 않는다.

4. **AI 역할이 총괄 오케스트레이터 쪽에만 치우쳐 있다**  
   TQQQ 매니저 자체의 운영 설명/주문 해설 AI는 아직 없다.

5. **freshness 관리가 약하다**  
   주문안은 계좌 입력과 가격 기준 시각에 강하게 의존하므로 stale 경고가 중요하다.

---

## 4. Design choice

세 가지 접근안 중 최종 선택은 다음이다.

### 채택안: 상태기계 모니터 중심 + 주문안 보조 + AI 운영 매니저

핵심 원칙:
- 먼저 "지금 어떤 상태인지"를 보여준다.
- 그 다음 "그래서 뭘 해야 하는지"를 보여준다.
- AI는 그 결과를 쉬운 말로 풀어 설명한다.

이 구조는 다음 이유로 채택됐다.
- 사용자는 수동 주문을 하기 전에 판단 근거를 이해해야 한다.
- 주문안만 크게 보여주면 실수 위험이 커진다.
- 상태 설명 → 주문안 → 체크리스트 흐름이 실전 운영에 더 맞다.

---

## 5. Information architecture

`CoreStrategyManager`는 다음 2열 구조로 재편한다.

### 좌측: deterministic 운영판
1. `EngineStateHero`
2. `StateMachineMonitor`
3. `OrderProposalCard`
4. `ExecutionChecklist`
5. `TransitionTimeline`

### 우측: AI Manager 패널
1. `AI Manager Brief`
2. `Ask TQQQ Manager`
3. `Order Memo`

### 화면 흐름
1. 현재 엔진 상태 확인
2. 계좌 입력 freshness 확인
3. 주문안 확인
4. 실행 체크리스트 확인
5. 필요시 AI 해설/질문 확인

---

## 6. Core UI components

### 6.1 `EngineStateHero`
역할:
- 현재 전략 상태를 선언하는 상단 헤더

표시 항목:
- 현재 상태 라벨(쉬운 말)
- 목표 비중
- 실제 비중
- 오늘 핵심 판단 한 줄
- 기준 시각 / freshness

예시 문구:
- "최근 상승이 강해서 지금은 평소보다 약간 보수적으로 운영하는 상태입니다."

### 6.2 `StateMachineMonitor`
역할:
- 현재 비중 결정 근거를 보여준다.

표시 항목:
- 기본 목표 비중
- 현재 적용 목표 비중
- 완충 상태 여부
- 해제 조건에 얼마나 가까운지
- 핵심 리스크 게이지

원칙:
- 내부 엔진 용어는 접어서 제공한다.
- 사용자용 메인 문구는 쉬운 말로 작성한다.

### 6.3 `OrderProposalCard`
역할:
- 수동 주문용 정확한 제안 카드

표시 항목:
- 오늘 액션(매수/매도/유지)
- 권장 수량
- 예상 주문 금액
- 주문 후 예상 비중
- 계산 기준 가격 / 시각
- 한 줄 이유

원칙:
- 삼성증권 수동 입력 메모처럼 보이게 한다.

### 6.4 `ExecutionChecklist`
역할:
- 실수 방지

표시 항목 예시:
- 계좌 입력 최신화 여부
- 현재가 기준 재확인
- 현금 부족 여부
- 장마감 기준 실행 원칙
- stale 데이터 경고

### 6.5 `TransitionTimeline`
역할:
- 최근 상태 전환 맥락 제공

표시 항목:
- 유지 / 매수 / 감량 / 현금 전환 / 완충 진입 / 완충 해제
- 발생 날짜
- 전환 사유

### 6.6 `TqqqAiManagerPanel`
역할:
- deterministic 결과를 쉬운 말로 풀어주는 운영 매니저

구성:
- 오늘 브리프
- quick prompts
- 자유 질문 입력
- 주문 메모

---

## 7. Snapshot contract additions

기존 snapshot 계약은 유지하고, 아래 블록을 additive하게 확장한다.

### `core_strategy_engine_state`
- `mode`
- `status_label`
- `plain_summary`
- `base_target_weight_pct`
- `target_weight_pct`
- `buffer_active`
- `buffer_reason`
- `buffer_release_hint`
- `generated_at`
- `stale`

### `core_strategy_order_proposal`
- `action`
- `order_quantity`
- `estimated_order_value_krw`
- `estimated_post_trade_weight_pct`
- `price_reference_krw`
- `rebalance_gap_before_pct`
- `rebalance_gap_after_pct`
- `reason_summary`
- `generated_at`
- `stale`

### `core_strategy_account_input`
- `cash_krw`
- `holding_quantity`
- `avg_cost_krw`
- `market_price_krw`
- `actual_weight_pct`
- `input_updated_at`
- `stale`

### `core_strategy_execution_checklist`
- `items[]` with `{ label, status, note }`

### `core_strategy_transition_timeline`
- `date`
- `event_type`
- `from_state`
- `to_state`
- `detail`
- `trigger`

### `core_strategy_ai_brief`
- `summary`
- `today_action`
- `warnings[]`
- `quick_prompts[]`
- `order_memo`
- `generated_at`

---

## 8. AI Manager behavior

### 역할 정의
AI는 다음만 담당한다.
1. 상황 요약
2. 실행 우선순위 정리
3. 주문안 해설
4. 운영 경고

### AI가 하지 말아야 할 일
- 엔진 밖에서 새 목표 비중 제안
- snapshot에 없는 수량/가격 추정
- stale 상태에서 확정적 주문 권고
- 백테스트 수익률만 근거로 공격적 행동 유도

### 말투 원칙
- 쉬운 설명이 먼저
- 숫자와 액션은 명확하게
- 내부 용어는 보조 설명으로만
- 과장/감정 표현 금지

예시:
- 나쁜 예: "현재는 overheat buffer active 상태입니다."
- 좋은 예: "최근 상승이 강해서 지금은 평소보다 약간 보수적으로 운영하는 상태입니다."

### UI 배치 원칙
- 메인 숫자/주문 카드는 deterministic
- AI는 오른쪽 패널에서 해설/메모/질문응답만 수행
- 기본 브리프는 짧게, 긴 설명은 explicit prompt 시에만

---

## 9. Phase 1 scope

### 포함
- `CoreStrategyManager` 재구성
- 상태기계 모니터 UI
- 주문안 카드 UI
- 실행 체크리스트 UI
- TQQQ 전용 AI 운영 패널
- snapshot contract 확장
- `soft_overheat_buffer` 상태 반영

### 제외
- AI가 비중/주문을 새로 계산하는 기능
- 삼성증권 자동주문 연동
- 체결 후 자동 actual 반영
- 다른 manager 동시 고도화
- 과도한 성과 리포트 전시

---

## 10. Validation criteria

1. 사용자가 화면만 보고 삼성증권에 수동 주문 입력 가능한가
2. 사용자가 왜 유지/매수/감량인지 쉬운 말로 이해하는가
3. stale 데이터면 경고가 우선 노출되는가
4. AI와 deterministic 카드가 같은 결론을 말하는가
5. `soft_overheat_buffer`가 UI/설명/주문안에 일관되게 반영되는가

---

## 11. Implementation note

이번 설계의 핵심은 "예쁜 카드 추가"가 아니다.

**TQQQ 엔진 결과를 운영 가능한 계약으로 승격하고, 그 결과를 쉬운 말의 AI 운영 매니저가 해설하는 구조**를 만드는 것이다.
