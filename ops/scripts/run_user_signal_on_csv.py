from __future__ import annotations

import argparse
from pathlib import Path
import importlib.util
import sys

import pandas as pd


def load_user_module():
    path = Path('ops/scripts/user_original_reference.py')
    spec = importlib.util.spec_from_file_location('user_original_reference', path)
    if spec is None or spec.loader is None:
        raise RuntimeError('cannot load user_original_reference.py')
    mod = importlib.util.module_from_spec(spec)
    sys.modules['user_original_reference'] = mod
    spec.loader.exec_module(mod)
    return mod


def main(data_csv: Path, out_csv: Path):
    u = load_user_module()
    df = pd.read_csv(data_csv, parse_dates=['time']).sort_values('time').reset_index(drop=True)

    # ensure required SMA columns
    u.ensure_sma(df, 'QQQ종가', 3, 'QQQ3일선')
    u.ensure_sma(df, 'QQQ종가', 161, 'QQQ161일선')
    u.ensure_sma(df, 'TQQQ종가', 200, 'TQQQ200일선')
    if 'SPY200일선' not in df.columns:
        u.ensure_sma(df, 'SPY종가', 200, 'SPY200일선')

    t = df['time'].to_numpy()
    s1c, s1w = u.compute_s1_tqqq_200ma_cross(t, df['TQQQ종가'].to_numpy(), df['TQQQ200일선'].to_numpy())
    s2c, s2w = u.compute_basic_strategy(t, df['QQQ종가'].to_numpy(), df['QQQ3일선'].to_numpy(), df['QQQ161일선'].to_numpy(), df['TQQQ종가'].to_numpy(), df['TQQQ200일선'].to_numpy(), df['SPY종가'].to_numpy(), df['SPY200일선'].to_numpy(), u.BasicParams(spy_bear_cap=0.0))
    s3c, s3w = u.compute_basic_strategy(t, df['QQQ종가'].to_numpy(), df['QQQ3일선'].to_numpy(), df['QQQ161일선'].to_numpy(), df['TQQQ종가'].to_numpy(), df['TQQQ200일선'].to_numpy(), df['SPY종가'].to_numpy(), df['SPY200일선'].to_numpy(), u.BasicParams(spy_bear_cap=0.10))

    out = pd.DataFrame({'time': t, 'S1_code': s1c, 'S1_weight': s1w, 'S2_code': s2c, 'S2_weight': s2w, 'S3_code': s3c, 'S3_weight': s3w})
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False, encoding='utf-8-sig')
    print(f'saved: {out_csv} rows={len(out)}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--data-csv', default='data/user_input_2000_ext.csv')
    ap.add_argument('--out-csv', default='reports/signals_s1_s2_s3_user_extended.csv')
    args = ap.parse_args()
    main(Path(args.data_csv), Path(args.out_csv))
