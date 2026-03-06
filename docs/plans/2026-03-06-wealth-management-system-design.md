# Wealth Management System Design

## 1. Context

The current product is an action-first TQQQ operations dashboard with Telegram alerting, backtest artifacts, and a static dashboard snapshot pipeline. The user has approved expanding it into an investment-operations-centered personal wealth management system that feels like an asset management manager rather than a single-strategy monitor.

The approved direction is a **hybrid structure**:
- Internally, the system should behave like an asset catalog / operating system.
- In the UI, it should still feel like manager-oriented surfaces (TQQQ Manager, Stock Research Manager, Real Estate Manager, etc.).
- The product remains **investment-operations first**, with broader wealth management used to support investment decisions rather than replace them.

## 2. Product Goal

Build a personal wealth management system that lets the user:
1. See total asset status and actionable priorities from a single home screen.
2. Operate the TQQQ core strategy in production with real-position awareness.
3. Manage stock ideas, real-estate candidates, cash, and debt in parallel.
4. Ask a real-time orchestrator AI for cross-domain guidance when needed.
5. Keep API cost controlled through cached manager summaries and on-demand real-time analysis.

## 3. Non-Goals (MVP)

The first release must **not** attempt to provide:
- Brokerage API integration.
- Fully automated real-estate crawling or transaction ingestion from every source.
- Manager-specific always-on real-time chat for every domain.
- Family sharing, inheritance workflows, or multi-user permissions.
- Full retirement / tax / insurance planning engine.
- Complex workflow automation beyond structured summaries, inbox generation, and targeted alerts.

The first release is intended to establish the platform skeleton, the data truth model, and the AI operating model without overbuilding.

## 4. Design Principles

### 4.1 Data is truth, AI is interpreter
All balances, positions, transactions, statuses, and watchlists must come from a canonical data layer. AI is allowed to summarize, interpret, prioritize, and recommend, but must never become the authoritative owner of financial state.

### 4.2 Investment operations remain the center
The system exists first to help the user run money well. Cash-flow, debt, research, and real estate are included because they affect portfolio decisions, liquidity, and prioritization.

### 4.3 Home is a desk, not a report
The home view should function like the user's daily operating desk:
- overall asset condition,
- today's priorities,
- recent changes,
- quick entry into domain managers,
- real-time access to the orchestrator AI.

### 4.4 Manager summaries are cheap; orchestrator dialogue is premium
Daily and event-driven manager summaries should be cached and reused. Expensive real-time reasoning should be reserved for the orchestrator chat or explicit deep-analysis actions.

### 4.5 Manual truth first
Because Samsung Securities API integration is unavailable, the first release must assume manual portfolio truth:
- manual positions,
- manual transactions,
- manual cash/debt state,
- manual stock watchlists,
- manual real-estate watchlists.

This is acceptable and preferable for early reliability.

## 5. Information Architecture

### 5.1 Primary navigation
Top-level navigation:
- **Home**
- **Managers**
- **Research**
- **Inbox**
- **Reports**

### 5.2 Managers / Assets navigation
Within Managers:
- **Core Strategy Manager** (TQQQ)
- **Stock Research Manager**
- **Real Estate Manager**
- **Cash & Debt**
- Future: Retirement / Insurance / Alternatives

### 5.3 Home structure
The Home page is the operating desk and must include:
1. **Wealth overview row**
   - total net worth,
   - total liquid assets,
   - major allocation split,
   - change/risk badges.
2. **Action / Inbox row**
   - today's must-do items,
   - weekly priorities,
   - warnings,
   - top three focus items.
3. **Manager cards row**
   - TQQQ,
   - Stocks,
   - Real Estate,
   - Cash & Debt,
   each with status, alerts, and a CTA.
4. **Orchestrator AI panel**
   - real-time chat input,
   - quick prompts,
   - recent recommendations.
5. **Recent activity / event log**
   - signals,
   - watchlist changes,
   - property changes,
   - cash/debt warnings.

### 5.4 Navigation metaphor
The UX metaphor is:
- **Home** = desk
- **Managers** = workrooms
- **Research** = archive / notebook
- **Inbox** = execution queue
- **Reports** = review book

This metaphor should remain stable across future expansion.

## 6. Manager Definitions

### 6.1 Core Strategy Manager (TQQQ)
**Purpose:** Operate the core leveraged ETF strategy in production.

**Primary data:**
- signal artifacts,
- backtest metrics,
- actual position ledger,
- transaction history,
- alert/job state.

**Required views:**
- target vs actual position,
- action card,
- strategy performance,
- risk gauges,
- signal timeline,
- execution recommendation,
- manager AI summary.

**Manager AI responsibilities:**
- explain current signal,
- explain target/actual divergence,
- flag execution gaps,
- summarize risk regime.

### 6.2 Stock Research Manager
**Purpose:** Track, score, and curate individual stock ideas.

