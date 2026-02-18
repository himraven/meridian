// ═══════════════════════════════════════════════════════════════════
// API Type Definitions — Smart Money Platform
// Generated from DATA_CONTRACT.md — DO NOT manually deviate
// ═══════════════════════════════════════════════════════════════════

// ═══ Common Types ═══

export interface ApiMetadata {
	total: number;
	filtered: number;
	filters: Record<string, any>;
	last_updated: string;
}

// ═══ Congress ═══

export interface CongressTrade {
	ticker: string;
	representative: string;
	bio_guide_id: string;
	party: 'Republican' | 'Democrat';
	chamber: 'Senate' | 'House';
	trade_type: 'Purchase' | 'Sale' | 'Sale (Partial)';
	amount_range: string;
	amount_min: number;
	amount_max: number;
	transaction_date: string;
	filing_date: string;
	price_at_trade: number | null;
	price_current: number | null;
	stock_return_pct: number | null;
	spy_return_pct: number | null;
	excess_return_pct: number | null;
	company: string;
}

export interface CongressTradesResponse {
	data: CongressTrade[];
	metadata: ApiMetadata;
}

// ═══ ARK ═══

export interface ArkTrade {
	ticker: string;
	etf: string;
	trade_type: 'Buy' | 'Sell';
	date: string;
	shares: number;
	weight_pct: number;
	price_at_trade: number | null;
	price_current: number | null;
	return_pct: number | null;
	company: string;
	change_type: string;
	change_pct: number;
	prev_shares: number;
}

export interface ArkTradesResponse {
	data: ArkTrade[];
	metadata: ApiMetadata;
}

export interface ArkHolding {
	ticker: string;
	etf: string;
	shares: number;
	weight_pct: number;
	market_value: number;
	date: string;
	price: number;
	company: string;
}

export interface ArkHoldingsResponse {
	data: ArkHolding[];
	metadata: ApiMetadata;
}

// ═══ Dark Pool ═══

export interface DarkpoolData {
	ticker: string;
	date: string;
	off_exchange_volume: number;
	short_volume: number;
	total_volume: number;
	dpi: number;
	off_exchange_pct: number;
	short_pct: number;
	z_score: number;
	z_score_window: number;
	source: string;
	company: string;
}

export interface DarkpoolAnalyticsResponse {
	data: DarkpoolData[];
	metadata: ApiMetadata;
}

// ═══ Institutions ═══

export interface InstitutionFiling {
	cik: string;
	fund_name: string;
	company_name: string;
	filing_date: string;
	quarter: string;
	total_value: number;
	holdings_count: number;
}

export interface InstitutionHolding {
	ticker: string;
	issuer: string;
	institution: string;
	cik: string;
	shares: number;
	value: number;
	pct_portfolio: number;
	cusip: string;
	filing_date: string;
	quarter: string;
}

export interface InstitutionsFilingsResponse {
	data: InstitutionFiling[];
	top_holdings: InstitutionHolding[];
	summary: {
		total_value: number;
		unique_tickers: number;
		filings_count: number;
	};
	metadata: ApiMetadata;
}

// ═══ Signals ═══

export interface SignalConfluence {
	ticker: string;
	score: number;
	direction: 'bullish' | 'bearish' | 'mixed';
	sources: string;
	source_count: number;
	signal_date: string;
	congress_score: number;
	ark_score: number;
	darkpool_score: number;
	institution_score: number;
	details: string;
	scoring: string;
	company: string;
}

export interface SignalsConfluenceResponse {
	data: SignalConfluence[];
	metadata: ApiMetadata;
}

// ═══ Ticker Detail ═══

export interface TickerDetailResponse {
	ticker: string;
	company: string;
	congress: {
		trades: CongressTrade[];
		count: number;
	};
	ark: {
		trades: ArkTrade[];
		holdings: ArkHolding[];
		trade_count: number;
		holding_etfs: number;
	};
	darkpool: {
		anomalies: DarkpoolData[];
		count: number;
	};
	institutions: {
		holdings: InstitutionHolding[];
		count: number;
	};
	confluence: {
		signals: SignalConfluence[];
		score: number;
	};
	metadata: {
		total_signals: number;
		has_confluence: boolean;
	};
}

// ═══ Portfolio ═══

export interface Position {
	id: number;
	market: string;
	ticker: string;
	name: string;
	signal_source: string;
	entry_date: string;
	entry_price: number;
	entry_reason: string;
	current_price: number;
	high_price: number;
	pnl_pct: number;
	status: string;
	exit_date: string | null;
	exit_price: number | null;
	exit_reason: string | null;
	holding_days: number;
	extra: Record<string, any>;
}

export interface PortfolioMetrics {
	total_return: number;
	sharpe: number;
	win_rate: number;
	avg_holding_days: number;
	open_positions: number;
	closed_positions: number;
	total_positions: number;
	unrealized_return: number;
	realized_return: number;
	best_position: Position | null;
	worst_position: Position | null;
}

export interface DailyReturn {
	date: string;
	portfolio_value: number;
	daily_return_pct: number;
	open_positions: number;
}

export interface ActionLog {
	date: string;
	timestamp: string;
	action: string;
	ticker: string;
	details: string;
}

export interface PortfolioResponse {
	created: string;
	last_updated: string;
	initial_capital: number;
	positions: Position[];
	closed_positions: Position[];
	metrics: PortfolioMetrics;
	daily_returns: DailyReturn[];
	actions_log: ActionLog[];
}

// ═══ CN Portfolio ═══

