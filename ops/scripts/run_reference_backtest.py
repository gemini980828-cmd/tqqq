from __future__ import annotations

import argparse
import math
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

os.environ.setdefault("YFINANCE_CACHE_DIR", ".yfinance-cache")
try:
    yf.set_tz_cache_location(".yfinance-cache/tz")
except Exception:
    pass


@dataclass(frozen=True)
class BasicParams:
    rsi_len: int = 14
    rsi_reentry_thr: float = 43.0
    vol_threshold: float = 0.059
    vol_len: int = 20
    dist200_enter: float = 101.00
    dist200_exit: float = 100.00
    use_slope_boost: bool = True
    slope_len: int = 45
    slope_thr: float = 0.1100
    dist_cap: float = 98.8
    vol_cap: float = 0.06
    use_overheat_split: bool = True
    overheat1_enter: float = 139.0
    overheat1_exit: float = 132.0
    overheat2_enter: float = 146.0
    overheat2_exit: float = 138.0
    overheat3_enter: float = 149.0
    overheat3_exit: float = 140.0
    overheat4_enter: float = 151.0
    overheat4_exit: float = 118.0
    use_principal_stop: bool = True
    principal_stop_pct: float = 0.941
    use_spy_filter: bool = True
    spy_enter: float = 100.25
    spy_exit: float = 97.75
    spy_confirm_days: int = 1
    spy_bear_cap: float = 0.0
    use_tp10: bool = True
    tp10_trigger: float = 0.10
    tp10_cap: float = 0.95


def code_weight(code: int) -> float:
    return {2: 1.00, 3: 0.90, 4: 0.80, 1: 0.10, 5: 0.05, 0: 0.00}.get(code, min(max(code / 1000.0, 0.0), 1.0) if code >= 100 else 0.0)


def weight_to_code(w: float) -> int:
    w = min(max(float(w), 0.0), 1.0)
    for tgt, code in [(0.0, 0), (0.05, 5), (0.10, 1), (0.80, 4), (0.90, 3), (1.0, 2)]:
        if abs(w - tgt) < 0.0005:
            return code
    return int(round(w * 1000.0))


def is_high_exposure(code: int) -> bool:
    return code_weight(code) >= 0.80 - 1e-9


def rsi_wilder(close: np.ndarray, length: int) -> np.ndarray:
    s = pd.Series(close)
    diff = s.diff()
    up = diff.clip(lower=0)
    down = -diff.clip(upper=0)
    roll_up = up.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    roll_down = down.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    rs = roll_up / roll_down
    out = 100 - 100 / (1 + rs)
    return out.to_numpy()


def rolling_linreg_slope(y: np.ndarray, length: int) -> np.ndarray:
    n = len(y)
    out = np.full(n, np.nan)
    x = np.arange(length, dtype=float)
    denom = length * np.sum(x * x) - np.sum(x) ** 2
    if length <= 1 or denom == 0:
        return out
    for i in range(length - 1, n):
        w = y[i - length + 1 : i + 1]
        if np.isnan(w).any():
            continue
        m = (length * np.sum(x * w) - np.sum(x) * np.sum(w)) / denom
        out[i] = m
    return out


