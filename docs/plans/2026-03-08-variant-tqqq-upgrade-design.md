# Autopilot Spec - 변형티큐 고도화 실험 (2026-03-08)

## Goal
원본 변형티큐의 상시 운용형·리스크 관리형 성격을 유지한 채, 눈덩이티큐에서 얻은 원리만 활용해 고도화 후보를 자동 발굴·평가한다.

## Hard Constraints
- 눈덩이티큐 숫자/룰 복붙 금지
- 전액 재집중 / 전량 청산형 전술 금지
- 원본 변형티큐 아이디어 훼손 금지
- 과최적화 방지 우선
- 최우선 기준: **MDD 개선**, 단 **CAGR 훼손 시 기각**

## Candidate Families
1. A / 코어 상태기계 보정형
   - 기존 `BasicParams` 범위 내 미세 조정 (기존 Phase2 프레임 재사용)
2. C / 운영 규율 강화형
   - 재진입 램프, 단기 재진입 억제 등 whipsaw 완화 오버레이
3. B / 현금 재장전 보조레이어형
   - 과열 구간 소폭 현금 버퍼 확보 같은 보수적 reserve 오버레이

## Acceptance Criteria
- 산출물: 실험 스크립트/모듈, 결과 CSV/JSON, 설계·계획 문서
- baseline 대비 각 후보의 `aftertax_cagr`, `pretax_mdd`, `oos_retention`, turnover 비교 가능
- strict 판정 규칙 구현:
  - `aftertax_cagr >= baseline_aftertax_cagr`
  - `pretax_mdd > baseline_pretax_mdd`
- OOS 게이트는 최소한 별도 flag로 보고
- 결과가 없더라도 "엄격 기준에서 채택안 없음"을 검증 증거와 함께 리포트

## Reuse Targets
- `src/tqqq_strategy/experiments/phase2_config.py`
- `src/tqqq_strategy/experiments/phase2_runner.py`
- `src/tqqq_strategy/experiments/phase2_oos.py`
- `ops/scripts/run_phase2_coarse.py`
- `ops/scripts/run_phase2_fine.py`
- `ops/scripts/select_phase2_best.py`
- `ops/scripts/run_backtest_from_user_signal.py`

## Deliverables
- `.omx/plans/autopilot-impl.md`
- `docs/plans/2026-03-08-variant-tqqq-upgrade-design.md`
- `docs/plans/2026-03-08-variant-tqqq-upgrade-implementation-plan.md`
- 실험 코드 + 테스트 + 결과 리포트
