# TQQQ Phase 2 성과개선 실험 Implementation Plan

## Goal
원본 신호엔진 기준선(세후 CAGR 38.60%) 대비, 과최적화 억제 게이트(MDD -50%, OOS 유지율 70%)를 만족하는 개선 파라미터를 탐색/채택한다.

## Task 1) 실험 설정 모듈화
- 파일: `src/tqqq_strategy/experiments/phase2_config.py` (create)
- 내용:
  - 탐색 파라미터 범위 정의
  - 제약조건 검증 함수(enter/exit, 단조성)
- 산출: 유효 후보 생성기

## Task 2) 원본 신호엔진 기반 실험 러너
- 파일: `src/tqqq_strategy/experiments/phase2_runner.py` (create)
- 입력:
  - baseline 데이터(`data/user_input.csv`)
  - 원본 로직 파라미터 세트
- 출력:
  - 후보별 성과 row

## Task 3) OOS 유지율 게이트
- 파일: `src/tqqq_strategy/experiments/phase2_oos.py` (create)
- 내용:
  - IS/OOS 분할 평가
  - 유지율 계산 및 통과 여부 판정

## Task 4) Coarse Grid 실행
- 파일: `ops/scripts/run_phase2_coarse.py` (create)
- 산출:
  - `experiments/trials.csv`

## Task 5) Fine Grid 실행
- 파일: `ops/scripts/run_phase2_fine.py` (create)
- 내용:
  - coarse 상위 후보 주변 정밀탐색
- 산출:
  - `experiments/trials_fine.csv`

## Task 6) 게이트 통과군/최종안 산출
- 파일: `ops/scripts/select_phase2_best.py` (create)
- 산출:
  - `experiments/passed_leaderboard.csv`
  - `experiments/best_config.json`

## Task 7) 검증
- 테스트:
  - 제약조건 위반 후보 제거 단위테스트
  - OOS 유지율 계산 단위테스트
- 실행:
  - 전체 pytest green
  - 실험 스크립트 재현 실행

## Done Criteria
- Gate 통과 후보 ≥ 1개 또는 baseline 유지 근거 명확
- 최종 산출물 3종(trials/leaderboard/best_config) 생성
- 재실행 시 동일 결과 재현

