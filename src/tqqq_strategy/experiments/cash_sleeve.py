from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class CashSleeveConfig:
    threshold_days: int
    annual_yield: float
    sleeve_cost_oneway: float = 0.0001
    eligible_max_weight: float = 0.999999


def build_parking_mask(
    target_weight: pd.Series,
    threshold_days: int,
    eligible_max_weight: float = 0.999999,
) -> pd.Series:
    active: list[bool] = []
    streak = 0
    for weight in target_weight.astype(float):
        eligible = weight <= eligible_max_weight
        if eligible:
            streak += 1
        else:
            streak = 0
        active.append(eligible and streak >= max(threshold_days, 1))
    return pd.Series(active, index=target_weight.index, dtype=bool)


def build_daily_yield_series_from_annual_returns(
    dates: pd.Series,
    annual_returns: dict[int, float],
    inception_date: str,
) -> pd.Series:
    inception = pd.Timestamp(inception_date)
    out = []
    for dt in pd.to_datetime(dates):
        if dt < inception:
            out.append(0.0)
            continue
        annual = annual_returns.get(int(dt.year), 0.0)
        out.append((1.0 + annual) ** (1.0 / 252.0) - 1.0)
    return pd.Series(out, index=dates.index if hasattr(dates, "index") else None, dtype=float)