def compute_basic_strategy(df: pd.DataFrame, params: BasicParams) -> pd.Series:
    q_close = df["QQQ_adj"].to_numpy()
    q_ma3 = pd.Series(q_close).rolling(3, min_periods=3).mean().to_numpy()
    q_ma161 = pd.Series(q_close).rolling(161, min_periods=161).mean().to_numpy()
    t_adj = df["TQQQ_adj"].to_numpy()
    t_exec = df["TQQQ_close"].to_numpy()
    t_ma200 = pd.Series(t_adj).rolling(200, min_periods=200).mean().to_numpy()
    spy_adj = df["SPY_adj"].to_numpy()
    spy_ma200 = pd.Series(spy_adj).rolling(200, min_periods=200).mean().to_numpy()

    n = len(df)
    codes = np.zeros(n, dtype=int)

    dist200 = np.where(t_ma200 > 0, (t_adj / t_ma200) * 100.0, np.nan)
    ret = np.full(n, np.nan)
    ret[1:] = t_adj[1:] / t_adj[:-1] - 1.0
    v20 = pd.Series(ret).rolling(params.vol_len, min_periods=params.vol_len).std(ddof=1).to_numpy()
    spy_dist = np.where(spy_ma200 > 0, (spy_adj / spy_ma200) * 100.0, np.nan)
    q_rsi = rsi_wilder(q_close, params.rsi_len)
    dist_slope = rolling_linreg_slope(dist200, params.slope_len)

    asset = 0
    locked = False
    above200 = False
    above_init = False
    overheat = 0
    full_entry = math.nan
    reentry_lock = False
    spy_bull = False
    spy_init = False
    spy_cnt = 0
    tp_active = False
    tp_reduced = False
    tp_entry = math.nan

    for i in range(n):
        ready = not any(
            np.isnan(x)
            for x in [q_ma3[i], q_ma161[i], v20[i], dist200[i], spy_dist[i]]
        )
        prev = asset
        if not ready:
            asset = 0
            codes[i] = asset
            continue

        locked = (v20[i] + 1e-10) >= max(params.vol_threshold, 1e-6)

        if not spy_init:
            spy_bull = bool(spy_dist[i] >= params.spy_enter)
            spy_init = True
            spy_cnt = 0
        else:
            if spy_bull and spy_dist[i] <= params.spy_exit:
                spy_cnt += 1
                if spy_cnt >= max(int(params.spy_confirm_days), 1):
                    spy_bull, spy_cnt = False, 0
            elif (not spy_bull) and spy_dist[i] >= params.spy_enter:
                spy_cnt += 1
                if spy_cnt >= max(int(params.spy_confirm_days), 1):
                    spy_bull, spy_cnt = True, 0
            else:
                spy_cnt = 0

        spy_force_cash = (not spy_bull) and params.spy_bear_cap <= 1e-9
        reentry_blocked = reentry_lock and not (q_rsi[i] >= params.rsi_reentry_thr)

        if not above_init:
            above200 = dist200[i] >= params.dist200_enter
            above_init = True
        else:
            if above200 and dist200[i] <= params.dist200_exit:
                above200 = False
            elif (not above200) and dist200[i] >= params.dist200_enter:
                above200 = True

        if locked or spy_force_cash or reentry_blocked:
            base = 0
        else:
            base0 = 2 if above200 else (1 if q_ma3[i] > q_ma161[i] else 0)
            slope_ok = (
                params.use_slope_boost
                and base0 == 1
                and not np.isnan(dist_slope[i])
                and dist200[i] <= params.dist_cap
                and v20[i] <= params.vol_cap
                and dist_slope[i] >= params.slope_thr
            )
            base = 2 if slope_ok else base0

        if base == 2 and not (locked or spy_force_cash or reentry_blocked):
            if dist200[i] >= params.overheat4_enter:
                overheat = 4
            elif dist200[i] >= params.overheat3_enter:
                overheat = max(overheat, 3)
            elif dist200[i] >= params.overheat2_enter:
                overheat = max(overheat, 2)
            elif dist200[i] >= params.overheat1_enter:
                overheat = max(overheat, 1)
            else:
                if dist200[i] <= params.overheat4_exit:
                    overheat = 0
                elif dist200[i] <= params.overheat3_exit:
                    overheat = min(overheat, 2)
                elif dist200[i] <= params.overheat2_exit:
                    overheat = min(overheat, 1)
                elif dist200[i] <= params.overheat1_exit:
                    overheat = 0
        else:
            overheat = 0

        pre = base
        if overheat == 4:
            pre = 0
        elif overheat == 3 and base != 0:
            pre = 5
        elif overheat == 2 and base == 2:
            pre = 4
        elif overheat == 1 and base == 2:
            pre = 3

        stop_hit = False
        if params.use_principal_stop and is_high_exposure(prev) and not math.isnan(full_entry):
            if t_adj[i] <= full_entry * params.principal_stop_pct:
                stop_hit = True
                reentry_lock = True

        final = 0 if stop_hit else pre

        if final == 2 and code_weight(prev) < 0.999 and not tp_active and not tp_reduced:
            tp_active, tp_reduced, tp_entry = True, False, float(t_adj[i])
        if tp_active and (not tp_reduced) and final == 2 and t_adj[i] >= tp_entry * (1 + params.tp10_trigger):
            tp_reduced = True
        if tp_reduced and final == 2:
            final = weight_to_code(params.tp10_cap)

        asset = final
        if reentry_lock and code_weight(asset) > 1e-9:
            reentry_lock = False

        if is_high_exposure(asset) and not is_high_exposure(prev):
            full_entry = float(t_adj[i])
        if (not is_high_exposure(asset)) and is_high_exposure(prev):
            full_entry = math.nan

        codes[i] = asset

    return pd.Series([code_weight(c) for c in codes], index=df.index, name="weight")