**Primary data:**
- watchlist,
- notes,
- filings/news metadata,
- screenshots/webp attachments,
- status labels,
- checklists / scores.

**Required views:**
- candidate board,
- state buckets (observe / candidate / hold / park / reject),
- recent changes,
- notes and attachments,
- manager AI research briefs.

**Manager AI responsibilities:**
- summarize a candidate in a few lines,
- group similar ideas,
- turn screenshots/notes into structured insight,
- identify promotion / rejection candidates.

### 6.3 Real Estate Manager
**Purpose:** Follow interest complexes, compare options, and support buy/no-buy decisions.

**Primary data:**
- saved complexes,
- price / rent / status snapshots,
- area notes,
- commute/school/location notes,
- attachments/links,
- priority labels.

**Required views:**
- interest list,
- state buckets (interest / review / waiting / exclude),
- trend cards,
- comparison tables,
- checklists,
- manager AI decision brief.

**Manager AI responsibilities:**
- summarize why a complex is still in consideration,
- compare top candidates,
- compress long notes into action-ready summaries,
- keep a decision log concise.

### 6.4 Cash & Debt
**Purpose:** Track investable cash, safety cash, debt burden, and payment schedule.

**Primary data:**
- cash balances,
- debt balances,
- repayment schedule,
- recurring outflows,
- account-level liquidity labels.

**Required views:**
- investable cash,
- operating cash buffer,
- debt dashboard,
- repayment calendar,
- liquidity warnings,
- manager AI summary.

**Manager AI responsibilities:**
- explain current liquidity,
- flag near-term cash pressure,
- tell whether portfolio action is constrained by cash/debt.

## 7. AI Architecture

## 7.1 Two-layer model
The approved AI architecture has two layers:

### A. Manager AI layer (batch / event driven)
Manager AIs generate structured summaries for each domain.
They are responsible for:
- summary text,
- key points,
- warnings,
- recommended actions,
- freshness metadata.

They must **not** own truth data or mutate core balances on their own.

### B. Orchestrator AI layer (real-time when requested)
The orchestrator AI is the only real-time conversational AI in the MVP.
It reads:
- canonical / derived state,
- latest manager summaries,
- inbox / alerts,
then responds to user questions such as:
- “What should I prioritize today?”
- “Is cash more urgent than adding risk?”
- “Which manager is currently the most important?”

## 7.2 Why this model was chosen
This model preserves:
- low baseline cost,
- fast UI loading,
- consistent answers,
- cross-domain reasoning when explicitly requested.

It also avoids the common failure mode where every page becomes an expensive real-time AI session.

## 8. Cost-Control Policy

The approved operating policy is **Policy B: batch summaries + on-demand real-time orchestrator**.

### 8.1 Rules
1. **Page load must not imply AI execution.**
   All default page renders use stored summaries and derived data.
2. **Manager AI runs on schedule or events.**
   Example triggers:
   - TQQQ signal changed,
   - watchlist state changed,
   - new note/attachment added,
   - property changed,
   - manual cash/debt state changed.
3. **Orchestrator AI runs only when asked.**
   It may also produce one lightweight daily overview, but not a full deep analysis automatically.
4. **Deep analysis is explicit.**
   “Re-evaluate this stock”, “Should I buy this property?”, “Rebalance suggestion” should be button-driven or command-driven, not automatic.
5. **Avoid repeated ingestion of raw long-form context.**
   Long notes, screenshots, and documents should first become structured manager summaries. The orchestrator should consume those summaries instead of repeatedly parsing raw source material.

### 8.2 Expected benefits
- predictable cost,
- reuse of cached reasoning,
- better response speed,
- simpler auditability of AI outputs.

## 9. Data Architecture

### 9.1 Four-layer data model
The approved data model has four layers.

#### A. Raw layer
Unmodified or lightly normalized source inputs:
- market data,
- signals,
- manual ledgers,
- notes,
- screenshots,
- real-estate source files,
- imported reports.

#### B. Canonical layer
System-internal normalized truth tables / records:
- assets,
- accounts,
- positions,
- transactions,
- watchlists,
- properties,
- cash_debt,
- notes,
- attachments,
- alerts.

This is the main source of truth layer.

#### C. Derived layer
Computed operational views:
- allocation,
- target vs actual,
- liquidity ratios,
- trend states,
- event timelines,
- inbox items,
- summary cards.

This layer is disposable and rebuildable.

#### D. AI summary layer
Structured outputs from manager AIs and the orchestrator:
- summary text,
- key points,
- warnings,
- actions,
- generation time,
- source version/hash,
- stale flag.

This layer improves usability but is **not** truth.

### 9.2 Source-of-truth assignments
- **TQQQ positions / transactions:** manual portfolio ledger + strategy artifacts.
- **Stocks:** watchlist table + notes + attachments + status labels.
- **Real estate:** saved complexes + snapshots + notes + ranking fields.
- **Cash/debt:** manual balances + schedules + recurring obligations.
- **Overall wealth:** aggregation from canonical asset and liability records.

