BASIC_DEDUCTION_KRW = 2_500_000.0
OVERSEAS_STOCK_TAX_RATE = 0.22


def apply_korean_overseas_tax(realized_profit_krw: float) -> float:
    taxable = max(realized_profit_krw - BASIC_DEDUCTION_KRW, 0.0)
    return taxable * OVERSEAS_STOCK_TAX_RATE