def compute_metrics(equity: pd.Series, daily_ret: pd.Series, bench: pd.Series) -> dict[str, float]:
    n = len(equity)
    years = n / 252
    cagr = float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1) if years > 0 else float("nan")
    running_max = equity.cummax()
    dd = equity / running_max - 1
    mdd = float(dd.min())

    ann_vol = float(daily_ret.std(ddof=1) * np.sqrt(252))
    sharpe = float((daily_ret.mean() * 252) / ann_vol) if ann_vol > 0 else float("nan")

    downside = daily_ret[daily_ret < 0]
    downside_vol = float(downside.std(ddof=1) * np.sqrt(252)) if len(downside) > 1 else float("nan")
    sortino = float((daily_ret.mean() * 252) / downside_vol) if downside_vol and downside_vol > 0 else float("nan")

    calmar = float(cagr / abs(mdd)) if mdd < 0 else float("nan")
    win_rate = float((daily_ret > 0).mean())
    profit_factor = float(daily_ret[daily_ret > 0].sum() / abs(daily_ret[daily_ret < 0].sum())) if (daily_ret[daily_ret < 0].sum() < 0) else float("nan")
    ulcer_index = float(np.sqrt(np.mean((dd * 100) ** 2)))

    cov = np.cov(daily_ret.fillna(0), bench.fillna(0))[0, 1]
    var_b = np.var(bench.fillna(0))
    beta = float(cov / var_b) if var_b > 0 else float("nan")

    peaks = equity.cummax()
    in_dd = equity < peaks
    max_dd_dur, cur = 0, 0
    for v in in_dd.to_numpy():
        cur = cur + 1 if v else 0
        max_dd_dur = max(max_dd_dur, cur)

    return {
        "CAGR": cagr,
        "MDD": mdd,
        "AnnualVol": ann_vol,
        "Sharpe": sharpe,
        "Sortino": sortino,
        "Calmar": calmar,
        "WinRateDaily": win_rate,
        "ProfitFactor": profit_factor,
        "UlcerIndex": ulcer_index,
        "BetaVsQQQ": beta,
        "MaxDDDurationDays": float(max_dd_dur),
    }


def apply_yearly_tax(
    equity: pd.Series,
    initial_capital_krw: float,
    annual_deduction_krw: float = 2_500_000,
    tax_rate: float = 0.22,
) -> pd.Series:
    taxed = equity.copy().astype(float)
    years = taxed.index.year
    for y in sorted(np.unique(years)):
        idx = taxed.index[years == y]
        if len(idx) < 2:
            continue
        start, end = idx[0], idx[-1]
        pnl_krw = (taxed.loc[end] - taxed.loc[start]) * initial_capital_krw
        tax_krw = max(pnl_krw - annual_deduction_krw, 0.0) * tax_rate
        taxed.loc[end] -= tax_krw / initial_capital_krw
    return taxed


def run(start: str, end: str, out_dir: Path, initial_capital_krw: float) -> None:
    raw = yf.download(["TQQQ", "QQQ", "SPY"], start=start, end=end, auto_adjust=False, progress=False)
    if raw.empty:
        raise RuntimeError("No data downloaded")

    df = pd.DataFrame(index=raw.index)
    for sym in ["TQQQ", "QQQ", "SPY"]:
        df[f"{sym}_close"] = raw[("Close", sym)]
        df[f"{sym}_adj"] = raw[("Adj Close", sym)]

    df = df.dropna().copy()
    weight = compute_basic_strategy(df, BasicParams(spy_bear_cap=0.0))
    ret = df["TQQQ_close"].pct_change().fillna(0.0)

    eq = pd.Series(index=df.index, dtype=float)
    eq.iloc[0] = 1.0
    prev_w = 0.0
    cost_oneway = 0.0005  # 5bps
    for i in range(1, len(df)):
        w_prev = float(weight.iloc[i - 1])
        gross = eq.iloc[i - 1] * (1.0 + w_prev * ret.iloc[i])
        turnover = abs(float(weight.iloc[i]) - prev_w)
        net = gross * (1.0 - turnover * cost_oneway)
        eq.iloc[i] = net
        prev_w = float(weight.iloc[i])

    eq = eq.ffill().fillna(1.0)
    qqq_eq = (1 + df["QQQ_close"].pct_change().fillna(0.0)).cumprod()

    pretax = compute_metrics(eq, eq.pct_change().fillna(0), qqq_eq.pct_change().fillna(0))
    taxed_eq = apply_yearly_tax(eq, initial_capital_krw=initial_capital_krw)
    aftertax_cagr = (taxed_eq.iloc[-1] / taxed_eq.iloc[0]) ** (252 / len(taxed_eq)) - 1
    pretax["AfterTaxCAGR"] = float(aftertax_cagr)

    out_dir.mkdir(parents=True, exist_ok=True)
    report = pd.DataFrame([pretax])
    report.to_csv(out_dir / "backtest_metrics_primary.csv", index=False)
    pd.DataFrame({"date": df.index, "weight": weight.values, "equity": eq.values, "taxed_equity": taxed_eq.values}).to_csv(
        out_dir / "backtest_equity_primary.csv", index=False
    )

    print("=== Backtest Summary (Primary) ===")
    for k, v in pretax.items():
        if "Days" in k:
            print(f"{k}: {v:.0f}")
        else:
            print(f"{k}: {v:.4f}")
    print(f"Saved: {(out_dir / 'backtest_metrics_primary.csv').as_posix()}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2011-06-23")
    ap.add_argument("--end", default="2026-01-31")
    ap.add_argument("--out-dir", default="reports")
    ap.add_argument("--initial-krw", type=float, default=100_000_000)
    args = ap.parse_args()
    run(args.start, args.end, Path(args.out_dir), args.initial_krw)
