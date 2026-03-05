# -*- coding: utf-8 -*-
"""
김째매매법(Pine v6)과 '동일한 목표 비중(assetCode / weight)'을 산출하기 위한 레퍼런스 구현.
(사용자 제공 코드 기반 실행용)
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd

FILE_PATH = "data/user_input.csv"
ENCODING = "utf-8-sig"


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


def to_float_series(s: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(s):
        return s.astype(float)
    return pd.to_numeric(s.astype(str).str.replace(",", ""), errors="coerce").astype(float)


def code_weight(code: int) -> float:
    if code == 2:
        return 1.00
    if code == 3:
        return 0.90
    if code == 4:
        return 0.80
    if code == 1:
        return 0.10
    if code == 5:
        return 0.05
    if code == 0:
        return 0.00
    if code >= 100:
        return float(min(max(code / 1000.0, 0.0), 1.0))
    return 0.00


def weight_to_code(w: float) -> int:
    wC = float(min(max(w, 0.0), 1.0))
    eps = 0.0005
    if wC <= eps:
        return 0
    if abs(wC - 0.05) < eps:
        return 5
    if abs(wC - 0.10) < eps:
        return 1
    if abs(wC - 0.80) < eps:
        return 4
    if abs(wC - 0.90) < eps:
        return 3
    if abs(wC - 1.00) < eps:
        return 2
    return int(round(wC * 1000.0))


def is_high_exposure(code: int) -> bool:
    return code_weight(code) >= (0.80 - 1e-9)


def rsi_wilder(close: np.ndarray, length: int) -> np.ndarray:
    n = len(close)
    rsi = np.full(n, np.nan, dtype=float)
    if n == 0:
        return rsi

    ch = np.diff(close, prepend=np.nan)
    up = np.where(np.isnan(ch), np.nan, np.maximum(ch, 0.0))
    dn = np.where(np.isnan(ch), np.nan, np.maximum(-ch, 0.0))

    up_sma = pd.Series(up).rolling(length, min_periods=length).mean().to_numpy()
    dn_sma = pd.Series(dn).rolling(length, min_periods=length).mean().to_numpy()

    au = np.full(n, np.nan, dtype=float)
    ad = np.full(n, np.nan, dtype=float)

    for i in range(n):
        if i == 0:
            continue
        if np.isnan(au[i - 1]):
            au[i] = up_sma[i]
            ad[i] = dn_sma[i]
        else:
            au[i] = (au[i - 1] * (length - 1.0) + up[i]) / float(length)
            ad[i] = (ad[i - 1] * (length - 1.0) + dn[i]) / float(length)

        if np.isnan(au[i]) or np.isnan(ad[i]):
            continue

        if au[i] == 0 and ad[i] == 0:
            rsi[i] = 50.0
        elif ad[i] == 0:
            rsi[i] = 100.0
        elif au[i] == 0:
            rsi[i] = 0.0
        else:
            rs = au[i] / ad[i]
            rsi[i] = 100.0 - (100.0 / (1.0 + rs))

    return rsi


def sample_stdev(series: np.ndarray, length: int) -> np.ndarray:
    return pd.Series(series).rolling(length, min_periods=length).std(ddof=1).to_numpy()


def rolling_linreg_slope(y: np.ndarray, length: int) -> np.ndarray:
    n = len(y)
    out = np.full(n, np.nan, dtype=float)
    if length <= 1:
        return out

    x = np.arange(length, dtype=float)
    sum_x = x.sum()
    sum_x2 = (x * x).sum()
    denom = length * sum_x2 - (sum_x * sum_x)
    if denom == 0:
        return out

    for i in range(length - 1, n):
        w = y[i - length + 1 : i + 1]
        if np.isnan(w).any():
            continue
        sum_y = float(w.sum())
        sum_xy = float((x * w).sum())
        m = (length * sum_xy - sum_x * sum_y) / denom
        out[i] = m
    return out


def compute_s1_tqqq_200ma_cross(time: np.ndarray, t_close: np.ndarray, t_ma200: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    n = len(t_close)
    code = np.zeros(n, dtype=int)
    weight = np.zeros(n, dtype=float)
    in_pos = False

    for i in range(n):
        if np.isnan(t_close[i]) or np.isnan(t_ma200[i]):
            in_pos = False
            code[i] = 0
            weight[i] = 0.0
            continue

        if i == 0 or np.isnan(t_close[i - 1]) or np.isnan(t_ma200[i - 1]):
            code[i] = 2 if in_pos else 0
            weight[i] = 1.0 if in_pos else 0.0
            continue

        cross_up = (t_close[i - 1] <= t_ma200[i - 1]) and (t_close[i] > t_ma200[i])
        cross_dn = (t_close[i - 1] >= t_ma200[i - 1]) and (t_close[i] < t_ma200[i])

        if (not in_pos) and cross_up:
            in_pos = True
        elif in_pos and cross_dn:
            in_pos = False

        code[i] = 2 if in_pos else 0
        weight[i] = 1.0 if in_pos else 0.0

    return code, weight


def compute_basic_strategy(
    time: np.ndarray,
    qqq_close: np.ndarray,
    q_ma3: np.ndarray,
    q_ma161: np.ndarray,
    t_close: np.ndarray,
    t_ma200: np.ndarray,
    spy_close: np.ndarray,
    spy_ma200: np.ndarray,
    params: BasicParams,
) -> Tuple[np.ndarray, np.ndarray]:
    n = len(t_close)
    codes = np.zeros(n, dtype=int)
    weights = np.zeros(n, dtype=float)

    dist200 = np.where(np.isnan(t_close) | np.isnan(t_ma200) | (t_ma200 == 0), np.nan, (t_close / t_ma200) * 100.0)
    t_ret = np.full(n, np.nan, dtype=float)
    t_ret[1:] = (t_close[1:] / t_close[:-1]) - 1.0
    t_v20 = sample_stdev(t_ret, params.vol_len)
    spyDist200 = np.where(np.isnan(spy_close) | np.isnan(spy_ma200) | (spy_ma200 == 0), np.nan, (spy_close / spy_ma200) * 100.0)

    q_rsi = rsi_wilder(qqq_close, params.rsi_len)
    rsi_reentry_ok = (~np.isnan(q_rsi)) & (q_rsi >= params.rsi_reentry_thr)
    dist_slope = rolling_linreg_slope(dist200, params.slope_len)

    ready = ((~np.isnan(q_ma3)) & (~np.isnan(q_ma161)) & (~np.isnan(t_v20)) & (~np.isnan(dist200)) & (~np.isnan(spyDist200)))

    locked = False
    assetCode = 0
    above200Hyst = False
    above200HystInited = False
    overheatStage = 0
    fullEntryClose = math.nan
    reentryLock = False
    spyBull = False
    spyInited = False
    spyConfirmCnt = 0
    tp10CycleActive = False
    tp10Reduced = False
    tp10EntryClose = math.nan

    for i in range(n):
        prevAsset = assetCode

        if not bool(ready[i]):
            assetCode = 0
            locked = False
            above200Hyst = False
            above200HystInited = False
            overheatStage = 0
            fullEntryClose = math.nan
            reentryLock = False
            spyBull = False
            spyInited = False
            spyConfirmCnt = 0
            tp10CycleActive = False
            tp10Reduced = False
            tp10EntryClose = math.nan
            codes[i] = assetCode
            weights[i] = code_weight(assetCode)
            continue

        locked = (t_v20[i] + 1e-10) >= max(params.vol_threshold, 1e-6)

        if not spyInited:
            spyBull = bool(spyDist200[i] >= params.spy_enter)
            spyInited = True
            spyConfirmCnt = 0
        else:
            if spyBull:
                if spyDist200[i] <= params.spy_exit:
                    spyConfirmCnt += 1
                    if spyConfirmCnt >= max(int(params.spy_confirm_days), 1):
                        spyBull = False
                        spyConfirmCnt = 0
                else:
                    spyConfirmCnt = 0
            else:
                if spyDist200[i] >= params.spy_enter:
                    spyConfirmCnt += 1
                    if spyConfirmCnt >= max(int(params.spy_confirm_days), 1):
                        spyBull = True
                        spyConfirmCnt = 0
                else:
                    spyConfirmCnt = 0

        spyBearNow = spyInited and (not spyBull)
        spyForceCash = spyBearNow and (params.spy_bear_cap <= 1e-9)
        reentryBlockedNow = reentryLock and (not bool(rsi_reentry_ok[i]))

        if not above200HystInited:
            above200Hyst = bool(dist200[i] >= params.dist200_enter)
            above200HystInited = True
        else:
            if above200Hyst and (dist200[i] <= params.dist200_exit):
                above200Hyst = False
            elif (not above200Hyst) and (dist200[i] >= params.dist200_enter):
                above200Hyst = True

        if locked or spyForceCash or reentryBlockedNow:
            baseCode = 0
        else:
            base0 = 2 if above200Hyst else (1 if (q_ma3[i] > q_ma161[i]) else 0)
            slopeApplicable = (params.use_slope_boost and (base0 == 1) and (not np.isnan(dist_slope[i])) and (dist200[i] <= params.dist_cap) and (t_v20[i] <= params.vol_cap))
            slopeOk = bool(slopeApplicable) and (dist_slope[i] >= params.slope_thr)
            baseCode = 2 if slopeOk else base0

        if locked or spyForceCash or reentryBlockedNow:
            overheatStage = 0
        else:
            st = overheatStage
            if st == 0:
                if baseCode == 2:
                    if dist200[i] >= params.overheat4_enter:
                        st = 4
                    elif dist200[i] >= params.overheat3_enter:
                        st = 3
                    elif dist200[i] >= params.overheat2_enter:
                        st = 2
                    elif dist200[i] >= params.overheat1_enter:
                        st = 1
                    else:
                        st = 0
                else:
                    st = 0
            elif st == 1:
                if dist200[i] >= params.overheat4_enter:
                    st = 4
                elif dist200[i] >= params.overheat3_enter:
                    st = 3
                elif dist200[i] >= params.overheat2_enter:
                    st = 2
                elif dist200[i] <= params.overheat1_exit:
                    st = 0
                else:
                    st = 1
            elif st == 2:
                if dist200[i] >= params.overheat4_enter:
                    st = 4
                elif dist200[i] >= params.overheat3_enter:
                    st = 3
                elif dist200[i] <= params.overheat1_exit:
                    st = 0
                elif dist200[i] <= params.overheat2_exit:
                    st = 1
                else:
                    st = 2
            elif st == 3:
                if dist200[i] >= params.overheat4_enter:
                    st = 4
                elif dist200[i] <= params.overheat1_exit:
                    st = 0
                elif dist200[i] <= params.overheat2_exit:
                    st = 1
                elif dist200[i] <= params.overheat3_exit:
                    st = 2
                else:
                    st = 3
            else:
                st = 0 if (dist200[i] <= params.overheat4_exit) else 4
            overheatStage = st

        preStopCode = baseCode
        if overheatStage == 4:
            preStopCode = 0
        elif overheatStage == 3:
            preStopCode = 0 if (baseCode == 0) else 5
        elif overheatStage == 2:
            preStopCode = 4 if (baseCode == 2) else baseCode
        elif overheatStage == 1:
            preStopCode = 3 if (baseCode == 2) else baseCode

        stopHit = False
        if params.use_principal_stop and is_high_exposure(prevAsset) and (not math.isnan(fullEntryClose)):
            lossCutPrice = fullEntryClose * params.principal_stop_pct
            stopHit = bool(t_close[i] <= lossCutPrice)
            if stopHit:
                reentryLock = True

        finalCode = 0 if stopHit else preStopCode
        if reentryBlockedNow:
            finalCode = 0

        wFinalPreTp = code_weight(finalCode)
        inHighNow = wFinalPreTp >= (0.80 - 1e-9)
        if (not inHighNow) or locked or stopHit or spyBearNow or reentryBlockedNow:
            tp10CycleActive = False
            tp10Reduced = False
            tp10EntryClose = math.nan
        else:
            entered100 = (finalCode == 2) and (code_weight(prevAsset) < 0.999) and (not tp10CycleActive) and (not tp10Reduced)
            if entered100:
                tp10CycleActive = True
                tp10Reduced = False
                tp10EntryClose = float(t_close[i])
            tpHitNow = (tp10CycleActive and (not tp10Reduced) and (finalCode == 2) and (not math.isnan(tp10EntryClose)) and (t_close[i] >= tp10EntryClose * (1.0 + params.tp10_trigger)))
            if tpHitNow:
                tp10Reduced = True
            if tp10Reduced and (finalCode == 2):
                finalCode = weight_to_code(params.tp10_cap)

        assetCode = int(finalCode)
        if reentryLock and (code_weight(assetCode) > 1e-9):
            reentryLock = False

        nowHigh = is_high_exposure(assetCode)
        prevHigh = is_high_exposure(prevAsset)
        if nowHigh and (not prevHigh):
            fullEntryClose = float(t_close[i])
        elif (not nowHigh) and prevHigh:
            fullEntryClose = math.nan

        codes[i] = assetCode
        weights[i] = code_weight(assetCode)

    return codes, weights


def load_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path, encoding=ENCODING)
    if "time" not in df.columns:
        raise ValueError("CSV에 'time' 컬럼이 필요합니다.")
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").reset_index(drop=True)
    for col in df.columns:
        if col == "time":
            continue
        df[col] = to_float_series(df[col])
    return df


def ensure_sma(df: pd.DataFrame, price_col: str, length: int, out_col: str) -> None:
    if out_col in df.columns and df[out_col].notna().sum() > 0:
        return
    df[out_col] = df[price_col].rolling(length, min_periods=length).mean()


def main() -> None:
    df = load_data(FILE_PATH)

    q_close_col = "QQQ종가"
    t_close_col = "TQQQ종가"
    spy_close_col = "SPY종가"
    spy_ma200_col = "SPY200일선"

    ensure_sma(df, q_close_col, 3, "QQQ3일선")
    ensure_sma(df, q_close_col, 161, "QQQ161일선")
    ensure_sma(df, t_close_col, 200, "TQQQ200일선")
    if spy_ma200_col not in df.columns:
        ensure_sma(df, spy_close_col, 200, spy_ma200_col)

    time = df["time"].to_numpy()
    q_close = df[q_close_col].to_numpy()
    q_ma3 = df["QQQ3일선"].to_numpy()
    q_ma161 = df["QQQ161일선"].to_numpy()
    t_close = df[t_close_col].to_numpy()
    t_ma200 = df["TQQQ200일선"].to_numpy()
    spy_close = df[spy_close_col].to_numpy()
    spy_ma200 = df[spy_ma200_col].to_numpy()

    s1_code, s1_w = compute_s1_tqqq_200ma_cross(time, t_close, t_ma200)
    p_s2 = BasicParams(spy_bear_cap=0.0)
    s2_code, s2_w = compute_basic_strategy(time, q_close, q_ma3, q_ma161, t_close, t_ma200, spy_close, spy_ma200, p_s2)
    p_s3 = BasicParams(spy_bear_cap=0.10)
    s3_code, s3_w = compute_basic_strategy(time, q_close, q_ma3, q_ma161, t_close, t_ma200, spy_close, spy_ma200, p_s3)

    out = pd.DataFrame({
        "time": time,
        "S1_code": s1_code,
        "S1_weight": s1_w,
        "S2_code": s2_code,
        "S2_weight": s2_w,
        "S3_code": s3_code,
        "S3_weight": s3_w,
    })

    print(out.tail(10).to_string(index=False))
    out_path = "reports/signals_s1_s2_s3_user_original.csv"
    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
