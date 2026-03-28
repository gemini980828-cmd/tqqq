# Alpha Wealth Desk Home Polish 작업 지시서

작성일: 2026-03-21  
대상: 웹 디자이너 / 프론트엔드 UX 담당  
목적: Home 레이아웃 개편 이후 남아 있는 UX 완성도 이슈를 정리하고, **Action-First 운영 대시보드** 관점에서 마감 수준으로 끌어올리기 위한 상세 작업 지시

---

# 1. 이번 요청의 목적

이번 요청은 “새로운 기능 추가”가 아닙니다.  
이미 구현된 Home 구조를 바탕으로, 사용자가 실제로 화면을 봤을 때:

- 어디를 먼저 봐야 하는지
- 어떤 manager가 더 급한지
- Hero에서 무엇을 읽고 바로 이해해야 하는지
- Orchestrator가 어떻게 더 자연스러운 대화 인터페이스처럼 느껴져야 하는지

를 더 명확하게 만드는 **UX polish 작업**입니다.

즉, 이번 작업의 핵심은:

> **작동하는 UI를, 실제 운영 대시보드다운 정보 위계와 행동 흐름을 가진 UI로 마무리하는 것**

입니다.

---

# 2. 이번 작업 범위

이번 라운드에서 반드시 다룰 항목은 아래 3가지입니다.

## 필수 작업
1. **Manager Workbench 상태 강조 연결**
2. **Hero를 정적 문구에서 동적 상태 문구로 변경**

## 가능하면 포함, 하지만 후순위 가능
3. **Orchestrator 패널 대화 흐름을 append + scroll-bottom 구조로 정리**

---

# 3. 작업 우선순위

## P1 — 반드시 반영

### A. Manager Workbench 상태 강조
### B. Hero 동적화

이 둘은 이번 Home의 핵심 목적과 직접 연결됩니다.

## P2 — 반영 권장

### C. Orchestrator conversation UX 개선

이건 분명 중요하지만, backend 연결을 막는 blocker는 아닙니다.  
시간/범위가 빡빡하면 P1 완료 후 처리해도 됩니다.

---

# 4. 작업 대상 파일

## 핵심 수정 대상
- `app/web/src/components/home/HomeManagerWorkbench.tsx`
- `app/web/src/components/ManagerCard.tsx`
- `app/web/src/components/home/HomeHeroCompact.tsx`
- `app/web/src/pages/Home.tsx`
- `app/web/src/components/OrchestratorPanel.tsx`

## 참고 파일
- `app/web/src/types/appSnapshot.ts`
- `app/web/src/lib/navigation.ts`
- `docs/analysis/2026-03-21-home-layout-execution-handoff.md`
- `docs/analysis/2026-03-21-home-layout-revision-analysis.md`

---

# 5. 작업 상세 지시

## Task 1. Manager Workbench 상태 강조 연결

## 목적
Manager grid를 단순 카드 목록이 아니라,  
**우선순위가 반영된 workspace entry portal**로 만들기 위함입니다.

현재 문제:
- `ManagerCard`에는 `hasPriorityAction`, `hasCrossAlert`를 반영하는 시각적 상태가 이미 있음
- 하지만 `HomeManagerWorkbench`에서 해당 값을 넘기지 않아
- 실제 Home에서는 모든 카드가 거의 동등하게 보임

이 상태는 Action-First UX와 충돌합니다.

---

## 해야 할 일

### 1) `HomeManagerWorkbench` props 확장

현재 `HomeManagerWorkbench`는 대략 다음만 받습니다:

- `managers`

이걸 아래처럼 확장하세요.

예시:

```ts
interface Props {
  managers: ManagerCardSummary[]
  priorityActions?: PriorityAction[]
  crossAlerts?: CrossManagerAlert[]
}
```

---

### 2) 각 manager별 강조 상태 계산

각 card마다 아래를 계산해야 합니다.

```ts
const hasPriorityAction = priorityActions.some(
  (action) => action.manager_id === manager.manager_id,
)

const hasCrossAlert = crossAlerts.some(
  (alert) => alert.manager_ids.includes(manager.manager_id),
)
```