export interface CnPosition {
	ticker: string;
	code: string;
	name: string;
	market: string;
	status: string;
	entry_price: number;
	current_price: number;
	pnl_pct: number;
	score: number;
	entry_date: string;
	days_held: number;
}

export interface CnPortfolioMetrics {
	total_return: number;
	open_positions: number;
	win_rate: number;
	best_position: CnPosition | null;
	worst_position: CnPosition | null;
	backtest_total_return: number;
	backtest_sharpe: number;
	backtest_max_drawdown: number;
}

export interface CnPortfolioResponse {
	created: string;
	last_updated: string;
	initial_capital: number;
	positions: CnPosition[];
	closed_positions: CnPosition[];
	metrics: CnPortfolioMetrics;
	daily_returns: DailyReturn[];
	actions_log: ActionLog[];
}

// ═══ HK Signals ═══

export interface HkSignal {
	rank: number;
	ticker: string;
	name: string;
	vmq_score: number;
	quality: number;
	momentum: number;
	value: number;
	sector: string;
	reason: string;
	pe: number;
	pb: number;
	roe: number;
	ff_roe: number;
	ff_gross_margin: number;
	ff_fcf_yield: number;
	ff_dividend_yield: number;
	ff_coverage: number;
	entry_score: number;
	entry_label: string;
	entry_zone: string;
	exit_levels: Record<string, any>;
	current_price: number;
	entry_description: string;
	indicators: Record<string, any>;
}

export interface HkSignalsResponse {
	date: string;
	generated_at: string;
	picks: HkSignal[];
	updated_at: string;
}

// ═══ CN Trend ═══

export interface CnTrendResponse {
	signal: 'bull' | 'bear';
	date: string;
	price: number;
	ma200: number;
	ma_distance_pct: number;
	rsi14: number;
	volume_ratio: number;
	last_signal_change: string | null;
	previous_signal: string | null;
	updated_at: string;
}

// ═══ CN 8x30 Strategy ═══

export interface Cn8x30NavResponse {
	dates: string[];
	strategy_nav: number[];
	benchmark_nav: number[];
	strategy_name: string;
	benchmark_name: string;
	total_return_pct: number;
	benchmark_return_pct: number;
}

export interface Cn8x30Holding {
	ts_code: string;
	close: number;
	score: number;
	ret_5d_pct: number;
	ret_20d_pct: number;
	daily_amount_wan: number;
	entry_price: number;
	pct_chg: number;
	name: string;
}

export interface Cn8x30PortfolioResponse {
	date: string;
	strategy: string;
	rebalance_days: number;
	top_n: number;
	initial_capital: number;
	per_stock: number;
	factors: Record<string, any>;
	holdings: Cn8x30Holding[];
	price_updated_at: string;
}

export interface Cn8x30MetricsResponse {
	total_return: number;
	max_drawdown: number;
	sharpe: number;
	trading_days: number;
	updated_at: string;
}

export interface Cn8x30SensitivityResponse {
	top_n_sensitivity: Record<string, any>;
	rebalance_sensitivity: Record<string, any>;
	monte_carlo: {
		mean: number;
		std: number;
		min: number;
		max: number;
		n: number;
	};
	confidence_score: {
		score: number;
		max: number;
		reasons: string[];
	};
	recommendation: string;
}

// ═══ System ═══

export interface VpsStatusResponse {
	cpu_pct: number;
	cpu_count: number;
	ram_used_gb: number;
	ram_total_gb: number;
	ram_pct: number;
	disk_used_gb: number;
	disk_total_gb: number;
	disk_pct: number;
	uptime: string;
	uptime_secs: number;
	hostname: string;
	os: string;
	load_avg: number[];
}

export interface AiStatusResponse {
	online: boolean;
	model: string;
	gateway_running: boolean;
	uptime: string | null;
	pid: number | null;
}

export interface CronJob {
	name: string;
	schedule: string;
	last_run: string;
	next_run: string;
	status: string;
}

export interface CronsResponse {
	crons: CronJob[];
}

// ═══ Usage ═══

export interface UsagePeriod {
	cost: number;
	tokens_in: number;
	tokens_out: number;
}

export interface UsageResponse {
	status: string;
	today: UsagePeriod;
	this_week: UsagePeriod;
	this_month: UsagePeriod;
	rate_limits: {
		current_session: {
			tokens_out: number;
			tokens_in: number;
			cost: number;
			window_hours: number;
			pct_used: number;
			resets_at?: string;
			resets_in_seconds?: number;
		};
		weekly: {
			all_models: {
				tokens_out: number;
				tokens_in: number;
				cost: number;
				limit: number;
				pct_used: number;
				resets_at?: string;
			};
			sonnet_only: {
				tokens_out?: number;
				limit?: number;
				pct_used: number;
				resets_at?: string;
			};
		};
		monthly?: {
			tokens_out: number;
			limit: number;
			pct_used: number;
		};
	};
	by_model?: Record<string, any>;
	by_day?: any[];
}

// ═══ Other ═══

export interface KnowledgeSection {
	[key: string]: any[];
}

export interface KnowledgeResponse {
	sections: Record<string, any[]>;
	stats: {
		total_articles: number;
		total_words: number;
		last_updated: string;
		section_count: number;
	};
}

export interface ChangelogEntry {
	date: string;
	version?: string;
	changes: string[];
}

export interface ChangelogResponse {
	entries: ChangelogEntry[];
	stats: {
		total: number;
	};
}

export interface DividendScreenerResponse {
	status: string;
	message: string;
	us: any[];
	hk: any[];
	cn: any[];
}
