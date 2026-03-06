export type RiskStatus = 'green' | 'amber' | 'red';

export type RiskGaugeValue = { value: number; threshold: number; status: RiskStatus };

export type ManagerCardSummary = {
  manager_id: string;
  label?: string;
  title?: string;
  status: string;
  summary?: string;
  headline?: string;
};

export type WealthOverview = {
  invested_krw?: number;
  investable_assets_krw?: number;
  cash_krw?: number;
  debt_krw?: number;
  net_worth_krw?: number;
};

export type CoreStrategyPosition = {
  symbol?: string;
  name?: string;
  quantity?: number;
  market_value_krw?: number;
  actual_value_krw?: number;
  market_price_krw?: number;
  avg_cost_krw?: number;
  target_weight_pct?: number;
  actual_weight_pct?: number;
  gap_weight_pct?: number;
  gap_pct?: number;
  rebalance_gap_krw?: number;
  investable_total_krw?: number;
};

export type AppSnapshot = {
  action_hero?: {
    action: string;
    target_weight_pct: number;
    reason_summary: string;
    updated_at: string;
  };
  kpi_cards?: {
    cagr_pct: number;
    mdd_pct: number;
    month_1_return_pct: number;
    condition_pass_rate: string;
  };
  risk_gauges?: {
    vol20?: RiskGaugeValue;
    spy200_dist?: RiskGaugeValue;
    tqqq_dist200?: RiskGaugeValue;
  };
  event_timeline?: Array<{
    date: string;
    type: string;
    detail: string;
  }>;
  ops_log?: {
    run_id: string;
    alert_key: string;
    last_success_at: string;
    next_run_at?: string;
  };
  wealth_home?: {
    overview?: WealthOverview;
    manager_cards?: ManagerCardSummary[];
    updated_at?: string;
  };
  wealth_overview?: WealthOverview;
  manager_cards?: ManagerCardSummary[];
  core_strategy_position?: CoreStrategyPosition;
  core_strategy_actuals?: CoreStrategyPosition;
  meta?: {
    manual_source_version?: string;
  };
};