그 후:

```tsx
<ManagerCard
  card={manager}
  hasPriorityAction={hasPriorityAction}
  hasCrossAlert={hasCrossAlert}
/>
```

로 전달하세요.

---

### 3) 시각적 해석 기준 유지

`ManagerCard`의 상태 해석은 아래를 유지하세요.

- `hasPriorityAction === true`
  - 가장 강한 강조
  - “지금 들어가야 하는 manager”

- `hasCrossAlert === true`
  - 중간 강조
  - “단독 manager는 아니지만 함께 봐야 하는 manager”

- 둘 다 아니면 normal monitoring

주의:
- priority와 cross alert가 동시에 있으면 **priority가 우선**

---

### 4) 카드가 실제 entry portal처럼 보이게 유지

`ManagerCard`에서 다음 affordance는 유지하거나 더 선명하게 해도 됩니다.

- headline
- status line
- 하단 `Enter →` 혹은 유사 진입 affordance

단, 지금 단계에서는 디자인 실험보다  
**“어느 카드가 더 급한지 바로 느껴지게 만드는 것”**이 우선입니다.

---

## 완료 기준

- Home에서 Manager Workbench를 봤을 때
  - 어떤 manager가 긴급한지
  - 어떤 manager가 cross-alert 관련인지
  - 어떤 manager가 일반 상태인지
  가 시각적으로 바로 구분됨

---

# 6. Task 2. Hero를 동적 상태 기반으로 변경

## 목적
현재 Hero는 감성적인 환영 문구 역할만 합니다.

하지만 운영 대시보드의 Hero는:

- 오늘의 핵심 액션
- 현재 운용 stance
- 가장 먼저 읽어야 하는 문장

을 전달해야 합니다.

즉, Hero는 “인사말”이 아니라  
**운영 지시의 첫 문장**이어야 합니다.

---

## 해야 할 일

### 1) `HomeHeroCompact`에 snapshot/action 정보 전달

현재 정적 텍스트만 출력하고 있다면,
최소 아래 데이터를 받도록 변경하세요.

예시:

```ts
type Props = {
  action?: string
  targetWeightPct?: number
  reasonSummary?: string
}
```

또는 더 직접적으로:

```ts
type Props = {
  snapshot?: AppSnapshot
}
```

둘 중 하나를 선택하되, 내부에서 과한 계산은 하지 마세요.

---

### 2) Hero 문장 구조

권장 구조:

#### 1행: 운영 headline
- 예:
  - `오늘은 매수 검토가 필요합니다.`
  - `오늘은 현재 비중 유지가 기본 전략입니다.`

#### 2행: 보조 요약
- 예:
  - `전략 목표 비중 100% 기준, 장마감 전 판단이 필요합니다.`
  - `리스크 조건은 안정적이며 현재 포지션을 유지합니다.`

#### 3행(optional): 아주 짧은 reason
- `reason_summary`를 너무 길게 다 노출하지 말고 1~2줄 압축

---

### 3) static greeting 제거

기존:
- `Good Morning.`
- `Here is what requires your attention today.`

이런 문구는 완전히 지우거나,
브랜드 보조 문구 수준으로만 축소하세요.

이번 Home의 핵심은 감성이 아니라 **즉시성**입니다.

---

### 4) Hero와 Action Center의 역할 분리

Hero는:
- **오늘의 한 줄 방향**

Priority Actions는:
- **실제 실행 항목 목록**

즉, Hero에서 액션 카드 내용을 그대로 반복하지 말고,
Action Center에 들어가기 전에 사용자의 시야를 정렬하는 역할만 하게 하세요.

---

## 완료 기준

- Home에 들어오면 첫 1초 안에
  - 오늘의 핵심 액션 방향
  - 기본 stance
  가 텍스트만 읽어도 이해됨

---

# 7. Task 3. Orchestrator 대화 UX 개선

## 중요도
P2  
가능하면 이번에 포함, 아니면 다음 라운드로 넘겨도 됨

## 목적
지금 Orchestrator는 구조화 응답은 좋아졌지만,  
대화 흐름 UX는 아직 완전히 자연스럽지 않을 수 있습니다.

