# Lessons Learned

- When presenting after-tax backtest metrics, do not apply tax directly to equity curve deltas.
  Always compute tax from realized gains at transaction level (sell events), aggregate by tax year,
  then apply deduction/rate. Add a tax ledger output to make assumptions auditable.
- 사용자가 기준 엔진(원본 코드)을 제공했을 때는, 명시적 승인 없이 대체 구현으로 실행하지 않는다.
  먼저 원본 코드 그대로 재현 실행을 하고, 대체/개선 엔진은 분리 실험으로 제안한다.
