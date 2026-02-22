<script lang="ts">
	import LWLineChart from '$lib/components/charts/LWLineChart.svelte';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const d  = $derived(data.signals as any);
	const ef = $derived(data.etfFlows as any);

	// ── Derived data ─────────────────────────────────────────────────
	const btcPrice    = $derived(d?.crypto_prices?.btc);
	const ethPrice    = $derived(d?.crypto_prices?.eth);
	const summary     = $derived(d?.summary ?? {});
	const signals     = $derived((d?.smart_money_signals ?? []) as any[]);
	const arkTrades   = $derived((d?.ark_trades ?? []) as any[]);
	const arkSentiment = $derived(d?.ark_sentiment);
	const insiders    = $derived((d?.insider_trades ?? []) as any[]);
	const shortInt    = $derived((d?.short_interest ?? []) as any[]);
	const darkpool    = $derived((d?.darkpool ?? []) as any[]);
	const congress    = $derived((d?.congress_trades ?? []) as any[]);
	const holdings    = $derived((d?.institution_holdings ?? []) as any[]);

	const BTC_TICKERS = ['IBIT', 'GBTC', 'FBTC', 'ARKB', 'BITB', 'BITO'];
	const ETH_TICKERS = ['ETHE', 'ETHU'];

	const etfSummary = $derived(ef?.crypto_etf_summary ?? {});

	function filterEtfs(tickers: string[]): any[] {
		if (!ef?.flows?.length) return [];
		return tickers
			.map((t: string) => ef.flows.find((f: any) => f.ticker === t))
			.filter(Boolean);
	}

	const btcEtfs = $derived(filterEtfs(BTC_TICKERS));
	const ethEtfs = $derived(filterEtfs(ETH_TICKERS));

	function sumAum(rows: any[]): number | null {
		if (!rows.length) return null;
		const total = rows.reduce((s: number, r: any) => s + (r.total_assets ?? 0), 0);
		return total > 0 ? total : null;
	}

	function sumFlow(rows: any[], field: string): number | null {
		if (!rows.length) return null;
		let sum = 0, hasData = false;
		for (const r of rows) {
			if (r[field] !== null && r[field] !== undefined) {
				sum += r[field];
				hasData = true;
			}
		}
		return hasData ? sum : null;
	}

	// ── Chart helpers ─────────────────────────────────────────────────
	function toChartData(rows: { date: string; value: number }[] | undefined | null) {
		if (!rows?.length) return [];
		return rows.map(r => ({ time: r.date, value: r.value }));
	}

	// ── Formatters ────────────────────────────────────────────────────
	function fmtPrice(v: number | null | undefined): string {
		if (v == null) return '—';
		if (v >= 1000) return `$${v.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
		return `$${v.toFixed(2)}`;
	}

	function fmtChange(v: number | null | undefined): string {
		if (v == null) return '—';
		return `${v > 0 ? '+' : ''}${v.toFixed(2)}%`;
	}

	function changeColor(v: number | null | undefined): string {
		if (v == null) return 'var(--text-muted)';
		return v > 0 ? 'var(--green)' : v < 0 ? 'var(--red)' : 'var(--text-muted)';
	}

	function fmtScore(v: number | null | undefined): string {
		if (v == null) return '—';
		return v.toFixed(1);
	}

	function scoreColor(v: number | null | undefined): string {
		if (v == null) return 'var(--text-dimmed)';
		if (v >= 70) return 'var(--green)';
		if (v >= 50) return 'var(--amber)';
		return 'var(--red)';
	}

	function fmtVol(v: number | null | undefined): string {
		if (v == null) return '—';
		if (v >= 1_000_000_000) return `${(v / 1_000_000_000).toFixed(1)}B`;
		if (v >= 1_000_000)     return `${(v / 1_000_000).toFixed(1)}M`;
		if (v >= 1_000)         return `${(v / 1_000).toFixed(1)}K`;
		return v.toLocaleString();
	}

	function fmtPct(v: number | null | undefined, decimals = 1): string {
		if (v == null) return '—';
		return `${v > 0 ? '+' : ''}${v.toFixed(decimals)}%`;
	}

	function fmtMoney(v: number | null | undefined): string {
		if (v == null) return '—';
		const abs = Math.abs(v);
		const prefix = v < 0 ? '-$' : '$';
		if (abs >= 1_000_000_000) return `${prefix}${(abs / 1_000_000_000).toFixed(1)}B`;
		if (abs >= 1_000_000)     return `${prefix}${(abs / 1_000_000).toFixed(1)}M`;
		if (abs >= 1_000)         return `${prefix}${(abs / 1_000).toFixed(0)}K`;
		return `${prefix}${abs.toLocaleString()}`;
	}

	function fmtAum(v: number | null | undefined): string {
		return fmtMoney(v);
	}

	function fmtFlow(v: number | null | undefined): string {
		if (v == null || v === 0) return '—';
		const abs = Math.abs(v);
		const prefix = v > 0 ? '+$' : '-$';
		if (abs >= 1_000_000_000) return `${prefix}${(abs / 1_000_000_000).toFixed(1)}B`;
		if (abs >= 1_000_000)     return `${prefix}${(abs / 1_000_000).toFixed(0)}M`;
		if (abs >= 1_000)         return `${prefix}${(abs / 1_000).toFixed(0)}K`;
		return `${prefix}${abs.toLocaleString()}`;
	}

	function flowColor(v: number | null | undefined): string {
		if (v == null || v === 0) return 'var(--text-dimmed)';
		return v > 0 ? 'var(--green)' : 'var(--red)';
	}

	function fmtFlowPct(v: number | null | undefined): string {
		if (v == null || v === 0) return '—';
		return `${v > 0 ? '+' : ''}${v.toFixed(2)}%`;
	}

	function fmtDtc(v: number | null | undefined): string {
		if (v == null) return '—';
		return v.toFixed(1) + 'd';
	}

	function fmtDpi(v: number | null | undefined): string {
		if (v == null) return '—';
		return (v * 100).toFixed(1) + '%';
	}

	function cacheLabel(ts: string | null | undefined): string {
		if (!ts) return '';
		try {
			const d = new Date(ts);
			const diffMin = Math.round((Date.now() - d.getTime()) / 60_000);
			if (diffMin < 1)  return 'just now';
			if (diffMin < 60) return `${diffMin}m ago`;
			const h = Math.floor(diffMin / 60);
			return `${h}h ago`;
		} catch { return ''; }
	}
</script>

<svelte:head>
	<title>Equity Signals — Meridian</title>
	<meta name="description" content="Smart money signals across crypto-adjacent stocks — ARK trades, insider activity, dark pool, short interest for COIN, MSTR, MARA, IBIT and more." />
</svelte:head>

<div class="space-y-5">

	<!-- ── Header ──────────────────────────────────────────────────── -->
	<div class="page-header">
		<div>
			<h1 class="page-title">Equity Signals</h1>
			<p class="page-subtitle">Smart money activity across crypto-adjacent stocks · COIN · MSTR · MARA · IBIT</p>
		</div>
		{#if d?.cached_at}
			<span class="cache-label">Updated {cacheLabel(d.cached_at)}</span>
		{/if}
	</div>

	<!-- ── Error state ──────────────────────────────────────────────── -->
	{#if data.error && !d}
		<div class="card-base">
			<p class="error-msg">⚠ Failed to load equity signals: {data.error}</p>
		</div>
	{/if}

	<!-- ── Loading state ────────────────────────────────────────────── -->
	{#if !data.error && !d}
		<div class="card-base">
			<div class="loading-row">
				<div class="spinner"></div>
				<span>Loading equity signals…</span>
			</div>
		</div>
	{/if}

	{#if d}

		<!-- ── Row 1: BTC + ETH Price Cards ─────────────────────────── -->
		<div class="two-col">

			<!-- BTC -->
			<div class="card-base price-card btc-card">
				<div class="price-header">
					<span class="price-symbol btc-sym">₿</span>
					<span class="price-name">BITCOIN</span>
				</div>
				<div class="price-row">
					<span class="price-value">{fmtPrice(btcPrice?.price)}</span>
					<span class="price-change" style="color: {changeColor(btcPrice?.change_24h_pct)}">
						{fmtChange(btcPrice?.change_24h_pct)}
					</span>
				</div>
				{#if btcPrice?.chart_90d?.length}
					<div class="chart-label">90-Day Price</div>
					<LWLineChart
						data={toChartData(btcPrice.chart_90d)}
						height={120}
						color="#f59e0b"
					/>
				{/if}
			</div>

			<!-- ETH -->
			<div class="card-base price-card eth-card">
				<div class="price-header">
					<span class="price-symbol eth-sym">Ξ</span>
					<span class="price-name">ETHEREUM</span>
				</div>
				<div class="price-row">
					<span class="price-value">{fmtPrice(ethPrice?.price)}</span>
					<span class="price-change" style="color: {changeColor(ethPrice?.change_24h_pct)}">
						{fmtChange(ethPrice?.change_24h_pct)}
					</span>
				</div>
				{#if ethPrice?.chart_90d?.length}
					<div class="chart-label">90-Day Price</div>
					<LWLineChart
						data={toChartData(ethPrice.chart_90d)}
						height={120}
						color="#818cf8"
					/>
				{/if}
			</div>

		</div>

		<!-- ── Row 2: ETF Flow Cards ─────────────────────────────────── -->
		{#if ef?.flows?.length}
			<div class="two-col">

				<!-- BTC ETF Flows -->
				<div class="card-base">
					<div class="section-hdr">
						<span class="section-label">BTC ETF FLOWS</span>
						<a href="/crypto/etf" class="more-link">Full ETF details →</a>
					</div>

					<div class="etf-kpis">
						<div class="etf-kpi">
							<span class="etf-kpi-label">Total AUM</span>
							<span class="etf-kpi-val">{fmtAum(etfSummary.btc_etf_total_aum ?? sumAum(btcEtfs))}</span>
						</div>
						<div class="etf-kpi">
							<span class="etf-kpi-label">Daily Flow</span>
							<span class="etf-kpi-val" style="color: {flowColor(etfSummary.btc_etf_daily_flow ?? sumFlow(btcEtfs, 'net_flow_usd'))}">
								{fmtFlow(etfSummary.btc_etf_daily_flow ?? sumFlow(btcEtfs, 'net_flow_usd'))}
							</span>
						</div>
						<div class="etf-kpi">
							<span class="etf-kpi-label">Weekly Flow</span>
							<span class="etf-kpi-val" style="color: {flowColor(etfSummary.btc_etf_weekly_flow ?? sumFlow(btcEtfs, 'flow_5d_usd'))}">
								{fmtFlow(etfSummary.btc_etf_weekly_flow ?? sumFlow(btcEtfs, 'flow_5d_usd'))}
							</span>
						</div>
					</div>

					{#if btcEtfs.length}
						<div class="table-wrap mt-3">
							<table class="data-table compact">
								<thead>
									<tr>
										<th>Ticker</th>
										<th>Name</th>
										<th class="text-right">AUM</th>
										<th class="text-right">Daily Flow</th>
										<th class="text-right">Flow %</th>
									</tr>
								</thead>
								<tbody>
									{#each btcEtfs as etf}
										<tr>
											<td><span class="ticker-mono">{etf.ticker}</span></td>
											<td class="dim text-truncate">{etf.name}</td>
											<td class="text-right mono">{fmtAum(etf.total_assets)}</td>
											<td class="text-right mono" style="color: {flowColor(etf.net_flow_usd)}">{fmtFlow(etf.net_flow_usd)}</td>
											<td class="text-right mono" style="color: {flowColor(etf.flow_pct_aum)}">{fmtFlowPct(etf.flow_pct_aum)}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{:else}
						<p class="empty-state mt-3">No BTC ETF data available</p>
					{/if}
				</div>

				<!-- ETH ETF Flows -->
				<div class="card-base">
					<div class="section-hdr">
						<span class="section-label">ETH ETF FLOWS</span>
					</div>

					<div class="etf-kpis">
						<div class="etf-kpi">
							<span class="etf-kpi-label">Total AUM</span>
							<span class="etf-kpi-val">{fmtAum(sumAum(ethEtfs))}</span>
						</div>
						<div class="etf-kpi">
							<span class="etf-kpi-label">Daily Flow</span>
							<span class="etf-kpi-val" style="color: {flowColor(etfSummary.eth_etf_daily_flow ?? sumFlow(ethEtfs, 'net_flow_usd'))}">
								{fmtFlow(etfSummary.eth_etf_daily_flow ?? sumFlow(ethEtfs, 'net_flow_usd'))}
							</span>
						</div>
						<div class="etf-kpi">
							<span class="etf-kpi-label">Weekly Flow</span>
							<span class="etf-kpi-val" style="color: {flowColor(etfSummary.eth_etf_weekly_flow ?? sumFlow(ethEtfs, 'flow_5d_usd'))}">
								{fmtFlow(etfSummary.eth_etf_weekly_flow ?? sumFlow(ethEtfs, 'flow_5d_usd'))}
							</span>
						</div>
					</div>

					{#if ethEtfs.length}
						<div class="table-wrap mt-3">
							<table class="data-table compact">
								<thead>
									<tr>
										<th>Ticker</th>
										<th>Name</th>
										<th class="text-right">AUM</th>
										<th class="text-right">Daily Flow</th>
										<th class="text-right">Flow %</th>
									</tr>
								</thead>
								<tbody>
									{#each ethEtfs as etf}
										<tr>
											<td><span class="ticker-mono">{etf.ticker}</span></td>
											<td class="dim text-truncate">{etf.name}</td>
											<td class="text-right mono">{fmtAum(etf.total_assets)}</td>
											<td class="text-right mono" style="color: {flowColor(etf.net_flow_usd)}">{fmtFlow(etf.net_flow_usd)}</td>
											<td class="text-right mono" style="color: {flowColor(etf.flow_pct_aum)}">{fmtFlowPct(etf.flow_pct_aum)}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{:else}
						<p class="empty-state mt-3">No ETH ETF data available</p>
					{/if}
				</div>

			</div>
		{/if}

		<!-- ── Row 3: Signal Summary ──────────────────────────────────── -->
		<div class="card-base">
			<div class="section-label">SIGNAL SUMMARY</div>
			<div class="summary-kpis">
				<div class="sum-stat">
					<span class="sum-val">{summary.total_signals ?? 0}</span>
					<span class="sum-label">Total Signals</span>
				</div>
				<div class="sum-divider"></div>
				<div class="sum-stat">
					<span class="sum-val green">{summary.bullish_signals ?? 0}</span>
					<span class="sum-label">Bullish</span>
				</div>
				<div class="sum-divider"></div>
				<div class="sum-stat">
					<span class="sum-val red">{summary.bearish_signals ?? 0}</span>
					<span class="sum-label">Bearish</span>
				</div>
				{#if summary.most_active_ticker}
					<div class="sum-divider"></div>
					<div class="sum-stat">
						<span class="sum-val">{summary.most_active_ticker}</span>
						<span class="sum-label">Most Active</span>
					</div>
				{/if}
			</div>
			{#if summary.narrative}
				<p class="summary-narrative">{summary.narrative}</p>
			{/if}
		</div>

		<!-- ── Row 4: Smart Money Composite Table ────────────────────── -->
		{#if signals.length}
			<div class="card-base">
				<div class="section-label">SMART MONEY COMPOSITE — CRYPTO EQUITIES</div>
				<div class="table-wrap">
					<table class="data-table">
						<thead>
							<tr>
								<th>Ticker</th>
								<th>Company</th>
								<th class="text-right">Score</th>
								<th>Direction</th>
								<th>Sources</th>
							</tr>
						</thead>
						<tbody>
							{#each signals as sig}
								<tr>
									<td>
										<a href="/ticker/{sig.ticker}" class="ticker-link">{sig.ticker}</a>
									</td>
									<td class="text-secondary text-truncate company-col">{sig.company || '—'}</td>
									<td class="text-right">
										<span class="score-val" style="color: {scoreColor(sig.score)}">{fmtScore(sig.score)}</span>
									</td>
									<td>
										<span
											class="dir-badge"
											class:bullish={sig.direction?.toLowerCase() === 'bullish'}
											class:bearish={sig.direction?.toLowerCase() === 'bearish'}
										>{sig.direction || '—'}</span>
									</td>
									<td>
										<div class="tags-row">
											{#each (sig.sources || []) as src}
												<span class="tag">{src}</span>
											{/each}
										</div>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{/if}

		<!-- ── Row 5: ARK Trades + Insider Activity ──────────────────── -->
		<div class="two-col">

			<!-- ARK Trades -->
			<div class="card-base">
				<div class="section-label">ARK INVEST TRADES</div>

				{#if arkSentiment}
					<div class="sentiment-bar">
						<span class="sentiment-label">30d Sentiment</span>
						<span
							class="sentiment-badge"
							style="color: {arkSentiment.net === 'bullish' ? 'var(--green)' : arkSentiment.net === 'bearish' ? 'var(--red)' : 'var(--amber)'}"
						>{(arkSentiment.net ?? '—').toUpperCase()}</span>
						<span class="sentiment-detail">{arkSentiment.buys ?? 0} buys · {arkSentiment.sells ?? 0} sells</span>
					</div>
				{/if}

				{#if arkTrades.length}
					<div class="table-wrap">
						<table class="data-table compact">
							<thead>
								<tr>
									<th>Date</th>
									<th>Ticker</th>
									<th>ETF</th>
									<th>Type</th>
									<th class="text-right">Shares</th>
									<th class="text-right">Wt %</th>
								</tr>
							</thead>
							<tbody>
								{#each arkTrades.slice(0, 20) as t}
									<tr>
										<td class="mono dim">{t.date?.slice(5) ?? '—'}</td>
										<td>
											<a href="/ticker/{t.ticker}" class="ticker-link">{t.ticker}</a>
										</td>
										<td class="dim">{t.etf ?? '—'}</td>
										<td>
											<span
												class="trade-badge"
												class:buy={t.trade_type === 'Buy' || t.change_type === 'INCREASED' || t.change_type === 'NEW_POSITION'}
												class:sell={t.trade_type === 'Sell' || t.change_type === 'DECREASED' || t.change_type === 'SOLD_OUT'}
											>{t.trade_type ?? t.change_type ?? '—'}</span>
										</td>
										<td class="text-right mono">{fmtVol(t.shares)}</td>
										<td class="text-right mono dim">{t.weight_pct != null ? t.weight_pct.toFixed(2) + '%' : '—'}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
					{#if arkTrades.length > 20}
						<p class="more-note">+{arkTrades.length - 20} more trades not shown</p>
					{/if}
				{:else}
					<p class="empty-state">No recent ARK crypto equity trades</p>
				{/if}
			</div>

			<!-- Insider Trades -->
			<div class="card-base">
				<div class="section-label">INSIDER ACTIVITY</div>
				{#if insiders.length}
					<div class="table-wrap">
						<table class="data-table compact">
							<thead>
								<tr>
									<th>Ticker</th>
									<th>Insider</th>
									<th>Type</th>
									<th class="text-right">Value</th>
								</tr>
							</thead>
							<tbody>
								{#each insiders.slice(0, 15) as t}
									<tr>
										<td>
											<a href="/ticker/{t.ticker}" class="ticker-link">{t.ticker}</a>
										</td>
										<td class="text-secondary text-truncate insider-col">
											{t.insider_name ?? '—'}
											{#if t.title}
												<span class="insider-title">· {t.title}</span>
											{/if}
										</td>
										<td>
											<span
												class="trade-badge"
												class:buy={t.transaction_type === 'Purchase'}
												class:sell={t.transaction_type === 'Sale'}
											>{t.transaction_type ?? '—'}</span>
										</td>
										<td class="text-right mono">{fmtMoney(t.value)}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<p class="empty-state">No recent insider trades in crypto equities</p>
				{/if}
			</div>

		</div>

		<!-- ── Row 6: Short Interest + Dark Pool ─────────────────────── -->
		<div class="two-col">

			<!-- Short Interest -->
			<div class="card-base">
				<div class="section-label">SHORT INTEREST</div>
				{#if shortInt.length}
					<div class="table-wrap">
						<table class="data-table compact">
							<thead>
								<tr>
									<th>Ticker</th>
									<th class="text-right">Short Int.</th>
									<th class="text-right">Change</th>
									<th class="text-right">DTC</th>
									<th class="text-right">% Float</th>
								</tr>
							</thead>
							<tbody>
								{#each shortInt.slice(0, 15) as si}
									<tr>
										<td>
											<a href="/ticker/{si.ticker}" class="ticker-link">{si.ticker}</a>
										</td>
										<td class="text-right mono">{fmtVol(si.short_interest)}</td>
										<td class="text-right mono" style="color: {si.change_pct > 0 ? 'var(--red)' : si.change_pct < 0 ? 'var(--green)' : 'var(--text-dimmed)'}">
											{fmtPct(si.change_pct)}
										</td>
										<td class="text-right mono dim">{fmtDtc(si.days_to_cover)}</td>
										<td class="text-right mono">{si.short_pct_float ? si.short_pct_float.toFixed(1) + '%' : '—'}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<p class="empty-state">No short interest data for crypto equities</p>
				{/if}
			</div>

			<!-- Dark Pool -->
			<div class="card-base">
				<div class="section-label">DARK POOL ACTIVITY</div>
				{#if darkpool.length}
					<div class="table-wrap">
						<table class="data-table compact">
							<thead>
								<tr>
									<th>Ticker</th>
									<th class="text-right">Total Vol</th>
									<th class="text-right">DPI</th>
									<th class="text-right">Off-Exch</th>
									<th class="text-right">Short %</th>
								</tr>
							</thead>
							<tbody>
								{#each darkpool as dp}
									<tr>
										<td>
											<a href="/ticker/{dp.ticker}" class="ticker-link">{dp.ticker}</a>
										</td>
										<td class="text-right mono">{fmtVol(dp.total_volume)}</td>
										<td class="text-right mono">{fmtDpi(dp.dpi)}</td>
										<td class="text-right mono">{fmtPct(dp.off_exchange_pct)}</td>
										<td class="text-right mono">{fmtPct(dp.short_pct)}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<p class="empty-state">No dark pool data for crypto equities</p>
				{/if}
			</div>

		</div>

		<!-- ── Row 7: Congress Trades (full width) ───────────────────── -->
		<div class="card-base">
			<div class="section-label">CONGRESS TRADES</div>
			{#if congress.length}
				<div class="table-wrap">
					<table class="data-table">
						<thead>
							<tr>
								<th>Date</th>
								<th>Representative</th>
								<th>Party</th>
								<th>Ticker</th>
								<th>Type</th>
								<th class="text-right">Amount</th>
							</tr>
						</thead>
						<tbody>
							{#each congress as t}
								<tr>
									<td class="mono dim">{t.transaction_date ?? '—'}</td>
									<td>{t.representative ?? '—'}</td>
									<td class="dim">{t.party?.charAt(0) ?? '—'}</td>
									<td>
										<a href="/ticker/{t.ticker}" class="ticker-link">{t.ticker}</a>
									</td>
									<td>
										<span
											class="trade-badge"
											class:buy={t.trade_type === 'Buy' || t.trade_type === 'Purchase'}
											class:sell={t.trade_type === 'Sell' || t.trade_type === 'Sale'}
										>{t.trade_type ?? '—'}</span>
									</td>
									<td class="text-right mono dim">{t.amount_range ?? '—'}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<div class="congress-empty">
					<p class="congress-empty-main">No recent crypto-related Congress trades</p>
					<p class="congress-empty-sub">This section populates when members disclose positions in crypto-adjacent stocks (COIN, MSTR, IBIT, MARA, etc.)</p>
				</div>
			{/if}
		</div>

		<!-- ── Row 8: 13F Holdings (full width, conditional) ─────────── -->
		{#if holdings.length}
			<div class="card-base">
				<div class="section-label">INSTITUTIONAL HOLDINGS (13F)</div>
				<div class="table-wrap">
					<table class="data-table">
						<thead>
							<tr>
								<th>Institution</th>
								<th>Ticker</th>
								<th class="text-right">Value</th>
								<th>Filing Date</th>
							</tr>
						</thead>
						<tbody>
							{#each holdings as h}
								<tr>
									<td class="text-truncate institution-col">{h.institution ?? '—'}</td>
									<td>
										<a href="/ticker/{h.ticker}" class="ticker-link">{h.ticker}</a>
									</td>
									<td class="text-right mono">{fmtMoney(h.value)}</td>
									<td class="mono dim">{h.filing_date ?? '—'}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{/if}

	{/if}
</div>

<style>
	/* ── Spacing helper ─────────────────────────────────────────────── */
	.space-y-5 > * + * { margin-top: 20px; }
	.mt-3 { margin-top: 12px; }

	/* ── Page Header ────────────────────────────────────────────────── */
	.page-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 12px;
		flex-wrap: wrap;
	}

	.page-title {
		font-size: 18px;
		font-weight: 600;
		color: var(--text-primary);
		letter-spacing: -0.01em;
	}

	.page-subtitle {
		font-size: 12px;
		color: var(--text-muted);
		margin-top: 3px;
	}

	.cache-label {
		font-size: 11px;
		color: var(--text-dimmed);
		flex-shrink: 0;
		white-space: nowrap;
		padding-top: 4px;
	}

	/* ── Card Base ──────────────────────────────────────────────────── */
	.card-base {
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 12px;
		padding: 20px;
	}

	/* ── Two-col grid ───────────────────────────────────────────────── */
	.two-col {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 16px;
	}

	@media (max-width: 768px) {
		.two-col { grid-template-columns: 1fr; }
	}

	/* ── Section labels ─────────────────────────────────────────────── */
	.section-label {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 0.07em;
		text-transform: uppercase;
		color: var(--text-muted);
		margin-bottom: 14px;
	}

	.section-hdr {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 14px;
	}

	.section-hdr .section-label {
		margin-bottom: 0;
	}

	.more-link {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 11px;
		color: var(--text-dimmed);
		text-decoration: none;
		transition: color 0.15s;
	}

	.more-link:hover {
		color: var(--text-secondary);
	}

	/* ── Price Cards ────────────────────────────────────────────────── */
	.price-card {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.btc-card { border-top: 2px solid rgba(245, 158, 11, 0.35); }
	.eth-card  { border-top: 2px solid rgba(129, 140, 248, 0.35); }

	.price-header {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.price-symbol {
		font-size: 18px;
		font-weight: 800;
		line-height: 1;
	}

	.btc-sym { color: #f59e0b; }
	.eth-sym { color: #818cf8; }

	.price-name {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.07em;
		text-transform: uppercase;
		color: var(--text-dimmed);
	}

	.price-row {
		display: flex;
		align-items: baseline;
		gap: 12px;
		flex-wrap: wrap;
	}

	.price-value {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 32px;
		font-weight: 700;
		color: var(--text-primary);
		letter-spacing: -0.02em;
		line-height: 1;
	}

	.price-change {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 16px;
		font-weight: 600;
	}

	.chart-label {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--text-dimmed);
		margin-top: 4px;
		margin-bottom: 6px;
	}

	/* ── ETF KPIs ───────────────────────────────────────────────────── */
	.etf-kpis {
		display: flex;
		gap: 20px;
		flex-wrap: wrap;
		padding: 12px 14px;
		background: var(--bg-elevated);
		border-radius: 8px;
		border: 1px solid var(--border-default);
	}

	.etf-kpi {
		display: flex;
		flex-direction: column;
		gap: 3px;
	}

	.etf-kpi-label {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 9px;
		font-weight: 600;
		letter-spacing: 0.07em;
		text-transform: uppercase;
		color: var(--text-dimmed);
	}

	.etf-kpi-val {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 18px;
		font-weight: 700;
		color: var(--text-primary);
		line-height: 1.2;
	}

	/* ── Signal Summary ─────────────────────────────────────────────── */
	.summary-kpis {
		display: flex;
		align-items: center;
		gap: 0;
		flex-wrap: wrap;
		margin-bottom: 14px;
	}

	.sum-stat {
		display: flex;
		flex-direction: column;
		gap: 3px;
		padding: 0 20px;
	}

	.sum-stat:first-child {
		padding-left: 0;
	}

	.sum-divider {
		width: 1px;
		height: 36px;
		background: var(--border-default);
	}

	.sum-val {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 28px;
		font-weight: 700;
		color: var(--text-primary);
		line-height: 1;
	}

	.sum-val.green { color: var(--green); }
	.sum-val.red   { color: var(--red); }

	.sum-label {
		font-size: 11px;
		color: var(--text-dimmed);
		letter-spacing: 0.02em;
	}

	.summary-narrative {
		font-size: 13px;
		color: var(--text-muted);
		line-height: 1.65;
		border-top: 1px solid var(--border-default);
		padding-top: 12px;
		margin-top: 2px;
	}

	/* ── ARK Sentiment bar ──────────────────────────────────────────── */
	.sentiment-bar {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 8px 12px;
		background: var(--bg-elevated);
		border-radius: 8px;
		border: 1px solid var(--border-default);
		margin-bottom: 12px;
		flex-wrap: wrap;
	}

	.sentiment-label {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--text-dimmed);
	}

	.sentiment-badge {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 13px;
		font-weight: 700;
		letter-spacing: 0.03em;
	}

	.sentiment-detail {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 11px;
		color: var(--text-dimmed);
	}

	/* ── Tables ─────────────────────────────────────────────────────── */
	.table-wrap {
		overflow-x: auto;
		-webkit-overflow-scrolling: touch;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 13px;
	}

	.data-table.compact {
		font-size: 12px;
	}

	.data-table th {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dimmed);
		padding: 5px 10px;
		border-bottom: 1px solid var(--border-default);
		text-align: left;
		white-space: nowrap;
	}

	.data-table td {
		padding: 8px 10px;
		border-bottom: 1px solid rgba(255,255,255,0.04);
		color: var(--text-secondary);
		white-space: nowrap;
	}

	.data-table.compact td {
		padding: 6px 10px;
	}

	.data-table tr:last-child td {
		border-bottom: none;
	}

	.data-table tbody tr:hover td {
		background: var(--bg-elevated);
	}

	/* Alignment helpers */
	.text-right   { text-align: right; }
	.text-secondary { color: var(--text-secondary); }

	/* Font helpers */
	.mono {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
	}

	.dim { color: var(--text-dimmed); }

	/* Truncation */
	.text-truncate {
		max-width: 160px;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.company-col   { max-width: 180px; }
	.insider-col   { max-width: 150px; }
	.institution-col { max-width: 200px; }

	/* ── Ticker link ────────────────────────────────────────────────── */
	.ticker-link {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 12px;
		font-weight: 700;
		color: var(--text-primary);
		text-decoration: none;
		letter-spacing: 0.03em;
		transition: color 0.15s;
	}

	.ticker-link:hover {
		color: var(--blue, #818cf8);
	}

	.ticker-mono {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 12px;
		font-weight: 700;
		color: var(--text-primary);
		letter-spacing: 0.03em;
	}

	/* ── Score ──────────────────────────────────────────────────────── */
	.score-val {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 13px;
		font-weight: 700;
	}

	/* ── Direction badge ────────────────────────────────────────────── */
	.dir-badge {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--text-dimmed);
		padding: 2px 7px;
		border-radius: 4px;
		background: var(--bg-elevated);
		border: 1px solid var(--border-default);
	}

	.dir-badge.bullish {
		color: var(--green);
		background: rgba(34, 197, 94, 0.08);
		border-color: rgba(34, 197, 94, 0.2);
	}

	.dir-badge.bearish {
		color: var(--red);
		background: rgba(239, 68, 68, 0.08);
		border-color: rgba(239, 68, 68, 0.2);
	}

	/* ── Trade badge ────────────────────────────────────────────────── */
	.trade-badge {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--text-dimmed);
	}

	.trade-badge.buy  { color: var(--green); }
	.trade-badge.sell { color: var(--red); }

	/* ── Source tags ────────────────────────────────────────────────── */
	.tags-row {
		display: flex;
		gap: 4px;
		flex-wrap: wrap;
		align-items: center;
	}

	.tag {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.02em;
		padding: 2px 6px;
		border-radius: 4px;
		background: var(--bg-elevated);
		border: 1px solid var(--border-default);
		color: var(--text-dimmed);
		white-space: nowrap;
	}

	/* ── Insider title ──────────────────────────────────────────────── */
	.insider-title {
		font-size: 10px;
		color: var(--text-dimmed);
	}

	/* ── "More trades" note ─────────────────────────────────────────── */
	.more-note {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 11px;
		color: var(--text-dimmed);
		margin-top: 10px;
		padding: 6px 10px;
		border-left: 2px solid var(--border-default);
	}

	/* ── Congress empty state ───────────────────────────────────────── */
	.congress-empty {
		text-align: center;
		padding: 24px 0;
	}

	.congress-empty-main {
		font-size: 13px;
		color: var(--text-muted);
		margin-bottom: 5px;
	}

	.congress-empty-sub {
		font-size: 11px;
		color: var(--text-dimmed);
		max-width: 480px;
		margin: 0 auto;
		line-height: 1.55;
	}

	/* ── Generic empty / error / loading ───────────────────────────── */
	.empty-state {
		font-size: 12px;
		color: var(--text-dimmed);
		padding: 10px 0;
	}

	.error-msg {
		font-size: 13px;
		color: var(--red);
		padding: 16px;
	}

	.loading-row {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 12px;
		padding: 40px;
		font-size: 13px;
		color: var(--text-muted);
	}

	.spinner {
		width: 18px;
		height: 18px;
		border: 2px solid var(--border-default);
		border-top-color: var(--text-muted);
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
		flex-shrink: 0;
	}

	@keyframes spin { to { transform: rotate(360deg); } }
</style>
