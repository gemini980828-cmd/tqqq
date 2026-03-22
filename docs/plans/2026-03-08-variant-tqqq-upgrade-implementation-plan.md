# Autopilot Implementation Plan - 변형티큐 고도화 실험 (2026-03-08)

## Requirements Summary
- 변형티큐 고도화 후보를 A/C/B 세 가족으로 구성한다.
- strict 채택 기준은 baseline 대비 MDD 개선 + CAGR 비훼손이다.
- OOS retention, stress, 비용/세후 관점을 함께 기록한다.
- 사용자 질문 없이 자율 실행하고 결과만 보고한다.

## Implementation Steps
1. 테스트 추가
   - overlay 변환과 strict ranking 로직의 기대 동작을 unit test로 고정
2. 실험 모듈 구현
   - baseline/phase2/overlay 후보 평가 유틸 추가
   - strict/soft ranking 계산 추가
3. 실행 스크립트 구현
   - Phase2 coarse/fine 결과 재사용 또는 자동 실행
   - overlay 후보 평가
   - 결과 CSV/JSON/markdown summary 저장
4. 문서화
   - design / implementation plan / review 업데이트
5. 검증
   - 새 unit tests
   - 기존 phase2/OOS 관련 tests
   - 실제 실험 스크립트 실행 및 산출물 확인

## Risks / Mitigations
- 과최적화: 후보 수를 소수의 구조적 preset으로 제한하고 strict rule을 baseline-relative로 고정
- 지표 혼동: baseline/strict/OOS flag를 분리 저장
- 성과 미개선: '채택안 없음'도 정식 결과로 허용

## Verification
- `pytest -q tests/experiments/test_upgrade_experiments.py tests/experiments/test_phase2_constraints.py tests/experiments/test_phase2_oos.py`
- `PYTHONPATH=src UV_CACHE_DIR=.uv-cache uv run python ops/scripts/run_variant_tqqq_upgrade_experiments.py`
