export type RiskStatus = 'green' | 'amber' | 'red';
export type InboxSeverity = 'high' | 'medium' | 'low';

export type RiskGaugeValue = { value: number; threshold: number; status: RiskStatus };

export type ManagerSummaryRecord = {
  manager_id: string;
  summary_text: string;
  key_points: string[];
  warnings: string[];
  recommended_actions: string[];
  generated_at: string;
  source_version: string;
  stale: boolean;
};

export type ManagerCardSummary = {
  manager_id: string;
  label?: string;
  title?: string;
  status: string;
  summary?: string;
  headline?: string;
  recommended_action?: string;
  warning_count?: number;
  stale?: boolean;
  generated_at?: string;
  warnings?: string[];
  key_points?: string[];
};

export type WealthOverview = {
  invested_krw?: number;
  investable_assets_krw?: number;
  cash_krw?: number;
  debt_krw?: number;
  net_worth_krw?: number;
};

export type LiquiditySummary = {
  cash_krw?: number;
  debt_krw?: number;
  net_liquidity_krw?: number;
  liquidity_ratio_pct?: number;
};

export type HomeInboxItem = {
  id: string;
  manager_id: string;
  severity: InboxSeverity;
  title: string;
  detail: string;
  recommended_action?: string;
  stale?: string;
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
    inbox_preview?: HomeInboxItem[];
    updated_at?: string;
  };
  wealth_overview?: WealthOverview;
  liquidity_summary?: LiquiditySummary;
  manager_cards?: ManagerCardSummary[];
  manager_summaries?: Record<string, ManagerSummaryRecord>;
  home_inbox?: HomeInboxItem[];
  orchestrator_briefs?: {
    action?: string;
    cash?: string;
    risk?: string;
    stock_research?: string;
    real_estate?: string;
    default_priority?: string;
  };
  orchestrator_policy?: {
    quick_prompts?: string[];
    intent_rules?: Array<{
      key: string;
      label: string;
      source_manager_id: string;
      priority: number;
      tokens: string[];
      support_keys?: string[];
    }>;
  };
  orchestrator_insights?: {
    total_questions?: number;
    last_question_at?: string | null;
    top_intents?: Array<{ intent: string; count: number }>;
    recent_questions?: Array<{
      timestamp: string;
      question: string;
      primary_intent: string;
      source_manager_ids: string[];
    }>;
  };
  core_strategy_position?: CoreStrategyPosition;
  core_strategy_actuals?: CoreStrategyPosition;
  meta?: {
    manual_source_version?: string;
    summary_source_version?: string;
    summary_store_path?: string;
  };
};