### 9.3 Staleness model
Every derived and AI summary record should carry:
- generated_at,
- source_version or source hash,
- stale / fresh indicator.

This is required so the UI can distinguish between valid cached reasoning and outdated AI interpretation.

## 10. UX Behavior

### 10.1 Desktop priority order
The desktop home view should emphasize:
1. wealth overview,
2. action/inbox,
3. manager status cards,
4. orchestrator AI,
5. recent event log.

### 10.2 Mobile priority order
The mobile order should collapse to:
1. total wealth snapshot,
2. today’s action,
3. manager cards,
4. orchestrator AI,
5. events.

### 10.3 User interaction model
The user should be able to:
- passively monitor via stored summaries,
- act from the inbox,
- drill into specific managers,
- ask the orchestrator for cross-domain prioritization.

The product should feel decisive and operational, not like an undirected chatbot shell.

## 11. Inbox and Reports

### 11.1 Inbox
Inbox is the execution queue and must collect:
- today’s trading actions,
- weekly review tasks,
- new research items,
- real-estate follow-up tasks,
- cash/debt warnings.

Inbox items should be derivable from canonical + derived + AI summary layers and should not depend solely on free-form AI output.

### 11.2 Reports
Reports are periodic review surfaces and should include:
- total wealth trend,
- allocation changes,
- realized decision history,
- TQQQ performance snapshots,
- stock research progression,
- real-estate ranking changes,
- liquidity/debt trend summaries.

Reports are review-oriented, not action-oriented.

## 12. MVP Scope

### 12.1 MVP includes
- Home operating desk.
- Managers shell with four domains:
  - Core Strategy,
  - Stock Research,
  - Real Estate,
  - Cash & Debt.
- Research hub for notes and attachments.
- Inbox.
- Reports shell.
- Real-time orchestrator chat.
- Batch/event-driven manager summaries.
- Manual portfolio truth and manual supporting ledgers.

### 12.2 MVP excludes
- brokerage API sync,
- fully automated real-estate ingestion at scale,
- family sharing / inheritance operations,
- multi-user collaboration,
- advanced tax / retirement simulation,
- domain-specific real-time chat for every manager.

## 13. Rollout Sequence

### Phase 1 — Platform skeleton
- global navigation,
- Home shell,
- canonical data model scaffolding,
- TQQQ manager migration,
- manual portfolio truth integration.

### Phase 2 — Domain manager breadth
- Stock Research Manager,
- Real Estate Manager,
- Cash & Debt,
- research notes / attachments,
- basic inbox and reports scaffolding.

### Phase 3 — AI operating layer
- manager summary jobs,
- freshness/staleness model,
- orchestrator data assembly,
- real-time orchestrator chat,
- lightweight daily overview.

### Phase 4 — Refinement
- richer reports,
- deeper alerting,
- scenario planning,
- ingestion automation,
- document/archive improvements.

## 14. MVP Success Criteria

The MVP is successful when:
1. The Home page gives the user a trustworthy single view of wealth status and current priorities.
2. TQQQ manager is production-usable with actual-vs-target awareness.
3. Stock and real-estate domains are usable as structured management surfaces, not just note dumps.
4. Cash and debt visibility materially informs portfolio decisions.
5. The orchestrator can answer cross-domain questions using stored manager summaries and canonical data.
6. The system remains useful even if AI summaries are temporarily unavailable.
7. API cost remains bounded because cached summaries power the default UX.

## 15. Key Risks and Guardrails

### Risks
- The Home page becomes overloaded.
- Canonical data model becomes too abstract too early.
- AI summaries diverge from data truth.
- Real-time orchestrator becomes a hidden always-on cost center.
- Too many top-level tabs dilute the product.

### Guardrails
- Keep top-level navigation minimal.
- Let Home summarize and route, not replace manager pages.
- Never let AI own authoritative balances or statuses.
- Require freshness metadata for every summary.
- Enforce manual-truth-first workflows before adding automation.

## 16. Future Expansion (Explicitly Deferred)

Potential future additions once the core platform stabilizes:
- retirement / pension manager,
- insurance manager,
- alternatives / collectibles,
- family sharing and executor access,
- document vault and legal packet management,
- advanced scenario planning and tax simulation,
- broader data connectors.

These should remain outside the initial execution plan unless they become blocking requirements.

## 17. Reference Patterns

The design direction was informed by the following product patterns:
- **Empower** for linked-account style holistic overview and transaction rule thinking.
- **Monarch** for recurring finance support, bill sync, and operational personal-finance overlays.
- **Kubera** for broader wealth-system framing, sharing, and manual asset flexibility.
- **Redfin** for real-estate favorites, saved search, and alert/watchlist patterns.

These references were used as pattern inspiration only. The approved design is customized for an investment-operations-centered personal system rather than a generic consumer finance app.
