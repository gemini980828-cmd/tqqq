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

/** Represents a high-priority action required from a specific manager */
export interface PriorityAction {
  id: string
  severity: 'high' | 'medium' | 'low'
  manager_id: string
  title: string
  detail: string
  recommended_action: string
  goto_screen?: string
  created_at?: string
}

/** Represents an alert involving multiple managers */
export interface CrossManagerAlert {
  id: string
  severity: 'high' | 'medium' | 'low'
  manager_ids: string[]
  title: string
  detail: string
  goto_screen?: string
  created_at?: string
}

/** Represents an event in the timeline, now including source manager and severity */
export interface EventTimelineItem {
  id?: string
  date: string
  type: string
  detail: string
  title?: string
  source_manager_id?: string
  severity?: 'high' | 'medium' | 'low' | 'info'
  entity_type?: string
  entity_id?: string
  timestamp?: string // optional legacy/alternate field
  event?: string // optional legacy/alternate field
}

/** Represents a research candidate from the discovery feed */
export interface ResearchCandidate {
  idea_id: string
  symbol: string
  status: string
  memo: string
  priority: string
  priority_reason: string
  manager_id: string
  next_action: string
}

/** Represents an AI-generated report highlight */
export interface ReportHighlight {
  id: string
  title: string
  summary: string
  severity: string
  manager_ids: string[]
  updated_at?: string
}

/** Represents a dynamically suggested prompt for the orchestrator */
export interface OrchestratorPromptStarter {
  id: string
  label: string
  prompt: string
  source_manager_ids: string[]
  intent: string
}

export interface CompareData {
  manager_pairs: Array<{
    pair_id: string
    manager_ids: string[]
    headlines?: Record<string, string>
  }>
  holding_overlap: Array<{
    overlap_id: string
    left_manager_id: string
    right_manager_id: string
    shared_symbols: string[]
  }>
  conflicting_recommendations: Array<{
    conflict_id: string
    manager_ids: string[]
    detail: string
  }>
}

export interface StockResearchQueueItem {
  id: string;
  symbol: string;
  title: string;
  reason: string;
  severity: string;
  status: string;
  is_held: boolean;
  next_action: string;
  age_label?: string;
  score?: number;
}

export interface StockResearchEvidenceRef {
  id?: string;
  label: string;
  source?: string;
  url?: string;
  summary?: string;
}

export type StockResearchSubscores = Record<string, number>;

export interface StockResearchWorkspaceItem {
  idea_id: string;
  symbol: string;
  company_name: string;
  status: string;
  memo: string;
  is_held: boolean;
  overlap_level: 'low' | 'medium' | 'high';
  priority: 'high' | 'medium' | 'low';
  priority_reason: string;
  next_action: string;
  generated_at: string;
  score?: number;
  risk_level?: 'low' | 'medium' | 'high';
  recent_status_change?: string;
  engine_version?: string;
  confidence?: 'low' | 'medium' | 'high' | string;
  reason_codes?: string[];
  evidence_refs?: StockResearchEvidenceRef[];
  subscores?: StockResearchSubscores;
}

export interface StockResearchCompareSeed {
  primary_symbol: string;
  candidate_symbols: string[];
  default_mode?: 'fit' | 'overlap' | 'action';
}

export interface StockResearchFilters {
  total_count: number;
  held_count: number;
  candidate_count: number;
  observe_count: number;
  status_counts: Record<string, number>;
}

export interface StockResearchFlow {
  pipeline: string[];
  active_stage?: string;
  stage_counts: Record<string, number>;
}

export interface StockResearchEvidence {
  chart?: unknown;
  news?: unknown[];
  institutional_flow?: unknown;
}

export interface StockResearchWorkspace {
  generated_at: string;
  filters: StockResearchFilters;
  queue: StockResearchQueueItem[];
  items: StockResearchWorkspaceItem[];
  compare_seed: StockResearchCompareSeed;
  flow?: StockResearchFlow;
  evidence?: StockResearchEvidence;
}

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
  event_timeline?: EventTimelineItem[];
  manager_events?: Record<string, EventTimelineItem[]>;
  home_discovery?: {
    priority_action_ids?: string[];
    cross_manager_alert_ids?: string[];
    prompt_ids?: string[];
    report_highlight_ids?: string[];
  };
  priority_actions?: PriorityAction[];
  cross_manager_alerts?: CrossManagerAlert[];
  orchestrator_prompt_starters?: OrchestratorPromptStarter[];
  research_candidates?: ResearchCandidate[];
  report_highlights?: ReportHighlight[];
  compare_data?: CompareData;
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
    signal_updated_at?: string;
    market_updated_at?: string;
    audit_available?: boolean;
  };
  stock_research_workspace?: StockResearchWorkspace;
};