채팅형 인터페이스는 사용자가 이미 학습한 패턴이 있으므로,
**최신 메시지가 아래에 쌓이는 구조**가 더 자연스럽습니다.

---

## 해야 할 일

### 1) history ordering 점검

현재 구조가 prepend(최신이 위)라면,
append(최신이 아래)로 바꾸세요.

즉:

- 오래된 메시지 위
- 최신 메시지 아래

구조가 되어야 합니다.

---

### 2) 새 응답 후 scroll-bottom

새 질문 제출 또는 새 응답 완료 시:

- 스크롤이 자연스럽게 아래로 이동해야 합니다.

단순 jump도 가능하지만,
가능하면 부드러운 이동이 더 좋습니다.

---

### 3) optimistic message 흐름 점검

현재 `'...'` 같은 placeholder를 쓰고 있다면:

- 사용자 질문
- 로딩 상태
- 최종 응답

이 한 흐름이 시각적으로 끊기지 않게 정리하세요.

목표는 “메시지가 위아래로 뒤집히는 느낌”을 없애는 것입니다.

---

### 4) input zone은 하단 고정 유지

데모 감성의 핵심 중 하나는:

- 메시지 영역은 스크롤되고
- 입력 영역은 하단에 안정적으로 남는 것

입니다.

이건 유지하세요.

---

## 완료 기준

- Orchestrator가 더 이상 “알림 목록”처럼 느껴지지 않고
- 실제 대화형 작업 콘솔처럼 느껴짐

---

# 8. 하지 말아야 할 것

1. **ManagerCard 내부 디자인을 새로 발명하지 말 것**
   - 이번 작업은 이미 있는 강조 시스템을 연결하는 것이 핵심

2. **Hero를 다시 긴 소개문구 영역으로 만들지 말 것**
   - 짧고 즉시적인 문장 유지

3. **Orchestrator에 새 기능을 추가하지 말 것**
   - 이번엔 대화 흐름 UX 정리만

4. **route / backend 계약을 건드리지 말 것**
   - 이번 작업은 프론트 polish 범위

5. **Action Center보다 Hero를 더 무겁게 만들지 말 것**
   - Hero는 방향 제시
   - Action Center는 실행 유도

---

# 9. 권장 작업 순서

## Step 1
- `HomeManagerWorkbench`에 priority/cross-alert 상태 연결

## Step 2
- `HomeHeroCompact`를 snapshot/action 기반으로 동적화

## Step 3
- Home에서 Hero → Action → Alert → Manager 흐름이 자연스러운지 확인

## Step 4
- 시간 여유가 있으면 Orchestrator append/scroll-bottom 정리

---

# 10. 검증 체크리스트

## 필수
- [ ] Home 진입 시 Hero가 정적 greeting이 아니라 운영 문장으로 보임
- [ ] Manager grid에서 긴급 manager가 바로 보임
- [ ] priority action 있는 manager가 visually surfaced 됨
- [ ] cross-alert 관련 manager가 visually surfaced 됨
- [ ] build 통과
- [ ] lint 통과

## 선택
- [ ] Orchestrator 최신 메시지가 아래에 쌓임
- [ ] 응답 완료 후 scroll-bottom 동작

---

# 11. 최종 완료 정의

이번 polish 작업은 아래를 만족하면 완료입니다.

1. Home의 첫 시선이 “오늘의 방향 → 지금 처리할 일 → 어느 manager로 갈지” 순으로 흐른다
2. Manager grid가 단순 카드 목록이 아니라 우선순위가 반영된 entry portal처럼 보인다
3. Hero가 더 이상 dead space가 아니라 운영 지시의 첫 문장 역할을 한다
4. Orchestrator는 가능하면 더 자연스러운 대화 인터페이스로 정리된다

---

# 12. 한 줄 지시

이번 작업은 **디자인을 새로 하는 것**이 아니라,  
**이미 구현된 Home을 진짜 운영 대시보드답게 정보 위계와 행동 흐름 측면에서 마감하는 작업**입니다.
