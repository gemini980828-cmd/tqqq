# Lessons Learned

- When presenting after-tax backtest metrics, do not apply tax directly to equity curve deltas.
  Always compute tax from realized gains at transaction level (sell events), aggregate by tax year,
  then apply deduction/rate. Add a tax ledger output to make assumptions auditable.