def cagr(eq: pd.Series) -> float:
    years = len(eq) / 252
    return float((eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1) if years > 0 else 0.0


def mdd(eq: pd.Series) -> float:
    return float((eq / eq.cummax() - 1).min())


def simulate_with_cash_sleeve(
    *,
    prices_krw: pd.Series,
    target_weight: pd.Series,
    initial_capital_krw: float,
    tqqq_cost_oneway: float,
    sleeve: CashSleeveConfig,
    sleeve_daily_yield: pd.Series | None = None,
) -> tuple[pd.Series, pd.DataFrame]:
    idx = prices_krw.index
    parking_mask = build_parking_mask(
        target_weight,
        threshold_days=sleeve.threshold_days,
        eligible_max_weight=getattr(sleeve, "eligible_max_weight", 0.999999),
    )
    sleeve_daily = (1.0 + sleeve.annual_yield) ** (1.0 / 252.0) - 1.0

    cash = float(initial_capital_krw)
    parked = 0.0
    shares = 0.0
    equity = pd.Series(index=idx, dtype=float)
    rows: list[dict[str, float | bool | str]] = []

    for i, dt in enumerate(idx):
        price = float(prices_krw.iloc[i])
        weight = float(target_weight.iloc[i])
        day_yield = float(sleeve_daily_yield.iloc[i]) if sleeve_daily_yield is not None else sleeve_daily

        if parked > 0.0:
            parked *= 1.0 + day_yield

        gross_equity = cash + parked + shares * price
        target_value = gross_equity * weight
        target_shares = target_value / price if price > 0 else 0.0
        delta = target_shares - shares

        tqqq_buy_fee = 0.0
        tqqq_sell_fee = 0.0
        sleeve_buy_fee = 0.0
        sleeve_sell_fee = 0.0

        if delta < -1e-12:
            sell_qty = min(-delta, shares)
            gross_proceeds = sell_qty * price
            tqqq_sell_fee = gross_proceeds * tqqq_cost_oneway
            cash += gross_proceeds - tqqq_sell_fee
            shares -= sell_qty

        elif delta > 1e-12:
            gross_need = delta * price
            total_need = gross_need * (1.0 + tqqq_cost_oneway)
            if total_need > cash and parked > 0.0:
                need_from_parked = min(parked, (total_need - cash) / max(1.0 - sleeve.sleeve_cost_oneway, 1e-12))
                sleeve_sell_fee = need_from_parked * sleeve.sleeve_cost_oneway
                parked -= need_from_parked
                cash += need_from_parked - sleeve_sell_fee
            buy_qty = delta
            gross_need = buy_qty * price
            tqqq_buy_fee = gross_need * tqqq_cost_oneway
            total_need = gross_need + tqqq_buy_fee
            if total_need > cash and price > 0:
                buy_qty = cash / (price * (1.0 + tqqq_cost_oneway))
                gross_need = buy_qty * price
                tqqq_buy_fee = gross_need * tqqq_cost_oneway
                total_need = gross_need + tqqq_buy_fee
            if buy_qty > 1e-12:
                shares += buy_qty
                cash -= total_need

        gross_equity = cash + parked + shares * price
        residual_target = gross_equity * max(0.0, 1.0 - weight)
        desired_parked = residual_target if bool(parking_mask.iloc[i]) else 0.0

        if desired_parked > parked + 1e-12:
            move = min(cash, desired_parked - parked)
            sleeve_buy_fee = move * sleeve.sleeve_cost_oneway
            if move + sleeve_buy_fee > cash:
                move = cash / (1.0 + sleeve.sleeve_cost_oneway)
                sleeve_buy_fee = move * sleeve.sleeve_cost_oneway
            if move > 1e-12:
                cash -= move + sleeve_buy_fee
                parked += move
        elif desired_parked + 1e-12 < parked:
            move = parked - desired_parked
            sleeve_sell_fee += move * sleeve.sleeve_cost_oneway
            parked -= move
            cash += move - move * sleeve.sleeve_cost_oneway

        total_equity = cash + parked + shares * price
        equity.iloc[i] = total_equity / initial_capital_krw
        rows.append(
            {
                "date": str(dt.date()),
                "weight": weight,
                "parking_active": bool(parking_mask.iloc[i]),
                "shares": shares,
                "cash_krw": cash,
                "parked_krw": parked,
                "tqqq_buy_fee_krw": tqqq_buy_fee,
                "tqqq_sell_fee_krw": tqqq_sell_fee,
                "sleeve_buy_fee_krw": sleeve_buy_fee,
                "sleeve_sell_fee_krw": sleeve_sell_fee,
                "equity_krw": total_equity,
            }
        )

    return equity, pd.DataFrame(rows)


def simulate_with_taxed_cash_sleeve(
    *,
    prices_krw: pd.Series,
    target_weight: pd.Series,
    initial_capital_krw: float,
    tqqq_cost_oneway: float,
    sleeve: CashSleeveConfig,
    annual_deduction_krw: float,
    tax_rate: float,
    sleeve_daily_yield: pd.Series | None = None,
) -> tuple[pd.Series, pd.Series, pd.DataFrame]:
    idx = prices_krw.index
    parking_mask = build_parking_mask(
        target_weight,
        threshold_days=sleeve.threshold_days,
        eligible_max_weight=sleeve.eligible_max_weight,
    )
    sleeve_daily = (1.0 + sleeve.annual_yield) ** (1.0 / 252.0) - 1.0

    cash = float(initial_capital_krw)
    parked = 0.0
    shares = 0.0
    avg_cost_krw = 0.0
    ytd_realized = 0.0
    cum_tax_paid = 0.0
    current_year = int(idx[0].year)

    eq_pre = pd.Series(index=idx, dtype=float)
    eq_after = pd.Series(index=idx, dtype=float)
    rows: list[dict[str, float | bool | str | int]] = []

    for i, dt in enumerate(idx):
        price = float(prices_krw.iloc[i])
        weight = float(target_weight.iloc[i])
        day_yield = float(sleeve_daily_yield.iloc[i]) if sleeve_daily_yield is not None else sleeve_daily

        if parked > 0.0:
            parked *= 1.0 + day_yield

        gross_equity = cash + parked + shares * price
        target_value = gross_equity * weight
        target_shares = target_value / price if price > 0 else 0.0
        delta = target_shares - shares

        tqqq_buy_fee = 0.0
        tqqq_sell_fee = 0.0
        sleeve_buy_fee = 0.0
        sleeve_sell_fee = 0.0
        realized_today = 0.0

        if delta < -1e-12:
            sell_qty = min(-delta, shares)
            gross_proceeds = sell_qty * price
            tqqq_sell_fee = gross_proceeds * tqqq_cost_oneway
            net_proceeds = gross_proceeds - tqqq_sell_fee
            removed_basis = avg_cost_krw * sell_qty
            realized_today = net_proceeds - removed_basis
            cash += net_proceeds
            shares -= sell_qty
            ytd_realized += realized_today
            if shares <= 1e-12:
                shares = 0.0
                avg_cost_krw = 0.0

        elif delta > 1e-12:
            gross_need = delta * price
            total_need = gross_need * (1.0 + tqqq_cost_oneway)
            if total_need > cash and parked > 0.0:
                need_from_parked = min(parked, (total_need - cash) / max(1.0 - sleeve.sleeve_cost_oneway, 1e-12))
                sleeve_sell_fee = need_from_parked * sleeve.sleeve_cost_oneway
                parked -= need_from_parked
                cash += need_from_parked - sleeve_sell_fee
            buy_qty = delta
            gross_need = buy_qty * price
            tqqq_buy_fee = gross_need * tqqq_cost_oneway
            total_need = gross_need + tqqq_buy_fee
            if total_need > cash and price > 0:
                buy_qty = cash / (price * (1.0 + tqqq_cost_oneway))
                gross_need = buy_qty * price
                tqqq_buy_fee = gross_need * tqqq_cost_oneway
                total_need = gross_need + tqqq_buy_fee
            if buy_qty > 1e-12:
                new_total_shares = shares + buy_qty
                avg_cost_krw = (shares * avg_cost_krw + total_need) / new_total_shares
                shares = new_total_shares
                cash -= total_need

        gross_equity = cash + parked + shares * price
        residual_target = gross_equity * max(0.0, 1.0 - weight)
        desired_parked = residual_target if bool(parking_mask.iloc[i]) else 0.0

        if desired_parked > parked + 1e-12:
            move = min(cash, desired_parked - parked)
            sleeve_buy_fee = move * sleeve.sleeve_cost_oneway
            if move + sleeve_buy_fee > cash:
                move = cash / (1.0 + sleeve.sleeve_cost_oneway)
                sleeve_buy_fee = move * sleeve.sleeve_cost_oneway
            if move > 1e-12:
                cash -= move + sleeve_buy_fee
                parked += move
        elif desired_parked + 1e-12 < parked:
            move = parked - desired_parked
            sleeve_sell_fee += move * sleeve.sleeve_cost_oneway
            parked -= move
            cash += move - move * sleeve.sleeve_cost_oneway

        pre_tax_equity = cash + parked + shares * price
        eq_pre.iloc[i] = pre_tax_equity
        eq_after.iloc[i] = pre_tax_equity - cum_tax_paid

        next_year = int(idx[i + 1].year) if i + 1 < len(idx) else None
        year_end = (next_year is None) or (next_year != current_year)
        if year_end:
            taxable = max(ytd_realized - annual_deduction_krw, 0.0)
            tax_paid_today = taxable * tax_rate
            if tax_paid_today > 0:
                cum_tax_paid += tax_paid_today
                cash -= tax_paid_today
                eq_after.iloc[i] = pre_tax_equity - cum_tax_paid
            rows.append(
                {
                    "year": current_year,
                    "realized_gain_krw": ytd_realized,
                    "taxable_gain_krw": taxable,
                    "tax_paid_krw": tax_paid_today,
                }
            )
            ytd_realized = 0.0
            if next_year is not None:
                current_year = next_year

        rows.append(
            {
                "date": str(dt.date()),
                "weight": weight,
                "parking_active": bool(parking_mask.iloc[i]),
                "shares": shares,
                "cash_krw": cash,
                "parked_krw": parked,
                "realized_today_krw": realized_today,
                "tqqq_buy_fee_krw": tqqq_buy_fee,
                "tqqq_sell_fee_krw": tqqq_sell_fee,
                "sleeve_buy_fee_krw": sleeve_buy_fee,
                "sleeve_sell_fee_krw": sleeve_sell_fee,
                "equity_krw": eq_pre.iloc[i],
                "taxed_equity_krw": eq_after.iloc[i],
            }
        )

    return eq_pre / initial_capital_krw, eq_after / initial_capital_krw, pd.DataFrame(rows)
